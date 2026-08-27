"""
Puente de retrocompatibilidad hacia app.proveedores.proveedor_groq.
"""

from app.proveedores.proveedor_groq import (
    ProveedorGroq,
    GroqProvider
)

__all__ = [
    "ProveedorGroq",
    "GroqProvider"
]
