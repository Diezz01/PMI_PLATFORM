from typing import Any

from app.services.pmi.base_calculator import PMICalculator


class MockPMICalculator(PMICalculator):

    @property
    def name(self) -> str:
        return "mock"

    @property
    def version(self) -> str:
        return "0.1"

    @property
    def required_parameters(self) -> list[str]:
        return []

    def calculate(self, parameters: dict[str, Any]) -> float:
        return 0.0