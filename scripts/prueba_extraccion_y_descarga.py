import asyncio
from playwright.async_api import async_playwright
from urls_pjn import URL_LOGIN, URL_CONSULTAS
from buscar_y_abrir_expediente_1 import buscar_y_abrir_expediente
from obtener_actuaciones_todas_paginas_async import obtener_actuaciones_todas_paginas_async
from descargar_archivos_actuaciones import descargar_archivos_actuaciones

async def prueba_extraccion_y_descarga():
    numero = input("📥 Ingrese número de expediente (solo números): ").strip()
    anio = input("📅 Ingrese año del expediente: ").strip()
    caratula = input("📝 Ingrese carátula exacta: ").strip()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()

        print("🔐 Iniciando sesión...")
        await page.goto(URL_LOGIN)
        await page.fill("input[name='username']", "20213071662")
        await page.fill("input[name='password']", "surrey1970")
        await page.click("#kc-login")
        await page.wait_for_selector("text='Menú'", timeout=10000)

        print("🌐 Abriendo consultas...")
        await page.goto(URL_CONSULTAS)
        await page.wait_for_load_state("load")

        resultado = await buscar_y_abrir_expediente(page, numero, anio, caratula)
        if not resultado["exito"]:
            print(f"❌ Error: {resultado['mensaje']}")
            await browser.close()
            return

        page_expediente = page
        expediente_datos = resultado["datos_expediente"]
        print(f"✅ Expediente abierto: {expediente_datos['numero']}")

        print("🔁 Extrayendo todas las actuaciones...")
        actuaciones = await obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos)

        carpeta_destino = f"Actuaciones/{expediente_datos['numero'].replace('/', '_')}"
        print("📦 Descargando archivos adjuntos...")
        await descargar_archivos_actuaciones(page_expediente, actuaciones, carpeta_destino)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(prueba_extraccion_y_descarga())