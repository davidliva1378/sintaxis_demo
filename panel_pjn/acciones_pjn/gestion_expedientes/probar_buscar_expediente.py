import asyncio
from playwright.async_api import async_playwright
from panel_pjn.acciones_pjn.urls_pjn import URL_LOGIN, URL_CONSULTAS
from busqueda_expediente import buscar_expedientes
from mostrar_y_elegir_expediente import mostrar_y_elegir_expediente


# Usuario y contraseña para pruebas (hardcodeado)
USUARIO = "20213071662"
CONTRASENA = "surrey1970"

async def login_portal(page):
    await page.goto(URL_LOGIN)
    await page.fill("#username", USUARIO)
    await page.fill("#password", CONTRASENA)
    await page.click("#kc-login")
    try:
        await page.wait_for_selector("text=Consultas", timeout=8000)
        print("✅ Login exitoso.")
        return True
    except Exception:
        print("❌ Error de login: no se detectó la página de inicio correctamente.")
        return False

async def main():
    numero = input("Ingrese número de expediente (opcional, ENTER para omitir): ").strip()
    anio = input("Ingrese año de expediente (opcional, ENTER para omitir): ").strip()
    caratula = input("Ingrese carátula exacta (opcional, ENTER para omitir): ").strip()

    if numero == "":
        numero = None
    if anio == "":
        anio = None
    if caratula == "":
        caratula = None

    async with async_playwright() as p:
        navegador = await p.chromium.launch(headless=False)
        page = await navegador.new_page()

        if not await login_portal(page):
            await navegador.close()
            return

        await page.goto(URL_CONSULTAS)

        filas = await buscar_expedientes(page, numero, anio, caratula)

        if not filas:
            print("❌ No se encontraron expedientes.")
        else:
            datos = await mostrar_y_elegir_expediente(page, filas)
            if datos:
                print("\n✅ Datos extraídos del expediente:")
                for clave, valor in datos.items():
                    print(f"{clave}: {valor}")
            else:
                print("❌ No se pudo extraer información del expediente.")

        await navegador.close()

if __name__ == "__main__":
    asyncio.run(main())
