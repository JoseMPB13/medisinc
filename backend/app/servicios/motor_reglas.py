"""
Motor Determinista de Reglas Duras de Seguridad Clínica (Safety Overrides Engine).
Calibrado según la Escala de Triaje Manchester y RAC Adaptado.
Evalúa de manera rigurosa y determinista los síntomas, edad y datos del paciente para
prevenir que cuadros críticos subestimados por el modelo de IA ingresen con prioridad baja.
Soporta normalización diacrítica y modismos populares de Santa Cruz de la Sierra / Bolivia.
"""

import unicodedata
from typing import Tuple, Optional, Dict, Any


def normalizar_texto(texto: str) -> str:
    """
    Normaliza el texto de entrada removiendo acentos, tildes, caracteres diacríticos
    y espacios adicionales. Convierte a minúsculas para coincidencia determinista.
    """
    if not texto:
        return ""
    return (
        unicodedata.normalize("NFKD", str(texto))
        .encode("ASCII", "ignore")
        .decode("utf-8")
        .lower()
        .strip()
    )


# -----------------------------------------------------------------------------
# 1. BANDERAS ROJAS CRÍTICAS (Emergencia Vital / Nivel I-II -> ROJO)
# -----------------------------------------------------------------------------
BANDERAS_ROJAS_CRITICAS = [
    # Cardiológico / Torácico
    "dolor de pecho",
    "dolor toracico",
    "opresion en el pecho",
    "opresion precordial",
    "dolor precordial",
    "punzada en el pecho",
    "dolor irradiado al brazo",
    "dolor en el brazo izquierdo",
    "dolor irradiado a mandibula",
    "palpitaciones severas",

    # Respiratorio
    "dificultad para respirar",
    "dificultad respiratoria",
    "falta de aire",
    "disnea",
    "asfixia",
    "ahogo",
    "sensacion de ahogo",
    "cianosis",
    "labios morados",
    "estridor",

    # Neurológico / Conciencia
    "perdida de conocimiento",
    "perdida de conciencia",
    "desmayo",
    "syncope",
    "sincope",
    "convulsion",
    "convulsiones",
    "paralisis",
    "asimetria facial",
    "boca torcida",
    "alteracion del habla",
    "dificultad para hablar",
    "perdida de fuerza",
    "hemiplejia",
    "rigidez de nuca",
    "rigidez en el cuello",

    # Hemorrágico / Quirúrgico Agudo
    "sangrado severo",
    "hemorragia",
    "vomito con sangre",
    "hematemesis",
    "sangrado incontrolable",
    "herida penetrante",
    "arma blanca",
    "arma de fuego",
]

# -----------------------------------------------------------------------------
# 2. BANDERAS AMARILLAS (Urgencia Mayor / Riesgo Potencial -> AMARILLO)
# -----------------------------------------------------------------------------
BANDERAS_AMARILLAS_URGENCIA = [
    # Abdomen Agudo
    "dolor en fosa iliaca derecha",
    "fosa iliaca derecha",
    "apendicitis",
    "abdomen en tabla",
    "dolor abdominal insoportable",
    "vientre duro",

    # Digestivo / Deshidratación / Modismos
    "basca persistente",
    "vomitos constantes",
    "vomitos incoercibles",
    "intolerancia oral",
    "deshidratacion",
    "estomago aventado",
    "empacho grave",

    # Cefalea / Infeccioso severo
    "dolor de tutuma",
    "retumbo en la cabeza",
    "quebrantamiento de cuerpo",
    "cuerpo cortado",
]


def evaluar_sobreescrituras_seguridad(
    sintomas_brutos: Optional[str] = None,
    edad: Optional[int] = None,
    datos_estaticos: Optional[Dict[str, Any]] = None,
    salida_ia: Any = None,
    **kwargs
) -> Tuple[str, bool, Optional[str]]:
    """
    Analiza clínicamente los síntomas brutos y evalúa si se debe forzar una sobreescritura
    determinista sobre la prioridad propuesta por el modelo de IA.

    Alineado a la Escala Manchester:
    - ROJO (Emergencia Vital): Inestabilidad hemodinámica, dolor torácico, disnea, síncope, lactante febril.
    - AMARILLO (Urgencia Mayor): Dolor severo (>= 7/10), abdomen agudo, vómitos incoercibles.
    - VERDE (No Urgente): Cuadros leves o moderados sin compromiso vital.
    """
    texto_sintomas = sintomas_brutos or kwargs.get("raw_symptoms") or ""
    edad_paciente = edad if edad is not None else kwargs.get("age", 0)
    datos_extra = datos_estaticos if datos_estaticos is not None else kwargs.get("static_data", {})
    resultado_ia = salida_ia if salida_ia is not None else kwargs.get("ai_output")

    sintomas_normalizados = normalizar_texto(texto_sintomas)

    # Extraer prioridad sugerida por la IA
    prioridad_ia_original = ""
    if isinstance(resultado_ia, dict):
        prioridad_ia_original = str(resultado_ia.get("prioridad_sugerida_ia") or resultado_ia.get("prioridad_final") or "").upper()
    elif hasattr(resultado_ia, "prioridad_sugerida_ia"):
        prioridad_ia_original = str(resultado_ia.prioridad_sugerida_ia).upper()
    elif resultado_ia is not None:
        prioridad_ia_original = str(resultado_ia).upper()

    es_ingles = "GREEN" in prioridad_ia_original or "YELLOW" in prioridad_ia_original or "RED" in prioridad_ia_original or prioridad_ia_original == ""
    prioridad_es_verde = prioridad_ia_original in ["GREEN", "VERDE", ""]

    # =========================================================================
    # REGLA 1 (ROJO): Banderas Rojas Críticas Inmediatas
    # =========================================================================
    for bandera in BANDERAS_ROJAS_CRITICAS:
        if bandera in sintomas_normalizados:
            motivo = f"Regla de Seguridad (Escala Manchester Nivel I-II): Detectado síntoma de riesgo crítico ({bandera.title()})"
            prioridad_retorno = "RED" if es_ingles else "ROJO"
            return prioridad_retorno, True, motivo

    # =========================================================================
    # REGLA 2 (ROJO PEDIÁTRICO): Lactante menor de 1 año con síndrome febril o "chuy"
    # =========================================================================
    if edad_paciente < 1:
        intensidad_normalizada = normalizar_texto(str(datos_extra.get("intensidad", "")))
        duracion_normalizada = normalizar_texto(str(datos_extra.get("duracion", "")))
        if (
            "fiebre" in sintomas_normalizados
            or "fiebre" in intensidad_normalizada
            or "fiebre" in duracion_normalizada
            or "chuy" in sintomas_normalizados
            or "chucho" in sintomas_normalizados
            or "temperatura" in sintomas_normalizados
            or "calentura" in sintomas_normalizados
        ):
            motivo = "Regla de Seguridad Pediatría (Nivel I): Lactante menor de 1 año con cuadro febril / riesgo de sepsis"
            prioridad_retorno = "RED" if es_ingles else "ROJO"
            return prioridad_retorno, True, motivo

    # =========================================================================
    # REGLA 3 (AMARILLO / ROJO por Intensidad de Dolor >= 7/10)
    # =========================================================================
    try:
        valor_intensidad = int(datos_extra.get("intensidad", 0))
        if valor_intensidad >= 9 and prioridad_es_verde:
            motivo = f"Regla de Seguridad (Nivel II): Dolor severo agudo de intensidad crítica ({valor_intensidad}/10)"
            prioridad_retorno = "YELLOW" if es_ingles else "AMARILLO"
            return prioridad_retorno, True, motivo
        elif valor_intensidad >= 7 and prioridad_es_verde:
            motivo = f"Regla de Seguridad (Nivel III): Dolor agudo de intensidad moderada-alta ({valor_intensidad}/10)"
            prioridad_retorno = "YELLOW" if es_ingles else "AMARILLO"
            return prioridad_retorno, True, motivo
    except (ValueError, TypeError):
        pass

    # =========================================================================
    # REGLA 4 (AMARILLO): Banderas de Abdomen Agudo o Deshidratación Severa
    # =========================================================================
    for bandera in BANDERAS_AMARILLAS_URGENCIA:
        if bandera in sintomas_normalizados and prioridad_es_verde:
            motivo = f"Regla de Seguridad (Nivel III): Detectado signo de urgencia mayor ({bandera.title()})"
            prioridad_retorno = "YELLOW" if es_ingles else "AMARILLO"
            return prioridad_retorno, True, motivo

    # =========================================================================
    # REGLA 5: Respetar la evaluación emitida por el modelo de IA
    # =========================================================================
    prioridad_final = prioridad_ia_original if prioridad_ia_original else ("GREEN" if es_ingles else "VERDE")
    return prioridad_final, False, None


# -----------------------------------------------------------------------------
# ALIASES DE COMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
normalize_text = normalizar_texto
CRITICAL_RED_FLAGS = BANDERAS_ROJAS_CRITICAS
evaluate_safety_overrides = evaluar_sobreescrituras_seguridad
