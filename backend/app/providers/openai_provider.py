"""
Puente de retrocompatibilidad hacia app.proveedores.proveedor_openai.
"""

from app.proveedores.proveedor_openai import (
    ProveedorOpenAI,
    OpenAIProvider
)

__all__ = [
    "ProveedorOpenAI",
    "OpenAIProvider"
]
