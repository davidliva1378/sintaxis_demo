
import asyncio
from playwright.async_api import async_playwright

from panel_pjn.acciones_pjn.urls_pjn import URL_LOGIN, URL_CONSULTAS
from gestion_expedientes.busqueda_expediente import buscar_expedientes
from gestion_expedientes.mostrar_y_elegir_expediente import mostrar_y_elegir_expediente
from panel_pjn.acciones_pjn.gestion_actuaciones.bk.historicas import extraer_actuaciones_historicas

USUARIO = "20213071662"
CONTRASENA = "surrey1970"

async def login_portal(page):
    try:
        await page.goto(URL_LOGIN)
    except Exception as e:
        print(f"❌ Error de conexión al intentar acceder al portal: {e}")
        return False

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
    numero = input("Número de expediente: ").strip()
    anio = input("Año: ").strip()
    caratula = input("Carátula exacta (opcional): ").strip() or None

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
            await navegador.close()
            return

        datos_expediente = await mostrar_y_elegir_expediente(page, filas)
        if not datos_expediente:
            print("❌ No se pudo abrir ni extraer el expediente.")
            await navegador.close()
            return

        print("\n🕰️ Buscando actuaciones históricas...")
        historicas, error = await extraer_actuaciones_historicas(page, datos_expediente)

        if error:
            print(f"❌ Error al extraer históricas: {error}")
        elif historicas:
            print(f"📜 Se extrajeron {len(historicas)} actuaciones históricas:")
            for act in historicas:
                print(f"🕰️ {act['Fecha']} - {act['Tipo']} - {act['Detalle'][:60]}...")
        else:
            print("📭 No se encontraron actuaciones históricas.")

        await navegador.close()

if __name__ == "__main__":
    asyncio.run(main())
