"""
Adaptador de Proveedor de IA: OpenAI (GPT-4o / GPT-4o-mini).
Procesa el resumen clínico y las preguntas de clarificación utilizando la API oficial
de OpenAI con salida estructurada en modo JSON y ejecución asíncrona no bloqueante.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.proveedores.proveedor_base import ProveedorIABase
from app.esquemas.triaje import EsquemaSalidaEstructuradaIA

logger = logging.getLogger(__name__)


class ProveedorOpenAI(ProveedorIABase):
    """
    Implementación del proveedor OpenAI con gpt-4o-mini y JSON Mode.
    """

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.cliente = None

        if self.api_key and "coloca_aqui" not in self.api_key:
            try:
                from openai import OpenAI
                self.cliente = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"[ProveedorOpenAI] No se pudo inicializar OpenAI Client ({e}). Operando en contingencia.")
                self.cliente = None

    async def estructurar_triaje(
        self,
        sintomas: str,
        edad: int,
        genero: str,
        datos_estaticos: Optional[Dict[str, Any]] = None,
        respuestas_dinamicas: Optional[Dict[str, Any]] = None,
        especialidad_solicitada: Optional[str] = "Medicina General",
        alergias_medicamentosas: Optional[str] = "Ninguna conocida",
        medicacion_actual: Optional[str] = "Ninguna",
        enfermedades_base: Optional[List[str]] = None,
        **kwargs
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
            "especialidad_solicitada": especialidad_solicitada or "Medicina General",
            "requested_specialty": especialidad_solicitada or "Medicina General",
            "alergias_medicamentosas": alergias_medicamentosas or "Ninguna conocida",
            "drug_allergies": alergias_medicamentosas or "Ninguna conocida",
            "medicacion_actual": medicacion_actual or "Ninguna",
            "current_medication": medicacion_actual or "Ninguna",
            "enfermedades_base": enfermedades_base or [],
            "base_diseases": enfermedades_base or [],
            "datos_estaticos": datos_estaticos or {},
            "static_data": datos_estaticos or {},
            "respuestas_dinamicas": respuestas_dinamicas or {},
            "dynamic_answers": respuestas_dinamicas or {}
        }

        prompt = self.construir_prompt_triaje(datos_paciente)

        if self.cliente:
            try:
                def llamar_openai():
                    return self.cliente.chat.completions.create(
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

                respuesta = await asyncio.wait_for(
                    asyncio.to_thread(llamar_openai),
                    timeout=6.0
                )
                raw_json = respuesta.choices[0].message.content.strip()
                parsed = json.loads(raw_json)
                return EsquemaSalidaEstructuradaIA(**parsed)
            except Exception as e:
                logger.warning(f"[ProveedorOpenAI] Error o timeout en llamada a OpenAI API ({e}). Activando fallback clínico.")

        # Fallback de contingencia
        return self.generar_salida_contingencia(datos_paciente)

    async def generar_preguntas_dinamicas(
        self,
        sintomas: str,
        edad: int,
        genero: str,
        especialidad_solicitada: str = "Medicina General",
        alergias_medicamentosas: str = "Ninguna conocida",
        medicacion_actual: str = "Ninguna",
        enfermedades_base: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Genera 2 a 3 preguntas adaptativas usando OpenAI GPT-4o-mini con fallback semiológico no bloqueante.
        """
        if self.cliente:
            try:
                prompt = self.construir_prompt_preguntas_dinamicas(
                    sintomas=sintomas,
                    edad=edad,
                    genero=genero,
                    especialidad_solicitada=especialidad_solicitada,
                    alergias_medicamentosas=alergias_medicamentosas,
                    medicacion_actual=medicacion_actual,
                    enfermedades_base=enfermedades_base
                )

                def llamar_openai_preguntas():
                    return self.cliente.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {
                                "role": "system",
                                "content": "Eres un asistente médico en triaje. Genera un JSON con una lista 'preguntas' de 2 a 3 preguntas."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        response_format={"type": "json_object"}
                    )

                respuesta = await asyncio.wait_for(
                    asyncio.to_thread(llamar_openai_preguntas),
                    timeout=5.5
                )
                raw_json = respuesta.choices[0].message.content.strip()
                parsed = json.loads(raw_json)
                lista = parsed if isinstance(parsed, list) else parsed.get("preguntas") or parsed.get("questions") or []
                if isinstance(lista, list) and len(lista) >= 2:
                    return lista
            except Exception as e:
                logger.warning(f"[ProveedorOpenAI] Error o timeout generando preguntas en OpenAI ({e}). Activando fallback.")

        return self.generar_preguntas_dinamicas_fallback(
            sintomas=sintomas,
            edad=edad,
            genero=genero,
            especialidad_solicitada=especialidad_solicitada,
            alergias_medicamentosas=alergias_medicamentosas,
            medicacion_actual=medicacion_actual,
            enfermedades_base=enfermedades_base
        )


# -----------------------------------------------------------------------------
# ALIASES DE COMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
OpenAIProvider = ProveedorOpenAI
