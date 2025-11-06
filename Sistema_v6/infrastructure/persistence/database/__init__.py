"""Módulo de base de datos.

Exporta los componentes principales de la capa de base de datos:
- Base: Clase base de SQLAlchemy para modelos
- engine: Engine de SQLAlchemy
- SessionLocal: Factory de sesiones
- get_db: Dependency para FastAPI
- Usuario: Modelo de usuario
"""

from .connection import Base, SessionLocal, engine, get_db
from .models import Usuario

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "Usuario",
]
