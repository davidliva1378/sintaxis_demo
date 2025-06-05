import asyncio
from playwright.async_api import async_playwright
from urls_pjn import  URL_LOGIN, URL_CONSULTAS
from panel_pjn.acciones_pjn.gestion_expedientes.bk.buscar_y_abrir_expediente_1 import buscar_expediente_por_numero

async def probar_busqueda_por_formulario():
    numero = input("📥 Ingrese número de expediente (solo números): ").strip()
    anio = input("📥 Ingrese año del expediente: ").strip()

    USUARIO = "20213071662"
    CLAVE = "surrey1970"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        # Login
        await page.goto(URL_LOGIN)
        await page.fill("input[name='username']", USUARIO)
        await page.fill("input[name='password']", CLAVE)
        await page.click("#kc-login")
        await page.wait_for_selector("text='Menú'", timeout=10000)

        # Ir a Consultas
        await page.goto(URL_CONSULTAS)
        await page.wait_for_load_state("load")

        # Buscar expediente por formulario
        exito = await buscar_expediente_por_numero(page, numero, anio)

        if exito:
            print("🎯 Búsqueda ejecutada con éxito. Revisar resultados en pantalla.")
        else:
            print("⚠️ La búsqueda no devolvió resultados o falló.")

        await page.wait_for_timeout(8000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(probar_busqueda_por_formulario())