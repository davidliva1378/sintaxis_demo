"""Configuración de pytest para tests del sistema.

Este archivo contiene fixtures y configuraciones compartidas para todos los tests.
"""

import sys
import os
from pathlib import Path
import pytest
from unittest.mock import MagicMock

# Agregar el directorio raíz al path para poder importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.config.settings import Settings, get_settings, reload_settings


@pytest.fixture(autouse=True)
def clean_env():
    """Limpia variables de entorno antes de cada test."""
    # Guardar estado original
    old_env = dict(os.environ)
    
    yield
    
    # Restaurar estado original
    os.environ.clear()
    os.environ.update(old_env)


@pytest.fixture
def test_settings(clean_env):
    """Provee una instancia de configuración para testing."""
    # Configurar env vars para test
    os.environ["ENVIRONMENT"] = "testing"
    os.environ["DB_DATABASE"] = "sintaxis_test"
    
    # Recargar settings
    return reload_settings()


@pytest.fixture
def mock_qdrant():
    """Mock para el servicio Qdrant."""
    mock = MagicMock()
    mock.search_similar.return_value = []
    mock.count.return_value = 0
    return mock


@pytest.fixture
def mock_llm():
    """Mock para el servicio LLM."""
    mock = MagicMock()
    mock.generate_answer.return_value = MagicMock(respuesta="Respuesta de prueba")
    mock.summarize.return_value = "Resumen de prueba"
    return mock
