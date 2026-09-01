"""
Módulo de Configuración Central de MediSinc-IA Backend en Español.
Carga y valida las variables de entorno utilizando Pydantic Settings
con validación estricta de seguridad en entornos productivos.
"""

from pathlib import Path
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator

# Ruta absoluta hacia la raíz del proyecto para asegurar la lectura del archivo .env
DIRECTORIO_BASE = Path(__file__).resolve().parent.parent.parent
ARCHIVO_ENV_RAIZ = DIRECTORIO_BASE / ".env"

# Patrones o palabras clave inseguras no permitidas en producción
PATRONES_INSEGUROS_PRODUCCION = [
    "PepperBolivia",
    "medisinc_secret",
    "medisinc_ia_secret",
    "SecretJWT",
    "123456",
    "placeholder",
    "secret_key",
    "changeme",
    "default_key"
]


class Configuracion(BaseSettings):
    """
    Configuración global del sistema con validación criptográfica estricta.
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

    @model_validator(mode="after")
    def validar_secretos_en_produccion(self):
        """
        Valida rigurosamente que las claves criptográficas no usen valores por defecto
        ni tengan longitudes insuficientes cuando se ejecuta en entorno de producción.
        """
        entorno = (self.ENVIRONMENT or self.ENTORNO or "development").lower()
        if entorno in ["production", "produccion", "prod"]:
            secretos = {
                "AES_SECRET_KEY": self.AES_SECRET_KEY,
                "HMAC_PEPPER_KEY": self.HMAC_PEPPER_KEY,
                "JWT_SECRET_KEY": self.JWT_SECRET_KEY,
            }

            for nombre_clave, valor_clave in secretos.items():
                if not valor_clave:
                    raise ValueError(
                        f"CRÍTICO [Seguridad]: La variable de entorno '{nombre_clave}' es obligatoria en producción."
                    )

                # Validación de longitud mínima de seguridad (mínimo 32 caracteres / 256 bits)
                if len(valor_clave) < 32:
                    raise ValueError(
                        f"CRÍTICO [Seguridad]: La clave '{nombre_clave}' tiene una longitud de {len(valor_clave)} caracteres. "
                        f"Se requiere un mínimo de 32 caracteres (256 bits) en producción."
                    )

                # Validación de patrones o frases de fallback prohibidas
                for patron in PATRONES_INSEGUROS_PRODUCCION:
                    if patron.lower() in valor_clave.lower():
                        raise ValueError(
                            f"CRÍTICO [Seguridad]: La clave '{nombre_clave}' contiene el patrón inseguro '{patron}'. "
                            f"Debe configurar una clave criptográfica real generada de forma aleatoria en el archivo .env."
                        )

        return self


# Instancia global de configuración
configuracion = Configuracion()
settings = configuracion
Settings = Configuracion
