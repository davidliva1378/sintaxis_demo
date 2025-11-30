"""WebSocket Manager para Monitoreo."""
from __future__ import annotations

import logging
from fastapi import WebSocket, WebSocketDisconnect
from infrastructure.di_container import get_container

logger = logging.getLogger(__name__)

async def websocket_monitoreo_endpoint(websocket: WebSocket, usuario_id: int):
    """Endpoint WebSocket para monitoreo."""
    # Obtener manager del contenedor
    manager = get_container().monitoreo_ws_manager
    
    await manager.connect(websocket, usuario_id)
    try:
        while True:
            # Mantener conexión viva y escuchar comandos simples (ping)
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, usuario_id)
    except Exception as e:
        logger.error(f"Error en WS monitoreo: {e}")
        manager.disconnect(websocket, usuario_id)
