"""
Servicio de Persistencia y Acceso a Datos con Supabase (PostgreSQL).
Proporciona métodos para interactuar con las tablas relacionales estandarizadas en español
utilizando el Service Role Key del SDK de Supabase y soporte de contingencia en memoria local.
"""

import logging
from typing import Optional, Dict, Any, List
from supabase import create_client, Client

from app.core.config import settings

logger = logging.getLogger(__name__)

# -----------------------------------------------------------------------------
# Base de datos en memoria local (Fallback de contingencia ante fallas de red/desarrollo)
# -----------------------------------------------------------------------------
_BD_LOCAL_TRIAJES: Dict[str, Dict[str, Any]] = {}
_BD_LOCAL_RESULTADOS_IA: Dict[str, Dict[str, Any]] = {}
_BD_LOCAL_PERFILES: Dict[str, Dict[str, Any]] = {
    "admin-01": {
        "id": "admin-01",
        "usuario_id": "auth-admin-01",
        "nombre_completo": "Dr. Fernando Morales (Admin)",
        "correo": "admin@medisinc.bo",
        "especialidad": "Dirección Médica y Emergenciología",
        "rol": "ADMIN",
        "esta_activo": True,
        "creado_en": "2026-08-01T08:00:00Z"
    },
    "medico-01": {
        "id": "medico-01",
        "usuario_id": "auth-doc-01",
        "nombre_completo": "Dra. Mariana Vaca",
        "correo": "medico@medisinc.bo",
        "especialidad": "Medicina General y Triaje",
        "rol": "MEDICO",
        "esta_activo": True,
        "creado_en": "2026-08-05T09:30:00Z"
    }
}
_BD_LOCAL_AUDITORIA: List[Dict[str, Any]] = []

# Aliases de compatibilidad con memoria previa
_IN_MEMORY_TRIAGE_DB = _BD_LOCAL_TRIAJES
_IN_MEMORY_AI_DB = _BD_LOCAL_RESULTADOS_IA
_IN_MEMORY_PROFILES_DB = _BD_LOCAL_PERFILES
_IN_MEMORY_AUDIT_LOG_DB = _BD_LOCAL_AUDITORIA


class ServicioSupabase:
    """
    Cliente encapsulado de Supabase para operaciones CRUD de triaje, auditoría y personal médico.
    """

    def __init__(self):
        self._cliente: Optional[Client] = None

    def obtener_cliente(self) -> Optional[Client]:
        """
        Obtiene de forma dinámica la instancia del cliente Supabase con Service Role Key.
        """
        if self._cliente is not None:
            return self._cliente

        url = settings.SUPABASE_URL
        clave = settings.SUPABASE_SERVICE_ROLE_KEY

        if url and "placeholder" not in url and clave and "placeholder" not in clave:
            try:
                self._cliente = create_client(url, clave)
                logger.info(f"✓ Conectado a Supabase: {url}")
                return self._cliente
            except Exception as e:
                logger.error(f"Error al conectar con el SDK de Supabase: {e}")
                self._cliente = None
        else:
            logger.warning("Supabase no configurado o en modo placeholder. Utilizando persistencia en memoria local.")

        return None

    def get_client(self) -> Optional[Client]:
        """Alias para compatibilidad con código existente."""
        return self.obtener_cliente()

    def crear_registro_triaje(self, datos: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserta un nuevo registro de triaje con estado inicial 'RECIBIDO' ('RECEIVED').
        """
        payload_triaje = {
            "codigo_acceso": datos.get("codigo_acceso") or datos.get("access_code"),
            "ci_hash": datos.get("ci_hash"),
            "ci_cifrado": datos.get("ci_cifrado") or datos.get("ci_encrypted"),
            "nombre_paciente": datos.get("nombre_paciente") or datos.get("patient_name"),
            "edad": datos.get("edad") if datos.get("edad") is not None else datos.get("age"),
            "genero": datos.get("genero") or datos.get("gender"),
            "sintomas_brutos": datos.get("sintomas_brutos") or datos.get("raw_symptoms"),
            "datos_estaticos": datos.get("datos_estaticos") or datos.get("static_data", {}),
            "respuestas_dinamicas": datos.get("respuestas_dinamicas") or datos.get("dynamic_answers", {}),
            "estado": "RECIBIDO",
            "prioridad_final": datos.get("prioridad_final") or datos.get("final_priority")
        }

        # Campos legacy para tabla antigua si aún no se ha migrado
        payload_legacy = {
            "access_code": payload_triaje["codigo_acceso"],
            "ci_hash": payload_triaje["ci_hash"],
            "ci_encrypted": payload_triaje["ci_cifrado"],
            "patient_name": payload_triaje["nombre_paciente"],
            "age": payload_triaje["edad"],
            "gender": payload_triaje["genero"],
            "raw_symptoms": payload_triaje["sintomas_brutos"],
            "static_data": payload_triaje["datos_estaticos"],
            "dynamic_answers": payload_triaje["respuestas_dinamicas"],
            "status": "RECEIVED",
            "final_priority": payload_triaje["prioridad_final"]
        }

        cliente = self.obtener_cliente()
        if cliente:
            try:
                # Intento en tabla estandarizada en español
                try:
                    respuesta = cliente.table("registros_triaje").insert(payload_triaje).execute()
                    if respuesta.data:
                        logger.info(f"✓ Registro insertado en 'registros_triaje'. ID: {respuesta.data[0].get('id')}")
                        return respuesta.data[0]
                except Exception:
                    # Fallback a tabla legacy
                    respuesta = cliente.table("triage_record").insert(payload_legacy).execute()
                    if respuesta.data:
                        logger.info(f"✓ Registro insertado en 'triage_record'. ID: {respuesta.data[0].get('id')}")
                        return respuesta.data[0]
            except Exception as e:
                logger.error(f"Error al insertar triaje en Supabase: {e}")

        # Fallback a persistencia en memoria local
        triaje_id = datos.get("id") or f"tr-local-{payload_triaje['codigo_acceso']}"
        payload_triaje["id"] = triaje_id
        payload_triaje["access_code"] = payload_triaje["codigo_acceso"]
        payload_triaje["status"] = "RECEIVED"
        payload_triaje["created_at"] = "2026-08-26T20:00:00Z"
        payload_triaje["creado_en"] = "2026-08-26T20:00:00Z"

        _BD_LOCAL_TRIAJES[triaje_id] = payload_triaje
        _BD_LOCAL_TRIAJES[payload_triaje["codigo_acceso"]] = payload_triaje
        return payload_triaje

    def create_triage_record(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Alias para compatibilidad con código existente."""
        return self.crear_registro_triaje(data)

    def guardar_resultado_ia(
        self,
        triaje_id: str,
        resultado_ia: Dict[str, Any],
        prioridad_final: str,
        sobreescritura_aplicada: bool,
        motivo_sobreescritura: Optional[str]
    ) -> bool:
        """
        Almacena el resultado estructurado de la IA y actualiza el estado del triaje a 'LISTO' ('READY').
        """
        payload_ia = {
            "triaje_id": triaje_id,
            "proveedor": settings.AI_PROVIDER,
            "modelo": "seleccion-automatica",
            "resultado_estructurado": resultado_ia,
            "sobreescritura_aplicada": sobreescritura_aplicada,
            "motivo_sobreescritura": motivo_sobreescritura
        }

        payload_ia_legacy = {
            "triage_id": triaje_id,
            "provider": settings.AI_PROVIDER,
            "model": "seleccion-automatica",
            "structured_result": resultado_ia,
            "override_applied": sobreescritura_aplicada,
            "override_reason": motivo_sobreescritura
        }

        cliente = self.obtener_cliente()
        if cliente:
            try:
                try:
                    cliente.table("resultados_ia").insert(payload_ia).execute()
                    cliente.table("registros_triaje").update({
                        "estado": "LISTO",
                        "prioridad_final": prioridad_final
                    }).eq("id", triaje_id).execute()
                    return True
                except Exception:
                    cliente.table("ai_result").insert(payload_ia_legacy).execute()
                    cliente.table("triage_record").update({
                        "status": "READY",
                        "final_priority": prioridad_final
                    }).eq("id", triaje_id).execute()
                    return True
            except Exception as e:
                logger.error(f"Error al actualizar resultado IA en Supabase: {e}")

        # Fallback local
        _BD_LOCAL_RESULTADOS_IA[triaje_id] = payload_ia
        if triaje_id in _BD_LOCAL_TRIAJES:
            _BD_LOCAL_TRIAJES[triaje_id]["estado"] = "LISTO"
            _BD_LOCAL_TRIAJES[triaje_id]["status"] = "READY"
            _BD_LOCAL_TRIAJES[triaje_id]["prioridad_final"] = prioridad_final
            _BD_LOCAL_TRIAJES[triaje_id]["final_priority"] = prioridad_final
            _BD_LOCAL_TRIAJES[triaje_id]["resultado_ia"] = payload_ia
            _BD_LOCAL_TRIAJES[triaje_id]["ai_result"] = payload_ia
        return True

    def update_triage_with_ai_result(
        self,
        triage_id: str,
        ai_result: Dict[str, Any],
        final_priority: str,
        override_applied: bool,
        override_reason: Optional[str]
    ) -> bool:
        """Alias para compatibilidad con código existente."""
        return self.guardar_resultado_ia(triage_id, ai_result, final_priority, override_applied, override_reason)

    def obtener_triaje_por_codigo(self, codigo_acceso: str) -> Optional[Dict[str, Any]]:
        """
        Busca un registro de triaje por su código único de acceso (ej. MS-8X92K).
        """
        return self.obtener_triaje_por_criterio(codigo_acceso=codigo_acceso)

    def obtener_triaje_por_hash_ci(self, ci_hash: str) -> Optional[Dict[str, Any]]:
        """
        Busca un registro de triaje por el hash seguro del Carnet de Identidad.
        """
        return self.obtener_triaje_por_criterio(ci_hash=ci_hash)

    def obtener_triaje_por_criterio(
        self,
        codigo_acceso: Optional[str] = None,
        ci_hash: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Consulta un expediente por código de acceso o hash de CI en Supabase o memoria local.
        """
        cliente = self.obtener_cliente()
        if cliente:
            try:
                try:
                    consulta = cliente.table("registros_triaje").select("*, resultados_ia(*)")
                    if codigo_acceso:
                        consulta = consulta.eq("codigo_acceso", codigo_acceso)
                    elif ci_hash:
                        consulta = consulta.eq("ci_hash", ci_hash)
                    resp = consulta.execute()
                    if resp.data:
                        return resp.data[0]
                except Exception:
                    consulta = cliente.table("triage_record").select("*, ai_result(*)")
                    if codigo_acceso:
                        consulta = consulta.eq("access_code", codigo_acceso)
                    elif ci_hash:
                        consulta = consulta.eq("ci_hash", ci_hash)
                    resp = consulta.execute()
                    if resp.data:
                        return resp.data[0]
            except Exception as e:
                logger.error(f"Error al buscar triaje en Supabase: {e}")

        # Fallback local
        if codigo_acceso:
            for r in _BD_LOCAL_TRIAJES.values():
                if r.get("codigo_acceso") == codigo_acceso or r.get("access_code") == codigo_acceso or r.get("id") == codigo_acceso:
                    rec = dict(r)
                    rec["resultados_ia"] = _BD_LOCAL_RESULTADOS_IA.get(rec.get("id"))
                    rec["ai_result"] = _BD_LOCAL_RESULTADOS_IA.get(rec.get("id"))
                    return rec
        if ci_hash:
            for r in _BD_LOCAL_TRIAJES.values():
                if r.get("ci_hash") == ci_hash:
                    rec = dict(r)
                    rec["resultados_ia"] = _BD_LOCAL_RESULTADOS_IA.get(rec.get("id"))
                    rec["ai_result"] = _BD_LOCAL_RESULTADOS_IA.get(rec.get("id"))
                    return rec
        return None

    def get_triage_by_code_or_hash(
        self,
        access_code: Optional[str] = None,
        ci_hash: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Alias para compatibilidad con código existente."""
        return self.obtener_triaje_por_criterio(codigo_acceso=access_code, ci_hash=ci_hash)

    def obtener_cola_guardia(self) -> List[Dict[str, Any]]:
        """
        Retorna la lista de espera de pacientes para el panel médico, ordenada estrictamente por:
        1. Urgencia clínica: ROJO / RED primero, AMARILLO / YELLOW después, VERDE / GREEN al final.
        2. Hora de llegada (creado_en / created_at).
        """
        todos_los_registros = []
        cliente = self.obtener_cliente()

        if cliente:
            try:
                try:
                    resp = cliente.table("registros_triaje").select("*, resultados_ia(*)").execute()
                    if resp.data:
                        todos_los_registros = resp.data
                except Exception:
                    resp = cliente.table("triage_record").select("*, ai_result(*)").execute()
                    if resp.data:
                        todos_los_registros = resp.data
            except Exception as e:
                logger.error(f"Error al consultar cola médica en Supabase: {e}")

        ids_vistos = set()
        for r in todos_los_registros:
            r_id = r.get("id")
            if r_id:
                ids_vistos.add(r_id)

        for k, r in _BD_LOCAL_TRIAJES.items():
            r_id = r.get("id")
            if r_id and r_id not in ids_vistos:
                ids_vistos.add(r_id)
                copia = dict(r)
                copia["resultados_ia"] = _BD_LOCAL_RESULTADOS_IA.get(r_id)
                copia["ai_result"] = _BD_LOCAL_RESULTADOS_IA.get(r_id)
                todos_los_registros.append(copia)

        # Mapa de pesos clínicos para ordenamiento por severidad
        peso_prioridad = {
            "ROJO": 1, "RED": 1,
            "AMARILLO": 2, "YELLOW": 2,
            "VERDE": 3, "GREEN": 3,
            None: 4, "": 4
        }

        # Ordenamiento homogéneo por prioridad y hora de llegada
        registros_ordenados = sorted(
            todos_los_registros,
            key=lambda r: (
                peso_prioridad.get(r.get("prioridad_final") or r.get("final_priority"), 4),
                r.get("creado_en") or r.get("created_at") or ""
            )
        )
        return registros_ordenados

    def guardar_revision_medica(
        self,
        triaje_id: str,
        medico_id: str,
        notas_medico: str,
        prioridad_ajustada: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registra la evaluación y diagnóstico realizado por el médico y pasa el estado a 'REVISADO'.
        """
        payload_revision = {
            "triaje_id": triaje_id,
            "medico_id": medico_id,
            "notas_medico": notas_medico,
            "prioridad_ajustada": prioridad_ajustada
        }

        cliente = self.obtener_cliente()
        if cliente:
            try:
                try:
                    cliente.table("revisiones_medicas").insert(payload_revision).execute()
                    cliente.table("registros_triaje").update({"estado": "REVISADO"}).eq("id", triaje_id).execute()
                except Exception:
                    cliente.table("medical_review").insert({
                        "triage_id": triaje_id,
                        "doctor_id": medico_id,
                        "doctor_notes": notas_medico,
                        "priority_adjusted": prioridad_ajustada
                    }).execute()
                    cliente.table("triage_record").update({"status": "REVIEWED"}).eq("id", triaje_id).execute()
            except Exception as e:
                logger.error(f"Error al guardar revisión médica en Supabase: {e}")

        # Fallback local
        if triaje_id in _BD_LOCAL_TRIAJES:
            _BD_LOCAL_TRIAJES[triaje_id]["estado"] = "REVISADO"
            _BD_LOCAL_TRIAJES[triaje_id]["status"] = "REVIEWED"
            if prioridad_ajustada:
                _BD_LOCAL_TRIAJES[triaje_id]["prioridad_final"] = prioridad_ajustada
                _BD_LOCAL_TRIAJES[triaje_id]["final_priority"] = prioridad_ajustada
        return {"estado": "exito", "status": "success", "triaje_id": triaje_id}

    def registrar_evento_auditoria(
        self,
        usuario_id: Optional[str],
        accion: str,
        recurso_id: Optional[str] = None,
        direccion_ip: Optional[str] = "127.0.0.1"
    ) -> Dict[str, Any]:
        """
        Inserta un registro inalterable en la bitácora de auditoría.
        """
        evento = {
            "usuario_id": usuario_id,
            "accion": accion,
            "recurso_id": recurso_id,
            "direccion_ip": direccion_ip
        }

        cliente = self.obtener_cliente()
        if cliente:
            try:
                try:
                    cliente.table("registros_auditoria").insert(evento).execute()
                except Exception:
                    cliente.table("audit_log").insert({
                        "user_id": usuario_id,
                        "action": accion,
                        "resource_id": recurso_id,
                        "ip_address": direccion_ip
                    }).execute()
            except Exception as e:
                logger.error(f"Error al insertar log de auditoría en Supabase: {e}")

        _BD_LOCAL_AUDITORIA.append(evento)
        return evento


# Instancia global del servicio Supabase en español
servicio_supabase = ServicioSupabase()
supabase_service = servicio_supabase
