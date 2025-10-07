# Monitor de expedientes y entradas (Sistema v4)

Este módulo implementa la bandeja de sistema que automatiza la verificación de expedientes y entradas del PJN utilizando Qt/PySide. Actualmente concentra la lógica en `monitor_entradas_expedientes_v4.py` y mantiene un icono embebido en `icono_base64.py`.

## Estado actual

* La bandeja crea accesos rápidos para ejecutar la verificación de expedientes y de entradas, mostrando mensajes y registrando métricas detalladas (totales esperados, descartes, paginación, rutas de guardado, etc.).【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L168-L247】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L357-L433】
* La configuración lee `config/config_monitor.json`, soporta modos `automatico`, `laboral` y `no_laboral`, expone un bloque `filtro_expedientes` con las opciones heredadas (`hoy`, `ultimo_dia_habil`, `dias_atras`, combinadas) y ahora puede modificarse desde el submenú “🛠️ Modo de trabajo”, que actualiza la configuración y reinicia los temporizadores al vuelo.【F:Sistema_v4/monitor/configuracion_modo.py†L8-L97】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L330-L414】
* Se restableció el hilo de entradas (`VerificadorEntradasV4`) que guarda historiales JSON/CSV dentro de la carpeta configurada para el monitoreo.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L263-L339】
* El submenú “🧰 Utilidades” incorpora las acciones “🔐 Estado de sesión” y “⚠️ Forzar nuevo login”, reutilizando `SESSION_FILE` para diagnosticar la cookie guardada y permitir su limpieza desde la bandeja.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L324-L346】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L573-L667】
* Se reactivó la comparación automática y manual de expedientes mediante el helper `comparar_expedientes`, notificando cambios desde la bandeja y registrando los informes generados en `datos_extraidos/monitoreo/reportes`. Si el helper no está disponible en la instalación, la acción queda deshabilitada y se informa al operador.【F:Sistema_v4/monitor/comparacion_expedientes.py†L1-L89】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L351-L361】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L523-L570】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L796-L813】
* El submenú “🧰 Utilidades” incorpora un respaldo guiado que copia los resultados recientes (expedientes y notificaciones) a una carpeta histórica con sello de tiempo configurable desde `config_monitor.json`, registrando archivos copiados y ausentes.【F:Sistema_v4/monitor/respaldo_historico.py†L1-L72】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L372-L430】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L675-L725】

## Capacidades del monitor general anterior (Sistema v2/core)

El monitor heredado ofrecía una bandeja más completa con acciones adicionales que hoy no están disponibles en v4.【F:core/modulos_monitor/general/monitor_general.py†L30-L49】 Entre las herramientas destacadas se incluyen:

* **Cambio de modo desde la bandeja**: un submenú permitía seleccionar `automatico`, `laboral` o `no_laboral`, actualizando el archivo de configuración y reiniciando los temporizadores inmediatamente.【F:core/modulos_monitor/general/monitor_general.py†L37-L45】【F:core/modulos_monitor/general/monitor_general.py†L223-L235】
* **Gestión de sesión**: había accesos para visualizar el estado del login guardado (leyendo `SESSION_FILE`) y para forzar un nuevo login eliminando la sesión persistida.【F:core/modulos_monitor/general/monitor_general.py†L33-L47】【F:core/modulos_monitor/general/monitor_general.py†L237-L277】
* **Comparación automática y manual de expedientes**: tras una verificación exitosa se disparaba una comparación contra una base anterior y el menú incluía una acción manual para repetirla.【F:core/modulos_monitor/general/monitor_general.py†L162-L198】【F:core/modulos_monitor/general/monitor_general.py†L282-L298】
* **Respaldo rápido**: un comando de la bandeja copiaba los últimos JSON de expedientes y notificaciones a una carpeta histórica con sello de tiempo.【F:core/modulos_monitor/general/monitor_general.py†L202-L222】

## Plan de mejoras para Sistema v4

Para facilitar la ejecución iterativa, las tareas se ordenan de menor a mayor dependencia y se detallan los pasos clave de cada una.

1. ✅ **Reintroducir la gestión interactiva del modo de trabajo**. El helper `configuracion_modo.py` centraliza la lectura/escritura de `config_monitor.json`, el submenú “🛠️ Modo de trabajo” expone las opciones disponibles y cada cambio reinicia los temporizadores y tooltips para reflejar el nuevo intervalo.【F:Sistema_v4/monitor/configuracion_modo.py†L8-L69】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L330-L462】
2. ✅ **Portar las utilidades de sesión**. Se reutiliza `SESSION_FILE` para informar el estado desde la bandeja, capturando errores de lectura y permitiendo eliminar la cookie persistida mediante las acciones del submenú de utilidades.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L314-L336】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L563-L657】

### Verificación del punto 2

* El submenú “🧰 Utilidades” crea las acciones “🔐 Estado de sesión” y “⚠️ Forzar nuevo login” conectándolas con los handlers `mostrar_estado_sesion` y `forzar_login` respectivamente.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L377-L401】
* `mostrar_estado_sesion` lee `SESSION_FILE`, diagnostica la validez de la cookie y expone información contextual (modo, intervalo, ruta y marca de tiempo), gestionando las excepciones heredadas para evitar cierres inesperados.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L703-L740】
* `forzar_login` elimina la cookie persistida, registra el resultado y notifica tanto éxito como fallos o ausencia de sesión, alineándose con el comportamiento del monitor legado.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L742-L757】

### Verificación del punto 3

* El menú principal incorpora la acción “🧪 Comparar expedientes”, que reutiliza el helper compartido para ejecutar el diff desde la bandeja.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L348-L351】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L523-L570】
* Tras cada verificación exitosa se dispara una comparación automática, registrando el resultado y evitando notificaciones invasivas cuando faltan archivos base.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L488-L570】
* `comparacion_expedientes.py` centraliza la resolución de rutas, el manejo de faltantes y la detección del informe generado, permitiendo reutilizar la lógica desde distintas acciones.【F:Sistema_v4/monitor/comparacion_expedientes.py†L1-L89】

### Utilidades de sesión en la bandeja v4

El submenú “🧰 Utilidades” replica el flujo del monitor legado: al pulsar “🔐 Estado de sesión” se intenta leer `SESSION_FILE` y se muestran mensajes diferenciados para sesión activa, incompleta o inexistente, junto con el modo actual, el intervalo configurado y la fecha de última actualización del archivo cuando está disponible.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L563-L626】

Se capturan explícitamente los errores `FileNotFoundError`, `JSONDecodeError` y cualquier excepción inesperada para evitar que la bandeja se cierre ante sesiones dañadas, registrando además el resultado en el log.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L574-L620】

La acción “⚠️ Forzar nuevo login” elimina `SESSION_FILE` cuando existe y notifica al operador si no se encontró una sesión previa o si ocurrió un error durante la eliminación, dejando registro en el log en todos los casos.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L628-L657】

3. ✅ **Reactivar la comparación de expedientes**
   1. Encapsular el flujo de comparación en un servicio reutilizable (auto/manual).
   2. Invocar el servicio al cierre exitoso de una verificación.
   3. Añadir una acción manual que permita relanzar la comparación bajo demanda.【F:Sistema_v4/monitor/comparacion_expedientes.py†L1-L89】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L348-L351】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L488-L570】
4. ✅ **Añadir respaldos históricos guiados**
   1. `respaldo_historico.py` encapsula la copia de resultados a carpetas con timestamp reutilizando la lista de archivos monitoreados.【F:Sistema_v4/monitor/respaldo_historico.py†L1-L72】
   2. La configuración admite `respaldo.destino` para personalizar el directorio histórico, manteniendo un valor por defecto en `DEFAULT_CONFIG`.【F:Sistema_v4/monitor/configuracion_modo.py†L11-L23】
   3. La acción “🗄️ Respaldar últimos resultados” notifica los archivos copiados o ausentes y registra los detalles en el log de la bandeja.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L372-L430】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L675-L725】
5. **Completar el placeholder de utilidades**
   1. Incorporar las acciones anteriores dentro del menú reservado.
   2. Evaluar utilidades adicionales (abrir carpeta de resultados, ejecutar informes) y documentarlas.
   3. Estabilizar el layout del menú para futuras extensiones.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L316-L333】
6. **Revisar la estrategia de reintentos**
   1. Separar las configuraciones de intervalo/reintentos entre expedientes y entradas.
   2. Permitir parámetros de reintento en `config_monitor.json` (intentos máximos, backoff).
   3. Adaptar el log para reflejar la nueva estrategia y alinearla con los escenarios heredados.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L412-L465】【F:core/modulos_monitor/general/monitor_general.py†L153-L199】
7. **Incorporar filtro por fecha de corte en la bandeja v4**
   1. ✅ Reutilizar `obtener_fecha_corte` del monitor heredado para exponer un bloque `filtro_expedientes` en `config_monitor.json`, documentando los modos (`hoy`, `ultimo_dia_habil`, `dias_atras`, combinados) y validaciones actuales.【F:Sistema_v4/monitor/configuracion_modo.py†L8-L97】【F:core/modulos_monitor/expedientes_modular/verificacion_expedientes.py†L19-L70】
   2. ✅ Al iniciar `VerificadorExpedientesV4`, resolver la fecha de corte y convertirla al formato esperado antes de invocar el hilo Playwright, replicando la traducción a `DD/MM/AAAA` que hoy realiza el monitor general.【F:core/modulos_monitor/expedientes_modular/verificacion_expedientes.py†L96-L158】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L173-L232】
   3. Propagar la fecha al flujo asincrónico de expedientes v4 para que detenga el barrido con motivo `limite_fecha/corte_fecha`, registrando totales y motivos igual que en v2/v3.【F:Sistema_v4/operaciones/expedientes/expedientes_v4.py†L217-L407】【F:Sistema_v3/operaciones/expedientes/expedientes_v4.py†L197-L360】
   4. Exponer en la interfaz (tooltip, notificación o diálogo) el motivo `corte_fecha` cuando el hilo se detenga por el umbral, manteniendo paridad con el mensaje usado por la bandeja heredada.【F:core/modulos_monitor/general/monitor_general.py†L120-L158】

### Configuración del filtro de expedientes

El bloque `filtro_expedientes` de `config_monitor.json` replica los modos soportados en el monitor heredado y permite ajustar el comportamiento del hilo sin editar código. Los campos disponibles son:

* `modo`: acepta `hoy`, `ultimo_dia_habil`, `dias_atras`, `hoy+ultimo_dia_habil`, `completo`/`sin_corte`/`none` y cadenas vacías para desactivar el filtro. El valor por defecto es `ultimo_dia_habil`.
* `dias_atras`: entero utilizado cuando `modo` es `dias_atras` para restar días a partir de la fecha actual. El helper heredado ignora valores no numéricos y omite el corte si se ingresa un dato inválido.
* `orden`: ordenamiento a solicitar al backend de expedientes (por ejemplo, `fecha` como valor predeterminado).

La función `obtener_fecha_corte` del módulo `configuracion_modo` delega en el helper compartido del monitor legado, garantizando que cualquier ajuste de configuración se traduzca en fechas ISO (`YYYY-MM-DD`) compatibles con los hilos existentes.【F:Sistema_v4/monitor/configuracion_modo.py†L8-L97】【F:core/modulos_monitor/expedientes_modular/verificacion_expedientes.py†L19-L70】

El monitor v4 traduce automáticamente esa fecha al formato `DD/MM/AAAA` antes de lanzar la extracción y la envía junto con el orden configurado al hilo Playwright, lo que habilita el motivo `limite_fecha` cuando el barrido alcanza el umbral temporal.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L173-L232】

Completar estas tareas en orden desbloquea dependencias graduales y garantiza que el monitor v4 recupere las capacidades críticas del monitor general v2 antes de que el legado sea descartado.
