"""
Contenedor de Inyección de Dependencias para Repositorios de MediSinc-IA.
Permite inyectar repositorios desacoplados en los controladores y sobreescribirlos en tests.
"""

from typing import Optional
from app.core.configuracion import configuracion
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

# Almacenes compartidos en memoria para resiliencia/fallback local
_BD_MEMORIA_TRIAJES = {}
_BD_MEMORIA_PACIENTES = {}
_BD_MEMORIA_PERFILES = {}
_BD_MEMORIA_AUDITORIA = []

# Clientes y repositorios singleton por defecto
_cliente_supabase = None

def _obtener_cliente_supabase():
    global _cliente_supabase
    if _cliente_supabase is not None:
        return _cliente_supabase

    url = configuracion.SUPABASE_URL
    key = configuracion.SUPABASE_SERVICE_ROLE_KEY

    if not url or not key or "placeholder" in url or "placeholder" in key:
        return None

    try:
        from supabase import create_client
        _cliente_supabase = create_client(url, key)
        return _cliente_supabase
    except Exception:
        return None


def obtener_repositorio_triaje() -> IRepositorioTriaje:
    """Proveedor de inyección de dependencias para el repositorio de triaje."""
    cliente = _obtener_cliente_supabase()
    return RepositorioTriajeSupabase(cliente_supabase=cliente, almacen_fallback=_BD_MEMORIA_TRIAJES)


def obtener_repositorio_pacientes() -> IRepositorioPacientes:
    """Proveedor de inyección de dependencias para el repositorio de pacientes."""
    cliente = _obtener_cliente_supabase()
    return RepositorioPacientesSupabase(cliente_supabase=cliente, almacen_fallback=_BD_MEMORIA_PACIENTES)


def obtener_repositorio_medicos() -> IRepositorioMedicos:
    """Proveedor de inyección de dependencias para el repositorio de médicos."""
    cliente = _obtener_cliente_supabase()
    return RepositorioMedicosSupabase(cliente_supabase=cliente, almacen_fallback=_BD_MEMORIA_PERFILES)


def obtener_repositorio_auditoria() -> IRepositorioAuditoria:
    """Proveedor de inyección de dependencias para el repositorio de auditoría."""
    cliente = _obtener_cliente_supabase()
    return RepositorioAuditoriaSupabase(cliente_supabase=cliente, almacen_fallback=_BD_MEMORIA_AUDITORIA)
