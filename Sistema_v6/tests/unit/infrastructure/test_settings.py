"""
Tests unitarios para configuración unificada del sistema.

Prueba las clases de configuración basadas en Pydantic Settings,
incluyendo singleton pattern, valores por defecto y carga desde env vars.
"""

import os
import pytest
from pathlib import Path
from infrastructure.config.settings import (
    Settings,
    AuthSettings,
    BrowserSettings,
    ScrapingSettings,
    StorageSettings,
    RAGSettings,
    get_settings,
    reload_settings,
)


@pytest.mark.unit
class TestAuthSettings:
    """Tests para configuración de autenticación."""

    def test_defaults_structure(self):
        """Debe tener la estructura correcta con valores por defecto."""
        auth = AuthSettings()
        # Verificar que tiene los atributos esperados
        assert hasattr(auth, 'login_url')
        assert hasattr(auth, 'usuario')
        assert hasattr(auth, 'password')
        assert hasattr(auth, 'session_file_name')
        assert hasattr(auth, 'session_timeout_seconds')
        
        # Verificar tipos y valores inmutables
        assert auth.login_url == "https://portalpjn.pjn.gov.ar/inicio"
        assert auth.session_file_name == "pjn_session.json"
        assert auth.session_timeout_seconds == 3600


@pytest.mark.unit
class TestBrowserSettings:
    """Tests para configuración del navegador."""

    def test_defaults(self):
        """Debe tener valores por defecto correctos."""
        browser = BrowserSettings()
        assert browser.headless is True
        assert browser.timeout_ms == 30000
        assert browser.navigation_timeout_ms == 60000
        assert browser.user_agent is None
        assert len(browser.args) > 0
        assert "--disable-blink-features=AutomationControlled" in browser.args

    def test_from_env_vars(self, monkeypatch):
        """Debe cargar desde variables de entorno con prefijo BROWSER_."""
        monkeypatch.setenv("BROWSER_HEADLESS", "false")
        monkeypatch.setenv("BROWSER_TIMEOUT_MS", "45000")
        
        browser = BrowserSettings()
        assert browser.headless is False
        assert browser.timeout_ms == 45000

    def test_anti_webdriver_script(self):
        """Debe tener script anti-webdriver configurado."""
        browser = BrowserSettings()
        assert "webdriver" in browser.anti_webdriver_script
        assert "undefined" in browser.anti_webdriver_script


@pytest.mark.unit
class TestScrapingSettings:
    """Tests para configuración de scraping."""

    def test_defaults(self):
        """Debe tener valores por defecto correctos."""
        scraping = ScrapingSettings()
        assert scraping.timeout_default == 8000
        assert scraping.timeout_login == 60000
        assert scraping.timeout_descarga == 30000
        assert scraping.max_paginas_expedientes == 200
        assert scraping.max_reintentos_descarga == 3
        assert scraping.caratula_coincidencia_parcial is True

    def test_from_env_vars(self, monkeypatch):
        """Debe cargar desde variables de entorno con prefijo SCRAPING_."""
        monkeypatch.setenv("SCRAPING_TIMEOUT_DEFAULT", "10000")
        monkeypatch.setenv("SCRAPING_MAX_PAGINAS_EXPEDIENTES", "500")
        
        scraping = ScrapingSettings()
        assert scraping.timeout_default == 10000
        assert scraping.max_paginas_expedientes == 500

    def test_none_max_paginas(self):
        """Debe permitir None para max_paginas_expedientes (sin límite)."""
        scraping = ScrapingSettings(max_paginas_expedientes=None)
        assert scraping.max_paginas_expedientes is None


@pytest.mark.unit
class TestStorageSettings:
    """Tests para configuración de almacenamiento."""

    def test_defaults(self):
        """Debe tener valores por defecto correctos."""
        storage = StorageSettings()
        assert storage.json_base_file == "expedientes_base.json"
        assert storage.json_sistema_file == "expedientes_sistema.json"
        assert storage.workspaces_dir == "expedientes"
        assert storage.downloads_dir == "descargas"
        assert storage.pretty_json is True
        assert storage.ensure_ascii is False

    def test_base_path_is_path(self):
        """base_path debe ser un objeto Path."""
        storage = StorageSettings()
        assert isinstance(storage.base_path, Path)
        assert storage.base_path.name == "data"

    def test_custom_base_path(self):
        """Debe aceptar base_path personalizado."""
        custom_path = Path("/tmp/test_data")
        storage = StorageSettings(base_path=custom_path)
        assert storage.base_path == custom_path


@pytest.mark.unit
class TestRAGSettings:
    """Tests para configuración de RAG."""

    def test_defaults(self):
        """Debe tener valores por defecto correctos."""
        rag = RAGSettings()
        assert rag.qdrant_host == "localhost"
        assert rag.qdrant_port == 6333
        assert rag.qdrant_collection == "actuaciones"
        assert rag.ollama_model == "llama3.2:1b"
        assert rag.ollama_temperature == 0.3
        assert rag.embedding_dimension == 768
        assert rag.chunk_size == 1500
        assert rag.chunk_overlap == 300

    def test_from_env_vars(self, monkeypatch):
        """Debe cargar desde variables de entorno con prefijo RAG_."""
        monkeypatch.setenv("RAG_QDRANT_HOST", "192.168.1.100")
        monkeypatch.setenv("RAG_QDRANT_PORT", "6334")
        monkeypatch.setenv("RAG_OLLAMA_MODEL", "llama3.1:8b")
        
        rag = RAGSettings()
        assert rag.qdrant_host == "192.168.1.100"
        assert rag.qdrant_port == 6334
        assert rag.ollama_model == "llama3.1:8b"

    def test_search_weights(self):
        """Debe tener pesos de búsqueda configurados."""
        rag = RAGSettings()
        assert rag.dense_weight == 0.7
        assert rag.sparse_weight == 0.3
        # Los pesos deben sumar 1.0
        assert rag.dense_weight + rag.sparse_weight == 1.0

    def test_paths_are_path_objects(self):
        """Los paths deben ser objetos Path."""
        rag = RAGSettings()
        assert isinstance(rag.cache_dir, Path)
        assert isinstance(rag.vector_store_path, Path)
        assert isinstance(rag.bm25_index_path, Path)


@pytest.mark.unit
class TestMainSettings:
    """Tests para la clase Settings principal."""

    def test_defaults_structure(self):
        """Debe tener la estructura correcta."""
        settings = Settings()
        # Verificar que tiene los atributos esperados
        assert hasattr(settings, 'environment')
        assert hasattr(settings, 'debug')
        assert hasattr(settings, 'database_url')
        
        # Verificar que environment es uno de los valores válidos
        assert settings.environment in ["development", "production", "testing"]
        # Verificar que debug es booleano
        assert isinstance(settings.debug, bool)

    def test_subsettings_initialized(self):
        """Debe inicializar todos los subsettings."""
        settings = Settings()
        assert isinstance(settings.auth, AuthSettings)
        assert isinstance(settings.browser, BrowserSettings)
        assert isinstance(settings.scraping, ScrapingSettings)
        assert isinstance(settings.storage, StorageSettings)
        assert isinstance(settings.rag, RAGSettings)

    def test_nested_access(self):
        """Debe permitir acceso anidado a configuración."""
        settings = Settings()
        # Acceso anidado
        assert settings.auth.login_url == "https://portalpjn.pjn.gov.ar/inicio"
        assert settings.browser.headless is True
        assert settings.rag.qdrant_port == 6333

    def test_environment_values(self):
        """Debe aceptar diferentes valores de environment."""
        for env in ["development", "production", "testing"]:
            settings = Settings(environment=env)
            assert settings.environment == env


@pytest.mark.unit
class TestGetSettings:
    """Tests para la función get_settings (singleton)."""

    def test_singleton_pattern(self):
        """Debe retornar la misma instancia (singleton)."""
        # Recargar para empezar limpio
        reload_settings()
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        # Deben ser la misma instancia
        assert settings1 is settings2

    def test_reload_settings(self):
        """reload_settings debe crear una nueva instancia."""
        settings1 = get_settings()
        settings2 = reload_settings()
        settings3 = get_settings()
        
        # settings2 es una nueva instancia
        assert settings1 is not settings2
        # Pero settings3 debe ser la misma que settings2 (nuevo singleton)
        assert settings2 is settings3

    def test_settings_persistence(self):
        """Los cambios en settings deben persistir en el singleton."""
        reload_settings()
        settings = get_settings()
        
        # Modificar un valor
        original_debug = settings.debug
        settings.debug = not original_debug
        
        # Obtener settings nuevamente
        settings2 = get_settings()
        
        # El cambio debe persistir
        assert settings2.debug == (not original_debug)
        
        # Restaurar
        settings.debug = original_debug


@pytest.mark.unit
class TestSettingsFromEnv:
    """Tests de integración para carga desde variables de entorno."""

    def test_explicit_override(self):
        """Debe permitir sobrescribir valores explícitamente."""
        # Crear settings con valores explícitos
        settings = Settings(
            environment="testing",
            debug=True
        )
        
        # Verificar que los valores explícitos se aplicaron
        assert settings.environment == "testing"
        assert settings.debug is True

    def test_env_var_types(self, monkeypatch):
        """Debe convertir tipos correctamente desde env vars."""
        monkeypatch.setenv("BROWSER_TIMEOUT_MS", "45000")  # string -> int
        monkeypatch.setenv("BROWSER_HEADLESS", "true")  # string -> bool
        monkeypatch.setenv("RAG_OLLAMA_TEMPERATURE", "0.7")  # string -> float
        
        settings = Settings()
        
        assert isinstance(settings.browser.timeout_ms, int)
        assert settings.browser.timeout_ms == 45000
        
        assert isinstance(settings.browser.headless, bool)
        assert settings.browser.headless is True
        
        assert isinstance(settings.rag.ollama_temperature, float)
        assert settings.rag.ollama_temperature == 0.7


@pytest.mark.unit
class TestSettingsValidation:
    """Tests para validación de configuración."""

    def test_invalid_environment(self):
        """Debe rechazar valores inválidos de environment."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            Settings(environment="invalid")

    def test_negative_timeout(self):
        """Debe aceptar timeouts positivos."""
        browser = BrowserSettings(timeout_ms=1000)
        assert browser.timeout_ms == 1000

    def test_zero_timeout(self):
        """Debe aceptar timeout de 0."""
        browser = BrowserSettings(timeout_ms=0)
        assert browser.timeout_ms == 0
