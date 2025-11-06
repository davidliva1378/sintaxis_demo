# Sistema PJN v6

**Sistema de extracción y monitoreo automatizado del Portal Judicial Nacional (Argentina)**

[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Playwright](https://img.shields.io/badge/Playwright-1.50+-orange.svg)](https://playwright.dev/python/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)](#testing)

---

## 🎯 Descripción

Sistema PJN v6 es una **refactorización completa del Sistema v5**, implementando **Clean Architecture** y **Domain-Driven Design** para:

- 📥 **Extracción completa** de expedientes, entradas/notificaciones y actuaciones del PJN
- 🔍 **Filtrado inteligente** de expedientes por múltiples criterios
- 📁 **Gestión de workspaces** con estructura organizada por expediente
- 🔔 **Monitoreo automático** de cambios con notificaciones multi-canal
- 🤖 **Integración MCP** para Claude AI y otros LLMs
- 🌐 **API REST moderna** con FastAPI y documentación interactiva
- ⌨️ **CLI poderosa** para automatización y scripting
- 🔌 **Sistema de plugins** extensible y modular

---

## ✨ Estado del Proyecto

### 🎉 Migración Completada

**Todas las capas de Clean Architecture están completas y funcionales:**

| Capa | Componentes | Estado |
|------|-------------|--------|
| **Domain Layer** | Entidades, Value Objects, Utils | ✅ 100% |
| **Application Layer** | Use Cases, Ports, Services | ✅ 100% |
| **Infrastructure Layer** | Adapters, Config, Storage, Scraping | ✅ 100% |
| **Presentation Layer** | CLI, REST API, MCP Server | ✅ 100% |
| **Testing** | Unit Tests, Integration Tests | ✅ Core completo |

**Líneas de código migradas:** ~8,500 líneas desde Sistema_v5

### 🚀 Funcionalidades Disponibles

#### ✅ Scraping (100% funcional)
- **Extracción de expedientes** con paginación PrimeFaces
- **Extracción de entradas** (bandeja de notificaciones) con scroll infinito
- **Extracción de actuaciones** con tabs (actuales + históricas)
- **Descarga de archivos** adjuntos de actuaciones
- **Gestión de sesiones** persistentes con Playwright
- **Anti-detección** y manejo inteligente de timeouts

#### ✅ Casos de Uso (Completos)
- `ExtraerExpedientesUseCase` - Extrae y filtra expedientes
- `ExtraerEntradasUseCase` - Extrae notificaciones
- `ExtraerActuacionesUseCase` - Extrae actuaciones de un expediente
- `FiltrarExpedientesUseCase` - Filtra con múltiples criterios
- `GestionarWorkspaceUseCase` - Crea y gestiona workspaces

#### ✅ Presentación (3 interfaces)
- **CLI** - Interfaz de línea de comandos con Rich
- **REST API** - API completa con FastAPI + Swagger/OpenAPI
- **MCP Server** - Integración con Claude AI (Model Context Protocol)

#### ✅ Infraestructura
- **JSONStorageAdapter** - Persistencia en archivos JSON
- **WorkspaceAdapter** - Gestión de directorios por expediente
- **PlaywrightScraperAdapter** - Scraping completo del PJN
- **Settings** - Configuración centralizada con Pydantic

---

## 📦 Instalación

### Requisitos Previos

- **Python 3.10+** (recomendado 3.11 o 3.12)
- **Git**
- **Navegador Chromium** (se instala automáticamente con Playwright)

### Instalación Rápida

```bash
# 1. Clonar repositorio
git clone https://github.com/tu-usuario/sistema-pjn-v6.git
cd sistema-pjn-v6/Sistema_v6

# 2. Crear entorno virtual
python -m venv venv

# Linux/Mac
source venv/bin/activate

# Windows
venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar Playwright (navegador)
playwright install chromium

# 5. Configurar credenciales PJN
cp .env.example .env
# Editar .env y agregar:
# PJN_USER=tu_usuario
# PJN_PASSWORD=tu_contraseña
```

---

## 🚀 Uso

### CLI - Interfaz de Línea de Comandos

```bash
# Ver ayuda general
python -m presentation.cli.main --help

# Extraer expedientes
python -m presentation.cli.main extraer-expedientes

# Extraer entradas/notificaciones
python -m presentation.cli.main extraer-entradas

# Extraer actuaciones de un expediente
python -m presentation.cli.main extraer-actuaciones "CNM 0001/2024"

# Filtrar expedientes
python -m presentation.cli.main filtrar \
    --dependencia "CNM" \
    --situacion "A sentencia" \
    --dias-activos 30

# Crear workspace para un expediente
python -m presentation.cli.main crear-workspace "CNM 0001/2024"
```

### API REST - Servidor HTTP

```bash
# Iniciar servidor (modo desarrollo)
python -m presentation.api.rest.main

# O con uvicorn directamente
uvicorn presentation.api.rest.main:app --reload --port 8000
```

**Endpoints disponibles:**

- `GET /` - Información de la API
- `GET /health` - Health check
- `POST /api/v1/expedientes/extraer` - Extrae expedientes
- `POST /api/v1/expedientes/filtrar` - Filtra expedientes
- `POST /api/v1/entradas/extraer` - Extrae entradas
- `POST /api/v1/actuaciones/extraer` - Extrae actuaciones
- `POST /api/v1/workspace/crear` - Crea workspace

**Documentación interactiva:**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### MCP Server - Integración con Claude AI

```bash
# Iniciar servidor MCP
python -m presentation.api.mcp.server
```

**Tools disponibles en Claude:**
- `extraer_expedientes` - Extrae lista de expedientes
- `extraer_entradas` - Extrae notificaciones
- `extraer_actuaciones` - Extrae actuaciones de un expediente
- `filtrar_expedientes` - Filtra por múltiples criterios
- `crear_workspace` - Crea estructura de directorios
- `leer_archivo_workspace` - Lee archivos del workspace

**Recursos disponibles:**
- `expediente://[numero]` - Acceso a datos de expedientes
- `workspace://[numero]` - Acceso a archivos del workspace

---

## 📖 Estructura del Proyecto

### Arquitectura Clean (Capas Concéntricas)

```
Sistema_v6/
├── core/                           # 🎯 DOMAIN LAYER
│   └── domain/
│       ├── entities/               # Entidades del dominio
│       │   ├── expediente.py       # ExpedienteResumen, ExpedienteIdentificacion
│       │   ├── entrada.py          # Entrada (notificaciones)
│       │   ├── actuacion.py        # Actuacion, ActuacionesArchivo
│       │   └── workspace.py        # WorkspaceInfo
│       ├── value_objects/          # Objetos de valor
│       │   ├── criterios_filtrado.py
│       │   └── configuracion_workspace.py
│       └── utils/                  # Utilidades del dominio
│           └── dates.py            # Normalización de fechas
│
├── application/                    # 📋 APPLICATION LAYER
│   ├── use_cases/                  # Casos de uso
│   │   ├── extraer_expedientes.py
│   │   ├── extraer_entradas.py
│   │   ├── extraer_actuaciones.py
│   │   ├── filtrar_expedientes.py
│   │   └── gestionar_workspace.py
│   └── ports/                      # Interfaces (contratos)
│       ├── repositories.py         # IExpedienteRepository, etc.
│       └── services.py             # IScraperPort, IStoragePort, etc.
│
├── infrastructure/                 # 🔧 INFRASTRUCTURE LAYER
│   ├── adapters/
│   │   ├── storage/                # Persistencia
│   │   │   ├── json_storage_adapter.py
│   │   │   └── workspace_adapter.py
│   │   └── scraping/               # Web scraping
│   │       ├── playwright_scraper_adapter.py  # ~590 líneas
│   │       ├── session_manager.py             # ~700 líneas
│   │       ├── pagination.py                  # ~240 líneas
│   │       ├── selectores.py                  # Selectores CSS
│   │       └── parsers/                       # HTML → Entities
│   │           ├── expedientes_parser.py
│   │           ├── entradas_parser.py
│   │           └── actuaciones_parser.py      # ~600 líneas
│   ├── config/
│   │   └── settings.py             # Configuración con Pydantic
│   └── exceptions.py               # Excepciones personalizadas
│
├── presentation/                   # 🖥️ PRESENTATION LAYER
│   ├── cli/                        # Interfaz CLI
│   │   ├── main.py                 # Comandos Click
│   │   └── formatters.py           # Formateo Rich
│   ├── api/
│   │   ├── rest/                   # API REST
│   │   │   ├── main.py             # FastAPI app
│   │   │   ├── routes/             # Endpoints
│   │   │   └── schemas.py          # Pydantic schemas
│   │   └── mcp/                    # MCP Server
│   │       ├── server.py           # Servidor MCP
│   │       └── tools.py            # Tools y recursos
│   └── dependencies.py             # Dependency injection
│
├── tests/                          # 🧪 TESTS
│   ├── unit/                       # Tests unitarios
│   │   └── core/domain/entities/
│   └── integration/                # Tests de integración
│       └── infrastructure/adapters/scraping/
│
├── docs/                           # 📚 DOCUMENTACIÓN
│   ├── ARCHITECTURE.md             # (este archivo)
│   ├── DEVELOPMENT.md              # (próximamente)
│   └── MIGRATION.md                # (próximamente)
│
├── scripts/                        # Scripts de utilidad
├── config/                         # Configuración
├── data/                           # Datos del sistema
├── pyproject.toml                  # Configuración del proyecto
├── requirements.txt                # Dependencias
└── .env                            # Variables de entorno
```

### Principios de Diseño

#### 1. **Clean Architecture**
- ✅ Dependencias apuntan hacia adentro
- ✅ Domain layer sin dependencias externas
- ✅ Inversión de dependencias con Ports & Adapters

#### 2. **Domain-Driven Design**
- ✅ Entidades ricas con lógica de negocio
- ✅ Value Objects inmutables
- ✅ Lenguaje ubicuo del dominio

#### 3. **SOLID**
- ✅ Single Responsibility: cada clase tiene una responsabilidad
- ✅ Open/Closed: extensible sin modificar
- ✅ Liskov Substitution: interfaces bien definidas
- ✅ Interface Segregation: interfaces específicas
- ✅ Dependency Inversion: abstracciones sobre implementaciones

#### 4. **Type Safety**
- ✅ Type hints en todas las funciones
- ✅ Pydantic para validación
- ✅ Mypy para validación estática

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Solo tests unitarios
pytest tests/unit/ -v

# Solo tests de integración (requieren credenciales PJN)
PJN_USUARIO=tu_usuario PJN_PASSWORD=tu_pass pytest tests/integration/ -v

# Tests con cobertura
pytest tests/ --cov=. --cov-report=html

# Tests en paralelo (más rápido)
pytest tests/ -n auto

# Tests de un módulo específico
pytest tests/unit/core/domain/entities/test_expediente.py -v
```

### Estado de Testing

| Tipo | Cobertura | Estado |
|------|-----------|--------|
| **Unit Tests** | Domain entities | ✅ Completo |
| **Integration Tests** | Scraping adapters | ✅ Completo |
| **E2E Tests** | - | ⏳ Pendiente |

**Tests de integración para scraping:**
- ✅ `test_initialization` - Inicialización del adapter
- ✅ `test_extraer_expedientes_con_credenciales` - Extracción completa
- ✅ `test_extraer_entradas_con_credenciales` - Extracción de notificaciones
- ✅ `test_extraer_actuaciones_con_credenciales` - Extracción de actuaciones

Ver [tests/integration/infrastructure/adapters/scraping/README.md](tests/integration/infrastructure/adapters/scraping/README.md) para más detalles.

---

## 🛠️ Desarrollo

### Setup Desarrollo

```bash
# Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# Instalar pre-commit hooks (opcional)
pre-commit install
```

### Formateo y Linting

```bash
# Formatear código con black
black .

# Ordenar imports con isort
isort .

# Linting con ruff
ruff check .

# Type checking con mypy
mypy .

# Todo junto (antes de commit)
black . && isort . && ruff check . && mypy .
```

### Convenciones de Código

- **Formateo:** Black (line-length=100)
- **Imports:** isort (black profile)
- **Linting:** Ruff (pyflakes, pycodestyle, etc.)
- **Type hints:** Obligatorios en todas las funciones públicas
- **Docstrings:** Google style para funciones públicas
- **Commits:** [Conventional Commits](https://www.conventionalcommits.org/)

---

## 📊 Roadmap

### ✅ Fase 0: Setup Inicial
- ✅ Estructura de directorios
- ✅ Configuración de proyecto
- ✅ Documentación base

### ✅ Fase 1: Domain Layer
- ✅ Entidades (Expediente, Entrada, Actuacion)
- ✅ Value Objects (CriteriosFiltrado, etc.)
- ✅ Utils (normalización de fechas)
- ✅ Tests unitarios

### ✅ Fase 2: Application Layer
- ✅ Use Cases (5 casos completos)
- ✅ Ports (interfaces)
- ✅ Dependency injection

### ✅ Fase 3: Infrastructure Layer
- ✅ Storage adapters (JSON, Workspace)
- ✅ Scraping completo (Playwright, parsers, pagination)
- ✅ Configuration (Settings con Pydantic)
- ✅ Exceptions personalizadas

### ✅ Fase 4: Presentation Layer
- ✅ CLI con Click + Rich
- ✅ REST API con FastAPI
- ✅ MCP Server para Claude AI
- ✅ Dependency injection

### ✅ Fase 5: Testing & Documentación
- ✅ Tests unitarios de dominio
- ✅ Tests de integración de scraping
- ✅ Documentación completa
- ⏳ E2E tests (pendiente)

### 🔜 Próximas Mejoras

- [ ] **Web UI** moderna (React/Vue)
- [ ] **Base de datos** (PostgreSQL + SQLAlchemy)
- [ ] **Caché** (Redis) para performance
- [ ] **Notificaciones** (Email, Telegram, WhatsApp)
- [ ] **Monitoreo automático** programado
- [ ] **Plugins** extensibles
- [ ] **IA local** (Ollama) para análisis
- [ ] **OCR** avanzado para PDFs

---

## 📚 Documentación Adicional

### Documentación Completa Disponible

- **[📖 Manual de Usuario Completo](MANUAL_USUARIO.md)** - Guía completa de configuración y uso (93 páginas)
  - Instalación (Docker y nativa)
  - Configuración inicial
  - Guía de todos los módulos (Expedientes, Workspaces, Monitoreo, Settings)
  - Guía de CLI y API REST
  - Flujos de trabajo comunes
  - Resolución de problemas
  - Mejores prácticas y FAQ

- **[🚀 Guía de Inicio Rápido](INICIO_RAPIDO.md)** - Empieza a usar el sistema en 5 minutos
  - Instalación rápida con Docker
  - Primera configuración
  - Primera extracción
  - Comandos útiles

- **[🐳 Guía de Docker](DOCKER.md)** - Deployment con Docker y Docker Compose
  - Requisitos y instalación
  - Comandos de Docker
  - Troubleshooting
  - Producción

- **[🌐 Plan de Web UI](docs/WEB_UI_PLAN.md)** - Documentación técnica del frontend
  - 12 fases de desarrollo completadas
  - Stack tecnológico completo
  - Componentes implementados
  - Testing y Docker

### Documentación Técnica Frontend

- **[🎨 UX Improvements](frontend/UX_IMPROVEMENTS.md)** - Mejoras de experiencia de usuario
- **[🧪 Testing Guide](frontend/TESTING.md)** - Guía de testing con Vitest

### Próxima Documentación

- [📐 Arquitectura Detallada](docs/ARCHITECTURE.md) *(próximamente)*
- [👨‍💻 Guía de Desarrollo](docs/DEVELOPMENT.md) *(próximamente)*
- [🔄 Historial de Migración v5→v6](docs/MIGRATION.md) *(próximamente)*

---

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crear una rama feature (`git checkout -b feature/amazing-feature`)
3. Hacer commits siguiendo [Conventional Commits](https://www.conventionalcommits.org/)
4. Push a la rama (`git push origin feature/amazing-feature`)
5. Abrir un Pull Request

### Tipos de Commits

```
feat: nueva funcionalidad
fix: corrección de bug
docs: documentación
style: formateo (no afecta lógica)
refactor: refactorización de código
test: agregar/modificar tests
chore: tareas de mantenimiento
perf: mejoras de performance
ci: cambios en CI/CD
```

---

## 📄 Licencia

Este proyecto está bajo la **MIT License** - ver [LICENSE](LICENSE) para detalles.

---

## 👥 Autores

- **Equipo Sistema PJN** - Desarrollo y mantenimiento

---

## 🙏 Agradecimientos

- **Portal Judicial Nacional** de Argentina por la plataforma
- **Playwright** por la excelente herramienta de web scraping
- **FastAPI** por el framework moderno de APIs
- **Pydantic** por la validación de datos
- **Click** por la CLI framework
- **Claude AI** por asistencia en arquitectura y desarrollo

---

## 📞 Soporte

- 🐛 **Issues:** [GitHub Issues](https://github.com/tu-usuario/sistema-pjn-v6/issues)
- 💬 **Discusiones:** [GitHub Discussions](https://github.com/tu-usuario/sistema-pjn-v6/discussions)
- 📧 **Email:** dev@sistemapjn.com

---

## 🔗 Enlaces Útiles

- [Portal Judicial Nacional](https://scw.pjn.gov.ar/)
- [Documentación Playwright](https://playwright.dev/python/)
- [Documentación FastAPI](https://fastapi.tiangolo.com/)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Model Context Protocol](https://modelcontextprotocol.io/)

---

**Versión:** 6.0.0
**Estado:** ✅ Core completo, listo para producción
**Última actualización:** 2025-11-05

---

Hecho con ❤️ para la comunidad legal argentina
