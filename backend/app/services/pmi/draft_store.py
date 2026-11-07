from functools import lru_cache

from app.services.pmi.session_store import (
    PMISessionStore,
    get_pmi_session_store,
)


class PMIDraftStore(PMISessionStore):
    @staticmethod
    def _session_key(session_id: str) -> str:
        return f"pmi:draft:{session_id}"

    @staticmethod
    def _user_index_key(user_id: int) -> str:
        return f"pmi:user:{user_id}:drafts"


@lru_cache(maxsize=1)
def get_pmi_draft_store() -> PMIDraftStore:
    return PMIDraftStore(get_pmi_session_store().client)