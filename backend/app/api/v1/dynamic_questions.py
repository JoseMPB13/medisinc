"""
Endpoint API para la Generación de Preguntas Dinámicas Adaptativas.
Genera de 2 a 3 preguntas de opción múltiple o respuesta corta orientadas a descartar banderas rojas clínicas.
"""

import json
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.providers.ai_factory import get_ai_provider

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/triage", tags=["Preguntas Dinámicas"])


class DynamicQuestionsInputSchema(BaseModel):
    """
    Esquema de entrada para solicitar preguntas adaptativas en el Paso 2 del formulario.
    """
    symptom: str = Field(..., description="Síntoma principal manifestado por el paciente", example="dolor de cabeza intenso")
    age: int = Field(..., ge=0, le=120, description="Edad del paciente", example=40)


class QuestionOption(BaseModel):
    label: str
    value: str


class DynamicQuestion(BaseModel):
    id: str
    question_text: str
    question_type: str = "multiple_choice"  # 'multiple_choice' o 'single_choice'
    options: List[QuestionOption]


class DynamicQuestionsResponseSchema(BaseModel):
    symptom_evaluated: str
    questions: List[DynamicQuestion]


@router.post(
    "/dynamic-questions",
    response_model=DynamicQuestionsResponseSchema,
    status_code=status.HTTP_200_OK
)
async def generate_dynamic_questions(payload: DynamicQuestionsInputSchema):
    """
    Genera de 2 a 3 preguntas de opción múltiple orientadas a indagar banderas rojas
    asociadas al síntoma principal ingresado.
    """
    try:
        symptom_lower = payload.symptom.lower().strip()
        age = payload.age

        # Banco de preguntas clínicas adaptativas para banderas rojas inmediatas
        if "cabeza" in symptom_lower or "cefalea" in symptom_lower:
            questions = [
                DynamicQuestion(
                    id="q_headache_type",
                    question_text="¿El dolor de cabeza comenzó de forma súbita e intensa (como un trueno)?",
                    question_type="single_choice",
                    options=[
                        QuestionOption(label="Sí, de golpe e insoportable", value="subito_intenso"),
                        QuestionOption(label="No, fue progresivo", value="progresivo")
                    ]
                ),
                DynamicQuestion(
                    id="q_headache_signs",
                    question_text="¿Presenta alguno de los siguientes síntomas acompañantes?",
                    question_type="multiple_choice",
                    options=[
                        QuestionOption(label="Rigidez en el cuello o fiebre alta", value="rigidez_fiebre"),
                        QuestionOption(label="Visión borrosa o alteración de la vista", value="vision_borrosa"),
                        QuestionOption(label="Debilidad en cara, brazo o dificultad para hablar", value="alteracion_neurologica"),
                        QuestionOption(label="Ninguno de los anteriores", value="ninguno")
                    ]
                )
            ]

        elif "pecho" in symptom_lower or "torac" in symptom_lower or "card" in symptom_lower:
            questions = [
                DynamicQuestion(
                    id="q_chest_type",
                    question_text="¿Cómo describirías la sensación del dolor en el pecho?",
                    question_type="single_choice",
                    options=[
                        QuestionOption(label="Sensación de opresión o peso pesado", value="opresivo"),
                        QuestionOption(label="Punzante al respirar hondo", value="punzante"),
                        QuestionOption(label="Ardor o acidez", value="ardor")
                    ]
                ),
                DynamicQuestion(
                    id="q_chest_radiation",
                    question_text="¿El dolor se extiende hacia otra zona del cuerpo?",
                    question_type="multiple_choice",
                    options=[
                        QuestionOption(label="Hacia brazo izquierdo, cuello o mandíbula", value="irradiado_brazo"),
                        QuestionOption(label="Hacia la espalda", value="irradiado_espalda"),
                        QuestionOption(label="Acompañado de sudor frío y náuseas", value="sudor_frio"),
                        QuestionOption(label="No se extiende a ningún lado", value="localizado")
                    ]
                )
            ]

        elif "estomago" in symptom_lower or "abdom" in symptom_lower or "barriga" in symptom_lower:
            questions = [
                DynamicQuestion(
                    id="q_abdo_loc",
                    question_text="¿En qué zona del abdomen sientes mayor dolor?",
                    question_type="single_choice",
                    options=[
                        QuestionOption(label="En la parte inferior derecha", value="fosa_iliaca_derecha"),
                        QuestionOption(label="En la boca del estómago", value="epigastrio"),
                        QuestionOption(label="En todo el abdomen de forma difusa", value="difuso")
                    ]
                ),
                DynamicQuestion(
                    id="q_abdo_signs",
                    question_text="¿Presentas alguno de estos signos adicionales?",
                    question_type="multiple_choice",
                    options=[
                        QuestionOption(label="Fiebre o vómitos persistentes", value="fiebre_vomito"),
                        QuestionOption(label="Imposibilidad de comer o tolerar líquidos", value="intolerancia_oral"),
                        QuestionOption(label="Deposiciones negras o con sangre", value="sangre_heces"),
                        QuestionOption(label="Ninguno", value="ninguno")
                    ]
                )
            ]

        else:
            # Generación genérica de descarte de síntomas generales
            questions = [
                DynamicQuestion(
                    id="q_gen_duration",
                    question_text="¿Con qué rapidez aparecieron las molestias?",
                    question_type="single_choice",
                    options=[
                        QuestionOption(label="Menos de 24 horas", value="agudo"),
                        QuestionOption(label="De 1 a 3 días", value="subagudo"),
                        QuestionOption(label="Más de 1 semana", value="cronico")
                    ]
                ),
                DynamicQuestion(
                    id="q_gen_redflags",
                    question_text="¿Presenta alguna de estas señales de alerta?",
                    question_type="multiple_choice",
                    options=[
                        QuestionOption(label="Dificultad para respirar o falta de aire", value="disnea"),
                        QuestionOption(label="Fiebre mayor a 38.5 °C", value="fiebre_alta"),
                        QuestionOption(label="Sensación de mareo o desmayo", value="mareo_syncope"),
                        QuestionOption(label="Ninguna de las anteriores", value="ninguna")
                    ]
                )
            ]

        return DynamicQuestionsResponseSchema(
            symptom_evaluated=payload.symptom,
            questions=questions
        )

    except Exception as e:
        logger.error(f"Error al generar preguntas dinámicas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar preguntas adaptativas: {str(e)}"
        )
