"""
Enrutador de Endpoints para el Portal Médico de Guardia API v1 en Español.
Proporciona la lista de espera priorizada, asignación concurrente de casos,
pestaña 'Mis Pacientes', liberación de guardia, descifrado seguro de CI en memoria,
cierre y diagnóstico de revisión médica con auditoría inalterable.
"""

import json
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query, Request, Depends
from pydantic import BaseModel, Field

from app.core.seguridad import descifrar_ci, hashear_ci, obtener_medico_actual
from app.esquemas.triaje import (
    EsquemaRevisionMedicaEntrada,
    EsquemaAsignacionPacienteEntrada,
    EsquemaDetalleExpedienteMedico
)
from app.servicios.servicio_supabase import (
    servicio_supabase,
    _BD_LOCAL_TRIAJES,
    _BD_LOCAL_RESULTADOS_IA
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/medico", tags=["Portal Médico de Guardia"])


def sanitizar_objeto_expediente(registro: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitiza y normaliza un expediente médico garantizando que estructuras complejas
    (datos_estaticos, respuestas_dinamicas, resultado_ia) se entreguen como diccionarios
    limpios y las cadenas de texto conserven formato UTF-8 válido.
    """
    if not isinstance(registro, dict):
        return {}

    copia = dict(registro)

    # Sanitizar datos estáticos
    datos_est = copia.get("datos_estaticos") or copia.get("static_data")
    if isinstance(datos_est, str):
        try:
            datos_est = json.loads(datos_est)
        except Exception:
            datos_est = {"motivo": datos_est}
    elif not isinstance(datos_est, dict):
        datos_est = {}
    copia["datos_estaticos"] = datos_est
    copia["static_data"] = datos_est

    # Sanitizar respuestas dinámicas
    resp_din = copia.get("respuestas_dinamicas") or copia.get("dynamic_answers")
    if isinstance(resp_din, str):
        try:
            resp_din = json.loads(resp_din)
        except Exception:
            resp_din = {}
    elif not isinstance(resp_din, dict):
        resp_din = {}
    copia["respuestas_dinamicas"] = resp_din
    copia["dynamic_answers"] = resp_din

    # Sanitizar resultado de IA
    res_ia = copia.get("resultados_ia") or copia.get("resultado_ia") or copia.get("ai_result")
    if isinstance(res_ia, list) and len(res_ia) > 0:
        res_ia = res_ia[0]
    if isinstance(res_ia, str):
        try:
            res_ia = json.loads(res_ia)
        except Exception:
            res_ia = None
    copia["resultado_ia"] = res_ia
    copia["resultados_ia"] = res_ia
    copia["ai_result"] = res_ia

    return copia


# =============================================================================
# 1. GET /panel (y /dashboard): Lista de Espera y Métricas Cuantitativas
# =============================================================================
@router.get(
    "/panel",
    summary="Dashboard de Guardia Médica Priorizado"
)
@router.get(
    "/dashboard",
    summary="Dashboard Médico Legacy",
    include_in_schema=False
)
async def obtener_panel_medico(
    solo_disponibles: bool = Query(False, description="Filtrar únicamente pacientes sin médico asignado"),
    only_available: Optional[bool] = Query(None, include_in_schema=False),
    especialidad: Optional[str] = Query(None, description="Filtrar pacientes por especialidad médica"),
    specialty: Optional[str] = Query(None, include_in_schema=False),
    usuario_actual: Dict[str, Any] = Depends(obtener_medico_actual)
):
    """
    Obtiene la lista de espera de pacientes para el dashboard del médico de guardia.
    Calcula métricas globales de atención en tiempo real y ordena por gravedad:
    1. ROJO / RED (🔴 Urgente)
    2. AMARILLO / YELLOW (🟡 Prioritario)
    3. VERDE / GREEN (🟢 No Urgente)
    Soporta filtrado opcional por especialidad médica.
    """
    try:
        filtrar_disponibles = only_available if only_available is not None else solo_disponibles
        esp_filtro = specialty or especialidad
        registros_ordenados = servicio_supabase.obtener_cola_guardia(
            solo_disponibles=filtrar_disponibles,
            especialidad=esp_filtro
        )

        registros_limpios = [sanitizar_objeto_expediente(r) for r in registros_ordenados]

        # Calcular métricas cuantitativas
        en_espera = sum(
            1 for r in registros_limpios
            if str(r.get("estado") or r.get("status") or "").upper() in ["RECIBIDO", "LISTO", "RECEIVED", "READY"]
            and not (r.get("medico_asignado_id") or r.get("assigned_doctor_id"))
        )
        en_consulta = sum(
            1 for r in registros_limpios
            if str(r.get("estado") or r.get("status") or "").upper() in ["EN_CONSULTA", "IN_CONSULTATION"]
        )
        atendidos = sum(
            1 for r in registros_limpios
            if str(r.get("estado") or r.get("status") or "").upper() in ["REVISADO", "REVIEWED"]
        )
        total_rojo = sum(
            1 for r in registros_limpios
            if str(r.get("prioridad_final") or r.get("final_priority") or "").upper() in ["ROJO", "RED"]
            and str(r.get("estado") or r.get("status") or "").upper() != "REVISADO"
        )

        return {
            "metricas": {
                "en_espera": en_espera,
                "en_consulta": en_consulta,
                "atendidos_hoy": atendidos,
                "atendidos": atendidos,
                "total_rojo": total_rojo,
                "total_hoy": len(registros_limpios)
            },
            "metrics": {
                "waiting_count": en_espera,
                "in_consultation_count": en_consulta,
                "reviewed_count": atendidos,
                "total_red": total_rojo,
                "total_today": len(registros_limpios)
            },
            "registros": registros_limpios,
            "records": registros_limpios
        }

    except Exception as e:
        logger.error(f"Error al recuperar panel médico: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cargando el panel médico: {str(e)}"
        )


# =============================================================================
# 2. POST /asignar/{triaje_id} (y /assign/{triaje_id}): Reclamo de Paciente
# =============================================================================
@router.post(
    "/asignar/{triaje_id}",
    status_code=status.HTTP_200_OK,
    summary="Reclamar y Asignar Paciente a Médico en Consulta"
)
@router.post(
    "/assign/{triaje_id}",
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
async def asignar_paciente_guardia(
    triaje_id: str,
    request: Request = None,
    usuario_actual: Dict[str, Any] = Depends(obtener_medico_actual)
):
    """
    Asigna un paciente de la cola general al médico en turno, cambiando el estado a 'EN_CONSULTA'.
    Control de concurrencia: Retorna HTTP 409 Conflict si el paciente ya fue tomado por otro médico.
    """
    try:
        medico_id = usuario_actual.get("id") or usuario_actual.get("usuario_id") or "doc-uuid-12345"
        cliente_ip = request.client.host if request and request.client else "127.0.0.1"

        try:
            resultado = servicio_supabase.asignar_paciente_a_medico(triaje_id=triaje_id, medico_id=medico_id)
        except ValueError as ve:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=str(ve)
            )

        # Auditoría inalterable de asignación
        servicio_supabase.registrar_evento_auditoria(
            usuario_id=medico_id,
            accion="RECLAMAR_PACIENTE_GUARDIA",
            recurso_id=triaje_id,
            direccion_ip=cliente_ip
        )

        return resultado

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error asignando paciente {triaje_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error en la asignación del paciente: {str(e)}"
        )


# =============================================================================
# 3. POST /liberar/{triaje_id} (y /release/{triaje_id}): Liberación a Cola
# =============================================================================
@router.post(
    "/liberar/{triaje_id}",
    status_code=status.HTTP_200_OK,
    summary="Liberar Paciente a la Cola de Guardia"
)
@router.post(
    "/release/{triaje_id}",
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
async def liberar_paciente_guardia(
    triaje_id: str,
    request: Request = None,
    usuario_actual: Dict[str, Any] = Depends(obtener_medico_actual)
):
    """
    Permite al médico facultativo liberar un paciente en consulta devolviéndolo a la cola general.
    """
    try:
        medico_id = usuario_actual.get("id") or usuario_actual.get("usuario_id") or "doc-uuid-12345"
        cliente_ip = request.client.host if request and request.client else "127.0.0.1"

        resultado = servicio_supabase.liberar_paciente(triaje_id=triaje_id, medico_id=medico_id)

        # Registrar trazabilidad
        servicio_supabase.registrar_evento_auditoria(
            usuario_id=medico_id,
            accion="LIBERAR_PACIENTE_GUARDIA",
            recurso_id=triaje_id,
            direccion_ip=cliente_ip
        )

        return resultado

    except Exception as e:
        logger.error(f"Error liberando paciente {triaje_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al liberar paciente: {str(e)}"
        )


# =============================================================================
# 4. GET /mis-pacientes (y /my-patients): Casos Asignados al Médico
# =============================================================================
@router.get(
    "/mis-pacientes",
    summary="Obtener Lista de Pacientes Asignados al Médico"
)
@router.get(
    "/my-patients",
    summary="Legacy My Patients",
    include_in_schema=False
)
async def obtener_mis_pacientes(
    incluir_revisados: bool = Query(False, description="Incluir consultas ya cerradas en el histórico"),
    include_reviewed: Optional[bool] = Query(None, include_in_schema=False),
    usuario_actual: Dict[str, Any] = Depends(obtener_medico_actual)
):
    """
    Retorna la lista de pacientes actualmente bajo atención directa del médico autenticado (EN_CONSULTA)
    y opcionalmente su histórico de atenciones concluidas (REVISADO).
    """
    try:
        medico_id = usuario_actual.get("id") or usuario_actual.get("usuario_id") or "doc-uuid-12345"
        filtrar_revisados = include_reviewed if include_reviewed is not None else incluir_revisados

        pacientes = servicio_supabase.obtener_pacientes_por_medico(medico_id=medico_id, incluir_revisados=filtrar_revisados)
        pacientes_limpios = [sanitizar_objeto_expediente(p) for p in pacientes]

        return {
            "estado": "exito",
            "status": "success",
            "medico_id": medico_id,
            "total": len(pacientes_limpios),
            "pacientes": pacientes_limpios,
            "patients": pacientes_limpios
        }

    except Exception as e:
        logger.error(f"Error al obtener pacientes asignados: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando pacientes del médico: {str(e)}"
        )


# =============================================================================
# 5. GET /paciente/{triaje_id} (y /patient/{triage_id}): Expediente y Descifrado
# =============================================================================
@router.get(
    "/paciente/{triaje_id}",
    summary="Detalle de Expediente con Descifrado Seguro de CI"
)
@router.get(
    "/patient/{triage_id}",
    include_in_schema=False
)
async def obtener_detalle_paciente(
    triaje_id: Optional[str] = None,
    triage_id: Optional[str] = None,
    request: Request = None,
    usuario_actual: Dict[str, Any] = Depends(obtener_medico_actual)
):
    """
    Recupera el expediente clínico completo del paciente con su CI descifrado en memoria
    y registra atómicamente la auditoría de acceso al expediente.
    """
    id_objetivo = triaje_id or triage_id
    try:
        medico_id = usuario_actual.get("id") or usuario_actual.get("usuario_id") or "doc-uuid-12345"
        cliente_ip = request.client.host if request and request.client else "127.0.0.1"

        registro = servicio_supabase.obtener_triaje_por_codigo(codigo_acceso=id_objetivo)

        if not registro:
            cliente = servicio_supabase.obtener_cliente()
            if cliente:
                try:
                    resp = cliente.table("registros_triaje").select("*, resultados_ia(*)").eq("id", id_objetivo).execute()
                    if resp.data:
                        registro = resp.data[0]
                    else:
                        resp_leg = cliente.table("triage_record").select("*, ai_result(*)").eq("id", id_objetivo).execute()
                        if resp_leg.data:
                            registro = resp_leg.data[0]
                except Exception as e:
                    logger.error(f"Error consultando paciente por ID en Supabase: {e}")

        if not registro and id_objetivo in _BD_LOCAL_TRIAJES:
            registro = dict(_BD_LOCAL_TRIAJES[id_objetivo])
            registro["resultados_ia"] = _BD_LOCAL_RESULTADOS_IA.get(registro.get("id"))
            registro["ai_result"] = _BD_LOCAL_RESULTADOS_IA.get(registro.get("id"))

        if not registro:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No se encontró el expediente del paciente con ID/Código '{id_objetivo}'"
            )

        # Descifrado seguro del Carnet de Identidad en memoria
        ci_cifrado = registro.get("ci_cifrado") or registro.get("ci_encrypted", "")
        ci_descifrado = descifrar_ci(ci_cifrado) if ci_cifrado else "NO_DISPONIBLE"

        # Registrar trazabilidad en bitácora de auditoría
        servicio_supabase.registrar_evento_auditoria(
            usuario_id=medico_id,
            accion="CONSULTA_EXPEDIENTE_DESCIFRADO_CI",
            recurso_id=registro.get("id"),
            direccion_ip=cliente_ip
        )

        registro_limpio = sanitizar_objeto_expediente(registro)
        registro_limpio["ci_descifrado"] = ci_descifrado
        registro_limpio["decrypted_ci"] = ci_descifrado

        return registro_limpio

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener detalle del paciente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando expediente: {str(e)}"
        )


# =============================================================================
# 6. POST /revisar (y /review): Cierre y Diagnóstico Médico
# =============================================================================
@router.post(
    "/revisar",
    status_code=status.HTTP_200_OK,
    summary="Registrar Revisión y Cierre Médico"
)
@router.post(
    "/review",
    status_code=status.HTTP_200_OK,
    include_in_schema=False
)
async def registrar_revision_medica(
    payload: EsquemaRevisionMedicaEntrada,
    request: Request = None,
    usuario_actual: Dict[str, Any] = Depends(obtener_medico_actual)
):
    """
    Registra las observaciones y diagnóstico del facultativo médico presencial,
    guarda el ajuste facultativo de prioridad y pasa el estado a 'REVISADO'.
    """
    try:
        medico_id = payload.medico_id or usuario_actual.get("id") or usuario_actual.get("usuario_id") or "doc-uuid-12345"
        cliente_ip = request.client.host if request and request.client else "127.0.0.1"

        resultado = servicio_supabase.guardar_revision_medica(
            triaje_id=payload.triaje_id,
            medico_id=medico_id,
            notas_medico=payload.notas_medico,
            prioridad_ajustada=payload.prioridad_ajustada
        )

        # Auditoría de cierre
        servicio_supabase.registrar_evento_auditoria(
            usuario_id=medico_id,
            accion="CIERRE_REVISION_MEDICA",
            recurso_id=payload.triaje_id,
            direccion_ip=cliente_ip
        )

        return {
            "estado": "exito",
            "status": "success",
            "mensaje": "Revisión médica registrada y triaje cerrado exitosamente.",
            "triaje_id": payload.triaje_id,
            "medico_id": medico_id
        }

    except Exception as e:
        logger.error(f"Error al registrar revisión médica: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar la revisión médica: {str(e)}"
        )
