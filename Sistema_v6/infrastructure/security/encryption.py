"""Utilidades para encriptación de credenciales.

Este módulo proporciona funciones para encriptar y desencriptar credenciales del PJN
usando Fernet (symmetric encryption).
"""

from __future__ import annotations

from cryptography.fernet import Fernet

from infrastructure.config import get_settings

settings = get_settings()

# Obtener o generar la clave Fernet
if settings.encryption.fernet_key:
    _fernet_key = settings.encryption.fernet_key.encode()
else:
    # Generar una nueva clave si no existe
    # NOTA: Esta clave debe guardarse en producción (variable de entorno)
    _fernet_key = Fernet.generate_key()
    print(f"WARNING: Fernet key generada automáticamente: {_fernet_key.decode()}")
    print("Guarde esta clave en la variable de entorno ENCRYPTION_FERNET_KEY")

cipher_suite = Fernet(_fernet_key)


def encrypt_credentials(text: str) -> str:
    """Encripta un texto usando Fernet.

    Args:
        text: Texto a encriptar (credencial del PJN)

    Returns:
        Texto encriptado (base64)

    Example:
        >>> encrypted = encrypt_credentials("mi_password")
        >>> print(encrypted)
        gAAAAABk...
    """
    if not text:
        return ""
    return cipher_suite.encrypt(text.encode()).decode()


def decrypt_credentials(encrypted_text: str) -> str:
    """Desencripta un texto usando Fernet.

    Args:
        encrypted_text: Texto encriptado (base64)

    Returns:
        Texto desencriptado

    Example:
        >>> encrypted = encrypt_credentials("mi_password")
        >>> decrypted = decrypt_credentials(encrypted)
        >>> print(decrypted)
        mi_password
    """
    if not encrypted_text:
        return ""
    return cipher_suite.decrypt(encrypted_text.encode()).decode()


def generate_fernet_key() -> str:
    """Genera una nueva clave Fernet.

    Returns:
        Clave Fernet en formato base64 string

    Example:
        >>> key = generate_fernet_key()
        >>> print(key)
        abcdef123456...
    """
    return Fernet.generate_key().decode()
