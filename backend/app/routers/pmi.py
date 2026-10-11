import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response
from redis.exceptions import RedisError

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.database import get_db

from app.configs.dependencies import get_current_user

from app.models.user import User
from app.models.pmi_calculation import PMICalculation, PMIResult

from app.schemas.pmi import (
    PMICalculateRequest,
    PMICalculateResponse,
    PMIMedianRequest,
    PMIMedianResponse,
    PMISessionsResponse,
    PMISessionSummary,
    PMIResultResponse,
    PMISaveRequest,
    PMISaveResponse
)

from app.services.pmi.pmi_service import PMIService

from app.services.pmi.session_store import (
    PMISessionConflict,
    PMISessionLimitReached,
    PMISessionNotFound,
    PMISessionStore,
    get_pmi_session_store,
)


router = APIRouter(
    prefix="/pmi",
    tags=["PMI"],
)

pmi_service = PMIService()

def _redis_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="PMI temporary session storage is unavailable",
    )


@router.post(
    "/calculate",
    response_model=PMICalculateResponse,
    status_code=status.HTTP_201_CREATED,
)
def calculate_pmi(
    request: PMICalculateRequest,
    current_user: User = Depends(get_current_user),
    session_store: PMISessionStore = Depends(get_pmi_session_store),
) -> PMICalculateResponse:
    try:
        results = pmi_service.calculate_all_methods(request.input_data)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    try:
        session = session_store.create_session(
            user_id=current_user.id,
            input_data=request.input_data,
            results=results,
        )
    except PMISessionLimitReached as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many open PMI calculations. Close one before starting another.",
        ) from exc
    except RedisError as exc:
        raise _redis_unavailable() from exc

    return PMICalculateResponse(
        session_id=session["session_id"],
        status=session["status"],
        expires_at=session["expires_at"],
        results=session["results"],
    )


@router.get(
    "/sessions",
    response_model=PMISessionsResponse,
)
def list_pmi_sessions(
    current_user: User = Depends(get_current_user),
    session_store: PMISessionStore = Depends(get_pmi_session_store),
) -> PMISessionsResponse:
    try:
        sessions = session_store.list_sessions(user_id=current_user.id)
    except RedisError as exc:
        raise _redis_unavailable() from exc

    summaries = [
        PMISessionSummary(
            session_id=session["session_id"],
            status=session["status"],
            created_at=session["created_at"],
            expires_at=session["expires_at"],
            available_methods=[
                result["method_name"] for result in session["results"]
            ],
            median_pmi=session["median_pmi"],
        )
        for session in sessions
    ]

    return PMISessionsResponse(sessions=summaries)


@router.post(
    "/sessions/{session_id}/median",
    response_model=PMIMedianResponse,
)
def calculate_session_median(
    session_id: str,
    request: PMIMedianRequest,
    current_user: User = Depends(get_current_user),
    session_store: PMISessionStore = Depends(get_pmi_session_store),
) -> PMIMedianResponse:
    try:
        session = session_store.get_session(
            user_id=current_user.id,
            session_id=session_id,
        )
    except PMISessionNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PMI calculation session not found or expired",
        ) from exc
    except RedisError as exc:
        raise _redis_unavailable() from exc

    if session["status"] not in {"calculated", "median_ready"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This PMI calculation is not available for median selection",
        )

    results_by_method = {
        result["method_name"]: result for result in session["results"]
    }
    unknown_methods = set(request.selected_methods) - set(results_by_method)

    if unknown_methods:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One or more selected methods are not available in this session",
        )

    selected_results = [
        results_by_method[method_name]
        for method_name in request.selected_methods
    ]

    try:
        median_pmi = pmi_service.calculate_median(
            session["results"],
            request.selected_methods,
        )

        expected_version = session["version"]
        session["selected_median_methods"] = request.selected_methods
        session["median_pmi"] = median_pmi
        session["status"] = "median_ready"

        updated_session = session_store.update_session(
            user_id=current_user.id,
            session=session,
            expected_version=expected_version,
        )
    except PMISessionNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PMI calculation session not found or expired",
        ) from exc
    except PMISessionConflict as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The PMI calculation changed concurrently. Reload it and try again.",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except RedisError as exc:
        raise _redis_unavailable() from exc

    return PMIMedianResponse(
        session_id=updated_session["session_id"],
        status=updated_session["status"],
        selected_methods=updated_session["selected_median_methods"],
        selected_results=selected_results,
        median_pmi=updated_session["median_pmi"],
        expires_at=updated_session["expires_at"],
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def close_pmi_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    session_store: PMISessionStore = Depends(get_pmi_session_store),
) -> None:
    try:
        session_store.delete_session(
            user_id=current_user.id,
            session_id=session_id,
        )
    except RedisError as exc:
        raise _redis_unavailable() from exc

logger = logging.getLogger(__name__)


def _find_saved_calculation(
    db: Session,
    *,
    user_id: int,
    session_id: str,
) -> PMICalculation | None:
    statement = (
        select(PMICalculation)
        .options(selectinload(PMICalculation.results))
        .where(
            PMICalculation.user_id == user_id,
            PMICalculation.session_id == session_id,
        )
    )
    return db.scalar(statement)


def _build_save_response(
    calculation: PMICalculation,
    *,
    session_id: str,
) -> PMISaveResponse:
    return PMISaveResponse(
        calculation_id=calculation.id,
        session_id=session_id,
        saved_results=[
            PMIResultResponse(
                method_name=result.method_name,
                pmi_value=result.pmi_value,
                input_params=result.parameters,
                method_version=result.method_version,
            )
            for result in calculation.results
        ],
        median_selected_methods=calculation.median_selected_methods,
        median_pmi=calculation.median_pmi,
        created_at=calculation.created_at,
    )


@router.post(
    "/sessions/{session_id}/save",
    response_model=PMISaveResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_pmi_session(
    session_id: str,
    request: PMISaveRequest,
    response: Response,
    current_user: User = Depends(get_current_user),
    session_store: PMISessionStore = Depends(get_pmi_session_store),
    db: Session = Depends(get_db),
) -> PMISaveResponse:
    #If the user repeat the same request after a timeout, the result is a record alredy created insted of create a duplicate 
    existing = _find_saved_calculation(
        db,
        user_id=current_user.id,
        session_id=session_id,
    )
    if existing:
        response.status_code = status.HTTP_200_OK
        return _build_save_response(existing, session_id=session_id)

    try:
        session = session_store.get_session(
            user_id=current_user.id,
            session_id=session_id,
        )
    except PMISessionNotFound as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="PMI calculation session not found or expired",
        ) from exc
    except RedisError as exc:
        raise _redis_unavailable() from exc

    if session["status"] != "median_ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Calculate the median before saving this PMI session",
        )

    results_by_method = {
        result["method_name"]: result
        for result in session["results"]
    }
    unknown_methods = set(request.selected_methods) - set(results_by_method)

    if unknown_methods:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="One or more selected methods are not available in this session",
        )

    saved_results = [
        results_by_method[method_name]
        for method_name in request.selected_methods
    ]

    calculation = PMICalculation(
        user_id=current_user.id,
        session_id=session_id,
        input_data=session["input_data"],
        median_pmi=session["median_pmi"],
        median_selected_methods=session["selected_median_methods"],
        results=[
            PMIResult(
                method_name=result["method_name"],
                pmi_value=result["pmi_value"],
                parameters=result["input_params"],
                method_version=result["method_version"],
            )
            for result in saved_results
        ],
    )

    try:
        db.add(calculation)
        db.commit()
        db.refresh(calculation)
    except IntegrityError as exc:
        db.rollback()

        existing = _find_saved_calculation(
            db,
            user_id=current_user.id,
            session_id=session_id,
        )
        if existing:
            response.status_code = status.HTTP_200_OK
            return _build_save_response(existing, session_id=session_id)

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This PMI session could not be saved",
        ) from exc
    except Exception:
        db.rollback()
        raise

    try:
        session_store.delete_session(
            user_id=current_user.id,
            session_id=session_id,
        )
    except RedisError:
        logger.warning(
            "Saved PMI calculation %s but could not remove temporary session",
            calculation.id,
        )

    return _build_save_response(calculation, session_id=session_id)