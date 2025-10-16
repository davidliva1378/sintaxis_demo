# Monitor PJN v5 - Guia Rapida

Guia de inicio rapido para poner el monitor en funcionamiento en 5 minutos.

## Instalacion Rapida

### 1. Instalar dependencias

```bash
# Activar entorno virtual
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# Instalar dependencias
pip install playwright plyer apscheduler

# Instalar navegadores
playwright install chromium
```

### 2. Configurar credenciales

Crear archivo `.env` en la raiz del proyecto:

```env
PJN_USER=tu_usuario_pjn
PJN_PASS=tu_password_pjn
```

### 3. Configurar monitor

Editar `config/monitor.json` (o usar la configuracion por defecto):

```json
{
  "modo": "automatico",
  "headless": true,
  "verificar_entradas": true,
  "verificar_expedientes": false,
  "fecha_desde_entradas": "15/10/2025",
  "fecha_hasta_entradas": "16/10/2025"
}
```

### 4. Probar

```bash
# Primera ejecucion (con ventana visible para ver que pasa)
python scripts/monitor_cli.py --verificar-ahora --no-headless --verbose

# Si funciono, ejecutar en modo headless
python scripts/monitor_cli.py --verificar-ahora
```

## Uso Basico

### Verificacion unica

```bash
# Verificacion inmediata
python scripts/monitor_cli.py --verificar-ahora

# Con logs detallados
python scripts/monitor_cli.py --verificar-ahora --verbose
```

### Modo continuo (Scheduler)

```bash
# Ejecutar monitor continuamente
python scripts/monitor_cli.py

# El monitor verificara automaticamente segun los intervalos configurados
```

### Configuraciones recomendadas

#### Solo entradas (mas rapido, mas estable)

```json
{
  "verificar_entradas": true,
  "verificar_expedientes": false
}
```

#### Con filtro de fechas (recomendado)

```json
{
  "fecha_desde_entradas": "15/10/2025",
  "fecha_hasta_entradas": "16/10/2025"
}
```

## Verificar que funciona

Despues de ejecutar `--verificar-ahora`, deberas ver:

```
============================================================
VERIFICACION INMEDIATA
============================================================

📥 Verificando entradas...
✅ 8 nuevas entradas detectadas:
  - FPA 4471/2020: Notificacion
  - FPA 8018/2017/CA2: Notificacion
  ... y 6 mas

📊 Verificacion de expedientes deshabilitada

============================================================
VERIFICACION COMPLETADA EXITOSAMENTE
============================================================
```

Si ves esto, el monitor esta funcionando correctamente.

## Solucionar Problemas

### Error: "ExtraccionError: Contenedor o filas no visibles"

**Solucion:** Credenciales incorrectas o sesion expirada.

```bash
# Eliminar sesion guardada
rm pjn/scraping/pjn_storage_state.json

# Verificar .env
cat .env  # Linux/macOS
type .env  # Windows
```

### Error: "No module named 'playwright'"

**Solucion:** Instalar dependencias.

```bash
pip install playwright
playwright install chromium
```

### No aparecen notificaciones desktop

**Solucion:** Verificar plyer y permisos.

```bash
pip install plyer

# En Windows: Configuracion > Sistema > Notificaciones
# Verificar que estan habilitadas
```

## Siguiente Paso

Ver documentacion completa en:
- `docs/MONITOR.md` - Documentacion completa
- `docs/MONITOR_EJEMPLOS.md` - Ejemplos practicos

## Comandos Utiles

```bash
# Ver ayuda
python scripts/monitor_cli.py --help

# Limpiar historial
rm -rf data/monitor/

# Limpiar sesion
rm pjn/scraping/pjn_storage_state.json

# Ver logs en tiempo real (Linux/macOS)
tail -f monitor.log

# Ejecutar en segundo plano (Linux/macOS)
nohup python scripts/monitor_cli.py > monitor.log 2>&1 &

# Ver procesos ejecutandose
ps aux | grep monitor_cli
```

## Configuracion Minima para Produccion

```json
{
  "modo": "automatico",
  "headless": true,
  "verificar_entradas": true,
  "verificar_expedientes": false,
  "intervalos_laboral_entradas": 15,
  "intervalos_no_laboral_entradas": 60,
  "notificar_nuevas_entradas": true,
  "notificar_errores": true,
  "fecha_desde_entradas": null,
  "fecha_hasta_entradas": null
}
```

Ejecutar:

```bash
# Modo continuo en segundo plano
python scripts/monitor_cli.py &
```

Listo! El monitor estara verificando automaticamente segun los intervalos configurados.
