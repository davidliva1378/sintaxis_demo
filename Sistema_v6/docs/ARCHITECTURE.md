# Arquitectura del Sistema PJN v6

**Documentación detallada de la arquitectura Clean Architecture implementada en Sistema PJN v6**

---

## 📋 Tabla de Contenidos

1. [Visión General](#visión-general)
2. [Clean Architecture](#clean-architecture)
3. [Capas del Sistema](#capas-del-sistema)
4. [Flujo de Datos](#flujo-de-datos)
5. [Patrones de Diseño](#patrones-de-diseño)
6. [Dependency Injection](#dependency-injection)
7. [Decisiones Arquitectónicas](#decisiones-arquitectónicas)
8. [Testing Strategy](#testing-strategy)

---

## 🎯 Visión General

Sistema PJN v6 implementa **Clean Architecture** (arquitectura limpia) propuesta por Robert C. Martin (Uncle Bob), combinada con principios de **Domain-Driven Design (DDD)** y el patrón **Ports & Adapters** (Hexagonal Architecture).

### Objetivos Principales

1. **Independencia de frameworks:** El negocio no depende de librerías externas
2. **Testeable:** La lógica de negocio se puede testear sin UI, base de datos, etc.
3. **Independencia de UI:** La UI puede cambiar sin afectar el resto
4. **Independencia de base de datos:** Podemos cambiar de JSON a PostgreSQL sin dolor
5. **Independencia de agentes externos:** La lógica no sabe nada del mundo exterior

### Principios SOLID

Todos los componentes siguen los principios SOLID:

- ✅ **S**ingle Responsibility Principle
- ✅ **O**pen/Closed Principle
- ✅ **L**iskov Substitution Principle
- ✅ **I**nterface Segregation Principle
- ✅ **D**ependency Inversion Principle

---

## 🏗️ Clean Architecture

### Diagrama de Capas Concéntricas

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │                                                      │  │
│  │  ┌────────────────────────────────────────────┐     │  │
│  │  │                                            │     │  │
│  │  │   ┌────────────────────────────────┐      │     │  │
│  │  │   │                                │      │     │  │
│  │  │   │       DOMAIN LAYER            │      │     │  │
│  │  │   │   (Entities, Value Objects)    │      │     │  │
│  │  │   │                                │      │     │  │
│  │  │   │   • ExpedienteResumen          │      │     │  │
│  │  │   │   • Entrada                    │      │     │  │
│  │  │   │   • Actuacion                  │      │     │  │
│  │  │   │   • CriteriosFiltrado          │      │     │  │
│  │  │   │                                │      │     │  │
│  │  │   └────────────────────────────────┘      │     │  │
│  │  │                                            │     │  │
│  │  │        APPLICATION LAYER                  │     │  │
│  │  │      (Use Cases, Ports)                   │     │  │
│  │  │                                            │     │  │
│  │  │   • ExtraerExpedientesUseCase             │     │  │
│  │  │   • FiltrarExpedientesUseCase             │     │  │
│  │  │   • IScraperPort (interface)              │     │  │
│  │  │   • IStoragePort (interface)              │     │  │
│  │  │                                            │     │  │
│  │  └────────────────────────────────────────────┘     │  │
│  │                                                      │  │
│  │           INFRASTRUCTURE LAYER                      │  │
│  │              (Adapters, Config)                     │  │
│  │                                                      │  │
│  │   • PlaywrightScraperAdapter                        │  │
│  │   • JSONStorageAdapter                              │  │
│  │   • WorkspaceAdapter                                │  │
│  │   • Settings (Pydantic)                             │  │
│  │                                                      │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│               PRESENTATION LAYER                            │
│            (CLI, REST API, MCP Server)                      │
│                                                             │
│   • Click CLI + Rich                                        │
│   • FastAPI REST API                                        │
│   • MCP Server                                              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Regla de Dependencias

**Las dependencias SIEMPRE apuntan hacia adentro:**

```
Presentation → Infrastructure → Application → Domain
```

- **Domain** no conoce nada del exterior (cero dependencias)
- **Application** solo conoce Domain
- **Infrastructure** conoce Application y Domain (implementa interfaces)
- **Presentation** conoce todo (orquesta las capas)

---

## 📦 Capas del Sistema

### 1. 🎯 Domain Layer (Core/Domain)

**Propósito:** Contiene la lógica de negocio pura y las reglas del dominio.

**Ubicación:** `core/domain/`

**Componentes:**

#### Entidades (Entities)

Objetos con identidad única que representan conceptos del negocio.

```python
# core/domain/entities/expediente.py
@dataclass(frozen=True)
class ExpedienteResumen:
    """Representa un resumen de expediente del PJN."""
    numero: str
    dependencia: str
    caratula: str
    situacion: str | None = None
    ultima_actuacion: str | None = None
    expediente_electronico: bool = False
```

**Entidades disponibles:**
- `ExpedienteResumen` - Resumen de expediente
- `ExpedienteIdentificacion` - Identificación única
- `Entrada` - Notificación/despacho
- `Actuacion` - Actuación judicial
- `ActuacionesArchivo` - Agregado de actuaciones
- `WorkspaceInfo` - Información del workspace

#### Value Objects

Objetos inmutables sin identidad definidos por sus atributos.

```python
# core/domain/value_objects/criterios_filtrado.py
@dataclass(frozen=True)
class CriteriosFiltrado:
    """Criterios para filtrar expedientes."""
    dependencia: str | None = None
    situacion: str | None = None
    caratula_contiene: str | None = None
    dias_actividad: int | None = None
    expediente_electronico: bool | None = None
```

#### Domain Utils

Funciones puras sin efectos secundarios.

```python
# core/domain/utils/dates.py
def normalizar_fecha(
    fecha_str: str,
    *,
    formatos_entrada: Sequence[str] | None = None,
    formato_salida: str = "%Y-%m-%d",
) -> str | None:
    """Normaliza una fecha a formato estándar ISO 8601."""
    # ...
```

**Características:**
- ✅ Sin dependencias externas
- ✅ 100% testeable con unit tests
- ✅ Inmutable (frozen dataclasses)
- ✅ Type hints completos

---

### 2. 📋 Application Layer

**Propósito:** Casos de uso del sistema e interfaces (ports).

**Ubicación:** `application/`

**Componentes:**

#### Use Cases

Orquestan la lógica de negocio usando entidades y servicios.

```python
# application/use_cases/extraer_expedientes.py
class ExtraerExpedientesUseCase:
    """Caso de uso: extraer expedientes del PJN."""

    def __init__(
        self,
        scraper: IScraperPort,
        storage: IStoragePort,
        repository: IExpedienteRepository,
    ):
        self._scraper = scraper
        self._storage = storage
        self._repository = repository

    async def execute(
        self,
        *,
        credenciales: tuple[str, str] | None = None,
        headless: bool = True,
    ) -> ExtraccionResult:
        """Ejecuta la extracción de expedientes."""
        # 1. Scraping
        expedientes = await self._scraper.extraer_expedientes(
            credenciales=credenciales,
            headless=headless,
        )

        # 2. Guardar en repositorio
        await self._repository.guardar_varios(expedientes)

        # 3. Persistir en storage
        await self._storage.guardar_json(
            datos=[exp.model_dump() for exp in expedientes],
            archivo=Path("data/expedientes_base.json"),
        )

        return ExtraccionResult(
            total=len(expedientes),
            exitosos=len(expedientes),
            fallidos=0,
        )
```

**Use Cases disponibles:**
- `ExtraerExpedientesUseCase` - Extrae expedientes
- `ExtraerEntradasUseCase` - Extrae entradas/notificaciones
- `ExtraerActuacionesUseCase` - Extrae actuaciones
- `FiltrarExpedientesUseCase` - Filtra expedientes
- `GestionarWorkspaceUseCase` - Gestiona workspaces

#### Ports (Interfaces)

Contratos que Infrastructure debe implementar.

```python
# application/ports/services.py
class IScraperPort(ABC):
    """Interfaz para scraping del PJN."""

    @abstractmethod
    async def extraer_expedientes(
        self,
        *,
        credenciales: tuple[str, str] | None = None,
        headless: bool = True,
    ) -> list[ExpedienteResumen]:
        """Extrae expedientes del PJN."""
        pass

    @abstractmethod
    async def extraer_entradas(
        self,
        *,
        credenciales: tuple[str, str] | None = None,
        headless: bool = True,
    ) -> list[Entrada]:
        """Extrae entradas/notificaciones."""
        pass
```

**Ports disponibles:**
- `IScraperPort` - Scraping del PJN
- `IStoragePort` - Almacenamiento de archivos
- `IWorkspacePort` - Gestión de workspaces
- `INotificacionPort` - Notificaciones
- `IExpedienteRepository` - Repositorio de expedientes
- `IEntradaRepository` - Repositorio de entradas
- `IActuacionRepository` - Repositorio de actuaciones

**Características:**
- ✅ Sin implementaciones concretas
- ✅ Solo interfaces (ABC)
- ✅ Dependency Inversion Principle

---

### 3. 🔧 Infrastructure Layer

**Propósito:** Implementaciones concretas de los ports.

**Ubicación:** `infrastructure/`

**Componentes:**

#### Adapters

Implementan las interfaces definidas en Application.

**Storage Adapters:**

```python
# infrastructure/adapters/storage/json_storage_adapter.py
class JSONStorageAdapter(IStoragePort):
    """Implementación de IStoragePort usando archivos JSON."""

    async def guardar_json(
        self,
        datos: Mapping[str, Any] | Sequence[Mapping[str, Any]],
        archivo: Path,
    ) -> None:
        """Guarda datos en formato JSON."""
        archivo.parent.mkdir(parents=True, exist_ok=True)

        with archivo.open("w", encoding="utf-8") as f:
            json.dump(
                datos,
                f,
                ensure_ascii=False,
                indent=2 if self._settings.storage.pretty_json else None,
            )
```

**Scraping Adapters:**

```python
# infrastructure/adapters/scraping/playwright_scraper_adapter.py
class PlaywrightScraperAdapter(IScraperPort):
    """Implementación de IScraperPort usando Playwright."""

    async def extraer_expedientes(
        self,
        *,
        credenciales: tuple[str, str] | None = None,
        headless: bool = True,
    ) -> list[ExpedienteResumen]:
        """Extrae expedientes usando Playwright."""
        async with obtener_sesion_autenticada(...) as page:
            # Scraping con paginación
            expedientes = await self._extraer_expedientes_con_paginacion(page)
            return expedientes
```

**Componentes de Scraping:**

```
infrastructure/adapters/scraping/
├── playwright_scraper_adapter.py  # Adapter principal (~590 líneas)
├── session_manager.py             # Gestión de sesiones (~700 líneas)
├── pagination.py                  # Estrategias de paginación (~240 líneas)
├── selectores.py                  # Selectores CSS del PJN
└── parsers/                       # HTML → Entities
    ├── expedientes_parser.py      # Parser de expedientes
    ├── entradas_parser.py         # Parser de entradas
    └── actuaciones_parser.py      # Parser de actuaciones (~600 líneas)
```

#### Configuration

```python
# infrastructure/config/settings.py
class Settings(BaseSettings):
    """Configuración del sistema con Pydantic."""

    auth: AuthSettings
    browser: BrowserSettings
    storage: StorageSettings
    monitoreo: MonitoreoSettings
    # ...

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
```

**Características:**
- ✅ Implementaciones intercambiables
- ✅ Fácil de testear con mocks
- ✅ Sin lógica de negocio

---

### 4. 🖥️ Presentation Layer

**Propósito:** Interfaces de usuario y entry points.

**Ubicación:** `presentation/`

**Componentes:**

#### CLI (Command Line Interface)

```python
# presentation/cli/main.py
import click

@click.group()
def cli():
    """Sistema PJN v6 - CLI."""
    pass

@cli.command()
@click.option("--headless/--no-headless", default=True)
async def extraer_expedientes(headless: bool):
    """Extrae expedientes del PJN."""
    # Dependency injection
    use_case = crear_extraer_expedientes_use_case()

    # Ejecutar
    result = await use_case.execute(headless=headless)

    # Mostrar resultado con Rich
    console.print(f"✓ Extraídos {result.total} expedientes")
```

#### REST API

```python
# presentation/api/rest/main.py
from fastapi import FastAPI, Depends

app = FastAPI(title="Sistema PJN v6 API")

@app.post("/api/v1/expedientes/extraer")
async def extraer_expedientes(
    request: ExtraerRequest,
    use_case: ExtraerExpedientesUseCase = Depends(get_extraer_use_case),
) -> ExtraccionResponse:
    """Extrae expedientes del PJN."""
    result = await use_case.execute(
        credenciales=request.credenciales,
        headless=request.headless,
    )

    return ExtraccionResponse(
        total=result.total,
        exitosos=result.exitosos,
        fallidos=result.fallidos,
    )
```

**Endpoints disponibles:**
- `POST /api/v1/expedientes/extraer` - Extrae expedientes
- `POST /api/v1/expedientes/filtrar` - Filtra expedientes
- `POST /api/v1/entradas/extraer` - Extrae entradas
- `POST /api/v1/actuaciones/extraer` - Extrae actuaciones
- `POST /api/v1/workspace/crear` - Crea workspace

#### MCP Server

```python
# presentation/api/mcp/server.py
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("sistema-pjn-v6")

@app.call_tool()
async def extraer_expedientes(
    credenciales: tuple[str, str] | None = None,
) -> list[dict]:
    """Tool para Claude AI: extrae expedientes."""
    use_case = crear_extraer_expedientes_use_case()
    result = await use_case.execute(credenciales=credenciales)
    return [exp.model_dump() for exp in result.expedientes]
```

**Tools MCP disponibles:**
- `extraer_expedientes` - Extrae expedientes
- `extraer_entradas` - Extrae notificaciones
- `extraer_actuaciones` - Extrae actuaciones
- `filtrar_expedientes` - Filtra expedientes
- `crear_workspace` - Crea workspace
- `leer_archivo_workspace` - Lee archivos

**Características:**
- ✅ Múltiples interfaces para el mismo core
- ✅ Dependency injection
- ✅ No contiene lógica de negocio

---

## 🔄 Flujo de Datos

### Ejemplo: Extracción de Expedientes

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER                                                     │
│    CLI: python -m presentation.cli.main extraer-expedientes │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. PRESENTATION LAYER (CLI)                                 │
│    • Parsea argumentos                                      │
│    • Crea dependencias con DI                               │
│    • Invoca use case                                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. APPLICATION LAYER (Use Case)                             │
│    ExtraerExpedientesUseCase.execute()                      │
│    • Valida parámetros                                      │
│    • Llama a scraper.extraer_expedientes()                  │
│    • Transforma entities                                    │
│    • Guarda en storage                                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. INFRASTRUCTURE LAYER (Adapter)                           │
│    PlaywrightScraperAdapter.extraer_expedientes()           │
│    • Abre navegador con Playwright                          │
│    • Autentica con session_manager                          │
│    • Extrae HTML con paginación                             │
│    • Parsea HTML → Entities                                 │
│    • Retorna list[ExpedienteResumen]                        │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. DOMAIN LAYER (Entities)                                  │
│    ExpedienteResumen                                        │
│    • Valida datos con Pydantic                              │
│    • Normaliza fechas                                       │
│    • Retorna entity inmutable                               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 6. INFRASTRUCTURE LAYER (Storage)                           │
│    JSONStorageAdapter.guardar_json()                        │
│    • Serializa entities                                     │
│    • Guarda en archivo JSON                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│ 7. PRESENTATION LAYER (CLI)                                 │
│    • Formatea resultado con Rich                            │
│    • Muestra tabla en terminal                              │
│    • Retorna exit code                                      │
└─────────────────────────────────────────────────────────────┘
```

### Flujo de Dependencias

```
CLI/API/MCP (Presentation)
    ↓ depends on
Use Cases (Application)
    ↓ depends on
Ports/Interfaces (Application)
    ↑ implemented by
Adapters (Infrastructure)
    ↓ uses
Entities (Domain)
```

---

## 🎨 Patrones de Diseño

### 1. Ports & Adapters (Hexagonal Architecture)

**Problema:** Dependencia de frameworks y librerías externas.

**Solución:** Definir interfaces (ports) en Application y crear adaptadores (adapters) en Infrastructure.

```python
# Application define el contrato
class IScraperPort(ABC):
    @abstractmethod
    async def extraer_expedientes(...) -> list[ExpedienteResumen]:
        pass

# Infrastructure implementa
class PlaywrightScraperAdapter(IScraperPort):
    async def extraer_expedientes(...) -> list[ExpedienteResumen]:
        # Implementación con Playwright
        pass

class SeleniumScraperAdapter(IScraperPort):  # Alternativa
    async def extraer_expedientes(...) -> list[ExpedienteResumen]:
        # Implementación con Selenium
        pass
```

### 2. Dependency Injection

**Problema:** Acoplamiento fuerte entre componentes.

**Solución:** Inyectar dependencias en constructores.

```python
# presentation/dependencies.py
def crear_extraer_expedientes_use_case() -> ExtraerExpedientesUseCase:
    """Factory para crear el use case con todas sus dependencias."""
    settings = get_settings()

    # Crear adapters
    scraper = PlaywrightScraperAdapter(
        login_url=settings.auth.login_url,
        settings=settings,
    )
    storage = JSONStorageAdapter(settings=settings)
    repository = ExpedienteRepositoryMemory()

    # Inyectar en use case
    return ExtraerExpedientesUseCase(
        scraper=scraper,
        storage=storage,
        repository=repository,
    )
```

### 3. Repository Pattern

**Problema:** Acceso directo a datos dificulta testing y cambios.

**Solución:** Abstraer acceso a datos detrás de interfaces.

```python
# Application define interface
class IExpedienteRepository(ABC):
    @abstractmethod
    async def obtener_todos(self) -> list[ExpedienteResumen]:
        pass

    @abstractmethod
    async def guardar(self, expediente: ExpedienteResumen) -> None:
        pass

# Infrastructure implementa
class ExpedienteRepositoryMemory(IExpedienteRepository):
    def __init__(self):
        self._expedientes: dict[str, ExpedienteResumen] = {}

    async def obtener_todos(self) -> list[ExpedienteResumen]:
        return list(self._expedientes.values())

    async def guardar(self, expediente: ExpedienteResumen) -> None:
        self._expedientes[expediente.numero] = expediente
```

### 4. Strategy Pattern

**Problema:** Diferentes algoritmos de paginación según el portal.

**Solución:** Definir estrategias intercambiables.

```python
# infrastructure/adapters/scraping/pagination.py
@runtime_checkable
class PaginationStrategy(Protocol):
    """Protocolo para estrategias de paginación."""

    async def navegar_siguiente(
        self,
        page: Page,
        tbody_locator: Locator,
        fingerprint_actual: str,
    ) -> tuple[bool, str | None]:
        """Navega a la siguiente página."""
        pass

class PrimeFacesPaginationStrategy:
    """Estrategia para portales PrimeFaces."""
    async def navegar_siguiente(...) -> tuple[bool, str | None]:
        # Implementación específica de PrimeFaces
        pass

class BootstrapPaginationStrategy:
    """Estrategia para portales Bootstrap."""
    async def navegar_siguiente(...) -> tuple[bool, str | None]:
        # Implementación específica de Bootstrap
        pass
```

### 5. Factory Pattern

**Problema:** Creación compleja de objetos con dependencias.

**Solución:** Centralizar creación en factories.

```python
# presentation/dependencies.py
def crear_extraer_expedientes_use_case() -> ExtraerExpedientesUseCase:
    """Factory que crea el use case completo."""
    settings = get_settings()
    scraper = PlaywrightScraperAdapter(...)
    storage = JSONStorageAdapter(...)
    repository = ExpedienteRepositoryMemory()

    return ExtraerExpedientesUseCase(
        scraper=scraper,
        storage=storage,
        repository=repository,
    )
```

### 6. Value Object Pattern

**Problema:** Objetos primitivos sin validación.

**Solución:** Encapsular en value objects inmutables.

```python
@dataclass(frozen=True)
class CriteriosFiltrado:
    """Value object para criterios de filtrado."""
    dependencia: str | None = None
    situacion: str | None = None
    dias_actividad: int | None = None

    def __post_init__(self):
        if self.dias_actividad is not None and self.dias_actividad < 0:
            raise ValueError("dias_actividad debe ser positivo")
```

---

## 💉 Dependency Injection

### Configuración Manual (Sin Framework)

```python
# presentation/dependencies.py
from infrastructure.config import get_settings
from infrastructure.adapters.scraping import PlaywrightScraperAdapter
from infrastructure.adapters.storage import JSONStorageAdapter
from application.use_cases import ExtraerExpedientesUseCase

def crear_extraer_expedientes_use_case() -> ExtraerExpedientesUseCase:
    """Factory para ExtraerExpedientesUseCase."""
    settings = get_settings()

    scraper = PlaywrightScraperAdapter(
        login_url=settings.auth.login_url,
        settings=settings,
    )

    storage = JSONStorageAdapter(settings=settings)

    repository = ExpedienteRepositoryMemory()

    return ExtraerExpedientesUseCase(
        scraper=scraper,
        storage=storage,
        repository=repository,
    )
```

### Uso en CLI

```python
# presentation/cli/main.py
@cli.command()
async def extraer_expedientes():
    """Extrae expedientes del PJN."""
    # Obtener use case con DI
    use_case = crear_extraer_expedientes_use_case()

    # Ejecutar
    result = await use_case.execute()

    # Mostrar resultado
    console.print(f"✓ {result.total} expedientes extraídos")
```

### Uso en FastAPI

```python
# presentation/api/rest/main.py
from fastapi import Depends

def get_extraer_use_case() -> ExtraerExpedientesUseCase:
    """Dependency para FastAPI."""
    return crear_extraer_expedientes_use_case()

@app.post("/api/v1/expedientes/extraer")
async def extraer_expedientes(
    use_case: ExtraerExpedientesUseCase = Depends(get_extraer_use_case),
) -> ExtraccionResponse:
    """Endpoint para extraer expedientes."""
    result = await use_case.execute()
    return ExtraccionResponse.from_result(result)
```

---

## 🎯 Decisiones Arquitectónicas

### 1. ¿Por qué Clean Architecture?

**Decisión:** Implementar Clean Architecture en lugar de arquitectura en capas tradicional.

**Razones:**
- ✅ Independencia de frameworks (podemos cambiar FastAPI por Flask)
- ✅ Testeable (lógica sin UI/DB)
- ✅ Flexible (agregar nuevas interfaces sin tocar el core)
- ✅ Mantenible (separación clara de responsabilidades)

### 2. ¿Por qué Pydantic en Domain?

**Decisión:** Usar Pydantic dataclasses para entidades del dominio.

**Razones:**
- ✅ Validación automática de tipos
- ✅ Serialización JSON out-of-the-box
- ✅ Inmutabilidad con `frozen=True`
- ✅ Type safety con mypy

**Trade-off:** Dependencia externa en Domain (aceptable porque es validación de datos).

### 3. ¿Por qué Playwright en lugar de Selenium?

**Decisión:** Usar Playwright para scraping.

**Razones:**
- ✅ Más rápido que Selenium
- ✅ Mejor manejo de async/await
- ✅ Anti-detección incorporada
- ✅ Manejo robusto de timeouts

### 4. ¿Por qué JSON y no Base de Datos?

**Decisión:** Usar JSON para persistencia (al principio).

**Razones:**
- ✅ Simple para MVP
- ✅ Sin setup de database
- ✅ Fácil de versionar (git)
- ✅ Fácil de migrar después (Ports & Adapters)

**Próximos pasos:** Agregar PostgreSQL como alternativa.

### 5. ¿Por qué 3 interfaces (CLI/API/MCP)?

**Decisión:** Implementar múltiples interfaces desde el inicio.

**Razones:**
- ✅ CLI para automatización y scripts
- ✅ API REST para integraciones web
- ✅ MCP para integración con LLMs (Claude AI)
- ✅ Demuestra flexibilidad de Clean Architecture

---

## 🧪 Testing Strategy

### Pirámide de Testing

```
         ┌──────┐
        ╱  E2E   ╲         ← Pocos, lentos, caros
       ╱──────────╲
      ╱ Integration╲       ← Moderados, medios
     ╱──────────────╲
    ╱   Unit Tests   ╲     ← Muchos, rápidos, baratos
   ╱──────────────────╲
  ╱────────────────────╲
```

### 1. Unit Tests (Domain Layer)

**Objetivo:** Testear lógica de negocio pura.

```python
# tests/unit/core/domain/entities/test_expediente.py
def test_expediente_resumen_valido():
    """Test: crear expediente con datos válidos."""
    exp = ExpedienteResumen(
        numero="CNM 0001/2024",
        dependencia="CNM",
        caratula="CASO DE PRUEBA",
        situacion="A sentencia",
        ultima_actuacion="2024-01-15",
    )

    assert exp.numero == "CNM 0001/2024"
    assert exp.dependencia == "CNM"

def test_criterios_filtrado_valida_dias():
    """Test: validación de dias_actividad."""
    with pytest.raises(ValueError):
        CriteriosFiltrado(dias_actividad=-1)  # ❌ No permitido
```

**Características:**
- ✅ Sin dependencias externas
- ✅ Muy rápidos (milisegundos)
- ✅ 100% de cobertura objetivo

### 2. Integration Tests (Infrastructure Layer)

**Objetivo:** Testear adapters con dependencias reales.

```python
# tests/integration/infrastructure/adapters/scraping/test_playwright_scraper_adapter.py
@pytest.mark.asyncio
async def test_extraer_expedientes_con_credenciales(
    pjn_credentials: tuple[str, str],
    test_settings: Settings,
):
    """Test: extracción real del PJN."""
    adapter = PlaywrightScraperAdapter(
        login_url="https://scw.pjn.gov.ar",
        settings=test_settings,
    )

    expedientes = await adapter.extraer_expedientes(
        credenciales=pjn_credentials,
        headless=True,
    )

    assert isinstance(expedientes, list)
    if expedientes:
        assert expedientes[0].numero
        assert expedientes[0].caratula
```

**Características:**
- ✅ Requieren credenciales PJN
- ✅ Se conectan al portal real
- ✅ Auto-skip si no hay credenciales

### 3. E2E Tests (Presentation Layer)

**Objetivo:** Testear flujo completo desde UI.

```python
# tests/e2e/test_cli.py (pendiente)
def test_cli_extraer_expedientes():
    """Test: CLI extrae expedientes end-to-end."""
    result = subprocess.run(
        ["python", "-m", "presentation.cli.main", "extraer-expedientes"],
        capture_output=True,
    )

    assert result.returncode == 0
    assert "expedientes extraídos" in result.stdout.decode()
```

### Estrategia de Mocking

```python
# tests/unit/application/use_cases/test_extraer_expedientes.py
@pytest.mark.asyncio
async def test_extraer_expedientes_use_case():
    """Test: use case con mocks."""
    # Arrange: crear mocks
    mock_scraper = AsyncMock(spec=IScraperPort)
    mock_scraper.extraer_expedientes.return_value = [
        ExpedienteResumen(numero="TEST", ...)
    ]

    mock_storage = AsyncMock(spec=IStoragePort)
    mock_repository = AsyncMock(spec=IExpedienteRepository)

    use_case = ExtraerExpedientesUseCase(
        scraper=mock_scraper,
        storage=mock_storage,
        repository=mock_repository,
    )

    # Act: ejecutar
    result = await use_case.execute()

    # Assert: verificar
    assert result.total == 1
    mock_scraper.extraer_expedientes.assert_called_once()
    mock_storage.guardar_json.assert_called_once()
```

---

## 📚 Referencias

- [Clean Architecture (Uncle Bob)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Domain-Driven Design (Martin Fowler)](https://martinfowler.com/bliki/DomainDrivenDesign.html)
- [Hexagonal Architecture (Alistair Cockburn)](https://alistair.cockburn.us/hexagonal-architecture/)
- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Ports and Adapters Pattern](https://herbertograca.com/2017/09/14/ports-adapters-architecture/)

---

**Versión:** 1.0
**Última actualización:** 2025-11-05
**Autor:** Equipo Sistema PJN
