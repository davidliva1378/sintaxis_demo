# Sistema PJN v6 - Arquitectura

**Versión:** 6.0.0
**Fecha de creación:** 2025-11-05
**Última actualización:** 2025-11-05
**Estado:** En desarrollo

---

## 📋 Índice

1. [Visión General](#visión-general)
2. [Decisiones de Arquitectura (ADRs)](#decisiones-de-arquitectura-adrs)
3. [Arquitectura del Sistema](#arquitectura-del-sistema)
4. [Estructura de Directorios](#estructura-de-directorios)
5. [Mapeo de Migración v5 → v6](#mapeo-de-migración-v5--v6)
6. [Stack Tecnológico](#stack-tecnológico)
7. [Patrones y Principios](#patrones-y-principios)
8. [Sistema de Plugins](#sistema-de-plugins)
9. [Flujo de las 4 Fases](#flujo-de-las-4-fases)
10. [Referencias](#referencias)

---

## 🎯 Visión General

Sistema PJN v6 es una refactorización completa de Sistema_v5 que implementa **Clean Architecture** con un **sistema de plugins extensible** para facilitar el mantenimiento, testing y adición de nuevas funcionalidades.

### Objetivos Principales

1. **Extensibilidad**: Agregar nuevas funcionalidades sin modificar el core
2. **Mantenibilidad**: Código organizado con separación clara de responsabilidades
3. **Testabilidad**: Alta cobertura de tests (85%+) con mocks simples
4. **Escalabilidad**: Preparado para evolucionar a microservicios
5. **Multi-usuario**: Sistema de permisos y autenticación
6. **Multiplataforma**: Web UI moderna (reemplazando Tkinter)

### Flujo de Trabajo del Sistema

El sistema implementa **4 fases principales**:

1. **Fase 1 - Extracción**: Extrae listado completo de expedientes del PJN → `JSON "base"`
2. **Fase 2 - Filtrado**: Usuario selecciona expedientes a monitorear → `JSON "sistema"`
3. **Fase 3 - Workspace**: Genera estructura de directorios por expediente
4. **Fase 4 - Monitoreo**: Mantiene actualizado el workspace con cambios del portal

---

## 📜 Decisiones de Arquitectura (ADRs)

### ADR-001: Clean Architecture

**Fecha:** 2025-11-05
**Estado:** Aprobado
**Contexto:** Sistema_v5 tenía código entrelazado difícil de mantener y testear
**Decisión:** Adoptar Clean Architecture con capas concéntricas:
- **Core/Domain**: Lógica de negocio pura sin dependencias externas
- **Application**: Casos de uso y orquestación
- **Infrastructure**: Implementaciones concretas (DB, APIs, scraping)
- **Presentation**: Interfaces de usuario (REST API, Web UI, CLI, MCP)

**Consecuencias:**
- ✅ Mayor testabilidad (domain 100% testeable)
- ✅ Menor acoplamiento entre módulos
- ✅ Cambiar implementaciones sin afectar negocio
- ⚠️ Más archivos y directorios (mayor complejidad inicial)

**Alternativas consideradas:**
- MVC tradicional (rechazado: bajo testing, alto acoplamiento)
- Arquitectura de tres capas (rechazado: no separa dominio de aplicación)

---

### ADR-002: Sistema de Plugins

**Fecha:** 2025-11-05
**Estado:** Aprobado
**Contexto:** Se planean múltiples extensiones futuras (notificaciones, IA local, oficios digitales, etc.)
**Decisión:** Implementar arquitectura de plugins con `PluginInterface` y `PluginManager`

**Consecuencias:**
- ✅ Agregar funcionalidad sin modificar core
- ✅ Desarrollo paralelo de múltiples features
- ✅ Habilitar/deshabilitar funcionalidades dinámicamente
- ⚠️ Overhead inicial de crear el sistema de plugins

**Plugins planificados:**
- `notificaciones` - Email, Telegram, WhatsApp
- `oficios_digitales` - Envío automático de oficios al PJN
- `ia_local` - Integración con Ollama para análisis y RAG
- `pdf_processing` - OCR, extracción de entidades, búsqueda semántica
- `escritos_automaticos` - Generación de escritos con templates + IA
- `auth` - Autenticación y permisos multi-usuario

---

### ADR-003: Web UI en lugar de Tkinter

**Fecha:** 2025-11-05
**Estado:** Aprobado
**Contexto:** Tkinter presenta problemas en Windows y UI limitada
**Decisión:** Reemplazar Tkinter por Web UI (React/Vue.js + FastAPI)

**Consecuencias:**
- ✅ UI moderna y responsive
- ✅ Multiplataforma sin problemas
- ✅ Acceso remoto desde navegador
- ✅ Reutilizar API REST para múltiples clientes
- ⚠️ Requiere aprender JavaScript/frontend (si no se conoce)

**Alternativas consideradas:**
- PyQt6/PySide6 (rechazado: más complejo, menos flexible que web)
- Electron (considerado para futuro: app de escritorio empaquetada)

---

### ADR-004: JSON como Storage Principal

**Fecha:** 2025-11-05
**Estado:** Aprobado
**Contexto:** Sistema_v5 usa JSON con éxito, fácil de versionar y migrar
**Decisión:** Mantener JSON para almacenamiento de datos del sistema

**Consecuencias:**
- ✅ Fácil inspección y debug (archivos legibles)
- ✅ Versionable con Git
- ✅ Sin dependencias de DB externa
- ✅ Portabilidad total
- ⚠️ No óptimo para queries complejas
- ⚠️ Posible migración a SQLite/PostgreSQL en futuro

**Alternativas consideradas:**
- SQLite (considerado para futuro con muchos expedientes)
- PostgreSQL (overkill para uso actual)

---

### ADR-005: Playwright para Scraping

**Fecha:** 2025-11-05
**Estado:** Aprobado
**Contexto:** Sistema_v5 usa Playwright exitosamente
**Decisión:** Mantener Playwright para scraping del PJN

**Consecuencias:**
- ✅ Probado en producción
- ✅ Manejo de JavaScript/SPA
- ✅ Sesiones persistentes
- ⚠️ Más lento que requests + BeautifulSoup

**Alternativas consideradas:**
- Selenium (rechazado: más lento, API menos ergonómica)
- Requests + BeautifulSoup (rechazado: no maneja JavaScript)

---

### ADR-006: FastAPI como Framework Web

**Fecha:** 2025-11-05
**Estado:** Aprobado
**Contexto:** Necesitamos REST API moderna y performante
**Decisión:** Usar FastAPI para API REST y servidor web

**Consecuencias:**
- ✅ Async nativo (compatible con Playwright)
- ✅ Documentación automática (Swagger/OpenAPI)
- ✅ Validación con Pydantic
- ✅ Muy rápido
- ⚠️ Más moderno que Flask (menos ejemplos legacy)

**Alternativas consideradas:**
- Flask (rechazado: no async nativo, menos features)
- Django (rechazado: overkill, demasiado opinado)

---

### ADR-007: Ports & Adapters (Hexagonal Architecture)

**Fecha:** 2025-11-05
**Estado:** Aprobado
**Contexto:** Necesitamos inversión de dependencias para testear application sin infrastructure
**Decisión:** Usar patrón Ports & Adapters:
- **Ports** (interfaces en `application/ports/`)
- **Adapters** (implementaciones en `infrastructure/`)

**Consecuencias:**
- ✅ Application no depende de Infrastructure
- ✅ Fácil mockear en tests
- ✅ Cambiar implementaciones sin tocar application
- ⚠️ Más archivos (interfaces + implementaciones)

---

## 🏗️ Arquitectura del Sistema

### Diagrama de Capas

```
┌─────────────────────────────────────────────────────┐
│                 PRESENTATION LAYER                   │
│  ┌──────────┐  ┌──────────┐  ┌────────┐  ┌───────┐ │
│  │ REST API │  │ MCP Server│  │ Web UI │  │  CLI  │ │
│  └────┬─────┘  └────┬──────┘  └───┬────┘  └───┬───┘ │
└───────┼─────────────┼─────────────┼───────────┼─────┘
        │             │             │           │
┌───────┴─────────────┴─────────────┴───────────┴─────┐
│              APPLICATION LAYER                       │
│  ┌──────────────┐  ┌─────────────────────────────┐  │
│  │  Use Cases   │  │  Application Services       │  │
│  │ - Fase 1     │  │ - ExtractionService         │  │
│  │ - Fase 2     │  │ - FilteringService          │  │
│  │ - Fase 3     │  │ - MonitoringService         │  │
│  │ - Fase 4     │  │ - NotificationService       │  │
│  └──────┬───────┘  └─────────┬───────────────────┘  │
│         │                    │                       │
│  ┌──────┴────────────────────┴───────────────────┐  │
│  │           Ports (Interfaces)                   │  │
│  │  - ScrapingPort                                │  │
│  │  - StoragePort                                 │  │
│  │  - NotificationPort                            │  │
│  └──────────────────┬─────────────────────────────┘  │
└─────────────────────┼────────────────────────────────┘
                      │
┌─────────────────────┼────────────────────────────────┐
│         INFRASTRUCTURE LAYER (Adapters)              │
│  ┌──────────────┐  ┌────────────┐  ┌──────────────┐ │
│  │   Scraping   │  │   Storage  │  │Notification  │ │
│  │  (Playwright)│  │ (JSON/FS)  │  │   (Plyer)    │ │
│  └──────────────┘  └────────────┘  └──────────────┘ │
└──────────────────────────────────────────────────────┘
                      │
┌─────────────────────┼────────────────────────────────┐
│               DOMAIN LAYER (Core)                    │
│  ┌───────────────────────────────────────────────┐  │
│  │         Entities (Business Logic)             │  │
│  │  - ExpedienteResumen                          │  │
│  │  - Entrada                                    │  │
│  │  - Actuacion                                  │  │
│  │  - EstadoExpediente                           │  │
│  └───────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────┐  │
│  │         Utils (Pure Functions)                │  │
│  │  - normalizar_texto()                         │  │
│  │  - normalizar_fecha()                         │  │
│  │  - generar_hash()                             │  │
│  └───────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

### Flujo de Dependencias

```
Presentation → Application → Domain
Infrastructure → Application
Infrastructure → Domain (solo para usar entidades)

❌ Domain NO debe importar nada de Infrastructure
❌ Domain NO debe importar nada de Application
❌ Domain NO debe importar nada de Presentation
✅ Todos pueden importar de Domain
```

---

## 📂 Estructura de Directorios

```
Sistema_v6/
│
├── core/                           # Domain Layer
│   ├── domain/
│   │   ├── entities/              # Modelos de negocio (ExpedienteResumen, Entrada, Actuacion)
│   │   ├── value_objects/         # Value objects (NumeroExpediente)
│   │   ├── utils/                 # Funciones puras (normalizar_texto, fechas, hashing)
│   │   ├── exceptions/            # Excepciones de dominio
│   │   └── validators/            # Validadores puros
│   └── plugins/                   # Sistema de plugins (PluginInterface, PluginManager)
│
├── application/                    # Application Layer
│   ├── use_cases/                 # Casos de uso (las 4 fases)
│   │   ├── fase1_extraer_listado.py
│   │   ├── fase2_filtrar_expedientes.py
│   │   ├── fase3_crear_workspace.py
│   │   └── fase4_monitorear.py
│   ├── services/                  # Application services
│   │   ├── extraction_service.py
│   │   ├── filtering_service.py
│   │   ├── monitoring_service.py
│   │   └── notification_service.py
│   ├── dto/                       # Data Transfer Objects
│   │   ├── extraction_request.py
│   │   └── monitoring_response.py
│   └── ports/                     # Interfaces (para inversión de dependencias)
│       ├── scraping_port.py
│       ├── storage_port.py
│       └── notification_port.py
│
├── infrastructure/                 # Infrastructure Layer
│   ├── scraping/                  # Web scraping con Playwright
│   │   ├── playwright/
│   │   │   ├── session_manager.py
│   │   │   ├── authenticator.py
│   │   │   └── browser_factory.py
│   │   ├── extractors/
│   │   │   ├── expediente_extractor.py
│   │   │   ├── actuacion_extractor.py
│   │   │   └── entrada_extractor.py
│   │   ├── pagination/
│   │   │   └── pagination_strategy.py
│   │   └── selectors/
│   │       └── css_selectors.py
│   │
│   ├── parsers/                   # HTML → Domain models
│   │   ├── expediente_parser.py
│   │   ├── actuacion_parser.py
│   │   └── entrada_parser.py
│   │
│   ├── persistence/               # Storage implementations
│   │   ├── json/                  # JSON repositories
│   │   │   ├── expediente_json_repository.py
│   │   │   ├── actuacion_json_repository.py
│   │   │   └── estado_json_repository.py
│   │   ├── filesystem/            # Workspace management
│   │   │   ├── workspace_manager.py
│   │   │   ├── manifest_manager.py
│   │   │   └── directory_structure.py
│   │   └── cache/
│   │       └── memory_cache.py
│   │
│   ├── config/                    # Configuración
│   │   ├── system_config.py
│   │   ├── monitor_config.py
│   │   └── config_loader.py
│   │
│   ├── monitoring/                # Monitoreo
│   │   ├── detector.py
│   │   ├── circuit_breaker.py
│   │   └── health_checker.py
│   │
│   ├── notification/              # Notificaciones
│   │   ├── plyer_notifier.py
│   │   └── notification_formatter.py
│   │
│   ├── scheduling/                # Programación de tareas
│   │   ├── apscheduler_adapter.py
│   │   └── job_definitions.py
│   │
│   ├── logging/                   # Logging
│   │   ├── logger_factory.py
│   │   └── formatters.py
│   │
│   └── pdf/                       # Procesamiento de PDFs
│       └── pdf_extractor.py
│
├── presentation/                   # Presentation Layer
│   ├── api/
│   │   ├── rest/                  # REST API (FastAPI)
│   │   │   ├── main.py
│   │   │   ├── routers/
│   │   │   │   ├── expedientes.py
│   │   │   │   ├── actuaciones.py
│   │   │   │   ├── monitoring.py
│   │   │   │   └── config.py
│   │   │   ├── schemas/           # Pydantic schemas
│   │   │   │   └── api_models.py
│   │   │   ├── middleware/
│   │   │   │   ├── auth.py
│   │   │   │   └── error_handler.py
│   │   │   └── dependencies.py
│   │   │
│   │   └── mcp/                   # MCP Server
│   │       ├── server.py
│   │       ├── tools/
│   │       │   ├── expedientes_tool.py
│   │       │   ├── actuaciones_tool.py
│   │       │   ├── estadisticas_tool.py
│   │       │   └── pdf_tool.py
│   │       ├── resources/
│   │       │   └── resource_handlers.py
│   │       ├── prompts/
│   │       │   └── prompt_templates.py
│   │       └── adapters/
│   │           └── data_loader.py
│   │
│   ├── cli/                       # Command Line Interface
│   │   ├── commands/
│   │   │   ├── extraer.py
│   │   │   ├── monitorear.py
│   │   │   ├── config.py
│   │   │   └── workspace.py
│   │   └── main.py
│   │
│   └── web/                       # Web UI
│       ├── frontend/              # React/Vue.js frontend
│       │   ├── src/
│       │   │   ├── components/
│       │   │   ├── pages/
│       │   │   ├── api/
│       │   │   └── App.jsx
│       │   └── public/
│       ├── templates/             # SSR templates (opcional)
│       └── static/                # Assets estáticos
│
├── plugins/                        # Plugins extensibles
│   ├── notificaciones/            # Email, Telegram, WhatsApp
│   ├── oficios_digitales/         # Envío de oficios al PJN
│   ├── ia_local/                  # Integración con Ollama (RAG, análisis)
│   ├── pdf_processing/            # OCR, extracción de entidades, búsqueda
│   ├── escritos_automaticos/      # Generación de escritos con IA
│   └── auth/                      # Autenticación multi-usuario
│
├── tests/                          # Tests
│   ├── unit/                      # Tests unitarios (por capa)
│   │   ├── core/
│   │   ├── application/
│   │   ├── infrastructure/
│   │   └── presentation/
│   ├── integration/               # Tests de integración
│   └── e2e/                       # Tests end-to-end
│
├── scripts/                        # Scripts de utilidad
│   ├── migrar_datos_v5_to_v6.py
│   ├── inicializar_sistema.py
│   └── backup_workspace.py
│
├── config/                         # Archivos de configuración
│   ├── system.json
│   ├── monitoring.json
│   ├── plugins.json
│   └── mcp_config.json
│
├── data/                           # Datos del sistema
│   ├── expedientes/               # Workspace de expedientes
│   ├── estados/                   # Estados de usuario
│   └── historial/                 # Historial del monitor
│
├── docs/                           # Documentación
│   ├── V6_ARCHITECTURE.md         # Este archivo
│   ├── V6_ROADMAP.md              # Progreso y tareas
│   ├── V6_CONTEXT.md              # Contexto para agente
│   ├── USER_GUIDE.md
│   ├── API_REFERENCE.md
│   └── DEVELOPER_GUIDE.md
│
├── .gitignore
├── .env.example
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── pytest.ini
├── mypy.ini
└── README.md
```

---

## 🔄 Mapeo de Migración v5 → v6

### Modelos de Dominio

| Sistema_v5 | Sistema_v6 | Cambios |
|------------|------------|---------|
| `pjn/models/expediente.py` | `core/domain/entities/expediente.py` | Ninguno (ya está bien diseñado) |
| `pjn/models/entrada.py` | `core/domain/entities/entrada.py` | Ninguno |
| `pjn/models/actuacion.py` | `core/domain/entities/actuacion.py` | Ninguno |
| `pjn/models/estado_expediente.py` | `core/domain/entities/estado.py` | Renombrado |

### Funciones Puras (Utils)

| Sistema_v5 | Sistema_v6 | Función |
|------------|------------|---------|
| `pjn/scraping/base.py::normalizar_texto()` | `core/domain/utils/text.py::normalizar_texto()` | Mover |
| `pjn/scraping/base.py::limpiar_texto()` | `core/domain/utils/text.py::limpiar_texto()` | Mover |
| `pjn/scraping/base.py::normalizar_fecha()` | `core/domain/utils/dates.py::normalizar_fecha()` | Mover |
| `pjn/scraping/base.py::generar_hash_identificador()` | `core/domain/utils/hashing.py::generar_hash()` | Mover + renombrar |
| `pjn/scraping/base.py::normalizar_numero_expediente()` | `core/domain/value_objects/numero_expediente.py::normalizar()` | Mover a value object |
| `pjn/scraping/base.py::descomponer_numero_expediente()` | `core/domain/value_objects/numero_expediente.py::descomponer()` | Mover a value object |

### Scraping

| Sistema_v5 | Sistema_v6 | Cambios |
|------------|------------|---------|
| `pjn/scraping/session_manager.py` | `infrastructure/scraping/playwright/session_manager.py` | Ninguno |
| `pjn/scraping/base.py` (autenticación) | `infrastructure/scraping/playwright/authenticator.py` | Extraer solo auth |
| `pjn/scraping/expedientes.py` | `infrastructure/scraping/extractors/expediente_extractor.py` | Implementar ScrapingPort |
| `pjn/scraping/actuaciones.py` | `infrastructure/scraping/extractors/actuacion_extractor.py` | Implementar ScrapingPort |
| `pjn/scraping/entradas.py` | `infrastructure/scraping/extractors/entrada_extractor.py` | Implementar ScrapingPort |
| `pjn/scraping/pagination.py` | `infrastructure/scraping/pagination/pagination_strategy.py` | Ninguno |
| `pjn/selectores.py` | `infrastructure/scraping/selectors/css_selectors.py` | Ninguno |

### Parsers

| Sistema_v5 | Sistema_v6 | Cambios |
|------------|------------|---------|
| `pjn/parsers/expedientes_parser.py` | `infrastructure/parsers/expediente_parser.py` | Ninguno |
| `pjn/parsers/actuaciones_parser.py` | `infrastructure/parsers/actuacion_parser.py` | Ninguno |
| `pjn/parsers/entradas_parser.py` | `infrastructure/parsers/entrada_parser.py` | Ninguno |

### Persistence

| Sistema_v5 | Sistema_v6 | Cambios |
|------------|------------|---------|
| `pjn/persistence/actuaciones.py` | `infrastructure/persistence/json/actuacion_json_repository.py` | Implementar StoragePort |
| `gestor_directorios/expedientes.py` | `infrastructure/persistence/filesystem/workspace_manager.py` | Implementar StoragePort |
| `gestor_directorios/archivos_usuario.py` | `infrastructure/persistence/filesystem/user_files_manager.py` | Implementar StoragePort |
| `configuracion/estados/estados_manager.py` | `infrastructure/persistence/json/estado_json_repository.py` | Implementar StoragePort |

### Configuration

| Sistema_v5 | Sistema_v6 | Cambios |
|------------|------------|---------|
| `configuracion/core/system_config.py` | `infrastructure/config/system_config.py` | Ninguno |
| `configuracion/core/scraping_config.py` | `infrastructure/config/scraping_config.py` | Ninguno |
| `configuracion/monitor/config.py` | `infrastructure/config/monitor_config.py` | Ninguno |

### Monitoring

| Sistema_v5 | Sistema_v6 | Cambios |
|------------|------------|---------|
| `pjn/monitor/core.py` | `application/services/monitoring_service.py` | Refactorizar (separar lógica) |
| `pjn/monitor/detector.py` | `infrastructure/monitoring/detector.py` | Ninguno |
| `pjn/monitor/circuit_breaker.py` | `infrastructure/monitoring/circuit_breaker.py` | Ninguno |
| `pjn/monitor/storage.py` | `infrastructure/persistence/json/historial_repository.py` | Implementar StoragePort |
| `pjn/monitor/notifier.py` | `infrastructure/notification/plyer_notifier.py` | Implementar NotificationPort |
| `pjn/monitor/scheduler.py` | `infrastructure/scheduling/apscheduler_adapter.py` | Ninguno |

### Services & Use Cases

| Sistema_v5 | Sistema_v6 | Cambios |
|------------|------------|---------|
| `pjn/services/actuaciones.py` | `application/services/actuacion_service.py` | Refactorizar |
| `extractor_inicial/services/listado_expedientes.py` | `application/use_cases/fase1_extraer_listado.py` | Refactorizar |
| `extractor_inicial/services/procesamiento.py` | `application/use_cases/fase4_extraer_completo.py` | Refactorizar |
| `extractor_inicial/filtrador.py` | `application/services/filtering_service.py` | Refactorizar |

### Presentation

| Sistema_v5 | Sistema_v6 | Cambios |
|------------|------------|---------|
| `mcp_server/` | `presentation/api/mcp/` | Reorganizar |
| `bin/ejecutar_extraccion.py` | `presentation/cli/commands/extraer.py` | Refactorizar |
| `bin/ejecutar_monitor.py` | `presentation/cli/commands/monitorear.py` | Refactorizar |
| `extractor_inicial/ui/` | **ELIMINAR** (reemplazado por Web UI) | Nueva implementación |
| `gui/` | **ELIMINAR** (reemplazado por Web UI) | Nueva implementación |

### Excepciones

| Sistema_v5 | Sistema_v6 | Cambios |
|------------|------------|---------|
| `pjn/exceptions.py` | `core/domain/exceptions/domain_exceptions.py` | Ninguno |

---

## 🛠️ Stack Tecnológico

### Backend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Python** | 3.10+ | Lenguaje principal |
| **FastAPI** | 0.104+ | REST API y servidor web |
| **Playwright** | 1.50+ | Web scraping |
| **Pydantic** | 2.0+ | Validación de datos |
| **APScheduler** | 3.11+ | Programación de tareas |
| **Plyer** | Latest | Notificaciones del sistema |

### Storage

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **JSON** | Native | Almacenamiento principal |
| **SQLite** | Native | (Futuro) Base de datos relacional |
| **Redis** | 7.0+ | (Futuro) Cache y queue |

### Frontend

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **React** o **Vue.js** | 18+ / 3+ | Framework UI |
| **Tailwind CSS** | 3.0+ | Estilos |
| **Axios** | 1.6+ | Cliente HTTP |
| **React Query** o **Pinia** | Latest | State management |
| **Vite** | 5.0+ | Build tool |

### IA Local (Plugins)

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Ollama** | Latest | LLM local (llama3.1, mistral) |
| **ChromaDB** | Latest | Vector database |
| **sentence-transformers** | Latest | Embeddings |
| **LangChain** | Latest | RAG orchestration |

### Testing

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **pytest** | 8.0+ | Framework de testing |
| **pytest-asyncio** | Latest | Tests async |
| **pytest-cov** | Latest | Cobertura de código |
| **unittest.mock** | Native | Mocking |

### Code Quality

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **black** | Latest | Formateo de código |
| **ruff** | Latest | Linting |
| **mypy** | Latest | Type checking |
| **isort** | Latest | Ordenar imports |

### DevOps

| Tecnología | Versión | Propósito |
|------------|---------|-----------|
| **Docker** | Latest | Containerización |
| **Docker Compose** | Latest | Orquestación |
| **Nginx** | Latest | Reverse proxy |
| **GitHub Actions** | N/A | CI/CD |

---

## 📐 Patrones y Principios

### SOLID Principles

1. **Single Responsibility Principle (SRP)**
   - Cada módulo tiene una única responsabilidad
   - Ejemplo: `expediente_extractor.py` solo extrae expedientes, no persiste

2. **Open/Closed Principle (OCP)**
   - Abierto a extensión, cerrado a modificación
   - Ejemplo: Agregar nuevo plugin sin modificar PluginManager

3. **Liskov Substitution Principle (LSP)**
   - Las implementaciones pueden sustituir sus interfaces
   - Ejemplo: Cualquier implementación de `StoragePort` es intercambiable

4. **Interface Segregation Principle (ISP)**
   - Interfaces específicas en lugar de generales
   - Ejemplo: `ScrapingPort` separado de `StoragePort`

5. **Dependency Inversion Principle (DIP)**
   - Depender de abstracciones, no de concreciones
   - Ejemplo: Application depende de `StoragePort`, no de `JSONRepository`

### Design Patterns Aplicados

1. **Repository Pattern**
   - `ExpedienteRepository`, `ActuacionRepository`
   - Abstrae persistencia

2. **Strategy Pattern**
   - `PaginationStrategy`
   - Diferentes estrategias de paginación

3. **Factory Pattern**
   - `BrowserFactory`
   - Creación de instancias de navegador

4. **Observer Pattern**
   - Callbacks en extracción
   - Notificaciones de cambios

5. **Circuit Breaker Pattern**
   - `CircuitBreaker`
   - Resiliencia ante fallos

6. **Singleton Pattern**
   - `PluginManager`
   - Una única instancia global

### Clean Code Principles

1. **DRY (Don't Repeat Yourself)**
   - Funciones utilitarias compartidas en `core/domain/utils/`

2. **YAGNI (You Aren't Gonna Need It)**
   - No agregar features hasta que sean necesarias

3. **KISS (Keep It Simple, Stupid)**
   - Soluciones simples antes que complejas

4. **Separation of Concerns**
   - Cada capa con su responsabilidad

5. **Explicit is Better Than Implicit**
   - Type hints en todo el código
   - Nombres descriptivos

---

## 🔌 Sistema de Plugins

### Interface de Plugin

```python
# core/plugins/plugin_interface.py
from abc import ABC, abstractmethod

class PluginInterface(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Nombre único del plugin"""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Versión del plugin"""
        pass

    @property
    def dependencies(self) -> list[str]:
        """Plugins de los que depende"""
        return []

    @abstractmethod
    async def initialize(self, config: dict):
        """Inicializar plugin"""
        pass

    @abstractmethod
    async def shutdown(self):
        """Cleanup al apagar"""
        pass

    def register_routes(self, router):
        """Registrar endpoints API"""
        pass
```

### Plugin Manager

```python
# core/plugins/plugin_manager.py
class PluginManager:
    def __init__(self):
        self.plugins: dict[str, PluginInterface] = {}

    async def load_plugin(self, plugin_class, config):
        plugin = plugin_class()

        # Verificar dependencias
        for dep in plugin.dependencies:
            if dep not in self.plugins:
                raise PluginError(f"Falta dependencia: {dep}")

        await plugin.initialize(config)
        self.plugins[plugin.name] = plugin
```

### Plugins Planificados

1. **notificaciones**
   - Email, Telegram, WhatsApp, Discord
   - Configuración por usuario
   - Horarios personalizados

2. **oficios_digitales**
   - Templates de oficios
   - Firma digital
   - Envío automático al PJN

3. **ia_local**
   - Integración con Ollama
   - RAG sobre expedientes
   - Análisis automático

4. **pdf_processing**
   - OCR con Tesseract
   - Extracción de entidades
   - Búsqueda semántica

5. **escritos_automaticos**
   - Generación con templates + IA
   - Sugerencias estratégicas

6. **auth**
   - Autenticación JWT
   - Sistema de permisos (RBAC)
   - Multi-usuario

---

## 🔄 Flujo de las 4 Fases

### Fase 1: Extracción del Listado

```
[Usuario]
   ↓ (GET /api/v1/expedientes/extraer)
[REST API Router]
   ↓
[Use Case: Fase1ExtraerListado]
   ↓
[ExtractionService]
   ↓ (usa)
[ScrapingPort] ← implementado por → [ExpedienteExtractor]
   ↓
[Playwright] → PJN Portal
   ↓
[ExpedienteParser] → [ExpedienteResumen]
   ↓
[StoragePort] ← implementado por → [JSONRepository]
   ↓
[data/listado_base.json]
```

### Fase 2: Filtrado

```
[Usuario en Web UI]
   ↓ (POST /api/v1/expedientes/filtrar)
[REST API Router]
   ↓
[Use Case: Fase2FiltrarExpedientes]
   ↓
[FilteringService]
   ↓
[FiltradorExpedientes] (apply filters)
   ↓
[EstadosManager] (assign states)
   ↓
[StoragePort] → [JSONRepository]
   ↓
[data/listado_sistema.json]
```

### Fase 3: Crear Workspace

```
[Sistema automático o manual]
   ↓
[Use Case: Fase3CrearWorkspace]
   ↓
[WorkspaceManager]
   ↓
[Create directories per expediente]
   ↓
[Generate manifest.json]
   ↓
[workspace/<numero_expediente>/]
   ├── manifest.json
   ├── actuaciones/
   ├── documentos/
   └── usuario/
```

### Fase 4: Monitoreo

```
[APScheduler] (cada N minutos)
   ↓
[Use Case: Fase4Monitorear]
   ↓
[MonitoringService]
   ↓
[DetectorCambios] (compare hashes)
   ↓
[ScrapingPort] → [ActuacionExtractor]
   ↓
[Playwright] → PJN Portal
   ↓
[StoragePort] → Update workspace
   ↓
[NotificationPort] → [PlyerNotifier]
   ↓
[System notification]
```

---

## 📚 Referencias

### Documentación Interna

- `V6_ROADMAP.md` - Estado y progreso del proyecto
- `V6_CONTEXT.md` - Contexto para agente (última sesión)
- `USER_GUIDE.md` - Guía de usuario
- `API_REFERENCE.md` - Referencia de API REST
- `DEVELOPER_GUIDE.md` - Guía para desarrolladores

### Recursos Externos

- [Clean Architecture (Robert C. Martin)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Hexagonal Architecture](https://alistair.cockburn.us/hexagonal-architecture/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Playwright Documentation](https://playwright.dev/python/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)

### Libros Recomendados

- **Clean Architecture** - Robert C. Martin
- **Domain-Driven Design** - Eric Evans
- **Patterns of Enterprise Application Architecture** - Martin Fowler
- **Refactoring** - Martin Fowler

---

## 🔄 Historial de Cambios

### v6.0.0 (2025-11-05)
- ✅ Documento inicial de arquitectura
- ✅ Definición de Clean Architecture
- ✅ Sistema de plugins
- ✅ Mapeo completo v5 → v6
- ✅ Stack tecnológico definido

---

**Última actualización:** 2025-11-05
**Mantenido por:** Equipo de desarrollo Sistema PJN
**Estado:** En desarrollo activo
