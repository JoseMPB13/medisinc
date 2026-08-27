"""
Adaptador de Proveedor de IA: OpenAI (GPT-4o / GPT-4o-mini).
Procesa peticiones de triaje mediante la API de OpenAI con JSON Object Mode
y validación estricta en el esquema Pydantic EsquemaSalidaEstructuradaIA.
"""

import json
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.proveedores.proveedor_base import ProveedorIABase
from app.esquemas.triaje import EsquemaSalidaEstructuradaIA

logger = logging.getLogger(__name__)


class ProveedorOpenAI(ProveedorIABase):
    """
    Implementación del proveedor OpenAI para modelos GPT-4o y GPT-4o-mini.
    """

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.cliente = None

        if self.api_key and "coloca_aqui" not in self.api_key:
            try:
                from openai import OpenAI
                self.cliente = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"[ProveedorOpenAI] Error al inicializar cliente OpenAI ({e}). Operando en contingencia.")
                self.cliente = None

    async def estructurar_triaje(
        self,
        sintomas: str,
        edad: int,
        genero: str,
        datos_estaticos: Optional[Dict[str, Any]] = None,
        respuestas_dinamicas: Optional[Dict[str, Any]] = None
    ) -> EsquemaSalidaEstructuradaIA:
        """
        Procesa el resumen clínico enviando el prompt a OpenAI con response_format={"type": "json_object"}.
        """
        datos_paciente = {
            "sintomas_brutos": sintomas,
            "raw_symptoms": sintomas,
            "edad": edad,
            "age": edad,
            "genero": genero,
            "gender": genero,
            "datos_estaticos": datos_estaticos or {},
            "static_data": datos_estaticos or {},
            "respuestas_dinamicas": respuestas_dinamicas or {},
            "dynamic_answers": respuestas_dinamicas or {}
        }

        prompt = self.construir_prompt_triaje(datos_paciente)

        if self.cliente:
            try:
                respuesta = self.cliente.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un médico de emergencias y triaje. Responde estrictamente en formato JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"}
                )
                raw_json = respuesta.choices[0].message.content.strip()
                parsed = json.loads(raw_json)
                return EsquemaSalidaEstructuradaIA(**parsed)
            except Exception as e:
                logger.warning(f"[ProveedorOpenAI] Error en llamada a OpenAI API ({e}). Activando fallback clínico.")

        # Fallback de contingencia
        return self.generar_salida_contingencia(datos_paciente)


# -----------------------------------------------------------------------------
# ALIASES DE COMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
OpenAIProvider = ProveedorOpenAI
