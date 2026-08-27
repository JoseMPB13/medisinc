"""
Puente de retrocompatibilidad hacia app.proveedores.proveedor_gemini.
"""

from app.proveedores.proveedor_gemini import (
    ProveedorGemini,
    GeminiProvider
)

__all__ = [
    "ProveedorGemini",
    "GeminiProvider"
]
