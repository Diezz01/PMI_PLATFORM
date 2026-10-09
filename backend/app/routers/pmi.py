from fastapi import APIRouter, HTTPException, Depends

from app.configs.dependencies import get_current_user
from app.models.user import User
from app.schemas.pmi import PMICalculateRequest, PMIAvailbaleResultsResponse
from app.services.pmi.pmi_service import PMIService

router = APIRouter(
    prefix="/pmi",
    tags=["PMI"],
    dependencies=[Depends(get_current_user)]
)

pmi_service = PMIService()

@router.post("/calculate", response_model= PMIAvailbaleResultsResponse)
def calculate_pmi(request: PMICalculateRequest)-> PMIAvailbaleResultsResponse:
    try:
        results = pmi_service.calculate_all_methods(request.input_data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return PMIAvailbaleResultsResponse(results=results)