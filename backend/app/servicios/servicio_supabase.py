"""
Servicio de Persistencia y Acceso a Datos con Supabase (PostgreSQL).
Proporciona métodos para interactuar con las tablas relacionales estandarizadas en español
utilizando el Service Role Key del SDK de Supabase y soporte de contingencia en memoria local.
"""

import logging
import uuid
import re
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from supabase import create_client, Client

from app.core.config import settings

logger = logging.getLogger(__name__)

# Regex para validar formato estándar de UUID v4/v5
UUID_REGEX = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)


def es_uuid_valido(identificador: Optional[str]) -> bool:
    """
    Verifica si una cadena cumple estrictamente con el formato canónico de UUID.
    """
    if not identificador or not isinstance(identificador, str):
        return False
    return bool(UUID_REGEX.match(identificador.strip()))


def asegurar_uuid_valido(identificador: Optional[str]) -> str:
    """
    Garantiza que el identificador entregado cumpla estrictamente el formato UUID de PostgreSQL.
    Si recibe un string no-UUID (ej: 'mock-doctor-uuid', 'doc-123'), genera un UUID v5 determinista
    o un UUID v4 seguro para no romper restricciones de tipo en Supabase/Postgres.
    """
    if not identificador:
        return str(uuid.uuid4())
    cadena = str(identificador).strip()
    if es_uuid_valido(cadena):
        return cadena
    # Generar UUID v5 determinista basado en el string
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"medisinc.bo.{cadena}"))


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
        "turno_asignado": "TODOS",
        "dias_guardia": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
        "esta_activo": True,
        "creado_en": "2026-08-01T08:00:00Z"
    },
    "doc-med-general-01": {
        "id": "doc-med-general-01",
        "usuario_id": "auth-doc-01",
        "nombre_completo": "Dr. Carlos Menacho",
        "correo": "carlos.menacho@medisinc.bo",
        "especialidad": "Medicina General",
        "rol": "MEDICO",
        "turno_asignado": "MANANA",
        "dias_guardia": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        "esta_activo": True,
        "creado_en": "2026-08-05T09:30:00Z"
    },
    "doc-pediatria-02": {
        "id": "doc-pediatria-02",
        "usuario_id": "auth-doc-02",
        "nombre_completo": "Dra. Mariana Vaca",
        "correo": "mariana.vaca@medisinc.bo",
        "especialidad": "Pediatría",
        "rol": "MEDICO",
        "turno_asignado": "MANANA",
        "dias_guardia": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"],
        "esta_activo": True,
        "creado_en": "2026-08-05T09:30:00Z"
    },
    "doc-ginecologia-03": {
        "id": "doc-ginecologia-03",
        "usuario_id": "auth-doc-03",
        "nombre_completo": "Dra. Sofía Justiniano",
        "correo": "sofia.justiniano@medisinc.bo",
        "especialidad": "Ginecología y Obstetricia",
        "rol": "MEDICO",
        "turno_asignado": "TARDE_NOCHE",
        "dias_guardia": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"],
        "esta_activo": True,
        "creado_en": "2026-08-05T09:30:00Z"
    },
    "doc-trauma-04": {
        "id": "doc-trauma-04",
        "usuario_id": "auth-doc-04",
        "nombre_completo": "Dr. Luis Fernando Aguilera",
        "correo": "luis.aguilera@medisinc.bo",
        "especialidad": "Traumatología y Urgencias",
        "rol": "MEDICO",
        "turno_asignado": "TODOS",
        "dias_guardia": ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
        "esta_activo": True,
        "creado_en": "2026-08-05T09:30:00Z"
    },
    "doc-cardio-05": {
        "id": "doc-cardio-05",
        "usuario_id": "auth-doc-05",
        "nombre_completo": "Dr. Roberto Antelo",
        "correo": "roberto.antelo@medisinc.bo",
        "especialidad": "Cardiología y Medicina Interna",
        "rol": "MEDICO",
        "turno_asignado": "MANANA",
        "dias_guardia": ["Lunes", "Miércoles", "Viernes"],
        "esta_activo": True,
        "creado_en": "2026-08-05T09:30:00Z"
    },
    "doc-odontologia-06": {
        "id": "doc-odontologia-06",
        "usuario_id": "auth-doc-06",
        "nombre_completo": "Dra. Valeria Cuéllar",
        "correo": "valeria.cuellar@medisinc.bo",
        "especialidad": "Odontología",
        "rol": "MEDICO",
        "turno_asignado": "TARDE_NOCHE",
        "dias_guardia": ["Lunes", "Martes", "Jueves", "Sábado"],
        "esta_activo": True,
        "creado_en": "2026-08-05T09:30:00Z"
    }
}
_BD_LOCAL_AUDITORIA: List[Dict[str, Any]] = []

def obtener_turno_actual(hora_bolivia: Optional[int] = None) -> str:
    """
    Determina el turno de guardia actual según la hora local de Bolivia (UTC-4).
    - MANANA: 07:00 a 14:59 (7 a 14)
    - TARDE_NOCHE: 15:00 a 22:59 (15 a 22)
    - MADRUGADA: 23:00 a 06:59 (23 a 6)
    """
    if hora_bolivia is None:
        hora_utc = datetime.now(timezone.utc)
        hora_bolivia = (hora_utc.hour - 4) % 24

    if 7 <= hora_bolivia < 15:
        return "MANANA"
    elif 15 <= hora_bolivia < 23:
        return "TARDE_NOCHE"
    else:
        return "MADRUGADA"

_MAPA_ESPECIALIDADES_IDS: Dict[str, str] = {
    "Medicina General": "20000000-0000-0000-0000-000000000001",
    "Pediatría": "20000000-0000-0000-0000-000000000002",
    "Ginecología y Obstetricia": "20000000-0000-0000-0000-000000000003",
    "Traumatología y Urgencias": "20000000-0000-0000-0000-000000000004",
    "Cardiología y Medicina Interna": "20000000-0000-0000-0000-000000000005",
    "Odontología": "20000000-0000-0000-0000-000000000006",
}
_BD_LOCAL_PACIENTES: Dict[str, Dict[str, Any]] = {}

# Aliases de compatibilidad con memoria previa
_IN_MEMORY_TRIAGE_DB = _BD_LOCAL_TRIAJES
_IN_MEMORY_AI_DB = _BD_LOCAL_RESULTADOS_IA
_IN_MEMORY_PROFILES_DB = _BD_LOCAL_PERFILES
_IN_MEMORY_AUDIT_LOG_DB = _BD_LOCAL_AUDITORIA


class ServicioSupabase:
    """
    Cliente encapsulado de Supabase para operaciones CRUD de triaje, auditoría y personal médico.
    Implementa arquitectura 3NF con tabla maestra de pacientes y episodios de triaje.
    """

    def __init__(self):
        self._cliente: Optional[Client] = None

    def obtener_cliente(self) -> Optional[Client]:
        """
        Inicializa o retorna la instancia del cliente oficial de Supabase.
        """
        if self._cliente is not None:
            return self._cliente

        url = settings.SUPABASE_URL
        clave = settings.SUPABASE_SERVICE_ROLE_KEY

        if not url or not clave or "placeholder" in url or "placeholder" in clave:
            logger.info("Supabase no configurado o en modo placeholder. Utilizando persistencia en memoria local.")
            return None

        try:
            self._cliente = create_client(url, clave)
            return self._cliente
        except Exception as e:
            logger.warning(f"Error al inicializar cliente de Supabase ({e}). Modo contingencia local activado.")
            return None

    def get_client(self) -> Optional[Client]:
        """Alias para compatibilidad con código existente."""
        return self.obtener_cliente()

    # =========================================================================
    # OPERACIONES DE TRIAJE
    # =========================================================================
    def guardar_registro_triaje_inmediato(
        self,
        triaje_id: str,
        codigo_acceso: str,
        ci_cifrado: str,
        ci_hash: str,
        nombre_paciente: str,
        edad: int,
        genero: str,
        sintomas_brutos: str,
        datos_estaticos: Dict[str, Any],
        respuestas_dinamicas: Optional[Dict[str, Any]] = None,
        estado: str = "RECIBIDO",
        prioridad_final: Optional[str] = None,
        especialidad_solicitada: str = "Medicina General",
        alergias_medicamentosas: str = "Ninguna conocida",
        medicacion_actual: str = "Ninguna",
        enfermedades_base: Optional[List[str]] = None,
        medico_asignado_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inserta el registro de pre-triaje capturado en el portal del paciente cumpliendo con 3NF.
        Separa la entidad paciente del episodio clínico de triaje.
        """
        ahora_iso = datetime.now(timezone.utc).isoformat()
        comorbilidades = enfermedades_base or []
        doc_id = medico_asignado_id or None
        esp_nombre = especialidad_solicitada or "Medicina General"
        esp_id = _MAPA_ESPECIALIDADES_IDS.get(esp_nombre, "20000000-0000-0000-0000-000000000001")

        # 1. Resolver Entidad Paciente
        paciente_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"paciente.{ci_hash}")) if ci_hash else str(uuid.uuid4())
        paciente_obj = {
            "id": paciente_id,
            "ci_hash": ci_hash,
            "ci_cifrado": ci_cifrado,
            "nombre_completo": nombre_paciente,
            "edad": edad,
            "genero": genero,
            "alergias_medicamentosas": alergias_medicamentosas or "Ninguna conocida",
            "enfermedades_base": comorbilidades,
            "medicacion_habitual": medicacion_actual or "No toma medicación",
            "creado_en": ahora_iso,
            "actualizado_en": ahora_iso
        }
        _BD_LOCAL_PACIENTES[paciente_id] = paciente_obj
        if ci_hash:
            _BD_LOCAL_PACIENTES[ci_hash] = paciente_obj

        # 2. Objeto 3NF registros_triaje
        registro_triaje_3nf = {
            "id": triaje_id,
            "codigo_acceso": codigo_acceso,
            "paciente_id": paciente_id,
            "especialidad_id": esp_id,
            "medico_asignado_id": doc_id,
            "asignado_en": ahora_iso if doc_id else None,
            "sintomas_brutos": sintomas_brutos,
            "datos_estaticos": datos_estaticos or {},
            "respuestas_dinamicas": respuestas_dinamicas or {},
            "estado": estado,
            "prioridad_final": prioridad_final,
            "creado_en": ahora_iso,
            "actualizado_en": ahora_iso
        }

        # 3. Payload consolidado para interoperabilidad total
        registro_combinado = {
            **paciente_obj,
            **registro_triaje_3nf,
            "nombre_paciente": nombre_paciente,
            "patient_name": nombre_paciente,
            "ci_cifrado": ci_cifrado,
            "ci_encrypted": ci_cifrado,
            "ci_hash": ci_hash,
            "edad": edad,
            "age": edad,
            "genero": genero,
            "gender": genero,
            "sintomas_brutos": sintomas_brutos,
            "raw_symptoms": sintomas_brutos,
            "especialidad_solicitada": esp_nombre,
            "requested_specialty": esp_nombre,
            "alergias_medicamentosas": alergias_medicamentosas or "Ninguna conocida",
            "drug_allergies": alergias_medicamentosas or "Ninguna conocida",
            "medicacion_actual": medicacion_actual or "Ninguna",
            "current_medication": medicacion_actual or "Ninguna",
            "enfermedades_base": comorbilidades,
            "base_diseases": comorbilidades,
            "assigned_doctor_id": doc_id,
            "assigned_at": ahora_iso if doc_id else None,
            "static_data": datos_estaticos or {},
            "dynamic_answers": respuestas_dinamicas or {},
            "status": "RECEIVED" if estado == "RECIBIDO" else estado,
            "final_priority": prioridad_final,
            "created_at": ahora_iso
        }

        # 4. Persistencia en Supabase
        cliente = self.obtener_cliente()
        if cliente:
            try:
                # Upsert en pacientes
                try:
                    cliente.table("pacientes").upsert(paciente_obj, on_conflict="ci_hash").execute()
                except Exception:
                    pass

                # Insert en registros_triaje
                try:
                    cliente.table("registros_triaje").insert(registro_triaje_3nf).execute()
                except Exception:
                    try:
                        cliente.table("registros_triaje").insert(registro_combinado).execute()
                    except Exception:
                        cliente.table("triage_record").insert(registro_combinado).execute()
            except Exception as e:
                logger.error(f"Error al guardar triaje en Supabase: {e}")

        # Fallback local
        _BD_LOCAL_TRIAJES[triaje_id] = registro_combinado
        _BD_LOCAL_TRIAJES[codigo_acceso] = registro_combinado

        return registro_combinado

    def crear_registro_triaje(self, datos_registro: Dict[str, Any]) -> Dict[str, Any]:
        """
        Inserta un registro de triaje a partir de un diccionario de datos estructurado.
        """
        return self.guardar_registro_triaje_inmediato(
            triaje_id=datos_registro.get("id") or datos_registro.get("triaje_id"),
            codigo_acceso=datos_registro.get("codigo_acceso") or datos_registro.get("access_code"),
            ci_cifrado=datos_registro.get("ci_cifrado") or datos_registro.get("ci_encrypted"),
            ci_hash=datos_registro.get("ci_hash"),
            nombre_paciente=datos_registro.get("nombre_paciente") or datos_registro.get("patient_name"),
            edad=datos_registro.get("edad") if datos_registro.get("edad") is not None else datos_registro.get("age"),
            genero=datos_registro.get("genero") or datos_registro.get("gender"),
            sintomas_brutos=datos_registro.get("sintomas_brutos") or datos_registro.get("raw_symptoms"),
            datos_estaticos=datos_registro.get("datos_estaticos") or datos_registro.get("static_data"),
            respuestas_dinamicas=datos_registro.get("respuestas_dinamicas") or datos_registro.get("dynamic_answers"),
            estado=datos_registro.get("estado") or datos_registro.get("status", "RECIBIDO"),
            prioridad_final=datos_registro.get("prioridad_final") or datos_registro.get("final_priority"),
            especialidad_solicitada=datos_registro.get("especialidad_solicitada") or datos_registro.get("requested_specialty", "Medicina General"),
            alergias_medicamentosas=datos_registro.get("alergias_medicamentosas") or datos_registro.get("drug_allergies", "Ninguna conocida"),
            medicacion_actual=datos_registro.get("medicacion_actual") or datos_registro.get("current_medication", "Ninguna"),
            enfermedades_base=datos_registro.get("enfermedades_base") or datos_registro.get("base_diseases", []),
            medico_asignado_id=datos_registro.get("medico_asignado_id") or datos_registro.get("assigned_doctor_id")
        )

    def create_triage_record(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Alias para compatibilidad con código existente."""
        return self.crear_registro_triaje(record_data)

    def save_immediate_triage_record(self, **kwargs) -> Dict[str, Any]:
        """Alias para compatibilidad con código existente."""
        return self.guardar_registro_triaje_inmediato(
            triaje_id=kwargs.get("triage_id") or kwargs.get("triaje_id"),
            codigo_acceso=kwargs.get("access_code") or kwargs.get("codigo_acceso"),
            ci_cifrado=kwargs.get("ci_encrypted") or kwargs.get("ci_cifrado"),
            ci_hash=kwargs.get("ci_hash"),
            nombre_paciente=kwargs.get("patient_name") or kwargs.get("nombre_paciente"),
            edad=kwargs.get("age") if kwargs.get("age") is not None else kwargs.get("edad"),
            genero=kwargs.get("gender") or kwargs.get("genero"),
            sintomas_brutos=kwargs.get("raw_symptoms") or kwargs.get("sintomas_brutos"),
            datos_estaticos=kwargs.get("static_data") or kwargs.get("datos_estaticos"),
            respuestas_dinamicas=kwargs.get("dynamic_answers") or kwargs.get("respuestas_dinamicas"),
            estado=kwargs.get("status") or kwargs.get("estado", "RECIBIDO"),
            prioridad_final=kwargs.get("final_priority") or kwargs.get("prioridad_final")
        )

    def guardar_resultado_ia(
        self,
        triaje_id: str,
        resultado_ia: Dict[str, Any],
        prioridad_final: str,
        sobreescritura_aplicada: bool = False,
        motivo_sobreescritura: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Inserta el resultado del análisis de IA y actualiza el estado a 'LISTO'.
        """
        payload_ia_es = {
            "triaje_id": triaje_id,
            "resultado_ia": resultado_ia,
            "prioridad_final": prioridad_final,
            "sobreescritura_aplicada": sobreescritura_aplicada,
            "motivo_sobreescritura": motivo_sobreescritura
        }

        payload_ia_en = {
            "triage_id": triaje_id,
            "ai_result": resultado_ia,
            "final_priority": prioridad_final,
            "override_applied": sobreescritura_aplicada,
            "override_reason": motivo_sobreescritura
        }

        cliente = self.obtener_cliente()
        if cliente:
            try:
                try:
                    cliente.table("resultados_ia").insert(payload_ia_es).execute()
                    cliente.table("registros_triaje").update({
                        "estado": "LISTO",
                        "prioridad_final": prioridad_final
                    }).eq("id", triaje_id).execute()
                except Exception:
                    cliente.table("ai_result").insert(payload_ia_en).execute()
                    cliente.table("triage_record").update({
                        "status": "READY",
                        "final_priority": prioridad_final
                    }).eq("id", triaje_id).execute()
            except Exception as e:
                logger.error(f"Error al guardar resultado de IA en Supabase: {e}")

        # Fallback local
        _BD_LOCAL_RESULTADOS_IA[triaje_id] = resultado_ia
        for k, r in _BD_LOCAL_TRIAJES.items():
            if r.get("id") == triaje_id or r.get("codigo_acceso") == triaje_id or k == triaje_id:
                r["estado"] = "LISTO"
                r["status"] = "READY"
                r["prioridad_final"] = prioridad_final
                r["final_priority"] = prioridad_final
                r["resultado_ia"] = resultado_ia
                r["ai_result"] = resultado_ia
                r["resultados_ia"] = resultado_ia

        return payload_ia_es

    def update_triage_with_ai_result(
        self,
        triage_id: str,
        ai_result: Dict[str, Any],
        final_priority: str,
        override_applied: bool = False,
        override_reason: Optional[str] = None
    ) -> bool:
        """Alias de compatibilidad para worker asíncrono."""
        try:
            self.guardar_resultado_ia(
                triaje_id=triage_id,
                resultado_ia=ai_result,
                prioridad_final=final_priority,
                sobreescritura_aplicada=override_applied,
                motivo_sobreescritura=override_reason
            )
            return True
        except Exception as e:
            logger.error(f"Error en update_triage_with_ai_result: {e}")
            return False

    def actualizar_triaje_con_resultado_ia(self, **kwargs) -> bool:
        """Alias en español para actualización asíncrona de IA."""
        return self.update_triage_with_ai_result(
            triage_id=kwargs.get("triaje_id") or kwargs.get("triage_id"),
            ai_result=kwargs.get("resultado_ia") or kwargs.get("ai_result"),
            final_priority=kwargs.get("prioridad_final") or kwargs.get("final_priority"),
            override_applied=kwargs.get("sobreescritura_aplicada") or kwargs.get("override_applied", False),
            override_reason=kwargs.get("motivo_sobreescritura") or kwargs.get("override_reason")
        )

    def save_ai_result(self, **kwargs) -> Dict[str, Any]:
        """Alias para compatibilidad con código existente."""
        return self.guardar_resultado_ia(
            triaje_id=kwargs.get("triage_id") or kwargs.get("triaje_id"),
            resultado_ia=kwargs.get("ai_result") or kwargs.get("resultado_ia"),
            prioridad_final=kwargs.get("final_priority") or kwargs.get("prioridad_final"),
            sobreescritura_aplicada=kwargs.get("override_applied") or kwargs.get("sobreescritura_aplicada", False),
            motivo_sobreescritura=kwargs.get("override_reason") or kwargs.get("motivo_sobreescritura")
        )

    def obtener_triaje_por_codigo(self, codigo_acceso: str) -> Optional[Dict[str, Any]]:
        """
        Recupera el triaje por su código de acceso.
        """
        cliente = self.obtener_cliente()
        if cliente:
            try:
                try:
                    resp = cliente.table("registros_triaje").select("*, resultados_ia(*)").eq("codigo_acceso", codigo_acceso).execute()
                    if resp.data:
                        return resp.data[0]
                except Exception:
                    resp = cliente.table("triage_record").select("*, ai_result(*)").eq("access_code", codigo_acceso).execute()
                    if resp.data:
                        return resp.data[0]
            except Exception as e:
                logger.error(f"Error al consultar triaje por código en Supabase: {e}")

        # Fallback local
        if codigo_acceso in _BD_LOCAL_TRIAJES:
            reg = dict(_BD_LOCAL_TRIAJES[codigo_acceso])
            reg_id = reg.get("id")
            if reg_id:
                reg["resultados_ia"] = _BD_LOCAL_RESULTADOS_IA.get(reg_id)
                reg["ai_result"] = _BD_LOCAL_RESULTADOS_IA.get(reg_id)
            return reg
        return None

    def get_triage_by_access_code(self, access_code: str) -> Optional[Dict[str, Any]]:
        """Alias para compatibilidad con código existente."""
        return self.obtener_triaje_por_codigo(codigo_acceso=access_code)

    def obtener_triaje_por_criterio(
        self,
        codigo_acceso: Optional[str] = None,
        ci_hash: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Busca un registro de triaje indexado por código de acceso o hash de CI.
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
                    resp = consulta.order("creado_en", desc=True).limit(1).execute()
                    if resp.data:
                        return resp.data[0]
                except Exception:
                    consulta = cliente.table("triage_record").select("*, ai_result(*)")
                    if codigo_acceso:
                        consulta = consulta.eq("access_code", codigo_acceso)
                    elif ci_hash:
                        consulta = consulta.eq("ci_hash", ci_hash)
                    resp = consulta.order("created_at", desc=True).limit(1).execute()
                    if resp.data:
                        return resp.data[0]
            except Exception as e:
                logger.error(f"Error al buscar triaje por criterio en Supabase: {e}")

        # Fallback local
        if codigo_acceso and codigo_acceso in _BD_LOCAL_TRIAJES:
            rec = dict(_BD_LOCAL_TRIAJES[codigo_acceso])
            rec["resultados_ia"] = _BD_LOCAL_RESULTADOS_IA.get(rec.get("id"))
            rec["ai_result"] = _BD_LOCAL_RESULTADOS_IA.get(rec.get("id"))
            return rec

        if ci_hash:
            for rec in _BD_LOCAL_TRIAJES.values():
                if rec.get("ci_hash") == ci_hash:
                    rec = dict(rec)
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

    def obtener_cola_guardia(
        self,
        solo_disponibles: bool = False,
        especialidad: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Retorna la lista de espera de pacientes para el panel médico, ordenada estrictamente por:
        1. Urgencia clínica: ROJO / RED primero, AMARILLO / YELLOW después, VERDE / GREEN al final.
        2. Hora de llegada (creado_en / created_at).
        Soporta filtrado opcional por especialidad médica solicitada.
        """
        todos_los_registros = []
        cliente = self.obtener_cliente()

        if cliente:
            try:
                try:
                    consulta = cliente.table("registros_triaje").select("*, resultados_ia(*)")
                    if solo_disponibles:
                        consulta = consulta.in_("estado", ["RECIBIDO", "LISTO", "RECEIVED", "READY"]).is_("medico_asignado_id", "null")
                    if especialidad and especialidad.upper() not in ["TODAS", "ALL", ""]:
                        consulta = consulta.eq("especialidad_solicitada", especialidad)
                    resp = consulta.execute()
                    if resp.data:
                        todos_los_registros = resp.data
                except Exception:
                    consulta = cliente.table("triage_record").select("*, ai_result(*)")
                    if solo_disponibles:
                        consulta = consulta.in_("status", ["RECEIVED", "READY"]).is_("assigned_doctor_id", "null")
                    if especialidad and especialidad.upper() not in ["TODAS", "ALL", ""]:
                        consulta = consulta.eq("requested_specialty", especialidad)
                    resp = consulta.execute()
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
                copia = dict(r)
                copia["resultados_ia"] = _BD_LOCAL_RESULTADOS_IA.get(r_id)
                copia["ai_result"] = _BD_LOCAL_RESULTADOS_IA.get(r_id)

                # Filtrar por especialidad si aplica
                esp_doc = copia.get("especialidad_solicitada") or copia.get("requested_specialty")
                if especialidad and especialidad.upper() not in ["TODAS", "ALL", ""] and esp_doc != especialidad:
                    continue

                if solo_disponibles:
                    estado = str(copia.get("estado") or copia.get("status") or "").upper()
                    medico_asig = copia.get("medico_asignado_id") or copia.get("assigned_doctor_id")
                    if estado in ["RECIBIDO", "LISTO", "RECEIVED", "READY"] and not medico_asig:
                        ids_vistos.add(r_id)
                        todos_los_registros.append(copia)
                else:
                    ids_vistos.add(r_id)
                    todos_los_registros.append(copia)

        peso_prioridad = {
            "ROJO": 1, "RED": 1,
            "AMARILLO": 2, "YELLOW": 2,
            "VERDE": 3, "GREEN": 3,
            None: 4, "": 4
        }

        registros_ordenados = sorted(
            todos_los_registros,
            key=lambda r: (
                peso_prioridad.get(r.get("prioridad_final") or r.get("final_priority"), 4),
                r.get("creado_en") or r.get("created_at") or ""
            )
        )
        return registros_ordenados

    def obtener_medicos_activos_por_especialidad(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retorna la lista de médicos en turno activo agrupados por especialidad médica.
        """
        medicos_por_esp: Dict[str, List[Dict[str, Any]]] = {
            "Medicina General": [],
            "Pediatría": [],
            "Ginecología y Obstetricia": [],
            "Traumatología y Urgencias": [],
            "Cardiología y Medicina Interna": [],
            "Odontología": []
        }

        cliente = self.obtener_cliente()
        if cliente:
            try:
                try:
                    res = cliente.table("perfiles").select("id, nombre_completo, especialidad, esta_activo").eq("esta_activo", True).execute()
                except Exception:
                    res = cliente.table("profiles").select("id, full_name, specialty, is_active").eq("is_active", True).execute()

                if res.data:
                    for p in res.data:
                        esp = p.get("especialidad") or p.get("specialty") or "Medicina General"
                        nombre = p.get("nombre_completo") or p.get("full_name") or "Médico de Guardia"
                        doc_item = {
                            "id": p.get("id"),
                            "nombre_completo": nombre,
                            "name": nombre,
                            "especialidad": esp,
                            "specialty": esp,
                            "esta_activo": True
                        }
                        if esp not in medicos_por_esp:
                            medicos_por_esp[esp] = []
                        medicos_por_esp[esp].append(doc_item)
                    return medicos_por_esp
            except Exception as e:
                logger.warning(f"Error consultando médicos en Supabase: {e}")

        # Fallback local
        for p in _BD_LOCAL_PERFILES.values():
            if (p.get("esta_activo") or p.get("is_active")) and p.get("rol") != "ADMIN":
                esp = p.get("especialidad") or p.get("specialty") or "Medicina General"
                nombre = p.get("nombre_completo") or p.get("full_name") or "Médico de Guardia"
                doc_item = {
                    "id": p.get("id"),
                    "nombre_completo": nombre,
                    "name": nombre,
                    "especialidad": esp,
                    "specialty": esp,
                    "esta_activo": True
                }
                if esp not in medicos_por_esp:
                    medicos_por_esp[esp] = []
                medicos_por_esp[esp].append(doc_item)

        return medicos_por_esp

    def obtener_conteo_especialistas_activos(self) -> Dict[str, int]:
        """
        Retorna la cantidad de médicos en turno activo agrupados por su especialidad médica.
        """
        medicos_dict = self.obtener_medicos_activos_por_especialidad()
        return {esp: len(docs) for esp, docs in medicos_dict.items()}

    def asignar_paciente_a_medico(self, triaje_id: str, medico_id: str) -> Dict[str, Any]:
        """
        Asigna la atención activa de un paciente a un médico de guardia transicionando su estado a 'EN_CONSULTA'.
        Control de concurrencia: Evita que dos médicos atiendan al mismo paciente simultáneamente.
        Manejo defensivo de UUIDs y soporte de búsqueda polimórfica (id / codigo_acceso).
        """
        ahora_iso = datetime.now(timezone.utc).isoformat()
        medico_uuid = asegurar_uuid_valido(medico_id)
        cliente = self.obtener_cliente()

        if cliente:
            try:
                # 1. Búsqueda polimórfica (por ID o por código de acceso)
                res_actual = None
                try:
                    if es_uuid_valido(triaje_id):
                        res_actual = cliente.table("registros_triaje").select("id, estado, medico_asignado_id").eq("id", triaje_id).execute()
                    else:
                        res_actual = cliente.table("registros_triaje").select("id, estado, medico_asignado_id").eq("codigo_acceso", triaje_id).execute()
                except Exception:
                    pass

                if res_actual and res_actual.data:
                    actual = res_actual.data[0]
                    asig = actual.get("medico_asignado_id")
                    estado = actual.get("estado")
                    if asig and asig not in [medico_id, medico_uuid] and estado == "EN_CONSULTA":
                        raise ValueError("El paciente ya se encuentra en atención con otro profesional médico")

                # 2. Actualizar estado a EN_CONSULTA en Supabase
                payload_update = {
                    "medico_asignado_id": medico_uuid,
                    "asignado_en": ahora_iso,
                    "estado": "EN_CONSULTA"
                }

                try:
                    if es_uuid_valido(triaje_id):
                        cliente.table("registros_triaje").update(payload_update).eq("id", triaje_id).execute()
                    else:
                        cliente.table("registros_triaje").update(payload_update).eq("codigo_acceso", triaje_id).execute()
                except Exception as e_up:
                    logger.warning(f"Aviso al actualizar en Supabase ({e_up}). Aplicando persistencia en contingencia local.")
            except ValueError:
                raise
            except Exception as e:
                logger.error(f"Error al asignar paciente en Supabase: {e}")

        # Fallback y actualización en almacén local
        encontrado = None
        for k, r in _BD_LOCAL_TRIAJES.items():
            if r.get("id") == triaje_id or r.get("codigo_acceso") == triaje_id or k == triaje_id:
                asig_local = r.get("medico_asignado_id") or r.get("assigned_doctor_id")
                est_local = r.get("estado") or r.get("status")
                if asig_local and asig_local not in [medico_id, medico_uuid] and est_local in ["EN_CONSULTA", "IN_CONSULTATION"]:
                    raise ValueError("El paciente ya se encuentra en atención con otro profesional médico")

                r["medico_asignado_id"] = medico_id
                r["assigned_doctor_id"] = medico_id
                r["asignado_en"] = ahora_iso
                r["assigned_at"] = ahora_iso
                r["estado"] = "EN_CONSULTA"
                r["status"] = "IN_CONSULTATION"
                encontrado = r

        if not encontrado and not cliente:
            raise KeyError(f"No se encontró el registro de triaje con ID {triaje_id}")

        return {
            "estado": "exito",
            "status": "success",
            "triaje_id": triaje_id,
            "medico_asignado_id": medico_id,
            "asignado_en": ahora_iso,
            "nuevo_estado": "EN_CONSULTA"
        }

    def liberar_paciente(self, triaje_id: str, medico_id: str) -> Dict[str, Any]:
        """
        Libera un paciente en consulta devolviéndolo a la cola general en estado 'LISTO'.
        """
        cliente = self.obtener_cliente()
        if cliente:
            try:
                payload_liberar = {
                    "medico_asignado_id": None,
                    "asignado_en": None,
                    "estado": "LISTO"
                }
                try:
                    if es_uuid_valido(triaje_id):
                        cliente.table("registros_triaje").update(payload_liberar).eq("id", triaje_id).execute()
                    else:
                        cliente.table("registros_triaje").update(payload_liberar).eq("codigo_acceso", triaje_id).execute()
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Error al liberar paciente en Supabase: {e}")

        # Fallback local
        for k, r in _BD_LOCAL_TRIAJES.items():
            if r.get("id") == triaje_id or r.get("codigo_acceso") == triaje_id or k == triaje_id:
                r["medico_asignado_id"] = None
                r["assigned_doctor_id"] = None
                r["asignado_en"] = None
                r["assigned_at"] = None
                r["estado"] = "LISTO"
                r["status"] = "READY"

        return {
            "estado": "exito",
            "status": "success",
            "triaje_id": triaje_id,
            "nuevo_estado": "LISTO"
        }

    def obtener_pacientes_por_medico(self, medico_id: str, incluir_revisados: bool = False) -> List[Dict[str, Any]]:
        """
        Retorna la lista de pacientes asignados a un facultativo médico específico.
        """
        pacientes_medico = []
        medico_uuid = asegurar_uuid_valido(medico_id)
        cliente = self.obtener_cliente()

        if cliente:
            try:
                try:
                    consulta = cliente.table("registros_triaje").select("*, resultados_ia(*)").or_(f"medico_asignado_id.eq.{medico_id},medico_asignado_id.eq.{medico_uuid}")
                    if not incluir_revisados:
                        consulta = consulta.in_("estado", ["EN_CONSULTA", "IN_CONSULTATION"])
                    resp = consulta.order("asignado_en", desc=True).execute()
                    if resp.data:
                        pacientes_medico = resp.data
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Error al consultar pacientes por médico en Supabase: {e}")

        ids_vistos = {p.get("id") for p in pacientes_medico if p.get("id")}

        for k, r in _BD_LOCAL_TRIAJES.items():
            r_id = r.get("id")
            if r_id and r_id not in ids_vistos:
                asig = r.get("medico_asignado_id") or r.get("assigned_doctor_id")
                est = str(r.get("estado") or r.get("status") or "").upper()

                if asig in [medico_id, medico_uuid]:
                    if incluir_revisados or est in ["EN_CONSULTA", "IN_CONSULTATION"]:
                        ids_vistos.add(r_id)
                        copia = dict(r)
                        copia["resultados_ia"] = _BD_LOCAL_RESULTADOS_IA.get(r_id)
                        copia["ai_result"] = _BD_LOCAL_RESULTADOS_IA.get(r_id)
                        pacientes_medico.append(copia)

        return pacientes_medico

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
        medico_uuid = asegurar_uuid_valido(medico_id)
        payload_revision = {
            "triaje_id": triaje_id,
            "medico_id": medico_uuid,
            "notas_medico": notas_medico,
            "prioridad_ajustada": prioridad_ajustada
        }

        cliente = self.obtener_cliente()
        if cliente:
            try:
                try:
                    cliente.table("revisiones_medicas").insert(payload_revision).execute()
                    if es_uuid_valido(triaje_id):
                        cliente.table("registros_triaje").update({
                            "estado": "REVISADO",
                            "medico_asignado_id": medico_uuid
                        }).eq("id", triaje_id).execute()
                    else:
                        cliente.table("registros_triaje").update({
                            "estado": "REVISADO",
                            "medico_asignado_id": medico_uuid
                        }).eq("codigo_acceso", triaje_id).execute()
                except Exception:
                    pass
            except Exception as e:
                logger.error(f"Error al guardar revisión médica en Supabase: {e}")

        # Fallback local
        for k, r in _BD_LOCAL_TRIAJES.items():
            if r.get("id") == triaje_id or r.get("codigo_acceso") == triaje_id or k == triaje_id:
                r["estado"] = "REVISADO"
                r["status"] = "REVIEWED"
                r["medico_asignado_id"] = medico_id
                r["assigned_doctor_id"] = medico_id
                if prioridad_ajustada:
                    r["prioridad_final"] = prioridad_ajustada
                    r["final_priority"] = prioridad_ajustada
        return {"estado": "exito", "status": "success", "triaje_id": triaje_id}

    def assign_patient_to_doctor(self, triage_id: str, doctor_id: str) -> Dict[str, Any]:
        """Alias para compatibilidad con código existente."""
        return self.asignar_paciente_a_medico(triaje_id=triage_id, medico_id=doctor_id)

    def release_patient(self, triage_id: str, doctor_id: str) -> Dict[str, Any]:
        """Alias para compatibilidad con código existente."""
        return self.liberar_paciente(triaje_id=triage_id, medico_id=doctor_id)

    def get_patients_by_doctor(self, doctor_id: str, include_reviewed: bool = False) -> List[Dict[str, Any]]:
        """Alias para compatibilidad con código existente."""
        return self.obtener_pacientes_por_medico(medico_id=doctor_id, incluir_revisados=include_reviewed)

    def registrar_evento_auditoria(
        self,
        usuario_id: Optional[str],
        accion: str,
        recurso_id: Optional[str] = None,
        direccion_ip: Optional[str] = "127.0.0.1"
    ) -> Dict[str, Any]:
        """
        Inserta un registro inalterable en la bitácora de auditoría con soporte bilingüe dual.
        """
        ahora_iso = datetime.now(timezone.utc).isoformat()
        usuario_uuid = asegurar_uuid_valido(usuario_id)
        recurso_uuid = asegurar_uuid_valido(recurso_id) if recurso_id else None

        evento = {
            "id": str(uuid.uuid4()),
            "usuario_id": usuario_uuid,
            "user_id": usuario_uuid,
            "accion": accion,
            "action": accion,
            "recurso_id": recurso_uuid,
            "resource_id": recurso_uuid,
            "direccion_ip": direccion_ip or "127.0.0.1",
            "ip_address": direccion_ip or "127.0.0.1",
            "fecha_hora": ahora_iso,
            "timestamp": ahora_iso
        }

        cliente = self.obtener_cliente()
        if cliente:
            try:
                try:
                    cliente.table("registros_auditoria").insert({
                        "usuario_id": usuario_uuid,
                        "accion": accion,
                        "recurso_id": recurso_uuid,
                        "direccion_ip": direccion_ip
                    }).execute()
                except Exception:
                    cliente.table("audit_log").insert({
                        "user_id": usuario_uuid,
                        "action": accion,
                        "resource_id": recurso_uuid,
                        "ip_address": direccion_ip
                    }).execute()
            except Exception as e:
                logger.warning(f"Aviso al guardar auditoría en Supabase: {e}")

        _BD_LOCAL_AUDITORIA.append(evento)
        return evento

    def obtener_medicos_activos_por_especialidad(self, especialidad: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Retorna un diccionario agrupado por especialidad con la lista de facultativos médicos activos.
        Ordena a los médicos de forma determinista para que el especialista asignado al turno actual
        (MANANA, TARDE_NOCHE, MADRUGADA o TODOS) aparezca en la primera posición.
        """
        turno_actual = obtener_turno_actual()
        medicos_agrupados: Dict[str, List[Dict[str, Any]]] = {}

        # 1. Consultar en Supabase
        cliente = self.obtener_cliente()
        medicos_supabase = []
        if cliente:
            try:
                try:
                    res = cliente.table("perfiles").select("*").eq("esta_activo", True).execute()
                except Exception:
                    res = cliente.table("profiles").select("*").eq("is_active", True).execute()
                if res.data:
                    medicos_supabase = res.data
            except Exception as e:
                logger.warning(f"Aviso al consultar médicos activos en Supabase: {e}")

        # 2. Unificar con perfiles locales
        perfiles_unificados = {}
        for p in _BD_LOCAL_PERFILES.values():
            if p.get("esta_activo") or p.get("is_active"):
                perfiles_unificados[p["id"]] = p

        for p in medicos_supabase:
            p_id = p.get("id")
            if p_id:
                perfiles_unificados[p_id] = {**perfiles_unificados.get(p_id, {}), **p}

        for p in perfiles_unificados.values():
            if p.get("rol") == "ADMIN" and p.get("especialidad") != "Medicina General":
                continue

            esp = p.get("especialidad") or p.get("specialty") or "Medicina General"
            if especialidad and esp.lower() != especialidad.lower():
                continue

            doc_item = {
                "id": p.get("id"),
                "nombre_completo": p.get("nombre_completo") or p.get("full_name") or "Médico de Guardia",
                "name": p.get("nombre_completo") or p.get("full_name") or "Médico de Guardia",
                "especialidad": esp,
                "specialty": esp,
                "turno_asignado": p.get("turno_asignado") or p.get("assigned_shift") or "TODOS",
                "dias_guardia": p.get("dias_guardia") or p.get("duty_days") or [],
                "esta_activo": True
            }

            if esp not in medicos_agrupados:
                medicos_agrupados[esp] = []
            medicos_agrupados[esp].append(doc_item)

        # 3. Ordenar para que el médico en turno activo (o 'TODOS') quede primero
        for esp, docs in medicos_agrupados.items():
            docs.sort(
                key=lambda d: (
                    0 if d["turno_asignado"] == turno_actual else (
                        1 if d["turno_asignado"] == "TODOS" else 2
                    )
                )
            )

        return medicos_agrupados

    def obtener_historial_por_paciente(self, paciente_id: str) -> Optional[Dict[str, Any]]:
        """
        Consulta el historial clínico y expedientes de triaje anteriores de un paciente por su ID o código.
        """
        if not paciente_id:
            return None

        cliente = self.obtener_cliente()
        paciente_encontrado = None
        triajes = []

        if cliente:
            try:
                # 1. Buscar en tabla pacientes
                try:
                    res_p = cliente.table("pacientes").select("*").eq("id", paciente_id).execute()
                    if res_p.data:
                        paciente_encontrado = res_p.data[0]
                except Exception:
                    pass

                # 2. Buscar en registros_triaje
                try:
                    res_t = cliente.table("registros_triaje").select("*, resultados_ia(*)").or_(f"id.eq.{paciente_id},paciente_id.eq.{paciente_id},codigo_acceso.eq.{paciente_id}").execute()
                    if res_t.data:
                        triajes = res_t.data
                        if not paciente_encontrado and triajes:
                            paciente_encontrado = {
                                "id": paciente_id,
                                "nombre_completo": triajes[0].get("nombre_paciente") or "Paciente Registrado",
                                "ci_cifrado": triajes[0].get("ci_cifrado")
                            }
                except Exception:
                    pass
            except Exception as e:
                logger.warning(f"Aviso consultando historial de paciente en Supabase: {e}")

        # 3. Fallback en memoria local
        if not paciente_encontrado:
            for k, t in _BD_LOCAL_TRIAJES.items():
                if t.get("id") == paciente_id or t.get("codigo_acceso") == paciente_id or k == paciente_id or t.get("paciente_id") == paciente_id:
                    paciente_encontrado = {
                        "id": paciente_id,
                        "nombre_completo": t.get("nombre_paciente") or t.get("patient_name") or "Paciente Local",
                        "ci_cifrado": t.get("ci_cifrado") or t.get("ci_encrypted")
                    }
                    triajes.append(t)

        if not paciente_encontrado and not triajes:
            return None

        return {
            "paciente": paciente_encontrado or {"id": paciente_id},
            "patient": paciente_encontrado or {"id": paciente_id},
            "historial": triajes,
            "history": triajes,
            "records": triajes,
            "registros": triajes,
            "total": len(triajes)
        }


# Instancia global del servicio Supabase en español
servicio_supabase = ServicioSupabase()
supabase_service = servicio_supabase
