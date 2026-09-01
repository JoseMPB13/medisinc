"""
Módulo de Repositorios Especializados de MediSinc-IA.
Implementa el Patrón Repository e Inyección de Dependencias.
"""

from app.repositorios.base import (
    IRepositorioTriaje,
    IRepositorioPacientes,
    IRepositorioMedicos,
    IRepositorioAuditoria
)
from app.repositorios.repositorio_triaje import RepositorioTriajeSupabase
from app.repositorios.repositorio_pacientes import RepositorioPacientesSupabase
from app.repositorios.repositorio_medicos import RepositorioMedicosSupabase
from app.repositorios.repositorio_auditoria import RepositorioAuditoriaSupabase
from app.repositorios.dependencias import (
    obtener_repositorio_triaje,
    obtener_repositorio_pacientes,
    obtener_repositorio_medicos,
    obtener_repositorio_auditoria
)

__all__ = [
    "IRepositorioTriaje",
    "IRepositorioPacientes",
    "IRepositorioMedicos",
    "IRepositorioAuditoria",
    "RepositorioTriajeSupabase",
    "RepositorioPacientesSupabase",
    "RepositorioMedicosSupabase",
    "RepositorioAuditoriaSupabase",
    "obtener_repositorio_triaje",
    "obtener_repositorio_pacientes",
    "obtener_repositorio_medicos",
    "obtener_repositorio_auditoria"
]
