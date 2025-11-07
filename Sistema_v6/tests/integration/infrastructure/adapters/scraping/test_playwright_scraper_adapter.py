"""Integration tests for PlaywrightScraperAdapter.

These tests require real PJN credentials and will connect to the actual portal.
Set the following environment variables to run these tests:
    - PJN_USUARIO: Your PJN username
    - PJN_PASSWORD: Your PJN password
    - PJN_URL: PJN portal URL (optional, defaults to https://scw.pjn.gov.ar)

To run only these tests:
    pytest tests/integration/infrastructure/adapters/scraping/test_playwright_scraper_adapter.py -v

To run with credentials:
    PJN_USUARIO=your_user PJN_PASSWORD=your_pass pytest tests/integration/... -v
"""

from __future__ import annotations

import pytest

from core.domain.entities import ExpedienteIdentificacion
from infrastructure.adapters.scraping import PlaywrightScraperAdapter
from infrastructure.config import Settings


class TestPlaywrightScraperAdapter:
    """Integration tests for PlaywrightScraperAdapter."""

    def test_initialization(self, test_settings: Settings, pjn_login_url: str):
        """Test adapter initialization."""
        adapter = PlaywrightScraperAdapter(
            login_url=pjn_login_url,
            settings=test_settings,
        )

        assert adapter._login_url == pjn_login_url
        assert adapter._settings == test_settings
        assert adapter._session_file.name == "test_session.json"

    @pytest.mark.asyncio
    async def test_extraer_expedientes_sin_credenciales(
        self,
        test_settings: Settings,
        pjn_login_url: str,
        skip_if_no_credentials,
        pjn_credentials: tuple[str, str],
    ):
        """Test extracting expedientes with real credentials."""
        adapter = PlaywrightScraperAdapter(
            login_url=pjn_login_url,
            settings=test_settings,
        )

        # Extract expedientes
        expedientes = await adapter.extraer_expedientes(
            credenciales=pjn_credentials,
            headless=True,
        )

        # Validate results
        assert isinstance(expedientes, list)

        # If there are expedientes, validate structure
        if expedientes:
            exp = expedientes[0]
            assert exp.numero
            assert exp.caratula
            assert exp.dependencia
            # Should have at least these fields populated
            print(f"✓ Extracted {len(expedientes)} expedientes")
            print(f"  First: {exp.numero} - {exp.caratula[:50]}...")

    @pytest.mark.asyncio
    async def test_extraer_entradas_con_credenciales(
        self,
        test_settings: Settings,
        pjn_login_url: str,
        skip_if_no_credentials,
        pjn_credentials: tuple[str, str],
    ):
        """Test extracting entradas with real credentials."""
        adapter = PlaywrightScraperAdapter(
            login_url=pjn_login_url,
            settings=test_settings,
        )

        # Extract entradas
        entradas = await adapter.extraer_entradas(
            credenciales=pjn_credentials,
            headless=True,
        )

        # Validate results
        assert isinstance(entradas, list)

        # If there are entradas, validate structure
        if entradas:
            entrada = entradas[0]
            assert entrada.numero
            assert entrada.caratula
            assert entrada.fecha
            print(f"✓ Extracted {len(entradas)} entradas")
            print(f"  First: {entrada.numero} - {entrada.fecha} - {entrada.caratula[:50]}...")

    @pytest.mark.asyncio
    async def test_extraer_actuaciones_con_credenciales(
        self,
        test_settings: Settings,
        pjn_login_url: str,
        skip_if_no_credentials,
        pjn_credentials: tuple[str, str],
    ):
        """Test extracting actuaciones with real credentials.

        Note: This test requires that you have at least one expediente
        available in your account. If not, this test will fail.
        """
        adapter = PlaywrightScraperAdapter(
            login_url=pjn_login_url,
            settings=test_settings,
        )

        # First get list of expedientes to find one to extract actuaciones from
        expedientes = await adapter.extraer_expedientes(
            credenciales=pjn_credentials,
            headless=True,
        )

        # Skip if no expedientes available
        if not expedientes:
            pytest.skip("No expedientes available in account to test actuaciones extraction")

        # Use first expediente
        exp = expedientes[0]
        identificacion = ExpedienteIdentificacion(
            numero=exp.numero,
            dependencia=exp.dependencia,
            caratula=exp.caratula,
        )

        # Extract actuaciones
        archivo = await adapter.extraer_actuaciones(
            identificacion=identificacion,
            credenciales=pjn_credentials,
            headless=True,
        )

        # Validate results
        assert archivo is not None
        assert archivo.encabezado is not None
        assert archivo.actuaciones is not None
        assert isinstance(archivo.actuaciones, tuple)

        print(f"✓ Extracted actuaciones for {exp.numero}")
        print(f"  Encabezado: {archivo.encabezado.numero}")
        print(f"  Total actuaciones: {len(archivo.actuaciones)}")

        # If there are actuaciones, validate structure
        if archivo.actuaciones:
            act = archivo.actuaciones[0]
            assert act.fecha
            assert act.tipo
            print(f"  First actuacion: {act.fecha} - {act.tipo}")


class TestPlaywrightScraperAdapterSinCredenciales:
    """Tests that don't require credentials (initialization, error handling)."""

    def test_initialization_with_defaults(self, pjn_login_url: str):
        """Test adapter initialization with default settings."""
        adapter = PlaywrightScraperAdapter(login_url=pjn_login_url)

        assert adapter._login_url == pjn_login_url
        assert adapter._settings is not None
        assert adapter._session_file is not None

    def test_initialization_with_custom_session_file(
        self,
        test_settings: Settings,
        pjn_login_url: str,
        tmp_path,
    ):
        """Test adapter initialization with custom session file."""
        custom_session = tmp_path / "custom_session.json"

        adapter = PlaywrightScraperAdapter(
            login_url=pjn_login_url,
            session_file=custom_session,
            settings=test_settings,
        )

        assert adapter._session_file == custom_session
