"""
Token Manager para autenticación MCP.

Gestiona tokens Bearer para acceso remoto al servidor MCP SSE.
Almacena tokens en archivo JSON con hash seguro.
"""

import json
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class Token:
    """Representa un token de acceso MCP."""

    token_id: str
    name: str
    token_hash: str
    created_at: str
    expires_at: Optional[str]
    last_used: Optional[str]
    is_active: bool
    permissions: List[str]

    def is_expired(self) -> bool:
        """Verifica si el token ha expirado."""
        if not self.expires_at:
            return False
        return datetime.fromisoformat(self.expires_at) < datetime.now()

    def is_valid(self) -> bool:
        """Verifica si el token es válido para uso."""
        return self.is_active and not self.is_expired()


class TokenManager:
    """
    Gestor de tokens para autenticación MCP.

    Características:
    - Generación segura de tokens con secrets
    - Almacenamiento con hash SHA-256
    - Soporte para expiración
    - Permisos por token
    - Registro de último uso
    """

    DEFAULT_TOKEN_LENGTH = 32
    TOKEN_PREFIX = "mcp_"

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Inicializa el gestor de tokens.

        Args:
            storage_path: Ruta al archivo de tokens. Si no se especifica,
                         usa ~/.sintaxis_mcp/tokens.json
        """
        if storage_path is None:
            storage_path = Path.home() / ".sintaxis_mcp" / "tokens.json"

        self.storage_path = Path(storage_path)
        self._ensure_storage()
        self._tokens: Dict[str, Token] = {}
        self._load_tokens()

    def _ensure_storage(self) -> None:
        """Asegura que el directorio de almacenamiento existe."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text("{}")
            # Permisos restrictivos (solo owner)
            self.storage_path.chmod(0o600)

    def _load_tokens(self) -> None:
        """Carga tokens desde el archivo."""
        try:
            data = json.loads(self.storage_path.read_text())
            self._tokens = {
                token_id: Token(**token_data)
                for token_id, token_data in data.items()
            }
            logger.info(f"Cargados {len(self._tokens)} tokens")
        except Exception as e:
            logger.error(f"Error cargando tokens: {e}")
            self._tokens = {}

    def _save_tokens(self) -> None:
        """Guarda tokens al archivo."""
        try:
            data = {
                token_id: asdict(token)
                for token_id, token in self._tokens.items()
            }
            self.storage_path.write_text(json.dumps(data, indent=2))
            logger.debug("Tokens guardados")
        except Exception as e:
            logger.error(f"Error guardando tokens: {e}")
            raise

    @staticmethod
    def _hash_token(token: str) -> str:
        """Genera hash SHA-256 del token."""
        return hashlib.sha256(token.encode()).hexdigest()

    def generate_token(
        self,
        name: str,
        expires_in_days: Optional[int] = None,
        permissions: Optional[List[str]] = None
    ) -> tuple[str, Token]:
        """
        Genera un nuevo token de acceso.

        Args:
            name: Nombre descriptivo del token (ej: "claude-desktop", "chatgpt")
            expires_in_days: Días hasta expiración. None = sin expiración
            permissions: Lista de permisos. None = todos

        Returns:
            Tupla (token_plaintext, Token object)

        Note:
            El token en texto plano solo se devuelve una vez.
            Debe guardarse de forma segura por el usuario.
        """
        # Generar token único
        token_id = secrets.token_hex(8)
        token_plaintext = f"{self.TOKEN_PREFIX}{secrets.token_urlsafe(self.DEFAULT_TOKEN_LENGTH)}"
        token_hash = self._hash_token(token_plaintext)

        # Calcular expiración
        expires_at = None
        if expires_in_days:
            expires_at = (datetime.now() + timedelta(days=expires_in_days)).isoformat()

        # Crear objeto token
        token = Token(
            token_id=token_id,
            name=name,
            token_hash=token_hash,
            created_at=datetime.now().isoformat(),
            expires_at=expires_at,
            last_used=None,
            is_active=True,
            permissions=permissions or ["*"]
        )

        self._tokens[token_id] = token
        self._save_tokens()

        logger.info(f"Token generado: {name} (ID: {token_id})")
        return token_plaintext, token

    def validate_token(self, token_plaintext: str) -> Optional[Token]:
        """
        Valida un token y actualiza último uso.

        Args:
            token_plaintext: Token en texto plano

        Returns:
            Token object si es válido, None si no
        """
        if not token_plaintext:
            return None

        # Remover prefijo "Bearer " si existe
        if token_plaintext.startswith("Bearer "):
            token_plaintext = token_plaintext[7:]

        token_hash = self._hash_token(token_plaintext)

        for token in self._tokens.values():
            if token.token_hash == token_hash:
                if token.is_valid():
                    # Actualizar último uso
                    token.last_used = datetime.now().isoformat()
                    self._save_tokens()
                    return token
                else:
                    logger.warning(f"Token inválido o expirado: {token.name}")
                    return None

        logger.warning("Token no encontrado")
        return None

    def revoke_token(self, token_id: str) -> bool:
        """
        Revoca un token por su ID.

        Args:
            token_id: ID del token a revocar

        Returns:
            True si se revocó, False si no existía
        """
        if token_id in self._tokens:
            self._tokens[token_id].is_active = False
            self._save_tokens()
            logger.info(f"Token revocado: {token_id}")
            return True
        return False

    def delete_token(self, token_id: str) -> bool:
        """
        Elimina un token permanentemente.

        Args:
            token_id: ID del token a eliminar

        Returns:
            True si se eliminó, False si no existía
        """
        if token_id in self._tokens:
            del self._tokens[token_id]
            self._save_tokens()
            logger.info(f"Token eliminado: {token_id}")
            return True
        return False

    def list_tokens(self, include_inactive: bool = False) -> List[Token]:
        """
        Lista todos los tokens.

        Args:
            include_inactive: Incluir tokens revocados

        Returns:
            Lista de tokens
        """
        tokens = list(self._tokens.values())
        if not include_inactive:
            tokens = [t for t in tokens if t.is_active]
        return tokens

    def get_token_info(self, token_id: str) -> Optional[Token]:
        """
        Obtiene información de un token por ID.

        Args:
            token_id: ID del token

        Returns:
            Token object o None
        """
        return self._tokens.get(token_id)

    def has_permission(self, token: Token, permission: str) -> bool:
        """
        Verifica si un token tiene un permiso específico.

        Args:
            token: Token a verificar
            permission: Permiso requerido (ej: "tools:execute", "resources:read")

        Returns:
            True si tiene permiso
        """
        if "*" in token.permissions:
            return True
        return permission in token.permissions

    def cleanup_expired(self) -> int:
        """
        Elimina tokens expirados.

        Returns:
            Número de tokens eliminados
        """
        expired = [
            token_id for token_id, token in self._tokens.items()
            if token.is_expired()
        ]
        for token_id in expired:
            del self._tokens[token_id]

        if expired:
            self._save_tokens()
            logger.info(f"Eliminados {len(expired)} tokens expirados")

        return len(expired)

    def get_stats(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas de tokens.

        Returns:
            Dict con estadísticas
        """
        tokens = list(self._tokens.values())
        active = [t for t in tokens if t.is_active]
        expired = [t for t in tokens if t.is_expired()]

        return {
            "total": len(tokens),
            "active": len(active),
            "inactive": len(tokens) - len(active),
            "expired": len(expired),
            "storage_path": str(self.storage_path)
        }
