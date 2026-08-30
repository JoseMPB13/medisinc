"""
Adaptador de Proveedor de IA: Google Gemini.
Procesa las peticiones de triaje mediante la API de Google Generative AI con
rotación resiliente de modelos ante cuotas 429 de Free Tier y fallback clínico inmediato (< 10ms).
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
    Implementación del proveedor Google Gemini con rotación automática de modelos
    y fallback clínico determinista ante saturación o agotamiento de cuota (429).
    """

    # Modelos oficiales ordenados por estabilidad, velocidad y alta cuota libre (1500 RPM)
    NOMBRES_MODELOS = [
        "gemini-flash-latest",
        "gemini-pro-latest",
        "gemini-flash-lite-latest",
        "gemini-2.5-flash"
    ]

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.modelos_disponibles: Dict[str, Any] = {}
        self.modelo = None

        if self.api_key and "coloca_aqui" not in self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)

                for nombre_modelo in self.NOMBRES_MODELOS:
                    try:
                        instancia = genai.GenerativeModel(
                            model_name=nombre_modelo,
                            generation_config={"response_mime_type": "application/json"}
                        )
                        self.modelos_disponibles[nombre_modelo] = instancia
                        if self.modelo is None:
                            self.modelo = instancia
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
        Procesa los datos clínicos del paciente rotando entre modelos si alguno agota su cuota 429.
        Si todos los modelos fallan, activa el fallback clínico determinista (< 10ms).
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

        # Iterar sobre los modelos disponibles en caso de 429 ResourceExhausted
        for nombre_modelo, mod in self.modelos_disponibles.items():
            try:
                respuesta = await asyncio.wait_for(
                    asyncio.to_thread(mod.generate_content, prompt),
                    timeout=25.0
                )
                raw_json = respuesta.text.strip()
                parsed = json.loads(raw_json)
                return EsquemaSalidaEstructuradaIA(**parsed)
            except Exception as e:
                logger.warning(f"[ProveedorGemini] Modelo {nombre_modelo} no disponible ({type(e).__name__}: {str(e)[:100]}). Intentando siguiente...")
                continue

        logger.warning("[ProveedorGemini] Todos los modelos de Gemini fallaron o agotaron cuota. Activando fallback clínico inmediato.")
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
        Genera 2 a 3 preguntas dinámicas adaptativas rotando entre modelos de Gemini ante cuotas 429.
        """
        prompt = self.construir_prompt_preguntas_dinamicas(
            sintomas=sintomas,
            edad=edad,
            genero=genero,
            especialidad_solicitada=especialidad_solicitada,
            alergias_medicamentosas=alergias_medicamentosas,
            medicacion_actual=medicacion_actual,
            enfermedades_base=enfermedades_base
        )

        for nombre_modelo, mod in self.modelos_disponibles.items():
            try:
                respuesta = await asyncio.wait_for(
                    asyncio.to_thread(mod.generate_content, prompt),
                    timeout=25.0
                )
                parsed = json.loads(respuesta.text.strip())
                lista = parsed if isinstance(parsed, list) else parsed.get("preguntas") or parsed.get("questions") or []
                if isinstance(lista, list) and len(lista) >= 2:
                    return lista
            except Exception as e:
                logger.warning(f"[ProveedorGemini] Modelo {nombre_modelo} falló en preguntas dinámicas ({type(e).__name__}: {str(e)[:100]}). Intentando siguiente...")
                continue

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
