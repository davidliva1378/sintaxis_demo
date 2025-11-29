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

    @property
    def has_pjn_credentials(self) -> bool:
        """Indica si el usuario tiene credenciales PJN configuradas."""
        return bool(self.pjn_usuario_encrypted and self.pjn_password_encrypted)

    def __repr__(self) -> str:
        """Representación string del usuario."""
        return f"<Usuario(id={self.id}, username='{self.username}', email='{self.email}')>"


class Expediente(Base):
    """Modelo de expediente."""
    __tablename__ = "expedientes"

    id = Column(Integer, primary_key=True, index=True)
    numero_normalizado = Column(String(50), unique=True, index=True)
    numero_original = Column(String(50))
    caratula = Column(Text)
    dependencia = Column(String(255))
    situacion = Column(String(255))
    ultima_actuacion = Column(DateTime, nullable=True)
    
    # Monitoreo
    estado_monitoreo = Column(String(50), default="activo")  # activo, pausado, archivado
    prioridad = Column(String(50), default="normal")
    
    # Metadatos
    fecha_creacion = Column(DateTime, default=datetime.utcnow)
    fecha_ultima_extraccion = Column(DateTime, nullable=True)
    fecha_ultimo_procesamiento = Column(DateTime, nullable=True)
    
    # Estadisticas
    total_actuaciones = Column(Integer, default=0)
    total_pdfs_descargados = Column(Integer, default=0)


class Actuacion(Base):
    """Modelo de actuación."""
    __tablename__ = "actuaciones"

    id = Column(String(50), primary_key=True)  # ID del sistema judicial o hash
    expediente_id = Column(Integer, index=True)
    fecha = Column(DateTime)
    tipo_ia = Column(String(100))  # Clasificación IA
    detalle = Column(Text)
    texto_extraido = Column(Text, nullable=True)
    utilidad = Column(String(50))  # ALTA, MEDIA, BAJA
    score = Column(Integer, default=0)


class Vencimiento(Base):
    """Modelo de vencimiento."""
    __tablename__ = "vencimientos"

    id = Column(Integer, primary_key=True, index=True)
    expediente_id = Column(Integer, index=True)
    descripcion = Column(Text)
    fecha_vencimiento = Column(DateTime)
    estado = Column(String(50), default="pendiente")  # pendiente, cumplido, vencido
    prioridad = Column(String(50), default="media")


class EntidadExtraida(Base):
    """Modelo de entidad extraída (NER)."""
    __tablename__ = "entidades_extraidas"

    id = Column(Integer, primary_key=True, index=True)
    expediente_id = Column(Integer, index=True)
    actuacion_id = Column(String(50), nullable=True)
    entity_type = Column(String(50))  # PERSONA, ORGANIZACION, FECHA, etc.
    entity_value = Column(Text)
    confidence_score = Column(Integer, default=0)

