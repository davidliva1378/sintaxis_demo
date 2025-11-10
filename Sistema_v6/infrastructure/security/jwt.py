"""Utilidades para manejo de JWT (JSON Web Tokens).

Este módulo proporciona funciones para crear y decodificar tokens JWT.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from jose import JWTError, jwt

from infrastructure.config import get_settings

settings = get_settings()


def create_access_token(data: dict[str, Any], expires_delta: timedelta | None = None) -> str:
    """Crea un token de acceso JWT.

    Args:
        data: Datos a incluir en el token (típicamente {"sub": username})
        expires_delta: Tiempo de expiración personalizado (opcional)

    Returns:
        Token JWT firmado

    Example:
        >>> token = create_access_token({"sub": "usuario1"})
        >>> print(token)
        eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt.secret_key, algorithm=settings.jwt.algorithm
    )

    return encoded_jwt


def decode_access_token(token: str) -> dict[str, Any] | None:
    """Decodifica y valida un token JWT.

    Args:
        token: Token JWT a decodificar

    Returns:
        Payload del token si es válido, None si es inválido o expirado

    Example:
        >>> token = create_access_token({"sub": "usuario1"})
        >>> payload = decode_access_token(token)
        >>> print(payload["sub"])
        usuario1
    """
    try:
        payload = jwt.decode(
            token, settings.jwt.secret_key, algorithms=[settings.jwt.algorithm]
        )
        return payload
    except JWTError:
        return None
