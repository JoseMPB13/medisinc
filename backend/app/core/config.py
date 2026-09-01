"""
Módulo de Configuración Central de MediSinc-IA Backend (Alias y Re-exportación).
Asegura compatibilidad total con módulos que importan desde app.core.config.
"""

from app.core.configuracion import Configuracion, configuracion, settings, Settings

__all__ = ["Configuracion", "configuracion", "settings", "Settings"]
