"""WebSocket Manager para Monitoreo (Infrastructure Layer)."""
from __future__ import annotations

import logging
from typing import Dict, List, Any
from fastapi import WebSocket

logger = logging.getLogger(__name__)

class MonitoreoWebSocketManager:
    """Gestor de conexiones WebSocket para monitoreo."""

    def __init__(self):
        # Mapa: usuario_id -> Lista de WebSockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, usuario_id: int):
        """Conecta un nuevo cliente."""
        await websocket.accept()
        if usuario_id not in self.active_connections:
            self.active_connections[usuario_id] = []
        self.active_connections[usuario_id].append(websocket)
        logger.info(f"Cliente WS conectado: usuario_id={usuario_id}")

    def disconnect(self, websocket: WebSocket, usuario_id: int):
        """Desconecta un cliente."""
        if usuario_id in self.active_connections:
            if websocket in self.active_connections[usuario_id]:
                self.active_connections[usuario_id].remove(websocket)
            if not self.active_connections[usuario_id]:
                del self.active_connections[usuario_id]
        logger.info(f"Cliente WS desconectado: usuario_id={usuario_id}")

    async def broadcast(self, message: dict, usuario_id: int | None = None):
        """Envía un mensaje a los clientes conectados.
        
        Args:
            message: Mensaje JSON a enviar
            usuario_id: ID del usuario específico (None para todos - admin broadcast)
        """
        if usuario_id is not None:
            # Enviar solo a un usuario
            if usuario_id in self.active_connections:
                for connection in self.active_connections[usuario_id]:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.warning(f"Error enviando WS a usuario {usuario_id}: {e}")
        else:
            # Broadcast a todos
            for uid, connections in self.active_connections.items():
                for connection in connections:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        logger.warning(f"Error enviando WS broadcast a {uid}: {e}")
