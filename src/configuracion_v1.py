import os

# Configuración de la base de datos
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "admin",
    "database": "test_v2"
}

# Directorios
CARPETA_REPORTES = "C:\\Users\\aleja\\OneDrive\\Escritorio\\Proyecto-Descargas\\Reportes"
EXCEL_PATH = os.path.join(CARPETA_REPORTES, "informe_comparacion.xlsx")
EXCEL_PATH_2 = os.path.join(CARPETA_REPORTES, "reporte_actuaciones.xlsx")
JSON_PATH = "C:\\Users\\aleja\\OneDrive\\Escritorio\\Proyecto-Descargas\\expedientes.json"
BASE_PATH = "E:\\Sistema\\Expedientes"

# Carpeta de archivos descargados
CARPETA_ORIGEN = "C:\\Users\\aleja\\OneDrive\\Escritorio\\Proyecto-Descargas"
CARPETA_EXPEDIENTES = "E:\\Sistema\\Expedientes"
