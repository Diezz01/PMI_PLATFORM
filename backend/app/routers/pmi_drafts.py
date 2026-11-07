from contextlib import contextmanager

from fastapi import APIRouter, Depends, HTTPException
from redis.exceptions import RedisError

from app.configs.dependencies import get_current_user
from app.models.user import User
from app.schemas.pmi_draft import (
    PMIDraftConfirmRequest,
    PMIDraftResponse,
    PMIDraftState,
    PMIDraftUpdateRequest,
)
from app.services.pmi.draft_service import (
    PMIDraftConflict,
    PMIDraftNotReady,
    PMIDraftService,
)
from app.services.pmi.draft_store import (
    PMIDraftStore,
    get_pmi_draft_store,
)
from app.services.pmi.session_store import (
    PMISessionConflict,
    PMISessionLimitReached,
    PMISessionNotFound,
)


router = APIRouter(prefix="/pmi/drafts", tags=["PMI drafts"])
draft_service = PMIDraftService()


@contextmanager
def _handle_errors():
    try:
        yield
    except PMISessionNotFound:
        raise HTTPException(
            status_code=404,
            detail="Bozza non trovata o scaduta.",
        ) from None
    except (PMISessionConflict, PMIDraftConflict):
        raise HTTPException(
            status_code=409,
            detail="La bozza è cambiata. Ricaricala e riprova.",
        ) from None
    except PMIDraftNotReady as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from None
    except PMISessionLimitReached:
        raise HTTPException(
            status_code=429,
            detail="Hai raggiunto il numero massimo di bozze aperte.",
        ) from None
    except RedisError:
        raise HTTPException(
            status_code=503,
            detail="L'archivio temporaneo delle bozze non è disponibile.",
        ) from None


def _read_state(record: dict) -> PMIDraftState:
    return PMIDraftState.model_validate(record["input_data"])


def _build_response(record: dict) -> PMIDraftResponse:
    summary = draft_service.summarize(_read_state(record))

    return PMIDraftResponse(
        **summary.model_dump(),
        draft_id=record["session_id"],
        expires_at=record["expires_at"],
    )


def _persist_state(
    *,
    store: PMIDraftStore,
    user_id: int,
    record: dict,
    state: PMIDraftState,
    expected_version: int,
) -> dict:
    # Redis incrementa la versione a ogni scrittura accettata.
    # Allineiamo la versione interna anche per aggiornamenti
    # che non modificano effettivamente i dati.
    persisted_state = state.model_copy(
        update={"version": expected_version + 1},
        deep=True,
    )

    return store.update_session(
        user_id=user_id,
        session={
            **record,
            "input_data": persisted_state.model_dump(mode="json"),
        },
        expected_version=expected_version,
    )


@router.post("", response_model=PMIDraftResponse, status_code=201)
def create_draft(
    current_user: User = Depends(get_current_user),
    store: PMIDraftStore = Depends(get_pmi_draft_store),
) -> PMIDraftResponse:
    with _handle_errors():
        state = draft_service.create()

        record = store.create_session(
            user_id=current_user.id,
            input_data=state.model_dump(mode="json"),
            results=[],
        )

        return _build_response(record)


@router.get("/{draft_id}", response_model=PMIDraftResponse)
def get_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    store: PMIDraftStore = Depends(get_pmi_draft_store),
) -> PMIDraftResponse:
    with _handle_errors():
        record = store.get_session(
            user_id=current_user.id,
            session_id=draft_id,
        )

        return _build_response(record)


@router.patch("/{draft_id}", response_model=PMIDraftResponse)
def update_draft(
    draft_id: str,
    request: PMIDraftUpdateRequest,
    current_user: User = Depends(get_current_user),
    store: PMIDraftStore = Depends(get_pmi_draft_store),
) -> PMIDraftResponse:
    with _handle_errors():
        record = store.get_session(
            user_id=current_user.id,
            session_id=draft_id,
        )

        state = draft_service.update(
            _read_state(record),
            request,
        )

        updated_record = _persist_state(
            store=store,
            user_id=current_user.id,
            record=record,
            state=state,
            expected_version=request.expected_version,
        )

        return _build_response(updated_record)


@router.post("/{draft_id}/confirm", response_model=PMIDraftResponse)
def confirm_draft(
    draft_id: str,
    request: PMIDraftConfirmRequest,
    current_user: User = Depends(get_current_user),
    store: PMIDraftStore = Depends(get_pmi_draft_store),
) -> PMIDraftResponse:
    with _handle_errors():
        record = store.get_session(
            user_id=current_user.id,
            session_id=draft_id,
        )

        state = draft_service.confirm(
            _read_state(record),
            request,
        )

        updated_record = _persist_state(
            store=store,
            user_id=current_user.id,
            record=record,
            state=state,
            expected_version=request.expected_version,
        )

        return _build_response(updated_record)


@router.delete("/{draft_id}", status_code=204)
def delete_draft(
    draft_id: str,
    current_user: User = Depends(get_current_user),
    store: PMIDraftStore = Depends(get_pmi_draft_store),
) -> None:
    with _handle_errors():
        store.delete_session(
            user_id=current_user.id,
            session_id=draft_id,
        )