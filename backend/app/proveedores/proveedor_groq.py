"""
Adaptador de Proveedor de IA: Groq Cloud (Llama 3 70B).
Implementa la interfaz ProveedorIABase utilizando modelos de inferencia ultra-rápida
de Groq con JSON Mode y ejecución asíncrona no bloqueante.
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.proveedores.proveedor_base import ProveedorIABase
from app.esquemas.triaje import EsquemaSalidaEstructuradaIA

logger = logging.getLogger(__name__)


class ProveedorGroq(ProveedorIABase):
    """
    Implementación del proveedor Groq Cloud con Llama 3 70B y modo JSON.
    """

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.cliente = None

        if self.api_key and "coloca_aqui" not in self.api_key:
            try:
                from groq import Groq
                self.cliente = Groq(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"[ProveedorGroq] No se pudo inicializar Groq Client ({e}). Operando en contingencia.")
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
        Procesa el resumen clínico enviando el prompt estructurado a Groq Cloud con JSON Mode.
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
                def llamar_groq():
                    return self.cliente.chat.completions.create(
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

                chat_completion = await asyncio.wait_for(
                    asyncio.to_thread(llamar_groq),
                    timeout=6.0
                )
                raw_json = chat_completion.choices[0].message.content.strip()
                parsed = json.loads(raw_json)
                return EsquemaSalidaEstructuradaIA(**parsed)
            except Exception as e:
                logger.warning(f"[ProveedorGroq] Error o timeout en llamada a Groq API ({e}). Activando fallback clínico.")

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
        Genera 2 a 3 preguntas adaptativas usando Groq Llama 3 con fallback semiológico no bloqueante.
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

                def llamar_groq_preguntas():
                    return self.cliente.chat.completions.create(
                        messages=[
                            {
                                "role": "system",
                                "content": "Eres un asistente médico en triaje. Genera un array JSON de 2 a 3 preguntas estructuradas."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        model="llama3-70b-8192",
                        response_format={"type": "json_object"}
                    )

                chat_completion = await asyncio.wait_for(
                    asyncio.to_thread(llamar_groq_preguntas),
                    timeout=5.5
                )
                raw_json = chat_completion.choices[0].message.content.strip()
                parsed = json.loads(raw_json)
                lista = parsed if isinstance(parsed, list) else parsed.get("preguntas") or parsed.get("questions") or []
                if isinstance(lista, list) and len(lista) >= 2:
                    return lista
            except Exception as e:
                logger.warning(f"[ProveedorGroq] Error o timeout generando preguntas en Groq ({e}). Activando fallback.")

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
GroqProvider = ProveedorGroq
