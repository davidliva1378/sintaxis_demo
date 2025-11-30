"""
Tests unitarios para el router de Health Check.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from presentation.api.rest.main import app
from presentation.api.rest.routers.health import router

client = TestClient(app)

@pytest.mark.unit
class TestHealthRouter:
    """Tests para endpoints de health check."""

    @patch("presentation.api.rest.routers.health.get_settings")
    @patch("presentation.api.rest.routers.health.test_mysql_connection")
    @patch("presentation.api.rest.routers.health.get_mysql_pool_status")
    @patch("presentation.api.rest.routers.health.shutil.disk_usage")
    @patch("presentation.api.rest.routers.health.psutil.virtual_memory")
    def test_health_check_healthy(
        self, 
        mock_memory, 
        mock_disk, 
        mock_pool, 
        mock_mysql, 
        mock_settings
    ):
        """Debe retornar estado healthy cuando todo está bien."""
        # Setup mocks
        mock_settings_instance = Mock()
        mock_settings_instance.storage.base_path.exists.return_value = True
        mock_settings.return_value = mock_settings_instance
        
        mock_mysql.return_value = True
        mock_pool.return_value = {"active": 1}
        
        mock_disk_usage = Mock()
        mock_disk_usage.free = 100 * (1024**3)
        mock_disk_usage.total = 500 * (1024**3)
        mock_disk_usage.used = 400 * (1024**3)
        mock_disk.return_value = mock_disk_usage
        
        mock_mem = Mock()
        mock_mem.available = 8 * (1024**3)
        mock_mem.percent = 50.0
        mock_memory.return_value = mock_mem
        
        # Execute request
        response = client.get("/api/v1/health")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["issues"] is None
        assert data["checks"]["database"]["mysql_connected"] is True

    @patch("presentation.api.rest.routers.health.get_settings")
    @patch("presentation.api.rest.routers.health.test_mysql_connection")
    @patch("presentation.api.rest.routers.health.get_mysql_pool_status")
    @patch("presentation.api.rest.routers.health.shutil.disk_usage")
    @patch("presentation.api.rest.routers.health.psutil.virtual_memory")
    def test_health_check_degraded(
        self, 
        mock_memory, 
        mock_disk, 
        mock_pool, 
        mock_mysql, 
        mock_settings
    ):
        """Debe retornar estado degraded cuando hay problemas."""
        # Setup mocks with issues
        mock_settings_instance = Mock()
        mock_settings_instance.storage.base_path.exists.return_value = False
        mock_settings.return_value = mock_settings_instance
        
        mock_mysql.return_value = False
        
        # Configure disk mock to return an object with integer attributes
        mock_disk_usage = Mock()
        mock_disk_usage.free = 100
        mock_disk_usage.total = 1000
        mock_disk_usage.used = 900
        mock_disk.return_value = mock_disk_usage
        
        # Configure memory mock
        mock_mem = Mock()
        mock_mem.percent = 95.0
        mock_mem.available = 100 # Need this for calculation
        mock_memory.return_value = mock_mem
        
        # Execute request
        response = client.get("/api/v1/health")
        
        # Verify
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "degraded"
        assert "base_path_missing" in data["issues"]
        assert "mysql_unavailable" in data["issues"]
        assert "memory_critical" in data["issues"]

    def test_liveness_check(self):
        """Debe retornar alive."""
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200
        assert response.json() == {"alive": True}

    @patch("presentation.api.rest.routers.health.get_settings")
    @patch("presentation.api.rest.routers.health.test_mysql_connection")
    def test_readiness_check(self, mock_mysql, mock_settings):
        """Debe verificar si está listo."""
        mock_settings_instance = Mock()
        mock_settings_instance.storage.base_path.exists.return_value = True
        mock_settings.return_value = mock_settings_instance
        
        mock_mysql.return_value = True
        
        response = client.get("/api/v1/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert data["checks"]["mysql_connected"] is True
