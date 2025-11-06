"""Session Manager - Gestión de sesiones Playwright para el sistema v6.

Este módulo maneja la autenticación y persistencia de sesiones del portal PJN
usando Playwright. Ofrece dos modos:

1. **Session Context Manager** (una sola operación):
   - Uso: `async with obtener_sesion_autenticada() as page:`
   - Crea sesión, ejecuta operación, cierra automáticamente

2. **Persistent Session Manager** (múltiples operaciones):
   - Uso: `manager = SessionManager(); page = await manager.ensure_session()`
   - Mantiene sesión viva entre operaciones
   - Ideal para monitoreo continuo

Migrado de: Sistema_v5/pjn/scraping/base.py + session_manager.py
"""

from __future__ import annotations

import json
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncIterator, Iterable

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError,
    async_playwright,
)

from infrastructure.config import Settings, get_settings
from infrastructure.exceptions import CredencialesFaltantes, SesionInvalida

from .selectores import SEL_AUTH

logger = logging.getLogger(__name__)


# === Funciones auxiliares privadas ===


def _obtener_credenciales(
    usuario: str | None = None,
    contraseña: str | None = None,
    settings: Settings | None = None,
) -> tuple[str, str]:
    """Obtiene credenciales desde parámetros, settings o variables de entorno.

    Args:
        usuario: Usuario explícito (opcional)
        contraseña: Contraseña explícita (opcional)
        settings: Settings del sistema (opcional)

    Returns:
        Tupla (usuario, contraseña)

    Raises:
        CredencialesFaltantes: Si no se encuentran credenciales
    """
    if settings is None:
        settings = get_settings()

    # Prioridad: parámetros > settings > env
    usuario_final = usuario or settings.auth.usuario or os.getenv("PJN_USER")
    contraseña_final = contraseña or settings.auth.password or os.getenv("PJN_PASSWORD")

    faltantes = []
    if not usuario_final:
        faltantes.append("usuario (PJN_USER)")
    if not contraseña_final:
        faltantes.append("contraseña (PJN_PASSWORD)")

    if faltantes:
        raise CredencialesFaltantes(
            f"Faltan credenciales requeridas: {', '.join(faltantes)}. "
            f"Provéelas como parámetros, en .env o en variables de entorno."
        )

    return usuario_final, contraseña_final  # type: ignore


async def _crear_contexto(
    playwright,
    *,
    storage_state: dict | None = None,
    headless: bool = False,
    browser_args: Iterable[str] | None = None,
    settings: Settings | None = None,
) -> tuple[Browser, BrowserContext]:
    """Crea un browser y context de Playwright con configuración adecuada.

    Args:
        playwright: Instancia de Playwright
        storage_state: Estado de almacenamiento guardado (opcional)
        headless: Si True, ejecuta sin interfaz gráfica
        browser_args: Argumentos adicionales para el navegador
        settings: Settings del sistema

    Returns:
        Tupla (Browser, BrowserContext)
    """
    if settings is None:
        settings = get_settings()

    args = list(settings.browser.args)
    if browser_args:
        args.extend(browser_args)

    browser = await playwright.chromium.launch(headless=headless, args=args)
    context = await browser.new_context(storage_state=storage_state)

    # Anti-detection: agregar script para ocultar webdriver
    await context.add_init_script(settings.browser.anti_webdriver_script)

    return browser, context


def _leer_storage_state(path: Path) -> dict | None:
    """Lee el storage state desde un archivo JSON.

    Args:
        path: Path del archivo de storage state

    Returns:
        Diccionario con el storage state o None si no existe/inválido
    """
    if not path.exists():
        logger.debug(f"Archivo de sesión no existe: {path}")
        return None

    try:
        with path.open("r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except Exception as e:
        logger.warning(f"Error leyendo storage state de {path}: {e}")
        return None


async def _guardar_storage_state(context: BrowserContext, destino: Path) -> None:
    """Guarda el storage state del contexto actual a un archivo.

    Args:
        context: Contexto de Playwright
        destino: Path donde guardar el storage state

    Raises:
        SesionInvalida: Si no se pudo obtener el storage state
    """
    try:
        storage = await context.storage_state()
    except Exception as exc:
        raise SesionInvalida("No se pudo obtener el storage state actual") from exc

    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8") as archivo:
        json.dump(storage, archivo, indent=2, ensure_ascii=False)

    logger.debug(f"Storage state guardado en: {destino}")


async def _realizar_login(
    playwright,
    *,
    usuario: str,
    contraseña: str,
    headless: bool,
    session_file: Path,
    login_url: str,
    browser_args: Iterable[str] | None,
    settings: Settings | None = None,
) -> None:
    """Realiza el login en el portal PJN y guarda el storage state.

    Args:
        playwright: Instancia de Playwright
        usuario: Usuario del PJN
        contraseña: Contraseña del PJN
        headless: Modo headless
        session_file: Path donde guardar la sesión
        login_url: URL de login
        browser_args: Argumentos del navegador
        settings: Settings del sistema

    Raises:
        SesionInvalida: Si el login falla
    """
    browser = context = page = None
    try:
        logger.info(f"Iniciando nuevo login en {login_url}")
        browser, context = await _crear_contexto(
            playwright,
            headless=headless,
            browser_args=browser_args,
            settings=settings,
        )
        page = await context.new_page()

        await page.goto(login_url)
        await page.wait_for_load_state("domcontentloaded")

        logger.debug("Página de login cargada, rellenando credenciales")
        await page.fill(SEL_AUTH.USUARIO, usuario)
        await page.fill(SEL_AUTH.PASSWORD, contraseña)
        await page.click(SEL_AUTH.BOTON_LOGIN)

        logger.info("Credenciales enviadas, esperando confirmación de login...")
        await page.wait_for_selector(SEL_AUTH.CONFIRMACION_LOGIN, timeout=60000)

        logger.info(f"Login exitoso, guardando sesión en {session_file}")
        await _guardar_storage_state(context, session_file)

    finally:
        if page:
            await page.close()
        if context:
            await context.close()
        if browser:
            await browser.close()


async def _verificar_sesion(page: Page) -> bool:
    """Verifica si la sesión actual está autenticada.

    Args:
        page: Página de Playwright

    Returns:
        True si la sesión es válida, False en caso contrario
    """
    try:
        await page.wait_for_selector(SEL_AUTH.CONFIRMACION_LOGIN, timeout=5000)
        logger.debug("Sesión verificada - elemento de confirmación encontrado")
        return True
    except TimeoutError:
        logger.debug("Elemento de confirmación no encontrado, verificando formulario de login")

    try:
        if await page.is_visible(SEL_AUTH.USUARIO):
            logger.warning("Sesión expirada - formulario de login visible")
            return False
    except Exception as e:
        logger.warning(f"Error al verificar visibilidad del formulario: {e}")
        return False

    logger.warning("No se pudo determinar el estado de la sesión")
    return False


# === Context Manager para operaciones únicas ===


@asynccontextmanager
async def obtener_sesion_autenticada(
    *,
    usuario: str | None = None,
    contraseña: str | None = None,
    session_file: Path | None = None,
    headless: bool = True,
    login_url: str | None = None,
    browser_args: Iterable[str] | None = None,
    settings: Settings | None = None,
) -> AsyncIterator[Page]:
    """Context manager para obtener una página autenticada (operación única).

    Uso recomendado para operaciones puntuales que no requieren persistencia.

    Args:
        usuario: Usuario del PJN (opcional, lee de settings/env)
        contraseña: Contraseña del PJN (opcional, lee de settings/env)
        session_file: Path del archivo de sesión (opcional)
        headless: Si True, ejecuta sin interfaz gráfica
        login_url: URL de login (opcional, lee de settings)
        browser_args: Argumentos adicionales del navegador
        settings: Settings del sistema

    Yields:
        Page: Página de Playwright autenticada y lista para usar

    Raises:
        CredencialesFaltantes: Si no se encuentran credenciales
        SesionInvalida: Si no se pudo autenticar

    Example:
        >>> async with obtener_sesion_autenticada() as page:
        ...     await page.goto("https://portalpjn.pjn.gov.ar/inicio")
        ...     # Realizar operaciones...
        ...     # Sesión se cierra automáticamente al salir
    """
    if settings is None:
        settings = get_settings()

    if session_file is None:
        session_file = settings.storage.base_path / settings.auth.session_file_name

    if login_url is None:
        login_url = settings.auth.login_url

    usuario_resuelto, contraseña_resuelta = _obtener_credenciales(usuario, contraseña, settings)

    async with async_playwright() as playwright:
        storage_state = _leer_storage_state(session_file)

        if storage_state is None:
            logger.warning(f"No hay sesión guardada en {session_file} - realizando login inicial")
            await _realizar_login(
                playwright,
                usuario=usuario_resuelto,
                contraseña=contraseña_resuelta,
                headless=headless,
                session_file=session_file,
                login_url=login_url,
                browser_args=browser_args,
                settings=settings,
            )
            storage_state = _leer_storage_state(session_file)
            if storage_state is None:
                raise SesionInvalida("No se pudo crear el archivo de sesión")
        else:
            logger.info(f"Reutilizando sesión guardada desde {session_file}")

        browser = context = page = None
        try:
            browser, context = await _crear_contexto(
                playwright,
                storage_state=storage_state,
                headless=headless,
                browser_args=browser_args,
                settings=settings,
            )
            page = await context.new_page()
            await page.goto(login_url)
            await page.wait_for_load_state("domcontentloaded")

            logger.debug("Verificando validez de la sesión...")
            if not await _verificar_sesion(page):
                logger.warning("Sesión inválida o expirada - realizando re-login automático")
                await page.close()
                await context.close()
                await browser.close()
                browser = context = page = None

                await _realizar_login(
                    playwright,
                    usuario=usuario_resuelto,
                    contraseña=contraseña_resuelta,
                    headless=headless,
                    session_file=session_file,
                    login_url=login_url,
                    browser_args=browser_args,
                    settings=settings,
                )
                storage_state = _leer_storage_state(session_file)
                if storage_state is None:
                    raise SesionInvalida("El login no generó un storage state válido")

                browser, context = await _crear_contexto(
                    playwright,
                    storage_state=storage_state,
                    headless=headless,
                    browser_args=browser_args,
                    settings=settings,
                )
                page = await context.new_page()
                await page.goto(login_url)
                await page.wait_for_load_state("domcontentloaded")

                if not await _verificar_sesion(page):
                    logger.error("Login falló después de reintentar - sesión no se pudo validar")
                    raise SesionInvalida("No se pudo validar la sesión luego de reloguear")

            logger.info("Sesión autenticada exitosamente - página lista para usar")
            yield page

        finally:
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()


# === Session Manager persistente ===


class SessionExpiredError(Exception):
    """Excepción lanzada cuando la sesión ha expirado y debe renovarse."""

    pass


class SessionManager:
    """Gestor de sesiones persistentes de Playwright.

    Mantiene una sesión de navegador viva entre múltiples operaciones,
    verificando validez y renovando automáticamente cuando es necesario.

    Ideal para monitoreo continuo donde se necesitan múltiples operaciones
    sin la sobrecarga de abrir/cerrar el navegador cada vez.

    Attributes:
        timeout_minutos: Tiempo máximo de vida de una sesión antes de renovar
        _settings: Configuración del sistema
        _session_file: Path del archivo de storage state
        _login_url: URL de login
        _browser_args: Argumentos adicionales del navegador
        _playwright: Instancia de Playwright
        _playwright_cm: Context manager de Playwright
        _browser: Navegador Chromium abierto
        _context: Contexto del navegador con storage state
        _page: Página activa autenticada
        _session_created_at: Timestamp de creación de la sesión
        _headless: Modo headless del navegador

    Example:
        >>> # Uso básico
        >>> manager = SessionManager()
        >>> page = await manager.ensure_session(headless=True)
        >>> # Usar page para operaciones...
        >>> await manager.close_session()
        >>>
        >>> # Uso con context manager
        >>> async with SessionManager() as manager:
        ...     page = await manager.ensure_session()
        ...     # Operaciones...
        ...     # Cierra automáticamente al salir
    """

    def __init__(
        self,
        timeout_minutos: int = 60,
        session_file: Path | None = None,
        login_url: str | None = None,
        browser_args: Iterable[str] | None = None,
        settings: Settings | None = None,
    ):
        """Inicializa el gestor de sesiones persistentes.

        Args:
            timeout_minutos: Tiempo máximo de vida de sesión (default: 60 minutos)
            session_file: Archivo para guardar storage state (opcional)
            login_url: URL para realizar login (opcional)
            browser_args: Argumentos adicionales para el navegador
            settings: Settings del sistema (opcional)
        """
        self.timeout_minutos = timeout_minutos

        if settings is None:
            settings = get_settings()
        self._settings = settings

        if session_file is None:
            session_file = settings.storage.base_path / settings.auth.session_file_name
        self._session_file = session_file

        if login_url is None:
            login_url = settings.auth.login_url
        self._login_url = login_url

        self._browser_args = browser_args

        # Estado de la sesión
        self._playwright = None
        self._playwright_cm = None
        self._browser: Browser | None = None
        self._context: BrowserContext | None = None
        self._page: Page | None = None
        self._session_created_at: datetime | None = None
        self._headless: bool = True

    async def ensure_session(
        self,
        headless: bool = True,
        usuario: str | None = None,
        contraseña: str | None = None,
    ) -> Page:
        """Asegura que existe una sesión válida, creándola o renovándola si es necesario.

        Esta es la función principal para obtener una página autenticada.
        Verifica si la sesión actual es válida, si expiró el timeout, y
        crea/renueva según sea necesario.

        Args:
            headless: Si True, ejecuta navegador sin interfaz gráfica
            usuario: Usuario para login (opcional, lee de settings/env si no se provee)
            contraseña: Contraseña para login (opcional, lee de settings/env si no se provee)

        Returns:
            Page: Página de Playwright autenticada y lista para usar

        Raises:
            SessionExpiredError: Si la sesión expiró y no pudo renovarse
            SesionInvalida: Si no se pudo crear una sesión válida
            CredencialesFaltantes: Si no se encuentran credenciales

        Example:
            >>> manager = SessionManager()
            >>> page = await manager.ensure_session(headless=True)
            >>> await page.goto("https://portalpjn.pjn.gov.ar/inicio")
        """
        # Verificar si cambió el modo headless
        if self._page is not None and self._headless != headless:
            logger.info("Cambió modo headless, recreando sesión...")
            await self.close_session()

        # Si no hay sesión, crear una nueva
        if self._page is None:
            logger.info("No hay sesión activa, creando nueva...")
            await self._create_session(headless, usuario, contraseña)
            return self._page  # type: ignore

        # Verificar timeout de sesión
        if self._session_created_at is not None:
            edad_sesion = datetime.now() - self._session_created_at
            if edad_sesion > timedelta(minutes=self.timeout_minutos):
                logger.info(
                    f"Sesión expirada por timeout ({edad_sesion.total_seconds() / 60:.1f} min), renovando..."
                )
                await self.close_session()
                await self._create_session(headless, usuario, contraseña)
                return self._page  # type: ignore

        # Verificar si la sesión sigue válida
        try:
            is_valid = await self.is_session_valid()
        except Exception as e:
            logger.warning(f"Error al verificar sesión: {e}, recreando...")
            await self.close_session()
            await self._create_session(headless, usuario, contraseña)
            return self._page  # type: ignore

        if not is_valid:
            logger.warning("Sesión inválida detectada, renovando...")
            await self.close_session()
            await self._create_session(headless, usuario, contraseña)
            return self._page  # type: ignore

        # Sesión válida, reutilizar
        logger.debug("Sesión válida, reutilizando...")
        return self._page

    async def is_session_valid(self) -> bool:
        """Verifica si la sesión actual es válida.

        Returns:
            bool: True si la sesión está activa y válida, False en caso contrario
        """
        if self._page is None or self._page.is_closed():
            return False

        try:
            return await _verificar_sesion(self._page)
        except Exception as e:
            logger.debug(f"Error al verificar sesión: {e}")
            return False

    async def close_session(self) -> None:
        """Cierra la sesión actual limpiamente.

        Cierra la página, contexto, navegador y Playwright en orden,
        manejando errores gracefully.
        """
        if self._page is not None:
            try:
                await self._page.close()
            except Exception:
                pass  # Mejor esfuerzo
            self._page = None

        if self._context is not None:
            try:
                await self._context.close()
            except Exception:
                pass
            self._context = None

        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception:
                pass
            self._browser = None

        if self._playwright_cm is not None:
            try:
                await self._playwright_cm.__aexit__(None, None, None)
            except Exception:
                pass
            self._playwright_cm = None
            self._playwright = None

        self._session_created_at = None
        logger.info("Sesión cerrada correctamente")

    async def _create_session(
        self,
        headless: bool,
        usuario: str | None = None,
        contraseña: str | None = None,
    ) -> None:
        """Crea una nueva sesión de navegador autenticada.

        Args:
            headless: Si True, ejecuta navegador sin interfaz gráfica
            usuario: Usuario para login
            contraseña: Contraseña para login

        Raises:
            SesionInvalida: Si no se pudo crear una sesión válida
            CredencialesFaltantes: Si no se encuentran credenciales
        """
        # Obtener credenciales
        usuario_resuelto, contraseña_resuelta = _obtener_credenciales(
            usuario, contraseña, self._settings
        )

        # Iniciar Playwright
        self._playwright_cm = async_playwright()
        self._playwright = await self._playwright_cm.__aenter__()

        # Verificar si existe storage state guardado
        storage_state = _leer_storage_state(self._session_file)

        if storage_state is None:
            logger.info("No hay storage state guardado, realizando login inicial...")
            # Realizar login y guardar storage state
            await _realizar_login(
                self._playwright,
                usuario=usuario_resuelto,
                contraseña=contraseña_resuelta,
                headless=headless,
                session_file=self._session_file,
                login_url=self._login_url,
                browser_args=self._browser_args,
                settings=self._settings,
            )
            # Recargar storage state
            storage_state = _leer_storage_state(self._session_file)
            if storage_state is None:
                raise SesionInvalida("Login no generó storage state válido")

        # Crear browser y context con storage state
        self._browser, self._context = await _crear_contexto(
            self._playwright,
            storage_state=storage_state,
            headless=headless,
            browser_args=self._browser_args,
            settings=self._settings,
        )

        # Crear página y verificar sesión
        self._page = await self._context.new_page()
        await self._page.goto(self._login_url)
        await self._page.wait_for_load_state("domcontentloaded")

        # Verificar si la sesión es válida
        if not await _verificar_sesion(self._page):
            logger.warning("Storage state inválido, realizando re-login...")

            # Cerrar navegador actual
            await self._page.close()
            await self._context.close()
            await self._browser.close()

            # Realizar nuevo login
            await _realizar_login(
                self._playwright,
                usuario=usuario_resuelto,
                contraseña=contraseña_resuelta,
                headless=headless,
                session_file=self._session_file,
                login_url=self._login_url,
                browser_args=self._browser_args,
                settings=self._settings,
            )

            # Recrear browser y context
            storage_state = _leer_storage_state(self._session_file)
            if storage_state is None:
                raise SesionInvalida("Re-login no generó storage state válido")

            self._browser, self._context = await _crear_contexto(
                self._playwright,
                storage_state=storage_state,
                headless=headless,
                browser_args=self._browser_args,
                settings=self._settings,
            )

            self._page = await self._context.new_page()
            await self._page.goto(self._login_url)
            await self._page.wait_for_load_state("domcontentloaded")

        self._headless = headless
        self._session_created_at = datetime.now()

        logger.info(
            f"Sesión persistente creada - Headless: {headless}, Timeout: {self.timeout_minutos} min"
        )

    async def __aenter__(self):
        """Soporte para async context manager."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cierra sesión automáticamente al salir del context manager."""
        await self.close_session()
        return False


__all__ = [
    "obtener_sesion_autenticada",
    "SessionManager",
    "SessionExpiredError",
]
