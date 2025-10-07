# Monitor de expedientes y entradas (Sistema v4)

Este módulo implementa la bandeja de sistema que automatiza la verificación de expedientes y entradas del PJN utilizando Qt/PySide. Actualmente concentra la lógica en `monitor_entradas_expedientes_v4.py` y mantiene un icono embebido en `icono_base64.py`.

## Estado actual

* La bandeja crea accesos rápidos para ejecutar la verificación de expedientes y de entradas, mostrando mensajes y registrando métricas detalladas (totales esperados, descartes, paginación, rutas de guardado, etc.).【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L168-L247】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L357-L433】
* La configuración lee `config/config_monitor.json` y soporta modos `automatico`, `laboral` y `no_laboral`, pero el modo sólo puede modificarse editando el archivo porque aún no existe UI para cambiarlo.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L88-L156】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L369-L412】
* Se restableció el hilo de entradas (`VerificadorEntradasV4`) que guarda historiales JSON/CSV dentro de la carpeta configurada para el monitoreo.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L263-L339】
* El menú contiene un marcador de posición para “utilidades adicionales” hasta que se complete la migración de herramientas heredadas.【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L316-L333】

## Capacidades del monitor general anterior (Sistema v2/core)

El monitor heredado ofrecía una bandeja más completa con acciones adicionales que hoy no están disponibles en v4.【F:core/modulos_monitor/general/monitor_general.py†L30-L49】 Entre las herramientas destacadas se incluyen:

* **Cambio de modo desde la bandeja**: un submenú permitía seleccionar `automatico`, `laboral` o `no_laboral`, actualizando el archivo de configuración y reiniciando los temporizadores inmediatamente.【F:core/modulos_monitor/general/monitor_general.py†L37-L45】【F:core/modulos_monitor/general/monitor_general.py†L223-L235】
* **Gestión de sesión**: había accesos para visualizar el estado del login guardado (leyendo `SESSION_FILE`) y para forzar un nuevo login eliminando la sesión persistida.【F:core/modulos_monitor/general/monitor_general.py†L33-L47】【F:core/modulos_monitor/general/monitor_general.py†L237-L277】
* **Comparación automática y manual de expedientes**: tras una verificación exitosa se disparaba una comparación contra una base anterior y el menú incluía una acción manual para repetirla.【F:core/modulos_monitor/general/monitor_general.py†L162-L198】【F:core/modulos_monitor/general/monitor_general.py†L282-L298】
* **Respaldo rápido**: un comando de la bandeja copiaba los últimos JSON de expedientes y notificaciones a una carpeta histórica con sello de tiempo.【F:core/modulos_monitor/general/monitor_general.py†L202-L222】

## Plan de mejoras para Sistema v4

Para facilitar la ejecución iterativa, las tareas se ordenan de menor a mayor dependencia y se detallan los pasos clave de cada una.

1. **Reintroducir la gestión interactiva del modo de trabajo**
   1. Leer/escribir `config_monitor.json` con un helper único para ambos monitores.
   2. Agregar el submenú “Cambiar modo” y enlazar cada acción con el helper anterior.
   3. Reiniciar temporizadores y actualizar tooltips/notificaciones tras el cambio.【F:core/modulos_monitor/general/monitor_general.py†L37-L45】【F:Sistema_v4/monitor/monitor_entradas_expedientes_v4.py†L369-L412】
2. **Portar las utilidades de sesión**
   1. Mapear la ubicación del `SESSION_FILE` en v4 y validar si existe.
   2. Crear acciones “Ver estado de sesión” y “Forzar login” reutilizando los mensajes existentes.
   3. Integrar ambas acciones al menú de utilidades.【F:core/modulos_monitor/general/monitor_general.py†L33-L47】【F:core/modulos_monitor/general/monitor_general.py†L237-L277】
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
