"""
Módulo de Configuración Central de MediSinc-IA Backend.
Carga y valida las variables de entorno utilizando Pydantic Settings.
"""

from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuración global del sistema. Lee desde variables de entorno o archivo .env.
    """
    # Configuración del servidor
    PORT: int = 8000
    ENVIRONMENT: str = "development"

    # Supabase (Base de datos PostgreSQL y Auth)
    SUPABASE_URL: str = "https://placeholder.supabase.co"
    SUPABASE_SERVICE_ROLE_KEY: str = "placeholder_key"

    # Cifrado y Hash de Datos Sensibles (CI)
    AES_SECRET_KEY: str = "medisinc_secret_aes_key_32_bytes_len!"
    HMAC_PEPPER_KEY: str = "medisinc_hmac_pepper_secret_key"

    # Proveedor de Inteligencia Artificial (gemini, groq, openai)
    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Upstash Redis & QStash (Procesamiento Asíncrono / Rate Limiting)
    UPSTASH_REDIS_REST_URL: Optional[str] = None
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = None

    # Carga de archivo .env opcional si existe en la raíz o directorio actual
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instancia global de configuración para uso en toda la aplicación
settings = Settings()
