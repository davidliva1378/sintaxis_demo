"""Constantes globales del sistema PJN v6.

Este módulo define constantes que se usan en múltiples lugares del código.
Para configuraciones que varían por entorno, ver infrastructure.config.settings

Nota: Adaptado de Sistema_v5.1.1/pjn/constants.py para compatibilidad.
"""

# ============================================================================
# URLS DEL PORTAL JUDICIAL NACIONAL
# ============================================================================

# URL principal del sistema de consultas del PJN
# Nota: La URL antigua https://portalpjn.pjn.gov.ar/consultas devolvía 404
# La URL actual es https://scw.pjn.gov.ar/scw/consultaListaRelacionados.seam
URL_CONSULTAS_DEFAULT = "https://scw.pjn.gov.ar/scw/consultaListaRelacionados.seam"
"""URL por defecto para consultas del PJN (puede ser sobreescrita por configuración)."""


# ============================================================================
# CÓDIGOS DE FINALIZACIÓN / MOTIVOS
# ============================================================================

# Motivos de finalización de extracción de expedientes
MOTIVO_FIN_LISTADO = "fin_listado"
"""Se alcanzó el final natural del paginado."""

MOTIVO_LIMITE_PAGINAS = "limite_paginas"
"""Se alcanzó el límite máximo de páginas configurado."""

MOTIVO_LIMITE_FECHA = "limite_fecha"
"""Se alcanzó la fecha de corte configurada."""

MOTIVO_LIMITE_TIEMPO = "limite_tiempo"
"""Se superó el tiempo máximo de extracción."""

MOTIVO_DUPLICADO_ENCONTRADO = "duplicado_encontrado"
"""Se encontró un expediente duplicado y se configuró detener."""

MOTIVO_BUCLE_DETECTADO = "bucle_detectado"
"""Se detectó un ciclo infinito en la paginación."""

MOTIVO_SIN_SIGUIENTE = "sin_siguiente"
"""No existe control para avanzar de página."""

MOTIVO_SIN_SIGUIENTE_HABILITADO = "sin_siguiente_habilitado"
"""El botón 'Siguiente' existe pero está deshabilitado."""

MOTIVO_SIGUIENTE_TIMEOUT = "siguiente_timeout"
"""Timeout esperando que aparezca el botón 'Siguiente'."""

MOTIVO_SIGUIENTE_DESHABILITADO = "siguiente_deshabilitado"
"""El botón 'Siguiente' se deshabilitó al intentar usarlo."""

MOTIVO_ERROR_CLICK = "error_click"
"""Falló el clic en el botón 'Siguiente'."""


# ============================================================================
# CAMPOS / KEYS DE DICCIONARIOS
# ============================================================================

# Campos de expedientes
CAMPO_NUMERO = "numero"
CAMPO_CARATULA = "caratula"
CAMPO_DEPENDENCIA = "dependencia"
CAMPO_SITUACION = "situacion"
CAMPO_FECHA = "fecha"
CAMPO_ULTIMA_ACTUACION = "ultima_actuacion"

# Campos de entradas
CAMPO_EVENTO = "evento"
CAMPO_TIPO_EVENTO = "tipo_evento"
CAMPO_LEIDA = "leida"
CAMPO_EXTRAIDA_EN = "extraida_en"

# Campos de actuaciones
CAMPO_INDICE = "indice"
CAMPO_TIPO = "tipo"
CAMPO_DETALLE = "detalle"
CAMPO_ARCHIVOS = "archivos"

# Campos de archivos
CAMPO_NOMBRE_ARCHIVO = "nombre"
CAMPO_URL = "url"
CAMPO_DESCARGADO = "descargado"
CAMPO_RUTA_LOCAL = "ruta_local"


# ============================================================================
# ORDENAMIENTO
# ============================================================================

ORDEN_FECHA = "fecha"
ORDEN_CARATULA = "caratula"
ORDEN_OFICINA = "oficina"
ORDEN_SITUACION = "situacion"

ORDENES_VALIDOS = {ORDEN_FECHA, ORDEN_CARATULA, ORDEN_OFICINA, ORDEN_SITUACION}


# ============================================================================
# ESTADOS DE PLAYWRIGHT
# ============================================================================

STATE_VISIBLE = "visible"
STATE_HIDDEN = "hidden"
STATE_ATTACHED = "attached"
STATE_DETACHED = "detached"


# ============================================================================
# EVENTOS DE NAVEGACIÓN
# ============================================================================

WAIT_UNTIL_DOMCONTENTLOADED = "domcontentloaded"
WAIT_UNTIL_LOAD = "load"
WAIT_UNTIL_NETWORKIDLE = "networkidle"


# ============================================================================
# EXTENSIONES DE ARCHIVO
# ============================================================================

EXT_JSON = ".json"
EXT_PDF = ".pdf"
EXT_CSV = ".csv"
EXT_XML = ".xml"
EXT_TXT = ".txt"


# ============================================================================
# ENCODING
# ============================================================================

ENCODING_UTF8 = "utf-8"
ENCODING_LATIN1 = "latin-1"
ENCODING_ASCII = "ascii"


# ============================================================================
# VALORES BOOLEANOS COMO STRING
# ============================================================================

# Para parseo de valores booleanos desde strings
BOOL_TRUE_VALUES = {"1", "true", "t", "yes", "y", "si", "sí"}
BOOL_FALSE_VALUES = {"0", "false", "f", "no", "n"}


# ============================================================================
# LONGITUDES MÁXIMAS
# ============================================================================

MAX_LONGITUD_FINGERPRINT = 4_096
"""Longitud máxima del fingerprint HTML para detección de cambios de página."""

MAX_LONGITUD_NOMBRE_ARCHIVO = 255
"""Longitud máxima de nombre de archivo (límite del sistema de archivos)."""


# ============================================================================
# CONSTANTES ADICIONALES V6
# ============================================================================

# Tipos de eventos (compatibilidad v5.1.1)
TIPO_EVENTO_NOTIFICACION = "N"
"""Evento de tipo Notificación."""

TIPO_EVENTO_DEMANDA = "D"
"""Evento de tipo Demanda."""

TIPOS_EVENTO_VALIDOS = {TIPO_EVENTO_NOTIFICACION, TIPO_EVENTO_DEMANDA}


# Estados de expedientes (v6)
ESTADO_EXPEDIENTE_ACTIVO = "activo"
ESTADO_EXPEDIENTE_INACTIVO = "inactivo"
ESTADO_EXPEDIENTE_ARCHIVADO = "archivado"


# Modos de monitoreo (v6)
MODO_MONITOR_AUTOMATICO = "automatico"
MODO_MONITOR_MANUAL = "manual"
MODO_MONITOR_PROGRAMADO = "programado"


# Días de la semana (en español para compatibilidad con v5.1.1)
DIA_LUNES = "lunes"
DIA_MARTES = "martes"
DIA_MIERCOLES = "miercoles"
DIA_JUEVES = "jueves"
DIA_VIERNES = "viernes"
DIA_SABADO = "sabado"
DIA_DOMINGO = "domingo"

DIAS_SEMANA_VALIDOS = {
    DIA_LUNES,
    DIA_MARTES,
    DIA_MIERCOLES,
    DIA_JUEVES,
    DIA_VIERNES,
    DIA_SABADO,
    DIA_DOMINGO,
}
