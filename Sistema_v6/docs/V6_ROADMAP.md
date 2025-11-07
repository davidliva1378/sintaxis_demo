# Sistema PJN v6 - Roadmap y Progreso

**Versión:** 6.0.0
**Fecha de inicio:** 2025-11-05
**Última actualización:** 2025-11-05
**Estado general:** 🟢 En desarrollo - Fase 0

---

## 📊 Estado General del Proyecto

### Progreso Global

```
Fase 0: Setup Inicial         [████████████████░░░░] 80% (EN PROGRESO)
Fase 1: Domain Layer          [░░░░░░░░░░░░░░░░░░░░]  0% (PENDIENTE)
Fase 2: Application Layer     [░░░░░░░░░░░░░░░░░░░░]  0% (PENDIENTE)
Fase 3: Infrastructure Layer  [░░░░░░░░░░░░░░░░░░░░]  0% (PENDIENTE)
Fase 4: Presentation Layer    [░░░░░░░░░░░░░░░░░░░░]  0% (PENDIENTE)
Fase 5: Plugin System         [░░░░░░░░░░░░░░░░░░░░]  0% (PENDIENTE)
Fase 6: Migración de Datos    [░░░░░░░░░░░░░░░░░░░░]  0% (PENDIENTE)
Fase 7: Testing & Docs        [░░░░░░░░░░░░░░░░░░░░]  0% (PENDIENTE)
─────────────────────────────────────────────────────────
PROGRESO TOTAL:               [██░░░░░░░░░░░░░░░░░░]  8%
```

### Información de Branches

```
Branch actual:    v6-refactorization
Branch base:      producción_v5.1.1 (preservada intacta)
Último commit:    [pendiente]
```

### Tiempo Estimado

- **Tiempo transcurrido:** 0 días
- **Tiempo estimado restante:** 27-38 días
- **Fecha estimada de completación:** 2025-12-10 / 2025-12-20

---

## 📋 FASE 0: Setup Inicial (1-2 días)

**Estado:** 🟡 EN PROGRESO (80%)
**Branch:** v6-refactorization
**Inicio:** 2025-11-05
**Estimación:** 1-2 días

### Checklist

#### 0.1 Git Branch Strategy
- [x] Verificar estado de git (clean)
- [x] Crear branch `v6-refactorization` desde `producción_v5.1.1`
- [ ] Configurar `.gitignore`
- [ ] Hacer commit inicial con estructura base

#### 0.2 Estructura de Directorios
- [x] Crear directorios principales (core, application, infrastructure, presentation)
- [x] Crear subdirectorios de domain (entities, value_objects, utils, exceptions)
- [x] Crear subdirectorios de application (use_cases, services, dto, ports)
- [x] Crear subdirectorios de infrastructure (scraping, parsers, persistence, etc.)
- [x] Crear subdirectorios de presentation (api, cli, web)
- [x] Crear directorio de plugins
- [x] Crear directorios de tests (unit, integration, e2e)
- [x] Crear directorios auxiliares (scripts, config, docs, data)

#### 0.3 Documentación de Contexto
- [x] Crear `docs/V6_ARCHITECTURE.md` con arquitectura completa
- [x] Crear `docs/V6_ROADMAP.md` (este archivo)
- [ ] Crear `docs/V6_CONTEXT.md` para continuidad del agente

#### 0.4 Configuración de Entorno
- [ ] Crear `pyproject.toml` con metadata del proyecto
- [ ] Crear `requirements.txt` con dependencias principales
- [ ] Crear `requirements-dev.txt` con dependencias de desarrollo
- [ ] Crear `.env.example` con variables de entorno
- [ ] Configurar entorno virtual (instrucciones en README)

#### 0.5 Archivos de Configuración
- [ ] Crear `pytest.ini` para configuración de tests
- [ ] Crear `mypy.ini` para type checking
- [ ] Crear `.gitignore` completo
- [ ] Crear `README.md` inicial

#### 0.6 Crear __init__.py
- [ ] Crear `__init__.py` en todos los directorios Python
- [ ] Agregar docstrings a los __init__.py principales

### Bloqueadores

- ⚠️ Ninguno identificado

### Notas

- Se decidió usar Web UI (React/Vue.js) en lugar de Tkinter por problemas en Windows
- Arquitectura de plugins para máxima extensibilidad
- Git branch `producción_v5.1.1` preservada intacta como fallback

### Próximos Pasos

1. Completar `docs/V6_CONTEXT.md`
2. Crear archivos de configuración base
3. Hacer commit inicial
4. Comenzar Fase 1: Domain Layer

---

## 📦 FASE 1: Domain Layer (3-4 días)

**Estado:** 🔴 PENDIENTE
**Branch:** v6-phase1-domain (a crear)
**Estimación:** 3-4 días
**Dependencias:** Fase 0 completa

### Objetivos

1. Migrar modelos de dominio de v5 → v6
2. Extraer funciones puras a utils/
3. Crear value objects
4. Implementar excepciones de dominio
5. Tests unitarios con 90%+ coverage
6. Validar que domain no tiene dependencias externas

### Checklist

#### 1.1 Modelos de Dominio (Entities)
- [ ] Migrar `ExpedienteResumen` → `core/domain/entities/expediente.py`
- [ ] Migrar `Entrada` → `core/domain/entities/entrada.py`
- [ ] Migrar `Actuacion` → `core/domain/entities/actuacion.py`
- [ ] Migrar `EstadoExpediente` → `core/domain/entities/estado.py`
- [ ] Verificar que todos usan `frozen=True` (inmutabilidad)
- [ ] Verificar `to_dict()` y `from_dict()` en todos

#### 1.2 Value Objects
- [ ] Crear `NumeroExpediente` value object
  - `normalizar()` (de `base.py`)
  - `descomponer()` (de `base.py`)
  - Validación en constructor
- [ ] Crear `FechaActuacion` value object (si necesario)

#### 1.3 Utils (Funciones Puras)
- [ ] Extraer `normalizar_texto()` → `core/domain/utils/text.py`
- [ ] Extraer `limpiar_texto()` → `core/domain/utils/text.py`
- [ ] Extraer `normalizar_fecha()` → `core/domain/utils/dates.py`
- [ ] Extraer `generar_hash_identificador()` → `core/domain/utils/hashing.py`
- [ ] Verificar que NINGUNA función tiene side effects

#### 1.4 Excepciones de Dominio
- [ ] Migrar `pjn/exceptions.py` → `core/domain/exceptions/domain_exceptions.py`
- [ ] Verificar jerarquía: `DomainException` → Subclases

#### 1.5 Validators
- [ ] Crear `core/domain/validators/expediente_validator.py` (si necesario)
- [ ] Crear validators para fechas, números, etc. (si necesario)

#### 1.6 Tests Unitarios
- [ ] `tests/unit/core/domain/entities/test_expediente.py`
- [ ] `tests/unit/core/domain/entities/test_entrada.py`
- [ ] `tests/unit/core/domain/entities/test_actuacion.py`
- [ ] `tests/unit/core/domain/entities/test_estado.py`
- [ ] `tests/unit/core/domain/utils/test_text.py`
- [ ] `tests/unit/core/domain/utils/test_dates.py`
- [ ] `tests/unit/core/domain/utils/test_hashing.py`
- [ ] `tests/unit/core/domain/value_objects/test_numero_expediente.py`
- [ ] Verificar coverage >= 90%

#### 1.7 Validación Final
- [ ] Ejecutar `pytest tests/unit/core/domain/` (todo verde)
- [ ] Ejecutar `mypy core/domain/` (sin errores)
- [ ] Ejecutar `black core/domain/` (formateado)
- [ ] Verificar que domain NO importa nada de infrastructure
- [ ] Verificar que domain NO importa nada de application
- [ ] Verificar que domain NO importa nada de presentation

### Bloqueadores Potenciales

- ⚠️ Imports circulares entre models y utils
  - **Solución**: Mover funciones puras a utils/ primero

### Métricas de Éxito

- ✅ Todos los modelos migrados
- ✅ Tests con 90%+ coverage
- ✅ Cero dependencias externas en domain/
- ✅ Type hints completos
- ✅ Documentación actualizada

---

## 🎯 FASE 2: Application Layer (4-5 días)

**Estado:** 🔴 PENDIENTE
**Branch:** v6-phase2-application (a crear)
**Estimación:** 4-5 días
**Dependencias:** Fase 1 completa

### Objetivos

1. Definir Ports (interfaces) para inversión de dependencias
2. Implementar 4 Use Cases principales (las 4 fases)
3. Crear Application Services
4. Definir DTOs
5. Tests unitarios con 85%+ coverage

### Checklist

#### 2.1 Ports (Interfaces)
- [ ] Crear `application/ports/scraping_port.py`
  - `ScrapingPort` (interface)
  - Métodos: `extraer_expedientes()`, `extraer_actuaciones()`, `extraer_entradas()`
- [ ] Crear `application/ports/storage_port.py`
  - `StoragePort` (interface)
  - Métodos: `guardar()`, `cargar()`, `listar()`, `eliminar()`
- [ ] Crear `application/ports/notification_port.py`
  - `NotificationPort` (interface)
  - Métodos: `notificar()`, `notificar_cambio()`, `notificar_error()`

#### 2.2 Use Cases (Las 4 Fases)
- [ ] Crear `application/use_cases/fase1_extraer_listado.py`
  - `Fase1ExtraerListadoUseCase`
  - Orquesta: scraping → parsing → storage
- [ ] Crear `application/use_cases/fase2_filtrar_expedientes.py`
  - `Fase2FiltrarExpedientesUseCase`
  - Orquesta: load → filter → assign states → storage
- [ ] Crear `application/use_cases/fase3_crear_workspace.py`
  - `Fase3CrearWorkspaceUseCase`
  - Orquesta: crear directorios → manifest → init historial
- [ ] Crear `application/use_cases/fase4_monitorear.py`
  - `Fase4MonitorearUseCase`
  - Orquesta: scrape → detect changes → update → notify

#### 2.3 Application Services
- [ ] Crear `application/services/extraction_service.py`
  - Lógica de extracción reutilizable
- [ ] Crear `application/services/filtering_service.py`
  - Lógica de filtrado avanzado
- [ ] Crear `application/services/monitoring_service.py`
  - Lógica de monitoreo
- [ ] Crear `application/services/notification_service.py`
  - Lógica de notificaciones

#### 2.4 DTOs (Data Transfer Objects)
- [ ] Crear `application/dto/extraction_request.py`
  - `ExtractionRequest`, `ExtractionResponse`
- [ ] Crear `application/dto/filtering_request.py`
  - `FilteringRequest`, `FilteringResponse`
- [ ] Crear `application/dto/monitoring_request.py`
  - `MonitoringRequest`, `MonitoringResponse`

#### 2.5 Tests Unitarios
- [ ] Tests para cada Use Case (con mocks de ports)
- [ ] Tests para cada Service
- [ ] Verificar coverage >= 85%

#### 2.6 Validación Final
- [ ] Todos los Use Cases testeados
- [ ] Application NO depende de implementaciones concretas
- [ ] Solo depende de Ports y Domain
- [ ] Type hints completos

### Bloqueadores Potenciales

- ⚠️ Definir firmas de Ports requiere conocer bien infrastructure
  - **Solución**: Revisar código v5 para entender contratos

### Métricas de Éxito

- ✅ 4 Use Cases implementados y testeados
- ✅ Ports bien definidos
- ✅ Tests con 85%+ coverage
- ✅ Inversión de dependencias correcta

---

## 🔧 FASE 3: Infrastructure Layer (7-10 días)

**Estado:** 🔴 PENDIENTE
**Branch:** v6-phase3-infrastructure (a crear)
**Estimación:** 7-10 días
**Dependencias:** Fase 2 completa

### Objetivos

1. Migrar scraping (Playwright)
2. Migrar parsers
3. Implementar repositories (JSON, filesystem)
4. Migrar configuración
5. Migrar monitoring
6. Implementar adapters para todos los Ports
7. Tests de integración

### Checklist

#### 3.1 Scraping
- [ ] Migrar `session_manager.py` → `infrastructure/scraping/playwright/`
- [ ] Migrar auth → `infrastructure/scraping/playwright/authenticator.py`
- [ ] Migrar `expedientes.py` → `infrastructure/scraping/extractors/expediente_extractor.py`
- [ ] Migrar `actuaciones.py` → `infrastructure/scraping/extractors/actuacion_extractor.py`
- [ ] Migrar `entradas.py` → `infrastructure/scraping/extractors/entrada_extractor.py`
- [ ] Migrar `pagination.py` → `infrastructure/scraping/pagination/`
- [ ] Migrar `selectores.py` → `infrastructure/scraping/selectors/`
- [ ] Implementar `ScrapingPort` en todos los extractors

#### 3.2 Parsers
- [ ] Migrar `expedientes_parser.py` → `infrastructure/parsers/`
- [ ] Migrar `actuaciones_parser.py` → `infrastructure/parsers/`
- [ ] Migrar `entradas_parser.py` → `infrastructure/parsers/`

#### 3.3 Persistence
- [ ] Implementar `ExpedienteJSONRepository` (implementa `StoragePort`)
- [ ] Implementar `ActuacionJSONRepository`
- [ ] Implementar `EstadoJSONRepository`
- [ ] Migrar `gestor_directorios/` → `infrastructure/persistence/filesystem/`
- [ ] Implementar `WorkspaceManager`
- [ ] Implementar `ManifestManager`

#### 3.4 Configuration
- [ ] Migrar `system_config.py` → `infrastructure/config/`
- [ ] Migrar `scraping_config.py` → `infrastructure/config/`
- [ ] Migrar `monitor_config.py` → `infrastructure/config/`
- [ ] Crear `ConfigLoader`

#### 3.5 Monitoring
- [ ] Migrar `detector.py` → `infrastructure/monitoring/`
- [ ] Migrar `circuit_breaker.py` → `infrastructure/monitoring/`
- [ ] Implementar `HealthChecker`

#### 3.6 Notification
- [ ] Migrar `notifier.py` → `infrastructure/notification/plyer_notifier.py`
- [ ] Implementar `NotificationPort`

#### 3.7 Scheduling
- [ ] Migrar `scheduler.py` → `infrastructure/scheduling/apscheduler_adapter.py`
- [ ] Implementar jobs definitions

#### 3.8 Logging
- [ ] Migrar `logging.py` → `infrastructure/logging/logger_factory.py`

#### 3.9 Tests de Integración
- [ ] Tests para scraping (mocks del portal)
- [ ] Tests para repositories (archivos reales)
- [ ] Tests para workflow completo de extracción

### Bloqueadores Potenciales

- ⚠️ Playwright requiere browser instalado
  - **Solución**: Incluir en setup instructions

### Métricas de Éxito

- ✅ Todos los Ports implementados
- ✅ Tests de integración pasando
- ✅ Migración completa de v5

---

## 🖥️ FASE 4: Presentation Layer (5-7 días)

**Estado:** 🔴 PENDIENTE
**Branch:** v6-phase4-presentation (a crear)
**Estimación:** 5-7 días
**Dependencias:** Fase 3 completa

### Objetivos

1. Implementar REST API (FastAPI)
2. Migrar MCP Server
3. Implementar Web UI (React/Vue.js)
4. Migrar CLI
5. Tests E2E

### Checklist

#### 4.1 REST API (FastAPI)
- [ ] Crear `presentation/api/rest/main.py` (app principal)
- [ ] Implementar router de expedientes (`/api/v1/expedientes`)
- [ ] Implementar router de actuaciones (`/api/v1/actuaciones`)
- [ ] Implementar router de monitoring (`/api/v1/monitoring`)
- [ ] Implementar router de config (`/api/v1/config`)
- [ ] Crear schemas Pydantic
- [ ] Implementar middleware de auth (JWT)
- [ ] Implementar middleware de error handling
- [ ] Configurar CORS
- [ ] Documentación automática (Swagger)

#### 4.2 MCP Server
- [ ] Migrar `mcp_server/` → `presentation/api/mcp/`
- [ ] Actualizar imports a nueva arquitectura
- [ ] Verificar que tools usan Application layer

#### 4.3 Web UI
- [ ] Setup proyecto frontend (Vite + React/Vue)
- [ ] Implementar componentes base
- [ ] Implementar páginas:
  - [ ] Dashboard
  - [ ] Expedientes (listado + detalle)
  - [ ] Actuaciones
  - [ ] Monitor
  - [ ] Configuración
- [ ] Integrar con REST API (Axios)
- [ ] Implementar state management
- [ ] Estilos con Tailwind CSS

#### 4.4 CLI
- [ ] Migrar scripts de `bin/` → `presentation/cli/commands/`
- [ ] Comando `extraer`
- [ ] Comando `monitorear`
- [ ] Comando `config`
- [ ] Comando `workspace`
- [ ] Usar Click o Typer para CLI

#### 4.5 Tests E2E
- [ ] Tests de workflow completo (4 fases)
- [ ] Tests de API endpoints
- [ ] Tests de Web UI (Playwright para frontend)

### Bloqueadores Potenciales

- ⚠️ Frontend requiere conocimientos de JavaScript/React
  - **Solución**: Usar templates existentes o contratar frontend dev

### Métricas de Éxito

- ✅ API REST funcional con todos los endpoints
- ✅ MCP Server migrado y funcional
- ✅ Web UI responsive y moderna
- ✅ CLI funcional
- ✅ Tests E2E pasando

---

## 🔌 FASE 5: Plugin System (3-4 días)

**Estado:** 🔴 PENDIENTE
**Branch:** v6-phase5-plugins (a crear)
**Estimación:** 3-4 días
**Dependencias:** Fase 4 completa

### Objetivos

1. Implementar sistema de plugins base
2. Crear plugin de ejemplo (Auth)
3. Documentar cómo crear plugins

### Checklist

#### 5.1 Core de Plugins
- [ ] Implementar `core/plugins/plugin_interface.py`
- [ ] Implementar `core/plugins/plugin_manager.py`
- [ ] Implementar `core/plugins/plugin_registry.py`
- [ ] Sistema de carga dinámica de plugins
- [ ] Sistema de dependencias entre plugins

#### 5.2 Plugin Base: Auth
- [ ] Implementar `plugins/auth/plugin.py`
- [ ] Implementar `plugins/auth/auth_service.py`
- [ ] Implementar `plugins/auth/permissions.py`
- [ ] Implementar `plugins/auth/user_repository.py`
- [ ] Registrar routes en API

#### 5.3 Configuración de Plugins
- [ ] Crear `config/plugins.json`
- [ ] Sistema de enable/disable plugins
- [ ] Validación de configuración

#### 5.4 Tests
- [ ] Tests para PluginManager
- [ ] Tests para plugin Auth

### Métricas de Éxito

- ✅ Sistema de plugins funcional
- ✅ Al menos 1 plugin de ejemplo funcional
- ✅ Documentación clara de cómo crear plugins

---

## 📊 FASE 6: Migración de Datos (2-3 días)

**Estado:** 🔴 PENDIENTE
**Branch:** v6-phase6-migration (a crear)
**Estimación:** 2-3 días
**Dependencias:** Fase 5 completa

### Objetivos

1. Crear scripts de migración v5 → v6
2. Migrar configuraciones
3. Migrar datos de estados
4. Migrar historial del monitor
5. Validar integridad

### Checklist

#### 6.1 Script de Migración
- [ ] Crear `scripts/migrar_datos_v5_to_v6.py`
- [ ] Migrar `config/sistema.json`
- [ ] Migrar `data/estados/estados_usuario.json`
- [ ] Migrar `var/monitor/historial_expedientes.json`
- [ ] Migrar `var/monitor/historial_entradas.json`
- [ ] Migrar workspace (directorios de expedientes)

#### 6.2 Validación
- [ ] Verificar integridad de JSONs migrados
- [ ] Verificar estructura de workspace
- [ ] Comparar counts (v5 vs v6)
- [ ] Tests de regresión

#### 6.3 Rollback Plan
- [ ] Documentar proceso de rollback
- [ ] Script de rollback (opcional)

### Métricas de Éxito

- ✅ Todos los datos migrados correctamente
- ✅ Validación exitosa
- ✅ Cero pérdida de datos

---

## 🧪 FASE 7: Testing & Documentation (3-4 días)

**Estado:** 🔴 PENDIENTE
**Branch:** v6-phase7-docs (a crear)
**Estimación:** 3-4 días
**Dependencias:** Fase 6 completa

### Objetivos

1. Completar suite de tests (unit + integration + e2e)
2. Documentación completa
3. Guías de usuario y developer
4. API reference

### Checklist

#### 7.1 Tests Completos
- [ ] Ejecutar `pytest tests/` (todo verde)
- [ ] Verificar coverage >= 85%
- [ ] Corregir tests rotos
- [ ] Agregar tests faltantes

#### 7.2 Documentación de Usuario
- [ ] Crear `docs/USER_GUIDE.md`
  - Instalación
  - Configuración inicial
  - Uso de las 4 fases
  - Troubleshooting
- [ ] Crear `docs/FAQ.md`

#### 7.3 Documentación de API
- [ ] Crear `docs/API_REFERENCE.md`
  - Documentar todos los endpoints
  - Ejemplos de uso
  - Schemas

#### 7.4 Documentación de Developer
- [ ] Crear `docs/DEVELOPER_GUIDE.md`
  - Setup de desarrollo
  - Arquitectura
  - Cómo contribuir
  - Cómo crear plugins
- [ ] Crear `docs/DEPLOYMENT.md`
  - Docker
  - Systemd
  - Nginx

#### 7.5 README Principal
- [ ] Actualizar `README.md` con overview completo

### Métricas de Éxito

- ✅ Coverage >= 85%
- ✅ Documentación completa
- ✅ Todos los tests pasando

---

## 🚀 EXTENSIONES FUTURAS (Post-lanzamiento)

### Plugin: Notificaciones
**Estimación:** 2 semanas
**Prioridad:** Alta
**Dependencias:** Fase 5 completa

- [ ] Email notifier
- [ ] Telegram notifier
- [ ] WhatsApp notifier
- [ ] Discord notifier
- [ ] Configuración por usuario
- [ ] Horarios personalizados

### Plugin: Oficios Digitales
**Estimación:** 2-3 semanas
**Prioridad:** Alta
**Dependencias:** Fase 5 completa

- [ ] Templates de oficios
- [ ] Template engine (Jinja2)
- [ ] Firma digital
- [ ] API de envío al PJN
- [ ] Tracking de oficios enviados

### Plugin: IA Local
**Estimación:** 3 semanas
**Prioridad:** Media
**Dependencias:** Fase 5 completa

- [ ] Integración con Ollama
- [ ] RAG sobre expedientes (ChromaDB)
- [ ] Análisis automático de expedientes
- [ ] Generación de resúmenes
- [ ] Consultas en lenguaje natural

### Plugin: Procesamiento de PDFs
**Estimación:** 2 semanas
**Prioridad:** Media
**Dependencias:** Fase 5 completa

- [ ] OCR con Tesseract
- [ ] Extracción de entidades (NER)
- [ ] Búsqueda semántica en PDFs
- [ ] Clasificación de documentos
- [ ] Índice de contenido

### Plugin: Escritos Automáticos
**Estimación:** 2-3 semanas
**Prioridad:** Media
**Dependencias:** Plugin IA Local

- [ ] Templates de escritos
- [ ] Generación con IA
- [ ] Sugerencias estratégicas
- [ ] Revisión automática
- [ ] Formateo profesional

### Plugin: Autenticación Multi-Usuario
**Estimación:** 2 semanas
**Prioridad:** Alta (si multi-usuario es necesario)
**Dependencias:** Fase 5 completa

- [ ] JWT authentication
- [ ] Sistema de roles (RBAC)
- [ ] Permisos por expediente
- [ ] User management
- [ ] Audit log

---

## 📈 Métricas del Proyecto

### Código

- **Líneas de código actuales:** 0
- **Líneas esperadas:** ~25,000
- **Cobertura de tests objetivo:** 85%+
- **Archivos Python:** ~150+

### Performance

- **Tiempo de extracción (fase 1):** < 5 min (100 expedientes)
- **Tiempo de monitoreo (fase 4):** < 2 min por ciclo
- **Memoria máxima:** < 500 MB

### Calidad

- **Complejidad ciclomática:** < 10 (promedio)
- **Duplicación de código:** < 5%
- **Deuda técnica:** Baja

---

## 🐛 Issues Conocidos

### Issues Abiertos

(Ninguno por ahora)

### Issues Resueltos

(Ninguno por ahora)

---

## 🗓️ Timeline Detallado

```
2025-11-05  ████████  Fase 0: Setup Inicial (EN PROGRESO)
2025-11-06  ░░░░░░░░
2025-11-07  ████████  Fase 1: Domain Layer
2025-11-08  ████████
2025-11-09  ████████
2025-11-10  ████████
2025-11-11  ████████  Fase 2: Application Layer
2025-11-12  ████████
2025-11-13  ████████
2025-11-14  ████████
2025-11-15  ████████
2025-11-16  ████████  Fase 3: Infrastructure Layer
2025-11-17  ████████
2025-11-18  ████████
2025-11-19  ████████
2025-11-20  ████████
2025-11-21  ████████
2025-11-22  ████████
2025-11-23  ████████
2025-11-24  ████████
2025-11-25  ████████
2025-11-26  ████████  Fase 4: Presentation Layer
2025-11-27  ████████
2025-11-28  ████████
2025-11-29  ████████
2025-11-30  ████████
2025-12-01  ████████
2025-12-02  ████████
2025-12-03  ████████  Fase 5: Plugin System
2025-12-04  ████████
2025-12-05  ████████
2025-12-06  ████████
2025-12-07  ████████  Fase 6: Migración de Datos
2025-12-08  ████████
2025-12-09  ████████
2025-12-10  ████████  Fase 7: Testing & Docs
2025-12-11  ████████
2025-12-12  ████████
2025-12-13  ████████
2025-12-14  ████████  LANZAMIENTO v6.0.0
```

---

## 📚 Próximos Pasos Inmediatos

### Hoy (2025-11-05)

1. ✅ Crear rama v6-refactorization
2. ✅ Crear estructura de directorios
3. ✅ Crear `docs/V6_ARCHITECTURE.md`
4. ✅ Crear `docs/V6_ROADMAP.md` (este archivo)
5. ⏳ Crear `docs/V6_CONTEXT.md`
6. ⏳ Crear archivos de configuración
7. ⏳ Hacer commit inicial

### Mañana (2025-11-06)

1. Completar Fase 0
2. Comenzar Fase 1: Migrar ExpedienteResumen
3. Crear tests para ExpedienteResumen

### Esta Semana (2025-11-05 a 2025-11-10)

1. Completar Fase 0
2. Completar Fase 1 (Domain Layer)
3. Comenzar Fase 2 (Application Layer)

---

## ✅ Checklist de Pre-Lanzamiento

Antes de lanzar v6.0.0, verificar:

- [ ] Todas las fases completadas
- [ ] Tests con 85%+ coverage (todos pasando)
- [ ] Documentación completa
- [ ] API REST funcional
- [ ] Web UI funcional
- [ ] CLI funcional
- [ ] MCP Server funcional
- [ ] Migración de datos exitosa
- [ ] Performance aceptable
- [ ] Sin issues críticos abiertos
- [ ] README actualizado
- [ ] CHANGELOG.md creado
- [ ] Tag de versión creado
- [ ] Deploy en ambiente de staging exitoso

---

## 📞 Contacto

**Mantenido por:** Equipo de desarrollo Sistema PJN
**Última actualización:** 2025-11-05
**Próxima revisión:** 2025-11-06

---

**Nota:** Este documento se actualiza diariamente durante el desarrollo. Si encuentras información desactualizada, por favor actualízala.
