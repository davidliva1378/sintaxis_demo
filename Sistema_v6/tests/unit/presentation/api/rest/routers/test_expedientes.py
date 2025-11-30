"""
Tests unitarios para el router de Expedientes.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from presentation.api.rest.main import app
from presentation.api.rest.routers.expedientes import router
from infrastructure.exceptions import PJNError

client = TestClient(app)

@pytest.mark.unit
class TestExpedientesRouter:
    """Tests para endpoints de expedientes."""

    @classmethod
    def setup_class(cls):
        from presentation.api.rest.rate_limiter import limiter
        limiter.enabled = False

    @patch("presentation.api.rest.routers.expedientes.get_container")
    def test_listar_expedientes_success(self, mock_get_container):
        """Debe listar expedientes correctamente."""
        # Setup mock container
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container
        
        # Setup mock repo
        mock_repo = AsyncMock()
        mock_exp1 = Mock(
            numero="EXP-001", 
            dependencia="Juzgado 1", 
            caratula="Caratula 1", 
            situacion="Despacho", 
            ultima_actuacion=None
        )
        mock_exp2 = Mock(
            numero="EXP-002", 
            dependencia="Juzgado 2", 
            caratula="Caratula 2", 
            situacion="Fallo", 
            ultima_actuacion=None
        )
        mock_repo.obtener_todos.return_value = [mock_exp1, mock_exp2]
        
        mock_container.expediente_repo = mock_repo
        
        response = client.get("/api/v1/expedientes?pagina=1&por_pagina=10")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 2
        assert len(data["expedientes"]) == 2
        assert data["expedientes"][0]["numero"] == "EXP-001"

    @patch("presentation.api.rest.routers.expedientes.get_container")
    def test_obtener_expediente_found(self, mock_get_container):
        """Debe obtener un expediente por número."""
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container
        
        mock_repo = AsyncMock()
        mock_exp = Mock(
            numero="EXP-001", 
            dependencia="Juzgado 1", 
            caratula="Caratula 1", 
            situacion="Despacho", 
            ultima_actuacion=None
        )
        mock_repo.obtener_por_numero.return_value = mock_exp
        
        mock_container.expediente_repo = mock_repo
        
        response = client.get("/api/v1/expedientes/EXP-001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["numero"] == "EXP-001"

    @patch("presentation.api.rest.routers.expedientes.get_container")
    def test_obtener_expediente_not_found(self, mock_get_container):
        """Debe retornar 404 si no existe."""
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container
        
        mock_repo = AsyncMock()
        mock_repo.obtener_por_numero.return_value = None
        
        mock_container.expediente_repo = mock_repo
        
        response = client.get("/api/v1/expedientes/NON-EXISTENT")
        
        assert response.status_code == 404

    @patch("presentation.api.rest.routers.expedientes.get_container")
    def test_extraer_expedientes_success(self, mock_get_container):
        """Debe iniciar extracción correctamente."""
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container
        
        # Mock use case
        mock_use_case = Mock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_result.value.total = 10
        mock_result.value.archivo_guardado = "/tmp/file.json"
        mock_result.error = None
        
        mock_use_case.execute = AsyncMock(return_value=mock_result)
        
        # Assign method mock directly
        mock_container.extraer_expedientes_use_case = Mock(return_value=mock_use_case)
        
        request_data = {
            "usuario": "user",
            "contrasena": "pass",
            "headless": True,
            "guardar_en": "/tmp/test.json"
        }
        
        response = client.post("/api/v1/expedientes/extraer", json=request_data)
        
        if response.status_code != 200:
            assert False, f"Status: {response.status_code}, Response: {response.text}"
            
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["total"] == 10
        
        # Verify use case was called
        mock_use_case.execute.assert_called_once()
        
        # Verify container was instantiated (called)
        mock_get_container.assert_called()

    @patch("presentation.api.rest.routers.expedientes.get_container")
    def test_extraer_expedientes_pjn_error(self, mock_get_container):
        """Debe manejar errores del PJN."""
        mock_container = MagicMock()
        mock_get_container.return_value = mock_container
        
        mock_use_case = Mock()
        mock_use_case.execute = AsyncMock(side_effect=PJNError("Error de conexión"))
        
        # Assign method mock directly
        mock_container.extraer_expedientes_use_case = Mock(return_value=mock_use_case)
        
        request_data = {
            "usuario": "user",
            "contrasena": "pass",
            "guardar_en": "/tmp/test.json"
        }
        
        response = client.post("/api/v1/expedientes/extraer", json=request_data)
        
        if response.status_code != 200:
            assert False, f"Status: {response.status_code}, Response: {response.text}"
            
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "Error de conexión" in data["error"]


