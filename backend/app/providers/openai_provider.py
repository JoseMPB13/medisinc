"""
Adaptador de Proveedor de IA: OpenAI (GPT-4o / GPT-3.5-Turbo).
Procesa las peticiones de triaje mediante la API de OpenAI con JSON Mode.
"""

import json
import logging
from typing import Dict, Any
from app.core.config import settings
from app.providers.base_provider import BaseAIProvider
from app.schemas.triage import AIStructuredOutput

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """
    Implementación del proveedor OpenAI.
    """

    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        if self.api_key:
            try:
                from openai import OpenAI
                self.client = OpenAI(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Error al inicializar cliente OpenAI: {e}")
                self.client = None
        else:
            self.client = None

    async def process_triage(self, patient_data: Dict[str, Any]) -> AIStructuredOutput:
        prompt = self._build_prompt(patient_data)

        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un médico de triaje. Responde estrictamente en formato JSON."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    response_format={"type": "json_object"}
                )
                raw_json = response.choices[0].message.content.strip()
                parsed = json.loads(raw_json)
                return AIStructuredOutput(**parsed)
            except Exception as e:
                logger.error(f"Error al invocar API de OpenAI: {e}")

        # Fallback de desarrollo si no hay API Key o falla la llamada
        return self._generate_fallback(patient_data)

    def _generate_fallback(self, patient_data: Dict[str, Any]) -> AIStructuredOutput:
        symptoms = patient_data.get('raw_symptoms', '').lower()
        is_red = any(term in symptoms for term in [
            "pecho", "respirar", "desmayo", "convulsion", "sangrado"
        ])
        priority = "RED" if is_red else "GREEN"

        return AIStructuredOutput(
            sintomas_principales=[patient_data.get('raw_symptoms', 'Sintomatología general')],
            duracion_e_intensidad="Cuadro sintomático en evaluación",
            factores_agravantes_antecedentes=["Sin datos adicionales"],
            senales_alerta_identificadas=["Evaluación realizada mediante OpenAI Fallback"],
            prioridad_sugerida_ia=priority,
            resumen_clinico_narrativo=f"Paciente de {patient_data.get('age')} años refiere '{patient_data.get('raw_symptoms')}'. Resumen estructurado por OpenAI provider.",
            informacion_faltante_critica=["Presión arterial", "Frecuencia cardíaca"]
        )
