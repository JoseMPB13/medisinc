"""
Pruebas Unitarias para Quick Wins de la Fase 1:
1. Validación de extracción y parsing resiliente de JSON para LLMs (extraer_json_seguro).
2. Validación de la caché en memoria con TTL para el catálogo de especialidades médicas.
"""

import pytest
import time
from app.core.utilidades_json import extraer_json_seguro
from app.api.v1.triaje import (
    obtener_catalogo_especialidades,
    invalidar_cache_catalogo,
    _CACHE_CATALOGO,
    _TTL_CACHE_CATALOGO
)


# =============================================================================
# 1. PRUEBAS PARA extraer_json_seguro
# =============================================================================

def test_extraer_json_puro():
    """Valida el parsing directo de un string JSON estándar."""
    json_crudo = '{"prioridad": "ROJO", "motivo": "Dolor precordial opresivo", "riesgo": 5}'
    resultado = extraer_json_seguro(json_crudo)
    assert isinstance(resultado, dict)
    assert resultado["prioridad"] == "ROJO"
    assert resultado["riesgo"] == 5


def test_extraer_json_con_markdown_codeblock():
    """Valida la extracción de JSON envuelto en bloques markdown ```json ... ```."""
    texto_llm = """
    Aquí está la evaluación estructurada del paciente:
    ```json
    {
        "prioridad_sugerida": "AMARILLO",
        "justificacion_clinica": "Fiebre persistente de 38.5C",
        "red_flags": ["Fiebre > 38.5"]
    }
    ```
    Espero que esta información sea de utilidad.
    """
    resultado = extraer_json_seguro(texto_llm)
    assert isinstance(resultado, dict)
    assert resultado["prioridad_sugerida"] == "AMARILLO"
    assert "Fiebre persistente de 38.5C" in resultado["justificacion_clinica"]
    assert len(resultado["red_flags"]) == 1


def test_extraer_json_con_texto_antes_y_despues_sin_markdown():
    """Valida la extracción de objeto JSON cuando el modelo genera texto antes y después sin fences."""
    texto_llm = """
    Hola, he analizado los síntomas. El resultado es:
    {"preguntas": [{"id": "p1", "pregunta": "¿Cuándo inició el dolor?", "tipo": "single_choice"}]}
    Favor revisar el protocolo.
    """
    resultado = extraer_json_seguro(texto_llm)
    assert isinstance(resultado, dict)
    assert "preguntas" in resultado
    assert len(resultado["preguntas"]) == 1
    assert resultado["preguntas"][0]["id"] == "p1"


def test_extraer_json_invalido_lanza_value_error():
    """Valida que entradas vacías o sin JSON estructurado lancen ValueError adecuadamente."""
    with pytest.raises(ValueError):
        extraer_json_seguro("")

    with pytest.raises(ValueError):
        extraer_json_seguro(None)

    with pytest.raises(ValueError):
        extraer_json_seguro("Este es un texto libre que no contiene llaves ni estructura de datos.")


# =============================================================================
# 2. PRUEBAS PARA CACHÉ EN MEMORIA CON TTL
# =============================================================================

@pytest.mark.asyncio
async def test_cache_catalogo_especialidades_hit_y_refresh():
    """
    Valida que el catálogo se guarde en caché en memoria dentro del TTL (60s)
    y que invalidar la caché o forzar refresco regenere los datos.
    """
    invalidar_cache_catalogo()

    # 1. Primera consulta: Generación inicial de caché
    catalogo_1 = await obtener_catalogo_especialidades()
    assert isinstance(catalogo_1, list)
    assert len(catalogo_1) >= 6

    # 2. Segunda consulta inmediata: Debe retornar el mismo objeto en memoria (Cache Hit)
    catalogo_2 = await obtener_catalogo_especialidades()
    assert catalogo_1 is catalogo_2  # Identidad de referencia en memoria

    # 3. Forzar refresco explícito: Debe reconstruir el catálogo
    catalogo_3 = await obtener_catalogo_especialidades(forzar_refresco=True)
    assert isinstance(catalogo_3, list)
    assert len(catalogo_3) >= 6

    # 4. Invalidación manual
    invalidar_cache_catalogo()
    catalogo_4 = await obtener_catalogo_especialidades()
    assert isinstance(catalogo_4, list)
