"""Numerical components for Henssge; not yet a registered PMI calculator.

Temperature quotient: Dani et al. (2023), equation (1),
https://doi.org/10.3390/diagnostics13071260.
"""
import math
from typing import Any
from app.schemas.pmi_results import PMICheckResult, PMIMethodResult
from app.services.pmi.base_calculator import PMICalculator 

INITIAL_BODY_TEMPERATURE_C = 37.2
AMBIENT_TEMPERATURE_MODEL = 23.0
MASS_SCALE_FACTOR = -1.2815
ALLOMETRIC_MASS_EXPONENT = -0.625
ASYMPTOTIC_CONSTATNT = 0.0284
MAX_BRACKET_ITERATIONS = 64
MAX_SOLVER_ITERATIONS = 200


class HenssgeDomainError(ValueError):
    pass

class HenssgeInputError(ValueError):
    pass

class HenssgeConvergenceError(RuntimeError):
    pass


def calculate_temperature_ratio(
    rectal_temperature_c: float,
    ambient_temperature_c: float,
) -> float:
    """Return Q = (Tb - Ta) / (37.2 - Ta) for the cooling model.

    Temperatures are in Celsius; Q is dimensionless, not a PMI.
    Mathematical domain: Ta < Tb <= 37.2. The initial-temperature boundary
    returns 1; HTTP input limits remain the responsibility of HenssgeInput.
    Equality Tb == Ta is thermal equilibrium, not a finite cooling-time input.
    """
    for name, value in (
        ("rectal_temperature_c", rectal_temperature_c),
        ("ambient_temperature_c", ambient_temperature_c),
    ):
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} must be a finite number")
        if not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number")

    if rectal_temperature_c >= INITIAL_BODY_TEMPERATURE_C:
        raise ValueError("rectal Temperature is higher than 37.2, Henssge is not appliable. The death is too recent or instantaneous")
    if ambient_temperature_c >= INITIAL_BODY_TEMPERATURE_C:
        raise ValueError("Ambient temperature must be below 37.2 C for the cooling model")
    if rectal_temperature_c <= ambient_temperature_c:
        raise ValueError("Rectal temperature must be strictly above ambient temperature")

    ratio = (rectal_temperature_c - ambient_temperature_c) / (
        INITIAL_BODY_TEMPERATURE_C - ambient_temperature_c
    )
    if not math.isfinite(ratio) or not 0.0 < ratio < 1.0:
        raise HenssgeDomainError(
            "The cooling ratio must be representable strictly between 0 and 1"
        )

    return ratio


def hennsge_estimation(
    rectal_temperature_c: float,
    ambient_temperature_c: float,
    body_mass_kg: float,
    cf: float)-> float : 
    q = calculate_temperature_ratio(rectal_temperature_c, ambient_temperature_c)

    if body_mass_kg <= 0:
        raise HenssgeInputError("Body mass must be positive")

    if cf <= 0:
        raise HenssgeInputError("Correction factor must be positive")
    
    corrected_body_mass = body_mass_kg * cf

    if corrected_body_mass <= 0:
        raise HenssgeDomainError("Corrected body mass must be positive")

    b = MASS_SCALE_FACTOR * corrected_body_mass ** ALLOMETRIC_MASS_EXPONENT + ASYMPTOTIC_CONSTATNT

    t = 0
    if ambient_temperature_c <= AMBIENT_TEMPERATURE_MODEL:
        coefficient_a = 1.25
        second_coefficient = 0.25
        exponent_multiplier = 5.0
    else:
        coefficient_a = 1.11
        second_coefficient = 0.11
        exponent_multiplier = 10

    def residual(hours: float) -> float:
        predicted_ratio = (
            coefficient_a * math.exp(b * hours)
            - second_coefficient
            * math.exp(exponent_multiplier * b * hours)
        )
        return predicted_ratio - q


    lower = 0.0
    upper = 1.0

    for _ in range(MAX_BRACKET_ITERATIONS):
        if residual(upper) <= 0:
            break
        upper *= 2.0
    else:
        raise HenssgeConvergenceError("Could not bracket the numerical solution")

    result : PMIMethodResult = PMIMethodResult()
    for _ in range(MAX_SOLVER_ITERATIONS):
        midpoint = lower + (upper - lower) / 2.0
        error = residual(midpoint)

        if error == 0.0:
            return midpoint

        if upper - lower <= TIME_TOLERANCE_HOURS:
            return midpoint

        if midpoint == lower or midpoint == upper:
            raise HenssgeConvergenceError(
                "Floating-point precision prevents further convergence"
            )

        if error > 0:
            lower = midpoint
        else:
            upper = midpoint

    raise HenssgeConvergenceError(
        "The numerical solver exceeded its iteration limit"
    )

class HenssgePMICalculator(PMICalculator):
    @property
    def name(self)-> str:
        return "hennsge"

    @property
    def version(self) -> str:
        return "development-1"

    @property
    def method_kind(self) -> str:
        return "henssge"

    @property
    def required_parameters(self) -> list[str]:
        return [
            "rectal_temperature_c",
            "ambient_temperature_c",
            "body_mass_kg",
            "correction_factor",
        ]

    def _failure(
        self,
        calculation_status: str,
        check_id: str,
        message: str,
    ) -> PMIMethodResult:
        return PMIMethodResult(
            method_id=self.name,
            method_name="Henssge",
            method_version=self.version,
            method_kind=self.method_kind,
            calculation_status=calculation_status,
            pmi_hours=None,
            time_reference=None,
            checks=[
                PMICheckResult(
                    id=check_id,
                    outcome="failed",
                    message=message,
                )
            ],
        )

    def evaluate(
        self,
        parameters: dict[str, Any],
    ) -> PMIMethodResult:
        missing = [
            field
            for field in self.required_parameters
            if parameters.get(field) is None
        ]

        if missing:
            return self._failure(
                "missing_input",
                "required_parameters",
                "Missing required parameters: " + ", ".join(missing),
            )

        try:
            hours = hennsge_estimation(
                rectal_temperature_c=parameters["rectal_temperature_c"],
                ambient_temperature_c=parameters["ambient_temperature_c"],
                body_mass_kg=parameters["body_mass_kg"],
                correction_factor=parameters["correction_factor"],
            )
        except HenssgeInputError as exc:
            return self._failure(
                "invalid_input", "numeric_input", str(exc)
            )
        except HenssgeDomainError as exc:
            return self._failure(
                "invalid_domain", "cooling_domain", str(exc)
            )
        except HenssgeConvergenceError as exc:
            return self._failure(
                "error", "numerical_convergence", str(exc)
            )

        return PMIMethodResult(
            method_id=self.name,
            method_name="Henssge",
            method_version=self.version,
            method_kind=self.method_kind,
            calculation_status="calculated",
            pmi_hours=hours,
            time_reference="temperature_measurement",
            checks=[
                PMICheckResult(
                    id="numerical_solution",
                    outcome="passed",
                    message="The cooling equation was solved numerically.",
                ),
                PMICheckResult(
                    id="scientific_applicability",
                    outcome="unknown",
                    message=(
                        "Scientific applicability checks are not yet complete. "
                        "The supplied correction factor is applied directly "
                        "to body mass. Additional weight-dependent corrections "
                        "and uncertainty intervals are not implemented."
                    ),
                ),
            ],
        )