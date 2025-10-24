
import asyncio
from playwright.async_api import async_playwright

from panel_pjn.acciones_pjn.urls_pjn import URL_LOGIN, URL_CONSULTAS
from gestion_expedientes.busqueda_expediente import buscar_expedientes
from gestion_expedientes.mostrar_y_elegir_expediente import mostrar_y_elegir_expediente
from gestion_actuaciones.extraccion_v2 import obtener_actuaciones_todas_paginas_async
from panel_pjn.acciones_pjn.gestion_actuaciones.bk.descarga import descargar_archivos_actuaciones

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

        print("\n📄 Extrayendo actuaciones (paginadas)...")
        actuaciones, error = await obtener_actuaciones_todas_paginas_async(page, datos_expediente)

        if error:
            print(f"❌ Error durante la extracción: {error}")
        elif actuaciones:
            print(f"✅ Se extrajeron {len(actuaciones)} actuaciones.")
            for act in actuaciones:
                print(f"{act.get('Fecha', '-')}: {act.get('Detalle', '-')} | Tipo: {act.get('Tipo', '-')}")

            carpeta_destino = f"Actuaciones/{datos_expediente['numero'].replace('/', '_')}"
            import os
            if not os.path.exists(carpeta_destino):
                os.makedirs(carpeta_destino)

            print("\n📥 Iniciando descarga de archivos adjuntos...")
            await descargar_archivos_actuaciones(page, actuaciones, carpeta_destino)
            print("✅ Descarga finalizada.")
        else:
            print("⚠️ No se encontraron actuaciones.")

        await navegador.close()

if __name__ == "__main__":
    asyncio.run(main())
