import os
import json
import asyncio
from playwright.async_api import async_playwright

URL_LOGIN = "https://portalpjn.pjn.gov.ar/inicio"
SELEC_USUARIO = "input[name='username']"
SELEC_CLAVE = "input[name='password']"
SELEC_BOTON = "#kc-login"
SELEC_CONFIRMACION = "text='Menú'"
SESSION_FILE = "estado_sesion.json"

USUARIO = os.getenv("PJN_USER", "20213071662")
CONTRASENA = os.getenv("PJN_PASSWORD", "surrey1970")

async def guardar_sesion(context):
    storage = await context.storage_state()
    with open(SESSION_FILE, "w") as f:
        json.dump(storage, f)
    print("✅ Estado de sesión guardado correctamente.")

async def iniciar_sesion(p):
    print("🔐 Iniciando nueva sesión (visible)...")
    browser = await p.chromium.launch(
        headless=False,  # Mostrar navegador
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
    )
    context = await browser.new_context()
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
    page = await context.new_page()
    await page.goto(URL_LOGIN)
    await page.wait_for_load_state("domcontentloaded")

    try:
        await page.fill(SELEC_USUARIO, USUARIO)
        await page.fill(SELEC_CLAVE, CONTRASENA)
        await page.click(SELEC_BOTON)
        print("⏳ Esperando confirmación de login...")
        await page.wait_for_selector(SELEC_CONFIRMACION, timeout=60000)
        print("✅ Login exitoso.")
        await guardar_sesion(context)
    except Exception as e:
        print("❌ Error en login automático:", e)

    return page, context, browser, p

async def reutilizar_sesion_async():
    p = await async_playwright().start()

    if not os.path.exists(SESSION_FILE):
        print("⚠️ No hay sesión guardada. Ejecutando login manual...")
        return await iniciar_sesion(p)

    print("🔄 Reutilizando sesión guardada (visual)...")
    with open(SESSION_FILE, "r") as f:
        storage_state = json.load(f)

    browser = await p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
    )
    context = await browser.new_context(storage_state=storage_state)
    await context.add_init_script("Object.defineProperty(navigator, 'webdriver', { get: () => undefined });")
    page = await context.new_page()
    await page.goto(URL_LOGIN)
    await page.wait_for_load_state("domcontentloaded")

    try:
        await page.wait_for_selector(SELEC_CONFIRMACION, timeout=10000)
        print("✅ Sesión activa, acceso exitoso.")
        return page, context, browser, p
    except:
        if await page.is_visible(SELEC_USUARIO):
            print("⚠️ Página de login detectada. Eliminando sesión y reiniciando login...")
            await context.close()
            await browser.close()
            os.remove(SESSION_FILE)
            return await iniciar_sesion(p)
        else:
            print("❌ No se pudo verificar si está logueado.")
            await context.close()
            await browser.close()
            await p.stop()
            return None, None, None, None

def reutilizar_sesion():
    return asyncio.run(reutilizar_sesion_async())

if __name__ == "__main__":
    asyncio.run(reutilizar_sesion_async())