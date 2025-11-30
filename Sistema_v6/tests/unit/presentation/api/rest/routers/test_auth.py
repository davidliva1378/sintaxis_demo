"""
Tests unitarios para el router de Autenticación.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from presentation.api.rest.main import app
from presentation.api.rest.routers.auth import router, get_db
from infrastructure.persistence.database import Usuario

client = TestClient(app)

@pytest.mark.unit
class TestAuthRouter:
    """Tests para endpoints de autenticación."""

    @patch("presentation.api.rest.routers.auth.get_password_hash")
    def test_register_user_success(self, mock_hash):
        """Debe registrar un usuario correctamente."""
        mock_hash.return_value = "hashed_secret"
        
        # Mock DB session
        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None # No existing user
        
        # Override dependency
        app.dependency_overrides[get_db] = lambda: mock_db
        
        user_data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "secretpassword"
        }
        
        # Configure the returned user object to match schema
        # Since the router creates a new Usuario instance, we can't easily mock its attributes 
        # unless we mock the Usuario constructor or the db.refresh call.
        # However, db.refresh updates the instance with DB values.
        # We can mock db.refresh to set the ID and timestamps on the object passed to it.
        def side_effect_refresh(obj):
            obj.id = 1
            obj.is_active = True
            obj.is_superuser = False
            obj.created_at = "2024-01-01T00:00:00"
            obj.updated_at = "2024-01-01T00:00:00"
            # Set underlying fields for property has_pjn_credentials
            obj.pjn_usuario_encrypted = None
            obj.pjn_password_encrypted = None
        
        mock_db.refresh.side_effect = side_effect_refresh
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        # Reset dependency
        app.dependency_overrides = {}
        
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "new@example.com"
        assert data["id"] == 1
        
        # Verify DB calls
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_register_user_existing_username(self):
        """Debe fallar si el username ya existe."""
        mock_db = MagicMock()
        # First query (username check) returns a user
        mock_db.query.return_value.filter.return_value.first.return_value = Usuario(username="existing")
        
        app.dependency_overrides[get_db] = lambda: mock_db
        
        user_data = {
            "username": "existing",
            "email": "new@example.com",
            "password": "secretpassword"  # Valid length > 8
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        
        app.dependency_overrides = {}
        
        assert response.status_code == 400
        assert "nombre de usuario ya está registrado" in response.json()["detail"]

    @patch("presentation.api.rest.routers.auth.verify_password")
    @patch("presentation.api.rest.routers.auth.create_access_token")
    def test_login_success(self, mock_create_token, mock_verify):
        """Debe loguear correctamente."""
        mock_verify.return_value = True
        mock_create_token.return_value = "fake_token"
        
        mock_db = MagicMock()
        mock_user = Usuario(username="testuser", hashed_password="hashed", is_active=True)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        app.dependency_overrides[get_db] = lambda: mock_db
        
        form_data = {
            "username": "testuser",
            "password": "password"
        }
        
        response = client.post("/api/v1/auth/login", data=form_data)
        
        app.dependency_overrides = {}
        
        assert response.status_code == 200
        data = response.json()
        assert data["access_token"] == "fake_token"
        assert data["token_type"] == "bearer"

    @patch("presentation.api.rest.routers.auth.decode_access_token")
    def test_get_me(self, mock_decode):
        """Debe obtener usuario actual."""
        mock_decode.return_value = {"sub": "testuser"}
        
        mock_db = MagicMock()
        mock_user = Usuario(
            id=1,
            username="testuser", 
            email="test@example.com", 
            is_active=True,
            is_superuser=False,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00",
            pjn_usuario_encrypted=None,
            pjn_password_encrypted=None
        )
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        app.dependency_overrides[get_db] = lambda: mock_db
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.get("/api/v1/auth/me", headers=headers)
        
        app.dependency_overrides = {}
        
        assert response.status_code == 200
        data = response.json()
        assert data["username"] == "testuser"

    @patch("presentation.api.rest.routers.auth.decode_access_token")
    def test_update_pjn_credentials(self, mock_decode):
        """Debe actualizar credenciales PJN."""
        mock_decode.return_value = {"sub": "testuser"}
        
        mock_db = MagicMock()
        mock_user = Usuario(
            id=1,
            username="testuser", 
            is_active=True,
            email="test@example.com",
            is_superuser=False,
            created_at="2024-01-01T00:00:00",
            updated_at="2024-01-01T00:00:00"
        )
        mock_user.pjn_usuario_encrypted = None
        mock_user.pjn_password_encrypted = None
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user
        
        app.dependency_overrides[get_db] = lambda: mock_db
        
        creds_data = {
            "pjn_usuario_encrypted": "encrypted_user",
            "pjn_password_encrypted": "encrypted_pass"
        }
        
        headers = {"Authorization": "Bearer valid_token"}
        response = client.put("/api/v1/auth/credentials", json=creds_data, headers=headers)
        
        app.dependency_overrides = {}
        
        assert response.status_code == 200
        assert mock_user.pjn_usuario_encrypted == "encrypted_user"
        mock_db.commit.assert_called_once()
