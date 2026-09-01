"""
Módulo Utilitario para Extracción y Parsing Resiliente de JSON emitido por Modelos LLM.
Limpia delimitadores Markdown, bloques de código, espacios y caracteres anómalos.
"""

import json
import logging
import re
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def extraer_json_seguro(texto_crudo: Optional[str]) -> Dict[str, Any]:
    """
    Extrae y parsea de forma segura un objeto JSON desde una respuesta de texto generada por LLMs.

    Maneja:
    1. Bloques de código Markdown (```json ... ``` o ``` ... ```).
    2. Texto conversacional introductorio o conclusivo alrededor del JSON.
    3. Espacios en blanco y saltos de línea irregulares.

    Entrada:
        texto_crudo (str): Cadena de texto recibida del proveedor de IA.

    Retorna:
        Dict[str, Any]: Diccionario con la estructura de datos parseada.

    Lanza:
        ValueError: Si el texto está vacío, no contiene un objeto JSON válido o no puede ser parseado.
    """
    if not texto_crudo or not isinstance(texto_crudo, str):
        raise ValueError("El contenido recibido para parsear como JSON está vacío o no es una cadena válida.")

    texto_limpio = texto_crudo.strip()

    # 1. Intento directo de deserialización
    try:
        resultado = json.loads(texto_limpio)
        if isinstance(resultado, dict):
            return resultado
    except Exception:
        pass

    # 2. Extracción de bloque de código Markdown (```json ... ``` o ``` ... ```)
    patron_markdown = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)
    match_md = patron_markdown.search(texto_limpio)
    if match_md:
        candidato_md = match_md.group(1).strip()
        try:
            resultado = json.loads(candidato_md)
            if isinstance(resultado, dict):
                return resultado
        except Exception:
            texto_limpio = candidato_md

    # 3. Búsqueda del objeto JSON delimitado por llaves exteriores { ... }
    inicio = texto_limpio.find("{")
    fin = texto_limpio.rfind("}")

    if inicio != -1 and fin != -1 and fin > inicio:
        candidato_llaves = texto_limpio[inicio:fin + 1].strip()
        try:
            resultado = json.loads(candidato_llaves)
            if isinstance(resultado, dict):
                return resultado
        except Exception as e:
            logger.warning(f"[utilidades_json] Falló el parsing del bloque entre llaves: {e}")

    # 4. Expresión regular como fallback para capturar estructuras balanceadas
    match_regex = re.search(r"(\{[\s\S]*\})", texto_limpio)
    if match_regex:
        candidato_regex = match_regex.group(1).strip()
        try:
            resultado = json.loads(candidato_regex)
            if isinstance(resultado, dict):
                return resultado
        except Exception as e:
            logger.error(f"[utilidades_json] Error crítico al deserializar JSON con regex: {e}")

    logger.error(f"[utilidades_json] No se pudo extraer un objeto JSON válido. Contenido recibido (primeros 200 chars): {texto_crudo[:200]}")
    raise ValueError("No se encontró una estructura JSON válida en el texto proporcionado.")
