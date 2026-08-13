"""
Adaptador de Proveedor de IA: Google Gemini 1.5 Flash.
Procesa las peticiones de triaje mediante la API de Google Generative AI.
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
    Implementación del proveedor Gemini de Google.
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(
                    model_name="gemini-1.5-flash",
                    generation_config={"response_mime_type": "application/json"}
                )
            except Exception as e:
                logger.error(f"Error al inicializar Gemini Client: {e}")
                self.model = None
        else:
            self.model = None

    async def process_triage(self, patient_data: Dict[str, Any]) -> AIStructuredOutput:
        prompt = self._build_prompt(patient_data)

        if self.model:
            try:
                response = self.model.generate_content(prompt)
                raw_json = response.text.strip()
                parsed = json.loads(raw_json)
                return AIStructuredOutput(**parsed)
            except Exception as e:
                logger.error(f"Error al invocar API de Gemini: {e}")

        # Fallback de desarrollo si no hay API Key o falla la petición
        return self._generate_fallback(patient_data)

    def _generate_fallback(self, patient_data: Dict[str, Any]) -> AIStructuredOutput:
        symptoms = patient_data.get('raw_symptoms', '').lower()
        is_red = any(term in symptoms for term in [
            "pecho", "respirar", "desmayo", "convulsion", "sangrado", "conciencia"
        ])
        priority = "RED" if is_red else "GREEN"

        return AIStructuredOutput(
            sintomas_principales=[patient_data.get('raw_symptoms', 'Sintomatología general')],
            duracion_e_intensidad=str(patient_data.get('static_data', {}).get('duracion', 'No especificado')),
            factores_agravantes_antecedentes=["No reportados"],
            senales_alerta_identificadas=["Síntoma evaluado por modelo de contingencia (Gemini)"],
            prioridad_sugerida_ia=priority,
            resumen_clinico_narrativo=f"Paciente de {patient_data.get('age')} años consulta por '{patient_data.get('raw_symptoms')}'. Evaluación generada en modo fallback.",
            informacion_faltante_critica=["Constantes vitales completas", "Antecedentes de patología previa"]
        )
