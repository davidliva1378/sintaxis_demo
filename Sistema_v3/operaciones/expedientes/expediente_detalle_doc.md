# 📄 Documentación Mejorada: `expediente_detalle.py`

Este módulo agrupa funciones que operan sobre un **expediente judicial puntual**, generalmente luego de haber sido seleccionado o buscado en el portal.

## 📚 Funciones incluidas

### `async def buscar_expediente_por_numero(page, numero)`
Busca un expediente específico por número.  
**Retorna:** `True` si se realizó la búsqueda, `False` en caso de error o si no se encontró el campo.

### `async def abrir_expediente_desde_fila(page, indice=0)`
Abre el expediente correspondiente a una fila de la tabla.  
**Retorna:** `True` si se abrió, `False` si no existe esa fila.

### `async def extraer_datos_expediente(page)`
Extrae datos visibles del expediente abierto (`numero`, `caratula`, `jurisdiccion`).  
**Retorna:** diccionario con los datos, `"N/D"` si no existen.

### `def mostrar_y_elegir_expediente(lista)`
Muestra lista en consola y permite elegir un expediente.  
⚠️ Solo válido en CLI (usa `input()`), no apto para GUI.

### `async def buscar_expedientes(page, numero=None, anio=None, caratula=None)`
Búsqueda avanzada.  
**Retorna:** lista de filas (`ElementHandle`) o lista vacía si no hubo resultados.

## ⚠️ Consideraciones
- `extraer_datos_expediente` depende de selectores específicos (`span#caratula`, `span#numeroExpediente`, `span#jurisdiccion`), que pueden cambiar.
- `mostrar_y_elegir_expediente` debe reemplazarse en la GUI por un selector visual.
