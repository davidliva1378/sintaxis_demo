"""Configuración de conexión a la base de datos.

Este módulo configura la conexión a SQLAlchemy y proporciona la sesión de base de datos.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from infrastructure.config import get_settings

settings = get_settings()

# Determinar la URL de la base de datos
# Por defecto usamos SQLite para MVP
if hasattr(settings, "database_url") and settings.database_url:
    SQLALCHEMY_DATABASE_URL = settings.database_url
else:
    # SQLite por defecto en data/sistema.db
    db_path = settings.storage.base_path / "sistema.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    SQLALCHEMY_DATABASE_URL = f"sqlite:///{db_path}"

# Crear engine
# connect_args solo es necesario para SQLite
connect_args = {"check_same_thread": False} if "sqlite" in SQLALCHEMY_DATABASE_URL else {}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args,
    echo=False,  # Desactivado para no interferir con MCP stdio
)

# Crear SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para los modelos
Base = declarative_base()


def get_db():
    """Dependency para FastAPI que proporciona una sesión de base de datos.

    Yields:
        Session: Sesión de SQLAlchemy

    Example:
        @app.get("/users/")
        def read_users(db: Session = Depends(get_db)):
            return db.query(Usuario).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
