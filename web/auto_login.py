"""Automatiza el inicio de sesión en el portal PJN.

Este módulo espera las credenciales a través de las variables de entorno
``PJN_USER`` y ``PJN_PASSWORD``.
Incluye utilidades para reutilizar una sesión previamente guardada tanto en
código sincrónico como asincrónico.
"""

import os
import json
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from playwright.async_api import async_playwright, Browser, BrowserContext

URL_LOGIN = "https://portalpjn.pjn.gov.ar/inicio"
SELEC_USUARIO = "input[name='username']"
SELEC_CLAVE = "input[name='password']"
SELEC_BOTON = "#kc-login"
SELEC_CONFIRMACION = "text='Menú'"
SESSION_FILE = Path(__file__).with_name("estado_sesion.json")


async def crear_contexto(p, storage_state=None) -> tuple[Browser, BrowserContext]:
    browser = await p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"],
    )
    context = await browser.new_context(storage_state=storage_state)
    await context.add_init_script(
        "Object.defineProperty(navigator, 'webdriver', { get: () => undefined });"
    )
    return browser, context


async def guardar_sesion(context):
    try:
        storage = await context.storage_state()
        with SESSION_FILE.open("w", encoding="utf-8") as f:
            json.dump(storage, f, ensure_ascii=False, indent=2)
        print("✅ Estado de sesión guardado correctamente.")
    except Exception as e:
        print("❌ Error al guardar la sesión:", e)


async def iniciar_sesion():
    """Inicia una nueva sesión usando ``PJN_USER`` y ``PJN_PASSWORD``."""
    USUARIO = os.getenv("PJN_USER")
    CONTRASENA = os.getenv("PJN_PASSWORD")
    missing_vars = [
        name
        for name, value in (("PJN_USER", USUARIO), ("PJN_PASSWORD", CONTRASENA))
        if value is None
    ]
    if missing_vars:
        raise EnvironmentError(
            f"Faltan variables de entorno requeridas: {', '.join(missing_vars)}"
        )

    p = browser = context = page = None
    try:
        print("🔐 Iniciando nueva sesión...")
        p = await async_playwright().start()
        browser, context = await crear_contexto(p)
        page = await context.new_page()
        await page.goto(URL_LOGIN)
        await page.wait_for_load_state("domcontentloaded")

        await page.fill(SELEC_USUARIO, USUARIO)
        await page.fill(SELEC_CLAVE, CONTRASENA)
        await page.click(SELEC_BOTON)
        print("⏳ Esperando confirmación de login...")
        await page.wait_for_selector(SELEC_CONFIRMACION, timeout=60000)
        print("✅ Login exitoso.")
        await guardar_sesion(context)
    except Exception as e:
        print("❌ Error en login automático:", e)
        raise RuntimeError("Login fallido") from e
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass
        if context:
            try:
                await context.close()
            except Exception:
                pass
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        if p:
            try:
                await p.stop()
            except Exception:
                pass


@asynccontextmanager
async def reutilizar_sesion_async():
    """Reutiliza una sesión guardada o inicia una nueva si es necesario."""
    missing_vars = [
        name for name in ("PJN_USER", "PJN_PASSWORD") if os.getenv(name) is None
    ]
    if missing_vars:
        raise EnvironmentError(
            f"Faltan variables de entorno requeridas: {', '.join(missing_vars)}"
        )

    p = browser = context = page = None
    try:
        p = await async_playwright().start()
        if not SESSION_FILE.exists():
            print("⚠️ No hay sesión guardada. Ejecutando login manual...")
            await iniciar_sesion()
        else:
            print("🔄 Reutilizando sesión guardada...")

        try:
            with SESSION_FILE.open("r", encoding="utf-8") as f:
                storage_state = json.load(f)
        except Exception as e:
            print("❌ Error al leer la sesión:", e)
            raise

        browser, context = await crear_contexto(p, storage_state=storage_state)
        page = await context.new_page()
        await page.goto(URL_LOGIN)
        await page.wait_for_load_state("domcontentloaded")

        try:
            await page.wait_for_selector(SELEC_CONFIRMACION, timeout=10000)
            print("✅ Sesión activa, acceso exitoso.")
        except Exception:
            if await page.is_visible(SELEC_USUARIO):
                print(
                    "⚠️ Página de login detectada. Eliminando sesión y reiniciando login..."
                )
                await page.close()
                await context.close()
                await browser.close()
                page = context = browser = None
                try:
                    SESSION_FILE.unlink()
                except Exception:
                    pass
                await iniciar_sesion()
                try:
                    with SESSION_FILE.open("r", encoding="utf-8") as f:
                        storage_state = json.load(f)
                except Exception as e:
                    print("❌ Error al leer la sesión:", e)
                    raise
                browser, context = await crear_contexto(p, storage_state=storage_state)
                page = await context.new_page()
                await page.goto(URL_LOGIN)
                await page.wait_for_load_state("domcontentloaded")
            else:
                print("❌ No se pudo verificar si está logueado.")
                await page.close()
                await context.close()
                await browser.close()
                page = context = browser = None

        yield page, context, browser
    except Exception as e:
        print("❌ Error en reutilizar_sesion_async:", e)
        yield None, None, None
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass
        if context:
            try:
                await context.close()
            except Exception:
                pass
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        if p:
            try:
                await p.stop()
            except Exception:
                pass

# Test manual
async def main():
    page = context = browser = p = None
    try:
        async with reutilizar_sesion_async() as (page, context, browser):
            if page:
                print("✅ Login exitoso y navegador activo.")
            else:
                print("❌ No se pudo iniciar sesión.")
            print("📋 Fin del proceso.")
    except Exception as e:
        print("❌ Error en la ejecución principal:", e)
    finally:
        if page:
            try:
                await page.close()
            except Exception:
                pass
        if context:
            try:
                await context.close()
            except Exception:
                pass
        if browser:
            try:
                await browser.close()
            except Exception:
                pass
        if p:
            try:
                await p.stop()
            except Exception:
                pass


def reutilizar_sesion():
    """Reutiliza una sesión guardada o inicia una nueva si es necesario.

    La función detecta si existe un bucle de eventos de :mod:`asyncio` en
    ejecución para adaptarse a ambos escenarios:

    * **Con loop activo:** retorna el context manager :func:`reutilizar_sesion_async`
      para ser utilizado con ``async with``.
    * **Sin loop activo:** ejecuta ``reutilizar_sesion_async`` mediante
      :func:`asyncio.run` y devuelve directamente la tupla
      ``(page, context, browser)``.

    Ejemplos
    --------
    Uso sincrónico::

        page, context, browser = reutilizar_sesion()

    Uso asincrónico::

        async with reutilizar_sesion() as (page, context, browser):
            ...
    """

    async def _runner():
        async with reutilizar_sesion_async() as triple:
            return triple

    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(_runner())
    else:
        return reutilizar_sesion_async()


if __name__ == "__main__":
    asyncio.run(main())
