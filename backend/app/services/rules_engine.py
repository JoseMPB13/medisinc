"""
Módulo de enlace de compatibilidad hacia motor_reglas.py.
"""

from app.servicios.motor_reglas import (
    normalizar_texto,
    normalize_text,
    BANDERAS_ROJAS_CRITICAS,
    CRITICAL_RED_FLAGS,
    evaluar_sobreescrituras_seguridad,
    evaluate_safety_overrides
)

__all__ = [
    "normalizar_texto",
    "normalize_text",
    "BANDERAS_ROJAS_CRITICAS",
    "CRITICAL_RED_FLAGS",
    "evaluar_sobreescrituras_seguridad",
    "evaluate_safety_overrides"
]
