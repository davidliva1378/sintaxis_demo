# Documentación de mejoras en actuaciones V4

## Refactorizaciones clave
- Se creó la rutina asíncrona `construir_actuacion_desde_fila` que concentra la extracción y normalización de datos de cada fila de la tabla de actuaciones.
  - Reduce la duplicidad de lógica entre `extraer_actuaciones_pagina` y `extraer_actuaciones_historicas`.
  - Garantiza el mismo tratamiento de hashes, banderas de archivo y marca temporal en ambos contextos.
- Las esperas al avanzar de página ahora comparan el HTML previo mediante parámetros (`wait_for_function`) evitando interpolaciones de cadenas que podían romperse con comillas en el markup.

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
| `total_archivos_con_enlace` | Número de actuaciones con archivos adjuntos detectados. |
| `descargas_pendientes` | Actuaciones con archivo cuyo atributo `Descargado` es falso o inexistente. Útil para reintentos de descarga. |
| `ultimo_hash_actual` | Hash de la actuación más reciente (primer elemento de la lista de actuales). Facilita cortes tempranos en procesos incrementales. |
| `ultima_fecha_actual` | Fecha normalizada de la última actuación actual registrada. |

Los campos existentes `Cantidad de Actuaciones Obtenidas` y `Cantidad de Archivos Descargados` se preservan para mantener compatibilidad hacia atrás.

## Consideraciones operativas
- Los valores de fechas provenientes del expediente se normalizan a `YYYY-MM-DD` antes de incorporarse al encabezado.
- Los totales se recalculan automáticamente cada vez que se regeneran las actuaciones (actuales o completas), evitando dependencias de datos intermedios.
- La estructura sigue guardándose en `Actuaciones/<numero>/actuaciones-<numero>.json` o en la carpeta del expediente dentro de `ActuacionesCompletas/` según el flujo utilizado.

## Próximos pasos sugeridos
- Aprovechar `ultimo_hash_actual` y `descargas_pendientes` para implementar la actualización incremental sin releer páginas ya procesadas.
- Serializar un historial de versiones del esquema en la documentación si se realizan más cambios futuros.
