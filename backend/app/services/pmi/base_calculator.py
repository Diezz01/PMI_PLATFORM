from abc import ABC, abstractmethod
from typing import Any
from app.schemas.pmi_results import PMIMethodResult

#this is the abstraction of a general PMI method calculation that will be used in the application
class PMICalculator(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        pass

    @property
    @abstractmethod
    def required_parameters(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def method_kind(self) -> str:
        """henssge, biochemical or mock."""
        pass

    @abstractmethod
    def evaluate(
        self,
        parameters: dict[str, Any],
    ) -> PMIMethodResult:
        pass

    def calculate(self, parameters: dict[str, Any]) -> float:

        result = self.evaluate(parameters)

        if (
            result.calculation_status != "calculated"
            or result.pmi_hours is None
        ):
            raise ValueError(
                f"Method '{self.name}' did not produce a PMI value"
            )

        return result.pmi_hours
    