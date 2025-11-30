"""
Tests unitarios para el router de Configuración.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from presentation.api.rest.main import app
from presentation.api.rest.routers.config import router

client = TestClient(app)

@pytest.mark.unit
class TestConfigRouter:
    """Tests para endpoints de configuración."""

    @patch("presentation.api.rest.routers.config.get_settings")
    def test_get_system_config(self, mock_get_settings):
        """Debe obtener la configuración del sistema."""
        # Setup mock settings with ALL required fields
        mock_settings = Mock()
        
        # Browser
        mock_settings.browser.headless = True
        mock_settings.browser.timeout_ms = 30000
        mock_settings.browser.navigation_timeout_ms = 60000
        mock_settings.browser.user_agent = None
        
        # Monitoreo
        mock_settings.monitoreo.intervalo_segundos = 3600
        mock_settings.monitoreo.dias_actividad = 30
        mock_settings.monitoreo.max_reintentos = 3
        mock_settings.monitoreo.notificar_cambios = True
        mock_settings.monitoreo.descargar_archivos = False
        mock_settings.monitoreo.fecha_corte_dias = None
        mock_settings.monitoreo.max_paginas_monitoreo = None
        mock_settings.monitoreo.tiempo_maximo_extraccion = None
        mock_settings.monitoreo.detener_en_duplicado = True
        mock_settings.monitoreo.orden_extraccion = "fecha"
        mock_settings.monitoreo.intervalos_laboral_expedientes = None
        mock_settings.monitoreo.intervalos_laboral_entradas = None
        mock_settings.monitoreo.intervalos_no_laboral_expedientes = None
        mock_settings.monitoreo.intervalos_no_laboral_entradas = None
        mock_settings.monitoreo.dias_laborales = ["lunes", "martes"]
        mock_settings.monitoreo.hora_inicio = "08:00"
        mock_settings.monitoreo.hora_fin = "18:00"
        
        # Scraping
        mock_settings.scraping.timeout_default = 5000
        mock_settings.scraping.timeout_login = 10000
        mock_settings.scraping.timeout_descarga = 30000
        mock_settings.scraping.max_paginas_expedientes = None
        mock_settings.scraping.max_reintentos_descarga = 3
        
        # MCP
        mock_settings.mcp.habilitar = True
        mock_settings.mcp.puerto = 8000
        mock_settings.mcp.mode = "stdio"
        mock_settings.mcp.workspace_path = "/tmp"
        mock_settings.mcp.server_name = "test"
        mock_settings.mcp.enable_pdf_extraction = True
        mock_settings.mcp.enable_full_text_search = True
        mock_settings.mcp.enable_statistics = True
        mock_settings.mcp.max_pdf_pages = 100
        mock_settings.mcp.max_pdf_size_mb = 10
        
        # Storage
        mock_settings.storage.base_path = Mock()
        mock_settings.storage.base_path.__str__ = Mock(return_value="/tmp/data")
        mock_settings.storage.json_base_file = "base.json"
        mock_settings.storage.json_sistema_file = "sistema.json"
        mock_settings.storage.workspaces_dir = "workspaces"
        mock_settings.storage.downloads_dir = "downloads"
        mock_settings.storage.pretty_json = True
        mock_settings.storage.ensure_ascii = False
        
        mock_get_settings.return_value = mock_settings
        
        # Execute
        response = client.get("/api/v1/config/sistema")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["browser"]["headless"] is True
        assert data["monitoreo"]["intervalo_segundos"] == 3600
        assert data["mcp"]["habilitar"] is True

    @patch("presentation.api.rest.routers.config._actualizar_env_file")
    @patch("presentation.api.rest.routers.config.reload_settings")
    @patch("presentation.api.rest.routers.config.PROJECT_ROOT")
    def test_update_system_config_success(
        self, 
        mock_project_root, 
        mock_reload, 
        mock_update_env
    ):
        """Debe actualizar la configuración correctamente."""
        mock_project_root.__truediv__.return_value = Mock()
        
        # Provide COMPLETE objects for update
        update_data = {
            "browser": {
                "headless": False,
                "timeout_ms": 45000,
                "navigation_timeout_ms": 60000,
                "user_agent": None
            },
            "monitoreo": {
                "intervalo_segundos": 7200,
                "dias_actividad": 30,
                "max_reintentos": 3,
                "notificar_cambios": True,
                "descargar_archivos": False,
                "dias_laborales": ["lunes"],
                "hora_inicio": "09:00",
                "hora_fin": "17:00"
            }
        }
        
        response = client.put("/api/v1/config/sistema", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify env updates
        mock_update_env.assert_called_once()
        updates = mock_update_env.call_args[0][1]
        assert updates["BROWSER_HEADLESS"] == "false"
        assert updates["BROWSER_TIMEOUT_MS"] == "45000"
        assert updates["MONITOREO_INTERVALO_SEGUNDOS"] == "7200"
        
        # Verify reload
        mock_reload.assert_called_once()

    def test_update_system_config_validation_error(self):
        """Debe validar los datos de entrada."""
        update_data = {
            "browser": {
                "headless": True,
                "timeout_ms": 500,  # Invalid < 1000
                "navigation_timeout_ms": 60000
            }
        }
        
        response = client.put("/api/v1/config/sistema", json=update_data)
        
        # Expect 400 because the router explicitly raises HTTPException(400)
        # BUT Pydantic might catch it first? No, Pydantic checks types.
        # The router checks values: if config.browser.timeout_ms < 1000
        assert response.status_code == 400
        assert "timeout_ms" in response.json()["detail"]

    @patch("presentation.api.rest.routers.config.VencimientosConfig")
    def test_get_vencimientos_config(self, mock_vencimientos_config):
        """Debe obtener configuración de vencimientos."""
        mock_instance = Mock()
        mock_instance.config = Mock()
        # Ensure dict() returns valid fields for VencimientosConfigModel
        mock_instance.config.dict.return_value = {
            "hybrid_analysis_enabled": False,
            "analysis_margin_days": 7,
            "llm_model": None,
            "system_prompt": "prompt",
            "custom_terms": []
        }
        # Also need to mock the attributes access if Pydantic model is used directly
        mock_instance.config.hybrid_analysis_enabled = False
        mock_instance.config.analysis_margin_days = 7
        mock_instance.config.llm_model = None
        mock_instance.config.system_prompt = "prompt"
        mock_instance.config.custom_terms = []
        
        mock_vencimientos_config.get_instance.return_value = mock_instance
        
        response = client.get("/api/v1/config/vencimientos")
        
        assert response.status_code == 200
        data = response.json()
        assert data["analysis_margin_days"] == 7

    @patch("presentation.api.rest.routers.config.VencimientosConfig")
    def test_update_vencimientos_config(self, mock_vencimientos_config):
        """Debe actualizar configuración de vencimientos."""
        mock_instance = Mock()
        mock_instance.config = Mock()
        # Return updated config after update
        mock_instance.config.hybrid_analysis_enabled = True
        mock_instance.config.analysis_margin_days = 10
        mock_instance.config.llm_model = "gpt-4"
        mock_instance.config.system_prompt = "prompt"
        mock_instance.config.custom_terms = []
        
        mock_vencimientos_config.get_instance.return_value = mock_instance
        
        update_data = {
            "hybrid_analysis_enabled": True,
            "analysis_margin_days": 10,
            "llm_model": "gpt-4"
        }
        
        response = client.post("/api/v1/config/vencimientos", json=update_data)
        
        assert response.status_code == 200
        mock_instance.update.assert_called_once()
