import asyncio
from playwright.async_api import async_playwright
from datetime import datetime

from panel_pjn.acciones_pjn.urls_pjn import URL_LOGIN, URL_CONSULTAS
from core.modulos_monitor.expedientes_modular.extraer_expedientes import extraer_expedientes_v2

def registrar_log(mensaje):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {mensaje}"
    print(log_entry)
    with open("log_monitor_expedientes.txt", "a", encoding="utf-8") as f:
        f.write(log_entry + "\n")

async def monitor_expedientes():
    registrar_log("🔐 Iniciando sesión PJN...")
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            context = await browser.new_context()
            page = await context.new_page()

            await page.goto(URL_LOGIN)
            await page.fill("input[name='username']", "20213071662")
            await page.fill("input[name='password']", "surrey1970")
            await page.click("#kc-login")
            await page.wait_for_selector("text='Menú'", timeout=10000)
            registrar_log("✅ Login exitoso.")

            await page.goto(URL_CONSULTAS)
            await page.wait_for_load_state("load")
            registrar_log("🌐 Abriendo sección de Consultas...")

            expedientes, ruta, estado = await extraer_expedientes_v2(
                page,
                carpeta_salida="datos_iniciales/",
                nombre_archivo="expedientes_monitor.json",
                detener_en_duplicado=True,
                tiempo_maximo_segundos=120
            )

            registrar_log(f"📦 Estado: {estado}")
            registrar_log(f"📊 Expedientes extraídos: {len(expedientes)}")
            if ruta:
                registrar_log(f"📁 Archivo guardado en: {ruta}")

            await browser.close()

    except Exception as e:
        registrar_log(f"❌ Error crítico en el monitor: {str(e)}")

if __name__ == "__main__":
    asyncio.run(monitor_expedientes())
