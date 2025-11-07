"""WebSocket para progreso de extracción masiva en tiempo real."""
from __future__ import annotations

import asyncio
import logging

from fastapi import WebSocket, WebSocketDisconnect

from infrastructure.services.gestor_sesiones_service import get_gestor_sesiones

logger = logging.getLogger(__name__)


async def websocket_progreso(websocket: WebSocket, session_id: str):
    """WebSocket para recibir actualizaciones de progreso en tiempo real.

    Este handler:
    1. Acepta la conexión WebSocket
    2. Verifica que la sesión existe
    3. Registra el WebSocket en el gestor de sesiones
    4. Envía el estado actual inmediatamente
    5. Mantiene la conexión abierta con ping/pong
    6. Envía estado final cuando la extracción termina
    7. Desregistra el WebSocket al cerrar

    Args:
        websocket: Conexión WebSocket
        session_id: ID de la sesión a monitorear
    """
    # Aceptar conexión
    await websocket.accept()
    logger.info(f"WebSocket conectado para sesión {session_id}")

    # Obtener gestor de sesiones
    gestor = get_gestor_sesiones()

    # Verificar que la sesión existe
    sesion = await gestor.obtener_sesion(session_id)
    if not sesion:
        await websocket.send_json({"error": "Sesión no encontrada"})
        await websocket.close()
        logger.warning(f"WebSocket: Sesión no encontrada {session_id}")
        return

    # Registrar WebSocket
    await gestor.registrar_websocket(session_id, websocket)

    try:
        # Enviar estado actual inmediatamente
        await websocket.send_json(
            {
                "session_id": sesion["session_id"],
                "estado": sesion["estado"],
                "fase": sesion["fase"],
                "progreso_actual": sesion["progreso_actual"],
                "progreso_total": sesion["progreso_total"],
                "porcentaje": sesion["porcentaje"],
                "mensaje": sesion["mensaje"],
                "errores": sesion["errores"],
            }
        )

        # Mantener conexión abierta
        while True:
            # Esperar mensajes del cliente (ping/pong para keep-alive)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)

                # Echo del mensaje recibido (para keep-alive)
                if data == "ping":
                    await websocket.send_text("pong")
                    logger.debug(f"WebSocket ping/pong para sesión {session_id}")

            except asyncio.TimeoutError:
                # Timeout normal, continuar
                pass

            # Verificar si la sesión terminó
            sesion_actual = await gestor.obtener_sesion(session_id)
            if sesion_actual and sesion_actual["estado"] in [
                "completado",
                "cancelado",
                "error",
            ]:
                # Enviar estado final
                await websocket.send_json(
                    {
                        "session_id": sesion_actual["session_id"],
                        "estado": sesion_actual["estado"],
                        "mensaje": sesion_actual["mensaje"],
                    }
                )
                logger.info(
                    f"WebSocket: Sesión {session_id} terminada con estado {sesion_actual['estado']}"
                )
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado para sesión {session_id}")

    except Exception as e:
        logger.error(f"Error en WebSocket {session_id}: {e}", exc_info=True)

    finally:
        # Desregistrar WebSocket
        await gestor.desregistrar_websocket(session_id, websocket)
        logger.info(f"WebSocket desregistrado para sesión {session_id}")
