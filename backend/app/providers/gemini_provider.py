"""
Adaptador de Proveedor de IA: Google Gemini.
Procesa las peticiones de triaje mediante la API de Google Generative AI con
manejo resiliente de excepciones, compatibilidad multi-modelo y fallback clínico inmediato.
"""

import json
import logging
from typing import Dict, Any
from app.core.config import settings
from app.providers.base_provider import BaseAIProvider
from app.schemas.triage import AIStructuredOutput

logger = logging.getLogger(__name__)


class GeminiProvider(BaseAIProvider):
    """
    Implementación del proveedor Gemini de Google con múltiples modelos compatibles y fallback automático.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = None

        if self.api_key and "coloca_aqui" not in self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                
                # Intentar inicializar modelos compatibles con salida JSON
                for model_name in [
                    "gemini-1.5-flash-latest",
                    "gemini-1.5-flash",
                    "gemini-2.0-flash",
                    "gemini-1.5-pro",
                    "gemini-pro"
                ]:
                    try:
                        self.model = genai.GenerativeModel(
                            model_name=model_name,
                            generation_config={"response_mime_type": "application/json"}
                        )
                        break
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"[GeminiProvider] No se pudo inicializar Gemini Client ({e}). Operando en modo fallback.")
                self.model = None

    async def process_triage(self, patient_data: Dict[str, Any]) -> AIStructuredOutput:
        """
        Procesa los datos clínicos del paciente. Si la API remota falla o no está configurada,
        entrega inmediatamente el resumen estructurado de contingencia.
        """
        prompt = self._build_prompt(patient_data)

        if self.model:
            try:
                response = self.model.generate_content(prompt)
                raw_json = response.text.strip()
                parsed = json.loads(raw_json)
                return AIStructuredOutput(**parsed)
            except Exception as e:
                logger.warning(f"[GeminiProvider] Fallo en llamada a Gemini API ({e}). Activando fallback clínico inmediato.")

        # Fallback de contingencia instantáneo (<10ms)
        return self._generate_fallback(patient_data)

    def _generate_fallback(self, patient_data: Dict[str, Any]) -> AIStructuredOutput:
        """
        Genera una evaluación médica preliminar determinista y estructurada en caso de indisponibilidad del LLM.
        """
        symptoms = str(patient_data.get("raw_symptoms", "")).lower()
        intensity = 5
        try:
            intensity = int(patient_data.get("static_data", {}).get("intensidad", 5))
        except (ValueError, TypeError):
            intensity = 5

        # Banderas rojas básicas para fallback
        is_red = any(term in symptoms for term in [
            "pecho", "torac", "respirar", "aire", "desmayo", "convulsion", "sangrado", "conciencia", "chuy", "asfixia"
        ])

        if is_red:
            priority = "RED"
        elif intensity >= 7:
            priority = "YELLOW"
        else:
            priority = "GREEN"

        duracion_txt = str(patient_data.get("static_data", {}).get("duracion", "Evolución reciente"))
        edad = patient_data.get("age", "No especificada")
        nombre = patient_data.get("patient_name", "Paciente")

        return AIStructuredOutput(
            sintomas_principales=[patient_data.get("raw_symptoms", "Sintomatología general reportada")],
            duracion_e_intensidad=f"Tiempo de evolución: {duracion_txt} | Intensidad reportada: {intensity}/10",
            factores_agravantes_antecedentes=["Sin antecedentes críticos declarados en el pre-triaje"],
            senales_alerta_identificadas=["Síntoma evaluado bajo protocolo de contingencia clínica rápida (Gemini)"],
            prioridad_sugerida_ia=priority,
            resumen_clinico_narrativo=(
                f"{nombre} ({edad} años) refiere '{patient_data.get('raw_symptoms')}'. "
                f"Cuadro de intensidad {intensity}/10 con {duracion_txt}. "
                f"Evaluación preliminar generada por el motor de contingencia clínica."
            ),
            informacion_faltante_critica=[
                "Control de signos vitales (presión arterial, SpO2, frecuencia cardíaca)",
                "Alergias medicamentosas y antecedentes patológicos familiares"
            ]
        )
