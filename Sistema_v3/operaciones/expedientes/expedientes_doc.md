# 📄 Documentación Mejorada: `expedientes.py`

Este módulo contiene funciones relacionadas con la extracción de **expedientes judiciales** visibles en el portal del Poder Judicial de la Nación (PJN).

## Funciones principales

### `extraer_expedientes(page, carpeta_salida=..., ...)`

Extrae todos los expedientes visibles desde la tabla del portal. Soporta ordenamiento, corte por fecha, límite de tiempo y guarda resultados como JSON.

**Parámetros destacados:**
- `page`: instancia de Playwright.
- `fecha_corte`: corte de extracción por última actuación.
- `orden`: `"fecha"`, `"caratula"`, `"situacion"`, `"oficina"`.
- `guardar_json`: si debe guardar archivo.

**Retorna:**
```python
(lista_de_expedientes, ruta_archivo_json, estado_final)
```
Donde `estado_final` puede ser:
- `"completo"` → extracción finalizada normalmente.
- `"corte_fecha"` → se alcanzó la fecha de corte.
- `"fin_listado"` → no hubo expedientes nuevos en la página actual y se asumió fin natural del listado.
- `"tiempo_maximo"` → se alcanzó el tiempo máximo configurado.
- `"tabla_no_disponible"` → no se encontró la tabla de expedientes.

> 🆕 A partir de esta versión la detección de filas repetidas ya no corta la extracción inmediatamente. Se continúa recorriendo el paginado y solo se finaliza con `"fin_listado"` cuando una página entera no aporta novedades. Además, se calcula un *fingerprint* del `<tbody>` tras cada clic en "Siguiente" para confirmar que la tabla haya cambiado efectivamente.

**Estructura de cada expediente:**
```json
{
  "numero": "FPA 1234/2021",
  "caratula": "GARCIA, JUAN c/ ESTADO NACIONAL",
  "dependencia": "JUZGADO FEDERAL PARANA",
  "situacion": "ACTIVO",
  "ultima_actuacion": "15/05/2025",
  "valido": true,
  "extraido_en": "2025-05-25T12:00:00"
}
```

**Ejemplo de uso:**
```python
expedientes, ruta, estado = await extraer_expedientes(page, fecha_corte="01/01/2024")
```
