import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response, Query
from redis.exceptions import RedisError
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from pydantic import ValidationError

from app.schemas.pmi_median import PMIMedianResult, PMIMedianSelection
from app.schemas.pmi_results import PMIMethodResult
from app.services.pmi.median_service import PMIMedianService
from app.database import get_db
from app.configs.dependencies import get_current_user
from app.models.user import User
from app.models.pmi_calculation import PMICalculation, PMIResult
from app.schemas.pmi import (
    PMICorrectiveFactorResponse,
    PMICorrectiveFactorsResponse,
    PMICalculateRequest,
    PMICalculateResponse,
    PMIMedianRequest,
    PMIMedianResponse,
    PMISessionsResponse,
    PMISessionSummary,
    PMIResultResponse,
    PMISaveRequest,
    PMISaveResponse,
    PMIHistoryItem,
    PMIHistoryResponse
)
from app.services.pmi.pmi_service import InvalidCorrectionFactor, PMIService
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
logger = logging.getLogger(__name__)

def _prepare_median_update(
    session: dict,
    request: PMIMedianRequest,
) -> tuple[PMIMedianResult, dict]:
    if session["version"] != request.expected_version:
        raise HTTPException(
            status_code=409,
            detail="La sessione è cambiata. Ricaricala prima di continuare.",
        )

    if session["status"] not in {"calculated", "median_ready"}:
        raise HTTPException(
            status_code=409,
            detail="Lo stato della sessione non permette di modificare la mediana.",
        )

    stored_results = session.get("evaluated_results")

    if stored_results is None:
        raise HTTPException(
            status_code=409,
            detail="Questa sessione usa il vecchio formato. Ripeti il calcolo.",
        )

    try:
        evaluated_results = [
            PMIMethodResult.model_validate(result)
            for result in stored_results
        ]
    except ValidationError:
        raise HTTPException(
            status_code=409,
            detail="Gli esiti della sessione non sono compatibili. Ripeti il calcolo.",
        ) from None

    selection = PMIMedianSelection(
        selected_method_ids=request.selected_method_ids,
        acknowledged_warning_method_ids=(
            request.acknowledged_warning_method_ids
        ),
    )

    try:
        median_result = PMIMedianService().calculate(
            evaluated_results,
            selection,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from None

    updates = {
        # Compatibilità temporanea con riepiloghi e salvataggio esistenti.
        "selected_median_methods": median_result.selected_method_ids,
        "median_pmi": median_result.pmi_hours,

        # Conserva anche le conferme esplicite degli avvisi.
        "median_result": median_result.model_dump(
            mode="json",
            exclude={"pmi_display"},
        ),

        "status": (
            "median_ready"
            if median_result.status == "calculated"
            else "calculated"
        ),
    }

    return median_result, updates

def _redis_unavailable() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="PMI temporary session storage is unavailable",
    )

def _format_pmi_hhmm(pmi_hours: float | None) -> str | None:
    if pmi_hours is None:
        return None

    sign = "-" if pmi_hours < 0 else ""
    total_minutes = int(abs(pmi_hours) * 60 + 0.5)
    hours, minutes = divmod(total_minutes, 60)
    return f"{sign}{hours:02d}:{minutes:02d}"


@router.get(
    "/correction-factors",
    response_model=PMICorrectiveFactorsResponse,
    summary="List correction factors and their descriptions",
)
def list_correction_factors(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PMICorrectiveFactorsResponse:
    factors = pmi_service.list_correction_factors(db=db)
    return PMICorrectiveFactorsResponse(
        correction_factors=[
            PMICorrectiveFactorResponse.model_validate(factor)
            for factor in factors
        ],
    )


@router.post(
    "/calculate",
    response_model=PMICalculateResponse,
    status_code=status.HTTP_201_CREATED
    )
def calculate_pmi(
    request: PMICalculateRequest,
    current_user: User = Depends(get_current_user),
    session_store: PMISessionStore = Depends(get_pmi_session_store),
    db: Session = Depends(get_db),
) -> PMICalculateResponse:
    input_data = request.input_data.model_dump(exclude_none=True)
    try:
        evaluated_results = pmi_service.evaluate_all_methods(input_data, db=db)

        # Formato temporaneo per gli endpoint esistenti.
        results = [
            {
                "method_name": result.method_id,
                "pmi_value": result.pmi_hours,
                "input_params": input_data,
                "method_version": result.method_version,
            }
            for result in evaluated_results
            if result.calculation_status == "calculated"
        ]

        stored_evaluated_results = [
            result.model_dump(
                mode="json",
                exclude={"applicability", "pmi_display"},
            )
            for result in evaluated_results
        ]
    except InvalidCorrectionFactor as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=[{
                "type": "value_error",
                "loc": ["body", "input_data", "correction_factor"],
                "msg": str(exc),
            }],
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    try:
        session = session_store.create_session(
            user_id=current_user.id,
            input_data=input_data,
            results=results,
            evaluated_results=stored_evaluated_results
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
        version=session["version"],
        evaluated_results=evaluated_results,
        results=[
            PMIResultResponse(
                method_name=result["method_name"],
                pmi_value=_format_pmi_hhmm(result["pmi_value"]),
                input_params=result["input_params"],
                method_version=result["method_version"],
            )
            for result in session["results"]
        ],
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
            version=session["version"],
            available_methods=[
                result["method_name"] for result in session["results"]
            ],
            median_pmi=_format_pmi_hhmm(session.get("median_pmi")),
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

    median_result, updates = _prepare_median_update(session, request)
    try:
        updated_session = session_store.update_session(
            user_id=current_user.id,
            session={**session, **updates},
            expected_version=request.expected_version,
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
        median=median_result,
        expires_at=updated_session["expires_at"],
        version=updated_session["version"],
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
        evaluation_snapshot=calculation.evaluation_snapshot,
        saved_results=[
            PMIResultResponse(
                method_name=result.method_name,
                pmi_value=_format_pmi_hhmm(result.pmi_value),
                input_params=result.parameters,
                method_version=result.method_version,
            )
            for result in calculation.results
        ],
        median_selected_methods=calculation.median_selected_methods,
        median_pmi=_format_pmi_hhmm(calculation.median_pmi),
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

    if session["status"] not in {"calculated", "median_ready"}:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This PMI session is not available for saving",
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
    median_pmi = session.get("median_pmi")

    median_selected_methods = (
        list(session.get("selected_median_methods", []))
        if median_pmi is not None
        else []
    )

    # La selezione per il salvataggio e quella per la mediana
    # rimangono indipendenti. Conserviamo i dettagli di entrambe.
    snapshot_method_ids = (
        set(request.selected_methods)
        | set(median_selected_methods)
    )

    stored_evaluated_results = session.get("evaluated_results")
    evaluation_snapshot = None

    if stored_evaluated_results is not None:
        evaluation_snapshot = {
            "schema_version": 1,
            "session_version": session["version"],
            "saved_method_ids": list(request.selected_methods),
            "evaluated_results": [
                result
                for result in stored_evaluated_results
                if result["method_id"] in snapshot_method_ids
            ],
            "median_result": session.get("median_result"),
        }

    calculation = PMICalculation(
        user_id=current_user.id,
        session_id=session_id,
        input_data=session["input_data"],
        median_pmi=median_pmi,
        median_selected_methods=median_selected_methods,
        evaluation_snapshot=evaluation_snapshot,
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

@router.get(
    "/history",
    response_model=PMIHistoryResponse,
)
def get_pmi_history(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> PMIHistoryResponse:
    user_filter = PMICalculation.user_id == current_user.id

    total = db.scalar(
        select(func.count())
        .select_from(PMICalculation)
        .where(user_filter)
    ) or 0

    calculations = db.scalars(
        select(PMICalculation)
        .options(selectinload(PMICalculation.results))
        .where(user_filter)
        .order_by(
            PMICalculation.created_at.desc(),
            PMICalculation.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    ).all()

    items = [
        PMIHistoryItem(
            calculation_id=calculation.id,
            input_data=calculation.input_data,
            median_selected_methods=calculation.median_selected_methods,
            median_pmi=_format_pmi_hhmm(calculation.median_pmi),
            evaluation_snapshot=calculation.evaluation_snapshot,
            saved_results=[
                PMIResultResponse(
                    method_name=result.method_name,
                    pmi_value=_format_pmi_hhmm(result.pmi_value),
                    input_params=result.parameters,
                    method_version=result.method_version,
                )
                for result in calculation.results
            ],
            created_at=calculation.created_at,
        )
        for calculation in calculations
    ]

    return PMIHistoryResponse(
        calculations=items,
        total=total,
        limit=limit,
        offset=offset,
    )

