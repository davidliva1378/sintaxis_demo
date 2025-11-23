"""Connection pool para MySQL.

Este módulo proporciona un pool de conexiones MySQL centralizado
usando mysql.connector.pooling para mejor rendimiento.
También ofrece SQLAlchemy QueuePool para uso con ORM.
"""

from __future__ import annotations

import os
import logging
from contextlib import contextmanager

import mysql.connector
from mysql.connector import pooling
from sqlalchemy import create_engine, text
from sqlalchemy.pool import QueuePool
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)

# Configuración de MySQL desde variables de entorno
MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
MYSQL_PORT = os.getenv('MYSQL_PORT', '3306')
MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'sintaxis')
MYSQL_USER = os.getenv('MYSQL_USER', 'root')
MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')

# Construir URL de conexión MySQL
MYSQL_DATABASE_URL = (
    f"mysql+mysqlconnector://{MYSQL_USER}:{MYSQL_PASSWORD}"
    f"@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}"
    f"?charset=utf8mb4"
)

# Crear engine con pool de conexiones
mysql_engine = create_engine(
    MYSQL_DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,           # Conexiones permanentes en el pool
    max_overflow=10,       # Conexiones adicionales permitidas
    pool_timeout=30,       # Segundos esperando conexión disponible
    pool_recycle=1800,     # Reciclar conexiones cada 30 min
    pool_pre_ping=True,    # Verificar conexión antes de usar
    echo=False,            # No loguear SQL
)

# SessionLocal para MySQL
MySQLSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=mysql_engine)


def get_mysql_db():
    """Dependency para FastAPI que proporciona una sesión MySQL.

    Yields:
        Session: Sesión de SQLAlchemy conectada a MySQL

    Example:
        @app.get("/expedientes/")
        def read_expedientes(db: Session = Depends(get_mysql_db)):
            result = db.execute(text("SELECT * FROM expedientes"))
            return result.fetchall()
    """
    db = MySQLSessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_mysql_connection():
    """Context manager para obtener una conexión MySQL del pool.

    Para uso directo sin FastAPI dependency injection.

    Example:
        with get_mysql_connection() as conn:
            result = conn.execute(text("SELECT 1"))
            print(result.fetchone())

    Yields:
        Connection: Conexión MySQL del pool
    """
    conn = mysql_engine.connect()
    try:
        yield conn
    finally:
        conn.close()


def get_mysql_pool_status() -> dict:
    """Obtiene el estado actual del pool de conexiones.

    Returns:
        dict con información del pool
    """
    pool = mysql_engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
    }


def test_mysql_connection() -> bool:
    """Prueba la conexión a MySQL.

    Returns:
        True si la conexión es exitosa
    """
    try:
        with get_mysql_connection() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        return True
    except Exception as e:
        logger.error(f"Error probando conexión MySQL: {e}")
        return False


logger.info(f"MySQL SQLAlchemy pool configurado: {MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}")

# ============================================================================
# Pool nativo mysql.connector (para código existente con cursor patterns)
# ============================================================================

# Configuración del pool nativo
_mysql_pool_config = {
    'pool_name': 'sintaxis_pool',
    'pool_size': 5,
    'pool_reset_session': True,
    'host': MYSQL_HOST,
    'port': int(MYSQL_PORT),
    'database': MYSQL_DATABASE,
    'user': MYSQL_USER,
    'password': MYSQL_PASSWORD,
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci',
}

# Crear pool nativo (singleton)
_native_pool = None

def _get_native_pool():
    """Obtiene o crea el pool nativo de mysql.connector."""
    global _native_pool
    if _native_pool is None:
        _native_pool = pooling.MySQLConnectionPool(**_mysql_pool_config)
        logger.info("MySQL native pool creado")
    return _native_pool


def get_pooled_connection():
    """Obtiene una conexión del pool nativo de mysql.connector.

    Esta función es compatible con el código existente que usa
    mysql.connector directamente con cursor patterns.

    Returns:
        PooledMySQLConnection: Conexión del pool

    Example:
        conn = get_pooled_connection()
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM expedientes")
            results = cursor.fetchall()
        finally:
            conn.close()  # Retorna la conexión al pool
    """
    pool = _get_native_pool()
    return pool.get_connection()


def get_native_pool_status() -> dict:
    """Obtiene el estado del pool nativo.

    Returns:
        dict con información del pool
    """
    try:
        pool = _get_native_pool()
        return {
            "pool_name": pool.pool_name,
            "pool_size": pool.pool_size,
        }
    except Exception as e:
        return {"error": str(e)}
