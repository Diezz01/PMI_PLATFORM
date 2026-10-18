"""Numerical components for Henssge; not yet a registered PMI calculator.

Temperature quotient: Dani et al. (2023), equation (1),
https://doi.org/10.3390/diagnostics13071260.
"""
import math


INITIAL_BODY_TEMPERATURE_C = 37.2


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

    if ambient_temperature_c >= INITIAL_BODY_TEMPERATURE_C:
        raise ValueError("Ambient temperature must be below 37.2 C for the cooling model")
    if rectal_temperature_c > INITIAL_BODY_TEMPERATURE_C:
        raise ValueError("Rectal temperature must not exceed 37.2 C for the cooling model")
    if rectal_temperature_c <= ambient_temperature_c:
        raise ValueError("Rectal temperature must be strictly above ambient temperature")

    ratio = (rectal_temperature_c - ambient_temperature_c) / (
        INITIAL_BODY_TEMPERATURE_C - ambient_temperature_c
    )
    if not 0 < ratio <= 1:
        raise ValueError("Temperature ratio must be representable in the interval (0, 1]")
    return ratio
