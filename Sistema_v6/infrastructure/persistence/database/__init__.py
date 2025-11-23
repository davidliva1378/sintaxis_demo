"""Módulo de base de datos.

Exporta los componentes principales de la capa de base de datos:
- Base: Clase base de SQLAlchemy para modelos
- engine: Engine de SQLAlchemy (SQLite)
- SessionLocal: Factory de sesiones (SQLite)
- get_db: Dependency para FastAPI (SQLite)
- Usuario: Modelo de usuario
- mysql_engine: Engine de SQLAlchemy (MySQL)
- get_mysql_db: Dependency para FastAPI (MySQL)
- get_mysql_connection: Context manager para MySQL
- get_mysql_pool_status: Estado del pool MySQL
"""

from .connection import Base, SessionLocal, engine, get_db
from .models import Usuario
from .mysql_pool import (
    mysql_engine,
    MySQLSessionLocal,
    get_mysql_db,
    get_mysql_connection,
    get_mysql_pool_status,
    test_mysql_connection,
    get_pooled_connection,
    get_native_pool_status,
)

__all__ = [
    # SQLite (auth/usuarios)
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "Usuario",
    # MySQL (expedientes/actuaciones)
    "mysql_engine",
    "MySQLSessionLocal",
    "get_mysql_db",
    "get_mysql_connection",
    "get_mysql_pool_status",
    "test_mysql_connection",
    "get_pooled_connection",
    "get_native_pool_status",
]
