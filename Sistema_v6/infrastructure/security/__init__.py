"""Módulo de seguridad.

Exporta las utilidades de seguridad:
- Password hashing (bcrypt)
- JWT tokens
- Encryption (Fernet)
"""

from .encryption import decrypt_credentials, encrypt_credentials, generate_fernet_key
from .jwt import create_access_token, decode_access_token
from .password import get_password_hash, verify_password

__all__ = [
    # Password
    "get_password_hash",
    "verify_password",
    # JWT
    "create_access_token",
    "decode_access_token",
    # Encryption
    "encrypt_credentials",
    "decrypt_credentials",
    "generate_fernet_key",
]
