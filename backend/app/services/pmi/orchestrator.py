from typing import Any
from statistics import median

from app.services.pmi.registry import registry

class PMIOrchestrator:

    def calculate(self, input_data: dict[str, Any]) -> dict[str,Any]:

        results = []

        for method in registry.get_all_calculators():
            required_parmas = (method.required_parameters)

            if not all (params in input_data for params in required_parmas):
                continue # if a requeste dparameter is not satified skip

            pmi_value = method.calculate(input_data)

            results.append({
                "method_name": method.name,
                "pmi_value": pmi_value,
                "input_params": input_data,
                "method_version":method.version
            })

        if not results:
            raise ValueError("No PMI calculation methoid is applicable with the provided parameters")

        return results

    def calculate_median(self, results: list[dict[str,Any]]) -> float:
        if not results:
            raise "No availbale results! At least one PMI is required"

        pmi_values = [res["pmi_value"] for res in results]

        return median(pmi_values) 