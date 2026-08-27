"""
Módulo puente de retrocompatibilidad hacia servicio_supabase.py.
"""

from app.servicios.servicio_supabase import (
    ServicioSupabase,
    servicio_supabase,
    supabase_service,
    _IN_MEMORY_TRIAGE_DB,
    _IN_MEMORY_AI_DB,
    _IN_MEMORY_PROFILES_DB,
    _IN_MEMORY_AUDIT_LOG_DB,
    _BD_LOCAL_TRIAJES,
    _BD_LOCAL_RESULTADOS_IA,
    _BD_LOCAL_PERFILES,
    _BD_LOCAL_AUDITORIA
)

SupabaseService = ServicioSupabase

__all__ = [
    "ServicioSupabase",
    "SupabaseService",
    "servicio_supabase",
    "supabase_service",
    "_IN_MEMORY_TRIAGE_DB",
    "_IN_MEMORY_AI_DB",
    "_IN_MEMORY_PROFILES_DB",
    "_IN_MEMORY_AUDIT_LOG_DB",
    "_BD_LOCAL_TRIAJES",
    "_BD_LOCAL_RESULTADOS_IA",
    "_BD_LOCAL_PERFILES",
    "_BD_LOCAL_AUDITORIA"
]
