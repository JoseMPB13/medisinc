"""
Repositorios en Memoria (Test Doubles / Fakes) para Aislamiento de Pruebas Unitarias.
Permite ejecutar suites de pruebas de alta velocidad sin dependencias de red.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

from app.repositorios.base import (
    IRepositorioTriaje,
    IRepositorioPacientes,
    IRepositorioMedicos,
    IRepositorioAuditoria
)
from app.esquemas.dominio import (
    RegistroTriajeDTO,
    PacienteDTO,
    PerfilMedicoDTO,
    EventoAuditoriaDTO,
    ResultadoIADTO
)


class RepositorioTriajeEnMemoria(IRepositorioTriaje):
    """Fake en memoria para pruebas de la capa de triaje."""

    def __init__(self):
        self._almacen: Dict[str, Dict[str, Any]] = {}

    async def guardar_triaje(self, datos_triaje: Dict[str, Any]) -> RegistroTriajeDTO:
        triaje_id = datos_triaje.get("id") or str(uuid.uuid4())
        self._almacen[triaje_id] = dict(datos_triaje)
        return RegistroTriajeDTO.model_validate(datos_triaje)

    async def obtener_por_id(self, triaje_id: str) -> Optional[RegistroTriajeDTO]:
        if triaje_id in self._almacen:
            return RegistroTriajeDTO.model_validate(self._almacen[triaje_id])
        return None

    async def obtener_por_codigo(self, codigo_acceso: str) -> Optional[RegistroTriajeDTO]:
        cod = codigo_acceso.upper().strip()
        for t in self._almacen.values():
            if (t.get("codigo_acceso") or "").upper() == cod or t.get("id") == codigo_acceso:
                return RegistroTriajeDTO.model_validate(t)
        return None

    async def obtener_cola_guardia(
        self,
        solo_disponibles: bool = False,
        especialidad: Optional[str] = None
    ) -> List[RegistroTriajeDTO]:
        res = []
        for t in self._almacen.values():
            if solo_disponibles and t.get("medico_asignado_id"):
                continue
            if especialidad and (t.get("especialidad_solicitada") or "").lower() != especialidad.lower():
                continue
            res.append(RegistroTriajeDTO.model_validate(t))
        return res

    async def actualizar_resultado_ia(
        self,
        triaje_id: str,
        resultado_ia: Dict[str, Any],
        prioridad_final: str,
        override_aplicado: bool = False,
        motivo_override: Optional[str] = None
    ) -> bool:
        if triaje_id in self._almacen:
            self._almacen[triaje_id]["resultados_ia"] = resultado_ia
            self._almacen[triaje_id]["prioridad_final"] = prioridad_final
            self._almacen[triaje_id]["estado"] = "LISTO"
            return True
        return False

    async def asignar_medico(self, triaje_id: str, medico_id: str) -> RegistroTriajeDTO:
        if triaje_id not in self._almacen:
            raise ValueError("Triaje no encontrado")
        self._almacen[triaje_id]["medico_asignado_id"] = medico_id
        self._almacen[triaje_id]["estado"] = "EN_CONSULTA"
        return RegistroTriajeDTO.model_validate(self._almacen[triaje_id])

    async def liberar_paciente(self, triaje_id: str, medico_id: str) -> RegistroTriajeDTO:
        if triaje_id not in self._almacen:
            raise ValueError("Triaje no encontrado")
        self._almacen[triaje_id]["medico_asignado_id"] = None
        self._almacen[triaje_id]["estado"] = "LISTO"
        return RegistroTriajeDTO.model_validate(self._almacen[triaje_id])

    async def cerrar_revision_medica(
        self,
        triaje_id: str,
        medico_id: str,
        notas_medico: str,
        prioridad_ajustada: Optional[str] = None
    ) -> RegistroTriajeDTO:
        if triaje_id not in self._almacen:
            raise ValueError("Triaje no encontrado")
        self._almacen[triaje_id]["estado"] = "REVISADO"
        self._almacen[triaje_id]["notas_medico"] = notas_medico
        if prioridad_ajustada:
            self._almacen[triaje_id]["prioridad_final"] = prioridad_ajustada
        return RegistroTriajeDTO.model_validate(self._almacen[triaje_id])


class RepositorioPacientesEnMemoria(IRepositorioPacientes):
    """Fake en memoria para pruebas de la capa de pacientes."""

    def __init__(self):
        self._almacen: Dict[str, Dict[str, Any]] = {}

    async def crear_o_actualizar_paciente(self, datos_paciente: Dict[str, Any]) -> PacienteDTO:
        paciente_id = datos_paciente.get("id") or str(uuid.uuid4())
        obj = {**datos_paciente, "id": paciente_id}
        self._almacen[paciente_id] = obj
        if obj.get("ci_hash"):
            self._almacen[obj["ci_hash"]] = obj
        return PacienteDTO.model_validate(obj)

    async def obtener_por_id(self, paciente_id: str) -> Optional[PacienteDTO]:
        if paciente_id in self._almacen:
            return PacienteDTO.model_validate(self._almacen[paciente_id])
        return None

    async def obtener_por_ci_hash(self, ci_hash: str) -> Optional[PacienteDTO]:
        if ci_hash in self._almacen:
            return PacienteDTO.model_validate(self._almacen[ci_hash])
        return None

    async def obtener_historial_clinico(self, paciente_id: str) -> Dict[str, Any]:
        paciente = await self.obtener_por_id(paciente_id)
        return {
            "paciente_id": paciente_id,
            "paciente": paciente.model_dump() if paciente else None,
            "ci_descifrado": "8492019",
            "total_atenciones": 1,
            "consultas": [{"id": "tr-mock-1", "estado": "REVISADO"}]
        }


class RepositorioMedicosEnMemoria(IRepositorioMedicos):
    """Fake en memoria para pruebas de la capa de médicos."""

    def __init__(self):
        self._almacen: Dict[str, Dict[str, Any]] = {}

    async def listar_medicos(
        self,
        rol: Optional[str] = None,
        esta_activo: Optional[bool] = None,
        busqueda: Optional[str] = None
    ) -> List[PerfilMedicoDTO]:
        res = []
        for m in self._almacen.values():
            if rol and m.get("rol") != rol.upper():
                continue
            if esta_activo is not None and m.get("esta_activo") != esta_activo:
                continue
            if busqueda and busqueda.lower() not in (m.get("nombre_completo") or "").lower():
                continue
            res.append(PerfilMedicoDTO.model_validate(m))
        return res

    async def obtener_por_id(self, medico_id: str) -> Optional[PerfilMedicoDTO]:
        if medico_id in self._almacen:
            return PerfilMedicoDTO.model_validate(self._almacen[medico_id])
        return None

    async def crear_medico(self, datos_medico: Dict[str, Any]) -> PerfilMedicoDTO:
        medico_id = datos_medico.get("id") or str(uuid.uuid4())
        obj = {**datos_medico, "id": medico_id}
        self._almacen[medico_id] = obj
        return PerfilMedicoDTO.model_validate(obj)

    async def actualizar_medico(self, medico_id: str, datos_actualizacion: Dict[str, Any]) -> PerfilMedicoDTO:
        if medico_id in self._almacen:
            self._almacen[medico_id].update(datos_actualizacion)
            return PerfilMedicoDTO.model_validate(self._almacen[medico_id])
        obj = {**datos_actualizacion, "id": medico_id}
        self._almacen[medico_id] = obj
        return PerfilMedicoDTO.model_validate(obj)

    async def obtener_medicos_activos_por_especialidad(self) -> Dict[str, List[Dict[str, Any]]]:
        agrupado = {}
        for m in self._almacen.values():
            if m.get("esta_activo", True):
                esp = m.get("especialidad", "Medicina General")
                agrupado.setdefault(esp, []).append(m)
        return agrupado


class RepositorioAuditoriaEnMemoria(IRepositorioAuditoria):
    """Fake en memoria para pruebas de la capa de auditoría."""

    def __init__(self):
        self._almacen: List[Dict[str, Any]] = []

    async def registrar_evento(
        self,
        usuario_id: str,
        accion: str,
        recurso_id: Optional[str] = None,
        direccion_ip: str = "127.0.0.1"
    ) -> EventoAuditoriaDTO:
        evento = {
            "id": str(uuid.uuid4()),
            "usuario_id": usuario_id,
            "accion": accion,
            "recurso_id": recurso_id,
            "direccion_ip": direccion_ip,
            "fecha_hora": datetime.now(timezone.utc).isoformat()
        }
        self._almacen.append(evento)
        return EventoAuditoriaDTO.model_validate(evento)

    async def listar_eventos(
        self,
        limite: int = 50,
        accion: Optional[str] = None
    ) -> List[EventoAuditoriaDTO]:
        res = list(reversed(self._almacen))
        if accion:
            res = [e for e in res if e.get("accion") == accion]
        return [EventoAuditoriaDTO.model_validate(e) for e in res[:limite]]
