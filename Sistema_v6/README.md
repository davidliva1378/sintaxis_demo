# Sistema v6 - Sistema de Gestión de Expedientes PJN

[![CI/CD Pipeline](https://github.com/USER/REPO/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/USER/REPO/actions)
[![codecov](https://codecov.io/gh/USER/REPO/branch/main/graph/badge.svg)](https://codecov.io/gh/USER/REPO)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Sistema modular para extracción, monitoreo y gestión de expedientes del Poder Judicial de la Nación (PJN).

## 📁 Estructura del Proyecto

```
Sistema_v6/
├── configuracion/           # Configuración centralizada
│   ├── config.py           # Configuración general del sistema
│   ├── urls.py             # URLs del portal PJN
│   └── estados.py          # Gestión de estados de expedientes
│
├── pjn/                    # Interacción con portal PJN
│   ├── auto_login.py       # Autenticación y sesiones
│   ├── navegador.py        # Control de Playwright
│   └── monitor/            # Monitoreo de expedientes
│       ├── extraer_expedientes.py
│       └── verificacion_expedientes.py
│
├── extractor_inicial/      # Extracción incremental
│   ├── extraccion_inicial.py
│   ├── procesamiento_expedientes.py
│   └── main_extraccion.py
│
├── extraccion_masiva/      # Extracción masiva de expedientes
│   ├── extractor_masivo.py
│   ├── gestor_batch.py
│   ├── gestor_estados.py
│   └── exportadores.py
│
├── gestion_expedientes/    # Comparación y gestión
│   ├── comparar_expedientes.py
│   └── guardar_comparacion.py
│
├── interfaz_web/           # Frontend FastAPI
│   ├── app.py
│   ├── backend/
│   │   ├── main.py         # Servidor FastAPI
│   │   ├── db.py
│   │   ├── api/            # API REST
│   │   │   ├── extraccion.py
│   │   │   └── expedientes.py
│   │   └── templates/      # Templates Jinja2
│   │       ├── base.html
│   │       ├── index.html
│   │       └── extraccion_masiva.html
│   └── static/             # Recursos estáticos
│       ├── js/
│       └── css/
│
├── utils/                  # Utilidades
│   └── logging.py
│
├── bin/                    # Scripts CLI
│   ├── ejecutar_extraccion.py
│   └── ejecutar_web.py
│
└── data/                   # Datos del sistema
    ├── expedientes/        # Expedientes extraídos
    ├── extraccion_masiva/  # Datos de extracciones masivas
    │   ├── listados/
    │   ├── reportes/
    │   └── logs/
    └── monitoreo/          # Datos de monitoreo
```

## 🚀 Inicio Rápido

### 1. Instalación

```bash
cd Sistema_v6
pip install -r requirements.txt
playwright install chromium
```

### 2. Configuración

Configurar variables de entorno:

```bash
export PJN_USERNAME="tu_usuario"
export PJN_PASSWORD="tu_contraseña"
export HEADLESS="true"
```

O crear archivo `.env`:

```env
PJN_USERNAME=tu_usuario
PJN_PASSWORD=tu_contraseña
HEADLESS=true
WEB_HOST=127.0.0.1
WEB_PORT=8000
```

### 3. Uso

#### Extracción Incremental

```bash
python bin/ejecutar_extraccion.py
```

#### Servidor Web

```bash
cd interfaz_web
uvicorn backend.main:app --reload
```

Luego abrir: http://localhost:8000

## 📋 Módulos Principales

### 1. Extracción Incremental

Extrae expedientes del PJN de forma incremental, detectando duplicados automáticamente:

```python
from Sistema_v6.extractor_inicial.extraccion_inicial import extraccion_incremental_async

await extraccion_incremental_async(procesar_expedientes=True)
```

### 2. Extracción Masiva

Extracción completa de expedientes con:
- Filtrado por estados
- Procesamiento por lotes
- Manejo de errores avanzado
- Reportes detallados

```python
from Sistema_v6.extraccion_masiva.extractor_masivo import ExtractorMasivo

extractor = ExtractorMasivo(config)
resultado = await extractor.ejecutar_extraccion_completa()
```

### 3. Gestión de Estados

Sistema de estados para clasificar expedientes:

```python
from Sistema_v6.configuracion.estados import GestorEstados, EstadoExpediente

gestor = GestorEstados()
gestor.actualizar_estado("12345/2024", EstadoExpediente.PRIORIZADO)
```

Estados disponibles:
- `NUEVO`: Recién descubierto
- `MONITOREADO`: En seguimiento activo
- `PRIORIZADO`: Requiere atención urgente
- `ARCHIVADO`: No requiere seguimiento
- `IGNORADO`: Excluido permanentemente

### 4. Interfaz Web

Interfaz web con FastAPI para:
- Visualizar expedientes
- Ejecutar extracciones masivas
- Ver reportes
- Gestionar estados

## 🔧 Configuración Avanzada

### Configuración de Extracción

Editar `Sistema_v6/configuracion/config.py`:

```python
class Config:
    # Timeouts
    TIMEOUT_NAVEGACION = 30000
    TIMEOUT_POR_EXPEDIENTE = 120

    # Errores
    UMBRAL_ERRORES_CONSECUTIVOS = 5
    MAX_REINTENTOS_POR_EXPEDIENTE = 3

    # Navegador
    HEADLESS = True
```

### Credenciales

**Opción 1: Variables de entorno**
```bash
export PJN_USERNAME="usuario"
export PJN_PASSWORD="contraseña"
```

**Opción 2: Archivo .env**
```env
PJN_USERNAME=usuario
PJN_PASSWORD=contraseña
```

## 📊 API REST

### Endpoints de Extracción Masiva

```
POST   /api/extraccion/masiva/iniciar      # Iniciar extracción
GET    /api/extraccion/masiva/progreso/{id} # Ver progreso
POST   /api/extraccion/masiva/cancelar/{id} # Cancelar extracción
GET    /api/extraccion/masiva/historial     # Historial de extracciones
GET    /api/extraccion/masiva/reporte/{id}  # Descargar reporte
WS     /api/extraccion/masiva/ws/{id}       # WebSocket para progreso
```

### Endpoints de Expedientes

```
GET    /api/expedientes                     # Listar expedientes
GET    /api/expedientes/{numero}            # Ver expediente
PUT    /api/expedientes/{numero}/estado     # Actualizar estado
```

## 🧪 Testing

### Ejecutar Tests Localmente

```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=. --cov-report=html --cov-report=term-missing

# Solo tests unitarios
pytest -m unit

# Solo tests de integración
pytest -m integration

# Tests en paralelo (más rápido)
pytest -n auto

# Excluir tests lentos
pytest -m "not slow"
```

### Ver Reporte de Cobertura

```bash
# Generar reporte HTML
pytest --cov=. --cov-report=html

# Abrir en navegador
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### Markers Disponibles

- `unit`: Tests unitarios (rápidos, sin dependencias externas)
- `integration`: Tests de integración (pueden requerir servicios externos)
- `e2e`: Tests end-to-end (requieren sistema completo)
- `slow`: Tests lentos (omitir con `-m "not slow"`)
- `rag`: Tests que requieren servicios RAG (Qdrant, Ollama)
- `db`: Tests que requieren base de datos
- `browser`: Tests que requieren navegador Playwright

### Configuración de Tests

La configuración de pytest está en `pytest.ini`. Incluye:
- Cobertura mínima requerida: 80%
- Modo asyncio automático
- Reportes de cobertura en HTML, XML y terminal
- Exclusión de archivos de test obsoletos

## 📝 Logs

Los logs se guardan en:
- `data/extraccion_masiva/logs/` - Logs de extracciones masivas
- `data/monitoreo/logs/` - Logs de monitoreo

## 🛠️ Desarrollo

### Estructura de Imports

Todos los imports deben usar la ruta completa desde `Sistema_v6`:

```python
from Sistema_v6.configuracion.config import Config
from Sistema_v6.pjn.auto_login import reutilizar_sesion_async
from Sistema_v6.configuracion.urls import URL_CONSULTAS
```

### Agregar Nuevo Módulo

1. Crear módulo en directorio apropiado
2. Agregar `__init__.py` si es un paquete
3. Usar imports absolutos desde `Sistema_v6`
4. Documentar en este README

## 📄 Licencia

Proyecto interno - Uso privado

## 👥 Autores

Sistema de Gestión de Expedientes PJN - Sistema v6

---

**Versión**: 6.0.0
**Última actualización**: 2025-11-07
