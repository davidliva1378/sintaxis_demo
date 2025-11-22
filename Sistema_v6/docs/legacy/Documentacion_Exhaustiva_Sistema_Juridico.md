# 📘 Documentación Exhaustiva de Funciones - Sistema Jurídico `Sistema_v2`

Cada módulo se documenta con sus funciones, indicando si son asíncronas, los parámetros, valores de retorno y descripción (si tiene docstring).


## 🔹 Módulo: `main.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `core/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `core/flujo_inicial/recopilar_datos_iniciales.py`

### ▸ `async def recopilar_datos_iniciales()`
- **Retorna:** `—`
- **Descripción:** Realiza la extracción inicial completa: - Expedientes - Notificaciones - Actuaciones por expediente (sin descargar archivos)


## 🔹 Módulo: `core/flujo_inicial/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `core/gestion_expedientes/comparar_expedientes.py`

### ▸ `def comparar_con_base(json_actual, base_json)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/gestion_expedientes/comparar_expedientes_monitor.py`

### ▸ `def comparar_expedientes_monitor(json_actual_path, base_json_path, carpeta_salida)`
- **Retorna:** `—`
- **Descripción:** Compara dos archivos JSON de expedientes y guarda un informe de diferencias.  :param json_actual_path: Ruta al archivo JSON actual extraído del portal. :param base_json_path: Ruta al archivo JSON base (histórico o simulado). :param carpeta_salida: Carpeta donde guardar el informe de comparación. :return: Tupla (nuevos, modificados, eliminados)


## 🔹 Módulo: `core/gestion_expedientes/guardar_comparacion.py`

### ▸ `def guardar_comparacion_json(nuevos, modificados, eliminados, carpeta_destino)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/gestion_expedientes/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `core/modulos_monitor/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `core/modulos_monitor/expedientes/monitoreo_automatico_habilitado.py`

### ▸ `def monitoreo_automatico_habilitado(config_path)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/expedientes/monitor_expedientes_async.py`

### ▸ `def registrar_log(mensaje)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def run()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def verificar_async()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def verificar_automaticamente()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def procesar_resultado(datos)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def actualizar_modo_monitor(nuevo_modo)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def verificar()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def iniciar_verificacion()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def reiniciar_timer()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def procesar_resultado(datos)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def ver_estado_sesion()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/expedientes/monitor_expedientes_async_con_rango.py`

### ▸ `def registrar_log(mensaje)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def run()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def verificar_async()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def verificar_automaticamente()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def verificar()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def iniciar_verificacion()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def procesar_resultado(datos)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def ver_estado_sesion()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/expedientes/obtener_intervalo_monitor.py`

### ▸ `def obtener_intervalo_monitor(config_path)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/expedientes/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `core/modulos_monitor/expedientes/bk/monitor_expedientes.py`

### ▸ `def registrar_log(texto)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def monitor_expedientes_robusto()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/expedientes/bk/monitor_expedientes_async_bk.py`

### ▸ `def registrar_log(mensaje)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def run()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def verificar_async()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def verificar()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def iniciar_verificacion()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def procesar_resultado(datos)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def ver_estado_sesion()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/expedientes/bk/monitor_expedientes_clasico_debug.py`

### ▸ `def registrar_log(mensaje)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def monitor_expedientes()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/expedientes/bk/monitor_expedientes_clasico_respetado.py`

### ▸ `def registrar_log(mensaje)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def monitor_expedientes()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/expedientes/bk/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `core/modulos_monitor/expedientes_modular/extraer_expedientes.py`

### ▸ `async def extraer_expedientes(page, carpeta_salida, delay, nombre_archivo, detener_en_duplicado, guardar_json, fecha_corte, tiempo_maximo_segundos)`
- **Retorna:** `tuple[list[dict], Optional[str], str]`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/expedientes_modular/extraer_expedientes_por_fecha.py`

### ▸ `async def ir_a_consultas_tras_login(fecha_corte)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/expedientes_modular/prueba_extraer_expedientes_fecha.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `core/modulos_monitor/expedientes_modular/verificacion_expedientes.py`

### ▸ `def registrar_log(mensaje)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def __init__(carpeta_salida)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def run()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def verificar_async()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/expedientes_modular/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `core/modulos_monitor/expedientes_modular/bk/extraer_expedientes_bk.py`

### ▸ `async def extraer_expedientes(page, carpeta_salida, delay, nombre_archivo, detener_en_duplicado, guardar_json, tiempo_maximo_segundos)`
- **Retorna:** `tuple[list[dict], Optional[str], str]`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/expedientes_modular/bk/verificacion_expedientes_bk.py`

### ▸ `def registrar_log(mensaje)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def run()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def verificar_async()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/general/monitor_general.py`

### ▸ `def run()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def verificar_async()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def cargar_config()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def esta_en_horario_laboral()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def obtener_intervalo()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def iniciar_temporizadores()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def verificar_expedientes()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def verificar_notificaciones()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def procesar_resultado_expedientes(datos)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def procesar_resultado_notificaciones(nuevas)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def respaldar_resultados_verificacion()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def cambiar_modo(nuevo_modo)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def actualizar_modo_seleccionado()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def estado_sesion()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def forzar_login()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def salir()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def comparar_expedientes()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/general/bk/monitor_general_bk.py`

### ▸ `def run()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def verificar_async()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def run()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def verificar_async()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def cargar_config()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def esta_en_horario_laboral()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def obtener_intervalo()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def iniciar_temporizadores()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def verificar_expedientes()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def verificar_notificaciones()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def procesar_resultado_expedientes(datos)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def procesar_resultado_notificaciones(nuevas)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def cambiar_modo(nuevo_modo)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def actualizar_modo_seleccionado()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def estado_sesion()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def forzar_login()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def salir()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/notificaciones/monitor_notificaciones_async.py`

### ▸ `def cargar_config()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def esta_en_horario_laboral(config)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def obtener_intervalo(config)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def run()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def verificar_async()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def actualizar_modo_seleccionado()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def cambiar_modo(nuevo_modo)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def iniciar_temporizador()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def verificar()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def procesar_resultado_verificacion(nuevas)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def mostrar_estado()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def salir()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def forzar_nuevo_login()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `core/modulos_monitor/notificaciones/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `notificaciones_v2/main_notificaciones.py`

### ▸ `def main()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `notificaciones_v2/notificaciones_control_v4_async.py`

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def normalizar_texto(t)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def actualizar_notificaciones_nuevas(page, destino)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `notificaciones_v2/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `notificaciones_v2/bk/main_notificaciones.py`

### ▸ `def main()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `notificaciones_v2/bk/notificaciones_control_v4.py`

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def normalizar_texto(t)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def actualizar_notificaciones_nuevas(page)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `notificaciones_v2/bk/notificaciones_control_v4_bk.py`

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def verificar()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def salir()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/panel_pjn_sync.py`

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def abrir_script_externo(ruta)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `panel_pjn/acciones_pjn/abrir_autorizados.py`

### ▸ `async def acceso_autorizados()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/abrir_consultas.py`

### ▸ `async def abrir_consultas()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/abrir_deox.py`

### ▸ `async def acceso_deox()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/abrir_escritos.py`

### ▸ `async def acceso_escritos()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/abrir_iwecs.py`

### ▸ `async def acceso_iwecs()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/abrir_notificaciones.py`

### ▸ `async def acceso_notificaciones()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/test_busqueda_y_descarga.py`

### ▸ `async def login_portal(page)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def main()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/test_busqueda_y_descarga_historicas.py`

### ▸ `async def login_portal(page)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def main()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/test_extraccion_completa.py`

### ▸ `async def login_portal(page)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def main()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/urls_pjn.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `panel_pjn/acciones_pjn/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_actuaciones/descarga_v2.py`

### ▸ `async def descargar_archivos_de_json(page, carpeta_destino)`
- **Retorna:** `—`
- **Descripción:** Lee el archivo unificado desde la carpeta del expediente y descarga los archivos vinculados usando Playwright. Marca las actuaciones descargadas como "Descargado": true.


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_actuaciones/extraccion_completa.py`

### ▸ `async def extraer_actuaciones_completas(page_expediente, expediente_datos, incluir_historicas, directorio_base)`
- **Retorna:** `tuple[list[dict], list[dict], str | None]`
- **Descripción:** Extrae actuaciones actuales e históricas (opcional) de un expediente y las guarda como JSON. También genera un único archivo con estructura detallada, campo EsHistorica y Descargado.


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_actuaciones/extraccion_v2.py`

### ▸ `async def extraer_actuaciones_pagina(page_expediente, expediente_datos, indice_inicial)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos, carpeta_destino)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_actuaciones/utilidades.py`

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `str`
- **Descripción:** Sin descripción

### ▸ `def normalizar_fecha(texto)`
- **Retorna:** `str`
- **Descripción:** Sin descripción

### ▸ `def generar_hash_archivo(fecha, tipo, detalle, longitud)`
- **Retorna:** `str`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_actuaciones/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_actuaciones/bk/descarga.py`

### ▸ `async def aviso_si_tarda(idx, segundos)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def descargar_archivos_actuaciones(page, actuaciones, carpeta_destino)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_actuaciones/bk/descarga_bk.py`

### ▸ `async def descargar_archivos_actuaciones(page, actuaciones, carpeta_destino)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_actuaciones/bk/extraccion_bk.py`

### ▸ `async def extraer_actuaciones_pagina(page_expediente, expediente_datos)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos, carpeta_destino)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_actuaciones/bk/historicas.py`

### ▸ `async def extraer_actuaciones_historicas(page_expediente, expediente_datos, indice_inicial)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_actuaciones/bk/utilidades_bk.py`

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `str`
- **Descripción:** Sin descripción

### ▸ `def normalizar_fecha(texto)`
- **Retorna:** `str`
- **Descripción:** Sin descripción

### ▸ `def generar_hash_archivo(fecha, tipo, detalle, longitud)`
- **Retorna:** `str`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_actuaciones/bk/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/abrir_expediente_desde_fila.py`

### ▸ `async def abrir_expediente_desde_fila(fila, page)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/buscar_expediente_por_numero.py`

### ▸ `async def buscar_expediente_por_numero(page, numero, anio, timeout)`
- **Retorna:** `tuple[bool, str]`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/busqueda_expediente.py`

### ▸ `async def buscar_expedientes(page, numero, anio, caratula)`
- **Retorna:** `List`
- **Descripción:** Busca expedientes en el portal PJN y devuelve una lista de filas encontradas.  :param page: Página Playwright actual. :param numero: Número de expediente (opcional). :param anio: Año de expediente (opcional). :param caratula: Carátula filtro (opcional). :return: Lista de filas (ElementHandle) encontradas.


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/extraer_datos_expediente.py`

### ▸ `async def extraer_datos_expediente(page)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/mostrar_y_elegir_expediente.py`

### ▸ `async def mostrar_y_elegir_expediente(page, filas)`
- **Retorna:** `Optional[Dict]`
- **Descripción:** Muestra los expedientes encontrados y permite al usuario seleccionar uno para abrir y extraer datos.  :param page: Página Playwright actual. :param filas: Lista de filas encontradas. :return: Diccionario de datos extraídos del expediente seleccionado, o None.


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/probar_buscar_expediente.py`

### ▸ `async def login_portal(page)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def main()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/bk/buscar_expediente_exacto.py`

### ▸ `async def buscar_expediente_exacto(page, texto_buscado)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def buscar_en_pagina()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def avanzar_pagina()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/bk/buscar_expediente_por_numero_bk.py`

### ▸ `async def buscar_expediente_por_numero(page, numero, anio, timeout)`
- **Retorna:** `tuple[bool, str]`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/bk/buscar_y_abrir_expediente.py`

### ▸ `async def buscar_y_abrir_expediente(page, numero, anio, caratula)`
- **Retorna:** `Optional[Dict]`
- **Descripción:** Busca y abre un expediente en el portal PJN. - Si se encuentra un solo resultado: abre automáticamente. - Si hay múltiples resultados: permite al usuario elegir.  :param page: Página de navegador Playwright actual. :param numero: Número del expediente (opcional). :param anio: Año del expediente (opcional). :param caratula: Carátula esperada (opcional). :return: Diccionario de datos extraídos del expediente, o None si falla.


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/bk/buscar_y_abrir_expediente_1.py`

### ▸ `async def buscar_y_abrir_expediente(page, numero, anio, caratula)`
- **Retorna:** `dict`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/bk/extraer_expedientes_bk.py`

### ▸ `async def extraer_expedientes(page, carpeta_salida, delay)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def guardar_json(expedientes, carpeta_salida)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/bk/probar_busqueda_y_apertura_v2.py`

### ▸ `async def probar_busqueda_y_apertura()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/bk/seleccionar_y_abrir_expediente.py`

### ▸ `async def seleccionar_y_abrir_expediente(page, caratula_filtro)`
- **Retorna:** `Tuple[bool, Optional[Dict]]`
- **Descripción:** Busca una fila en la tabla de resultados de expedientes. Si encuentra una fila que coincida (o cualquiera si no hay filtro), la abre y extrae los datos del expediente.  :param page: Página Playwright actual. :param caratula_filtro: Carátula exacta esperada (opcional). :return: (exito, datos)          - exito: True si se abrió y extrajo correctamente, False en caso contrario.          - datos: Diccionario de datos extraídos si exito=True, None si exito=False.


## 🔹 Módulo: `panel_pjn/acciones_pjn/gestion_expedientes/bk/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `panel_pjn/acciones_pjn/trash/obtener_actuaciones_async.py`

### ▸ `async def obtener_actuaciones_async(page_expediente, expediente_datos, carpeta_destino)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def normalizar_fecha(texto)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/trash/obtener_actuaciones_todas_paginas_async.py`

### ▸ `async def extraer_actuaciones_pagina(page_expediente, expediente_datos)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos, carpeta_destino)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def normalizar_fecha(texto)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `panel_pjn/acciones_pjn/trash/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `scripts/descargar_archivos_actuaciones.py`

### ▸ `async def descargar_archivos_actuaciones(page, actuaciones, carpeta_destino)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `scripts/probar_extraccion_todas_paginas.py`

### ▸ `async def probar_extraccion_completa()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `scripts/prueba_expediente_y_actuaciones.py`

### ▸ `async def prueba_expediente_y_actuaciones()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `scripts/prueba_extraccion_y_descarga.py`

### ▸ `async def prueba_extraccion_y_descarga()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `scripts/setup_path.py`

### ▸ `def incluir_ruta_base()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `scripts/test_buscar_expediente_exacto.py`

### ▸ `async def buscar_expediente()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `scripts/test_busqueda_por_formulario.py`

### ▸ `async def probar_busqueda_por_formulario()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `scripts/test_modulo_gestion_actuaciones.py`

### ▸ `async def prueba_modulo_gestion_actuaciones()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `src/actuaciones_v1.py`

### ▸ `def actualizar_ultima_actuacion(id_expediente, nueva_fecha)`
- **Retorna:** `—`
- **Descripción:** Actualiza la fecha de la última actuación de un expediente.

### ▸ `def obtener_id_expediente(numero_expediente)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def obtener_o_insertar_tipo_actuacion(nombre_tipo)`
- **Retorna:** `—`
- **Descripción:** Obtiene el ID del tipo de actuación. Si no existe, lo inserta en la base de datos.

### ▸ `def existe_actuacion(expediente_id, fecha, tipo_actuacion_id, detalle)`
- **Retorna:** `—`
- **Descripción:** Verifica si una actuación ya está registrada en la base de datos.

### ▸ `def insertar_actuacion(expediente_id, oficina, fecha, tipo_actuacion_id, detalle, foja, archivo, usuario_id)`
- **Retorna:** `—`
- **Descripción:** Inserta una nueva actuación en la base de datos.

### ▸ `def mover_archivo(nombre_archivo, expediente_id)`
- **Retorna:** `—`
- **Descripción:** Mueve el archivo de actuación desde la carpeta de descargas a la carpeta 'Documentos' dentro del expediente.

### ▸ `def procesar_actuaciones(json_path)`
- **Retorna:** `—`
- **Descripción:** Procesa el archivo JSON de actuaciones e inserta nuevas actuaciones en la base de datos.


## 🔹 Módulo: `src/backup.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `src/configuracion_v1.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `src/database_v1.py`

### ▸ `def conectar_bd()`
- **Retorna:** `—`
- **Descripción:** Establece conexión con la base de datos.


## 🔹 Módulo: `src/expedientes_v1.py`

### ▸ `def buscar_expediente(numero)`
- **Retorna:** `—`
- **Descripción:** Busca un expediente en la base de datos.

### ▸ `def obtener_expedientes()`
- **Retorna:** `—`
- **Descripción:** Obtiene todos los expedientes de la base de datos.

### ▸ `def actualizar_situacion(id_expediente, nueva_situacion)`
- **Retorna:** `—`
- **Descripción:** Actualiza la situación de un expediente en la base de datos.

### ▸ `def actualizar_caratula(id_expediente, nueva_caratula)`
- **Retorna:** `—`
- **Descripción:** Actualiza la carátula de un expediente en la base de datos.

### ▸ `def integrar_expedientes_json_bd()`
- **Retorna:** `—`
- **Descripción:** Función principal que coordina el proceso de integración de expedientes desde un JSON a la BD. Compara los expedientes en la base de datos y retorna los cambios encontrados como DataFrame

### ▸ `def comparar_expedientes(nuevos_expedientes)`
- **Retorna:** `—`
- **Descripción:** Compara expedientes nuevos con los existentes en la base de datos y devuelve un DataFrame con los cambios.

### ▸ `def cargar_expediente(numero, caratula, tipo_proceso, situacion_id, dependencia_id, observacion, instancia, fecha_inicio, fecha_actualizacion, ultima_actuacion, jurisdiccion_nombre)`
- **Retorna:** `—`
- **Descripción:** Inserta un nuevo expediente en la base de datos, asegurando que la jurisdicción exista.

### ▸ `def cargar_expediente_v2(numero, numero_solo, anio, incidental, caratula, ultima_actuacion, fecha_inicio, situacion_id, dependencia_id, prefijo_id)`
- **Retorna:** `—`
- **Descripción:** Inserta o actualiza un expediente en la base de datos.

### ▸ `def obtener_o_insertar_jurisdiccion(nombre_jurisdiccion)`
- **Retorna:** `—`
- **Descripción:** Obtiene el ID de la jurisdicción si existe; si no, la inserta en la base de datos.

### ▸ `def actualizar_jurisdiccion_expediente(expediente_id, nueva_jurisdiccion)`
- **Retorna:** `—`
- **Descripción:** Actualiza la jurisdicción de un expediente si está en NULL, 'SIN ASIGNAR' o es diferente.


## 🔹 Módulo: `src/funciones_v1_sin_uso.py`

### ▸ `def cargar_json()`
- **Retorna:** `—`
- **Descripción:** Carga el archivo JSON de expedientes y convierte fechas.

### ▸ `def comparar_expedientes(nuevos_expedientes)`
- **Retorna:** `—`
- **Descripción:** Compara expedientes nuevos con los existentes en la base de datos y consolida los cambios en una sola fila.


## 🔹 Módulo: `src/procesador_excel.py`

### ▸ `def obtener_mapeos_bd(conn)`
- **Retorna:** `—`
- **Descripción:** Obtiene los mapeos de Juzgados, Secretarías, Situaciones, Dependencias y Prefijos desde la base de datos.

### ▸ `def crear_dependencia_si_no_existe(conn, juzgado_id, secretaria_id)`
- **Retorna:** `—`
- **Descripción:** Crea una nueva dependencia en la base de datos si no existe.

### ▸ `def generar_script_insercion_sql_con_dependencias(df_expedientes)`
- **Retorna:** `—`
- **Descripción:** Genera un script SQL para insertar o actualizar expedientes en la base de datos, incluyendo la asignación de dependencias, situaciones y prefijos desde la base de datos.


## 🔹 Módulo: `src/procesador_json_v1.py`

### ▸ `def cargar_json()`
- **Retorna:** `—`
- **Descripción:** Carga el archivo JSON de expedientes y convierte las fechas al formato adecuado.

### ▸ `def procesar_expedientes(json_data)`
- **Retorna:** `—`
- **Descripción:** Procesa un JSON de expedientes y devuelve un DataFrame con columnas estructuradas.  :param json_data: Lista de diccionarios con los datos de expedientes. :return: DataFrame procesado.


## 🔹 Módulo: `src/reportes_v1.py`

### ▸ `def normalizar_texto(texto)`
- **Retorna:** `—`
- **Descripción:** Elimina espacios extra y convierte a mayúsculas para evitar falsos positivos en la detección de cambios.

### ▸ `def guardar_en_excel(df)`
- **Retorna:** `—`
- **Descripción:** Guarda los cambios detectados en un archivo Excel con una estructura más clara y ordenada.

### ▸ `def guardar_reporte_actuaciones(actuaciones)`
- **Retorna:** `—`
- **Descripción:** Guarda las actuaciones insertadas en un archivo Excel para auditoría.


## 🔹 Módulo: `src/sincronizacion_v1.py`

### ▸ `def crear_carpeta_expediente(id_expediente)`
- **Retorna:** `—`
- **Descripción:** Crea una carpeta para el expediente con subcarpetas.

### ▸ `def sincronizar_expedientes()`
- **Retorna:** `—`
- **Descripción:** Sincroniza los expedientes de la base de datos con las carpetas en la PC.

### ▸ `def main()`
- **Retorna:** `—`
- **Descripción:** Función principal que ejecuta la sincronización.


## 🔹 Módulo: `src/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `ui/Interfaz/interfaz_acts.py`

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def seleccionar_archivo()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def guardar_actuacion()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `ui/Interfaz/interfaz_cedulas.py`

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def cargar_cedulas()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def procesar_cedula(row)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def archivar_cedula(row)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def eliminar_cedula(row)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def descargar_pdf(row)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `ui/Interfaz/interfaz_exptes.py`

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def cargar_expedientes()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def filtrar_expedientes()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def ver_detalle(row)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def editar_expediente(row)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def eliminar_expediente(row)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def exportar_pdf(row)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `ui/Interfaz/interfaz_exptes2.py`

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `ui/Interfaz/interfaz_tablero.py`

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def agregar_expediente()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def limpiar_tablero()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `ui/Interfaz/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `web/auto_login.py`

### ▸ `async def guardar_sesion(context)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def iniciar_sesion(p)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def reutilizar_sesion_async()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def main()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def reutilizar_sesion()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `web/auto_login_vis.py`

### ▸ `async def guardar_sesion(context)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def iniciar_sesion(p)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def reutilizar_sesion_async()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def reutilizar_sesion()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `web/auto_login_vis_popup.py`

### ▸ `async def guardar_sesion(context)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def iniciar_sesion(p)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def reutilizar_sesion_async()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def reutilizar_sesion()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def obtener_ultima_pestania()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def handle_popup(popup)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def handle_popup(popup)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `web/extractor_v1.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `web/funciones_navegador_async.py`

### ▸ `async def extraer_datos_expediente(page_expediente)`
- **Retorna:** `—`
- **Descripción:** Extrae los datos del expediente en la pestaña activa y busca en la base de datos.

### ▸ `async def obtener_actuaciones(page_expediente, expediente_datos)`
- **Retorna:** `—`
- **Descripción:** Descarga todas las actuaciones y genera un archivo JSON.

### ▸ `def comparar_actuaciones(expediente_id, actuaciones_nuevas)`
- **Retorna:** `—`
- **Descripción:** Compara las actuaciones obtenidas del sitio web con las almacenadas en la base de datos.

### ▸ `def normalizar_fecha(fecha)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `web/funciones_navegador_v2.py`

### ▸ `def extraer_datos_expediente(page_expediente)`
- **Retorna:** `—`
- **Descripción:** Extrae los datos del expediente en la pestaña activa y busca en la base de datos.

### ▸ `def obtener_actuaciones(page_expediente, expediente_datos)`
- **Retorna:** `—`
- **Descripción:** Descarga todas las actuaciones y genera un archivo JSON.

### ▸ `def comparar_actuaciones(expediente_id, actuaciones_nuevas)`
- **Retorna:** `—`
- **Descripción:** Compara las actuaciones obtenidas del sitio web con las almacenadas en la base de datos.

### ▸ `def normalizar_fecha(fecha)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `web/monitoreo.py`

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `—`
- **Descripción:** Limpia los expedientes eliminando saltos de línea innecesarios.

### ▸ `def cargar_json_existente()`
- **Retorna:** `—`
- **Descripción:** Carga el archivo JSON existente para mantener el estado de 'leída'.

### ▸ `def guardar_en_csv(expedientes_por_fecha)`
- **Retorna:** `—`
- **Descripción:** Guarda los expedientes en un archivo CSV con el estado de lectura.

### ▸ `def guardar_en_json(expedientes_por_fecha)`
- **Retorna:** `—`
- **Descripción:** Guarda los expedientes en JSON manteniendo el estado de lectura.

### ▸ `def capturar_lista_expedientes(page)`
- **Retorna:** `—`
- **Descripción:** Captura la lista completa de expedientes con scroll automático sin duplicados por fecha.


## 🔹 Módulo: `web/monitoreo_bk1.py`

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `—`
- **Descripción:** Limpia los expedientes eliminando saltos de línea innecesarios.

### ▸ `def cargar_json_existente()`
- **Retorna:** `—`
- **Descripción:** Carga el archivo JSON existente para mantener el estado de 'leída'.

### ▸ `def guardar_en_csv(expedientes_por_fecha)`
- **Retorna:** `—`
- **Descripción:** Guarda los expedientes en un archivo CSV con el estado de lectura.

### ▸ `def guardar_en_json(expedientes_por_fecha)`
- **Retorna:** `—`
- **Descripción:** Guarda los expedientes en JSON manteniendo el estado de lectura.

### ▸ `def capturar_lista_expedientes(page)`
- **Retorna:** `—`
- **Descripción:** Captura la lista completa de expedientes con scroll automático sin duplicados por fecha.


## 🔹 Módulo: `web/navegador.py`

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def mostrar_mensaje(titulo, mensaje)`
- **Retorna:** `—`
- **Descripción:** Muestra un cuadro de diálogo con un mensaje.

### ▸ `def obtener_pestaña_activa()`
- **Retorna:** `—`
- **Descripción:** Obtiene la pestaña activa en Playwright.

### ▸ `def extraer_datos_expediente()`
- **Retorna:** `—`
- **Descripción:** Extrae los datos del expediente en la pestaña activa y busca en la base de datos.

### ▸ `def obtener_actuaciones()`
- **Retorna:** `—`
- **Descripción:** Descarga todas las actuaciones (actuaciones, notificaciones, cédulas) en una única carpeta.

### ▸ `def refrescar_pagina()`
- **Retorna:** `—`
- **Descripción:** Recarga la página actual.

### ▸ `def cerrar_navegador()`
- **Retorna:** `—`
- **Descripción:** Cierra el navegador y la aplicación.

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `—`
- **Descripción:** Elimina saltos de línea y prefijos innecesarios.


## 🔹 Módulo: `web/navegador_v1.py`

### ▸ `def iniciar_navegador()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `web/navegador_v10.py`

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def ejecutar_async(coroutine)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def mostrar_mensaje(titulo, mensaje)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def obtener_pestaña_activa()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def extraer_datos_expediente()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def obtener_actuaciones()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def comparar_actuaciones()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def refrescar_pagina()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def cerrar_navegador()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def cerrar()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `web/navegador_v2.py`

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def mostrar_mensaje(titulo, mensaje)`
- **Retorna:** `—`
- **Descripción:** Muestra un cuadro de diálogo con un mensaje.

### ▸ `def obtener_pestaña_activa()`
- **Retorna:** `—`
- **Descripción:** Obtiene la pestaña activa en Playwright.

### ▸ `def extraer_datos_expediente()`
- **Retorna:** `—`
- **Descripción:** Llama a la función de extracción de datos desde el módulo externo.

### ▸ `def obtener_actuaciones()`
- **Retorna:** `—`
- **Descripción:** Llama a la función de obtención de actuaciones desde el módulo externo y devuelve las actuaciones obtenidas.

### ▸ `def comparar_actuaciones()`
- **Retorna:** `—`
- **Descripción:** Compara las actuaciones del expediente en la web con las almacenadas en la base de datos.

### ▸ `def refrescar_pagina()`
- **Retorna:** `—`
- **Descripción:** Recarga la página actual.

### ▸ `def cerrar_navegador()`
- **Retorna:** `—`
- **Descripción:** Cierra el navegador y la aplicación.


## 🔹 Módulo: `web/navegador_v3_async.py`

### ▸ `def __init__()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def ejecutar_async(coroutine)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def mostrar_mensaje(titulo, mensaje)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def obtener_pestaña_activa()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def extraer_datos_expediente()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def obtener_actuaciones()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def comparar_actuaciones()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def refrescar_pagina()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def cerrar_navegador()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def cerrar()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `web/__init__.py`

_No se detectaron funciones definidas._

## 🔹 Módulo: `web/bk/auto_login_bk.py`

### ▸ `def guardar_sesion(context)`
- **Retorna:** `—`
- **Descripción:** Guarda cookies y localStorage para reutilizar la sesión.

### ▸ `def iniciar_sesion()`
- **Retorna:** `—`
- **Descripción:** Inicia sesión en el Portal PJN asegurando que Playwright no sea detectado.

### ▸ `def reutilizar_sesion()`
- **Retorna:** `—`
- **Descripción:** Reutiliza la sesión guardada y devuelve la página activa.


## 🔹 Módulo: `web/bk/auto_login_v2_bk.py`

### ▸ `async def guardar_sesion(context)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def iniciar_sesion(p)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def reutilizar_sesion_async()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def reutilizar_sesion()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `web/bk/funciones_navegador_v2_bk.py`

### ▸ `def extraer_datos_expediente(page_expediente)`
- **Retorna:** `—`
- **Descripción:** Extrae los datos del expediente en la pestaña activa y busca en la base de datos.

### ▸ `def obtener_actuaciones(page_expediente, expediente_datos)`
- **Retorna:** `—`
- **Descripción:** Descarga todas las actuaciones y genera un archivo JSON.

### ▸ `def comparar_actuaciones(expediente_id, actuaciones_nuevas)`
- **Retorna:** `—`
- **Descripción:** Compara las actuaciones obtenidas del sitio web con las almacenadas en la base de datos.

### ▸ `def normalizar_fecha(fecha)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def limpiar_texto(texto)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `web/interfaz_web/app.py`

### ▸ `def iniciar_backend()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `web/interfaz_web/backend/db.py`

### ▸ `def conectar()`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `def obtener_expedientes()`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `web/interfaz_web/backend/main.py`

### ▸ `async def home(request)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def panel_admin(request)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def vista_monitoreo(request)`
- **Retorna:** `—`
- **Descripción:** Sin descripción

### ▸ `async def marcar_leido(fecha, numero)`
- **Retorna:** `—`
- **Descripción:** Sin descripción


## 🔹 Módulo: `web/interfaz_web/backend/__init__.py`

_No se detectaron funciones definidas._
