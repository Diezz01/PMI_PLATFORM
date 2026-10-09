from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

#those are contracts that allow the LLM to execute the function requeste dby the user in Natural langauge
# The operation could be:
#- request to calcultate PMI
#- request to consider only specific results
#There are also included the contract for the response related to the request

class PMICalculateRequest(BaseModel):
    input_data: dict[str, Any]

class PMIResultResponse(BaseModel):
    method_name: str
    pmi_value: float
    input_params: dict[str,Any]
    method_version: str

#keep track of the avilable response, in this way the user can select which method store and use for the median
class PMIAvailbaleResultsResponse(BaseModel):
    results: list[PMIResultResponse]

#Through the LLM the user select the method and they are incapsulated in this request for the backend
class PMIMedianRequest(BaseModel):
    selected_methods: list[str] = Field(min_lenght = 1)

class PMIMedianResponse(BaseModel):
    selected_results: list[PMIResultResponse]
    median_pmi: float

class PMISaveRequest(BaseModel):
    selected_methods: list[str] 
    #selected_methods: list[str] = Field(min_lenght = 1)

class PMISaveResponse(BaseModel):
    calculation_id: int
    saved_result: list[PMIResultResponse]
    median_pmi: float
    created_at: datetime