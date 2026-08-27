"""
Enrutador de Endpoints de Triaje Clínico API v1 en Español.
Maneja la recepción inmediata de datos del paciente, generación de preguntas dinámicas,
encolamiento asíncrono de IA, consulta de estado y búsqueda por código de acceso o CI.
"""

from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, status, BackgroundTasks, Query, Depends, Request
import logging

from app.core.seguridad import cifrar_ci, hashear_ci, generar_codigo_acceso
from app.core.limite_peticiones import verificar_limite_peticiones
from app.esquemas.triaje import (
    EsquemaEntradaPaciente,
    EsquemaRespuestaInmediataTriaje,
    EsquemaEntradaPreguntasDinamicas,
    EsquemaRespuestaPreguntasDinamicas,
    EsquemaItemPreguntaDinamica
)
from app.servicios.servicio_supabase import servicio_supabase
from app.services.queue_service import queue_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/triaje", tags=["Triaje Clínico"])


# =============================================================================
# 1. POST /procesar (y /process): Registro Público de Pre-Triaje
# =============================================================================
@router.post(
    "/procesar",
    response_model=EsquemaRespuestaInmediataTriaje,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verificar_limite_peticiones)],
    summary="Registrar Pre-Triaje de Paciente"
)
@router.post(
    "/process",
    response_model=EsquemaRespuestaInmediataTriaje,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verificar_limite_peticiones)],
    include_in_schema=False
)
async def procesar_triaje(
    entrada_paciente: EsquemaEntradaPaciente,
    background_tasks: BackgroundTasks
):
    """
    Endpoint Público de Ingreso de Paciente:
    1. Aplica Rate Limiting (5 solicitudes cada 5 minutos por IP).
    2. Genera código único alfanumérico (ej. MS-8X92K).
    3. Cifra el CI con AES-256 (Fernet) y calcula el hash ciego HMAC-SHA256 con Pepper.
    4. Persiste en registros_triaje con estado 'RECIBIDO' ('RECEIVED').
    5. Encola la tarea asíncrona para evaluación del modelo de IA y Safety Overrides.
    6. Retorna respuesta inmediata en < 15ms para renderizado del Código QR interactivo.
    """
    try:
        # Cifrado y Hashing de seguridad del Carnet de Identidad
        ci_cifrado = cifrar_ci(entrada_paciente.ci)
        ci_hasheado = hashear_ci(entrada_paciente.ci)
        codigo_acceso = generar_codigo_acceso()

        triaje_id = f"tr-{codigo_acceso.lower()}"

        datos_registro = {
            "id": triaje_id,
            "codigo_acceso": codigo_acceso,
            "access_code": codigo_acceso,
            "ci_hash": ci_hasheado,
            "ci_cifrado": ci_cifrado,
            "ci_encrypted": ci_cifrado,
            "nombre_paciente": entrada_paciente.nombre_paciente,
            "patient_name": entrada_paciente.nombre_paciente,
            "edad": entrada_paciente.edad,
            "age": entrada_paciente.edad,
            "genero": entrada_paciente.genero,
            "gender": entrada_paciente.genero,
            "sintomas_brutos": entrada_paciente.sintomas_brutos,
            "raw_symptoms": entrada_paciente.sintomas_brutos,
            "datos_estaticos": entrada_paciente.datos_estaticos,
            "static_data": entrada_paciente.datos_estaticos,
            "respuestas_dinamicas": entrada_paciente.respuestas_dinamicas,
            "dynamic_answers": entrada_paciente.respuestas_dinamicas,
            "estado": "RECIBIDO",
            "status": "RECEIVED",
            "prioridad_final": None
        }

        # Guardar registro inicial en Supabase / Base Local
        registro_guardado = servicio_supabase.crear_registro_triaje(datos_registro)
        id_guardado = registro_guardado.get("id", triaje_id)

        # Encolar tarea asíncrona de IA y motor de reglas
        payload_dict = entrada_paciente.model_dump()
        await queue_service.enqueue_triage_job(
            triage_id=id_guardado,
            patient_payload=payload_dict,
            background_tasks=background_tasks
        )

        return EsquemaRespuestaInmediataTriaje(
            triaje_id=id_guardado,
            triage_id=id_guardado,
            codigo_acceso=codigo_acceso,
            access_code=codigo_acceso,
            estado="RECEIVED",
            status="RECEIVED",
            nombre_paciente=entrada_paciente.nombre_paciente,
            patient_name=entrada_paciente.nombre_paciente,
            mensaje="Pre-triaje registrado exitosamente. Tu resumen clínico se encuentra en procesamiento.",
            message="Pre-triaje registrado exitosamente. Tu resumen clínico se encuentra en procesamiento.",
            creado_en=datetime.now(timezone.utc).isoformat(),
            created_at=datetime.now(timezone.utc).isoformat()
        )

    except Exception as e:
        logger.error(f"Error al procesar pre-triaje: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar el pre-triaje: {str(e)}"
        )


# =============================================================================
# 2. POST /preguntas-dinamicas (y /dynamic-questions): Clarificación Adaptativa
# =============================================================================
@router.post(
    "/preguntas-dinamicas",
    response_model=EsquemaRespuestaPreguntasDinamicas,
    status_code=status.HTTP_200_OK,
    summary="Generar Preguntas Adaptativas de Pre-Triaje"
)
@router.post(
    "/dynamic-questions",
    response_model=EsquemaRespuestaPreguntasDinamicas,
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
async def generar_preguntas_dinamicas_api(entrada: EsquemaEntradaPreguntasDinamicas):
    """
    Genera de 2 a 3 preguntas dinámicas orientadas a:
    1. Descartar banderas rojas y características específicas del padecimiento.
    2. Identificar antecedentes y enfermedades preexistentes (diabetes, hipertensión, asma, etc.).
    3. Conocer medicamentos habituales y tratamientos recientes.
    """
    try:
        sintoma_texto = (entrada.sintomas_brutos or entrada.sintoma or "").lower().strip()

        # Pregunta 1: Específica del síntoma o banderas rojas
        if "cabeza" in sintoma_texto or "cefalea" in sintoma_texto or "tutuma" in sintoma_texto:
            p1 = {
                "id": "q_headache_type",
                "pregunta": "¿El dolor de cabeza comenzó de forma súbita e intensa (como un trueno) o con visión borrosa?",
                "question_text": "¿El dolor de cabeza comenzó de forma súbita e intensa (como un trueno) o con visión borrosa?",
                "tipo_pregunta": "single_choice",
                "question_type": "single_choice",
                "opciones": [
                    {"etiqueta": "Sí, comenzó de golpe y con intensidad extrema", "label": "Sí, comenzó de golpe y con intensidad extrema", "valor": "subito_intenso", "value": "subito_intenso"},
                    {"etiqueta": "Acompañado de rigidez de cuello o fiebre alta", "label": "Acompañado de rigidez de cuello o fiebre alta", "valor": "rigidez_cuello", "value": "rigidez_cuello"},
                    {"etiqueta": "No, fue apareciendo de forma progresiva", "label": "No, fue apareciendo de forma progresiva", "valor": "progresivo", "value": "progresivo"}
                ]
            }
        elif "pecho" in sintoma_texto or "torac" in sintoma_texto or "card" in sintoma_texto or "palpita" in sintoma_texto:
            p1 = {
                "id": "q_chest_type",
                "pregunta": "¿Cómo describirías el dolor en el pecho y hacia dónde se extiende?",
                "question_text": "¿Cómo describirías el dolor en el pecho y hacia dónde se extiende?",
                "tipo_pregunta": "single_choice",
                "question_type": "single_choice",
                "opciones": [
                    {"etiqueta": "Opresión fuerte que va hacia el brazo izquierdo, cuello o mandíbula", "label": "Opresión fuerte que va hacia el brazo izquierdo, cuello o mandíbula", "valor": "irradiado_brazo_mandibula", "value": "irradiado_brazo_mandibula"},
                    {"etiqueta": "Punzante al respirar hondo o toser", "label": "Punzante al respirar hondo o toser", "valor": "punzante_pleuritico", "value": "punzante_pleuritico"},
                    {"etiqueta": "Ardor o molestia con acidez estomacal", "label": "Ardor o molestia con acidez estomacal", "valor": "ardor_reflujo", "value": "ardor_reflujo"}
                ]
            }
        elif "estomago" in sintoma_texto or "abdom" in sintoma_texto or "barriga" in sintoma_texto or "aventado" in sintoma_texto or "basca" in sintoma_texto:
            p1 = {
                "id": "q_abdo_loc",
                "pregunta": "¿En qué zona se concentra el dolor y presenta vómitos incontrolables?",
                "question_text": "¿En qué zona se concentra el dolor y presenta vómitos incontrolables?",
                "tipo_pregunta": "single_choice",
                "question_type": "single_choice",
                "opciones": [
                    {"etiqueta": "En la parte inferior derecha del abdomen (fosa ilíaca)", "label": "En la parte inferior derecha del abdomen (fosa ilíaca)", "valor": "fosa_iliaca_derecha", "value": "fosa_iliaca_derecha"},
                    {"etiqueta": "En la boca del estómago o dolor difuso con náuseas", "label": "En la boca del estómago o dolor difuso con náuseas", "valor": "epigastrio_nauseas", "value": "epigastrio_nauseas"},
                    {"etiqueta": "Vómitos frecuentes o imposibilidad de retener líquidos", "label": "Vómitos frecuentes o imposibilidad de retener líquidos", "valor": "vomitos_severos", "value": "vomitos_severos"}
                ]
            }
        elif "respir" in sintoma_texto or "aire" in sintoma_texto or "tos" in sintoma_texto or "ahog" in sintoma_texto:
            p1 = {
                "id": "q_resp_severity",
                "pregunta": "¿Tiene dificultad para respirar en reposo o silbidos en el pecho?",
                "question_text": "¿Tiene dificultad para respirar en reposo o silbidos en el pecho?",
                "tipo_pregunta": "single_choice",
                "question_type": "single_choice",
                "opciones": [
                    {"etiqueta": "Sí, me falta el aire incluso al estar sentado o hablar", "label": "Sí, me falta el aire incluso al estar sentado o hablar", "valor": "disnea_reposo", "value": "disnea_reposo"},
                    {"etiqueta": "Tengo tos persistente con silbidos en el pecho", "label": "Tengo tos persistente con silbidos en el pecho", "valor": "tos_sibilancias", "value": "tos_sibilancias"},
                    {"etiqueta": "Molestia leve solo al realizar esfuerzos físicos", "label": "Molestia leve solo al realizar esfuerzos físicos", "valor": "esfuerzo_leve", "value": "esfuerzo_leve"}
                ]
            }
        elif "fiebr" in sintoma_texto or "chuy" in sintoma_texto or "chucho" in sintoma_texto or "calentura" in sintoma_texto:
            p1 = {
                "id": "q_fever_signs",
                "pregunta": "¿Qué síntomas acompañan a la fiebre o escalofríos?",
                "question_text": "¿Qué síntomas acompañan a la fiebre o escalofríos?",
                "tipo_pregunta": "single_choice",
                "question_type": "single_choice",
                "opciones": [
                    {"etiqueta": "Fiebre alta (>38.5 °C) con quebrantamiento y dolor detrás de los ojos", "label": "Fiebre alta (>38.5 °C) con quebrantamiento y dolor detrás de los ojos", "valor": "fiebre_dengue_like", "value": "fiebre_dengue_like"},
                    {"etiqueta": "Escalofríos intensos con tos o dolor de garganta", "label": "Escalofríos intensos con tos o dolor de garganta", "valor": "fiebre_respiratoria", "value": "fiebre_respiratoria"},
                    {"etiqueta": "Fiebre moderada sin otros signos de alarma", "label": "Fiebre moderada sin otros signos de alarma", "valor": "febril_leve", "value": "febril_leve"}
                ]
            }
        else:
            p1 = {
                "id": "q_gen_evolution",
                "pregunta": "¿Cómo ha sido la evolución y rapidez de los síntomas?",
                "question_text": "¿Cómo ha sido la evolución y rapidez de los síntomas?",
                "tipo_pregunta": "single_choice",
                "question_type": "single_choice",
                "opciones": [
                    {"etiqueta": "Aparición repentina en las últimas horas", "label": "Aparición repentina en las últimas horas", "valor": "inicio_agudo", "value": "inicio_agudo"},
                    {"etiqueta": "Malestar progresivo de 1 a 3 días", "label": "Malestar progresivo de 1 a 3 días", "valor": "inicio_subagudo", "value": "inicio_subagudo"},
                    {"etiqueta": "Cuadro persistente desde hace más de una semana", "label": "Cuadro persistente desde hace más de una semana", "valor": "inicio_cronico", "value": "inicio_cronico"}
                ]
            }

        # Pregunta 2: Enfermedades previas / Comorbilidades
        p2 = {
            "id": "q_antecedentes_enfermedades",
            "pregunta": "¿Padece alguna enfermedad o condición médica previa relevante?",
            "question_text": "¿Padece alguna enfermedad o condición médica previa relevante?",
            "tipo_pregunta": "multiple_choice",
            "question_type": "multiple_choice",
            "opciones": [
                {"etiqueta": "Hipertensión arterial (presión alta)", "label": "Hipertensión arterial (presión alta)", "valor": "hipertension", "value": "hipertension"},
                {"etiqueta": "Diabetes mellitus (azúcar en sangre)", "label": "Diabetes mellitus (azúcar en sangre)", "valor": "diabetes", "value": "diabetes"},
                {"etiqueta": "Problemas del corazón / infarto previo", "label": "Problemas del corazón / infarto previo", "valor": "cardiopatia", "value": "cardiopatia"},
                {"etiqueta": "Asma, bronquitis crónica o EPOC", "label": "Asma, bronquitis crónica o EPOC", "valor": "asma_epoc", "value": "asma_epoc"},
                {"etiqueta": "Enfermedad renal o hepática", "label": "Enfermedad renal o hepática", "valor": "renal_hepatica", "value": "renal_hepatica"},
                {"etiqueta": "Ninguna enfermedad diagnosticada", "label": "Ninguna enfermedad diagnosticada", "valor": "ninguna", "value": "ninguna"}
            ]
        }

        # Pregunta 3: Medicamentos habituales o recientes
        p3 = {
            "id": "q_medicamentos_actuales",
            "pregunta": "¿Toma medicamentos habitualmente o ha tomado algo para este malestar?",
            "question_text": "¿Toma medicamentos habitualmente o ha tomado algo para este malestar?",
            "tipo_pregunta": "multiple_choice",
            "question_type": "multiple_choice",
            "opciones": [
                {"etiqueta": "Medicamentos para la presión arterial o el corazón", "label": "Medicamentos para la presión arterial o el corazón", "valor": "antihipertensivos", "value": "antihipertensivos"},
                {"etiqueta": "Anticoagulantes o aspirina diariamente", "label": "Anticoagulantes o aspirina diariamente", "valor": "anticoagulantes", "value": "anticoagulantes"},
                {"etiqueta": "Insulina o pastillas para la diabetes", "label": "Insulina o pastillas para la diabetes", "valor": "antidiabeticos", "value": "antidiabeticos"},
                {"etiqueta": "Tomé analgésicos o antibióticos en las últimas horas", "label": "Tomé analgésicos o antibióticos en las últimas horas", "valor": "analgesicos_recientes", "value": "analgesicos_recientes"},
                {"etiqueta": "No tomo ningún medicamento de forma regular", "label": "No tomo ningún medicamento de forma regular", "valor": "ninguno", "value": "ninguno"}
            ]
        }

        preguntas = [p1, p2, p3]

        return EsquemaRespuestaPreguntasDinamicas(
            sintoma_evaluado=sintoma_texto,
            symptom_evaluated=sintoma_texto,
            preguntas=preguntas,
            questions=preguntas
        )

    except Exception as e:
        logger.error(f"Error al generar preguntas dinámicas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar preguntas adaptativas: {str(e)}"
        )


# =============================================================================
# 3. GET /estado/{identificador} (y /status/{identifier}): Polling de Estado
# =============================================================================
@router.get(
    "/estado/{identificador}",
    summary="Consultar Estado de Triaje"
)
@router.get(
    "/status/{identifier}",
    include_in_schema=False
)
async def consultar_estado_triaje(identificador: str = None, identifier: str = None):
    """
    Consulta el estado y resumen estructurado de un pre-triaje por código alfanumérico (ej. MS-8X92K) o ID.
    """
    codigo = identificador or identifier
    registro = servicio_supabase.obtener_triaje_por_codigo(codigo_acceso=codigo)
    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontró ningún registro con el código de acceso '{codigo}'"
        )
    return registro


# =============================================================================
# 4. GET /buscar (y /lookup): Búsqueda Indexada
# =============================================================================
@router.get(
    "/buscar",
    summary="Buscar Expediente de Triaje"
)
@router.get(
    "/lookup",
    include_in_schema=False
)
async def buscar_triaje(
    codigo_acceso: Optional[str] = Query(None),
    access_code: Optional[str] = Query(None),
    ci: Optional[str] = Query(None)
):
    """
    Búsqueda indexada de expedientes por Código de Acceso o por Carnet de Identidad.
    """
    codigo = codigo_acceso or access_code
    if not codigo and not ci:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar un código de acceso ('codigo_acceso'/'access_code') o un Carnet de Identidad ('ci')"
        )

    ci_hasheado = hashear_ci(ci) if ci else None
    registro = servicio_supabase.obtener_triaje_por_criterio(codigo_acceso=codigo, ci_hash=ci_hasheado)

    if not registro:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró ningún expediente para el criterio de búsqueda ingresado"
        )
    return registro
