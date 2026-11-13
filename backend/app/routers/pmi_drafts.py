from contextlib import contextmanager
from sqlalchemy.orm import Session
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
from app.database import get_db
from app.routers.pmi import _calculate_and_store_pmi
from app.schemas.pmi import PMICalculateRequest, PMICalculateResponse
from app.schemas.pmi_draft import PMIDraftCalculateRequest
from app.services.pmi.session_store import (
    PMISessionStore,
    get_pmi_session_store,
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
        # Share the chat lock so an active turn cannot recreate deleted history.
        lock = store.client.lock(
            f"pmi:chat-lock:{current_user.id}:{draft_id}",
            timeout=30,
            blocking=False,
        )
        if not lock.acquire(blocking=False):
            raise HTTPException(status_code=409, detail="Wait for the current reply before deleting the chat.")
        try:
            store.delete_session(
                user_id=current_user.id,
                session_id=draft_id,
            )
            store.client.delete(f"pmi:chat:{current_user.id}:{draft_id}")
        finally:
            if lock.owned():
                lock.release()

@router.post(
    "/{draft_id}/calculate",
    response_model=PMICalculateResponse,
    status_code=201,
)
def calculate_from_draft(
    draft_id: str,
    request: PMIDraftCalculateRequest,
    current_user: User = Depends(get_current_user),
    store: PMIDraftStore = Depends(get_pmi_draft_store),
    session_store: PMISessionStore = Depends(get_pmi_session_store),
    db: Session = Depends(get_db),
) -> PMICalculateResponse:
    with _handle_errors():
        record = store.get_session(
            user_id=current_user.id,
            session_id=draft_id,
        )

        state = _read_state(record)

        if state.version != request.expected_version:
            raise PMIDraftConflict(
                "La bozza è cambiata. Ricaricala prima del calcolo."
            )

        # Rifiuta le bozze non confermate e restituisce
        # una copia validata dei dati da calcolare.
        calculation_input = draft_service.get_calculation_input(state)

    return _calculate_and_store_pmi(
        request=PMICalculateRequest(input_data=calculation_input),
        current_user=current_user,
        session_store=session_store,
        db=db,
        source_draft={
            "draft_id": draft_id,
            "version": state.version,
        },
    )
