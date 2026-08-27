"""
Adaptador de Proveedor de IA: Google Gemini.
Procesa las peticiones de triaje mediante la API de Google Generative AI con
manejo resiliente de excepciones, compatibilidad multi-modelo y fallback clínico inmediato.
"""

import json
import logging
from typing import Dict, Any, Optional
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

                # Modelos compatibles con modo de respuesta JSON
                for nombre_modelo in [
                    "gemini-1.5-flash-latest",
                    "gemini-1.5-flash",
                    "gemini-2.0-flash",
                    "gemini-1.5-pro",
                    "gemini-pro"
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
        respuestas_dinamicas: Optional[Dict[str, Any]] = None
    ) -> EsquemaSalidaEstructuradaIA:
        """
        Procesa los datos clínicos del paciente. Si la API de Gemini falla o no responde,
        activa inmediatamente el resumen estructurado de contingencia médica (< 10ms).
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

        if self.modelo:
            try:
                respuesta = self.modelo.generate_content(prompt)
                raw_json = respuesta.text.strip()
                parsed = json.loads(raw_json)
                return EsquemaSalidaEstructuradaIA(**parsed)
            except Exception as e:
                logger.warning(f"[ProveedorGemini] Fallo en llamada a Gemini API ({e}). Activando fallback clínico inmediato.")

        # Fallback de contingencia inmediato
        return self.generar_salida_contingencia(datos_paciente)


# -----------------------------------------------------------------------------
# ALIASES DE COMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
GeminiProvider = ProveedorGemini
