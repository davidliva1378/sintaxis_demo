from .listar_y_filtrar import buscar_expedientes
from .abrir_desde_fila import abrir_expediente_desde_fila
from .extraer_detalle import extraer_datos_expediente

async def buscar_y_cargar_expediente(page, *, numero=None, anio=None, caratula=None):
    """
    1) Busca (por numero+anio o caratula)
    2) Abre el primer resultado
    3) Extrae y devuelve los datos del expediente (dict) o None si no hay resultados
    """
    filas = await buscar_expedientes(page, numero=numero, anio=anio, caratula=caratula)
    if not filas:
        return None
    ok, motivo = await abrir_expediente_desde_fila(page, filas[0])
    if not ok:
        raise RuntimeError(f"No se pudo abrir el expediente: {motivo}")
    return await extraer_datos_expediente(page)
