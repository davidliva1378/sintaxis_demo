"""Schemas Pydantic para autenticación.

Este módulo define los schemas de request/response para los endpoints de auth.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserRegister(BaseModel):
    """Schema para registro de usuario."""

    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserLogin(BaseModel):
    """Schema para login de usuario."""

    username: str
    password: str


class Token(BaseModel):
    """Schema para respuesta de token."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema para datos del token decodificado."""

    username: str | None = None


class UserResponse(BaseModel):
    """Schema para respuesta de usuario (sin password)."""

    id: int
    username: str
    email: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    has_pjn_credentials: bool = False

    class Config:
        """Configuración del schema."""

        from_attributes = True


class PJNCredentialsUpdate(BaseModel):
    """Schema para actualizar credenciales del PJN.

    Note:
        Las credenciales deben ser encriptadas en el cliente antes de enviarse.
    """

    pjn_usuario_encrypted: str
    pjn_password_encrypted: str


class PJNCredentialsResponse(BaseModel):
    """Schema para respuesta de credenciales PJN."""

    has_credentials: bool
    pjn_usuario_encrypted: str | None = None
    pjn_password_encrypted: str | None = None
