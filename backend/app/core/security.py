"""
Módulo de enlace de compatibilidad hacia seguridad.py.
Permite mantener operativas las importaciones legadas mientras se completa la migración.
"""

from app.core.seguridad import (
    cifrar_ci,
    descifrar_ci,
    hashear_ci,
    generar_codigo_acceso,
    obtener_perfil_usuario_actual,
    obtener_medico_actual,
    obtener_admin_actual,
    encrypt_ci,
    decrypt_ci,
    hash_ci,
    generate_access_code,
    get_current_user_profile,
    get_current_doctor,
    get_current_admin
)

__all__ = [
    "cifrar_ci",
    "descifrar_ci",
    "hashear_ci",
    "generar_codigo_acceso",
    "obtener_perfil_usuario_actual",
    "obtener_medico_actual",
    "obtener_admin_actual",
    "encrypt_ci",
    "decrypt_ci",
    "hash_ci",
    "generate_access_code",
    "get_current_user_profile",
    "get_current_doctor",
    "get_current_admin"
]
