from app.services.pmi.base_calculator import PMICalculator
from app.services.pmi.mock import MockPMICalculator
from app.services.pmi.henssge import HenssgePMICalculator
from app.services.pmi.sturner import SturnerPMICalculator
from app.services.pmi.coe import CoePMICalculator
from app.services.pmi.adjutantis import AdjutantisPMICalculator
from app.services.pmi.agrarwal import AgrarwalPMICalculator
from app.services.pmi.stephens import StephensPMICalculator
from app.services.pmi.madea import MadeaPMICalculator
from app.services.pmi.devenaux import DevenauxPMICalculator

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

registry.register(MockPMICalculator())
registry.register(HenssgePMICalculator())
registry.register(SturnerPMICalculator())
registry.register(CoePMICalculator())
registry.register(AdjutantisPMICalculator())
registry.register(AgrarwalPMICalculator())
registry.register(StephensPMICalculator())
registry.register(MadeaPMICalculator())
registry.register(DevenauxPMICalculator())
