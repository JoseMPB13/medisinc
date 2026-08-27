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
    Genera de 2 a 3 preguntas dinámicas orientadas a descartar banderas rojas clínicas.
    """
    try:
        sintoma_texto = (entrada.sintomas_brutos or entrada.sintoma or "").lower().strip()

        if "cabeza" in sintoma_texto or "cefalea" in sintoma_texto:
            preguntas = [
                {
                    "id": "q_headache_type",
                    "pregunta": "¿El dolor de cabeza comenzó de forma súbita e intensa (como un trueno)?",
                    "question_text": "¿El dolor de cabeza comenzó de forma súbita e intensa (como un trueno)?",
                    "tipo_pregunta": "single_choice",
                    "question_type": "single_choice",
                    "opciones": [
                        {"etiqueta": "Sí, de golpe e insoportable", "label": "Sí, de golpe e insoportable", "valor": "subito_intenso", "value": "subito_intenso"},
                        {"etiqueta": "No, fue progresivo", "label": "No, fue progresivo", "valor": "progresivo", "value": "progresivo"}
                    ]
                },
                {
                    "id": "q_headache_signs",
                    "pregunta": "¿Presenta alguno de los siguientes síntomas acompañantes?",
                    "question_text": "¿Presenta alguno de los siguientes síntomas acompañantes?",
                    "tipo_pregunta": "multiple_choice",
                    "question_type": "multiple_choice",
                    "opciones": [
                        {"etiqueta": "Rigidez en el cuello o fiebre alta", "label": "Rigidez en el cuello o fiebre alta", "valor": "rigidez_fiebre", "value": "rigidez_fiebre"},
                        {"etiqueta": "Visión borrosa o alteración visual", "label": "Visión borrosa o alteración visual", "valor": "vision_borrosa", "value": "vision_borrosa"},
                        {"etiqueta": "Debilidad en cara, brazo o dificultad para hablar", "label": "Debilidad en cara, brazo o dificultad para hablar", "valor": "alteracion_neurologica", "value": "alteracion_neurologica"},
                        {"etiqueta": "Ninguno de los anteriores", "label": "Ninguno de los anteriores", "valor": "ninguno", "value": "ninguno"}
                    ]
                }
            ]
        elif "pecho" in sintoma_texto or "torac" in sintoma_texto or "card" in sintoma_texto:
            preguntas = [
                {
                    "id": "q_chest_type",
                    "pregunta": "¿Cómo describirías la sensación del dolor en el pecho?",
                    "question_text": "¿Cómo describirías la sensación del dolor en el pecho?",
                    "tipo_pregunta": "single_choice",
                    "question_type": "single_choice",
                    "opciones": [
                        {"etiqueta": "Sensación de opresión o peso pesado", "label": "Sensación de opresión o peso pesado", "valor": "opresivo", "value": "opresivo"},
                        {"etiqueta": "Punzante al respirar hondo", "label": "Punzante al respirar hondo", "valor": "punzante", "value": "punzante"},
                        {"etiqueta": "Ardor o acidez", "label": "Ardor o acidez", "valor": "ardor", "value": "ardor"}
                    ]
                },
                {
                    "id": "q_chest_radiation",
                    "pregunta": "¿El dolor se extiende hacia otra zona del cuerpo?",
                    "question_text": "¿El dolor se extiende hacia otra zona del cuerpo?",
                    "tipo_pregunta": "multiple_choice",
                    "question_type": "multiple_choice",
                    "opciones": [
                        {"etiqueta": "Hacia brazo izquierdo, cuello o mandíbula", "label": "Hacia brazo izquierdo, cuello o mandíbula", "valor": "irradiado_brazo", "value": "irradiado_brazo"},
                        {"etiqueta": "Hacia la espalda", "label": "Hacia la espalda", "valor": "irradiado_espalda", "value": "irradiado_espalda"},
                        {"etiqueta": "Acompañado de sudor frío y náuseas", "label": "Acompañado de sudor frío y náuseas", "valor": "sudor_frio", "value": "sudor_frio"},
                        {"etiqueta": "No se extiende a ningún lado", "label": "No se extiende a ningún lado", "valor": "localizado", "value": "localizado"}
                    ]
                }
            ]
        elif "estomago" in sintoma_texto or "abdom" in sintoma_texto or "barriga" in sintoma_texto:
            preguntas = [
                {
                    "id": "q_abdo_loc",
                    "pregunta": "¿En qué zona del abdomen sientes mayor dolor?",
                    "question_text": "¿En qué zona del abdomen sientes mayor dolor?",
                    "tipo_pregunta": "single_choice",
                    "question_type": "single_choice",
                    "opciones": [
                        {"etiqueta": "En la parte inferior derecha", "label": "En la parte inferior derecha", "valor": "fosa_iliaca_derecha", "value": "fosa_iliaca_derecha"},
                        {"etiqueta": "En la boca del estómago", "label": "En la boca del estómago", "valor": "epigastrio", "value": "epigastrio"},
                        {"etiqueta": "En todo el abdomen de forma difusa", "label": "En todo el abdomen de forma difusa", "valor": "difuso", "value": "difuso"}
                    ]
                },
                {
                    "id": "q_abdo_signs",
                    "pregunta": "¿Presentas alguno de estos signos adicionales?",
                    "question_text": "¿Presentas alguno de estos signos adicionales?",
                    "tipo_pregunta": "multiple_choice",
                    "question_type": "multiple_choice",
                    "opciones": [
                        {"etiqueta": "Fiebre o vómitos persistentes", "label": "Fiebre o vómitos persistentes", "valor": "fiebre_vomito", "value": "fiebre_vomito"},
                        {"etiqueta": "Imposibilidad de comer o tolerar líquidos", "label": "Imposibilidad de comer o tolerar líquidos", "valor": "intolerancia_oral", "value": "intolerancia_oral"},
                        {"etiqueta": "Deposiciones con sangre o muy oscuras", "label": "Deposiciones con sangre o muy oscuras", "valor": "sangre_heces", "value": "sangre_heces"},
                        {"etiqueta": "Ninguno de los anteriores", "label": "Ninguno de los anteriores", "valor": "ninguno", "value": "ninguno"}
                    ]
                }
            ]
        else:
            preguntas = [
                {
                    "id": "q_gen_duration",
                    "pregunta": "¿Con qué rapidez aparecieron las molestias?",
                    "question_text": "¿Con qué rapidez aparecieron las molestias?",
                    "tipo_pregunta": "single_choice",
                    "question_type": "single_choice",
                    "opciones": [
                        {"etiqueta": "Menos de 24 horas", "label": "Menos de 24 horas", "valor": "agudo", "value": "agudo"},
                        {"etiqueta": "De 1 a 3 días", "label": "De 1 a 3 días", "valor": "subagudo", "value": "subagudo"},
                        {"etiqueta": "Más de 1 semana", "label": "Más de 1 semana", "valor": "cronico", "value": "cronico"}
                    ]
                },
                {
                    "id": "q_gen_redflags",
                    "pregunta": "¿Presenta alguna de estas señales de alerta?",
                    "question_text": "¿Presenta alguna de estas señales de alerta?",
                    "tipo_pregunta": "multiple_choice",
                    "question_type": "multiple_choice",
                    "opciones": [
                        {"etiqueta": "Dificultad para respirar o falta de aire", "label": "Dificultad para respirar o falta de aire", "valor": "disnea", "value": "disnea"},
                        {"etiqueta": "Fiebre alta persistente (>38.5 °C)", "label": "Fiebre alta persistente (>38.5 °C)", "valor": "fiebre_alta", "value": "fiebre_alta"},
                        {"etiqueta": "Sensación de mareo intenso o desmayo", "label": "Sensación de mareo intenso o desmayo", "valor": "mareo_sincope", "value": "mareo_sincope"},
                        {"etiqueta": "Ninguna de las anteriores", "label": "Ninguna de las anteriores", "valor": "ninguno", "value": "ninguno"}
                    ]
                }
            ]

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
