# Documentación de mejoras en actuaciones V4

## Refactorizaciones clave
- Se creó la rutina asíncrona `construir_actuacion_desde_fila` que concentra la extracción y normalización de datos de cada fila de la tabla de actuaciones.
  - Reduce la duplicidad de lógica entre `extraer_actuaciones_pagina` y `extraer_actuaciones_historicas`.
  - Garantiza el mismo tratamiento de hashes, banderas de archivo y marca temporal en ambos contextos.
- Las esperas al avanzar de página ahora comparan el HTML previo mediante parámetros (`wait_for_function`) evitando interpolaciones de cadenas que podían romperse con comillas en el markup y, si el paginador no refleja el cambio, recurren a `document.getElementById` para verificar el refresco de la tabla.

## Metadatos ampliados en el JSON de actuaciones
Cada archivo generado incluye un encabezado enriquecido bajo la clave `Expediente` con los siguientes campos adicionales:

| Campo | Descripción |
| --- | --- |
| `version_formato` | Versión del esquema del archivo de actuaciones. Permite validar compatibilidades futuras. |
| `fecha_extraccion` | Fecha y hora de generación del snapshot en formato `YYYY-MM-DD HH:MM:SS`. |
| `incluye_historicas` | Indica si el archivo contiene actuaciones históricas además de las actuales. |
| `total_actuales` | Cantidad de actuaciones presentes en la pestaña actual al momento de la captura. |
| `total_historicas` | Cantidad de actuaciones históricas incorporadas. |
| `total_actuaciones` | Suma de actuaciones actuales e históricas disponibles en el archivo. |
| `total_archivos_con_enlace` | Número de actuaciones con archivos adjuntos detectados. Se actualiza tras cada descarga diferida. |
| `descargas_pendientes` | Actuaciones con archivo cuyo atributo `Descargado` es falso o inexistente. Se recalcula automáticamente luego de ejecutar el downloader. |
| `ultimo_hash_actual` | Hash de la actuación más reciente (primer elemento de la lista de actuales). Facilita cortes tempranos en procesos incrementales. |
| `ultima_fecha_actual` | Fecha normalizada de la última actuación actual registrada. |

Los campos existentes `Cantidad de Actuaciones Obtenidas` y `Cantidad de Archivos Descargados` se preservan para mantener compatibilidad hacia atrás, pero ahora el segundo contabiliza únicamente los adjuntos que ya poseen `Descargado = true`.

## Consideraciones operativas
- Los valores de fechas provenientes del expediente se normalizan a `YYYY-MM-DD` antes de incorporarse al encabezado.
- Los totales se recalculan automáticamente cada vez que se regeneran las actuaciones (actuales o completas), evitando dependencias de datos intermedios.
- Tras ejecutar `descargar_archivos_de_json`, el encabezado se actualiza en disco para reflejar la cantidad de archivos descargados y los pendientes restantes.
- La estructura sigue guardándose en `Actuaciones/<numero>/actuaciones-<numero>.json` o en la carpeta del expediente dentro de `ActuacionesCompletas/` según el flujo utilizado.
- La normalización del número de expediente para construir rutas se encapsuló en `normalizar_numero_expediente`, evitando diferencias entre scripts auxiliares y rutinas de extracción.
- Durante la descarga diferida de adjuntos, la carpeta del expediente se crea automáticamente si no existiera, evitando errores de ruta ausente y permitiendo ejecutar el flujo sólo con conocer el número de expediente.

## Próximos pasos sugeridos
- Aprovechar `ultimo_hash_actual` y `descargas_pendientes` para implementar la actualización incremental sin releer páginas ya procesadas.
- Serializar un historial de versiones del esquema en la documentación si se realizan más cambios futuros.
