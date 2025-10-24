# Documentación exhaustiva del monitor de expedientes y entradas (Sistema v4)

## 1. Propósito general

El módulo de monitorización de Sistema v4 ofrece una bandeja de sistema (system tray) que automatiza tres tareas clave del flujo PJN:

1. **Verificación periódica de expedientes** mediante Playwright, respetando ventanas horarias, filtros por fecha de corte y límites configurables.
2. **Sincronización de entradas y notificaciones** con almacenamiento JSON/CSV y seguimiento independiente de cadencias.
3. **Operaciones auxiliares** (comparación con base histórica, respaldos guiados, diagnóstico de sesión, forzado de login y edición completa de la configuración).

Todo el comportamiento se concentra en `monitor_entradas_expedientes_v4.py`, apoyándose en helpers especializados para configuración (`configuracion_modo.py`), comparación (`comparacion_expedientes.py`), respaldo (`respaldo_historico.py`) e íconos (`icono_base64.py`).【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1-L237】【F:Sistema_v4/monitor/configuracion_modo.py†L1-L97】【F:Sistema_v4/monitor/comparacion_expedientes.py†L1-L222】【F:Sistema_v4/monitor/respaldo_historico.py†L1-L72】

---

## 2. Componentes principales del monitor

| Componente | Responsabilidad | Detalles clave |
| --- | --- | --- |
| `MonitorExpedientesTray` | Inicializa Qt, crea el icono de bandeja y arma el menú contextual. Gestiona timers, hilos y persistencia de configuración. | Habilita acciones para verificar expedientes/entradas, utilidades, comparación manual, diálogo de configuración y salida. Controla reintentos, notificaciones y tooltips dinámicos.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L925-L1507】 |
| `VerificadorExpedientesV4` | Hilo `QThread` que ejecuta la extracción completa de expedientes. | Reutiliza la sesión automática, envía filtros de fecha y orden al helper Playwright, recopila metadatos, guarda JSON y devuelve un `ResultadoExpedientes` estructurado.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L925-L1221】 |
| `VerificadorEntradasV4` | Hilo `QThread` para sincronizar notificaciones. | Guarda historiales en JSON/CSV, maneja errores de sesión y reporta mediante `ResultadoEntradas`.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1223-L1285】 |
| `ConfiguracionDialog` | Diálogo PySide tabulado para editar `config_monitor.json`. | Agrupa pestañas (general, intervalos, filtro, reintentos, respaldo, notificaciones), añade ayudas, checkboxes por día, vista previa de corte y restauración de defaults.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L190-L835】 |
| `configuracion_modo.py` | Helper común de lectura/escritura de configuración. | Define defaults con bloques extendidos (rutas, reintentos, comparación, filtros), realiza mezcla profunda y reutiliza la lógica de fecha de corte heredada.【F:Sistema_v4/monitor/configuracion_modo.py†L5-L97】 |
| `comparacion_expedientes.py` | Servicio para comparar archivos actuales vs. base histórica. | Resuelve rutas, modos (parcial vs. total), filtra la base por fecha cuando corresponde y genera informes JSON con avisos detallados.【F:Sistema_v4/monitor/comparacion_expedientes.py†L1-L222】 |
| `respaldo_historico.py` | Utilidad para copias de seguridad guiadas. | Copia archivos seleccionados al destino histórico con timestamp, registrando copiados y omitidos.【F:Sistema_v4/monitor/respaldo_historico.py†L1-L72】 |

---

## 3. Estructura de archivos y directorios

Por defecto, el monitor trabaja dentro de `datos_extraidos/monitoreo`, carpeta que concentra:

* `expedientes_monitor.json`: última extracción exitosa de expedientes.
* `expedientes_monitor - base.json`: archivo de referencia para comparación.
* `notificaciones/` (subcarpeta generada por Playwright) con historiales JSON/CSV.
* `reportes/`: informes generados por las comparaciones.
* `historico/`: destino por defecto de los respaldos programados.【F:Sistema_v4/monitor/configuracion_modo.py†L16-L55】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1321-L1429】【F:Sistema_v4/monitor/comparacion_expedientes.py†L55-L133】【F:Sistema_v4/monitor/respaldo_historico.py†L4-L72】

Los caminos pueden personalizarse desde el diálogo de configuración (pestañas General y Respaldo) para adaptarse a entornos de producción sin modificar el código.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L420-L621】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1568-L1638】

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
- `notificaciones`: banderas que gobiernan los toasts de comparación y respaldo.【F:Sistema_v4/monitor/configuracion_modo.py†L16-L71】

### 4.2 Carga y persistencia

`cargar_config_monitor` lee el archivo, inyecta defaults faltantes y devuelve siempre un diccionario completo; `guardar_config_monitor` persiste usando UTF-8 y crea directorios intermedios. `actualizar_modo_monitor` valida los modos antes de escribir. `obtener_fecha_corte` delega en el helper heredado para mantener paridad con versiones previas.【F:Sistema_v4/monitor/configuracion_modo.py†L33-L97】

### 4.3 Edición interactiva

`ConfiguracionDialog` inicializa los controles desde la configuración actual, aplica validaciones in situ (por ejemplo, rutas existentes, intervalos positivos, días laborales mediante checkboxes) y muestra una vista previa dinámica de la fecha resultante. Al guardar, realiza una mezcla profunda para preservar claves personalizadas y reinicia temporizadores/tooltips de inmediato.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L190-L835】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1806-L1845】

---

## 5. Menú de bandeja y acciones disponibles

| Acción | Descripción | Consideraciones |
| --- | --- | --- |
| `📥 Verificar expedientes` | Lanza `VerificadorExpedientesV4` respetando filtros, orden y rutas configuradas. | Deshabilita la acción mientras el hilo corre, muestra progreso en logs y notifica con estado/resumen al finalizar.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L925-L1507】 |
| `📤 Verificar entradas` | Ejecuta `VerificadorEntradasV4` guardando JSON/CSV en el directorio configurado. | Gestiona reintentos, diferencia errores de sesión y notifica cantidad de novedades.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1223-L1507】 |
| `🧪 Comparar expedientes` | Compara manualmente contra la base histórica si el helper está disponible. | Deshabilitada automáticamente cuando falta `comparacion_expedientes.py` o las dependencias de comparación; respeta preferencias de notificación.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L34-L105】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1497-L1779】 |
| `🛠️ Modo de trabajo` | Submenú con opciones chequeables (`automatico`, `laboral`, `no_laboral`). | Actualiza el JSON, recalcula temporizadores y tooltips y registra el cambio en el log.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1007-L1279】 |
| `🧰 Utilidades` | Agrupa estado de sesión, forzado de login, respaldo guiado y marcador para futuras herramientas. | `mostrar_estado_sesion` diagnostica `SESSION_FILE`, `forzar_login` lo elimina, `respaldar_resultados` invoca `generar_respaldo_monitoreo`.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1007-L1707】【F:Sistema_v4/monitor/respaldo_historico.py†L4-L72】 |
| `⚙️ Configuración…` | Abre el diálogo de configuración descrito arriba. | Permite restablecer defaults, valida datos y persiste cambios inmediatos.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L190-L835】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1806-L1845】 |
| `🛑 Salir` | Cierra la aplicación y detiene timers/hilos en ejecución. | Libera la bandeja y termina el proceso Qt.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L925-L1507】 |

---

## 6. Flujo de verificación de expedientes

1. **Preparación del hilo**: `verificar_expedientes` valida que no exista una ejecución en curso, determina directorios de salida, resuelve configuración (incluyendo modo de comparación para omitir la fecha de corte en modo total), traduce la fecha ISO a `DD/MM/AAAA` y registra parámetros iniciales.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1274-L1341】
2. **Ejecución Playwright**: `VerificadorExpedientesV4` reutiliza la sesión automatizada, navega a `URL_CONSULTAS` e invoca `extraer_expedientes_completos` con orden y fecha de corte. El helper devuelve expedientes, motivo y metadatos de paginación/descartes.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L925-L1069】
3. **Procesamiento de resultados**: el hilo guarda el JSON (si corresponde), normaliza estados, preserva motivos controlados (`limite_fecha`, `limite_tiempo`, etc.) para evitar falsos “total_incompleto” y emite un `ResultadoExpedientes` con totales, motivo original, páginas recorridas, descartes y ruta final.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1045-L1221】
4. **Post-proceso en la bandeja**: `procesar_resultado_expedientes` registra métricas, muestra notificaciones diferenciadas (advertencia solo si el estado quedó incompleto real), programa reintentos según configuración y desencadena comparación automática cuando procede.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1348-L1510】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1469-L1510】

Estados considerados “exitosos” (`completo`, `corte_controlado`) reinician el contador de reintentos y permiten la comparación posterior. Cualquier otro estado incrementa el contador, respeta límites y espera configurados y detiene los reintentos al agotarlos.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1469-L1510】

---

## 7. Flujo de verificación de entradas

El proceso de entradas replica la estructura anterior con particularidades:

1. `verificar_entradas` evita solapamiento de hilos, resuelve la ruta de monitoreo y programa el QThread con la carpeta de destino configurable.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1429-L1468】
2. `VerificadorEntradasV4` guarda el historial en JSON/CSV dentro del directorio, manejando errores de sesión y excepciones para emitir `ResultadoEntradas` consistente.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1223-L1285】
3. El manejador registra fallos o cantidad de novedades, respeta reintentos independientes y muestra notificaciones solo si hay cambios o si las preferencias lo permiten.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1512-L1566】

---

## 8. Gestión de reintentos y temporizadores

- **Temporizadores base**: se inicializan dos `QTimer` independientes (expedientes y entradas) con intervalos calculados según modo actual y ventana horaria. Cada timer se reinicia tras cada ejecución para mantener la cadencia.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1348-L1429】
- **Reintentos automáticos**: `reintentos_config` guarda `maximos` y `espera_segundos` por tipo. Si un flujo no termina en estado exitoso, programa `QTimer.singleShot` con la espera configurada; si los reintentos están en cero, se registra que fueron desactivados.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1469-L1545】
- **Actualización dinámica**: al guardar configuración se recalculan intervalos, tooltips y contadores para reflejar los valores nuevos sin reiniciar la aplicación.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L607-L704】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1806-L1845】

---

## 9. Comparación de expedientes

`comparacion_expedientes.comparar_expedientes` encapsula el flujo completo:

1. Resuelve rutas considerando la configuración actual (`rutas.monitoreo`).
2. Normaliza el modo (`parcial` o `total`) y registra avisos sobre la estrategia utilizada.
3. Verifica la existencia de archivos actuales/base y devuelve faltantes en caso de ausencia.
4. Filtra la base por fecha de corte cuando el modo es parcial (si existe helper y fecha válida), registrando cuántos expedientes se descartaron.
5. Invoca `comparar_con_base` para obtener listas de nuevos/modificados/eliminados.
6. Genera un informe JSON en `reportes/` cuando hay cambios, informando errores de escritura como avisos complementarios.【F:Sistema_v4/monitor/comparacion_expedientes.py†L52-L222】

El monitor recopila los avisos devueltos, los vuelca al log y decide qué notificaciones mostrar en función de las preferencias (`notificaciones.comparacion_sin_cambios`, `comparacion_faltantes`). En modo de comparación total, también omite la fecha de corte al lanzar la verificación para mantener conjuntos compatibles.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L34-L105】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1274-L1341】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1497-L1779】

---

## 10. Respaldo histórico guiado

`generar_respaldo_monitoreo` acepta el directorio de monitoreo, la carpeta de destino histórico y la lista de archivos a copiar. Crea subcarpetas con timestamp (`YYYYMMDD_HHMMSS`), reporta archivos copiados/omitidos y devuelve estructuras listas para registrar en el log. El monitor lo invoca desde el submenú de utilidades respetando las preferencias de notificación y actualizando el tooltip cuando corresponde.【F:Sistema_v4/monitor/respaldo_historico.py†L4-L72】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1568-L1638】

---

## 11. Gestión de sesión

Las acciones “🔐 Estado de sesión” y “⚠️ Forzar nuevo login” reutilizan `SESSION_FILE` del módulo `auto_login`:

- `mostrar_estado_sesion` informa ruta, fecha de actualización, modo actual, intervalos vigentes y validez del JSON de cookies, manejando `FileNotFoundError`, `JSONDecodeError` y excepciones genéricas para evitar cierres inesperados.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1641-L1687】
- `forzar_login` elimina el archivo y notifica éxito, ausencia de sesión previa o errores en la eliminación.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1688-L1707】

---

## 12. Notificaciones y registro

Todas las acciones utilizan `registrar_log` para dejar trazabilidad con prefijos temáticos (📈, ⚠️, ❌, etc.). Las notificaciones en bandeja (`showMessage`) respetan las preferencias configuradas y alternan íconos informativos/advertencias según el estado devuelto. Los tooltips se actualizan al recalcular intervalos, mostrando la próxima ejecución estimada para expedientes y entradas.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1184-L1334】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1348-L1510】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1568-L1687】

---

## 13. Modo de comparación total vs. parcial

- **Modo parcial**: mantiene la fecha de corte activa tanto en la extracción como en la comparación de bases. Ideal para vigilancia diaria o ventanas acotadas. Si no se obtiene fecha válida, el helper registra un aviso y continúa con la base completa.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1274-L1341】【F:Sistema_v4/monitor/comparacion_expedientes.py†L83-L222】
- **Modo total**: omite la fecha de corte en la extracción inicial y compara contra toda la base histórica, útil para auditorías completas. El monitor registra explícitamente esta decisión antes de lanzar el hilo.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1274-L1341】【F:Sistema_v4/monitor/comparacion_expedientes.py†L83-L133】

El diálogo de configuración permite alternar entre modos y activar/desactivar la comparación automática tras cada verificación exitosa.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L190-L835】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1497-L1510】

---

## 14. Estrategia de fallback y compatibilidad

El monitor aplica importaciones condicionales para funcionar tanto con la arquitectura v4 como con los módulos heredados de v3. Cuando un helper opcional (comparación, respaldo, fecha de corte) no está disponible, la aplicación deshabilita la acción correspondiente y registra instrucciones para habilitarla. Esto permite ejecutar la bandeja en entornos incompletos sin fallar en tiempo de importación.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L34-L187】【F:Sistema_v4/monitor/comparacion_expedientes.py†L1-L52】

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
| Corte alcanzado antes de recorrer todas las páginas | Estado `corte_controlado`, mantiene motivo original y notifica que la detención es esperada. No se reintenta automáticamente. | Validar que el filtro configurado sea el deseado; ejecutar comparación parcial para detectar novedades dentro del rango. 【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1348-L1510】 |
| Falta `expedientes_monitor - base.json` | Comparación devuelve faltantes y no genera informe; la bandeja registra el aviso y evita notificar cambios inexistentes. | Volver a generar la base desde el directorio de monitoreo antes de repetir la comparación. 【F:Sistema_v4/monitor/comparacion_expedientes.py†L101-L140】 |
| Error al copiar archivos en respaldo | `generar_respaldo_monitoreo` captura excepciones por archivo y las refleja en el resumen emitido al monitor. | Revisar permisos de escritura del destino configurado. 【F:Sistema_v4/monitor/respaldo_historico.py†L4-L72】 |
| Sesión expirada | `mostrar_estado_sesion` informa ausencia o corrupción de `SESSION_FILE`; `verificar_expedientes`/`entradas` registran `sesion_no_disponible`. | Ejecutar “⚠️ Forzar nuevo login” y reintentar la operación. 【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L1512-L1687】 |

---

## 17. Extensiones futuras sugeridas

- Integrar utilidades adicionales en el submenú (apertura de carpeta de monitoreo, ejecución de informes personalizados, limpieza de historiales obsoletos).
- Incorporar métricas de rendimiento (duración de cada verificación, estadísticas de reintentos) en el log o en un panel complementario.
- Sincronizar ajustes con perfiles multiusuario (por ejemplo, almacenar configuraciones por cuenta de Windows/Linux) aprovechando la mezcla profunda de configuración existente.
- Añadir pruebas automatizadas para el diálogo de configuración utilizando `pytest-qt` y mocks de `guardar_config_monitor`.

Esta documentación consolida la arquitectura actual del monitor, su configuración, los flujos operativos y las herramientas complementarias, facilitando el mantenimiento y la incorporación de nuevas funcionalidades en iteraciones posteriores.
