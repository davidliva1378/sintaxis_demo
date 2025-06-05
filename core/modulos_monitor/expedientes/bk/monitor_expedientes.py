import asyncio
from playwright.async_api import async_playwright
from panel_pjn.acciones_pjn.urls_pjn import URL_LOGIN, URL_CONSULTAS
from datetime import datetime
import os
from core.modulos_monitor.expedientes_modular.extraer_expedientes import extraer_expedientes_v2

def registrar_log(texto):
    ruta = os.path.join(os.path.dirname(__file__), "log.txt")
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {texto}\n")
    print(texto)

async def monitor_expedientes_robusto():
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            registrar_log("🔐 Iniciando sesión PJN...")
            await page.goto(URL_LOGIN)
            await page.fill("input[name='username']", "20213071662")
            await page.fill("input[name='password']", "surrey1970")
            await page.click("#kc-login")
            await page.wait_for_selector("text='Menú'", timeout=10000)

            registrar_log("🌐 Navegando a Consultas...")
            await page.goto(URL_CONSULTAS)
            await page.wait_for_load_state("load")

            registrar_log("📥 Iniciando extracción robusta de expedientes...")
            ruta = await extraer_expedientes_v2(page)

            registrar_log(f"✅ Extracción finalizada. Archivo: {ruta}")
            await browser.close()

    except Exception as e:
        mensaje = str(e)
        if "INTERNET_DISCONNECTED" in mensaje or "ERR_NAME_NOT_RESOLVED" in mensaje or "ERR_INTERNET_DISCONNECTED" in mensaje:
            registrar_log("🌐 Sin conexión a Internet. No se pudo iniciar sesión ni continuar.")
        else:
            registrar_log(f"❌ Error crítico en el monitor: {mensaje}")

if __name__ == "__main__":
    asyncio.run(monitor_expedientes_robusto())