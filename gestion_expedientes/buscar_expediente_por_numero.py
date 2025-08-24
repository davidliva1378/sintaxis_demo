from playwright.async_api import Page, TimeoutError
import asyncio

async def buscar_expediente_por_numero(page: Page, numero: str, anio: str, timeout: int = 8000) -> tuple[bool, str]:
    try:
        print(f"🔎 Buscando expediente {numero}/{anio} usando el formulario...")

        # Mostrar el panel de búsqueda
        await page.click("a[href='#collapseOne']")
        await page.wait_for_selector("#collapseOne.collapse.in", timeout=5000)

        # Completar número y año
        await page.fill("#j_idt83\:consultaExpediente\:j_idt116\:numero", numero)
        await page.fill("#j_idt83\:consultaExpediente\:j_idt118\:anio", anio)

        # Click en Consultar
        await page.click("#j_idt83\:consultaExpediente\:consultaFiltroSearchButtonSAU")

        # Intentar detectar mensaje de "no encontrado" primero
        try:
            await page.wait_for_selector("text=No se han encontrado expedientes", timeout=3000)
            print(f"❗ Expediente {numero}/{anio} no encontrado.")
            return False, "no_encontrado"
        except TimeoutError:
            pass  # No hay mensaje de error, seguir esperando la tabla

        # Esperar la tabla de resultados
        await page.wait_for_selector("table.table-striped", timeout=timeout)
        print(f"✅ Resultados cargados correctamente para {numero}/{anio}.")
        return True, "OK"

    except TimeoutError:
        print(f"⏳ Tiempo de espera agotado buscando expediente {numero}/{anio}.")
        return False, "timeout"

    except Exception as e:
        print(f"❌ Error general buscando expediente {numero}/{anio}: {e}")
        return False, "error"
