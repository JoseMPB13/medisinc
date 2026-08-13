"""
Clase Base Abstracta para los Proveedores de Inteligencia Artificial en MediSinc-IA.
Define la interfaz uniforme (patrón Adapter) que deben cumplir Gemini, Groq y OpenAI.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from app.schemas.triage import AIStructuredOutput


class BaseAIProvider(ABC):
    """
    Interfaz abstracta para adaptar diferentes LLMs al motor de triaje.
    """

    @abstractmethod
    async def process_triage(self, patient_data: Dict[str, Any]) -> AIStructuredOutput:
        """
        Procesa la información del paciente y genera un resumen estructurado estricto.

        Entrada: patient_data (dict) - Contiene síntomas, edad, género, datos estáticos y respuestas dinámicas.
        Salida: AIStructuredOutput - Instancia validada de Pydantic con la evaluación clínica.
        """
        pass

    def _build_prompt(self, patient_data: Dict[str, Any]) -> str:
        """
        Construye el Prompt estructurado con las instrucciones de triaje clínico.
        """
        return f"""
Eres un asistente médico experto en triaje clínico y evaluación inicial de pacientes.
Tu objetivo es analizar los datos capturados y generar un JSON estricto con el resumen clínico.

DATOS DEL PACIENTE:
- Nombre: {patient_data.get('patient_name')}
- Edad: {patient_data.get('age')} años
- Género: {patient_data.get('gender')}
- Síntoma Principal (Declaración directa del paciente): "{patient_data.get('raw_symptoms')}"
- Datos Fijos / Intensidad: {patient_data.get('static_data')}
- Respuestas a Preguntas Adaptativas: {patient_data.get('dynamic_answers')}

REGLAS DE PRIORIZACIÓN DE TRIAJE:
- RED (🔴 Urgente / Emergencia): Dolor torácico opresivo, dificultad respiratoria severa, pérdida de conciencia, convulsiones, sangrado incontrolable, fiebre alta en lactantes, alteración del habla o parálisis.
- YELLOW (🟡 Prioritario): Dolor moderado a severo (6-8/10) sin signos de colapso, fiebre persistente elevada, deshidratación moderada, trauma cerrado sin alteración hemodinámica.
- GREEN (🟢 No Urgente): Sintomatología leve (1-5/10), síntomas catarrales leves, erupciones cutáneas estables, consultas generales de seguimiento.

INSTRUCCIONES DE SALIDA:
Debes responder ÚNICAMENTE con un objeto JSON válido (sin texto antes ni después) con el siguiente formato estricto:

{{
  "sintomas_principales": ["lista de síntomas traducidos a terminología médica"],
  "duracion_e_intensidad": "resumen de evolución e intensidad",
  "factores_agravantes_antecedentes": ["factores o antecedentes identificados"],
  "senales_alerta_identificadas": ["banderas rojas o señales de alarma detectadas"],
  "prioridad_sugerida_ia": "RED" | "YELLOW" | "GREEN",
  "resumen_clinico_narrativo": "síntesis narrativa concisa de 2 a 3 oraciones redactada para rápida lectura médica",
  "informacion_faltante_critica": ["preguntas o datos clave no respondidos que el médico debe indagar"]
}}
"""
