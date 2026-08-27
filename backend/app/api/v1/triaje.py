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
from app.proveedores.fabrica_ia import FabricaIA

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
    Genera de 2 a 3 preguntas dinámicas adaptativas mediante IA / PQRST orientadas a:
    1. Descartar banderas rojas y características específicas del padecimiento.
    2. Identificar antecedentes y enfermedades preexistentes (diabetes, hipertensión, asma, etc.).
    3. Conocer medicamentos habituales y tratamientos recientes.
    """
    try:
        sintoma_texto = (entrada.sintomas_brutos or entrada.sintoma or "").strip()
        genero_texto = entrada.genero or "No especificado"

        proveedor = FabricaIA.obtener_proveedor()
        preguntas_generadas = await proveedor.generar_preguntas_dinamicas(
            sintomas=sintoma_texto,
            edad=entrada.edad,
            genero=genero_texto
        )

        # Normalización bilingüe de claves
        preguntas_formateadas = []
        for p in preguntas_generadas:
            p_dict = dict(p)
            texto_p = p_dict.get("pregunta") or p_dict.get("question_text") or ""
            p_dict["pregunta"] = texto_p
            p_dict["question_text"] = texto_p

            tipo_p = p_dict.get("tipo_pregunta") or p_dict.get("question_type") or "single_choice"
            p_dict["tipo_pregunta"] = tipo_p
            p_dict["question_type"] = tipo_p

            opciones_raw = p_dict.get("opciones") or p_dict.get("options") or []
            opciones_fmt = []
            for o in opciones_raw:
                if isinstance(o, dict):
                    lbl = o.get("etiqueta") or o.get("label") or o.get("texto") or ""
                    val = o.get("valor") or o.get("value") or o.get("id") or lbl
                    opciones_fmt.append({"etiqueta": lbl, "label": lbl, "valor": val, "value": val})
                elif isinstance(o, str):
                    opciones_fmt.append({"etiqueta": o, "label": o, "valor": o.lower().replace(" ", "_"), "value": o.lower().replace(" ", "_")})

            p_dict["opciones"] = opciones_fmt
            p_dict["options"] = opciones_fmt
            preguntas_formateadas.append(p_dict)

        return EsquemaRespuestaPreguntasDinamicas(
            sintoma_evaluado=sintoma_texto,
            symptom_evaluated=sintoma_texto,
            preguntas=preguntas_formateadas,
            questions=preguntas_formateadas
        )

    except Exception as e:
        logger.error(f"Error al generar preguntas dinámicas: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al procesar preguntas adaptativas: {str(e)}"
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
