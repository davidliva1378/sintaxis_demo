import asyncio
from panel_pjn.acciones_pjn.gestion_expedientes.buscar_expediente_por_numero import buscar_expediente_por_numero
from panel_pjn.acciones_pjn.gestion_expedientes.abrir_expediente_desde_fila import abrir_expediente_desde_fila
from panel_pjn.acciones_pjn.gestion_expedientes.extraer_datos_expediente import extraer_datos_expediente
from playwright.async_api import Page

async def buscar_y_abrir_expediente(page: Page, numero: str, anio: str, caratula: str) -> dict:
    try:
        resultado = {
            "exito": False,
            "datos_expediente": None,
            "tipo": "",
            "mensaje": ""
        }

        # Buscar por formulario
        exito = await buscar_expediente_por_numero(page, numero, anio)

        if not exito:
            resultado["tipo"] = "no_encontrado"
            resultado["mensaje"] = "No se encontraron resultados para el número y año ingresados."
            return resultado

        tabla = await page.query_selector("table.table-striped")
        if not tabla:
            resultado["tipo"] = "no_encontrado"
            resultado["mensaje"] = "No se encontró la tabla de resultados."
            return resultado

        filas = await tabla.query_selector_all("tbody tr")
        if not filas:
            resultado["tipo"] = "no_encontrado"
            resultado["mensaje"] = "No se encontraron filas en la tabla."
            return resultado

        fila_elegida = None
        caratula_filtro = caratula.strip().lower()

        for fila in filas:
            columnas = await fila.query_selector_all("td")
            if len(columnas) >= 3:
                caratula_texto = (await columnas[2].inner_text()).strip().lower()
                if caratula_texto == caratula_filtro:
                    fila_elegida = fila
                    break

        if not fila_elegida:
            resultado["tipo"] = "no_encontrado"
            resultado["mensaje"] = "No se encontró una carátula que coincida exactamente."
            return resultado

        # Intentar abrir el expediente
        abierto = await abrir_expediente_desde_fila(fila_elegida, page)
        if not abierto:
            resultado["tipo"] = "cancelado"
            resultado["mensaje"] = "No se pudo abrir el expediente desde la fila seleccionada."
            return resultado

        datos = await extraer_datos_expediente(page)
        if not datos:
            resultado["tipo"] = "cancelado"
            resultado["mensaje"] = "No se pudieron extraer datos del expediente."
            return resultado

        # Todo OK
        resultado["exito"] = True
        resultado["datos_expediente"] = datos
        resultado["tipo"] = "unico"
        resultado["mensaje"] = "Expediente abierto y datos extraídos correctamente."
        return resultado

    except Exception as e:
        return {
            "exito": False,
            "datos_expediente": None,
            "tipo": "error",
            "mensaje": f"Error inesperado: {str(e)}"
        }