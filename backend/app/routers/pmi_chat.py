import asyncio
import json
import logging
import math
import time
from contextlib import contextmanager
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from redis.exceptions import RedisError

from app.configs.dependencies import get_current_user
from app.models.user import User
from app.schemas.pmi_chat import PMIChatRequest, PMIChatResponse
from app.schemas.pmi_draft import PMIDraftResponse, PMIDraftState
from app.services.pmi.chat_service import PMIChatError, PMIChatService
from app.services.pmi.chat_tools import PMIChatTools
from app.services.pmi.draft_service import PMIDraftService
from app.services.pmi.draft_store import (
    PMIDraftStore,
    get_pmi_draft_store,
)
from app.services.pmi.ollama_client import OllamaError
from app.services.pmi.session_store import PMISessionNotFound


router = APIRouter(prefix="/pmi/drafts", tags=["PMI chat"])
logger = logging.getLogger(__name__)

MAX_CHAT_TURNS = 50
TURN_TIMEOUT_SECONDS = 300


@contextmanager
def _storage_errors():
    try:
        yield
    except PMISessionNotFound:
        raise HTTPException(
            status_code=404,
            detail="Bozza non trovata o scaduta.",
        ) from None
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail=(
                "Archivio temporaneamente non disponibile. "
                "Ricarica la conversazione prima di riprovare."
            ),
        ) from None


def _chat_key(user_id: int, draft_id: str) -> str:
    return f"pmi:chat:{user_id}:{draft_id}"


def _load_turns(
    store: PMIDraftStore,
    user_id: int,
    draft_id: str,
) -> list[dict]:
    raw = store.client.get(_chat_key(user_id, draft_id))
    return json.loads(raw) if raw else []


def _save_turns(
    store: PMIDraftStore,
    user_id: int,
    draft_id: str,
    record: dict,
    turns: list[dict],
) -> None:
    ttl = math.ceil(record["absolute_expires_epoch"] - time.time())

    if ttl <= 0:
        raise PMISessionNotFound

    # Store JSON directly. Do not decode/re-encode message arrays in Lua.
    store.client.set(
        _chat_key(user_id, draft_id),
        json.dumps(turns, ensure_ascii=False, allow_nan=False),
        ex=ttl,
    )


def _response(record: dict, turns: list[dict]) -> PMIChatResponse:
    state = PMIDraftState.model_validate(record["input_data"])
    summary = PMIDraftService.summarize(state)

    return PMIChatResponse(
        draft=PMIDraftResponse(
            **summary.model_dump(),
            draft_id=record["session_id"],
            expires_at=record["expires_at"],
        ),
        turns=turns,
    )


def _model_history(turns: list[dict]) -> list[dict]:
    # The UI receives the full stored conversation.
    # The model receives the last two completed exchanges plus
    # the current draft snapshot supplied by PMIChatService.
    completed = [
        turn for turn in turns
        if turn["status"] == "completed"
    ][-2:]

    history = []

    for turn in completed:
        history.append({
            "role": "user",
            "content": turn["user_message"],
        })
        history.append({
            "role": "assistant",
            "content": turn["assistant_message"],
        })

    return history


async def _run_turn(
    service: PMIChatService,
    *,
    user_id: int,
    draft_id: str,
    message: str,
    history: list[dict],
) -> dict:
    async with asyncio.timeout(TURN_TIMEOUT_SECONDS):
        return await service.run_turn(
            user_id=user_id,
            draft_id=draft_id,
            user_message=message,
            history=history,
            debug=False,
        )


@router.get("/{draft_id}/chat", response_model=PMIChatResponse)
def get_chat(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    store: PMIDraftStore = Depends(get_pmi_draft_store),
) -> PMIChatResponse:
    with _storage_errors():
        # Ownership is checked before reading any conversation.
        record = store.get_session(
            user_id=current_user.id,
            session_id=draft_id,
        )
        turns = _load_turns(store, current_user.id, draft_id)

        return _response(record, turns)


@router.post("/{draft_id}/chat", response_model=PMIChatResponse)
def send_message(
    draft_id: str,
    request: PMIChatRequest,
    current_user: User = Depends(get_current_user),
    store: PMIDraftStore = Depends(get_pmi_draft_store),
) -> PMIChatResponse:
    # A synchronous endpoint runs in FastAPI's thread pool.
    # asyncio.run manages the asynchronous model calls inside that thread.
    with _storage_errors():
        record = store.get_session(
            user_id=current_user.id,
            session_id=draft_id,
        )

        remaining_lifetime = (
            record["absolute_expires_epoch"] - time.time()
        )
        if remaining_lifetime <= 0:
            raise PMISessionNotFound

        # Keep the lock valid for the remaining lifetime of this draft.
        # A second chat request must not execute concurrently.
        lock = store.client.lock(
            f"pmi:chat-lock:{current_user.id}:{draft_id}",
            timeout=remaining_lifetime,
            blocking=False,
        )

        if not lock.acquire(blocking=False):
            raise HTTPException(
                status_code=409,
                detail="Un messaggio è già in elaborazione per questa bozza.",
            )

        try:
            # Re-read after acquiring the lock.
            record = store.get_session(
                user_id=current_user.id,
                session_id=draft_id,
            )
            turns = _load_turns(store, current_user.id, draft_id)
            request_id = str(request.request_id)

            existing = next(
                (
                    turn for turn in turns
                    if turn["request_id"] == request_id
                ),
                None,
            )

            if existing is not None:
                if existing["user_message"] != request.message:
                    raise HTTPException(
                        status_code=409,
                        detail="request_id già usato per un messaggio diverso.",
                    )

                if existing["status"] == "completed":
                    return _response(record, turns)

                raise HTTPException(
                    status_code=409,
                    detail=(
                        "Questa richiesta è in elaborazione o è fallita. "
                        "Rileggi conversazione e bozza prima di inviare "
                        "un nuovo messaggio."
                    ),
                )

            if len(turns) >= MAX_CHAT_TURNS:
                raise HTTPException(
                    status_code=409,
                    detail="Raggiunto il limite di messaggi per questa bozza.",
                )

            history = _model_history(turns)

            turn = {
                "request_id": request_id,
                "user_message": request.message,
                "assistant_message": None,
                "status": "processing",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "error": None,
            }
            turns.append(turn)

            # Persist the request before invoking the model.
            _save_turns(
                store, current_user.id, draft_id, record, turns
            )

            service = PMIChatService(PMIChatTools(store))

            try:
                outcome = asyncio.run(
                    _run_turn(
                        service,
                        user_id=current_user.id,
                        draft_id=draft_id,
                        message=request.message,
                        history=history,
                    )
                )
            except (OllamaError, PMIChatError, TimeoutError):
                turn["status"] = "failed"
                turn["error"] = (
                    "Il turno non è stato completato. "
                    "Eventuali aggiornamenti già riusciti restano salvati: "
                    "controlla la bozza prima di riprovare."
                )
            except Exception as exc:
                # Do not log case data or raw exception messages.
                logger.error(
                    "PMI chat turn failed with %s",
                    type(exc).__name__,
                )
                turn["status"] = "failed"
                turn["error"] = (
                    "Errore interno durante il turno. "
                    "Controlla la bozza prima di riprovare."
                )
            else:
                turn["status"] = "completed"
                turn["assistant_message"] = outcome["reply"]

            _save_turns(
                store, current_user.id, draft_id, record, turns
            )

            # Return the authoritative draft, including changes that
            # may have succeeded before a later model failure.
            current_record = store.get_session(
                user_id=current_user.id,
                session_id=draft_id,
            )
            return _response(current_record, turns)

        finally:
            try:
                if lock.owned():
                    lock.release()
            except RedisError:
                logger.warning("Could not release a PMI chat lock")