#refactorizada
from playwright.async_api import Page
from panel_pjn.acciones_pjn.gestion_expedientes.abrir_expediente_desde_fila import abrir_expediente_desde_fila
#from abrir_expediente_desde_fila import abrir_expediente_desde_fila
from panel_pjn.acciones_pjn.gestion_expedientes.extraer_datos_expediente import extraer_datos_expediente
from typing import List, Optional, Dict

async def mostrar_y_elegir_expediente(page: Page, filas: List) -> Optional[Dict]:
    """
    Muestra los expedientes encontrados y permite al usuario seleccionar uno para abrir y extraer datos.

    :param page: Página Playwright actual.
    :param filas: Lista de filas encontradas.
    :return: Diccionario de datos extraídos del expediente seleccionado, o None.
    """

    if not filas:
        print("❌ No hay filas disponibles para seleccionar.")
        return None

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

        seleccion = input("👉 Ingrese el número de opción que desea abrir (0 para cancelar): ")
        try:
            idx_elegido = int(seleccion) - 1
            if idx_elegido == -1:
                print("❌ Operación cancelada por el usuario.")
                return None
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
