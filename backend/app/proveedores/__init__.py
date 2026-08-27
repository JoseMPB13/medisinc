"""
Capa de Proveedores de Inteligencia Artificial Agnóstica para MediSinc-IA en Español.
"""

from app.proveedores.proveedor_base import ProveedorIABase, BaseAIProvider
from app.proveedores.proveedor_gemini import ProveedorGemini, GeminiProvider
from app.proveedores.proveedor_groq import ProveedorGroq, GroqProvider
from app.proveedores.proveedor_openai import ProveedorOpenAI, OpenAIProvider
from app.proveedores.fabrica_ia import obtener_proveedor_ia, get_ai_provider

__all__ = [
    "ProveedorIABase",
    "BaseAIProvider",
    "ProveedorGemini",
    "GeminiProvider",
    "ProveedorGroq",
    "GroqProvider",
    "ProveedorOpenAI",
    "OpenAIProvider",
    "obtener_proveedor_ia",
    "get_ai_provider"
]
