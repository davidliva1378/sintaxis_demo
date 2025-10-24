import asyncio
from playwright.async_api import async_playwright
from urls_pjn import URL_LOGIN, URL_CONSULTAS
from buscar_y_abrir_expediente_1 import buscar_y_abrir_expediente
from obtener_actuaciones_async import obtener_actuaciones_async
import os

async def prueba_expediente_y_actuaciones():
    numero = input("📥 Ingrese número de expediente (solo números): ").strip()
    anio = input("📅 Ingrese año del expediente: ").strip()
    caratula = input("📝 Ingrese carátula exacta: ").strip()

    USUARIO = "20213071662"
    CLAVE = "surrey1970"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        print("🔐 Iniciando sesión PJN...")
        await page.goto(URL_LOGIN)
        await page.fill("input[name='username']", USUARIO)
        await page.fill("input[name='password']", CLAVE)
        await page.click("#kc-login")
        await page.wait_for_selector("text='Menú'", timeout=10000)

        print("🌐 Accediendo a Consultas...")
        await page.goto(URL_CONSULTAS)
        await page.wait_for_load_state("load")

        resultado = await buscar_y_abrir_expediente(page, numero, anio, caratula)

        if not resultado["exito"]:
            print(f"❌ No se pudo abrir el expediente: {resultado['mensaje']}")
            await browser.close()
            return

        print(f"✅ Expediente abierto correctamente: {resultado['datos_expediente']['numero']}")
        decision = input("¿Desea extraer las actuaciones? (s/n): ").strip().lower()

        if decision == "s":
            carpeta = os.path.join("../Actuaciones")
            os.makedirs(carpeta, exist_ok=True)
            await obtener_actuaciones_async(page, resultado["datos_expediente"], carpeta_destino=carpeta)
        else:
            print("⏹️ Extracción de actuaciones cancelada.")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(prueba_expediente_y_actuaciones())