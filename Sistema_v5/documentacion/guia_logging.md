# Guía del Sistema de Logging - Sistema_v5

## Descripción General

Sistema_v5 implementa un sistema de logging centralizado que reemplaza el uso de `print()` con un sistema profesional basado en el módulo `logging` de Python. Esto permite:

- **Control de verbosidad**: Mostrar solo los mensajes relevantes según el nivel configurado
- **Logs en archivo**: Guardar automáticamente todos los logs para depuración
- **Colores en consola**: Mejor legibilidad con códigos de color ANSI
- **Compatibilidad con emojis**: Mantiene el estilo visual existente

## Uso Básico

### Importar el logger en un módulo

```python
from Sistema_v5.pjn.utils.logging import get_logger

logger = get_logger(__name__)
```

### Niveles de logging disponibles

```python
# DEBUG: Información detallada para depuración
logger.debug("🔍 Variable x = %s", x)

# INFO: Mensajes informativos del flujo normal
logger.info("✅ Archivo descargado: %s", nombre_archivo)

# WARNING: Advertencias que no detienen la ejecución
logger.warning("⚠️ Timeout detectado, reintentando...")

# ERROR: Errores que afectan la operación pero no detienen el programa
logger.error("❌ No se pudo descargar el archivo: %s", error)

# CRITICAL: Errores críticos que requieren atención inmediata
logger.critical("💥 Sistema en estado crítico")
```

## Configuración

### Mediante Variables de Entorno

```bash
# Nivel de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export LOG_LEVEL=DEBUG

# Guardar logs en archivo
export LOG_FILE=logs/sistema_v5.log

# Desactivar colores en consola
export LOG_COLORS=false
```

### Mediante Código

```python
from Sistema_v5.pjn.utils.logging import setup_logging

# Solo INFO y superiores en consola
setup_logging(level="INFO")

# DEBUG en consola y archivo
setup_logging(level="DEBUG", log_file="debug.log")

# Solo errores en consola, todo en archivo
setup_logging(
    level="ERROR",           # Consola: solo errores
    log_file="app.log",
    file_level="DEBUG"       # Archivo: todo
)
```

## Ejemplos de Uso

### Migración desde print()

**Antes:**
```python
print(f"📄 Página {pagina}: extrayendo...")
print(f"✅ Descargados: {total}")
```

**Después:**
```python
logger.info("📄 Página %d: extrayendo...", pagina)
logger.info("✅ Descargados: %d", total)
```

### Logging con contexto

```python
# Información de depuración
logger.debug("🔍 Procesando actuación #%d", indice)
logger.debug("🔍 Hash calculado: %s", hash_value)

# Flujo normal
logger.info("📥 Descargando %d archivos...", total_archivos)

# Advertencias
logger.warning("⚠️ Timeout en actuación %d, reintentando (%d/3)...", idx, intento)

# Errores
logger.error("❌ Error de I/O al guardar archivo %s: %s", nombre, error)
```

### Manejo de excepciones

```python
try:
    resultado = operacion_riesgosa()
except Exception as e:
    logger.error("❌ Error durante la operación: %s", e)
    logger.debug("Detalles completos:", exc_info=True)  # Incluye stack trace
```

## Niveles Recomendados por Entorno

### Desarrollo
```bash
export LOG_LEVEL=DEBUG
export LOG_FILE=logs/dev.log
```
Muestra toda la información para depuración.

### Producción
```bash
export LOG_LEVEL=INFO
export LOG_FILE=logs/prod.log
```
Muestra solo información relevante del flujo normal.

### Testing/CI
```bash
export LOG_LEVEL=WARNING
export LOG_FILE=logs/test.log
```
Solo advertencias y errores para mantener output limpio.

## Formato de Salida

### Consola
```
INFO - ✅ Archivo descargado: documento.pdf
WARNING - ⚠️ Timeout detectado, reintentando...
ERROR - ❌ No se pudo descargar el archivo
```

### Archivo
```
2025-01-15 10:30:45 - Sistema_v5.pjn.scraping.actuaciones - INFO - ✅ Archivo descargado: documento.pdf
2025-01-15 10:30:46 - Sistema_v5.pjn.scraping.actuaciones - WARNING - ⚠️ Timeout detectado, reintentando...
2025-01-15 10:30:47 - Sistema_v5.pjn.scraping.actuaciones - ERROR - ❌ No se pudo descargar el archivo
```

## Buenas Prácticas

### 1. Usar parámetros en lugar de f-strings

**Incorrecto:**
```python
logger.info(f"Procesando expediente {numero}")
```

**Correcto:**
```python
logger.info("Procesando expediente %s", numero)
```

**Razón:** El formatting lazy solo se ejecuta si el nivel de log está activo, mejorando performance.

### 2. Elegir el nivel apropiado

- `DEBUG`: Información interna, valores de variables, pasos detallados
- `INFO`: Progreso normal, operaciones completadas exitosamente
- `WARNING`: Situaciones anómalas que no impiden continuar (timeouts con retry, archivos faltantes no críticos)
- `ERROR`: Errores que afectan la operación actual pero no detienen el programa
- `CRITICAL`: Errores que requieren atención inmediata o detienen el sistema

### 3. Mantener emojis para legibilidad

Los emojis son útiles para identificar rápidamente el tipo de mensaje:
- 🔍 DEBUG
- ℹ️ / ✅ / 📄 INFO
- ⚠️ / ⏳ WARNING
- ❌ ERROR
- 💥 CRITICAL

### 4. Incluir contexto relevante

```python
# Bien: incluye contexto suficiente
logger.error("❌ Error al descargar archivo %s del expediente %s: %s",
             nombre_archivo, expediente_numero, error)

# Insuficiente: falta contexto
logger.error("❌ Error al descargar")
```

## Testing del Sistema de Logging

Ejecutar el script de demostración:

```bash
# Modo normal (INFO)
python Sistema_v5/test_logging_demo.py

# Ver todo el debug
LOG_LEVEL=DEBUG python Sistema_v5/test_logging_demo.py

# Solo errores
LOG_LEVEL=ERROR python Sistema_v5/test_logging_demo.py

# Guardar en archivo
LOG_FILE=logs/demo.log python Sistema_v5/test_logging_demo.py
```

## Módulos con Logging Implementado

- ✅ `Sistema_v5/pjn/scraping/actuaciones.py`
- ✅ `Sistema_v5/pjn/scraping/entradas.py`
- ✅ `Sistema_v5/pjn/scraping/expedientes.py`
- ✅ `Sistema_v5/pjn/scripts/rf_test_extraccion_completa.py`

## Solución de Problemas

### Los logs no aparecen en consola

Verificar que el nivel configurado sea suficientemente bajo:
```python
setup_logging(level="DEBUG")
```

### Los colores no se muestran

- Asegurarse de que `LOG_COLORS` no esté en `false`
- Verificar que la terminal soporte códigos ANSI
- En Windows, usar Windows Terminal o activar soporte ANSI

### Los logs en archivo están vacíos

Verificar permisos de escritura y que el directorio exista:
```python
setup_logging(log_file="logs/app.log")  # Crea 'logs/' automáticamente
```

## Referencias

- Documentación oficial de logging: https://docs.python.org/3/library/logging.html
- Módulo de logging: `Sistema_v5/pjn/utils/logging.py`
- Script de demostración: `Sistema_v5/test_logging_demo.py`
