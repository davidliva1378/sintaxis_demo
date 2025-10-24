from playwright.async_api import Page
from abrir_expediente_desde_fila import abrir_expediente_desde_fila
from extraer_datos_expediente import extraer_datos_expediente
from typing import Optional, Tuple, Dict

async def seleccionar_y_abrir_expediente(page: Page, caratula_filtro: Optional[str] = None) -> Tuple[bool, Optional[Dict]]:
    """
    Busca una fila en la tabla de resultados de expedientes.
    Si encuentra una fila que coincida (o cualquiera si no hay filtro), la abre y extrae los datos del expediente.

    :param page: Página Playwright actual.
    :param caratula_filtro: Carátula exacta esperada (opcional).
    :return: (exito, datos)
             - exito: True si se abrió y extrajo correctamente, False en caso contrario.
             - datos: Diccionario de datos extraídos si exito=True, None si exito=False.
    """
    print("🔎 Buscando fila adecuada en la tabla de resultados...")

    tabla = await page.query_selector("table.table-striped")
    if not tabla:
        print("⚠️ No se encontró la tabla de resultados.")
        return False, None

    filas = await tabla.query_selector_all("tbody tr")
    fila_elegida = None

    for fila in filas:
        columnas = await fila.query_selector_all("td")
        if len(columnas) >= 3:
            caratula_texto = (await columnas[2].inner_text()).strip().lower()
            if not caratula_filtro or caratula_texto == caratula_filtro.lower():
                fila_elegida = fila
                break

    if not fila_elegida:
        print("❌ No se encontró ninguna fila que coincida exactamente con la carátula proporcionada.")
        return False, None

    exito_apertura = await abrir_expediente_desde_fila(fila_elegida, page)
    if not exito_apertura:
        print("⚠️ No se pudo abrir el expediente desde la fila seleccionada.")
        return False, None

    datos = await extraer_datos_expediente(page)
    if datos:
        print("✅ Expediente abierto y datos extraídos correctamente.")
        return True, datos
    else:
        print("⚠️ No se pudieron extraer datos luego de abrir el expediente.")
        return False, None
