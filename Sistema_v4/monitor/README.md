# Monitor de expedientes y entradas (Sistema v4)

Este módulo implementa la bandeja de sistema que automatiza la verificación de expedientes y entradas del PJN utilizando Qt/PySide. Actualmente concentra la lógica en `monitor_entradas_expedientes_v4.py` y mantiene un icono embebido en `icono_base64.py`.

## Estado actual

* La bandeja crea accesos rápidos para ejecutar la verificación de expedientes y de entradas, mostrando mensajes y registrando métricas detalladas (totales esperados, descartes, paginación, rutas de guardado, etc.).【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L168-L247】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L357-L433】
* La configuración lee `config/config_monitor.json`, soporta modos `automatico`, `laboral` y `no_laboral` y ahora puede modificarse desde el submenú “🛠️ Modo de trabajo”, que actualiza la configuración y reinicia los temporizadores al vuelo.【F:Sistema_v4/monitor/configuracion_modo.py†L8-L69】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L330-L414】
* Se restableció el hilo de entradas (`VerificadorEntradasV4`) que guarda historiales JSON/CSV dentro de la carpeta configurada para el monitoreo.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L263-L339】
* El submenú “🧰 Utilidades” incorpora las acciones “🔐 Estado de sesión” y “⚠️ Forzar nuevo login”, reutilizando `SESSION_FILE` para diagnosticar la cookie guardada y permitir su limpieza desde la bandeja.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L314-L336】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L563-L657】

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

### Utilidades de sesión en la bandeja v4

El submenú “🧰 Utilidades” replica el flujo del monitor legado: al pulsar “🔐 Estado de sesión” se intenta leer `SESSION_FILE` y se muestran mensajes diferenciados para sesión activa, incompleta o inexistente, junto con el modo actual, el intervalo configurado y la fecha de última actualización del archivo cuando está disponible.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L563-L626】

Se capturan explícitamente los errores `FileNotFoundError`, `JSONDecodeError` y cualquier excepción inesperada para evitar que la bandeja se cierre ante sesiones dañadas, registrando además el resultado en el log.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L574-L620】

La acción “⚠️ Forzar nuevo login” elimina `SESSION_FILE` cuando existe y notifica al operador si no se encontró una sesión previa o si ocurrió un error durante la eliminación, dejando registro en el log en todos los casos.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L628-L657】

3. **Reactivar la comparación de expedientes**
   1. Encapsular el flujo de comparación en un servicio reutilizable (auto/manual).
   2. Invocar el servicio al cierre exitoso de una verificación.
   3. Añadir una acción manual que permita relanzar la comparación bajo demanda.【F:core/modulos_monitor/general/monitor_general.py†L162-L198】【F:core/modulos_monitor/general/monitor_general.py†L282-L298】
4. **Añadir respaldos históricos guiados**
   1. Implementar un helper que copie los últimos JSON/CSV a una carpeta con timestamp.
   2. Permitir seleccionar la ubicación de respaldo desde la configuración.
   3. Exponer la acción en el menú y notificar el resultado al usuario.【F:core/modulos_monitor/general/monitor_general.py†L202-L222】
5. **Completar el placeholder de utilidades**
   1. Incorporar las acciones anteriores dentro del menú reservado.
   2. Evaluar utilidades adicionales (abrir carpeta de resultados, ejecutar informes) y documentarlas.
   3. Estabilizar el layout del menú para futuras extensiones.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L316-L333】
6. **Revisar la estrategia de reintentos**
   1. Separar las configuraciones de intervalo/reintentos entre expedientes y entradas.
   2. Permitir parámetros de reintento en `config_monitor.json` (intentos máximos, backoff).
   3. Adaptar el log para reflejar la nueva estrategia y alinearla con los escenarios heredados.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L412-L465】【F:core/modulos_monitor/general/monitor_general.py†L153-L199】

Completar estas tareas en orden desbloquea dependencias graduales y garantiza que el monitor v4 recupere las capacidades críticas del monitor general v2 antes de que el legado sea descartado.
