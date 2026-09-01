"""
Interfaces y Contratos Abstractos para la Capa de Repositorios (Patrón Repository).
Define operaciones asíncronas para Triaje, Pacientes, Médicos y Auditoría.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.esquemas.dominio import (
    RegistroTriajeDTO,
    PacienteDTO,
    PerfilMedicoDTO,
    EventoAuditoriaDTO,
    ResultadoIADTO
)


class IRepositorioTriaje(ABC):
    """Contrato para la persistencia y gestión de episodios de triaje."""

    @abstractmethod
    async def guardar_triaje(self, datos_triaje: Dict[str, Any]) -> RegistroTriajeDTO:
        pass

    @abstractmethod
    async def obtener_por_id(self, triaje_id: str) -> Optional[RegistroTriajeDTO]:
        pass

    @abstractmethod
    async def obtener_por_codigo(self, codigo_acceso: str) -> Optional[RegistroTriajeDTO]:
        pass

    @abstractmethod
    async def obtener_cola_guardia(
        self,
        solo_disponibles: bool = False,
        especialidad: Optional[str] = None
    ) -> List[RegistroTriajeDTO]:
        pass

    @abstractmethod
    async def actualizar_resultado_ia(
        self,
        triaje_id: str,
        resultado_ia: Dict[str, Any],
        prioridad_final: str,
        override_aplicado: bool = False,
        motivo_override: Optional[str] = None
    ) -> bool:
        pass

    @abstractmethod
    async def asignar_medico(self, triaje_id: str, medico_id: str) -> RegistroTriajeDTO:
        pass

    @abstractmethod
    async def liberar_paciente(self, triaje_id: str, medico_id: str) -> RegistroTriajeDTO:
        pass

    @abstractmethod
    async def cerrar_revision_medica(
        self,
        triaje_id: str,
        medico_id: str,
        notas_medico: str,
        prioridad_ajustada: Optional[str] = None
    ) -> RegistroTriajeDTO:
        pass


class IRepositorioPacientes(ABC):
    """Contrato para la gestión de pacientes y su historial clínico (3NF)."""

    @abstractmethod
    async def crear_o_actualizar_paciente(self, datos_paciente: Dict[str, Any]) -> PacienteDTO:
        pass

    @abstractmethod
    async def obtener_por_id(self, paciente_id: str) -> Optional[PacienteDTO]:
        pass

    @abstractmethod
    async def obtener_por_ci_hash(self, ci_hash: str) -> Optional[PacienteDTO]:
        pass

    @abstractmethod
    async def obtener_historial_clinico(self, paciente_id: str) -> Dict[str, Any]:
        pass


class IRepositorioMedicos(ABC):
    """Contrato para la gestión de personal médico y turnos de guardia."""

    @abstractmethod
    async def listar_medicos(
        self,
        rol: Optional[str] = None,
        esta_activo: Optional[bool] = None,
        busqueda: Optional[str] = None
    ) -> List[PerfilMedicoDTO]:
        pass

    @abstractmethod
    async def obtener_por_id(self, medico_id: str) -> Optional[PerfilMedicoDTO]:
        pass

    @abstractmethod
    async def crear_medico(self, datos_medico: Dict[str, Any]) -> PerfilMedicoDTO:
        pass

    @abstractmethod
    async def actualizar_medico(self, medico_id: str, datos_actualizacion: Dict[str, Any]) -> PerfilMedicoDTO:
        pass

    @abstractmethod
    async def obtener_medicos_activos_por_especialidad(self) -> Dict[str, List[Dict[str, Any]]]:
        pass


class IRepositorioAuditoria(ABC):
    """Contrato para la bitácora inalterable de auditoría."""

    @abstractmethod
    async def registrar_evento(
        self,
        usuario_id: str,
        accion: str,
        recurso_id: Optional[str] = None,
        direccion_ip: str = "127.0.0.1"
    ) -> EventoAuditoriaDTO:
        pass

    @abstractmethod
    async def listar_eventos(
        self,
        limite: int = 50,
        accion: Optional[str] = None
    ) -> List[EventoAuditoriaDTO]:
        pass
