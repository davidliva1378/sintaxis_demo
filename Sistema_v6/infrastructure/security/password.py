"""Utilidades para manejo de contraseñas.

Este módulo proporciona funciones para hashear y verificar contraseñas usando bcrypt.
"""

from __future__ import annotations

import bcrypt

# Configurar el contexto de password hashing con bcrypt
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash.

    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash de la contraseña (bcrypt)

    Returns:
        True si la contraseña es correcta, False en caso contrario
    """
    try:
        # bcrypt requiere bytes
        if isinstance(plain_password, str):
            plain_password_bytes = plain_password.encode('utf-8')
        else:
            plain_password_bytes = plain_password

        if isinstance(hashed_password, str):
            hashed_password_bytes = hashed_password.encode('utf-8')
        else:
            hashed_password_bytes = hashed_password

        return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Hashea una contraseña usando bcrypt.

    Args:
        password: Contraseña en texto plano

    Returns:
        Hash de la contraseña (bcrypt)
    """
    if isinstance(password, str):
        password_bytes = password.encode('utf-8')
    else:
        password_bytes = password

    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')
