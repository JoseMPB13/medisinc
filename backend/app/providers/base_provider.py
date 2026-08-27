"""
Puente de retrocompatibilidad hacia app.proveedores.proveedor_base.
"""

from app.proveedores.proveedor_base import (
    ProveedorIABase,
    BaseAIProvider,
    MAPEADOR_DIALECTAL_BOLIVIA
)

__all__ = [
    "ProveedorIABase",
    "BaseAIProvider",
    "MAPEADOR_DIALECTAL_BOLIVIA"
]
