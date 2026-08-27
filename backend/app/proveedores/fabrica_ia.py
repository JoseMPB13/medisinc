"""
Fábrica de Proveedores de Inteligencia Artificial (Pattern Factory).
Instancia dinámicamente el adaptador de IA configurado en la variable de entorno AI_PROVIDER.
Permite alternar transparentemente entre Gemini, Groq y OpenAI sin modificar la lógica de negocio.
"""

import logging
from app.core.config import settings
from app.proveedores.proveedor_base import ProveedorIABase
from app.proveedores.proveedor_gemini import ProveedorGemini
from app.proveedores.proveedor_groq import ProveedorGroq
from app.proveedores.proveedor_openai import ProveedorOpenAI

logger = logging.getLogger(__name__)


def obtener_proveedor_ia() -> ProveedorIABase:
    """
    Retorna la instancia del proveedor de Inteligencia Artificial activo según la configuración.

    Salida:
        ProveedorIABase: Instancia concreta (ProveedorGemini, ProveedorGroq o ProveedorOpenAI).
    """
    nombre_proveedor = (settings.AI_PROVIDER or "gemini").lower().strip()

    if nombre_proveedor == "groq":
        logger.info("✓ Utilizando proveedor de IA: Groq Cloud (Llama 3)")
        return ProveedorGroq()
    elif nombre_proveedor == "openai":
        logger.info("✓ Utilizando proveedor de IA: OpenAI (GPT-4o)")
        return ProveedorOpenAI()
    else:
        logger.info("✓ Utilizando proveedor de IA: Google Gemini 1.5 Flash (Predeterminado)")
        return ProveedorGemini()


class FabricaIA:
    """Clase envolvente Fábrica para compatibilidad de invocación estática."""

    @staticmethod
    def obtener_proveedor() -> ProveedorIABase:
        return obtener_proveedor_ia()

    @staticmethod
    def get_provider() -> ProveedorIABase:
        return obtener_proveedor_ia()


# -----------------------------------------------------------------------------
# ALIASES DE COMPATIBILIDAD CON CÓDIGO EXISTENTE
# -----------------------------------------------------------------------------
get_ai_provider = obtener_proveedor_ia
AIFactory = FabricaIA
