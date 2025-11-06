"""Tests para los schemas de configuración.

Este módulo contiene tests para verificar la validación de schemas Pydantic
de configuración del sistema.
"""

import pytest
from pydantic import ValidationError

from presentation.api.rest.schemas import (
    BrowserConfigSchema,
    MonitoreoConfigSchema,
    ScrapingConfigSchema,
    MCPConfigSchema,
    StorageConfigSchema,
    SystemConfigResponse,
    SystemConfigUpdateRequest,
)


class TestBrowserConfigSchema:
    """Tests para BrowserConfigSchema."""

    def test_valid_browser_config(self):
        """Test creación de schema válido de browser."""
        config = BrowserConfigSchema(
            headless=True,
            timeout_ms=30000,
            navigation_timeout_ms=60000,
            user_agent="Mozilla/5.0"
        )

        assert config.headless == True
        assert config.timeout_ms == 30000
        assert config.navigation_timeout_ms == 60000
        assert config.user_agent == "Mozilla/5.0"


    def test_browser_config_with_null_user_agent(self):
        """Test browser config con user_agent=None es válido."""
        config = BrowserConfigSchema(
            headless=False,
            timeout_ms=45000,
            navigation_timeout_ms=90000,
            user_agent=None
        )

        assert config.user_agent is None


class TestMonitoreoConfigSchema:
    """Tests para MonitoreoConfigSchema."""

    def test_valid_monitoreo_config_basico(self):
        """Test configuración básica de monitoreo sin modo avanzado."""
        config = MonitoreoConfigSchema(
            intervalo_segundos=1800,
            dias_actividad=30,
            max_reintentos=3,
            notificar_cambios=True,
            descargar_archivos=True,
            intervalos_laboral_expedientes=None,
            intervalos_laboral_entradas=None,
            intervalos_no_laboral_expedientes=None,
            intervalos_no_laboral_entradas=None,
            dias_laborales=["lunes", "martes", "miercoles", "jueves", "viernes"],
            hora_inicio="08:00",
            hora_fin="18:00"
        )

        assert config.intervalo_segundos == 1800
        assert config.dias_actividad == 30
        assert config.intervalos_laboral_expedientes is None


    def test_valid_monitoreo_config_avanzado(self):
        """Test configuración avanzada de monitoreo con horarios laborales."""
        config = MonitoreoConfigSchema(
            intervalo_segundos=0,
            dias_actividad=30,
            max_reintentos=3,
            notificar_cambios=True,
            descargar_archivos=True,
            intervalos_laboral_expedientes=10,
            intervalos_laboral_entradas=15,
            intervalos_no_laboral_expedientes=60,
            intervalos_no_laboral_entradas=30,
            dias_laborales=["lunes", "martes", "miercoles", "jueves", "viernes"],
            hora_inicio="08:00",
            hora_fin="18:00"
        )

        assert config.intervalos_laboral_expedientes == 10
        assert config.intervalos_laboral_entradas == 15
        assert config.intervalos_no_laboral_expedientes == 60
        assert config.intervalos_no_laboral_entradas == 30


class TestScrapingConfigSchema:
    """Tests para ScrapingConfigSchema."""

    def test_valid_scraping_config(self):
        """Test configuración válida de scraping."""
        config = ScrapingConfigSchema(
            timeout_default=8000,
            timeout_login=60000,
            timeout_descarga=30000,
            max_paginas_expedientes=200,
            max_reintentos_descarga=3
        )

        assert config.timeout_default == 8000
        assert config.timeout_login == 60000
        assert config.max_paginas_expedientes == 200


    def test_scraping_config_sin_limite_paginas(self):
        """Test scraping config con max_paginas_expedientes=None."""
        config = ScrapingConfigSchema(
            timeout_default=8000,
            timeout_login=60000,
            timeout_descarga=30000,
            max_paginas_expedientes=None,
            max_reintentos_descarga=3
        )

        assert config.max_paginas_expedientes is None


class TestMCPConfigSchema:
    """Tests para MCPConfigSchema."""

    def test_valid_mcp_config(self):
        """Test configuración válida de MCP Server."""
        config = MCPConfigSchema(
            habilitar=True,
            puerto=5000,
            mode="stdio",
            workspace_path="workspace",
            server_name="sintaxis-actuaciones-v6",
            enable_pdf_extraction=True,
            enable_full_text_search=True,
            enable_statistics=True,
            max_pdf_pages=100,
            max_pdf_size_mb=50
        )

        assert config.habilitar == True
        assert config.puerto == 5000
        assert config.mode == "stdio"
        assert config.max_pdf_pages == 100


    def test_mcp_config_mode_http(self):
        """Test MCP config con mode='http'."""
        config = MCPConfigSchema(
            habilitar=True,
            puerto=5000,
            mode="http",
            workspace_path="workspace",
            server_name="test-server",
            enable_pdf_extraction=False,
            enable_full_text_search=False,
            enable_statistics=False,
            max_pdf_pages=50,
            max_pdf_size_mb=25
        )

        assert config.mode == "http"


class TestStorageConfigSchema:
    """Tests para StorageConfigSchema."""

    def test_valid_storage_config(self):
        """Test configuración válida de Storage."""
        config = StorageConfigSchema(
            base_path="data",
            json_base_file="expedientes_base.json",
            json_sistema_file="expedientes_sistema.json",
            workspaces_dir="workspaces",
            downloads_dir="descargas",
            pretty_json=True,
            ensure_ascii=False
        )

        assert config.base_path == "data"
        assert config.pretty_json == True
        assert config.ensure_ascii == False


class TestSystemConfigResponse:
    """Tests para SystemConfigResponse."""

    def test_valid_system_config_response(self):
        """Test creación de response completo del sistema."""
        response = SystemConfigResponse(
            browser=BrowserConfigSchema(
                headless=True,
                timeout_ms=30000,
                navigation_timeout_ms=60000,
                user_agent=None
            ),
            monitoreo=MonitoreoConfigSchema(
                intervalo_segundos=1800,
                dias_actividad=30,
                max_reintentos=3,
                notificar_cambios=True,
                descargar_archivos=True,
                intervalos_laboral_expedientes=None,
                intervalos_laboral_entradas=None,
                intervalos_no_laboral_expedientes=None,
                intervalos_no_laboral_entradas=None,
                dias_laborales=["lunes"],
                hora_inicio="08:00",
                hora_fin="18:00"
            ),
            scraping=ScrapingConfigSchema(
                timeout_default=8000,
                timeout_login=60000,
                timeout_descarga=30000,
                max_paginas_expedientes=200,
                max_reintentos_descarga=3
            ),
            mcp=MCPConfigSchema(
                habilitar=True,
                puerto=5000,
                mode="stdio",
                workspace_path="workspace",
                server_name="test",
                enable_pdf_extraction=True,
                enable_full_text_search=True,
                enable_statistics=True,
                max_pdf_pages=100,
                max_pdf_size_mb=50
            ),
            storage=StorageConfigSchema(
                base_path="data",
                json_base_file="base.json",
                json_sistema_file="sistema.json",
                workspaces_dir="workspaces",
                downloads_dir="descargas",
                pretty_json=True,
                ensure_ascii=False
            )
        )

        assert response.browser.headless == True
        assert response.monitoreo.intervalo_segundos == 1800
        assert response.scraping.timeout_default == 8000
        assert response.mcp.puerto == 5000
        assert response.storage.base_path == "data"


class TestSystemConfigUpdateRequest:
    """Tests para SystemConfigUpdateRequest."""

    def test_update_request_solo_browser(self):
        """Test request de actualización con solo browser."""
        request = SystemConfigUpdateRequest(
            browser=BrowserConfigSchema(
                headless=False,
                timeout_ms=45000,
                navigation_timeout_ms=90000,
                user_agent=None
            ),
            monitoreo=None,
            scraping=None,
            mcp=None,
            storage=None
        )

        assert request.browser is not None
        assert request.monitoreo is None
        assert request.scraping is None


    def test_update_request_multiple_sections(self):
        """Test request con múltiples secciones."""
        request = SystemConfigUpdateRequest(
            browser=BrowserConfigSchema(
                headless=True,
                timeout_ms=30000,
                navigation_timeout_ms=60000,
                user_agent=None
            ),
            monitoreo=MonitoreoConfigSchema(
                intervalo_segundos=3600,
                dias_actividad=60,
                max_reintentos=5,
                notificar_cambios=False,
                descargar_archivos=True,
                intervalos_laboral_expedientes=None,
                intervalos_laboral_entradas=None,
                intervalos_no_laboral_expedientes=None,
                intervalos_no_laboral_entradas=None,
                dias_laborales=["lunes"],
                hora_inicio="09:00",
                hora_fin="17:00"
            ),
            scraping=None,
            mcp=None,
            storage=None
        )

        assert request.browser.timeout_ms == 30000
        assert request.monitoreo.intervalo_segundos == 3600


    def test_update_request_all_null(self):
        """Test request válido con todas las secciones en None."""
        request = SystemConfigUpdateRequest(
            browser=None,
            monitoreo=None,
            scraping=None,
            mcp=None,
            storage=None
        )

        assert request.browser is None
        assert request.monitoreo is None
        assert request.scraping is None
        assert request.mcp is None
        assert request.storage is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
