"""
Pruebas Automatizadas de Seguridad y Hardening - Fase 2:
1. Validación estricta de secretos criptográficos según el entorno (Development vs Production).
2. Rate Limiter en memoria acotado con política de evicción LRU y mitigación de DoS / OOM.
"""

import pytest
import time
import asyncio
from app.core.configuracion import Configuracion
from app.core.limite_peticiones import RateLimiterMemoria


# =============================================================================
# 1. PRUEBAS DE VALIDACIÓN DE SECRETOS CRIPTOGRÁFICOS
# =============================================================================

def test_configuracion_permite_claves_prueba_en_development():
    """Valida que en entorno de desarrollo se permitan los valores base predeterminados."""
    config = Configuracion(
        ENVIRONMENT="development",
        AES_SECRET_KEY="medisinc_secret_aes_key_32_bytes_len!",
        HMAC_PEPPER_KEY="medisinc_hmac_pepper_secret_key",
        JWT_SECRET_KEY="medisinc_secret_jwt_key_32_bytes_len!"
    )
    assert config.ENVIRONMENT == "development"
    assert len(config.AES_SECRET_KEY) >= 32


def test_configuracion_permite_claves_prueba_en_test():
    """Valida que en entorno de pruebas ('test') no se bloquee la inicialización."""
    config = Configuracion(
        ENVIRONMENT="test",
        AES_SECRET_KEY="test_key_aes_very_simple_1234567890",
        HMAC_PEPPER_KEY="test_pepper_12345678901234567890",
        JWT_SECRET_KEY="test_jwt_secret_key_1234567890123456"
    )
    assert config.ENVIRONMENT == "test"


def test_configuracion_produccion_bloquea_claves_con_patrones_inseguros():
    """Valida que en producción se rechacen claves con palabras clave o fallbacks prohibidos."""
    # Caso 1: Clave con subcadena "PepperBolivia"
    with pytest.raises(ValueError, match="CRÍTICO \\[Seguridad\\]"):
        Configuracion(
            ENVIRONMENT="production",
            AES_SECRET_KEY="AES_SECURE_RANDOM_KEY_2026_VERY_LONG_STRING_PRODUCTION!",
            HMAC_PEPPER_KEY="PepperBolivia2026SecureHash_Which_Is_Known_Publicly!",
            JWT_SECRET_KEY="JWT_SECURE_RANDOM_KEY_2026_VERY_LONG_STRING_PRODUCTION!"
        )

    # Caso 2: Clave con subcadena "medisinc_secret"
    with pytest.raises(ValueError, match="CRÍTICO \\[Seguridad\\]"):
        Configuracion(
            ENVIRONMENT="production",
            AES_SECRET_KEY="medisinc_secret_aes_key_32_bytes_len!",
            HMAC_PEPPER_KEY="HMAC_PEPPER_KEY_SUPER_RANDOM_SECURE_TOKEN_2026_A!",
            JWT_SECRET_KEY="JWT_SECURE_RANDOM_KEY_2026_VERY_LONG_STRING_PRODUCTION!"
        )


def test_configuracion_produccion_bloquea_claves_cortas_menores_a_32_caracteres():
    """Valida que en producción se rechacen claves menores a 32 caracteres (256 bits)."""
    with pytest.raises(ValueError, match="longitud de 12 caracteres"):
        Configuracion(
            ENVIRONMENT="production",
            AES_SECRET_KEY="clave_corta!",
            HMAC_PEPPER_KEY="HMAC_PEPPER_KEY_SUPER_RANDOM_SECURE_TOKEN_2026_A!",
            JWT_SECRET_KEY="JWT_SECURE_RANDOM_KEY_2026_VERY_LONG_STRING_PRODUCTION!"
        )


def test_configuracion_produccion_acepta_claves_robustas_generadas():
    """Valida que en producción se acepten claves de alta entropía y longitud adecuada."""
    config_prod = Configuracion(
        ENVIRONMENT="production",
        AES_SECRET_KEY="k8N$9zP2q!L5mR7vX3wY0aB4cE6gH1jK3mN5pQ7rT9vX1z",
        HMAC_PEPPER_KEY="f3A#9pL1w$8xZ4mQ7vR0eT2yU5bN8cM1jK4gH6sD9vX2zB",
        JWT_SECRET_KEY="t7X@2mN5q$8wZ1vR4eT9yU3bN6cM0jK5gH8sD2vX7zB9pL"
    )
    assert config_prod.ENVIRONMENT == "production"
    assert len(config_prod.AES_SECRET_KEY) >= 32


# =============================================================================
# 2. PRUEBAS PARA RATE LIMITER EN MEMORIA CON EVICCIÓN LRU
# =============================================================================

@pytest.mark.asyncio
async def test_rate_limiter_permite_hasta_el_umbral_y_bloquea_excesos():
    """Valida que el limitador admita N peticiones y bloquee a partir de N+1."""
    limiter = RateLimiterMemoria(capacidad_maxima=100, ventana_segundos=60, limite_maximo=3)
    ip_prueba = "192.168.1.50"

    # Peticiones 1, 2 y 3 deben ser admitidas
    assert await limiter.registrar_y_validar(ip_prueba) is True
    assert await limiter.registrar_y_validar(ip_prueba) is True
    assert await limiter.registrar_y_validar(ip_prueba) is True

    # Petición 4 debe ser bloqueada
    assert await limiter.registrar_y_validar(ip_prueba) is False


@pytest.mark.asyncio
async def test_rate_limiter_eviccion_lru_al_superar_capacidad():
    """
    Valida que al superar la capacidad máxima (ej. 3 IPs),
    se expulse la IP menos recientemente usada (LRU) manteniendo el tamaño acotado.
    """
    limiter = RateLimiterMemoria(capacidad_maxima=3, ventana_segundos=60, limite_maximo=5)

    # 1. Registrar 3 IPs
    await limiter.registrar_y_validar("10.0.0.1")
    await limiter.registrar_y_validar("10.0.0.2")
    await limiter.registrar_y_validar("10.0.0.3")
    assert limiter.total_ips_registradas == 3

    # 2. Usar nuevamente la IP 10.0.0.1 para que la más antigua sea 10.0.0.2
    await limiter.registrar_y_validar("10.0.0.1")

    # 3. Registrar una 4ta IP ("10.0.0.4")
    # Debe expulsar "10.0.0.2" porque "10.0.0.1" fue refrescada y "10.0.0.3" es más reciente que "10.0.0.2"
    await limiter.registrar_y_validar("10.0.0.4")

    # La capacidad máxima se mantiene estrictamente en 3
    assert limiter.total_ips_registradas == 3
    assert "10.0.0.2" not in limiter._almacen
    assert "10.0.0.1" in limiter._almacen
    assert "10.0.0.3" in limiter._almacen
    assert "10.0.0.4" in limiter._almacen


@pytest.mark.asyncio
async def test_rate_limiter_restablece_acceso_tras_expirar_ventana():
    """Valida que una vez expirada la ventana de tiempo, el usuario recupere el acceso."""
    # Ventana ultra-corta de 0.2 segundos para prueba rápida
    limiter = RateLimiterMemoria(capacidad_maxima=50, ventana_segundos=0.2, limite_maximo=1)
    ip_prueba = "172.16.0.99"

    assert await limiter.registrar_y_validar(ip_prueba) is True
    # Inmediatamente después debe estar bloqueado
    assert await limiter.registrar_y_validar(ip_prueba) is False

    # Esperar que expire la ventana
    await asyncio.sleep(0.25)

    # El acceso debe restablecerse
    assert await limiter.registrar_y_validar(ip_prueba) is True
