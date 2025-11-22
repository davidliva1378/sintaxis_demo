# Documentación del Módulo gestion_actuaciones

## 📁 Estructura del Módulo

```
gestion_actuaciones/
├── __init__.py
├── extraccion.py
├── descarga.py
└── utilidades.py
```

## 1. __init__.py
Importa funciones clave para acceso directo.

## 2. extraccion.py

### `async def extraer_actuaciones_pagina(page_expediente, expediente_datos)`
Extrae datos de una sola página de actuaciones.

### `async def obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos, carpeta_destino="Actuaciones")`
Recorre todas las páginas y guarda un JSON consolidado.

## 3. descarga.py

### `async def descargar_archivos_actuaciones(page, actuaciones, carpeta_destino)`
Descarga todos los archivos PDF listados en las actuaciones.

## 4. utilidades.py

### `limpiar_texto(texto)`
Limpia texto eliminando etiquetas y saltos de línea.

### `normalizar_fecha(texto)`
Convierte fechas a formato ISO (YYYY-MM-DD).

### `generar_hash_archivo(fecha, tipo, detalle, longitud=6)`
Genera un hash único para nombrar archivos descargados.

## 💡 Ejemplo de uso

```python
from gestion_actuaciones import obtener_actuaciones_todas_paginas_async, descargar_archivos_actuaciones

resultado = await buscar_y_abrir_expediente(page, numero, anio, caratula)
page_expediente = page
expediente_datos = resultado["datos_expediente"]

actuaciones = await obtener_actuaciones_todas_paginas_async(page_expediente, expediente_datos)
await descargar_archivos_actuaciones(page_expediente, actuaciones, "Actuaciones/FPA_000000_2024")
```

## 🧪 Requisitos

- Python 3.8+
- playwright
- asyncio