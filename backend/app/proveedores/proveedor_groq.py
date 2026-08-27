"""
Adaptador de Proveedor de IA: Groq Cloud (Llama 3).
Procesa peticiones de triaje mediante la API de inferencia ultra-rápida de Groq
con formato de respuesta JSON forzado y validación estricta en Pydantic.
"""

import json
import logging
from typing import Dict, Any, Optional
from app.core.config import settings
from app.proveedores.proveedor_base import ProveedorIABase
from app.esquemas.triaje import EsquemaSalidaEstructuradaIA

logger = logging.getLogger(__name__)


class ProveedorGroq(ProveedorIABase):
    """
    Implementación del proveedor Groq para modelos de la familia Llama 3.
    """

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.cliente = None

        if self.api_key and "coloca_aqui" not in self.api_key:
            try:
                from groq import Groq
                self.cliente = Groq(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"[ProveedorGroq] Error al inicializar cliente Groq ({e}). Operando en contingencia.")
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
        Procesa el resumen clínico enviando el prompt estructurado a Groq Cloud con JSON Mode.
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
                chat_completion = self.cliente.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un asistente médico experto en triaje clínico. Responde estrictamente en formato JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    model="llama3-70b-8192",
                    response_format={"type": "json_object"}
                )
                raw_json = chat_completion.choices[0].message.content.strip()
                parsed = json.loads(raw_json)
                return EsquemaSalidaEstructuradaIA(**parsed)
            except Exception as e:
                logger.warning(f"[ProveedorGroq] Error en llamada a Groq API ({e}). Activando fallback clínico.")

        # Fallback de contingencia
        return self.generar_salida_contingencia(datos_paciente)


# -----------------------------------------------------------------------------
# ALIASES DE COMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
GroqProvider = ProveedorGroq
