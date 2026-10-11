import json
import secrets
import time
from datetime import datetime, timezone
from functools import lru_cache
from typing import Any

from redis import Redis

from app.configs.config import settings


class PMISessionNotFound(Exception):
    """Session do not exist, is expired or do not belong to the user!"""


class PMISessionLimitReached(Exception):
    """User Reached the maximum number of opened Session!"""


class PMISessionConflict(Exception):
    """Session already modified by another request!"""


_CREATE_SCRIPT = """
local now = tonumber(ARGV[1])
local max_sessions = tonumber(ARGV[2])
local payload = ARGV[3]
local ttl = tonumber(ARGV[4])
local expires_at = tonumber(ARGV[5])
local session_id = ARGV[6]
local index_ttl = tonumber(ARGV[7])

redis.call('ZREMRANGEBYSCORE', KEYS[1], '-inf', now)

if redis.call('ZCARD', KEYS[1]) >= max_sessions then
    return 0
end

redis.call('SET', KEYS[2], payload, 'EX', ttl, 'NX')
redis.call('ZADD', KEYS[1], expires_at, session_id)
redis.call('EXPIRE', KEYS[1], index_ttl)

return 1
"""

_TOUCH_SCRIPT = """
local raw = redis.call('GET', KEYS[1])
if not raw then
    return ''
end

local session = cjson.decode(raw)
if tonumber(session.user_id) ~= tonumber(ARGV[1]) then
    return ''
end

local now = tonumber(ARGV[2])
local idle_ttl = tonumber(ARGV[3])
local absolute_expiry = tonumber(session.absolute_expires_epoch)
local expires_at = math.min(now + idle_ttl, absolute_expiry)
local ttl = expires_at - now

if ttl <= 0 then
    redis.call('DEL', KEYS[1])
    redis.call('ZREM', KEYS[2], ARGV[4])
    return ''
end

session.expires_at = ARGV[5]
redis.call('SET', KEYS[1], cjson.encode(session), 'EX', ttl)
redis.call('ZADD', KEYS[2], expires_at, ARGV[4])
redis.call('EXPIRE', KEYS[2], tonumber(ARGV[6]))

return cjson.encode(session)
"""

_UPDATE_SCRIPT = """
local raw = redis.call('GET', KEYS[1])
if not raw then
    return -1
end

local current = cjson.decode(raw)
if tonumber(current.user_id) ~= tonumber(ARGV[1]) then
    return -1
end

if tonumber(current.version) ~= tonumber(ARGV[2]) then
    return 0
end

redis.call('SET', KEYS[1], ARGV[3], 'EX', tonumber(ARGV[4]))
redis.call('ZADD', KEYS[2], tonumber(ARGV[5]), ARGV[6])
redis.call('EXPIRE', KEYS[2], tonumber(ARGV[7]))

return 1
"""

_DELETE_SCRIPT = """
local raw = redis.call('GET', KEYS[1])
if not raw then
    redis.call('ZREM', KEYS[2], ARGV[1])
    return 0
end

local session = cjson.decode(raw)
if tonumber(session.user_id) ~= tonumber(ARGV[2]) then
    return 0
end

redis.call('DEL', KEYS[1])
redis.call('ZREM', KEYS[2], ARGV[1])

return 1
"""


def _utc_iso(timestamp: int) -> str:
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat()


class PMISessionStore:

    def __init__(self, client: Redis) -> None:
        self.client = client
        self._create_script = client.register_script(_CREATE_SCRIPT)
        self._touch_script = client.register_script(_TOUCH_SCRIPT)
        self._update_script = client.register_script(_UPDATE_SCRIPT)
        self._delete_script = client.register_script(_DELETE_SCRIPT)

    @staticmethod
    def _session_key(session_id: str) -> str:
        return f"pmi:session:{session_id}"

    @staticmethod
    def _user_index_key(user_id: int) -> str:
        return f"pmi:user:{user_id}:sessions"

    #set up the session for the user
    def create_session(self,*,user_id: int,input_data: dict[str, Any],results: list[dict[str, Any]]) -> dict[str, Any]:
        now = int(time.time())
        absolute_expiry = now + settings.PMI_SESSION_MAX_TTL_SECONDS
        expires_at = min(
            now + settings.PMI_SESSION_IDLE_TTL_SECONDS,
            absolute_expiry,
        )
        ttl = expires_at - now

        session_id = secrets.token_urlsafe(32)
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "input_data": input_data,
            "results": results,
            "selected_median_methods": [],
            "median_pmi": None,
            "selected_save_methods": [],
            "status": "calculated",
            "version": 1,
            "created_at": _utc_iso(now),
            "expires_at": _utc_iso(expires_at),
            "absolute_expires_epoch": absolute_expiry,
        }

        created = self._create_script(
            keys=[
                self._user_index_key(user_id),
                self._session_key(session_id),
            ],
            args=[
                now,
                settings.PMI_MAX_OPEN_SESSIONS_PER_USER,
                json.dumps(session, separators=(",", ":")),
                ttl,
                expires_at,
                session_id,
                settings.PMI_SESSION_MAX_TTL_SECONDS,
            ],
        )

        if int(created) != 1:
            raise PMISessionLimitReached

        return session

    def get_session(
        self,
        *,
        user_id: int,
        session_id: str,
    ) -> dict[str, Any]:
        now = int(time.time())
        session_key = self._session_key(session_id)

        raw = self.client.get(session_key)
        if not raw:
            raise PMISessionNotFound

        stored_session = json.loads(raw)
        expires_at = min(
            now + settings.PMI_SESSION_IDLE_TTL_SECONDS,
            int(stored_session["absolute_expires_epoch"]),
        )

        raw = self._touch_script(
            keys=[
                session_key,
                self._user_index_key(user_id),
            ],
            args=[
                user_id,
                now,
                settings.PMI_SESSION_IDLE_TTL_SECONDS,
                session_id,
                _utc_iso(expires_at),
                settings.PMI_SESSION_MAX_TTL_SECONDS,
            ],
        )

        if not raw:
            raise PMISessionNotFound

        return json.loads(raw)

    def update_session(
        self,
        *,
        user_id: int,
        session: dict[str, Any],
        expected_version: int,
    ) -> dict[str, Any]:
        now = int(time.time())
        absolute_expiry = int(session["absolute_expires_epoch"])
        expires_at = min(
            now + settings.PMI_SESSION_IDLE_TTL_SECONDS,
            absolute_expiry,
        )
        ttl = expires_at - now

        if ttl <= 0:
            raise PMISessionNotFound

        updated = dict(session)
        updated["version"] = expected_version + 1
        updated["expires_at"] = _utc_iso(expires_at)

        result = self._update_script(
            keys=[
                self._session_key(session["session_id"]),
                self._user_index_key(user_id),
            ],
            args=[
                user_id,
                expected_version,
                json.dumps(updated, separators=(",", ":")),
                ttl,
                expires_at,
                session["session_id"],
                settings.PMI_SESSION_MAX_TTL_SECONDS,
            ],
        )

        if int(result) == -1:
            raise PMISessionNotFound
        if int(result) == 0:
            raise PMISessionConflict

        return updated

    def list_sessions(self, *, user_id: int) -> list[dict[str, Any]]:
        now = int(time.time())
        index_key = self._user_index_key(user_id)

        self.client.zremrangebyscore(index_key, "-inf", now)
        session_ids = self.client.zrange(index_key, 0, -1)

        sessions = []
        for session_id in session_ids:
            try:
                sessions.append(
                    self.get_session(user_id=user_id, session_id=session_id)
                )
            except PMISessionNotFound:
                self.client.zrem(index_key, session_id)

        return sessions

    def delete_session(self, *, user_id: int, session_id: str) -> None:
        self._delete_script(
            keys=[
                self._session_key(session_id),
                self._user_index_key(user_id),
            ],
            args=[session_id, user_id],
        )


@lru_cache(maxsize=1)
def get_pmi_session_store() -> PMISessionStore:
    # Singleston keep only the pool of redis connection and not users sessions
    client = Redis.from_url(
        settings.REDIS_URL,
        password=settings.REDIS_PASSWORD or None,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2,
        health_check_interval=30,
    )
    return PMISessionStore(client)