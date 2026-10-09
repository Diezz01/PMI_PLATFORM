from abc import ABC, abstractmethod
from typing import Any

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

    @abstractmethod
    def calculate(self, parameters: dict[str, Any]) -> float:
        pass
    