# Mejoras pendientes para la Web App del Monitor PJN

## Configuración y validaciones
- ~~Exponer en la interfaz los campos restantes de `MonitorConfig` (intervalos fuera de horario, límites de reintentos, horario laboral) y validar los valores antes de persistirlos para reducir la edición manual del JSON.~~ ✅ Implementado en la UI de configuración con validaciones de entrada.
- ~~Permitir la carga/descarga del archivo `monitor.json` desde la web para facilitar respaldos y restauraciones rápidas.~~ ✅ Botones dedicados de importación/exportación disponibles.

## Experiencia de usuario
- ~~Agregar un indicador visual cuando el monitor se encuentra inicializando o deteniéndose que bloquee acciones repetidas mientras se completa la operación.~~ ✅ Overlay de estado bloquea interacciones redundantes.
- ~~Mostrar el PID y la hora de arranque también cuando el monitor estaba activo antes de abrir el dashboard, extendiendo el endpoint `/api/monitor/status`.~~ ✅ El endpoint retorna metadatos persistidos.

## Observabilidad
- ~~Registrar los intentos de arranque/detención del monitor en un log específico o en la base de datos para auditoría.~~ ✅ Se escribe en `logs/monitor_web_actions.log`.
- ~~Exponer métricas (por ejemplo, número de entradas nuevas en las últimas 24h) mediante un endpoint JSON para integraciones externas o paneles de monitoreo.~~ ✅ Nuevo endpoint `/api/metrics`.

## Calidad del código
- Añadir pruebas unitarias para `get_monitor_config`, `get_storage` y los endpoints JSON, usando fixtures de datos persistentes para prevenir regresiones.
- Aplicar un formateador consistente (por ejemplo, `black`/`ruff`) y configurar CI para ejecutarlo en cada commit.
