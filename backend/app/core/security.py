"""
Módulo de Seguridad y Criptografía de MediSinc-IA.
Proporciona funciones para cifrado AES-256 (Fernet), hashing HMAC-SHA256 con Pepper
y generación de códigos únicos de acceso.
"""

import base64
import hashlib
import hmac
import random
import string
from cryptography.fernet import Fernet
from app.core.config import settings


def _get_fernet_key() -> bytes:
    """
    Deriva una clave válida Fernet de 32 bytes codificada en URL-safe base64
    a partir de AES_SECRET_KEY.
    """
    key_bytes = settings.AES_SECRET_KEY.encode('utf-8')
    # Genera hash SHA-256 estable para garantizar exactamente 32 bytes
    hashed_key = hashlib.sha256(key_bytes).digest()
    return base64.urlsafe_b64encode(hashed_key)


def encrypt_ci(ci_text: str) -> str:
    """
    Cifra el Carnet de Identidad (CI) del paciente utilizando AES-256 (Fernet).

    Entrada: ci_text (str) - Texto plano del CI.
    Salida: str - Token cifrado codificado en base64 string.
    """
    if not ci_text:
        return ""
    fernet = Fernet(_get_fernet_key())
    encrypted_bytes = fernet.encrypt(ci_text.encode('utf-8'))
    return encrypted_bytes.decode('utf-8')


def decrypt_ci(ci_encrypted: str) -> str:
    """
    Descifra el Carnet de Identidad (CI) cifrado.

    Entrada: ci_encrypted (str) - Token cifrado.
    Salida: str - Texto plano original del CI.
    """
    if not ci_encrypted:
        return ""
    fernet = Fernet(_get_fernet_key())
    decrypted_bytes = fernet.decrypt(ci_encrypted.encode('utf-8'))
    return decrypted_bytes.decode('utf-8')


def hash_ci(ci_text: str) -> str:
    """
    Calcula un hash unidireccional seguro HMAC-SHA256 del CI concatenado con HMAC_PEPPER_KEY.
    Permite realizar búsquedas exactas en base de datos sin exponer el CI en texto plano.

    Entrada: ci_text (str) - Carnet de identidad en texto plano.
    Salida: str - Hash hexdigest HMAC-SHA256.
    """
    if not ci_text:
        return ""
    pepper_bytes = settings.HMAC_PEPPER_KEY.encode('utf-8')
    # Normalizar eliminando espacios e hipercaracteres
    normalized_ci = ci_text.strip().replace(" ", "").upper()
    ci_bytes = normalized_ci.encode('utf-8')
    return hmac.new(pepper_bytes, ci_bytes, hashlib.sha256).hexdigest()


def generate_access_code() -> str:
    """
    Genera un código único alfanumérico legible de acceso para el paciente (ej. MS-8X92K).

    Salida: str - Código con prefijo 'MS-' seguido de 5 caracteres alfanuméricos en mayúscula.
    """
    # Caracteres legibles evitando confusiones (sin O, 0, I, 1)
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    suffix = "".join(random.choices(alphabet, k=5))
    return f"MS-{suffix}"
