# Revisión de Sistema_v5 / Web App

## Problemas detectados

1. **Las plantillas usan atributos inexistentes en los modelos.**
   - En el dashboard se accede a `entrada.expediente`, `entrada.tipo` y `entrada.contenido`, pero el modelo `Entrada` solo expone `numero`, `tipo_evento` y `evento`/`extraida_en`. Estas referencias producirán valores vacíos o errores al renderizar.【F:Sistema_v5/web_app/templates/dashboard.html†L288-L304】【F:Sistema_v5/pjn/models/entrada.py†L10-L41】
   - El listado de entradas repite el mismo patrón (`entrada.expediente`, `entrada.tipo`, `entrada.contenido`, `entrada.detectada_en`), que tampoco existen en `Entrada`. Esto impide mostrar la información real del monitoreo.【F:Sistema_v5/web_app/templates/entradas.html†L18-L35】【F:Sistema_v5/pjn/models/entrada.py†L10-L41】
   - Las tablas de expedientes esperan campos como `exp.expediente`, `exp.organismo`, `exp.actuaciones_count`, `exp.estado_hash` o `exp.detectado_en`, pero `ExpedienteResumen` solo tiene `numero`, `dependencia`, `caratula`, `situacion` y `ultima_actuacion`. El resultado es que las columnas se renderizarán vacías o causarán excepciones.【F:Sistema_v5/web_app/templates/dashboard.html†L309-L324】【F:Sistema_v5/web_app/templates/expedientes.html†L18-L42】【F:Sistema_v5/pjn/models/expediente.py†L10-L40】

2. **Inconsistencias entre la configuración del monitor y el formulario web.**
   - El formulario ofrece modos `todo`, `entradas` y `expedientes`, mientras que `MonitorConfig.modo` solo acepta `automatico`, `laboral` o `no_laboral`. Guardar la configuración desde la web deja el sistema en un estado no soportado.【F:Sistema_v5/web_app/templates/config.html†L16-L24】【F:Sistema_v5/pjn/monitor/config.py†L15-L103】
   - El endpoint `/config/update` convierte valores numéricos con `int(...)` sin validar cadenas vacías. Si el usuario borra un campo numérico, Flask enviará `""` y se lanzará un `ValueError`, devolviendo un 500 en vez de un mensaje controlado.【F:Sistema_v5/web_app/app.py†L160-L188】

3. **Gestión de procesos del monitor poco portable.**
   - La ruta `/api/monitor/start` busca un ejecutable fijo en `.venv/Scripts/python.exe`, un layout exclusivo de Windows. En Linux o macOS (o si no existe esa carpeta) el monitor no arrancará. Es preferible usar `sys.executable` o permitir configurar la ruta desde el JSON.【F:Sistema_v5/web_app/app.py†L30-L188】

4. **Oportunidades de mejora adicionales.**
   - `get_storage()` inicializa `StorageManager` con `config.directorio_datos` tal como viene. Como el valor por defecto es relativo (`"data/monitor"`), al ejecutar la app desde otro directorio los datos podrían terminar fuera del proyecto. Conviene resolver la ruta contra el root de Sistema_v5.【F:Sistema_v5/web_app/app.py†L46-L134】【F:Sistema_v5/pjn/monitor/config.py†L60-L103】
   - En `dashboard()` se ordenan fechas con `datetime.fromisoformat`, pero los modelos aceptan fechas en distintos formatos (`YYYY-MM-DD` o `DD/MM/YYYY`). Si el monitor guarda fechas locales (`DD/MM/YYYY`), la web fallará al ordenarlas. Sería mejor normalizar o usar `dateutil.parser`.【F:Sistema_v5/web_app/app.py†L82-L133】【F:Sistema_v5/pjn/monitor/config.py†L52-L103】
   - `app.py` mantiene imports y constantes (`json`, `Thread`, `DATA_DIR`) sin uso, lo que dificulta el mantenimiento y puede confundir al lector.【F:Sistema_v5/web_app/app.py†L9-L188】

## Recomendaciones

- Ajustar las plantillas para que usen los nombres reales de los atributos (`numero`, `tipo_evento`, `evento`, `extraida_en`, `dependencia`, etc.) o enriquecer los modelos/serializadores para exponer los campos requeridos.
- Unificar los modos disponibles en UI y backend (por ejemplo, reemplazar las opciones por `automático`, `horario laboral`, `fuera de horario`) y validar entradas antes de persistirlas.
- Resolver la ruta del intérprete Python de forma dinámica (`sys.executable`, configuración o servicio supervisor) para soportar distintos entornos.
- Normalizar y validar los datos antes de ordenarlos/renderizarlos (fechas, textos largos) y limpiar imports/constantes obsoletas para reducir ruido.
- Documentar la estructura esperada de los archivos JSON en `data/monitor` para facilitar pruebas manuales y automatizadas.
