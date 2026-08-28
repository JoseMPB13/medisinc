"""
Adaptador de Proveedor de IA: Google Gemini.
Procesa las peticiones de triaje mediante la API de Google Generative AI con
manejo asíncrono no bloqueante (asyncio.to_thread), timeout estricto y fallback clínico inmediato (< 10ms).
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from app.core.config import settings
from app.proveedores.proveedor_base import ProveedorIABase
from app.esquemas.triaje import EsquemaSalidaEstructuradaIA

logger = logging.getLogger(__name__)


class ProveedorGemini(ProveedorIABase):
    """
    Implementación del proveedor Google Gemini con modelos optimizados y fallback automático.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.modelo = None

        if self.api_key and "coloca_aqui" not in self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)

                # Modelos oficiales compatibles con modo JSON en la API activa
                for nombre_modelo in [
                    "gemini-2.5-flash",
                    "gemini-flash-latest",
                    "gemini-2.5-flash-lite",
                    "gemini-2.5-pro",
                    "gemini-1.5-flash",
                    "gemini-pro-latest"
                ]:
                    try:
                        self.modelo = genai.GenerativeModel(
                            model_name=nombre_modelo,
                            generation_config={"response_mime_type": "application/json"}
                        )
                        break
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"[ProveedorGemini] No se pudo inicializar Gemini Client ({e}). Operando en modo contingencia.")
                self.modelo = None

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
        Procesa los datos clínicos del paciente. Si la API de Gemini falla, tarda más de 6s o no responde,
        activa inmediatamente el resumen estructurado de contingencia médica (< 10ms).
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

        if self.modelo:
            try:
                # Ejecutar llamada con timeout defensivo de 12s
                respuesta = await asyncio.wait_for(
                    asyncio.to_thread(self.modelo.generate_content, prompt),
                    timeout=12.0
                )
                raw_json = respuesta.text.strip()
                parsed = json.loads(raw_json)
                return EsquemaSalidaEstructuradaIA(**parsed)
            except Exception as e:
                logger.warning(f"[ProveedorGemini] Fallo o timeout en llamada a Gemini API ({type(e).__name__}: {e}). Activando fallback clínico inmediato.")

        # Fallback de contingencia inmediato
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
        Genera 2 a 3 preguntas dinámicas adaptativas aplicando semiología PQRST con fallback clínico no bloqueante.
        """
        if self.modelo:
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
                # Ejecutar con timeout de 10.0s
                respuesta = await asyncio.wait_for(
                    asyncio.to_thread(self.modelo.generate_content, prompt),
                    timeout=10.0
                )
                parsed = json.loads(respuesta.text.strip())
                lista = parsed if isinstance(parsed, list) else parsed.get("preguntas") or parsed.get("questions") or []
                if isinstance(lista, list) and len(lista) >= 2:
                    return lista
            except Exception as e:
                logger.warning(f"[ProveedorGemini] Error o timeout generando preguntas dinámicas ({type(e).__name__}: {e}). Activando fallback.")

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
GeminiProvider = ProveedorGemini
