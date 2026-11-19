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
from app.services.pmi.rognum_h_1991 import RognumH1991PMICalculator
from app.services.pmi.rognum_k_1991 import RognumK1991PMICalculator
from app.services.pmi.gamero import GameroPMICalculator
from app.services.pmi.madea_k_1994 import MadeaK1994PMICalculator
from app.services.pmi.madea_h_1994 import MadeaH1994PMICalculator
from app.services.pmi.james_k_1997 import JamesK1997PMICalculator
from app.services.pmi.james_h_1997 import JamesH1997PMICalculator
from app.services.pmi.munoz import MunozPMICalculator
from app.services.pmi.zhou import ZhouPMICalculator
from app.services.pmi.jashnani import JashnaniPMICalculator
from app.services.pmi.bortolotti import BortolottiPMICalculator
from app.services.pmi.salam import SalamPMICalculator
from app.services.pmi.mihailovic import MihailovicPMICalculator
from app.services.pmi.nermeen import NermeenPMICalculator
from app.services.pmi.siddamsetty import SiddamsettyPMICalculator
from app.services.pmi.tumram import TumramPMICalculator
from app.services.pmi.swain import SwainPMICalculator
from app.services.pmi.rognum_k_2016 import RognumK2016PMICalculator
from app.services.pmi.rognum_h_2016 import RognumH2016PMICalculator
from app.services.pmi.saldana import SaldanaPMICalculator
from app.services.pmi.palacio_k import PalacioKPMICalculator
from app.services.pmi.palacio_am import PalacioAmPMICalculator
from app.services.pmi.focardi import FocardiPMICalculator

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
registry.register(RognumH1991PMICalculator())
registry.register(RognumK1991PMICalculator())
registry.register(GameroPMICalculator())
registry.register(MadeaK1994PMICalculator())
registry.register(MadeaH1994PMICalculator())
registry.register(JamesK1997PMICalculator())
registry.register(JamesH1997PMICalculator())
registry.register(MunozPMICalculator())
registry.register(ZhouPMICalculator())
registry.register(JashnaniPMICalculator())
registry.register(BortolottiPMICalculator())
registry.register(SalamPMICalculator())
registry.register(MihailovicPMICalculator())
registry.register(NermeenPMICalculator())
registry.register(SiddamsettyPMICalculator())
registry.register(TumramPMICalculator())
registry.register(SwainPMICalculator())
registry.register(RognumK2016PMICalculator())
registry.register(RognumH2016PMICalculator())
registry.register(SaldanaPMICalculator())
registry.register(PalacioKPMICalculator())
registry.register(PalacioAmPMICalculator())
registry.register(FocardiPMICalculator())
