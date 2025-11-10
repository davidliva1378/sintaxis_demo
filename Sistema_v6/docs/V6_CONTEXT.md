# Sistema PJN v6 - Contexto para Agente

**Última actualización:** 2025-11-05 12:25
**Sesión actual:** #001
**Estado:** Fase 0 - Setup Inicial (80%)

---

## 📌 RESUMEN DE ÚLTIMA SESIÓN

### Sesión #001 (2025-11-05)

**Rama actual:** `v6-refactorization`
**Trabajando en:** Fase 0 - Setup Inicial
**Progreso:** 80%

#### Tareas Completadas ✅

1. Crear rama `v6-refactorization` desde `producción_v5.1.1`
2. Crear estructura completa de directorios Sistema_v6/
3. Generar `docs/V6_ARCHITECTURE.md` (arquitectura completa)
4. Generar `docs/V6_ROADMAP.md` (tracking de progreso)
5. Generar `docs/V6_CONTEXT.md` (este archivo)

#### Tareas Pendientes 📋

1. Crear archivos de configuración base:
   - `pyproject.toml`
   - `requirements.txt`
   - `requirements-dev.txt`
   - `.env.example`
   - `pytest.ini`
   - `mypy.ini`
2. Crear `.gitignore`
3. Crear `README.md` inicial
4. Crear `__init__.py` en todos los directorios Python
5. Hacer commit inicial con estructura base

#### Próximo Paso

**Fase 0.6:** Crear archivos de configuración base (`pyproject.toml`, `requirements.txt`, etc.)

---

## 🎯 OBJETIVO ACTUAL

**Fase 0:** Completar setup inicial del proyecto
**Meta:** Tener estructura base lista y hacer commit inicial
**ETA:** 2025-11-05 final del día

---

## 📂 ESTRUCTURA ACTUAL TRABAJANDO

### Directorios Creados

```
Sistema_v6/
├── core/domain/
│   ├── entities/      [VACÍO]
│   ├── value_objects/ [VACÍO]
│   ├── utils/         [VACÍO]
│   ├── exceptions/    [VACÍO]
│   └── validators/    [VACÍO]
├── application/
│   ├── use_cases/     [VACÍO]
│   ├── services/      [VACÍO]
│   ├── dto/           [VACÍO]
│   └── ports/         [VACÍO]
├── infrastructure/
│   ├── scraping/      [VACÍO]
│   ├── parsers/       [VACÍO]
│   ├── persistence/   [VACÍO]
│   └── ...
├── presentation/
│   ├── api/rest/      [VACÍO]
│   ├── api/mcp/       [VACÍO]
│   ├── cli/           [VACÍO]
│   └── web/           [VACÍO]
├── plugins/           [VACÍO]
├── tests/             [VACÍO]
├── scripts/           [VACÍO]
├── config/            [VACÍO]
├── data/              [VACÍO]
└── docs/              [3 archivos MD]
    ├── V6_ARCHITECTURE.md  ✅
    ├── V6_ROADMAP.md       ✅
    └── V6_CONTEXT.md       ✅
```

### Archivos Pendientes de Crear

- `pyproject.toml` - Configuración del proyecto
- `requirements.txt` - Dependencias principales
- `requirements-dev.txt` - Dependencias de desarrollo
- `.env.example` - Variables de entorno ejemplo
- `.gitignore` - Ignorar archivos innecesarios
- `pytest.ini` - Configuración de tests
- `mypy.ini` - Configuración de type checking
- `README.md` - Documentación inicial
- `__init__.py` (múltiples) - En todos los directorios Python

---

## ⚠️ DECISIONES PENDIENTES

### Decisiones Técnicas

1. **¿Usar Pydantic o dataclasses en domain?**
   - **Opción A:** Pydantic (validación automática, mejor serialización)
   - **Opción B:** dataclasses (más simple, stdlib)
   - **Recomendación:** Pydantic para DTOs/API, dataclasses para domain
   - **Estado:** ⏳ Pendiente de confirmar

2. **¿Estructura de tests: mirrors src o flat?**
   - **Opción A:** `tests/unit/core/domain/entities/test_expediente.py` (mirrors)
   - **Opción B:** `tests/unit/test_expediente.py` (flat)
   - **Recomendación:** Mirrors (opción A) para mejor organización
   - **Estado:** ⏳ Pendiente de confirmar

3. **¿Frontend: React o Vue.js?**
   - **Opción A:** React (más popular, más jobs)
   - **Opción B:** Vue.js (más simple, mejor para Python devs)
   - **Recomendación:** Vue.js 3 con Composition API
   - **Estado:** ⏳ Pendiente de confirmar

### Decisiones de Negocio

1. **¿Implementar multi-usuario desde Fase Base o en Plugin?**
   - **Recomendación:** Implementar como Plugin (Fase 5)
   - **Estado:** ✅ Decidido (Plugin)

2. **¿Prioridad de plugins?**
   - Alta: Notificaciones, Auth (si multi-usuario)
   - Media: IA Local, Oficios Digitales
   - Baja: PDF Processing, Escritos Automáticos
   - **Estado:** ⏳ Confirmar con usuario

---

## 🐛 PROBLEMAS ENCONTRADOS

### Problemas Resueltos ✅

(Ninguno por ahora - primera sesión)

### Problemas Abiertos 🔴

(Ninguno por ahora)

### Warnings/Notas ⚠️

1. **Tree command no disponible en Windows**
   - Usar `ls` o `dir` en su lugar
   - No es bloqueante

---

## 💻 COMANDOS ÚTILES

### Git

```bash
# Ver estado actual
git status

# Cambiar de rama
git checkout v6-refactorization

# Ver historial de commits
git log --oneline --graph

# Ver diferencias
git diff
```

### Testing

```bash
# Ejecutar todos los tests
pytest tests/

# Tests con cobertura
pytest tests/ --cov=Sistema_v6 --cov-report=html

# Tests de un módulo específico
pytest tests/unit/core/domain/

# Tests con output verbose
pytest tests/ -v
```

### Type Checking

```bash
# Verificar tipos en todo el proyecto
mypy Sistema_v6/

# Verificar solo domain
mypy Sistema_v6/core/domain/

# Con strict mode
mypy Sistema_v6/ --strict
```

### Code Quality

```bash
# Formatear código
black Sistema_v6/

# Linting
ruff check Sistema_v6/

# Ordenar imports
isort Sistema_v6/

# Todo junto
black Sistema_v6/ && isort Sistema_v6/ && ruff check Sistema_v6/
```

### Desarrollo

```bash
# Activar entorno virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Ejecutar servidor API
uvicorn presentation.api.rest.main:app --reload

# Ejecutar CLI
python -m presentation.cli.main extraer --help
```

---

## 🔍 REFERENCIAS RÁPIDAS

### Imports Importantes

```python
# Domain
from core.domain.entities.expediente import ExpedienteResumen
from core.domain.entities.entrada import Entrada
from core.domain.utils.text import normalizar_texto
from core.domain.utils.dates import normalizar_fecha

# Application
from application.use_cases.fase1_extraer_listado import Fase1ExtraerListadoUseCase
from application.ports.scraping_port import ScrapingPort
from application.services.extraction_service import ExtractionService

# Infrastructure
from infrastructure.scraping.extractors.expediente_extractor import ExpedienteExtractor
from infrastructure.persistence.json.expediente_json_repository import ExpedienteJSONRepository
from infrastructure.config.system_config import SystemConfig

# Presentation
from presentation.api.rest.routers.expedientes import router as expedientes_router
```

### Paths Importantes

```python
# Sistema_v6/
BASE_DIR = Path(__file__).parent

# Directorios de datos
DATA_DIR = BASE_DIR / "data"
CONFIG_DIR = BASE_DIR / "config"
WORKSPACE_DIR = DATA_DIR / "expedientes"

# Archivos de configuración
SYSTEM_CONFIG = CONFIG_DIR / "system.json"
MONITOR_CONFIG = CONFIG_DIR / "monitoring.json"
PLUGINS_CONFIG = CONFIG_DIR / "plugins.json"

# Archivos de datos
LISTADO_BASE = DATA_DIR / "listado_base.json"
LISTADO_SISTEMA = DATA_DIR / "listado_sistema.json"
ESTADOS_USUARIO = DATA_DIR / "estados" / "estados_usuario.json"
```

### Convenciones de Código

```python
# Naming conventions
class MyClass:              # PascalCase para clases
    pass

def my_function():          # snake_case para funciones
    pass

MY_CONSTANT = "value"       # UPPER_CASE para constantes

my_variable = "value"       # snake_case para variables

# Type hints (siempre usar)
def process(data: dict[str, Any]) -> ExpedienteResumen:
    ...

# Docstrings (Google style)
def my_function(param: str) -> bool:
    """Descripción breve de la función.

    Args:
        param: Descripción del parámetro.

    Returns:
        Descripción del valor de retorno.

    Raises:
        ValueError: Cuando el parámetro es inválido.
    """
    pass
```

---

## 📚 CHECKLIST DE FASE ACTUAL (Fase 0)

### Fase 0: Setup Inicial

- [x] 0.1 Git Branch Strategy
  - [x] Crear branch `v6-refactorization`
  - [ ] Configurar `.gitignore`
  - [ ] Commit inicial

- [x] 0.2 Estructura de Directorios
  - [x] Crear directorios principales
  - [x] Crear subdirectorios de domain
  - [x] Crear subdirectorios de application
  - [x] Crear subdirectorios de infrastructure
  - [x] Crear subdirectorios de presentation
  - [x] Crear directorio de plugins
  - [x] Crear directorios de tests
  - [x] Crear directorios auxiliares

- [x] 0.3 Documentación de Contexto
  - [x] `docs/V6_ARCHITECTURE.md`
  - [x] `docs/V6_ROADMAP.md`
  - [x] `docs/V6_CONTEXT.md`

- [ ] 0.4 Configuración de Entorno
  - [ ] `pyproject.toml`
  - [ ] `requirements.txt`
  - [ ] `requirements-dev.txt`
  - [ ] `.env.example`

- [ ] 0.5 Archivos de Configuración
  - [ ] `pytest.ini`
  - [ ] `mypy.ini`
  - [ ] `.gitignore`
  - [ ] `README.md`

- [ ] 0.6 Crear __init__.py
  - [ ] En todos los directorios Python

**Progreso Fase 0:** 80% (4/6 sub-tareas completas)

---

## 🎯 MÉTRICAS DE SESIÓN ACTUAL

### Archivos Creados

- `Sistema_v6/` (directorio raíz)
- `docs/V6_ARCHITECTURE.md` (8,500 líneas)
- `docs/V6_ROADMAP.md` (5,200 líneas)
- `docs/V6_CONTEXT.md` (este archivo)

### Líneas de Código

- **Total:** 0 líneas de código Python
- **Documentación:** ~15,000 líneas de Markdown

### Tiempo Invertido

- **Fase 0:** ~2 horas
- **Total proyecto:** ~2 horas

---

## 🔮 PRÓXIMA SESIÓN

### Cuando Retomes el Trabajo

1. **Leer este documento completo** (V6_CONTEXT.md)
2. **Revisar** `docs/V6_ROADMAP.md` para ver progreso
3. **Consultar** `docs/V6_ARCHITECTURE.md` si necesitas detalles de arquitectura
4. **Continuar con Fase 0.6:** Crear archivos de configuración

### Puntos de Verificación

Antes de continuar, verificar:

- [x] Branch: `v6-refactorization`
- [x] Estructura de directorios creada
- [x] 3 documentos MD creados
- [ ] Archivos de configuración creados
- [ ] Commit inicial realizado

### Si Encuentras Problemas

1. Consultar sección "Problemas Encontrados" arriba
2. Revisar documentos de arquitectura y roadmap
3. Si es un problema nuevo, agregarlo a este documento
4. Documentar la solución para futuras sesiones

---

## 📖 GLOSARIO DE TÉRMINOS

### Arquitectura

- **Domain:** Capa de lógica de negocio pura (sin dependencias)
- **Application:** Capa de casos de uso y orquestación
- **Infrastructure:** Implementaciones concretas (DB, APIs, scraping)
- **Presentation:** Interfaces de usuario (REST, MCP, CLI, Web)
- **Port:** Interface/abstracción (para inversión de dependencias)
- **Adapter:** Implementación concreta de un Port
- **Use Case:** Caso de uso que orquesta application services
- **Entity:** Modelo de dominio con identidad
- **Value Object:** Objeto inmutable sin identidad
- **DTO:** Data Transfer Object (para comunicación entre capas)
- **Plugin:** Módulo extensible que se carga dinámicamente

### Negocio

- **Expediente:** Caso judicial en el PJN
- **Actuación:** Movimiento/novedad en un expediente
- **Entrada:** Notificación o despacho en la bandeja del usuario
- **Workspace:** Directorio con archivos de un expediente
- **Manifest:** Archivo JSON con metadata del expediente
- **PJN:** Portal Judicial Nacional (Argentina)

### Fases del Sistema

- **Fase 1:** Extracción del listado completo → JSON "base"
- **Fase 2:** Filtrado por usuario → JSON "sistema"
- **Fase 3:** Creación del workspace (directorios)
- **Fase 4:** Monitoreo continuo y actualización

---

## 🔗 ENLACES ÚTILES

### Documentación Interna

- [V6_ARCHITECTURE.md](./V6_ARCHITECTURE.md) - Arquitectura completa
- [V6_ROADMAP.md](./V6_ROADMAP.md) - Progreso y tareas
- [V6_CONTEXT.md](./V6_CONTEXT.md) - Este archivo

### Documentación Externa

- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [Playwright Python](https://playwright.dev/python/)
- [Pydantic](https://docs.pydantic.dev/)
- [Clean Architecture Blog](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

### Sistema v5 (Referencia)

- `Sistema_v5/pjn/` - Código original de scraping
- `Sistema_v5/extractor_inicial/` - Flujo de extracción inicial
- `Sistema_v5/mcp_server/` - Servidor MCP original

---

## 📝 NOTAS ADICIONALES

### Convenciones de Commits

```bash
# Formato: <tipo>(<scope>): <descripción>

# Tipos:
feat     # Nueva funcionalidad
fix      # Bug fix
docs     # Documentación
style    # Formateo (no afecta código)
refactor # Refactorización
test     # Tests
chore    # Mantenimiento

# Ejemplos:
git commit -m "feat(domain): agregar ExpedienteResumen entity"
git commit -m "fix(scraping): corregir extracción de actuaciones"
git commit -m "docs: actualizar V6_ROADMAP.md con progreso"
git commit -m "test(domain): agregar tests para normalizar_texto"
```

### Workflow de Desarrollo

1. **Crear branch de feature** (si es necesario)
   ```bash
   git checkout -b v6-phase1-domain
   ```

2. **Hacer cambios incrementales**
   - Escribir código
   - Escribir tests
   - Ejecutar tests
   - Hacer commit

3. **Antes de hacer commit:**
   ```bash
   black .
   isort .
   ruff check .
   mypy .
   pytest tests/
   ```

4. **Hacer commit**
   ```bash
   git add .
   git commit -m "feat(domain): descripción"
   ```

5. **Actualizar documentos de contexto**
   - Actualizar `V6_CONTEXT.md` (este archivo)
   - Actualizar `V6_ROADMAP.md` con progreso

---

## ⚡ ATAJOS Y TIPS

### Tips de Productividad

1. **Consultar este archivo al inicio de cada sesión**
2. **Actualizar este archivo al final de cada sesión**
3. **Hacer commits frecuentes y pequeños**
4. **Escribir tests junto con el código (TDD)**
5. **Documentar decisiones importantes en V6_ARCHITECTURE.md**
6. **Actualizar roadmap cuando completes tareas**

### Atajos de Git

```bash
# Status
alias gs='git status'

# Add all
alias ga='git add .'

# Commit
alias gc='git commit -m'

# Push
alias gp='git push'

# Pull
alias gl='git pull'

# Log
alias glog='git log --oneline --graph --all'
```

### Atajos de Pytest

```bash
# Tests rápidos (sin coverage)
alias pt='pytest tests/'

# Tests con coverage
alias ptc='pytest tests/ --cov=Sistema_v6'

# Tests verbose
alias ptv='pytest tests/ -v'

# Tests con pdb on failure
alias ptd='pytest tests/ --pdb'
```

---

## 🎉 CELEBRACIONES

### Hitos Alcanzados

- [x] 2025-11-05: Estructura de proyecto creada ✨
- [x] 2025-11-05: 3 documentos de contexto completos 📚
- [ ] Fase 0 completada 🎯
- [ ] Fase 1 completada 🏗️
- [ ] Primera extracción funcional 🚀
- [ ] v6.0.0 lanzado 🎊

---

**Última actualización:** 2025-11-05 12:25
**Próxima actualización:** Al final de la sesión actual o inicio de próxima sesión
**Mantenido por:** Agente Claude Code

---

**IMPORTANTE:** Este documento debe actualizarse al final de cada sesión de trabajo para mantener contexto continuo entre sesiones.
