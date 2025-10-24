import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))
import asyncio
from playwright.async_api import async_playwright
from panel_pjn.acciones_pjn.urls_pjn import URL_LOGIN, URL_CONSULTAS
from buscar_expediente_por_numero import buscar_expediente_por_numero
from abrir_expediente_desde_fila import abrir_expediente_desde_fila
from extraer_datos_expediente import extraer_datos_expediente

async def probar_busqueda_y_apertura():
    numero = input("📥 Ingrese número de expediente (solo números): ").strip()
    anio = input("📥 Ingrese año del expediente: ").strip()
    caratula_filtro = input("📝 (Opcional) Ingrese carátula exacta: ").strip().lower()

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

        exito = await buscar_expediente_por_numero(page, numero, anio)

        if exito:
            print("🎯 Búsqueda ejecutada. Buscando fila adecuada...")

            tabla = await page.query_selector("table.table-striped")
            if tabla:
                filas = await tabla.query_selector_all("tbody tr")
                fila_elegida = None

                for fila in filas:
                    columnas = await fila.query_selector_all("td")
                    if len(columnas) >= 3:
                        caratula_texto = (await columnas[2].inner_text()).strip().lower()
                        if not caratula_filtro or caratula_texto == caratula_filtro:
                            fila_elegida = fila
                            break

                if fila_elegida:
                    exito_apertura = await abrir_expediente_desde_fila(fila_elegida, page)
                    if exito_apertura:
                        print("✅ Expediente abierto correctamente.")
                        datos = await extraer_datos_expediente(page)
                        if datos:
                            print("📄 Datos extraídos:")
                            for clave, valor in datos.items():
                                print(f"   {clave}: {valor}")
                    else:
                        print("⚠️ No se pudo abrir el expediente.")
                else:
                    print("❌ No se encontró ninguna fila que coincida exactamente con la carátula.")
            else:
                print("⚠️ No se encontró la tabla de resultados.")
        else:
            print("❌ La búsqueda falló o no devolvió resultados.")

        await page.wait_for_timeout(8000)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(probar_busqueda_y_apertura())