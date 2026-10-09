from typing import Any

from app.services.pmi.orchestrator import PMIOrchestrator

class PMIService:

    def __init__(self):
        self.orchestartor = PMIOrchestrator()

    def calculate_all_methods(self, input_params: dict[str, Any]) -> list[dict[str, Any]]:
        return self.orchestartor.calculate(input_params)

    def calculate_median(self, results: list[dict[str, Any]], selected_methods: list[str] )-> float:

        selected_results = [res for res in results if res["method_name"] in selected_methods]

        if not selected_results:
            raise ValueError("No Valid PMI result were selected")

        return self.orchestartor.calculate_median(selected_results)
