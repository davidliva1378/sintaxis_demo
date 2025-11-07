"""Modelos de base de datos SQLAlchemy.

Este módulo define los modelos ORM para el sistema multi-usuario.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from .connection import Base


class Usuario(Base):
    """Modelo de usuario del sistema.

    Attributes:
        id: ID único del usuario
        username: Nombre de usuario único
        email: Email único del usuario
        hashed_password: Contraseña hasheada con bcrypt
        pjn_usuario_encrypted: Usuario del PJN encriptado con Fernet
        pjn_password_encrypted: Contraseña del PJN encriptada con Fernet
        created_at: Fecha de creación del usuario
        updated_at: Fecha de última actualización
        is_active: Si el usuario está activo
        is_superuser: Si el usuario es administrador

    Note:
        Las credenciales del PJN se almacenan encriptadas con Fernet (symmetric encryption).
        El cliente debe encriptar las credenciales antes de enviarlas al backend.
    """

    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Credenciales PJN encriptadas (Fernet symmetric encryption)
    pjn_usuario_encrypted = Column(Text, nullable=True)
    pjn_password_encrypted = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Status flags
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        """Representación string del usuario."""
        return f"<Usuario(id={self.id}, username='{self.username}', email='{self.email}')>"
