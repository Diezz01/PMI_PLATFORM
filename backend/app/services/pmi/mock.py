from typing import Any

from app.schemas.pmi_results import PMICheckResult, PMIMethodResult
from app.services.pmi.base_calculator import PMICalculator


class MockPMICalculator(PMICalculator): 
    @property
    def name(self) -> str:
        return "mock"

    @property
    def method_kind(self) -> str:
        return "mock"

    @property
    def version(self) -> str:
        return "development-1"

    @property
    def required_parameters(self) -> list[str]:
        return []

    def evaluate(
        self,
        parameters: dict[str, Any],
    ) -> PMIMethodResult:
        return PMIMethodResult(
            method_id=self.name,
            method_name="Mock - development only",
            method_version=self.version,
            method_kind=self.method_kind,
            calculation_status="calculated",
            pmi_hours=0.0,
            time_reference=None,
            checks=[
                PMICheckResult(
                    id="development_only",
                    outcome="unknown",
                    field=None,
                    message=(
                        "Synthetic development result. "
                        "No scientific formula or applicability "
                        "criteria have been evaluated."
                    ),
                )
            ],
        )