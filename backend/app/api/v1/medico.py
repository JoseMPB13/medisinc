"""
Enrutador de Endpoints para el Portal Médico de Guardia API v1 en Español.
Proporciona la lista de espera ordenada por prioridad clínica, la revisión médica presencial,
el descifrado seguro del CI en memoria y trazabilidad inalterable en registros_auditoria.
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query, Request, Depends
from pydantic import BaseModel, Field

from app.core.seguridad import descifrar_ci, hashear_ci, obtener_medico_actual
from app.esquemas.triaje import (
    EsquemaRevisionMedicaEntrada,
    MedicalReviewSchema,
    EsquemaDetalleExpedienteMedico
)
from app.servicios.servicio_supabase import (
    servicio_supabase,
    _BD_LOCAL_TRIAJES,
    _BD_LOCAL_RESULTADOS_IA,
    _IN_MEMORY_TRIAGE_DB,
    _IN_MEMORY_AI_DB
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/medico", tags=["Portal Médico"])


# =============================================================================
# 1. GET /panel (y /dashboard): Lista de Espera Priorizada
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
async def obtener_panel_medico():
    """
    Obtiene la lista de espera de pacientes para el dashboard del médico de guardia.
    Ordena los registros por nivel de urgencia:
    1. ROJO / RED (🔴 Urgente) primero.
    2. AMARILLO / YELLOW (🟡 Prioritario) al centro.
    3. VERDE / GREEN (🟢 No Urgente) abajo.
    Orden secundario: Hora de llegada (creado_en / created_at).
    """
    try:
        registros_ordenados = servicio_supabase.obtener_cola_guardia()

        # Calcular métricas globales del panel
        en_espera = sum(1 for r in registros_ordenados if r.get("estado") in ["RECIBIDO", "LISTO", "RECEIVED", "READY"] or r.get("status") in ["RECIBIDO", "LISTO", "RECEIVED", "READY"])
        atendidos = sum(1 for r in registros_ordenados if r.get("estado") in ["REVISADO", "REVIEWED"] or r.get("status") in ["REVISADO", "REVIEWED"])
        total_rojo = sum(1 for r in registros_ordenados if (r.get("prioridad_final") in ["ROJO", "RED"] or r.get("final_priority") in ["ROJO", "RED"]))

        return {
            "metricas": {
                "en_espera": en_espera,
                "atendidos": atendidos,
                "total_rojo": total_rojo,
                "total_hoy": len(registros_ordenados)
            },
            "metrics": {
                "waiting_count": en_espera,
                "reviewed_count": atendidos,
                "total_red": total_rojo,
                "total_today": len(registros_ordenados)
            },
            "registros": registros_ordenados,
            "records": registros_ordenados
        }

    except Exception as e:
        logger.error(f"Error al recuperar panel médico: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cargando el panel médico: {str(e)}"
        )


# =============================================================================
# 2. GET /paciente/{triaje_id} (y /patient/{triage_id}): Expediente y Descifrado
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
    request: Request = None
):
    """
    Recupera el expediente clínico de un paciente y descifra su Carnet de Identidad en memoria.
    Registra de forma atómica la acción en la bitácora de auditoría.
    """
    id_objetivo = triaje_id or triage_id
    try:
        cliente_ip = request.client.host if request and request.client else "127.0.0.1"

        registro = servicio_supabase.obtener_triaje_por_codigo(codigo_acceso=id_objetivo)

        # Si no se encuentra por código de acceso, buscar por ID directo
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
            usuario_id=registro.get("id"),
            accion="CONSULTA_EXPEDIENTE_DESCIFRADO_CI",
            recurso_id=registro.get("id"),
            direccion_ip=cliente_ip
        )

        registro["ci_descifrado"] = ci_descifrado
        registro["decrypted_ci"] = ci_descifrado
        return registro

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener detalle del paciente: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error consultando expediente: {str(e)}"
        )


# =============================================================================
# 3. POST /revisar (y /review): Cierre y Diagnóstico Médico
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
    request: Request = None
):
    """
    Registra las observaciones y diagnóstico del facultativo médico presencial,
    guarda el ajuste facultativo de prioridad y pasa el estado a 'REVISADO'.
    """
    try:
        cliente_ip = request.client.host if request and request.client else "127.0.0.1"

        resultado = servicio_supabase.guardar_revision_medica(
            triaje_id=payload.triaje_id,
            medico_id=payload.medico_id or "doc-uuid-12345",
            notas_medico=payload.notas_medico,
            prioridad_ajustada=payload.prioridad_ajustada
        )

        # Auditoría de cierre
        servicio_supabase.registrar_evento_auditoria(
            usuario_id=payload.medico_id or "doc-uuid-12345",
            accion="CIERRE_REVISION_MEDICA",
            recurso_id=payload.triaje_id,
            direccion_ip=cliente_ip
        )

        return {
            "estado": "exito",
            "status": "success",
            "mensaje": "Revisión médica registrada y triaje cerrado exitosamente.",
            "triaje_id": payload.triaje_id
        }

    except Exception as e:
        logger.error(f"Error al registrar revisión médica: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar la revisión médica: {str(e)}"
        )
