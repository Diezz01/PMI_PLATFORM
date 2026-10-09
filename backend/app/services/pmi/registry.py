from app.services.pmi.base_calculator import PMICalculator
from app.services.pmi.mock import MockPMICalculator

class PMICalculatorsRegistry:
    
    def __init__(self):
        self._calculators: dict[str, PMICalculator] = {}

    def register(self, calculator: PMICalculator)-> None:
        self._calculators[calculator.name] = calculator

    def get_calculator(self, name: str) -> PMICalculator:
        if name not in self._calculators:
            raise ValueError(f"PMI calculator '{name}' not found!")

        return self._calculators[name]

    def get_all_calculators(self) -> list[PMICalculator]:
        return list(self._calculators.values())

registry = PMICalculatorsRegistry()

registry.register(
    MockPMICalculator()
)