# 🎛️ Configurador del Sistema PJN

Este documento describe el sistema de configuración unificado del Sistema_v5.

## 📋 Índice

- [Descripción General](#descripción-general)
- [Inicio Rápido](#inicio-rápido)
- [Interfaz Gráfica](#interfaz-gráfica)
- [Uso Programático](#uso-programático)
- [Migración](#migración)
- [Opciones de Configuración](#opciones-de-configuración)
- [Ejemplos](#ejemplos)

---

## 🎯 Descripción General

El configurador proporciona una forma centralizada y unificada de gestionar **todas** las opciones del sistema, reemplazando la configuración dispersa anterior.

### ✨ Características

- ✅ **Interfaz gráfica completa** con pestañas organizadas
- ✅ **50+ opciones configurables** (directorios, monitoreo, extracción, sistema)
- ✅ **Validación automática** de todos los parámetros
- ✅ **Migración desde monitor.json** con backup automático
- ✅ **Exportar/Importar** configuraciones
- ✅ **Backups automáticos** con timestamp
- ✅ **Retrocompatible** con configuraciones anteriores

---

## 🚀 Inicio Rápido

### 1. Abrir el Configurador

```bash
# Abrir GUI con configuración por defecto
python scripts/configurar_sistema.py

# Usar un archivo específico
python scripts/configurar_sistema.py --config mi_config.json
```

### 2. Migrar desde monitor.json (si aplica)

```bash
python scripts/migrar_configuraciones.py
```

El script:
- ✅ Lee `config/monitor.json`
- ✅ Crea backup automático
- ✅ Migra a `config/sistema.json`
- ✅ Crea estructura de directorios

### 3. Uso Programático

```python
from pjn import SystemConfig

# Cargar configuración
config = SystemConfig.from_file("config/sistema.json")

# Acceder a opciones
print(config.directorio_expedientes_base)
print(config.modo_monitor)
print(config.nivel_log)
```

---

## 🖥️ Interfaz Gráfica

La GUI está organizada en **4 pestañas**:

### 📁 Pestaña Directorios

Configura dónde se guardan los archivos del sistema:

| Directorio | Descripción | Default |
|------------|-------------|---------|
| `directorio_extraccion_inicial` | Extracciones iniciales (fuente para comparaciones) | `data/inicial` |
| `directorio_extracciones_temporales` | Extracciones en progreso | `data/temp` |
| `directorio_expedientes_base` | Carpetas de expedientes individuales | `data/expedientes` |
| `directorio_comparaciones` | Resultados de comparaciones | `data/comparaciones` |
| `directorio_reportes` | Reportes generados | `data/reportes` |
| `directorio_logs` | Archivos de log | `logs` |
| `directorio_backups` | Backups de configuración | `backups` |
| `directorio_cache` | Cache de sesiones | `.cache` |
| `directorio_descargas` | PDFs descargados | `descargas` |
| `directorio_monitor_datos` | Datos del monitor | `data/monitor` |

**Cada campo incluye:**
- Campo de texto editable
- Botón 📂 para explorar directorios
- Tooltip descriptivo

### 🔍 Pestaña Monitoreo

Configura el comportamiento del monitor:

#### Modo de Operación
- **Automático**: Alterna entre intervalos laborales y no laborales
- **Laboral**: Siempre usa intervalos laborales
- **No Laboral**: Siempre usa intervalos no laborales

#### Intervalos de Verificación
- **Horario Laboral**:
  - Expedientes: 15 minutos (default)
  - Entradas: 10 minutos (default)
- **Horario No Laboral**:
  - Expedientes: 60 minutos (default)
  - Entradas: 30 minutos (default)

#### Horario Laboral
- **Hora inicio**: 08:00 (default)
- **Hora fin**: 18:00 (default)
- **Días laborales**: Lunes a Viernes (default)

#### Verificaciones
- ☑️ Verificar entradas
- ☑️ Verificar expedientes

#### Notificaciones
- ☑️ Notificar nuevas entradas
- ☑️ Notificar cambios en expedientes
- ☑️ Notificar errores

### ⚙️ Pestaña Extracción

Configura el scraping y extracción:

#### Browser
- ☑️ Modo headless (sin interfaz gráfica)

#### Límites
- **Máximo de páginas**: 200 (default)

#### Timeouts (milisegundos)
- **Por defecto**: 8,000 ms
- **Login**: 60,000 ms
- **Descarga**: 30,000 ms

#### Reintentos
- **Expedientes**: 3 reintentos (default)
- **Entradas**: 3 reintentos (default)
- **Descargas**: 3 reintentos (default)

### 🔧 Pestaña Sistema

Configura el sistema en general:

#### Logging
- **Nivel**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- ☑️ Rotación de logs
- **Tamaño máximo**: 50 MB (default)

#### Backups
- **Intervalo automático**: 7 días (default)
- **Retener históricos**: 90 días (default)

#### Sesión del Portal
- ☑️ Guardar sesión entre ejecuciones
- **Duración**: 24 horas (default)

#### Límites de Recursos
- **Memoria**: 2048 MB (0 = sin límite)
- **Archivos en cache**: 1000 (0 = sin límite)

#### Reportes
- ☐ Generar reportes automáticamente
- **Formato**: JSON, Excel, PDF

---

## 📝 Uso Programático

### Crear Configuración

```python
from pjn import SystemConfig

# Configuración por defecto
config = SystemConfig()

# Configuración personalizada
config = SystemConfig(
    # Directorios
    directorio_expedientes_base="mi_data/expedientes",
    directorio_logs="mi_logs",

    # Monitoreo
    modo_monitor="laboral",
    intervalos_laboral_expedientes=30,
    hora_inicio="09:00",
    hora_fin="17:00",
    dias_laborales=["lunes", "miércoles", "viernes"],

    # Extracción
    headless=True,
    max_paginas_expedientes=100,
    timeout_default=10_000,

    # Sistema
    nivel_log="DEBUG",
    max_tamaño_log_mb=100,
    intervalo_backup_automatico=14
)
```

### Guardar y Cargar

```python
# Guardar configuración
config.to_file("config/sistema.json")

# Cargar configuración
config = SystemConfig.from_file("config/sistema.json")

# Convertir a diccionario
config_dict = config.to_dict()
```

### Crear Directorios

```python
# Crear todos los directorios definidos
config.crear_directorios()

# Los directorios se crean automáticamente si no existen
```

### Hacer Backups

```python
# Backup con timestamp automático
backup_path = config.hacer_backup()
print(f"Backup creado en: {backup_path}")

# Backup en ubicación específica
backup_path = config.hacer_backup("backups/mi_backup.json")
```

---

## 🔄 Migración

### Desde monitor.json

Si tienes un archivo `config/monitor.json` existente:

```bash
python scripts/migrar_configuraciones.py
```

**El script hará:**

1. ✅ Leer `config/monitor.json`
2. ✅ Crear backup en `backups/monitor_YYYYMMDD_HHMMSS.json`
3. ✅ Convertir a `SystemConfig`
4. ✅ Crear todos los directorios
5. ✅ Guardar en `config/sistema.json`
6. ✅ Mostrar resumen detallado

**Programáticamente:**

```python
from pjn.system_config import SystemConfig

# Migrar desde monitor.json
config = SystemConfig.from_monitor_config("config/monitor.json")

# Guardar como sistema.json
config.to_file("config/sistema.json")
```

---

## 📚 Opciones de Configuración

### Todas las Opciones (53 total)

#### Directorios (10)
```python
directorio_extraccion_inicial: str = "data/inicial"
directorio_extracciones_temporales: str = "data/temp"
directorio_expedientes_base: str = "data/expedientes"
directorio_comparaciones: str = "data/comparaciones"
directorio_reportes: str = "data/reportes"
directorio_logs: str = "logs"
directorio_backups: str = "backups"
directorio_cache: str = ".cache"
directorio_descargas: str = "descargas"
directorio_monitor_datos: str = "data/monitor"
```

#### Monitoreo (14)
```python
modo_monitor: ModoMonitor = "automatico"  # "automatico" | "laboral" | "no_laboral"
intervalos_laboral_expedientes: int = 15
intervalos_laboral_entradas: int = 10
intervalos_no_laboral_expedientes: int = 60
intervalos_no_laboral_entradas: int = 30
dias_laborales: list[str] = ["lunes", "martes", "miercoles", "jueves", "viernes"]
hora_inicio: str = "08:00"
hora_fin: str = "18:00"
verificar_entradas: bool = True
verificar_expedientes: bool = True
notificar_nuevas_entradas: bool = True
notificar_cambios_expedientes: bool = True
notificar_errores: bool = True
fecha_desde_entradas: str | None = None
fecha_hasta_entradas: str | None = None
fecha_desde_expedientes: str | None = None
fecha_hasta_expedientes: str | None = None
fecha_corte_expedientes: str | None = None
```

#### Extracción (9)
```python
headless: bool = True
max_paginas_expedientes: int = 200
timeout_default: int = 8_000
timeout_login: int = 60_000
timeout_descarga: int = 30_000
max_reintentos_expedientes: int = 3
espera_reintentos_expedientes: int = 30
max_reintentos_entradas: int = 3
espera_reintentos_entradas: int = 30
max_reintentos_descarga: int = 3
```

#### Sistema (14)
```python
fecha_inicio_sistema: str | None = None  # Auto-generada
fecha_ultimo_backup: str | None = None  # Auto-actualizada
intervalo_backup_automatico: int = 7
retener_historico_dias: int = 90
nivel_log: NivelLog = "INFO"  # "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL"
max_tamaño_log_mb: int = 50
rotacion_logs: bool = True
guardar_sesion: bool = True
duracion_sesion_horas: int = 24
limite_memoria_mb: int = 2048
max_archivos_cache: int = 1000
modo_comparacion: ModoComparacion = "manual"  # "automatico" | "manual" | "deshabilitado"
comparacion_automatica: bool = False  # Legacy
generar_reportes_automaticos: bool = False
formato_reportes: FormatoReporte = "json"  # "json" | "excel" | "pdf"
```

---

## 💡 Ejemplos

### Ejemplo 1: Configuración de Desarrollo

```python
from pjn import SystemConfig

config = SystemConfig(
    # Directorios locales
    directorio_expedientes_base="dev_data/expedientes",
    directorio_logs="dev_logs",

    # Monitor más frecuente
    intervalos_laboral_expedientes=5,
    intervalos_laboral_entradas=3,

    # Browser visible para debugging
    headless=False,

    # Logging detallado
    nivel_log="DEBUG",

    # Límites bajos para testing
    max_paginas_expedientes=10
)

config.to_file("config/desarrollo.json")
```

### Ejemplo 2: Configuración de Producción

```python
from pjn import SystemConfig

config = SystemConfig(
    # Directorios de producción
    directorio_expedientes_base="/var/data/pjn/expedientes",
    directorio_logs="/var/log/pjn",
    directorio_backups="/var/backups/pjn",

    # Monitor conservador
    intervalos_laboral_expedientes=30,
    intervalos_no_laboral_expedientes=120,

    # Browser headless
    headless=True,

    # Logging normal
    nivel_log="INFO",

    # Backups frecuentes
    intervalo_backup_automatico=1,  # Diario

    # Límites de recursos
    limite_memoria_mb=4096,
    max_archivos_cache=5000
)

config.to_file("config/produccion.json")
```

### Ejemplo 3: Solo Monitoreo de Entradas

```python
from pjn import SystemConfig

config = SystemConfig(
    # Deshabilitar expedientes
    verificar_expedientes=False,
    notificar_cambios_expedientes=False,

    # Solo entradas
    verificar_entradas=True,
    notificar_nuevas_entradas=True,

    # Intervalos cortos
    intervalos_laboral_entradas=5,
    intervalos_no_laboral_entradas=15
)

config.to_file("config/solo_entradas.json")
```

### Ejemplo 4: Configuración con Filtros de Fecha

```python
from pjn import SystemConfig

config = SystemConfig(
    # Filtrar solo entradas recientes
    fecha_desde_entradas="2025-01-01",
    fecha_hasta_entradas="2025-12-31",

    # Filtrar expedientes por rango
    fecha_desde_expedientes="2024-01-01",
    fecha_hasta_expedientes=None  # Hasta hoy
)

config.to_file("config/con_filtros.json")
```

---

## 🧪 Testing

### Ejecutar Tests Unitarios

```bash
# Todos los tests de configuración
python -m pytest tests/test_system_config.py -v

# Test específico
python -m pytest tests/test_system_config.py::TestSystemConfigDefaults -v
```

### Crear Configuración de Test

```python
from pjn import SystemConfig

config = SystemConfig(
    directorio_expedientes_base="test_data",
    modo_monitor="no_laboral",
    intervalos_no_laboral_expedientes=5,
    headless=True,
    nivel_log="DEBUG",
    max_paginas_expedientes=5
)
```

---

## 🔧 Troubleshooting

### Error: "directorio_datos no puede estar vacío"

**Causa**: Intentaste crear una configuración con un directorio vacío.

**Solución**:
```python
config = SystemConfig(directorio_monitor_datos="data/monitor")
```

### Error: "hora_inicio debe ser anterior a hora_fin"

**Causa**: El horario laboral está invertido.

**Solución**:
```python
config = SystemConfig(
    hora_inicio="08:00",
    hora_fin="18:00"  # Debe ser posterior a hora_inicio
)
```

### Error: "dias_laborales contiene días inválidos"

**Causa**: Días en inglés o mal escritos.

**Solución**:
```python
config = SystemConfig(
    dias_laborales=["lunes", "martes", "miércoles"]  # En español
)
```

### GUI no se abre

**Causa**: tkinter no está disponible.

**Solución**:
```bash
# En macOS
brew install python-tk

# En Ubuntu/Debian
sudo apt-get install python3-tk

# Verificar
python -c "import tkinter; print('OK')"
```

---

## 📞 Soporte

- **Documentación completa**: Ver `docs/README_DOCUMENTACION.md`
- **Ejemplos**: Ver `docs/DOCUMENTACION_GUIAS.md`
- **API Reference**: Ver `docs/DOCUMENTACION_COMPLETA.md`

---

## 🎉 Resumen

El configurador proporciona:

✅ **50+ opciones** organizadas en 4 categorías
✅ **Interfaz gráfica** simple y completa
✅ **Validación automática** de todos los parámetros
✅ **Migración automática** desde configuraciones antiguas
✅ **Backups automáticos** con timestamp
✅ **Uso programático** completo desde Python

**¡Listo para usar!** 🚀
