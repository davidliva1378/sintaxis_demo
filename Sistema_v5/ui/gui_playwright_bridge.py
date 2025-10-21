"""Puente entre la GUI y Playwright para reutilizar sesiones autenticadas.

Este módulo inicializa :func:`obtener_pagina_autenticada` en un hilo de
segundo plano y expone utilidades síncronas que pueden ser utilizadas desde
la interfaz Tkinter. El objetivo es evitar bloqueos en la interfaz y
reutilizar la misma pestaña autenticada entre múltiples expedientes.
"""
from __future__ import annotations

import asyncio
import re
import threading
from dataclasses import dataclass, field
from typing import Any, Awaitable, Coroutine

from playwright.async_api import Page

from Sistema_v5.pjn.models import ExpedienteResumen
from Sistema_v5.pjn.scraping import obtener_pagina_autenticada
from Sistema_v5.pjn.scraping.expedientes import (
    buscar_expedientes,
    mostrar_y_elegir_expediente,
)
from Sistema_v5.pjn.utils.logging import get_logger
from urls_pjn import URL_CONSULTAS

logger = get_logger(__name__)


class PlaywrightBridgeError(RuntimeError):
    """Error base para problemas del puente Playwright."""


class PlaywrightSessionError(PlaywrightBridgeError):
    """Falla al iniciar o reutilizar la sesión de Playwright."""


class ExpedienteNotFoundError(PlaywrightBridgeError):
    """El expediente solicitado no pudo encontrarse en el portal."""


class ExpedienteNavigationError(PlaywrightBridgeError):
    """El expediente no pudo abrirse o extraerse correctamente."""


@dataclass(slots=True)
class GUIPlaywrightBridge:
    """Gestiona una sesión de Playwright reutilizable para la GUI."""

    headless: bool = False
    login_url: str | None = None
    _loop: asyncio.AbstractEventLoop | None = field(init=False, default=None, repr=False)
    _thread: threading.Thread | None = field(init=False, default=None, repr=False)
    _session_cm: Any | None = field(init=False, default=None, repr=False)
    _page: Page | None = field(init=False, default=None, repr=False)
    _lock: asyncio.Lock | None = field(init=False, default=None, repr=False)
    _closed: bool = field(init=False, default=False, repr=False)

    def __post_init__(self) -> None:
        # El ciclo de vida real se controla en :meth:`start`, pero mantenemos
        # esta función para documentar que la instancia inicia “apagada”.
        self._closed = False

    # ------------------------------------------------------------------
    # Inicialización y finalización
    # ------------------------------------------------------------------
    def start(self) -> None:
        """Inicia el hilo de Playwright y abre la página autenticada."""

        if self._closed:
            raise PlaywrightSessionError("La sesión de Playwright ya fue cerrada.")
        if self._loop is not None:
            return

        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(
            target=self._loop.run_forever, name="gui-playwright", daemon=True
        )
        self._thread.start()

        try:
            self._run_async(self._initialize())
        except Exception as exc:  # noqa: BLE001 - propagamos como error de sesión
            self.close()
            raise PlaywrightSessionError(
                "No se pudo iniciar la sesión autenticada de Playwright"
            ) from exc

    def close(self) -> None:
        """Cierra la sesión y detiene el hilo de Playwright."""

        if self._closed:
            return

        if self._loop is not None:
            try:
                self._run_async(self._finalize())
            except Exception:  # pragma: no cover - mejor esfuerzo
                logger.exception("Error al cerrar la sesión de Playwright")
            finally:
                loop = self._loop
                if loop is not None:
                    loop.call_soon_threadsafe(loop.stop)
                if self._thread is not None:
                    self._thread.join(timeout=2)

        self._loop = None
        self._thread = None
        self._session_cm = None
        self._page = None
        self._lock = None
        self._closed = True

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def run_coroutine(self, coro: Awaitable[Any]) -> Any:
        """Ejecuta una corrutina en el hilo de Playwright y devuelve su resultado."""

        if self._loop is None:
            raise PlaywrightSessionError("La sesión de Playwright no está inicializada.")
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def get_expediente_payload(self, expediente: ExpedienteResumen) -> dict[str, Any]:
        """Obtiene los datos necesarios para procesar un expediente."""

        if self._loop is None:
            raise PlaywrightSessionError("La sesión de Playwright no está inicializada.")
        return self.run_coroutine(self._build_payload(expediente))

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    def _run_async(self, coro: Coroutine[Any, Any, Any]) -> Any:
        if self._loop is None:
            raise PlaywrightSessionError("No hay un loop activo para ejecutar la tarea.")
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    async def _initialize(self) -> None:
        self._lock = asyncio.Lock()
        login_url = self.login_url
        cm = obtener_pagina_autenticada(headless=self.headless, login_url=login_url)
        self._session_cm = cm
        page, _context, _browser = await cm.__aenter__()
        self._page = page
        await self._ensure_consultas_page()

    async def _finalize(self) -> None:
        if self._session_cm is not None:
            try:
                await self._session_cm.__aexit__(None, None, None)
            finally:
                self._session_cm = None
        self._page = None

    async def _ensure_consultas_page(self) -> None:
        page = await self._get_page()
        if page.url != URL_CONSULTAS:
            await page.goto(URL_CONSULTAS)
            await page.wait_for_load_state("domcontentloaded")
            await page.wait_for_timeout(500)

    async def _get_page(self) -> Page:
        if self._page is None:
            raise PlaywrightSessionError("La página autenticada no está disponible.")
        if self._page.is_closed():
            raise PlaywrightSessionError("La página de Playwright se encuentra cerrada.")
        return self._page

    async def _build_payload(self, expediente: ExpedienteResumen) -> dict[str, Any]:
        if self._lock is None:
            raise PlaywrightSessionError("La sesión de Playwright no está lista.")

        async with self._lock:
            page = await self._get_page()
            await self._ensure_consultas_page()

            numero, anio = _split_numero_anio(expediente.numero)
            caratula = expediente.caratula if expediente.caratula else None

            try:
                filas = await buscar_expedientes(
                    page,
                    numero=numero,
                    anio=anio,
                    caratula=None if numero and anio else caratula,
                )
            except Exception as exc:  # noqa: BLE001
                logger.exception("Error buscando expediente %s", expediente.numero)
                raise ExpedienteNavigationError(
                    f"No se pudo realizar la búsqueda del expediente {expediente.numero}."
                ) from exc

            if not filas:
                raise ExpedienteNotFoundError(
                    f"El expediente {expediente.numero} no fue encontrado en el portal."
                )

            try:
                datos = await mostrar_y_elegir_expediente(page, filas)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Error abriendo expediente %s", expediente.numero)
                raise ExpedienteNavigationError(
                    f"No se pudo abrir el expediente {expediente.numero}."
                ) from exc

            if not datos:
                raise ExpedienteNavigationError(
                    f"No se pudieron obtener los datos del expediente {expediente.numero}."
                )

            if "numero" not in datos or not datos.get("numero"):
                datos["numero"] = expediente.numero
            datos.setdefault("caratula", expediente.caratula)
            datos.setdefault("dependencia", expediente.dependencia)
            datos["page"] = page
            return datos


def _split_numero_anio(valor: str | None) -> tuple[str | None, str | None]:
    if not valor:
        return None, None
    texto = valor.strip()
    if not texto:
        return None, None

    match = re.search(r"(\d+)[^\d]{0,5}(\d{2,4})$", texto)
    if match:
        return match.group(1), match.group(2)

    numeros = re.findall(r"\d+", texto)
    if len(numeros) >= 2:
        return numeros[-2], numeros[-1]

    return None, None


__all__ = [
    "GUIPlaywrightBridge",
    "PlaywrightBridgeError",
    "PlaywrightSessionError",
    "ExpedienteNotFoundError",
    "ExpedienteNavigationError",
]
