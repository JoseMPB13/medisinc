"""
Motor Determinista de Reglas Duras de Seguridad Clínica (Safety Overrides Engine).
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

    Entrada:
        texto (str): Cadena de texto a normalizar.
    Salida:
        str: Texto limpio en minúsculas y sin acentos.
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


# Lista exhaustiva de señales de peligro vital (Banderas Rojas y Modismos Cruceños/Bolivianos)
BANDERAS_ROJAS_CRITICAS = [
    # 1. Emergencias Cardiológicas y Torácicas
    "dolor de pecho",
    "dolor toracico",
    "opresion en el pecho",
    "opresion precordial",
    "dolor precordial",
    "punzada en el pecho",
    "dolor irradiado al brazo",
    "dolor en el brazo izquierdo",
    "palpitaciones severas",

    # 2. Emergencias Respiratorias
    "dificultad para respirar",
    "dificultad respiratoria",
    "falta de aire",
    "disnea",
    "asfixia",
    "ahogo",
    "sensacion de ahogo",
    "cianosis",
    "labios morados",

    # 3. Emergencias Neurológicas y Estado de Conciencia
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

    # 4. Hemorragias y Cuadros Abdominales Quirúrgicos
    "sangrado severo",
    "hemorragia",
    "vomito con sangre",
    "hematemesis",
    "sangrado incontrolable",
    "dolor en fosa iliaca derecha",
    "abdomen en tabla",
    "dolor abdominal insoportable",

    # 5. Modismos Populares Regionales de Santa Cruz de la Sierra y Bolivia
    "chuy",
    "chucho de frio",
    "chucho",
    "basca",
    "basca persistente",
    "estomago aventado",
    "empacho grave",
    "quebrantamiento de cuerpo",
    "cuerpo cortado",
    "dolor de tutuma",
    "retumbo en la cabeza",
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

    Soporta argumentos posicionales y nominales en español e inglés:
    (sintomas_brutos/raw_symptoms, edad/age, datos_estaticos/static_data, salida_ia/ai_output).
    """
    # Manejo flexible de parámetros español / inglés
    texto_sintomas = sintomas_brutos or kwargs.get("raw_symptoms") or ""
    edad_paciente = edad if edad is not None else kwargs.get("age", 0)
    datos_extra = datos_estaticos if datos_estaticos is not None else kwargs.get("static_data", {})
    resultado_ia = salida_ia if salida_ia is not None else kwargs.get("ai_output")

    sintomas_normalizados = normalizar_texto(texto_sintomas)

    # Extraer prioridad sugerida por la IA (compatible con dict o Pydantic model)
    prioridad_ia_original = ""
    if isinstance(resultado_ia, dict):
        prioridad_ia_original = str(resultado_ia.get("prioridad_sugerida_ia") or resultado_ia.get("prioridad_final") or "").upper()
    elif hasattr(resultado_ia, "prioridad_sugerida_ia"):
        prioridad_ia_original = str(resultado_ia.prioridad_sugerida_ia).upper()
    elif resultado_ia is not None:
        prioridad_ia_original = str(resultado_ia).upper()

    # Normalizar a estándar bilingüe
    prioridad_es_baja = prioridad_ia_original in ["GREEN", "VERDE", "YELLOW", "AMARILLO", ""]
    es_ingles = "GREEN" in prioridad_ia_original or "YELLOW" in prioridad_ia_original or "RED" in prioridad_ia_original or prioridad_ia_original == ""

    # 1. Regla Crítica: Banderas Rojas y Emergencias Médicas Inmediatas
    for bandera in BANDERAS_ROJAS_CRITICAS:
        if bandera in sintomas_normalizados:
            if prioridad_es_baja or prioridad_ia_original in ["RED", "ROJO"]:
                motivo = f"Regla de Seguridad: Detectado síntoma de riesgo crítico ({bandera.title()})"
                prioridad_retorno = "RED" if es_ingles else "ROJO"
                return prioridad_retorno, True, motivo

    # 2. Regla Crítica Pediatría: Lactantes menores de 1 año con síndrome febril o "chuy"
    if edad_paciente < 1:
        intensidad_normalizada = normalizar_texto(str(datos_extra.get("intensidad", "")))
        duracion_normalizada = normalizar_texto(str(datos_extra.get("duracion", "")))
        if (
            "fiebre" in sintomas_normalizados
            or "fiebre" in intensidad_normalizada
            or "fiebre" in duracion_normalizada
            or "chuy" in sintomas_normalizados
            or "temperatura" in sintomas_normalizados
        ):
            motivo = "Regla de Seguridad Pediatría: Lactante menor de 1 año con cuadro febril"
            prioridad_retorno = "RED" if es_ingles else "ROJO"
            return prioridad_retorno, True, motivo

    # 3. Regla Crítica por Dolor Severo / Extremo (Intensidad 9-10/10)
    try:
        valor_intensidad = int(datos_extra.get("intensidad", 0))
        if valor_intensidad >= 9 and prioridad_ia_original in ["GREEN", "VERDE"]:
            motivo = f"Regla de Seguridad: Intensidad severa de dolor ({valor_intensidad}/10)"
            prioridad_retorno = "YELLOW" if es_ingles else "AMARILLO"
            return prioridad_retorno, True, motivo
    except (ValueError, TypeError):
        pass

    # Si no aplica ninguna regla dura, se respeta la prioridad sugerida por la IA
    return prioridad_ia_original if prioridad_ia_original else "GREEN", False, None


# -----------------------------------------------------------------------------
# ALIASES DE COMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
normalize_text = normalizar_texto
CRITICAL_RED_FLAGS = BANDERAS_ROJAS_CRITICAS
evaluate_safety_overrides = evaluar_sobreescrituras_seguridad
