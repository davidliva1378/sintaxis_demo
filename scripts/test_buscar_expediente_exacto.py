import asyncio
from playwright.async_api import async_playwright
from panel_pjn.acciones_pjn.gestion_expedientes.bk.buscar_expediente_exacto import buscar_expediente_exacto
from urls_pjn import URL_LOGIN, URL_CONSULTAS

async def buscar_expediente():
    texto = input("🔎 Ingrese número o carátula del expediente: ").strip()
    USUARIO = "20213071662"
    CLAVE = "surrey1970"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(URL_LOGIN)
        await page.fill("input[name='username']", USUARIO)
        await page.fill("input[name='password']", CLAVE)
        await page.click("#kc-login")
        await page.wait_for_selector("text='Menú'", timeout=10000)

        await page.goto(URL_CONSULTAS)
        await page.wait_for_load_state("load")

        fila = await buscar_expediente_exacto(page, texto)

        if fila:
            print("✅ Expediente localizado. Visualmente resaltado.")
            await fila.scroll_into_view_if_needed()
            await fila.hover()

        await page.wait_for_timeout(8000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(buscar_expediente())