"""Servicio para gestión de sesiones de extracción masiva."""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Set

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class GestorSesiones:
    """Gestor de sesiones de extracción activas.

    Maneja el ciclo de vida de las sesiones de extracción masiva,
    incluyendo:
    - Creación y configuración de sesiones
    - Actualización de progreso
    - Broadcast de actualizaciones via WebSocket
    - Finalización y cleanup

    Attributes:
        sesiones: Dict de sesiones activas (session_id -> datos)
        websockets: Dict de WebSockets conectados (session_id -> Set[WebSocket])
        lock: Lock para acceso thread-safe
    """

    def __init__(self):
        """Inicializa el gestor de sesiones."""
        self.sesiones: Dict[str, Dict[str, Any]] = {}
        self.websockets: Dict[str, Set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def crear_sesion(
        self, session_id: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Crear una nueva sesión de extracción.

        Args:
            session_id: ID único de la sesión
            config: Configuración de la extracción

        Returns:
            Dict con datos iniciales de la sesión
        """
        async with self.lock:
            sesion = {
                "session_id": session_id,
                "config": config,
                "estado": "iniciando",
                "fase": "configuracion",
                "progreso_actual": 0,
                "progreso_total": 0,
                "porcentaje": 0.0,
                "mensaje": "Iniciando extracción...",
                "errores": 0,
                "tiempo_inicio": datetime.now().isoformat(),
                "tiempo_fin": None,
                "resultados": None,
                "archivos": [],
                "extractor": None,
                "task": None,
            }
            self.sesiones[session_id] = sesion
            self.websockets[session_id] = set()

            logger.info(f"Sesión creada: {session_id}")
            return sesion

    async def actualizar_progreso(self, session_id: str, **kwargs):
        """Actualizar el progreso de una sesión.

        Args:
            session_id: ID de la sesión
            **kwargs: Campos a actualizar
        """
        async with self.lock:
            if session_id not in self.sesiones:
                logger.warning(f"Sesión no encontrada: {session_id}")
                return

            # Actualizar campos
            self.sesiones[session_id].update(kwargs)

            # Calcular tiempo transcurrido
            inicio = datetime.fromisoformat(self.sesiones[session_id]["tiempo_inicio"])
            transcurrido = (datetime.now() - inicio).total_seconds()
            self.sesiones[session_id]["tiempo_transcurrido"] = transcurrido

            # Enviar actualización por WebSocket
            await self._broadcast(session_id, self.sesiones[session_id])

    async def obtener_sesion(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Obtener información de una sesión.

        Args:
            session_id: ID de la sesión

        Returns:
            Dict con datos de la sesión o None si no existe
        """
        async with self.lock:
            return self.sesiones.get(session_id)

    async def finalizar_sesion(self, session_id: str, resultados: Dict[str, Any]):
        """Finalizar una sesión con resultados.

        Args:
            session_id: ID de la sesión
            resultados: Resultados de la extracción
        """
        async with self.lock:
            if session_id not in self.sesiones:
                logger.warning(f"Sesión no encontrada al finalizar: {session_id}")
                return

            self.sesiones[session_id].update(
                {
                    "estado": "completado",
                    "tiempo_fin": datetime.now().isoformat(),
                    "resultados": resultados,
                }
            )

            # Broadcast estado final
            await self._broadcast(session_id, self.sesiones[session_id])

            logger.info(f"Sesión finalizada: {session_id}")

    async def marcar_error(self, session_id: str, error: str):
        """Marcar una sesión como error.

        Args:
            session_id: ID de la sesión
            error: Mensaje de error
        """
        async with self.lock:
            if session_id not in self.sesiones:
                logger.warning(f"Sesión no encontrada al marcar error: {session_id}")
                return

            self.sesiones[session_id].update(
                {
                    "estado": "error",
                    "mensaje": f"Error: {error}",
                    "tiempo_fin": datetime.now().isoformat(),
                }
            )

            # Broadcast estado de error
            await self._broadcast(session_id, self.sesiones[session_id])

            logger.error(f"Sesión con error: {session_id} - {error}")

    async def registrar_websocket(self, session_id: str, websocket: WebSocket):
        """Registrar un WebSocket para una sesión.

        Args:
            session_id: ID de la sesión
            websocket: Conexión WebSocket
        """
        async with self.lock:
            if session_id not in self.websockets:
                self.websockets[session_id] = set()
            self.websockets[session_id].add(websocket)

            logger.debug(
                f"WebSocket registrado para sesión {session_id}. "
                f"Total: {len(self.websockets[session_id])}"
            )

    async def desregistrar_websocket(self, session_id: str, websocket: WebSocket):
        """Desregistrar un WebSocket.

        Args:
            session_id: ID de la sesión
            websocket: Conexión WebSocket
        """
        async with self.lock:
            if session_id in self.websockets:
                self.websockets[session_id].discard(websocket)

                logger.debug(
                    f"WebSocket desregistrado de sesión {session_id}. "
                    f"Restantes: {len(self.websockets[session_id])}"
                )

                # Limpiar set vacío
                if not self.websockets[session_id]:
                    del self.websockets[session_id]

    async def _broadcast(self, session_id: str, data: Dict[str, Any]):
        """Enviar datos a todos los WebSockets de una sesión.

        Args:
            session_id: ID de la sesión
            data: Datos a enviar
        """
        if session_id not in self.websockets:
            return

        # Crear copia para evitar problemas con modificaciones concurrentes
        websockets_copy = self.websockets[session_id].copy()

        if not websockets_copy:
            return

        # Filtrar datos para enviar solo lo necesario
        mensaje = {
            "session_id": data["session_id"],
            "estado": data["estado"],
            "fase": data["fase"],
            "progreso_actual": data["progreso_actual"],
            "progreso_total": data["progreso_total"],
            "porcentaje": data["porcentaje"],
            "mensaje": data["mensaje"],
            "errores": data["errores"],
            "tiempo_transcurrido": data.get("tiempo_transcurrido", 0),
        }

        # Enviar a todos los WebSockets conectados
        for websocket in websockets_copy:
            try:
                await websocket.send_json(mensaje)
            except Exception as e:
                logger.error(
                    f"Error enviando a WebSocket en sesión {session_id}: {e}"
                )
                # Desregistrar WebSocket con error
                await self.desregistrar_websocket(session_id, websocket)

    async def limpiar_sesion(self, session_id: str):
        """Limpiar una sesión del gestor.

        Args:
            session_id: ID de la sesión
        """
        async with self.lock:
            # Cerrar todos los WebSockets
            if session_id in self.websockets:
                websockets_copy = self.websockets[session_id].copy()
                for ws in websockets_copy:
                    try:
                        await ws.close()
                    except Exception:
                        pass
                del self.websockets[session_id]

            # Eliminar sesión
            if session_id in self.sesiones:
                del self.sesiones[session_id]

            logger.info(f"Sesión limpiada: {session_id}")


# Instancia singleton
_gestor: Optional[GestorSesiones] = None


def get_gestor_sesiones() -> GestorSesiones:
    """Obtener instancia singleton del gestor de sesiones.

    Returns:
        Instancia de GestorSesiones
    """
    global _gestor
    if _gestor is None:
        _gestor = GestorSesiones()
        logger.info("GestorSesiones inicializado")
    return _gestor


def reset_gestor_sesiones():
    """Resetear el gestor de sesiones (útil para testing).

    CUIDADO: Esto cerrará todas las sesiones activas.
    """
    global _gestor
    _gestor = None
    logger.info("GestorSesiones reseteado")
