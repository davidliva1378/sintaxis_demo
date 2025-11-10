"""Tests para el router de configuración del sistema.

Este módulo contiene tests para verificar el correcto funcionamiento
de los endpoints de configuración.
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import shutil

from presentation.api.rest.main import app
from infrastructure.config import reload_settings


@pytest.fixture
def client():
    """Cliente de pruebas para FastAPI."""
    return TestClient(app)


@pytest.fixture
def temp_env_file():
    """Crea un archivo .env temporal para tests."""
    # Guardar el .env original
    original_env = Path(".env")
    backup_env = Path(".env.backup")

    if original_env.exists():
        shutil.copy(original_env, backup_env)

    # Crear .env temporal con valores de prueba
    test_env_content = """
# Test configuration
BROWSER_HEADLESS=true
BROWSER_TIMEOUT_MS=30000
BROWSER_NAVIGATION_TIMEOUT_MS=60000

MONITOREO_INTERVALO_SEGUNDOS=1800
MONITOREO_DIAS_ACTIVIDAD=30
MONITOREO_MAX_REINTENTOS=3
MONITOREO_NOTIFICAR_CAMBIOS=true
MONITOREO_DESCARGAR_ARCHIVOS=true
MONITOREO_DIAS_LABORALES=lunes,martes,miercoles,jueves,viernes
MONITOREO_HORA_INICIO=08:00
MONITOREO_HORA_FIN=18:00

SCRAPING_TIMEOUT_DEFAULT=8000
SCRAPING_TIMEOUT_LOGIN=60000
SCRAPING_TIMEOUT_DESCARGA=30000
SCRAPING_MAX_PAGINAS_EXPEDIENTES=200
SCRAPING_MAX_REINTENTOS_DESCARGA=3

MCP_HABILITAR=true
MCP_PUERTO=5000
MCP_MODE=stdio
MCP_WORKSPACE_PATH=workspace
MCP_SERVER_NAME=sintaxis-actuaciones-v6
MCP_ENABLE_PDF_EXTRACTION=true
MCP_ENABLE_FULL_TEXT_SEARCH=true
MCP_ENABLE_STATISTICS=true
MCP_MAX_PDF_PAGES=100
MCP_MAX_PDF_SIZE_MB=50

STORAGE_BASE_PATH=data
STORAGE_JSON_BASE_FILE=expedientes_base.json
STORAGE_JSON_SISTEMA_FILE=expedientes_sistema.json
STORAGE_WORKSPACES_DIR=workspaces
STORAGE_DOWNLOADS_DIR=descargas
STORAGE_PRETTY_JSON=true
STORAGE_ENSURE_ASCII=false
"""

    original_env.write_text(test_env_content)

    yield original_env

    # Restaurar el .env original
    if backup_env.exists():
        shutil.copy(backup_env, original_env)
        backup_env.unlink()


class TestConfigRouter:
    """Tests para el router de configuración."""

    def test_get_config_sistema_success(self, client, temp_env_file):
        """Test GET /api/v1/config/sistema retorna configuración correcta."""
        # Recargar settings con el .env temporal
        reload_settings()

        response = client.get("/api/v1/config/sistema")

        assert response.status_code == 200
        data = response.json()

        # Verificar estructura de respuesta
        assert "browser" in data
        assert "monitoreo" in data
        assert "scraping" in data
        assert "mcp" in data
        assert "storage" in data

        # Verificar valores de browser
        assert data["browser"]["headless"] == True
        assert data["browser"]["timeout_ms"] == 30000
        assert data["browser"]["navigation_timeout_ms"] == 60000

        # Verificar valores de monitoreo
        assert data["monitoreo"]["intervalo_segundos"] == 1800
        assert data["monitoreo"]["dias_actividad"] == 30
        assert data["monitoreo"]["max_reintentos"] == 3

        # Verificar valores de scraping
        assert data["scraping"]["timeout_default"] == 8000
        assert data["scraping"]["timeout_login"] == 60000
        assert data["scraping"]["max_reintentos_descarga"] == 3


    def test_put_config_sistema_browser_success(self, client, temp_env_file):
        """Test PUT /api/v1/config/sistema actualiza browser correctamente."""
        update_data = {
            "browser": {
                "headless": False,
                "timeout_ms": 45000,
                "navigation_timeout_ms": 90000,
                "user_agent": "Test User Agent"
            }
        }

        response = client.put("/api/v1/config/sistema", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assert "message" in data
        assert "updates" in data
        assert "BROWSER_HEADLESS" in data["updates"]
        assert data["updates"]["BROWSER_HEADLESS"] == "false"
        assert data["updates"]["BROWSER_TIMEOUT_MS"] == "45000"


    def test_put_config_sistema_monitoreo_success(self, client, temp_env_file):
        """Test PUT /api/v1/config/sistema actualiza monitoreo correctamente."""
        update_data = {
            "monitoreo": {
                "intervalo_segundos": 3600,
                "dias_actividad": 60,
                "max_reintentos": 5,
                "notificar_cambios": False,
                "descargar_archivos": True,
                "dias_laborales": ["lunes", "martes", "miercoles"],
                "hora_inicio": "09:00",
                "hora_fin": "17:00"
            }
        }

        response = client.put("/api/v1/config/sistema", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assert data["updates"]["MONITOREO_INTERVALO_SEGUNDOS"] == "3600"
        assert data["updates"]["MONITOREO_DIAS_ACTIVIDAD"] == "60"


    def test_put_config_sistema_validation_error_timeout_too_low(self, client, temp_env_file):
        """Test PUT con timeout muy bajo retorna error de validación."""
        update_data = {
            "browser": {
                "headless": True,
                "timeout_ms": 500,  # Menor al mínimo de 1000
                "navigation_timeout_ms": 60000,
                "user_agent": None
            }
        }

        response = client.put("/api/v1/config/sistema", json=update_data)

        assert response.status_code == 400
        assert "timeout_ms debe ser >= 1000ms" in response.json()["detail"]


    def test_put_config_sistema_validation_error_intervalo_negativo(self, client, temp_env_file):
        """Test PUT con intervalo negativo retorna error."""
        update_data = {
            "monitoreo": {
                "intervalo_segundos": -100,
                "dias_actividad": 30,
                "max_reintentos": 3,
                "notificar_cambios": True,
                "descargar_archivos": True,
                "dias_laborales": ["lunes"],
                "hora_inicio": "08:00",
                "hora_fin": "18:00"
            }
        }

        response = client.put("/api/v1/config/sistema", json=update_data)

        assert response.status_code == 400
        assert "intervalo_segundos debe ser >= 0" in response.json()["detail"]


    def test_put_config_sistema_mcp_success(self, client, temp_env_file):
        """Test PUT actualiza configuración de MCP correctamente."""
        update_data = {
            "mcp": {
                "habilitar": False,
                "puerto": 6000,
                "mode": "http",
                "workspace_path": "test_workspace",
                "server_name": "test-server",
                "enable_pdf_extraction": False,
                "enable_full_text_search": True,
                "enable_statistics": True,
                "max_pdf_pages": 50,
                "max_pdf_size_mb": 25
            }
        }

        response = client.put("/api/v1/config/sistema", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assert data["updates"]["MCP_HABILITAR"] == "false"
        assert data["updates"]["MCP_PUERTO"] == "6000"
        assert data["updates"]["MCP_MODE"] == "http"


    def test_put_config_sistema_storage_success(self, client, temp_env_file):
        """Test PUT actualiza configuración de Storage correctamente."""
        update_data = {
            "storage": {
                "base_path": "test_data",
                "json_base_file": "test_base.json",
                "json_sistema_file": "test_sistema.json",
                "workspaces_dir": "test_workspaces",
                "downloads_dir": "test_downloads",
                "pretty_json": False,
                "ensure_ascii": True
            }
        }

        response = client.put("/api/v1/config/sistema", json=update_data)

        assert response.status_code == 200
        data = response.json()

        assert data["success"] == True
        assert data["updates"]["STORAGE_BASE_PATH"] == "test_data"
        assert data["updates"]["STORAGE_PRETTY_JSON"] == "false"


    def test_put_config_sistema_partial_update(self, client, temp_env_file):
        """Test PUT con actualización parcial solo modifica campos enviados."""
        # Solo actualizar browser
        update_data = {
            "browser": {
                "headless": False,
                "timeout_ms": 35000,
                "navigation_timeout_ms": 70000,
                "user_agent": None
            }
        }

        response = client.put("/api/v1/config/sistema", json=update_data)

        assert response.status_code == 200
        data = response.json()

        # Verificar que solo se actualizó browser
        assert "BROWSER_HEADLESS" in data["updates"]
        assert "MONITOREO_INTERVALO_SEGUNDOS" not in data["updates"]
        assert "SCRAPING_TIMEOUT_DEFAULT" not in data["updates"]


    def test_put_config_sistema_validation_error_puerto_invalido(self, client, temp_env_file):
        """Test PUT con puerto inválido retorna error."""
        update_data = {
            "mcp": {
                "habilitar": True,
                "puerto": 99999,  # Puerto inválido > 65535
                "mode": "stdio",
                "workspace_path": "workspace",
                "server_name": "test",
                "enable_pdf_extraction": True,
                "enable_full_text_search": True,
                "enable_statistics": True,
                "max_pdf_pages": 100,
                "max_pdf_size_mb": 50
            }
        }

        response = client.put("/api/v1/config/sistema", json=update_data)

        assert response.status_code == 400
        assert "puerto debe estar entre 1 y 65535" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
