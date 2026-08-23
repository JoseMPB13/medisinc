"""
Motor de Reglas Duras de Seguridad de Triaje (Safety Overrides Engine).
Evalúa de manera determinista los síntomas y datos del paciente para prevenir que
cuadros críticos categorizados erróneamente por la IA ingresen como prioridad Verde o Amarilla.
Soporta normalización diacrítica (remoción de tildes) y modismos cruceños/bolivianos.
"""

import unicodedata
from typing import Tuple, Optional, Dict, Any
from app.schemas.triage import AIStructuredOutput


def normalize_text(text: str) -> str:
    """
    Normaliza texto removiendo acentos, tildes, caracteres diacríticos y espacios sobrantes.
    Convierte a minúsculas para matching determinista.

    Entrada: text (str) - Texto a normalizar.
    Salida: str - Texto limpio en minúsculas y sin acentos.
    """
    if not text:
        return ""
    return (
        unicodedata.normalize("NFKD", str(text))
        .encode("ASCII", "ignore")
        .decode("utf-8")
        .lower()
        .strip()
    )


# Términos y frases de alerta crítica (Banderas Rojas normalizadas y modismos cruceños)
CRITICAL_RED_FLAGS = [
    # Emergencia cardiológica y torácica
    "dolor de pecho",
    "dolor toracico",
    "opresion en el pecho",
    "opresion precordial",
    "dolor precordial",
    "punzada en el pecho",
    # Emergencia respiratoria
    "dificultad para respirar",
    "dificultad respiratoria",
    "falta de aire",
    "disnea",
    "asfixia",
    "ahogo",
    # Emergencia neurológica y estado de conciencia
    "perdida de conocimiento",
    "perdida de conciencia",
    "desmayo",
    "syncope",
    "sincope",
    "convulsion",
    "convulsiones",
    "paralisis",
    "asimetria facial",
    "alteracion del habla",
    "perdida de fuerza",
    # Hemorragias y shock
    "sangrado severo",
    "hemorragia",
    "vomito con sangre",
    "sangrado incontrolable",
    # Modismos regionales de Santa Cruz de la Sierra / Bolivia
    "chuy",
    "chucho de frio",
    "basca",
    "basca persistente",
    "estomago aventado",
    "empacho grave",
    "quebrantamiento de cuerpo",
    "dolor de tutuma",
]


def evaluate_safety_overrides(
    raw_symptoms: str,
    age: int,
    static_data: Dict[str, Any],
    ai_output: AIStructuredOutput
) -> Tuple[str, bool, Optional[str]]:
    """
    Analiza los síntomas y evalúa si se debe sobreescribir la prioridad propuesta por la IA.

    Entrada:
        raw_symptoms (str) - Texto libre del síntoma expresado por el paciente.
        age (int) - Edad del paciente en años.
        static_data (dict) - Datos adicionales (ej. intensidad, tiempo de evolución).
        ai_output (AIStructuredOutput) - Resultado preliminar estructurado generado por la IA.

    Salida:
        Tuple[str, bool, Optional[str]] - (prioridad_final, override_applied, override_reason)
    """
    symptoms_normalized = normalize_text(raw_symptoms)
    ai_priority = ai_output.prioridad_sugerida_ia.upper()

    # 1. Regla Crítica: Banderas Rojas y Emergencias
    for flag in CRITICAL_RED_FLAGS:
        if flag in symptoms_normalized:
            if ai_priority in ["GREEN", "YELLOW"]:
                reason = f"Regla de Seguridad: Detectado síntoma de riesgo crítico ({flag.title()})"
                return "RED", True, reason

    # 2. Regla Crítica Pediatría: Lactantes menores de 1 año con fiebre o "chuy"
    if age < 1:
        intensity_normalized = normalize_text(str(static_data.get("intensidad", "")))
        if (
            "fiebre" in symptoms_normalized
            or "fiebre" in intensity_normalized
            or "chuy" in symptoms_normalized
        ):
            if ai_priority in ["GREEN", "YELLOW"]:
                reason = "Regla de Seguridad Pediatría: Lactante menor de 1 año con cuadro febril"
                return "RED", True, reason

    # 3. Regla Crítica por Intensidad de Dolor Extremo (9-10/10)
    try:
        intensity_val = int(static_data.get("intensidad", 0))
        if intensity_val >= 9 and ai_priority == "GREEN":
            reason = f"Regla de Seguridad: Intensidad severa de dolor ({intensity_val}/10)"
            return "YELLOW", True, reason
    except (ValueError, TypeError):
        pass

    # Si no se activó ninguna regla de sobreescritura, se respeta la prioridad sugerida por la IA
    return ai_priority, False, None
