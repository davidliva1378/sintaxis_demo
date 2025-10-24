from playwright.async_api import Page, TimeoutError
from buscar_expediente_por_numero import buscar_expediente_por_numero
from seleccionar_y_abrir_expediente import seleccionar_y_abrir_expediente
from abrir_expediente_desde_fila import abrir_expediente_desde_fila
from extraer_datos_expediente import extraer_datos_expediente
from typing import Optional, Dict, Tuple

async def buscar_y_abrir_expediente(page: Page, numero: Optional[str] = None, anio: Optional[str] = None, caratula: Optional[str] = None) -> Optional[Dict]:
    """
    Busca y abre un expediente en el portal PJN.
    - Si se encuentra un solo resultado: abre automáticamente.
    - Si hay múltiples resultados: permite al usuario elegir.

    :param page: Página de navegador Playwright actual.
    :param numero: Número del expediente (opcional).
    :param anio: Año del expediente (opcional).
    :param caratula: Carátula esperada (opcional).
    :return: Diccionario de datos extraídos del expediente, o None si falla.
    """

    if not numero and not caratula:
        print("❌ Se debe proporcionar al menos un número o una carátula para buscar.")
        return None

    # Realizar búsqueda
    exito, motivo = await buscar_expediente_por_numero(page, numero, anio)

    if not exito:
        if motivo == "no_encontrado":
            print("❗ No se encontraron expedientes para los datos ingresados.")
        elif motivo == "timeout":
            print("⏳ La búsqueda tardó demasiado en cargar.")
        else:
            print(f"❌ Error inesperado durante la búsqueda: {motivo}")
        return None

    # Buscar tabla de resultados
    tabla = await page.query_selector("table.table-striped")
    if not tabla:
        print("⚠️ No se encontró la tabla de resultados.")
        return None

    filas = await tabla.query_selector_all("tbody tr")
    if not filas:
        print("❌ No se encontraron filas en la tabla de resultados.")
        return None

    # Si hay solo una fila
    if len(filas) == 1:
        print("✅ Solo un expediente encontrado. Abriendo directamente...")
        fila = filas[0]
    else:
        print("🔎 Se encontraron múltiples expedientes:")
        opciones = []

        for idx, fila in enumerate(filas, start=1):
            columnas = await fila.query_selector_all("td")
            if len(columnas) >= 3:
                nro = (await columnas[0].inner_text()).strip()
                anio_fila = (await columnas[1].inner_text()).strip()
                caratula_fila = (await columnas[2].inner_text()).strip()
                print(f"[{idx}] Número: {nro} / Año: {anio_fila} / Carátula: {caratula_fila}")
                opciones.append(fila)

        seleccion = input("👉 Ingrese el número de opción que desea abrir: ")
        try:
            idx_elegido = int(seleccion) - 1
            fila = opciones[idx_elegido]
        except (ValueError, IndexError):
            print("❌ Selección inválida.")
            return None

    # Abrir el expediente seleccionado
    exito_apertura = await abrir_expediente_desde_fila(fila, page)
    if not exito_apertura:
        print("⚠️ No se pudo abrir el expediente seleccionado.")
        return None

    # Extraer datos
    datos = await extraer_datos_expediente(page)
    if datos:
        print("✅ Datos extraídos correctamente del expediente.")
        return datos
    else:
        print("⚠️ No se pudieron extraer datos luego de abrir el expediente.")
        return None
