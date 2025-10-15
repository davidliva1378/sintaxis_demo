# Sistema de Logging - Sistema_v5

## Resumen

Sistema_v5 implementa un sistema de logging flexible y configurable que reemplaza los `print()` statements, manteniendo el mismo estilo visual con emojis pero agregando capacidades profesionales de logging.

---

## ✨ Características

- ✅ **Mantiene estilo visual actual:** Emojis y formato idéntico a `print()`
- ✅ **Control de verbosidad:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- ✅ **Colores en consola:** Diferenciación visual automática por nivel
- ✅ **Logs a archivo opcional:** Guarda todo en archivo mientras muestra en consola
- ✅ **Configuración por variables de entorno:** Sin cambiar código
- ✅ **Timestamps automáticos:** En archivos de log
- ✅ **Filtrado por módulo:** Controla qué módulos son verbosos

---

## 🚀 Uso Rápido

### Migración desde `print()`

```python
# ANTES (con print)
print(f"📄 Página {pagina}: extrayendo...")
print(f"✅ Archivo descargado: {nombre}")
print(f"❌ Error: {e}")

# DESPUÉS (con logging)
from Sistema_v5.pjn.utils.logging import get_logger

logger = get_logger(__name__)

logger.info("📄 Página %d: extrayendo...", pagina)
logger.info("✅ Archivo descargado: %s", nombre)
logger.error("❌ Error: %s", e)
```

**Resultado en consola:** ¡Exactamente igual! Solo que ahora tienes control total.

---

## 📊 Niveles de Logging

| Nivel | Cuándo Usar | Ejemplo |
|-------|-------------|---------|
| `DEBUG` | Detalles técnicos para desarrollo | `logger.debug("🔍 Variable x = %s", x)` |
| `INFO` | Flujo normal del programa | `logger.info("📄 Página 1: extrayendo...")` |
| `WARNING` | Advertencias recuperables | `logger.warning("⚠️ Timeout, reintentando...")` |
| `ERROR` | Errores que afectan funcionalidad | `logger.error("❌ Error descargando: %s", e)` |
| `CRITICAL` | Errores fatales | `logger.critical("💥 Sistema inestable")` |

---

## 🎛️ Configuración por Ambiente

### Modo Desarrollo (ver todo)

```bash
export LOG_LEVEL=DEBUG
python script.py
```

**Output:**
```
DEBUG - 🔍 fecha_limpia: "12/09/2025"
DEBUG - 🔍 Hash: abc123
INFO - 📄 Página 1: extrayendo...
INFO - ✅ Archivo descargado
```

### Modo Producción (solo información importante)

```bash
export LOG_LEVEL=INFO
python script.py
```

**Output:**
```
INFO - 📄 Página 1: extrayendo...
INFO - ✅ Archivo descargado
```
(Los `DEBUG` no se muestran)

### Modo Usuario (solo errores)

```bash
export LOG_LEVEL=ERROR
python script.py
```

**Output:**
```
ERROR - ❌ Error descargando archivo
```

### Guardar Logs en Archivo

```bash
export LOG_FILE=logs/sistema_v5.log
python script.py
```

- **Consola:** Solo INFO y superiores
- **Archivo:** TODO incluso DEBUG, con timestamps

**Contenido del archivo:**
```
2025-10-14 23:30:15 - Sistema_v5.pjn.scraping.actuaciones - DEBUG - fecha_limpia: "12/09/2025"
2025-10-14 23:30:16 - Sistema_v5.pjn.scraping.actuaciones - INFO - 📄 Página 1: extrayendo...
2025-10-14 23:30:18 - Sistema_v5.pjn.scraping.actuaciones - INFO - ✅ Archivo descargado
```

---

## 💻 Ejemplos de Código

### Setup Básico en un Módulo

```python
# En cualquier archivo .py
from Sistema_v5.pjn.utils.logging import get_logger

logger = get_logger(__name__)

def mi_funcion():
    logger.info("📄 Iniciando proceso...")
    logger.debug("🔍 Valor de x: %s", x)
    logger.info("✅ Proceso completado")
```

### Setup en un Script Ejecutable

```python
#!/usr/bin/env python3
from Sistema_v5.pjn.utils.logging import get_logger, setup_logging

# Configuración manual (opcional)
setup_logging(
    level="DEBUG",
    log_file="logs/mi_script.log",
    use_colors=True
)

logger = get_logger(__name__)

def main():
    logger.info("🚀 Script iniciado")
    # ... tu código ...
    logger.info("✅ Script completado")

if __name__ == "__main__":
    main()
```

### Logging con Manejo de Excepciones

```python
try:
    resultado = operacion_riesgosa()
    logger.info("✅ Operación exitosa: %s", resultado)
except TimeoutError as e:
    logger.error("❌ Timeout: %s", e)
except Exception as e:
    logger.critical("💥 Error inesperado: %s", e, exc_info=True)
    # exc_info=True incluye el stack trace en el log
```

---

## 🎨 Manteniendo el Estilo Visual

### Emojis Recomendados

```python
# Progreso y éxito
logger.info("📄 Procesando página...")
logger.info("✅ Completado")
logger.info("📁 Archivos guardados en: %s", path)
logger.info("📥 Descargando %d archivos...", count)

# Información
logger.info("ℹ️ No se detectaron cambios")
logger.info("⏭️ Archivo ya existe: %s", nombre)

# Advertencias
logger.warning("⚠️ Timeout, reintentando...")
logger.warning("🟡 Ya existe: %s", archivo)

# Errores
logger.error("❌ Error: %s", e)
logger.error("🚫 Sin archivo para descargar")

# Debug
logger.debug("🔍 Variable x = %s", x)
logger.debug("⏳ Esperando respuesta...")
```

---

## 🔧 Configuración Avanzada

### Variables de Entorno Disponibles

| Variable | Valores | Default | Descripción |
|----------|---------|---------|-------------|
| `LOG_LEVEL` | DEBUG, INFO, WARNING, ERROR, CRITICAL | INFO | Nivel de logging en consola |
| `LOG_FILE` | Ruta de archivo | None | Dónde guardar logs |
| `LOG_COLORS` | true, false, 1, 0 | true | Si usar colores en consola |

### Configuración Programática

```python
from Sistema_v5.pjn.utils.logging import setup_logging

# Configuración personalizada
setup_logging(
    level="DEBUG",              # Nivel para consola
    log_file="logs/debug.log",  # Archivo donde guardar
    use_colors=True,            # Colores en consola
    file_level="DEBUG"          # Nivel para archivo (independiente)
)
```

### Silenciar Módulos Ruidosos

```python
import logging

# Silenciar playwright
logging.getLogger('playwright').setLevel(logging.WARNING)

# Solo errores de urllib3
logging.getLogger('urllib3').setLevel(logging.ERROR)
```

---

## 📝 Mejores Prácticas

### 1. Usa Parámetros, No f-strings

```python
# ❌ EVITAR (menos eficiente)
logger.info(f"📄 Página {pagina}: extrayendo...")

# ✅ PREFERIR (más eficiente)
logger.info("📄 Página %d: extrayendo...", pagina)
```

**Por qué:** El f-string se evalúa siempre, incluso si el log no se mostrará. Los parámetros solo se evalúan si el nivel está activo.

### 2. Usa el Nivel Correcto

```python
# Detalles de desarrollo
logger.debug("🔍 Hash calculado: %s", hash_val)

# Flujo normal del programa
logger.info("📄 Página 1: extrayendo...")

# Problemas recuperables
logger.warning("⚠️ Timeout, reintentando...")

# Errores que afectan funcionalidad
logger.error("❌ Error descargando: %s", e)

# Errores críticos/fatales
logger.critical("💥 Sistema en estado crítico")
```

### 3. Include Context en Errores

```python
try:
    descargar_archivo(url)
except Exception as e:
    logger.error(
        "❌ Error descargando archivo %s: %s",
        nombre_archivo,
        e,
        exc_info=True  # Incluye stack trace
    )
```

### 4. Usa `__name__` para el Logger

```python
# ✅ CORRECTO
logger = get_logger(__name__)

# ❌ EVITAR
logger = get_logger("mi_logger")
```

**Por qué:** `__name__` incluye automáticamente el módulo completo, permitiendo filtrado granular.

---

## 🧪 Testing

### Ejecutar Demo

```bash
# Demo básico
python Sistema_v5/test_logging_demo.py

# Con DEBUG
LOG_LEVEL=DEBUG python Sistema_v5/test_logging_demo.py

# Guardar en archivo
LOG_FILE=logs/demo.log python Sistema_v5/test_logging_demo.py

# Sin colores
LOG_COLORS=false python Sistema_v5/test_logging_demo.py
```

---

## 📊 Comparación: Antes vs Después

### Ejemplo Real de actuaciones.py

**Antes:**
```python
print(f"📥 Iniciando descarga de archivos ({len(actuaciones)} actuaciones)...")

for idx, act in enumerate(actuaciones, start=1):
    if os.path.exists(ruta_archivo):
        print(f"⏭️ Archivo ya existe: {nombre_archivo}")
        continue

    try:
        print(f"✅ Archivo descargado: {nombre_archivo}")
    except Exception as e:
        print(f"❌ Error: {e}")
```

**Después:**
```python
logger.info("📥 Iniciando descarga de archivos (%d actuaciones)...", len(actuaciones))

for idx, act in enumerate(actuaciones, start=1):
    if os.path.exists(ruta_archivo):
        logger.info("⏭️ Archivo ya existe: %s", nombre_archivo)
        continue

    try:
        logger.info("✅ Archivo descargado: %s", nombre_archivo)
    except Exception as e:
        logger.error("❌ Error: %s", e)
```

**Resultado:** Mismo output visual, pero ahora puedes:
- Desactivar logs de archivos existentes con `LOG_LEVEL=WARNING`
- Ver detalles técnicos con `LOG_LEVEL=DEBUG`
- Guardar todo en archivo con `LOG_FILE=logs/descargas.log`

---

## 🎯 Migración Gradual

No es necesario cambiar todo de una vez. Puedes migrar gradualmente:

### Fase 1: Imports

```python
from Sistema_v5.pjn.utils.logging import get_logger

logger = get_logger(__name__)
```

### Fase 2: Funciones Críticas

Empieza con las funciones más importantes:
- Funciones de extracción
- Funciones de descarga
- Manejo de errores

### Fase 3: Resto del Código

Migra el resto gradualmente según necesidad.

---

## 📚 Recursos

- **Script de demo:** `Sistema_v5/test_logging_demo.py`
- **Documentación oficial Python:** https://docs.python.org/3/library/logging.html
- **Módulo de logging:** `Sistema_v5/pjn/utils/logging.py`

---

## 🐛 Troubleshooting

### Los logs no se muestran

```python
# Verifica el nivel
import logging
print(logging.getLogger().level)

# Fuerza INFO
from Sistema_v5.pjn.utils.logging import setup_logging
setup_logging("INFO")
```

### Los colores no funcionan

```bash
# Desactiva colores si hay problemas
export LOG_COLORS=false
```

### Quiero el comportamiento anterior temporalmente

```bash
# Nivel ERROR solo muestra errores (similar a modo silencioso)
LOG_LEVEL=ERROR python script.py
```

---

**Última actualización:** Octubre 2025
**Mantenido por:** Equipo sintaXis
