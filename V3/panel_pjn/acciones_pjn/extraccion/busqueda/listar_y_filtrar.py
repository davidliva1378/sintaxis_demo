from playwright.async_api import Page, TimeoutError
from panel_pjn.acciones_pjn.gestion_expedientes.buscar_expediente_por_numero import buscar_expediente_por_numero

#from buscar_expediente_por_numero import buscar_expediente_por_numero
from typing import Optional, List

async def buscar_expedientes(page: Page, numero: Optional[str] = None, anio: Optional[str] = None, caratula: Optional[str] = None) -> List:
    """
    Busca expedientes en el portal PJN y devuelve una lista de filas encontradas.

    :param page: Página Playwright actual.
    :param numero: Número de expediente (opcional).
    :param anio: Año de expediente (opcional).
    :param caratula: Carátula filtro (opcional).
    :return: Lista de filas (ElementHandle) encontradas.
    """

    if not numero and not caratula:
        print("❌ Se debe proporcionar al menos un número o una carátula para buscar.")
        return []

    exito, motivo = await buscar_expediente_por_numero(page, numero, anio)

    if not exito:
        if motivo == "no_encontrado":
            print("❗ No se encontraron expedientes para los datos ingresados.")
        elif motivo == "timeout":
            print("⏳ La búsqueda tardó demasiado en cargar.")
        else:
            print(f"❌ Error inesperado durante la búsqueda: {motivo}")
        return []

    tabla = await page.query_selector("table.table-striped")
    if not tabla:
        print("⚠️ No se encontró la tabla de resultados.")
        return []

    filas = await tabla.query_selector_all("tbody tr")
    if not filas:
        print("❌ No se encontraron filas en la tabla de resultados.")
        return []

    # Si se pasa una carátula, filtrar solo las filas que coincidan
    if caratula:
        filas_filtradas = []
        for fila in filas:
            columnas = await fila.query_selector_all("td")
            if len(columnas) >= 3:
                caratula_texto = (await columnas[2].inner_text()).strip().lower()
                if caratula_texto == caratula.lower():
                    filas_filtradas.append(fila)
        return filas_filtradas

    return filas
