import asyncio
import os
from playwright.async_api import async_playwright
from panel_pjn.acciones_pjn.urls_pjn import URL_LOGIN, URL_CONSULTAS
from gestion_expedientes.busqueda_expediente import buscar_expedientes #ref
from gestion_expedientes.mostrar_y_elegir_expediente import mostrar_y_elegir_expediente
from panel_pjn.acciones_pjn.gestion_actuaciones.extraccion_completa import extraer_actuaciones_completas
from panel_pjn.acciones_pjn.gestion_actuaciones.descarga_v2 import descargar_archivos_de_json

#from panel_pjn.acciones_pjn.gestion_actuaciones.extraccion_completa import extraer_actuaciones_completas, descargar_archivos_de_json

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

        print("\n📂 Extrayendo actuaciones actuales e históricas...")
        actuales, historicas, error = await extraer_actuaciones_completas(
            page_expediente=page,
            expediente_datos=datos_expediente,
            incluir_historicas=True
        )

        if error:
            print(f"❌ Error en la extracción: {error}")
        else:
            print(f"✅ Se extrajeron {len(actuales)} actuaciones actuales.")
            print(f"📜 Se extrajeron {len(historicas)} actuaciones históricas.")
            numero_normalizado = datos_expediente['numero'].replace('/', '_')
            carpeta = os.path.join("ActuacionesCompletas", numero_normalizado)
            print(f"📁 JSONs guardados en: {carpeta}")

            descargar = input("\n¿Deseás descargar los archivos vinculados? (s/n): ").strip().lower()
            if descargar == "s":
                await descargar_archivos_de_json(page, carpeta)

        await navegador.close()

if __name__ == "__main__":
    asyncio.run(main())
