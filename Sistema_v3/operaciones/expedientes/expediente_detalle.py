# sistema/operaciones/expediente_detalle.py

"""
Funciones específicas para operar sobre un expediente puntual:
- Búsqueda por número
- Apertura desde fila
- Extracción de datos visibles
"""

from playwright.async_api import Page

# Buscar expediente por número
async def buscar_expediente_por_numero(page: Page, numero: str) -> bool:
    try:
        input_busqueda = await page.query_selector("input[type='text']")
        if not input_busqueda:
            print("❌ Campo de búsqueda no encontrado.")
            return False
        await input_busqueda.fill(numero)
        await page.keyboard.press("Enter")
        await page.wait_for_timeout(2000)
        print(f"🔍 Búsqueda realizada para: {numero}")
        return True
    except Exception as e:
        print(f"⚠️ Error en búsqueda: {e}")
        return False


# Abrir expediente desde una fila de tabla
async def abrir_expediente_desde_fila(page: Page, indice: int = 0) -> bool:
    try:
        filas = await page.query_selector_all("table.table-striped tbody tr")
        if not filas or indice >= len(filas):
            print(f"❌ No se encontró la fila {indice}.")
            return False
        await filas[indice].click()
        await page.wait_for_load_state("domcontentloaded")
        print(f"📂 Expediente abierto desde fila {indice}")
        return True
    except Exception as e:
        print(f"⚠️ Error al abrir expediente: {e}")
        return False


# Extraer datos visibles del expediente abierto
async def extraer_datos_expediente(page: Page) -> dict:
    try:
        caratula_elem = await page.query_selector("span#caratula")
        numero_elem = await page.query_selector("span#numeroExpediente")
        jurisdiccion_elem = await page.query_selector("span#jurisdiccion")

        return {
            "numero": await numero_elem.inner_text() if numero_elem else "N/D",
            "caratula": await caratula_elem.inner_text() if caratula_elem else "N/D",
            "jurisdiccion": await jurisdiccion_elem.inner_text() if jurisdiccion_elem else "N/D"
        }
    except Exception as e:
        print(f"⚠️ Error al extraer datos del expediente: {e}")
        return {}


# Mostrar lista y elegir un expediente por índice
def mostrar_y_elegir_expediente(lista: list[dict]) -> dict:
    if not lista:
        print("📭 No hay expedientes para elegir.")
        return {}
    for i, exp in enumerate(lista):
        print(f"{i + 1}. {exp.get('numero')} - {exp.get('caratula')}")
    try:
        indice = int(input("Seleccione un expediente por número: ")) - 1
        if 0 <= indice < len(lista):
            return lista[indice]
        print("❌ Selección inválida.")
    except ValueError:
        print("⚠️ Entrada inválida.")
    return {}
# Búsqueda avanzada: por número, año y/o carátula
from typing import Optional, List
from playwright.async_api import ElementHandle

async def buscar_expedientes(
    page: Page,
    numero: Optional[str] = None,
    anio: Optional[str] = None,
    caratula: Optional[str] = None
) -> List[ElementHandle]:
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

    # Se asume que buscar_expediente_por_numero fue redefinida para aceptar también año
    exito = await buscar_expediente_por_numero(page, numero)
    if not exito:
        print("❗ No se encontraron expedientes para los datos ingresados.")
        return []

    tabla = await page.query_selector("table.table-striped")
    if not tabla:
        print("⚠️ No se encontró la tabla de resultados.")
        return []

    filas = await tabla.query_selector_all("tbody tr")
    print(f"🔎 Se encontraron {len(filas)} fila(s) en la tabla de resultados.")
    return filas