# Monitor de Expedientes

Este módulo provee un monitor ligero basado en bandeja del sistema que
verifica periódicamente actualizaciones del listado de expedientes del PJN.
Las utilidades adicionales (entradas, comparaciones, respaldos, etc.) se
reincorporarán en iteraciones futuras.

## Configuración

1. Asegurarse de contar con un archivo de sesión válido (`estado_sesion.json`).
2. Opcionalmente ajustar los intervalos en `config/config_monitor.json`.
3. Los resultados se guardan en `datos_extraidos/monitoreo` y los registros
en `impresion_logs/log_monitoreo.txt`.

## Ejecución

```bash
python -m Sistema_v3.monitor.monitor_entradas_expedientes_v4
```

Al iniciarse, el monitor coloca un icono en la bandeja del sistema con
acciones para verificar expedientes y salir de la aplicación. Las opciones
adicionales de versiones anteriores se mostrarán como recordatorio de que
volverán a estar disponibles más adelante.
