import asyncio
#from .extraer_datos_expediente import extraer_datos_expediente
#refactorizada
from panel_pjn.acciones_pjn.gestion_expedientes.extraer_datos_expediente import extraer_datos_expediente


async def abrir_expediente_desde_fila(fila, page):
    if not fila:
        print("❌ No se proporcionó ninguna fila válida.")
        return False

    enlace = await fila.query_selector("a")
    if enlace:
        print("👁 Haciendo clic para abrir el expediente...")
        await enlace.click()
        await page.wait_for_load_state("load")
        await page.wait_for_timeout(2000)

        # Verificación: intentar extraer datos del expediente
        datos = await extraer_datos_expediente(page)
        if datos:
            print("✅ Datos del expediente extraídos correctamente.")
            return True
        else:
            print("⚠️ No se pudieron extraer datos. Posible error de apertura.")
            return False
    else:
        print("⚠️ No se encontró enlace para abrir el expediente en la fila.")
        return False