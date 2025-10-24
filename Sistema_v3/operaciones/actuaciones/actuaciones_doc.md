# 📄 Documentación Mejorada: `actuaciones.py`

Módulo que gestiona las actuaciones judiciales de un expediente.

## Funciones principales

### `async def extraer_actuaciones(page_expediente)`
Extrae actuaciones con paginación completa.

### `async def extraer_actuaciones_completas(page, expedientes, ruta_salida)`
Recorre múltiples expedientes y guarda resultados JSON por cada uno.

### `async def descargar_adjuntos(page, actuaciones, carpeta_destino)`
Descarga PDFs adjuntos.  
- Evita duplicados.  
- Verifica existencia de archivos.  
- Crea carpeta por expediente.

### `async def extraer_actuaciones_historicas(page_expediente, expediente_datos, indice_inicial=1)`
Accede a la pestaña de históricas y extrae información si existe.

## Formato de salida (JSON por expediente)
```json
{
  "Expediente": "FPA 1234/2021",
  "Actuaciones": [
    {
      "Indice": 1,
      "Fecha": "2025-05-20",
      "Tipo": "CEDULA_ELECTRONICA_PARTE",
      "Detalle": "Notificación electrónica",
      "Oficina": "JUZGADO FEDERAL",
      "TieneArchivo": true,
      "NombreArchivo": "cedula_1234.pdf",
      "Hash": "abc123",
      "ExtraidaEn": "2025-05-21T12:00:00"
    }
  ]
}
```

## Errores posibles
- `"Timeout"` al cargar tabla.  
- `"Error general"` en caso de fallos en Playwright.  
- Lista vacía si no existen actuaciones.  

