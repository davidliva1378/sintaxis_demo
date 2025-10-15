"""Utilidades compartidas para los scrapers del portal PJN.

Este módulo centraliza la lógica que antes estaba repetida en los scripts
para:

* Normalización de texto y fechas.
* Generación de identificadores y nombres de archivo seguros.
* Gestión de sesiones de Playwright (inicio de sesión y reutilización del
  estado de almacenamiento).

El objetivo es que `actuaciones`, `expedientes` y `entradas` dependan de
estas funciones comunes en lugar de reimplementar variantes locales.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import unicodedata
from contextlib import asynccontextmanager
from datetime import date, datetime
from pathlib import Path
from typing import AsyncIterator, Iterable, Sequence

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    TimeoutError,
    async_playwright,
)

from ..config import get_config
from ..exceptions import CredencialesFaltantes, SesionInvalida
from ..selectores import SEL_AUTH

# === Constantes de autenticación (ahora desde config) ===
_config = get_config()
PJN_LOGIN_URL = _config.auth.login_url
DEFAULT_SESSION_FILE = Path(__file__).with_name(_config.auth.session_file_name)
DEFAULT_BROWSER_ARGS = list(_config.browser.args)


# === Normalización de texto y fechas ===

def limpiar_texto(texto: str | None) -> str:
    """Elimina saltos de línea y espacios redundantes.

    Devuelve una cadena vacía si ``texto`` es ``None``.
    """

    if texto is None:
        return ""

    resultado = re.sub(r"\s+", " ", str(texto).replace("\r", " "))
    return resultado.strip()


def normalizar_texto(texto: str | None) -> str:
    """Normaliza el texto a minúsculas ASCII sin acentos."""

    texto_limpio = limpiar_texto(texto)
    if not texto_limpio:
        return ""
    return unicodedata.normalize("NFKD", texto_limpio.lower()).encode(
        "ascii", "ignore"
    ).decode("utf-8")


def normalizar_fecha(
    valor: str | date | datetime | None,
    *,
    formato_salida: str = "%Y-%m-%d",
    formatos_entrada: Sequence[str] | None = None,
) -> str | None:
    """Convierte fechas comunes del PJN al formato deseado.

    Si no puede interpretarse ``valor``, devuelve el texto original limpiado.
    """

    if valor is None:
        return None

    if isinstance(valor, datetime):
        return valor.strftime(formato_salida)

    if isinstance(valor, date):
        return datetime.combine(valor, datetime.min.time()).strftime(
            formato_salida
        )

    texto = limpiar_texto(str(valor))
    if not texto:
        return None

    formatos = formatos_entrada or (
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%d-%m-%Y",
        "%d/%m/%y",
        "%d-%m-%y",
    )
    for fmt in formatos:
        try:
            return datetime.strptime(texto, fmt).strftime(formato_salida)
        except ValueError:
            continue

    return texto


def generar_hash_identificador(*componentes: object, longitud: int = 6) -> str:
    """Genera un hash estable a partir de múltiples componentes."""

    base = "::".join(limpiar_texto(str(c)) for c in componentes if c is not None)
    digest = hashlib.sha256(base.encode("utf-8")).hexdigest()
    return digest[:longitud]


def normalizar_numero_expediente(
    valor: object,
    *,
    valor_por_defecto: str = "expediente",
) -> str:
    """Convierte un número de expediente en un nombre seguro para rutas."""

    if valor is None:
        numero = valor_por_defecto
    else:
        numero = limpiar_texto(str(valor))
        if not numero:
            numero = valor_por_defecto

    return re.sub(r"[^\w-]", "_", numero)


# === Gestión de sesiones de Playwright ===

def _obtener_credenciales(
    usuario: str | None = None, contraseña: str | None = None
) -> tuple[str, str]:
    usuario = usuario or os.getenv("PJN_USER")
    contraseña = contraseña or os.getenv("PJN_PASSWORD")
    faltantes = [
        nombre
        for nombre, valor in (("PJN_USER", usuario), ("PJN_PASSWORD", contraseña))
        if not valor
    ]
    if faltantes:
        raise CredencialesFaltantes(
            f"Faltan variables de entorno requeridas: {', '.join(faltantes)}"
        )
    return usuario, contraseña  # type: ignore[return-value]


async def _crear_contexto(
    playwright,
    *,
    storage_state: dict | None = None,
    headless: bool = False,
    browser_args: Iterable[str] | None = None,
) -> tuple[Browser, BrowserContext]:
    args = list(DEFAULT_BROWSER_ARGS)
    if browser_args:
        args.extend(browser_args)

    browser = await playwright.chromium.launch(headless=headless, args=args)
    context = await browser.new_context(storage_state=storage_state)
    await context.add_init_script(_config.browser.anti_webdriver_script)
    return browser, context


def _leer_storage_state(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        with path.open("r", encoding="utf-8") as archivo:
            return json.load(archivo)
    except Exception:
        return None


async def _guardar_storage_state(context: BrowserContext, destino: Path) -> None:
    try:
        storage = await context.storage_state()
    except Exception as exc:  # pragma: no cover - defensivo
        raise SesionInvalida("No se pudo obtener el storage state actual") from exc

    destino.parent.mkdir(parents=True, exist_ok=True)
    with destino.open("w", encoding="utf-8") as archivo:
        json.dump(storage, archivo, indent=2, ensure_ascii=False)


async def _realizar_login(
    playwright,
    *,
    usuario: str,
    contraseña: str,
    headless: bool,
    session_file: Path,
    login_url: str,
    browser_args: Iterable[str] | None,
) -> None:
    browser = context = page = None
    try:
        browser, context = await _crear_contexto(
            playwright, headless=headless, browser_args=browser_args
        )
        page = await context.new_page()
        await page.goto(login_url)
        await page.wait_for_load_state("domcontentloaded")
        await page.fill(SEL_AUTH.USUARIO, usuario)
        await page.fill(SEL_AUTH.PASSWORD, contraseña)
        await page.click(SEL_AUTH.BOTON_LOGIN)
        await page.wait_for_selector(SEL_AUTH.CONFIRMACION_LOGIN, timeout=60000)
        await _guardar_storage_state(context, session_file)
    finally:
        if page:
            await page.close()
        if context:
            await context.close()
        if browser:
            await browser.close()


async def _verificar_sesion(page: Page) -> bool:
    try:
        await page.wait_for_selector(SEL_AUTH.CONFIRMACION_LOGIN, timeout=5000)
        return True
    except TimeoutError:
        pass

    try:
        if await page.is_visible(SEL_AUTH.USUARIO):
            return False
    except Exception:
        return False

    return False


@asynccontextmanager
async def obtener_pagina_autenticada(
    *,
    usuario: str | None = None,
    contraseña: str | None = None,
    session_file: Path = DEFAULT_SESSION_FILE,
    headless: bool = False,
    login_url: str = PJN_LOGIN_URL,
    browser_args: Iterable[str] | None = None,
) -> AsyncIterator[tuple[Page, BrowserContext, Browser]]:
    """Devuelve una página autenticada reutilizando el *storage state* local.

    Si el archivo de sesión no existe o resulta inválido se realiza un login
    automático y se reintenta.
    """

    usuario_resuelto, contraseña_resuelta = _obtener_credenciales(usuario, contraseña)

    async with async_playwright() as playwright:
        storage_state = _leer_storage_state(session_file)
        if storage_state is None:
            await _realizar_login(
                playwright,
                usuario=usuario_resuelto,
                contraseña=contraseña_resuelta,
                headless=headless,
                session_file=session_file,
                login_url=login_url,
                browser_args=browser_args,
            )
            storage_state = _leer_storage_state(session_file)
            if storage_state is None:
                raise SesionInvalida("No se pudo crear el archivo de sesión")

        browser = context = page = None
        try:
            browser, context = await _crear_contexto(
                playwright,
                storage_state=storage_state,
                headless=headless,
                browser_args=browser_args,
            )
            page = await context.new_page()
            await page.goto(login_url)
            await page.wait_for_load_state("domcontentloaded")

            if not await _verificar_sesion(page):
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
                )
                storage_state = _leer_storage_state(session_file)
                if storage_state is None:
                    raise SesionInvalida("El login no generó un storage state válido")

                browser, context = await _crear_contexto(
                    playwright,
                    storage_state=storage_state,
                    headless=headless,
                    browser_args=browser_args,
                )
                page = await context.new_page()
                await page.goto(login_url)
                await page.wait_for_load_state("domcontentloaded")

                if not await _verificar_sesion(page):
                    raise SesionInvalida(
                        "No se pudo validar la sesión luego de reloguear"
                    )

            yield page, context, browser
        finally:
            if page:
                await page.close()
            if context:
                await context.close()
            if browser:
                await browser.close()

