# Análisis de Configuración - Sistema_v5.1.1

**Rama analizada:** `producción_v5.1.1`
**Fecha de análisis:** 2025-11-06
**Propósito:** Replicar configuración en rama `claude/v6-testing-011CUquXfHQF1jAeAMXMPexk` del proyecto Sistema_v6

---

## Tabla de Contenidos

1. [Estructura del Proyecto](#estructura-del-proyecto)
2. [Dependencias Python](#dependencias-python)
3. [Archivos de Configuración](#archivos-de-configuración)
4. [Variables de Entorno](#variables-de-entorno)
5. [Scripts de Ejecución](#scripts-de-ejecución)
6. [Sistema de Configuración](#sistema-de-configuración)
7. [Recomendaciones para Replicación](#recomendaciones-para-replicación)

---

## 1. Estructura del Proyecto

### Directorio raíz
```
sintaXis/
├── Sistema_v5/              # Directorio principal del proyecto
├── tests/                   # Tests del proyecto
├── .gitignore
└── Documentación (.md)
```

### Estructura de Sistema_v5
```
Sistema_v5/
├── backup_manager/          # Gestión de backups
├── bin/                     # Scripts ejecutables
├── config/                  # Archivos de configuración JSON
├── configuracion/           # Módulo de configuración (Python)
│   ├── core/               # Configuraciones principales
│   ├── cli/                # CLI para configuración
│   ├── monitor/            # Config específica del monitor
│   ├── estados/            # Gestión de estados
│   └── utils/              # Utilidades de configuración
├── docs/                    # Documentación
├── extractor_inicial/       # Módulo de extracción inicial
├── gestor_directorios/      # Gestión de directorios de expedientes
├── gui/                     # Interfaz gráfica
├── mcp_server/              # Servidor MCP (Model Context Protocol)
├── pjn/                     # Módulo principal de scraping PJN
│   ├── agenda/
│   ├── cli/
│   ├── gui/
│   ├── models/
│   ├── monitor/
│   ├── parsers/
│   ├── persistence/
│   ├── scraping/
│   ├── scripts/
│   ├── services/
│   └── utils/
├── procesador_pdf/          # Procesamiento de PDFs
├── tests/                   # Tests
├── web_app/                 # Aplicación web Flask
├── requirements.txt         # Dependencias de producción
└── requirements-dev.txt     # Dependencias de desarrollo
```

---

## 2. Dependencias Python

### 2.1 Requirements.txt (Producción)

**Versión mínima de Python:** >= 3.10

#### Core Dependencies
```txt
# Web scraping y automatización
playwright==1.50.0

# Scheduling y tareas asíncronas
APScheduler==3.11.0

# Variables de entorno
python-dotenv>=1.0.0
```

#### GUI y System Tray (Multiplataforma)
```txt
# macOS
rumps==0.4.0; sys_platform == 'darwin'
pyobjc-core==11.1; sys_platform == 'darwin'
pyobjc-framework-Cocoa==11.1; sys_platform == 'darwin'
pyobjc-framework-Quartz==11.1; sys_platform == 'darwin'
pyobjc-framework-Security==11.1; sys_platform == 'darwin'
pyobjc-framework-WebKit==11.1; sys_platform == 'darwin'

# Windows/Linux
pystray==0.19.5; sys_platform != 'darwin'
pillow==12.0.0; sys_platform != 'darwin'
```

#### Web Application
```txt
Flask==3.1.2
```

#### MCP Server
```txt
# Model Context Protocol
mcp>=1.0.0
pdfplumber>=0.11.0          # Extracción de texto de PDFs
python-dateutil>=2.8.0       # Parsing de fechas

# HTTP Server (ChatGPT/Claude compatible)
fastapi>=0.104.1
uvicorn[standard]>=0.24.0
python-multipart>=0.0.6
pydantic>=2.0.0
```

#### Testing
```txt
pytest==8.4.2
pytest-asyncio==1.2.0
pytest-cov>=5.0.0
```

### 2.2 Requirements-dev.txt (Desarrollo)

```txt
# Incluye requirements.txt
-r requirements.txt

# Testing extendido
pytest==8.4.2
pytest-asyncio==1.2.0
pytest-cov>=5.0.0
pytest-mock>=3.12.0
pytest-timeout>=2.2.0

# Code Quality
black>=24.0.0               # Formateo
isort>=5.13.0               # Ordenamiento de imports
mypy>=1.8.0                 # Type checking
ruff>=0.1.0                 # Linter rápido

# Pre-commit
pre-commit>=3.6.0

# Debugging
ipython>=8.20.0
ipdb>=0.13.13
```

---

## 3. Archivos de Configuración

### 3.1 config/sistema.json

**Ubicación:** `Sistema_v5/config/sistema.json`

Este es el archivo de configuración principal del sistema. Contiene:

#### Directorios
```json
{
  "directorio_monitor_datos": "/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v5/var/monitor",
  "directorio_extraccion_inicial": "/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v5/workspace/inicial",
  "directorio_extracciones_temporales": "/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v5/workspace/temp",
  "directorio_expedientes_base": "/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v5/workspace/expedientes",
  "directorio_comparaciones": "/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v5/workspace/comparaciones",
  "directorio_logs": "/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v5/var/log",
  "directorio_backups": "/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v5/backups",
  "directorio_cache": "/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v5/var/cache",
  "directorio_descargas": "/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v5/workspace/downloads",
  "directorio_reportes": "/Users/davidalejandroliva/PycharmProjects/sintaXis/Sistema_v5/workspace/reportes"
}
```

**IMPORTANTE:** Los paths son absolutos en el archivo original. Para replicación, se recomienda usar paths relativos.

#### Monitor - Configuración de horarios
```json
{
  "modo_monitor": "automatico",
  "headless": false,
  "intervalos_laboral_expedientes": 10,     // minutos
  "intervalos_laboral_entradas": 15,        // minutos
  "intervalos_no_laboral_expedientes": 3,   // minutos
  "intervalos_no_laboral_entradas": 2,      // minutos
  "dias_laborales": ["lunes", "martes", "jueves", "viernes"],
  "hora_inicio": "08:00",
  "hora_fin": "18:00"
}
```

#### Monitor - Reintentos y notificaciones
```json
{
  "max_reintentos_expedientes": 3,
  "espera_reintentos_expedientes": 30,      // segundos
  "max_reintentos_entradas": 3,
  "espera_reintentos_entradas": 30,         // segundos
  "notificar_nuevas_entradas": true,
  "notificar_cambios_expedientes": true,
  "notificar_errores": true,
  "actualizar_actuaciones_automaticamente": false,
  "max_reintentos_actualizacion_actuaciones": 2
}
```

#### Monitor - Filtros de fechas
```json
{
  "fecha_corte_expedientes": null,
  "fecha_desde_entradas": null,
  "fecha_hasta_entradas": null,
  "fecha_desde_expedientes": null,
  "fecha_hasta_expedientes": null,
  "dias_atras_entradas": 5,
  "dias_atras_expedientes": 2
}
```

#### Extracción
```json
{
  "extraccion_expedientes_completa": true,
  "expedientes_orden": "fecha",
  "expedientes_detener_duplicados": true,
  "expedientes_max_paginas": null,
  "max_paginas_expedientes": null,
  "timeout_default": 8000,                  // ms
  "timeout_login": 60000,                   // ms
  "timeout_descarga": 30000,                // ms
  "max_reintentos_descarga": 15
}
```

#### Sistema
```json
{
  "fecha_inicio_sistema": "2025-10-21",
  "fecha_ultimo_backup": null,
  "intervalo_backup_automatico": 7,         // días
  "retener_historico_dias": 90,
  "nivel_log": "DEBUG",
  "max_tamaño_log_mb": 50,
  "rotacion_logs": false,
  "guardar_sesion": true,
  "duracion_sesion_horas": 24,
  "limite_memoria_mb": 2048,
  "max_archivos_cache": 1000
}
```

#### Reportes
```json
{
  "generar_reportes": true,
  "formatos_reportes": ["json"],
  "dias_retencion_reportes": 30,
  "modo_comparacion": "manual",
  "generar_reportes_automaticos": false,
  "formato_reportes": "json"
}
```

### 3.2 config/monitor.json

Configuración específica del monitor (versión legacy, ahora unificada en sistema.json):

```json
{
  "headless": false,
  "modo": "automatico",
  "directorio_datos": "/Users/.../Sistema_v5/var/monitor",
  "intervalos_laboral_expedientes": 15,
  "intervalos_laboral_entradas": 10,
  "intervalos_no_laboral_expedientes": 55,
  "intervalos_no_laboral_entradas": 30,
  "dias_laborales": ["lunes", "martes", "jueves", "viernes"],
  "hora_inicio": "08:00",
  "hora_fin": "18:00",
  "sesion_persistente": true,
  "sesion_timeout_minutos": 60,
  "tipos_entradas": ["N"],
  "comparacion_automatica": false,
  "dias_atras_entradas": 14
}
```

---

## 4. Variables de Entorno

### 4.1 Sistema Principal

El sistema soporta configuración mediante variables de entorno con prefijo `SISTEMA_`:

#### Directorios
```bash
SISTEMA_DIRECTORIO_EXTRACCION_INICIAL
SISTEMA_DIRECTORIO_EXTRACCIONES_TEMPORALES
SISTEMA_DIRECTORIO_EXPEDIENTES_BASE
SISTEMA_DIRECTORIO_COMPARACIONES
SISTEMA_DIRECTORIO_REPORTES
SISTEMA_DIRECTORIO_LOGS
SISTEMA_DIRECTORIO_BACKUPS
SISTEMA_DIRECTORIO_CACHE
SISTEMA_DIRECTORIO_DESCARGAS
SISTEMA_DIRECTORIO_MONITOR_DATOS
```

#### Monitor
```bash
SISTEMA_MODO_MONITOR                           # automatico|manual
SISTEMA_HEADLESS                               # true|false
SISTEMA_INTERVALOS_LABORAL_EXPEDIENTES         # minutos
SISTEMA_INTERVALOS_LABORAL_ENTRADAS            # minutos
SISTEMA_INTERVALOS_NO_LABORAL_EXPEDIENTES      # minutos
SISTEMA_INTERVALOS_NO_LABORAL_ENTRADAS         # minutos
SISTEMA_DIAS_LABORALES                         # lunes,martes,miercoles,...
SISTEMA_HORA_INICIO                            # HH:MM
SISTEMA_HORA_FIN                               # HH:MM
SISTEMA_NOTIFICAR_NUEVAS_ENTRADAS              # true|false
SISTEMA_NOTIFICAR_CAMBIOS_EXPEDIENTES          # true|false
SISTEMA_NOTIFICAR_ERRORES                      # true|false
```

#### Scraping
```bash
SISTEMA_MAX_PAGINAS_EXPEDIENTES
SISTEMA_TIMEOUT_DEFAULT                        # ms
SISTEMA_TIMEOUT_LOGIN                          # ms
SISTEMA_TIMEOUT_DESCARGA                       # ms
SISTEMA_MAX_REINTENTOS_DESCARGA
```

#### Sistema
```bash
SISTEMA_NIVEL_LOG                              # DEBUG|INFO|WARNING|ERROR|CRITICAL
SISTEMA_MAX_TAMANO_LOG_MB
SISTEMA_ROTACION_LOGS                          # true|false
SISTEMA_GUARDAR_SESION                         # true|false
SISTEMA_DURACION_SESION_HORAS
SISTEMA_LIMITE_MEMORIA_MB
SISTEMA_MAX_ARCHIVOS_CACHE
```

### 4.2 MCP Server

Variables con prefijo `MCP_`:

```bash
MCP_WORKSPACE_PATH                             # Ruta al workspace
MCP_SERVER_NAME                                # Nombre del servidor
MCP_SERVER_VERSION                             # Versión
MCP_SERVER_HOST                                # 0.0.0.0 o 127.0.0.1
MCP_SERVER_PORT                                # Puerto (default: 8000)
MCP_AUTH_TOKENS                                # Tokens separados por coma
MCP_MAX_PDF_PAGES                              # Límite de páginas por PDF
MCP_MAX_PDF_SIZE_MB                            # Tamaño máximo en MB
MCP_ENABLE_PDF_EXTRACTION                      # true|false
MCP_ENABLE_FULL_TEXT_SEARCH                    # true|false
MCP_ENABLE_STATISTICS                          # true|false
```

### 4.3 PJN Scraping

Variables con prefijo `PJN_`:

```bash
PJN_MAX_PAGINAS                                # Límite de páginas
PJN_TIMEOUT_DEFAULT                            # Timeout en ms
PJN_TIMEOUT_LOGIN                              # Timeout login en ms
PJN_MAX_REINTENTOS_DESCARGA                    # Reintentos
PJN_HEADLESS                                   # true|false
PJN_COINCIDENCIA_CARATULA_PARCIAL              # true|false
PJN_LOGIN_URL                                  # URL de login
PJN_DIR_ACTUACIONES                            # Directorio actuaciones
PJN_DIR_ENTRADAS                               # Directorio entradas
```

---

## 5. Scripts de Ejecución

### 5.1 Scripts principales en bin/

Todos los scripts están en `Sistema_v5/bin/`:

#### 5.1.1 ejecutar_mcp_server.py
**Descripción:** Inicia el servidor MCP para acceso a actuaciones
**Uso:**
```bash
python bin/ejecutar_mcp_server.py [--config CONFIG_FILE] [--workspace WORKSPACE_PATH] [--port PORT] [--debug]
```

**Características:**
- Lee configuración desde archivo JSON o variables de entorno
- Valida configuración antes de iniciar
- Logging configurado en stderr (no interfiere con stdio MCP)
- Soporte para debug mode

#### 5.1.2 ejecutar_extraccion.py
**Descripción:** Script de extracción inicial v2.0 con GUI integrada
**Uso:**
```bash
# Modo GUI (recomendado)
python bin/ejecutar_extraccion.py

# Con opciones
python bin/ejecutar_extraccion.py --headless --config config/sistema.json

# Desde JSON existente
python bin/ejecutar_extraccion.py --desde-json data/expedientes.json

# Modo CLI (sin GUI)
python bin/ejecutar_extraccion.py --no-gui --headless
```

**Opciones:**
- `--config`: Archivo de configuración (default: config/sistema.json)
- `--headless`: Ejecutar Playwright sin navegador visible
- `--no-filtros`: Omitir paso de filtrado
- `--no-adjuntos`: No descargar archivos adjuntos
- `--umbral-errores`: Errores consecutivos antes de pausar (default: 5)
- `--desde-json`: Usar JSON ya extraído
- `--no-gui`: Modo CLI sin interfaz gráfica

**Flujo del script:**
1. **Fase 1:** Extracción del listado completo (MonitorPJN)
2. **Fase 2:** Filtrado y gestión de estados (GUI integrada)
3. **Fase 3:** Generación de directorios por expediente
4. **Fase 4:** Extracción completa batch con manejo de errores
5. **Post-proceso:** Inicialización del sistema de estados

#### 5.1.3 Otros scripts importantes

```bash
bin/
├── ejecutar_monitor.py                    # Monitor manual
├── ejecutar_monitor_continuo.py          # Monitor continuo
├── ejecutar_monitor_sistema.py           # Monitor del sistema
├── ejecutar_monitor_statusbar.py         # Monitor en status bar (macOS)
├── ejecutar_monitor_tray.py              # Monitor en system tray
├── ejecutar_monitor_universal.py         # Monitor multiplataforma
├── ejecutar_web.py                       # Aplicación web Flask
├── inicializar_directorios.py            # Inicializa estructura de dirs
├── start_http_server.py                  # Servidor HTTP para MCP
└── seleccionar_expedientes.py            # Selector de expedientes
```

### 5.2 Scripts de mantenimiento

Ubicados en `Sistema_v5/scripts/mantenimiento/`:

```bash
scripts/mantenimiento/
├── inicializar_sistema_estados.py        # Inicializa estados de expedientes
├── inicializar_historial_monitor.py     # Inicializa historial del monitor
└── ...
```

---

## 6. Sistema de Configuración

### 6.1 Arquitectura de configuración

El sistema usa una **arquitectura de configuración unificada** con tres capas:

```
┌─────────────────────────────────────┐
│   Variables de Entorno (ENV)       │
│   (Mayor prioridad)                 │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Archivos JSON                     │
│   config/sistema.json                │
│   config/monitor.json                │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│   Valores por Defecto (Hardcoded)  │
│   En clases Python                  │
└─────────────────────────────────────┘
```

### 6.2 Clases de Configuración

#### 6.2.1 SystemConfig (Configuración Unificada)
**Archivo:** `configuracion/core/system_config.py`

Clase principal que unifica toda la configuración del sistema:

```python
from Sistema_v5.configuracion.core import SystemConfig

# Cargar desde archivo
config = SystemConfig.from_file("config/sistema.json")

# Cargar desde variables de entorno
config = SystemConfig.from_env(prefix="SISTEMA_")

# Migrar desde monitor.json legacy
config = SystemConfig.from_monitor_config("config/monitor.json")

# Guardar configuración
config.to_file("config/sistema.json")

# Crear backup
backup_path = config.hacer_backup()

# Crear todos los directorios
config.crear_directorios()
```

**Componentes:**
- Directorios del sistema
- Configuración de monitoreo
- Parámetros de extracción y scraping
- Configuración de comparaciones y reportes
- Configuración del sistema (logs, backups, cache)

#### 6.2.2 ScrapingConfig
**Archivo:** `configuracion/core/scraping_config.py`

Configuración de scraping del portal PJN:

```python
from Sistema_v5.configuracion.core import ScrapingConfig, BrowserConfig, AuthConfig

# Scraping
scraping = ScrapingConfig()
scraping.timeout_default           # 8000 ms
scraping.timeout_login             # 60000 ms
scraping.max_paginas_expedientes   # 200

# Browser
browser = BrowserConfig()
browser.headless                   # False
browser.args                       # Lista de argumentos

# Auth
auth = AuthConfig()
auth.login_url                     # URL de login
auth.session_file_name             # Archivo de sesión
```

#### 6.2.3 MCPConfig
**Archivo:** `mcp_server/config.py`

Configuración del servidor MCP:

```python
from Sistema_v5.mcp_server.config import MCPConfig

# Desde archivo
config = MCPConfig.from_file("config/mcp_config.json")

# Desde env
config = MCPConfig.from_env()

# Validar
errors = config.validate()

# Guardar
config.save("config/mcp_config.json")
```

#### 6.2.4 MonitorConfig
**Archivo:** `configuracion/monitor/config.py`

Configuración específica del monitor:

```python
from Sistema_v5.configuracion.monitor import MonitorConfig
from Sistema_v5.configuracion.core import SystemConfig

# Crear desde SystemConfig
system_config = SystemConfig.from_file("config/sistema.json")
monitor_config = MonitorConfig.from_system_config(system_config)

# Validar
monitor_config.validar()
```

### 6.3 Constantes del Sistema

**Archivo:** `pjn/constants.py`

Constantes globales del sistema (no configurables):

```python
# URL del portal
URL_CONSULTAS = "https://scw.pjn.gov.ar/scw/consultaListaRelacionados.seam"

# Motivos de finalización
MOTIVO_FIN_LISTADO = "fin_listado"
MOTIVO_LIMITE_PAGINAS = "limite_paginas"
MOTIVO_LIMITE_FECHA = "limite_fecha"
MOTIVO_DUPLICADO_ENCONTRADO = "duplicado_encontrado"

# Campos de expedientes
CAMPO_NUMERO = "numero"
CAMPO_CARATULA = "caratula"
CAMPO_DEPENDENCIA = "dependencia"

# Ordenamiento
ORDEN_FECHA = "fecha"
ORDEN_CARATULA = "caratula"
ORDEN_OFICINA = "oficina"

# Timeouts y límites
MAX_LONGITUD_FINGERPRINT = 4_096
MAX_LONGITUD_NOMBRE_ARCHIVO = 255
```

---

## 7. Recomendaciones para Replicación

### 7.1 Checklist de Migración a Sistema_v6

#### ✅ Paso 1: Estructura de directorios
- [ ] Crear estructura base de directorios:
  ```
  Sistema_v6/
  ├── bin/
  ├── config/
  ├── configuracion/
  ├── docs/
  ├── mcp_server/
  ├── pjn/
  ├── tests/
  ├── var/
  │   ├── cache/
  │   ├── log/
  │   └── monitor/
  └── workspace/
      ├── comparaciones/
      ├── descargas/
      ├── downloads/
      ├── expedientes/
      ├── inicial/
      ├── reportes/
      └── temp/
  ```

#### ✅ Paso 2: Dependencias
- [ ] Copiar `requirements.txt` y adaptarlo
- [ ] Copiar `requirements-dev.txt` y adaptarlo
- [ ] Verificar compatibilidad de versiones
- [ ] Instalar en entorno virtual
- [ ] Ejecutar `playwright install` para browsers

#### ✅ Paso 3: Archivos de configuración
- [ ] Crear `config/sistema.json` con paths relativos:
  ```json
  {
    "directorio_monitor_datos": "var/monitor",
    "directorio_extraccion_inicial": "workspace/inicial",
    "directorio_expedientes_base": "workspace/expedientes",
    "directorio_logs": "var/log",
    ...
  }
  ```
- [ ] Ajustar intervalos de monitoreo según necesidad
- [ ] Configurar días laborales y horarios
- [ ] Establecer nivel de log apropiado (INFO para prod, DEBUG para dev)

#### ✅ Paso 4: Sistema de configuración
- [ ] Copiar módulo `configuracion/` completo
- [ ] Copiar `pjn/constants.py`
- [ ] Verificar imports en `configuracion/__init__.py`
- [ ] Probar carga de configuración:
  ```python
  from Sistema_v6.configuracion.core import SystemConfig
  config = SystemConfig.from_file("config/sistema.json")
  config.crear_directorios()
  ```

#### ✅ Paso 5: MCP Server
- [ ] Copiar módulo `mcp_server/`
- [ ] Crear `config/mcp_config.json`:
  ```json
  {
    "workspace_path": "workspace",
    "server_name": "sintaxis-actuaciones-v6",
    "server_version": "1.0.0",
    "server_host": "0.0.0.0",
    "server_port": 8000,
    "enable_pdf_extraction": true
  }
  ```
- [ ] Probar servidor: `python bin/ejecutar_mcp_server.py --debug`

#### ✅ Paso 6: Scripts de ejecución
- [ ] Copiar scripts de `bin/`
- [ ] Actualizar paths internos si es necesario
- [ ] Hacer scripts ejecutables: `chmod +x bin/*.py`
- [ ] Crear wrapper scripts si se necesitan

#### ✅ Paso 7: Testing
- [ ] Copiar configuración de pytest
- [ ] Copiar tests relevantes
- [ ] Ejecutar suite de tests: `pytest tests/`
- [ ] Verificar cobertura: `pytest --cov=Sistema_v6`

#### ✅ Paso 8: Variables de entorno
- [ ] Crear archivo `.env.example` con todas las variables:
  ```bash
  # Sistema Principal
  SISTEMA_HEADLESS=true
  SISTEMA_NIVEL_LOG=INFO
  SISTEMA_MODO_MONITOR=automatico

  # MCP Server
  MCP_SERVER_PORT=8000
  MCP_ENABLE_PDF_EXTRACTION=true

  # PJN Scraping
  PJN_HEADLESS=true
  PJN_MAX_PAGINAS=200
  ```
- [ ] Documentar en README.md

### 7.2 Cambios Clave Recomendados

#### 🔄 De v5.1.1 a v6

1. **Paths absolutos → Paths relativos**
   - En v5.1.1 los paths en JSON son absolutos
   - En v6 usar paths relativos al directorio raíz del proyecto
   - Implementar función `get_project_root()` para resolver paths

2. **Unificación de configuración**
   - v5.1.1 tiene `config/sistema.json` Y `config/monitor.json`
   - v6 debería usar solo `config/sistema.json` (ya unificado en v5.1.1)
   - Mantener método de migración `from_monitor_config()` por compatibilidad

3. **Mejoras en logging**
   - Estandarizar formato de logs
   - Implementar rotación de logs (en v5.1.1 está en `false`)
   - Separar logs por módulo

4. **Variables de entorno**
   - Crear archivo `.env` para desarrollo
   - Documentar todas las variables disponibles
   - Implementar validación de variables críticas

5. **Testing**
   - Aumentar cobertura de tests
   - Agregar tests de integración
   - Configurar CI/CD

### 7.3 Diferencias Importantes

#### ⚠️ Notas sobre compatibilidad

1. **Python 3.10+** es REQUERIDO
   - Uso de `from __future__ import annotations`
   - Type hints modernos (`X | Y` en lugar de `Union[X, Y]`)
   - Match statements (si se usan)

2. **Playwright**
   - Requiere instalación de browsers: `playwright install`
   - En headless mode: `playwright install --with-deps chromium`

3. **macOS vs Linux/Windows**
   - System tray: `rumps` (macOS) vs `pystray` (otros)
   - Paths: usar `pathlib.Path` para compatibilidad

4. **Permisos**
   - Scripts en `bin/` necesitan permisos de ejecución
   - Directorios `var/` y `workspace/` necesitan permisos de escritura

### 7.4 Documentación Adicional

Para completar la replicación, consultar también:

- `Sistema_v5/docs/` - Documentación completa del sistema
- `Sistema_v5/docs/MONITOR.md` - Documentación del monitor
- `Sistema_v5/docs/mcp/` - Documentación del servidor MCP
- `Sistema_v5/README.md` - README principal (si existe)

---

## Resumen Ejecutivo

### Archivos Clave para Replicar

1. **Dependencias:**
   - `requirements.txt`
   - `requirements-dev.txt`

2. **Configuración:**
   - `config/sistema.json` (PRINCIPAL)
   - `config/monitor.json` (legacy, opcional)
   - `mcp_server/config.py`

3. **Módulos Python:**
   - `configuracion/` (completo)
   - `pjn/constants.py`
   - `mcp_server/` (completo)

4. **Scripts:**
   - `bin/ejecutar_mcp_server.py`
   - `bin/ejecutar_extraccion.py`
   - Otros scripts según necesidad

5. **Estructura:**
   - Crear directorios `var/` y `workspace/` con subdirectorios
   - Copiar `.gitignore`

### Prioridad de Replicación

**Alta prioridad (esencial):**
- ✅ Dependencias (requirements.txt)
- ✅ Módulo configuracion/
- ✅ config/sistema.json
- ✅ Estructura de directorios
- ✅ pjn/constants.py

**Media prioridad (importante):**
- ⚡ MCP Server completo
- ⚡ Scripts de bin/
- ⚡ Sistema de variables de entorno

**Baja prioridad (opcional):**
- 📋 Web app (Flask)
- 📋 GUI (Tkinter)
- 📋 Scripts de mantenimiento específicos

---

**Fin del análisis**
