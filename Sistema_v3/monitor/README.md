# Monitor de Expedientes y Entradas

Este módulo provee un monitor ligero basado en bandeja del sistema que
verifica periódicamente nuevas entradas del PJN y actualizaciones de
expedientes.

## Configuración

1. Asegurarse de contar con un archivo de sesión válido (`estado_sesion.json`).
2. Opcionalmente ajustar los intervalos en `config/config_monitor.json`.
3. Los resultados se guardan en `datos_extraidos/monitoreo` y los registros
en `impresion_logs/log_monitoreo.txt`.

## Ejecución

```bash
python -m Sistema_v3.monitor.monitor_entradas_expedientes
```

Al iniciarse, el monitor coloca un icono en la bandeja del sistema con
acciones para verificar expedientes, verificar entradas, consultar el
estado de la sesión y salir de la aplicación.
