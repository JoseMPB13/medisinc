"""
Puente de retrocompatibilidad hacia app.proveedores.fabrica_ia.
"""

from app.proveedores.fabrica_ia import (
    obtener_proveedor_ia,
    get_ai_provider
)

__all__ = [
    "obtener_proveedor_ia",
    "get_ai_provider"
]
