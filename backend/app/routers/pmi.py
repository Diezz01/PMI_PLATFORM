from fastapi import APIRouter, HTTPException

from app.schemas.pmi import PMICalculateRequest, PMIAvailbaleResultsResponse
from app.services.pmi.pmi_service import PMIService

router = APIRouter(
    prefix="/pmi",
    tags=["PMI"],
)

pmi_service = PMIService()

@router.post("/calculate", response_model= PMIAvailbaleResultsResponse)
def calculate_pmi(request: PMICalculateRequest)-> PMIAvailbaleResultsResponse:
    try:
        results = pmi_service.calculate_all_methods(request.input_data)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return PMIAvailbaleResultsResponse(results=results)