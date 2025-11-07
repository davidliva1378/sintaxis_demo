"""Utilidades para manejo de contraseñas.

Este módulo proporciona funciones para hashear y verificar contraseñas usando bcrypt.
"""

from __future__ import annotations

from passlib.context import CryptContext

# Configurar el contexto de password hashing con bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica una contraseña contra su hash.

    Args:
        plain_password: Contraseña en texto plano
        hashed_password: Hash de la contraseña (bcrypt)

    Returns:
        True si la contraseña es correcta, False en caso contrario

    Example:
        >>> hashed = get_password_hash("mi_password")
        >>> verify_password("mi_password", hashed)
        True
        >>> verify_password("password_incorrecta", hashed)
        False
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hashea una contraseña usando bcrypt.

    Args:
        password: Contraseña en texto plano

    Returns:
        Hash de la contraseña (bcrypt)

    Example:
        >>> hashed = get_password_hash("mi_password")
        >>> print(hashed)
        $2b$12$...
    """
    return pwd_context.hash(password)
