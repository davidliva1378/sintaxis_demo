# Documentación de `Sistema_v3`

Listado de funciones encontradas en el módulo `Sistema_v3` con información disponible para su documentación.

## `operaciones/rf_test_extraccion_completa.py`
- **`async def login_portal(page)`**  
  Inicia sesión en el portal PJN. *Sin docstring.*
- **`async def main()`**  
  Script interactivo de prueba para realizar la extracción completa de un expediente. *Sin docstring.*

## `operaciones/entradas/entradas.py`
- **`async def actualizar_notificaciones_nuevas(page: Page, destino: Optional[str] = None)`**  
  Recorre la bandeja de notificaciones y actualiza el historial en JSON/CSV. *Sin docstring.*
- **`def notificaciones_proximas_a_vencer(destino: Optional[str] = None, horas: int = 48)`**  
  Devuelve las notificaciones cuyo vencimiento ocurre dentro de las próximas `horas`; lee el archivo `historial_notificaciones.json` y filtra las entradas cercanas al vencimiento.

## `operaciones/expedientes/expedientes.py`
- **`async def extraer_expedientes(page, carpeta_salida, delay, nombre_archivo, detener_en_duplicado, guardar_json, fecha_corte, tiempo_maximo_segundos, orden)`**  
  Extrae listados de expedientes según los parámetros indicados y los guarda en disco. *Sin docstring.*

## `operaciones/expedientes/expediente_detalle.py`
- **`async def buscar_expediente_por_numero(page: Page, numero: str) -> bool`**  
  Realiza la búsqueda de un expediente a partir de su número en el portal PJN. *Sin docstring.*
- **`async def abrir_expediente_desde_fila(page: Page, indice: int = 0) -> bool`**  
  Abre el expediente correspondiente a la fila indicada dentro de la tabla de resultados. *Sin docstring.*
- **`async def extraer_datos_expediente(page: Page) -> dict`**  
  Obtiene la información básica del expediente abierto (número, carátula, etc.). *Sin docstring.*
- **`def mostrar_y_elegir_expediente(lista: list[dict]) -> dict`**  
  Muestra una lista de expedientes y permite seleccionar uno para su tratamiento. *Sin docstring.*
- **`async def buscar_expedientes(page: Page, numero: Optional[str] = None, anio: Optional[str] = None, caratula: Optional[str] = None) -> List[ElementHandle]`**  
  *Docstring:* Busca expedientes en el portal PJN y devuelve una lista de filas encontradas (parámetros: `page`, `numero`, `anio`, `caratula`).

## `operaciones/expedientes/utils.py`
- **`def limpiar_texto(texto)`**  
  Normaliza cadenas eliminando espacios y caracteres extraños. *Sin docstring.*
- **`def normalizar_texto(t)`**  
  Convierte texto a una forma normalizada para comparaciones. *Sin docstring.*

## `operaciones/expedientes/ref_expedientes.py`
- **`async def extraer_expedientes(page, carpeta_salida, delay, nombre_archivo, detener_en_duplicado, guardar_json, fecha_corte, tiempo_maximo_segundos, orden)`**  
  Rutina alternativa para extraer expedientes. *Sin docstring.*
- **`async def extraer_datos_expediente(page)`**  
  Obtiene los datos del expediente actualmente abierto. *Sin docstring.*
- **`async def abrir_expediente_desde_fila(fila, page)`**  
  Abre el expediente asociado a la fila seleccionada. *Sin docstring.*
- **`async def mostrar_y_elegir_expediente(page: Page, filas: List) -> Optional[Dict]`**  
  *Docstring:* Muestra los expedientes encontrados y permite elegir uno; retorna un diccionario con los datos extraídos.
- **`async def buscar_expediente_por_numero(page: Page, numero: str, anio: str, timeout: int = 8000) -> tuple[bool, str]`**  
  Busca un expediente específico combinando número y año, devolviendo resultado y motivo. *Sin docstring.*
- **`async def buscar_expedientes(page: Page, numero: Optional[str] = None, anio: Optional[str] = None, caratula: Optional[str] = None) -> List`**  
  *Docstring:* Busca expedientes en el portal PJN y devuelve una lista de filas encontradas (parámetros: `page`, `numero`, `anio`, `caratula`).

## `operaciones/actuaciones/actuaciones_utils.py`
- **`def limpiar_texto(texto: str) -> str`**  
  Limpieza de cadenas utilizadas en actuaciones. *Sin docstring.*
- **`def normalizar_fecha(texto: str) -> str`**  
  Normaliza fechas al formato esperado. *Sin docstring.*
- **`def generar_hash_archivo(fecha: str, tipo: str, detalle: str, longitud: int = 6) -> str`**  
  Crea un identificador hash a partir de los datos de la actuación. *Sin docstring.*

## `operaciones/actuaciones/actuaciones.py`
- **`async def aviso_si_tarda(idx, segundos)`**  
  *Docstring:* Muestra un aviso si la descarga de una actuación demora más de `segundos`.
- **`async def descargar_archivos_actuaciones(page: Page, actuaciones: list, carpeta_destino: str)`**  
  *Docstring:* Descarga los archivos adjuntos para cada actuación de la lista.
- **`async def extraer_actuaciones_pagina(page_expediente, expediente_datos, indice_inicial=1)`**  
  *Docstring:* Obtiene las actuaciones listadas en la página actual del expediente.
- **`async def obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos, carpeta_destino="Actuaciones")`**  
  *Docstring:* Recorre todas las páginas de actuaciones y reúne los datos en una lista única, guardándolos en `carpeta_destino`.
- **`async def extraer_actuaciones_completas(page_expediente, expediente_datos: dict, incluir_historicas: bool = True, directorio_base: str = "ActuacionesCompletas") -> tuple[list[dict], list[dict], str | None]`**  
  *Docstring:* Extrae actuaciones actuales e históricas (opcional), genera JSON unificado y añade metadatos como `EsHistorica` y `Descargado`.
- **`async def descargar_archivos_de_json(page, carpeta_destino: str)`**  
  *Docstring:* Lee el JSON unificado del expediente, descarga archivos pendientes y actualiza el estado de cada actuación.
- **`async def extraer_actuaciones_historicas(page_expediente, expediente_datos, indice_inicial=1)`**  
  *Docstring:* Recupera las actuaciones históricas del expediente indicado.

## `operaciones/actuaciones/rf_actuaciones.py`
- **`async def extraer_actuaciones_historicas(page_expediente, expediente_datos, indice_inicial=1)`**  
  Extrae actuaciones históricas usando una versión alternativa del flujo. *Sin docstring.*
- **`async def extraer_actuaciones_pagina(page_expediente, expediente_datos, indice_inicial=1)`**  
  Obtiene las actuaciones de la página actual. *Sin docstring.*
- **`async def obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos, carpeta_destino="Actuaciones")`**  
  Recorre todas las páginas de actuaciones. *Sin docstring.*
- **`async def extraer_actuaciones_completas(page_expediente, expediente_datos: dict, incluir_historicas: bool = True, directorio_base: str = "ActuacionesCompletas") -> tuple[list[dict], list[dict], str | None]`**  
  *Docstring:* Variante que extrae actuaciones actuales e históricas y genera un JSON final.
- **`async def aviso_si_tarda(idx, segundos)`**  
  Aviso de descarga prolongada. *Sin docstring.*
- **`async def descargar_archivos_actuaciones(page: Page, actuaciones: list, carpeta_destino: str)`**  
  Descarga archivos adjuntos. *Sin docstring.*
- **`async def descargar_archivos_de_json(page, carpeta_destino: str)`**  
  *Docstring:* Lee el JSON de actuaciones consolidado y descarga los archivos faltantes marcándolos como descargados.

