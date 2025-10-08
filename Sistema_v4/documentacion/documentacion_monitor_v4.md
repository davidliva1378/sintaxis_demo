# Documentación exhaustiva del monitor de expedientes y entradas (Sistema v4)

## 1. Propósito general

El módulo de monitorización de Sistema v4 ofrece una bandeja de sistema (system tray) que automatiza tres tareas clave del flujo PJN:

1. **Verificación periódica de expedientes** mediante Playwright, respetando ventanas horarias, filtros por fecha de corte y límites configurables.
2. **Sincronización de entradas y notificaciones** con almacenamiento JSON/CSV y seguimiento independiente de cadencias.
3. **Operaciones auxiliares** (comparación con base histórica, respaldos guiados, diagnóstico de sesión, forzado de login y edición completa de la configuración).

Todo el comportamiento se concentra en `monitor_entradas_expedientes_v4.py`, apoyándose en helpers especializados para configuración (`configuracion_modo.py`), comparación (`comparacion_expedientes.py`), respaldo (`respaldo_historico.py`) e íconos (`icono_base64.py`).

---

## 2. Componentes principales del monitor

| Componente | Responsabilidad | Detalles clave |
| --- | --- | --- |
| `MonitorExpedientesTray` | Inicializa Qt, crea el icono de bandeja y arma el menú contextual. Gestiona timers, hilos y persistencia de configuración. | Habilita acciones para verificar expedientes/entradas, utilidades, comparación manual, diálogo de configuración y salida. Controla reintentos, notificaciones y tooltips dinámicos. |
| `VerificadorExpedientesV4` | Hilo `QThread` que ejecuta la extracción completa de expedientes. | Reutiliza la sesión automática, envía filtros de fecha y orden al helper Playwright, recopila metadatos, guarda JSON y devuelve un `ResultadoExpedientes` estructurado. |
| `VerificadorEntradasV4` | Hilo `QThread` para sincronizar notificaciones. | Guarda historiales en JSON/CSV, maneja errores de sesión y reporta mediante `ResultadoEntradas`. |
| `ConfiguracionDialog` | Diálogo PySide tabulado para editar `config_monitor.json`. | Agrupa pestañas (general, intervalos, filtro, reintentos, respaldo, notificaciones), añade ayudas, checkboxes por día, vista previa de corte y restauración de defaults. |
| `configuracion_modo.py` | Helper común de lectura/escritura de configuración. | Define defaults con bloques extendidos (rutas, reintentos, comparación, filtros), realiza mezcla profunda y reutiliza la lógica de fecha de corte heredada. |
| `comparacion_expedientes.py` | Servicio para comparar archivos actuales vs. base histórica. | Resuelve rutas, modos (parcial vs. total), filtra la base por fecha cuando corresponde y genera informes JSON con avisos detallados. |
| `respaldo_historico.py` | Utilidad para copias de seguridad guiadas. | Copia archivos seleccionados al destino histórico con timestamp, registrando copiados y omitidos. |

---

## 3. Estructura de archivos y directorios

Por defecto, el monitor trabaja dentro de `datos_extraidos/monitoreo`, carpeta que concentra:

* `expedientes_monitor.json`: última extracción exitosa de expedientes.
* `expedientes_monitor - base.json`: archivo de referencia para comparación.
* `notificaciones/` (subcarpeta generada por Playwright) con historiales JSON/CSV.
* `reportes/`: informes generados por las comparaciones.
* `historico/`: destino por defecto de los respaldos programados.

Los caminos pueden personalizarse desde el diálogo de configuración (pestañas General y Respaldo) para adaptarse a entornos de producción sin modificar el código.

### 3.1 Archivos clave del monitor

| Archivo | Ubicación | Descripción |
| --- | --- | --- |
| `monitor_entradas_expedientes_v4.py` | `Sistema_v4/monitor/` | Aplicación principal del monitor, contiene la lógica de bandeja, hilos de verificación y diálogo de configuración. |
| `configuracion_modo.py` | `Sistema_v4/monitor/` | Helper de gestión de configuración, define defaults y operaciones de carga/guardado. |
| `comparacion_expedientes.py` | `Sistema_v4/monitor/` | Servicio de comparación entre archivos actuales y base histórica. |
| `respaldo_historico.py` | `Sistema_v4/monitor/` | Utilidad para copias de seguridad guiadas con timestamp. |
| `icono_base64.py` | `Sistema_v4/monitor/` | Ícono codificado en base64 para la bandeja del sistema. |
| `config_monitor.json` | Raíz del proyecto | Configuración persistente del monitor (modos, intervalos, filtros, etc.). |
| `session.json` | Raíz del proyecto | Archivo de sesión compartido con el auto_login del sistema. |

---

## 4. Configuración persistente (`config_monitor.json`)

### 4.1 Bloques disponibles

`configuracion_modo.DEFAULT_CONFIG` define los valores base y se fusiona recursivamente con el JSON existente al cargarlo. Las claves principales son:

- `modo`: `automatico`, `laboral`, `no_laboral`.
- `horario_laboral`: días hábiles, horario, intervalos por tipo de verificación.
- `fuera_horario`: intervalos fuera del horario definido.
- `filtro_expedientes`: modo de fecha de corte (`hoy`, `ultimo_dia_habil`, `dias_atras`, combinaciones, `sin_corte`), cantidad de días y orden solicitado al portal.
- `comparacion`: `modo` (`parcial` o `total`) y bandera `auto` para la ejecución post-verificación.
- `respaldo`: destino y lista de archivos a copiar.
- `rutas`: carpeta base de monitoreo.
- `reintentos`: límites y esperas independientes para expedientes/entradas.
- `notificaciones`: banderas que gobiernan los toasts de comparación y respaldo.

### 4.2 Carga y persistencia

`cargar_config_monitor` lee el archivo, inyecta defaults faltantes y devuelve siempre un diccionario completo; `guardar_config_monitor` persiste usando UTF-8 y crea directorios intermedios. `actualizar_modo_monitor` valida los modos antes de escribir. `obtener_fecha_corte` delega en el helper heredado para mantener paridad con versiones previas.

### 4.3 Edición interactiva

`ConfiguracionDialog` inicializa los controles desde la configuración actual, aplica validaciones in situ (por ejemplo, rutas existentes, intervalos positivos, días laborales mediante checkboxes) y muestra una vista previa dinámica de la fecha resultante. Al guardar, realiza una mezcla profunda para preservar claves personalizadas y reinicia temporizadores/tooltips de inmediato.

---

## 5. Menú de bandeja y acciones disponibles

| Acción | Descripción | Consideraciones |
| --- | --- | --- |
| `📥 Verificar expedientes` | Lanza `VerificadorExpedientesV4` respetando filtros, orden y rutas configuradas. | Deshabilita la acción mientras el hilo corre, muestra progreso en logs y notifica con estado/resumen al finalizar. |
| `📤 Verificar entradas` | Ejecuta `VerificadorEntradasV4` guardando JSON/CSV en el directorio configurado. | Gestiona reintentos, diferencia errores de sesión y notifica cantidad de novedades. |
| `🧪 Comparar expedientes` | Compara manualmente contra la base histórica si el helper está disponible. | Deshabilitada automáticamente cuando falta `comparacion_expedientes.py` o las dependencias de comparación; respeta preferencias de notificación. |
| `🛠️ Modo de trabajo` | Submenú con opciones chequeables (`automatico`, `laboral`, `no_laboral`). | Actualiza el JSON, recalcula temporizadores y tooltips y registra el cambio en el log. |
| `🧰 Utilidades` | Agrupa estado de sesión, forzado de login, respaldo guiado y marcador para futuras herramientas. | `mostrar_estado_sesion` diagnostica `SESSION_FILE`, `forzar_login` lo elimina, `respaldar_resultados` invoca `generar_respaldo_monitoreo`. |
| `⚙️ Configuración…` | Abre el diálogo de configuración descrito arriba. | Permite restablecer defaults, valida datos y persiste cambios inmediatos. |
| `🛑 Salir` | Cierra la aplicación y detiene timers/hilos en ejecución. | Libera la bandeja y termina el proceso Qt. |

---

## 6. Flujo de verificación de expedientes

1. **Preparación del hilo**: `verificar_expedientes` valida que no exista una ejecución en curso, determina directorios de salida, resuelve configuración (incluyendo modo de comparación para omitir la fecha de corte en modo total), traduce la fecha ISO a `DD/MM/AAAA` y registra parámetros iniciales.
2. **Ejecución Playwright**: `VerificadorExpedientesV4` reutiliza la sesión automatizada, navega a `URL_CONSULTAS` e invoca `extraer_expedientes_completos` con orden y fecha de corte. El helper devuelve expedientes, motivo y metadatos de paginación/descartes.
3. **Procesamiento de resultados**: el hilo guarda el JSON (si corresponde), normaliza estados, preserva motivos controlados (`limite_fecha`, `limite_tiempo`, etc.) para evitar falsos "total_incompleto" y emite un `ResultadoExpedientes` con totales, motivo original, páginas recorridas, descartes y ruta final.
4. **Post-proceso en la bandeja**: `procesar_resultado_expedientes` registra métricas, muestra notificaciones diferenciadas (advertencia solo si el estado quedó incompleto real), programa reintentos según configuración y desencadena comparación automática cuando procede.

Estados considerados "exitosos" (`completo`, `corte_controlado`) reinician el contador de reintentos y permiten la comparación posterior. Cualquier otro estado incrementa el contador, respeta límites y espera configurados y detiene los reintentos al agotarlos.

---

## 7. Flujo de verificación de entradas

El proceso de entradas replica la estructura anterior con particularidades:

1. `verificar_entradas` evita solapamiento de hilos, resuelve la ruta de monitoreo y programa el QThread con la carpeta de destino configurable.
2. `VerificadorEntradasV4` guarda el historial en JSON/CSV dentro del directorio, manejando errores de sesión y excepciones para emitir `ResultadoEntradas` consistente.
3. El manejador registra fallos o cantidad de novedades, respeta reintentos independientes y muestra notificaciones solo si hay cambios o si las preferencias lo permiten.

---

## 8. Gestión de reintentos y temporizadores

- **Temporizadores base**: se inicializan dos `QTimer` independientes (expedientes y entradas) con intervalos calculados según modo actual y ventana horaria. Cada timer se reinicia tras cada ejecución para mantener la cadencia.
- **Reintentos automáticos**: `reintentos_config` guarda `maximos` y `espera_segundos` por tipo. Si un flujo no termina en estado exitoso, programa `QTimer.singleShot` con la espera configurada; si los reintentos están en cero, se registra que fueron desactivados.
- **Actualización dinámica**: al guardar configuración se recalculan intervalos, tooltips y contadores para reflejar los valores nuevos sin reiniciar la aplicación.

---

## 9. Comparación de expedientes

`comparacion_expedientes.comparar_expedientes` encapsula el flujo completo:

1. Resuelve rutas considerando la configuración actual (`rutas.monitoreo`).
2. Normaliza el modo (`parcial` o `total`) y registra avisos sobre la estrategia utilizada.
3. Verifica la existencia de archivos actuales/base y devuelve faltantes en caso de ausencia.
4. Filtra la base por fecha de corte cuando el modo es parcial (si existe helper y fecha válida), registrando cuántos expedientes se descartaron.
5. Invoca `comparar_con_base` para obtener listas de nuevos/modificados/eliminados.
6. Genera un informe JSON en `reportes/` cuando hay cambios, informando errores de escritura como avisos complementarios.

El monitor recopila los avisos devueltos, los vuelca al log y decide qué notificaciones mostrar en función de las preferencias (`notificaciones.comparacion_sin_cambios`, `comparacion_faltantes`). En modo de comparación total, también omite la fecha de corte al lanzar la verificación para mantener conjuntos compatibles.

---

## 10. Respaldo histórico guiado

`generar_respaldo_monitoreo` acepta el directorio de monitoreo, la carpeta de destino histórico y la lista de archivos a copiar. Crea subcarpetas con timestamp (`YYYYMMDD_HHMMSS`), reporta archivos copiados/omitidos y devuelve estructuras listas para registrar en el log. El monitor lo invoca desde el submenú de utilidades respetando las preferencias de notificación y actualizando el tooltip cuando corresponde.

---

## 11. Gestión de sesión

Las acciones "🔐 Estado de sesión" y "⚠️ Forzar nuevo login" reutilizan `SESSION_FILE` del módulo `auto_login`:

- `mostrar_estado_sesion` informa ruta, fecha de actualización, modo actual, intervalos vigentes y validez del JSON de cookies, manejando `FileNotFoundError`, `JSONDecodeError` y excepciones genéricas para evitar cierres inesperados.
- `forzar_login` elimina el archivo y notifica éxito, ausencia de sesión previa o errores en la eliminación.

---

## 12. Notificaciones y registro

Todas las acciones utilizan `registrar_log` para dejar trazabilidad con prefijos temáticos (📈, ⚠️, ❌, etc.). Las notificaciones en bandeja (`showMessage`) respetan las preferencias configuradas y alternan íconos informativos/advertencias según el estado devuelto. Los tooltips se actualizan al recalcular intervalos, mostrando la próxima ejecución estimada para expedientes y entradas.

---

## 13. Modo de comparación total vs. parcial

- **Modo parcial**: mantiene la fecha de corte activa tanto en la extracción como en la comparación de bases. Ideal para vigilancia diaria o ventanas acotadas. Si no se obtiene fecha válida, el helper registra un aviso y continúa con la base completa.
- **Modo total**: omite la fecha de corte en la extracción inicial y compara contra toda la base histórica, útil para auditorías completas. El monitor registra explícitamente esta decisión antes de lanzar el hilo.

El diálogo de configuración permite alternar entre modos y activar/desactivar la comparación automática tras cada verificación exitosa.

---

## 14. Estrategia de fallback y compatibilidad

El monitor aplica importaciones condicionales para funcionar tanto con la arquitectura v4 como con los módulos heredados de v3. Cuando un helper opcional (comparación, respaldo, fecha de corte) no está disponible, la aplicación deshabilita la acción correspondiente y registra instrucciones para habilitarla. Esto permite ejecutar la bandeja en entornos incompletos sin fallar en tiempo de importación.

---

## 15. Buenas prácticas operativas

1. **Mantener sincronizada la base histórica**: cuando se cambia el modo de comparación o la fecha de corte, regenerar `expedientes_monitor - base.json` con el mismo rango para evitar falsos positivos masivos.
2. **Respaldos regulares**: aprovechar la acción guiada o programar ejecuciones periódicas manuales para conservar historiales previos antes de auditorías.
3. **Monitorear logs**: revisar `registrar_log` para identificar problemas de autenticación, fallos de Playwright o configuraciones inválidas.
4. **Revisar preferencias tras actualizaciones**: la mezcla profunda preserva claves personalizadas, pero conviene abrir el diálogo tras cada actualización para validar que los valores reflejan las políticas vigentes.
5. **Ejecutar comparaciones totales con criterio**: solo cuando se requiera una auditoría completa, debido al mayor tiempo de ejecución y volumen de cambios reportados.

---

## 16. Escenarios comunes y respuestas del monitor

| Escenario | Comportamiento | Acción sugerida |
| --- | --- | --- |
| Corte alcanzado antes de recorrer todas las páginas | Estado `corte_controlado`, mantiene motivo original y notifica que la detención es esperada. No se reintenta automáticamente. | Validar que el filtro configurado sea el deseado; ejecutar comparación parcial para detectar novedades dentro del rango. |
| Falta `expedientes_monitor - base.json` | Comparación devuelve faltantes y no genera informe; la bandeja registra el aviso y evita notificar cambios inexistentes. | Volver a generar la base desde el directorio de monitoreo antes de repetir la comparación. |
| Error al copiar archivos en respaldo | `generar_respaldo_monitoreo` captura excepciones por archivo y las refleja en el resumen emitido al monitor. | Revisar permisos de escritura del destino configurado. |
| Sesión expirada | `mostrar_estado_sesion` informa ausencia o corrupción de `SESSION_FILE`; `verificar_expedientes`/`entradas` registran `sesion_no_disponible`. | Ejecutar "⚠️ Forzar nuevo login" y reintentar la operación. |

---

## 17. Extensiones futuras sugeridas

- Integrar utilidades adicionales en el submenú (apertura de carpeta de monitoreo, ejecución de informes personalizados, limpieza de historiales obsoletos).
- Incorporar métricas de rendimiento (duración de cada verificación, estadísticas de reintentos) en el log o en un panel complementario.
- Sincronizar ajustes con perfiles multiusuario (por ejemplo, almacenar configuraciones por cuenta de Windows/Linux) aprovechando la mezcla profunda de configuración existente.
- Añadir pruebas automatizadas para el diálogo de configuración utilizando `pytest-qt` y mocks de `guardar_config_monitor`.

---

## 18. Ejemplo de configuración completa

A continuación se presenta un ejemplo de archivo `config_monitor.json` con valores típicos de producción:

```json
{
  "modo": "automatico",
  "horario_laboral": {
    "dias": ["lunes", "martes", "miércoles", "jueves", "viernes"],
    "inicio": "08:00",
    "fin": "18:00",
    "intervalos": {
      "expedientes": 3600,
      "entradas": 1800
    }
  },
  "fuera_horario": {
    "intervalos": {
      "expedientes": 7200,
      "entradas": 3600
    }
  },
  "filtro_expedientes": {
    "modo": "ultimo_dia_habil",
    "dias_atras": 0,
    "orden": "fecha_desc"
  },
  "comparacion": {
    "modo": "parcial",
    "auto": true
  },
  "respaldo": {
    "destino": "datos_extraidos/monitoreo/historico",
    "archivos": [
      "expedientes_monitor.json",
      "expedientes_monitor - base.json",
      "notificaciones"
    ]
  },
  "rutas": {
    "monitoreo": "datos_extraidos/monitoreo"
  },
  "reintentos": {
    "expedientes": {
      "maximos": 3,
      "espera_segundos": 300
    },
    "entradas": {
      "maximos": 2,
      "espera_segundos": 180
    }
  },
  "notificaciones": {
    "comparacion_sin_cambios": false,
    "comparacion_faltantes": true,
    "respaldo": true
  }
}
```

---

Esta documentación consolida la arquitectura actual del monitor, su configuración, los flujos operativos y las herramientas complementarias, facilitando el mantenimiento y la incorporación de nuevas funcionalidades en iteraciones posteriores.
