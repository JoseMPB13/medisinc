"""
Adaptador de Proveedor de IA: Groq (Llama 3).
Procesa las peticiones de triaje mediante la API ultra-rápida de Groq.
"""

import json
import logging
from typing import Dict, Any
from app.core.config import settings
from app.providers.base_provider import BaseAIProvider
from app.schemas.triage import AIStructuredOutput

logger = logging.getLogger(__name__)


class GroqProvider(BaseAIProvider):
    """
    Implementación del proveedor Groq (Llama 3).
    """

    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        if self.api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Error al inicializar cliente Groq: {e}")
                self.client = None
        else:
            self.client = None

    async def process_triage(self, patient_data: Dict[str, Any]) -> AIStructuredOutput:
        prompt = self._build_prompt(patient_data)

        if self.client:
            try:
                chat_completion = self.client.chat.completions.create(
                    messages=[
                        {
                            "role": "system",
                            "content": "Eres un asistente médico experto en triaje. Responde estrictamente en formato JSON."
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
                return AIStructuredOutput(**parsed)
            except Exception as e:
                logger.error(f"Error al invocar API de Groq: {e}")

        # Fallback de desarrollo si no hay API Key o falla la llamada
        return self._generate_fallback(patient_data)

    def _generate_fallback(self, patient_data: Dict[str, Any]) -> AIStructuredOutput:
        symptoms = patient_data.get('raw_symptoms', '').lower()
        is_red = any(term in symptoms for term in [
            "pecho", "respirar", "desmayo", "convulsion", "sangrado"
        ])
        priority = "RED" if is_red else "YELLOW"

        return AIStructuredOutput(
            sintomas_principales=[patient_data.get('raw_symptoms', 'Sintomatología general')],
            duracion_e_intensidad="Evolución reciente reportada",
            factores_agravantes_antecedentes=["Sin antecedentes críticos documentados"],
            senales_alerta_identificadas=["Resumen generado por proveedor de respaldo Groq"],
            prioridad_sugerida_ia=priority,
            resumen_clinico_narrativo=f"Paciente de {patient_data.get('age')} años refiere '{patient_data.get('raw_symptoms')}'. Procesado en contingencia Groq.",
            informacion_faltante_critica=["Examen físico presencial", "Saturación de oxígeno"]
        )
