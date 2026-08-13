"""
Fábrica de Proveedores de Inteligencia Artificial (Pattern Factory).
Instancia dinámicamente el proveedor configurado en la variable de entorno AI_PROVIDER.
"""

import logging
from app.core.config import settings
from app.providers.base_provider import BaseAIProvider
from app.providers.gemini_provider import GeminiProvider
from app.providers.groq_provider import GroqProvider
from app.providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


def get_ai_provider() -> BaseAIProvider:
    """
    Retorna la instancia del proveedor de IA configurado en el sistema.

    Salida: BaseAIProvider - Instancia adaptada (GeminiProvider, GroqProvider, o OpenAIProvider).
    """
    provider_name = (settings.AI_PROVIDER or "gemini").lower()

    if provider_name == "groq":
        logger.info("Utilizando proveedor de IA: Groq (Llama 3)")
        return GroqProvider()
    elif provider_name == "openai":
        logger.info("Utilizando proveedor de IA: OpenAI")
        return OpenAIProvider()
    else:
        logger.info("Utilizando proveedor de IA: Google Gemini 1.5 Flash (Predeterminado)")
        return GeminiProvider()
