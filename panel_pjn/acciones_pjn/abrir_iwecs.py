import asyncio
from urls_pjn import URL_LOGIN, URL_IWECS

from playwright.async_api import async_playwright

async def acceso_iwecs():
    USUARIO = "20213071662"
    CLAVE = "surrey1970"

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()

        await page.goto(URL_LOGIN)
        await page.wait_for_selector("input[name='username']")
        await page.fill("input[name='username']", USUARIO)
        await page.fill("input[name='password']", CLAVE)
        await page.click("#kc-login")
        await page.wait_for_selector("text='Menú'", timeout=10000)
        print("✅ Login exitoso")

        await page.goto(URL_IWECS)
        await page.wait_for_load_state("load")
        print(f"✅ Sección IWECS abierta: {page.url}")

        await page.wait_for_timeout(15000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(acceso_iwecs())