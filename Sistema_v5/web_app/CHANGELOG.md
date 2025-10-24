# Changelog - Aplicación Web Monitor PJN

## 2025-10-19 - Simplificación y Optimización

### ✅ Correcciones
- **Corregido**: Error de importación `MonitorError` en `app.py`
  - Archivo: `Sistema_v5/pjn/monitor/exceptions.py`
  - Agregado `MonitorError` a los exports del wrapper

### 🎯 Optimizaciones

#### Eliminación de Archivos Redundantes
- ❌ **Eliminado**: `run_app.sh` - No funciona en Windows
- ❌ **Eliminado**: `INICIO_RAPIDO.md` - Documentación redundante
- ❌ **Eliminado**: `EJECUTAR_WEB_APP.txt` - Guía redundante

**Razón**: Mantener un solo archivo multiplataforma (`run_app.py`) reduce complejidad y mejora mantenibilidad.

#### Mejoras en `run_app.py`
- ✅ **Mejorado**: Documentación extensa en el docstring
- ✅ **Agregado**: Manejo de errores robusto
- ✅ **Agregado**: Mensajes informativos al iniciar
- ✅ **Agregado**: Validación de puertos
- ✅ **Agregado**: Detección de plataforma
- ✅ **Agregado**: Sugerencias de solución de errores

#### Mejoras en `app.py`
- ✅ **Agregado**: Soporte para variables de entorno (`FLASK_PORT`, `FLASK_HOST`, `FLASK_DEBUG`)
- ✅ **Configurado**: Puerto 8080 por defecto (evita conflicto con AirPlay Receiver en macOS)

#### Documentación Consolidada
- ✅ **Actualizado**: `README.md` con toda la información consolidada
  - Inicio rápido
  - Configuración
  - Rutas disponibles
  - Solución de problemas
  - Compatibilidad multiplataforma (Windows, macOS, Linux)
  - Preguntas frecuentes

### 📊 Estado Actual

**Archivos Activos**:
```
web_app/
├── app.py              # Aplicación Flask completa (NECESARIO)
├── run_app.py          # Script de inicio (RECOMENDADO)
├── README.md           # Documentación completa
└── CHANGELOG.md        # Este archivo
```

**Ejecución Recomendada**:
```bash
# Todas las plataformas
python3 Sistema_v5/web_app/run_app.py
```

### 🎯 Beneficios
1. **Menos archivos** = Menos confusión
2. **Un solo método de ejecución** = Más simple
3. **Multiplataforma** = Funciona igual en Windows, macOS y Linux
4. **Mejor documentado** = Todo en un solo README
5. **Más mantenible** = Menos duplicación de código

## 2025-10-19 - Integración con Monitor Universal

### 🔧 Corrección Importante

**Problema**: Al iniciar el monitor desde la aplicación web, no aparecía el icono en la bandeja del sistema.

**Causa**: La aplicación web ejecutaba `ejecutar_monitor_continuo.py` en lugar de `ejecutar_monitor_universal.py`.

**Solución**: Actualizado `app.py` línea 66:
```python
# Antes
MONITOR_SCRIPT = _resolve_path_from_env("MONITOR_SCRIPT_PATH", BASE_DIR / "ejecutar_monitor_continuo.py")

# Ahora
MONITOR_SCRIPT = _resolve_path_from_env("MONITOR_SCRIPT_PATH", BASE_DIR / "ejecutar_monitor_universal.py")
```

### ✅ Beneficios

Ahora cuando inicias el monitor desde la app web:
- ✅ **macOS**: Aparece icono en la barra de menú superior (usando `rumps`)
- ✅ **Windows**: Aparece icono en la bandeja del sistema (usando `pystray`)
- ✅ **Linux**: Aparece icono en la bandeja del sistema (usando `pystray`)

### 📋 Scripts de Monitor Disponibles

| Script | Propósito | Interfaz Gráfica |
|--------|-----------|------------------|
| `ejecutar_monitor_universal.py` | **Recomendado** - Detector automático de SO | ✅ Sí (tray/statusbar) |
| `ejecutar_monitor_statusbar.py` | Solo macOS (rumps) | ✅ Sí (statusbar) |
| `ejecutar_monitor_tray.py` | Windows/Linux (pystray) | ✅ Sí (tray) |
| `ejecutar_monitor_continuo.py` | Sin interfaz gráfica | ❌ No (solo consola) |
| `ejecutar_monitor_sistema.py` | Versión con sistema de bandeja genérico | ✅ Sí |

**La aplicación web ahora usa**: `ejecutar_monitor_universal.py` 🎉

### 🔄 Variable de Entorno (Opcional)

Si necesitas cambiar el script que ejecuta la app web:

```bash
export MONITOR_SCRIPT_PATH=/ruta/a/otro_script.py
python3 Sistema_v5/web_app/run_app.py
```

