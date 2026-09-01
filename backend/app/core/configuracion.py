"""
Módulo de Configuración Central de MediSinc-IA Backend en Español.
Carga y valida las variables de entorno utilizando Pydantic Settings
buscando en la raíz del proyecto y directorio actual.
"""

from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict

# Ruta absoluta hacia la raíz del proyecto para asegurar la lectura del archivo .env
DIRECTORIO_BASE = Path(__file__).resolve().parent.parent.parent
ARCHIVO_ENV_RAIZ = DIRECTORIO_BASE / ".env"


class Configuracion(BaseSettings):
    """
    Configuración global del sistema. Lee desde variables de entorno o archivo .env en la raíz.
    """
    # Configuración de la aplicación
    PROJECT_NAME: str = "MediSinc-IA"
    NOMBRE_PROYECTO: str = "MediSinc-IA"
    VERSION: str = "2.0.0"
    ENVIRONMENT: str = "development"
    ENTORNO: str = "development"
    PORT: int = 8000
    PUERTO: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    PREFIJO_API_V1: str = "/api/v1"

    # Supabase (Base de datos PostgreSQL y Auth)
    SUPABASE_URL: str = "https://placeholder.supabase.co"
    SUPABASE_SERVICE_ROLE_KEY: str = "placeholder_key"

    # Cifrado y Hash de Datos Sensibles (CI)
    AES_SECRET_KEY: str = "medisinc_secret_aes_key_32_bytes_len!"
    HMAC_PEPPER_KEY: str = "medisinc_hmac_pepper_secret_key"
    JWT_SECRET_KEY: str = "medisinc_secret_jwt_key_32_bytes_len!"


    # Proveedor de Inteligencia Artificial (gemini, groq, openai)
    AI_PROVIDER: str = "gemini"
    GEMINI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Upstash Redis & QStash (Procesamiento Asíncrono / Rate Limiting)
    UPSTASH_REDIS_REST_URL: Optional[str] = None
    UPSTASH_REDIS_REST_TOKEN: Optional[str] = None

    # Control de Límite de Peticiones (Rate Limiting)
    RATE_LIMIT_REQUESTS: int = 5
    RATE_LIMIT_MINUTES: int = 5

    # Configuración CORS
    CORS_ORIGINS: List[str] = ["*"]

    # Carga de archivo .env en la raíz del proyecto o directorio actual
    model_config = SettingsConfigDict(
        env_file=(str(ARCHIVO_ENV_RAIZ), "../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


# Instancia global de configuración
configuracion = Configuracion()
settings = configuracion
Settings = Configuracion
