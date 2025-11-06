# Guía de Desarrollo - Sistema PJN v6

**Guía completa para desarrolladores que deseen contribuir o extender el sistema**

---

## 📋 Tabla de Contenidos

1. [Setup del Entorno](#setup-del-entorno)
2. [Estructura del Código](#estructura-del-código)
3. [Agregar Nuevos Componentes](#agregar-nuevos-componentes)
4. [Convenciones de Código](#convenciones-de-código)
5. [Testing](#testing)
6. [Debugging](#debugging)
7. [Troubleshooting](#troubleshooting)
8. [Workflow de Contribución](#workflow-de-contribución)

---

## 🚀 Setup del Entorno

### Requisitos del Sistema

- **Python 3.10+** (recomendado 3.11 o 3.12)
- **Git**
- **Visual Studio Code** (recomendado) o tu editor preferido
- **Terminal** con soporte UTF-8

### Instalación Completa

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

# 3. Actualizar pip
pip install --upgrade pip

# 4. Instalar dependencias de desarrollo
pip install -r requirements-dev.txt

# 5. Instalar dependencias de producción
pip install -r requirements.txt

# 6. Instalar Playwright
playwright install chromium

# 7. Instalar pre-commit hooks (opcional pero recomendado)
pre-commit install

# 8. Verificar instalación
python -c "import playwright; print('✓ Playwright OK')"
python -c "import fastapi; print('✓ FastAPI OK')"
python -c "import pydantic; print('✓ Pydantic OK')"
```

### Configuración de .env

```bash
# Copiar plantilla
cp .env.example .env

# Editar con tus credenciales
# .env
PJN_USER=tu_usuario_pjn
PJN_PASSWORD=tu_contraseña_pjn
PJN_URL=https://scw.pjn.gov.ar

# Storage
STORAGE_BASE_PATH=./data
STORAGE_PRETTY_JSON=true

# Logging
LOG_LEVEL=INFO
LOG_TO_FILE=true

# API
API_HOST=127.0.0.1
API_PORT=8000
API_RELOAD=true
```

### Configuración de VS Code

`.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": false,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": true,
    "editor.rulers": [100]
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    ".pytest_cache": true,
    ".mypy_cache": true,
    ".ruff_cache": true
  }
}
```

`.vscode/extensions.json`:

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-python.black-formatter",
    "charliermarsh.ruff",
    "streetsidesoftware.code-spell-checker",
    "eamodio.gitlens"
  ]
}
```

---

## 📁 Estructura del Código

### Visión General por Capa

```
Sistema_v6/
│
├── core/                           # 🎯 DOMAIN LAYER
│   └── domain/
│       ├── entities/               # Entidades con lógica
│       ├── value_objects/          # Objetos inmutables
│       └── utils/                  # Utilidades puras
│
├── application/                    # 📋 APPLICATION LAYER
│   ├── use_cases/                  # Casos de uso
│   └── ports/                      # Interfaces (contratos)
│
├── infrastructure/                 # 🔧 INFRASTRUCTURE LAYER
│   ├── adapters/                   # Implementaciones
│   │   ├── storage/
│   │   └── scraping/
│   ├── config/                     # Configuración
│   └── exceptions.py               # Excepciones
│
├── presentation/                   # 🖥️ PRESENTATION LAYER
│   ├── cli/                        # CLI con Click
│   ├── api/
│   │   ├── rest/                   # FastAPI
│   │   └── mcp/                    # MCP Server
│   └── dependencies.py             # DI
│
├── tests/                          # 🧪 TESTS
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── docs/                           # 📚 DOCUMENTACIÓN
├── scripts/                        # Scripts de utilidad
├── config/                         # Configs del sistema
└── data/                           # Datos generados
```

### Convenciones de Nombrado

| Tipo | Patrón | Ejemplo |
|------|--------|---------|
| **Módulos** | snake_case | `extraer_expedientes.py` |
| **Clases** | PascalCase | `ExtraerExpedientesUseCase` |
| **Funciones** | snake_case | `normalizar_fecha()` |
| **Constantes** | UPPER_SNAKE_CASE | `DEFAULT_TIMEOUT` |
| **Variables privadas** | _snake_case | `_session_file` |
| **Type hints** | PascalCase | `ExpedienteResumen` |

---

## ➕ Agregar Nuevos Componentes

### 1. Agregar Nueva Entidad

**Archivo:** `core/domain/entities/nueva_entidad.py`

```python
"""Documentación de la entidad."""

from __future__ import annotations

from dataclasses import dataclass

from pydantic import Field
from pydantic.dataclasses import dataclass as pydantic_dataclass


@pydantic_dataclass(frozen=True)
class NuevaEntidad:
    """Descripción de la entidad.

    Attributes:
        campo1: Descripción del campo
        campo2: Descripción del campo
    """

    campo1: str = Field(min_length=1)
    campo2: int = Field(gt=0)

    def algun_metodo(self) -> str:
        """Método de dominio.

        Returns:
            Resultado del método.
        """
        return f"{self.campo1}-{self.campo2}"


__all__ = ["NuevaEntidad"]
```

**Test:** `tests/unit/core/domain/entities/test_nueva_entidad.py`

```python
"""Tests para NuevaEntidad."""

import pytest
from pydantic import ValidationError

from core.domain.entities import NuevaEntidad


def test_nueva_entidad_valida():
    """Test: crear entidad con datos válidos."""
    entidad = NuevaEntidad(campo1="test", campo2=42)

    assert entidad.campo1 == "test"
    assert entidad.campo2 == 42


def test_nueva_entidad_campo1_vacio():
    """Test: campo1 no puede estar vacío."""
    with pytest.raises(ValidationError):
        NuevaEntidad(campo1="", campo2=42)


def test_nueva_entidad_campo2_negativo():
    """Test: campo2 debe ser positivo."""
    with pytest.raises(ValidationError):
        NuevaEntidad(campo1="test", campo2=-1)


def test_nueva_entidad_algun_metodo():
    """Test: método de dominio."""
    entidad = NuevaEntidad(campo1="test", campo2=42)

    result = entidad.algun_metodo()

    assert result == "test-42"
```

### 2. Agregar Nuevo Use Case

**Archivo:** `application/use_cases/nuevo_use_case.py`

```python
"""Caso de uso: descripción breve."""

from __future__ import annotations

import logging

from application.ports import IScraperPort, IStoragePort
from core.domain.entities import NuevaEntidad

logger = logging.getLogger(__name__)


class NuevoUseCase:
    """Caso de uso para [descripción].

    Este caso de uso:
    1. Hace X
    2. Hace Y
    3. Hace Z

    Attributes:
        _scraper: Port de scraping
        _storage: Port de storage
    """

    def __init__(
        self,
        scraper: IScraperPort,
        storage: IStoragePort,
    ):
        """Inicializa el caso de uso.

        Args:
            scraper: Implementación de IScraperPort
            storage: Implementación de IStoragePort
        """
        self._scraper = scraper
        self._storage = storage

    async def execute(
        self,
        *,
        param1: str,
        param2: int = 10,
    ) -> list[NuevaEntidad]:
        """Ejecuta el caso de uso.

        Args:
            param1: Descripción del parámetro
            param2: Descripción del parámetro (default: 10)

        Returns:
            Lista de entidades procesadas

        Raises:
            ValueError: Si los parámetros son inválidos
            ExtraccionError: Si falla la extracción
        """
        logger.info(f"Ejecutando caso de uso con param1={param1}")

        # 1. Validar parámetros
        if not param1:
            raise ValueError("param1 no puede estar vacío")

        # 2. Ejecutar lógica
        # ...

        # 3. Retornar resultado
        return []


__all__ = ["NuevoUseCase"]
```

**Test:** `tests/unit/application/use_cases/test_nuevo_use_case.py`

```python
"""Tests para NuevoUseCase."""

import pytest
from unittest.mock import AsyncMock

from application.use_cases import NuevoUseCase
from application.ports import IScraperPort, IStoragePort


@pytest.mark.asyncio
async def test_nuevo_use_case_exitoso():
    """Test: ejecución exitosa del use case."""
    # Arrange
    mock_scraper = AsyncMock(spec=IScraperPort)
    mock_storage = AsyncMock(spec=IStoragePort)

    use_case = NuevoUseCase(
        scraper=mock_scraper,
        storage=mock_storage,
    )

    # Act
    result = await use_case.execute(param1="test", param2=5)

    # Assert
    assert isinstance(result, list)


@pytest.mark.asyncio
async def test_nuevo_use_case_param1_vacio():
    """Test: error si param1 está vacío."""
    mock_scraper = AsyncMock(spec=IScraperPort)
    mock_storage = AsyncMock(spec=IStoragePort)

    use_case = NuevoUseCase(
        scraper=mock_scraper,
        storage=mock_storage,
    )

    with pytest.raises(ValueError, match="param1 no puede estar vacío"):
        await use_case.execute(param1="", param2=5)
```

### 3. Agregar Nuevo Adapter

**Archivo:** `infrastructure/adapters/nuevo_adapter.py`

```python
"""Adapter para [descripción]."""

from __future__ import annotations

import logging
from pathlib import Path

from application.ports import INuevoPort
from infrastructure.config import Settings

logger = logging.getLogger(__name__)


class NuevoAdapter(INuevoPort):
    """Implementación de INuevoPort usando [tecnología].

    Attributes:
        _settings: Configuración del sistema
    """

    def __init__(self, *, settings: Settings | None = None):
        """Inicializa el adapter.

        Args:
            settings: Configuración (opcional, usa defaults)
        """
        from infrastructure.config import get_settings

        if settings is None:
            settings = get_settings()

        self._settings = settings

    async def metodo_del_port(self, param: str) -> str:
        """Implementa método del port.

        Args:
            param: Descripción del parámetro

        Returns:
            Resultado del método

        Raises:
            ExtraccionError: Si falla la operación
        """
        try:
            logger.info(f"Ejecutando adapter con param={param}")

            # Implementación específica
            # ...

            return "resultado"

        except Exception as e:
            logger.exception("Error en adapter")
            raise ExtraccionError(f"Fallo en adapter: {e}") from e


__all__ = ["NuevoAdapter"]
```

### 4. Agregar Endpoint en API REST

**Archivo:** `presentation/api/rest/routes/nuevo_endpoint.py`

```python
"""Endpoints para [funcionalidad]."""

from fastapi import APIRouter, Depends, HTTPException, status

from application.use_cases import NuevoUseCase
from presentation.dependencies import get_nuevo_use_case
from presentation.api.rest.schemas import NuevoRequest, NuevoResponse

router = APIRouter(prefix="/nuevo", tags=["nuevo"])


@router.post("/", response_model=NuevoResponse, status_code=status.HTTP_200_OK)
async def ejecutar_nuevo(
    request: NuevoRequest,
    use_case: NuevoUseCase = Depends(get_nuevo_use_case),
) -> NuevoResponse:
    """Ejecuta [funcionalidad].

    Args:
        request: Datos de la petición
        use_case: Use case inyectado por DI

    Returns:
        Respuesta con el resultado

    Raises:
        HTTPException: Si ocurre un error
    """
    try:
        result = await use_case.execute(
            param1=request.param1,
            param2=request.param2,
        )

        return NuevoResponse(
            success=True,
            total=len(result),
            data=result,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno: {e}",
        )


__all__ = ["router"]
```

**Registrar en `main.py`:**

```python
# presentation/api/rest/main.py
from presentation.api.rest.routes import nuevo_endpoint

app.include_router(nuevo_endpoint.router, prefix="/api/v1")
```

### 5. Agregar Comando CLI

**Archivo:** `presentation/cli/main.py`

```python
@cli.command("nuevo-comando")
@click.option("--param1", required=True, help="Descripción del parámetro")
@click.option("--param2", type=int, default=10, help="Otro parámetro")
def nuevo_comando(param1: str, param2: int):
    """Descripción del comando.

    Ejemplo:
        python -m presentation.cli.main nuevo-comando --param1 test --param2 5
    """
    console.print("[bold blue]Ejecutando nuevo comando...[/]")

    try:
        # Crear use case con DI
        use_case = crear_nuevo_use_case()

        # Ejecutar (async)
        result = asyncio.run(use_case.execute(param1=param1, param2=param2))

        # Mostrar resultado
        console.print(f"[green]✓ Procesados {len(result)} elementos[/]")

        # Tabla con Rich (opcional)
        table = Table(title="Resultados")
        table.add_column("Campo 1")
        table.add_column("Campo 2")

        for item in result:
            table.add_row(item.campo1, str(item.campo2))

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗ Error: {e}[/]")
        raise click.Abort()
```

---

## 📝 Convenciones de Código

### Formateo

```bash
# Black - Formateo automático (line-length=100)
black .

# isort - Ordenar imports
isort .

# Ruff - Linting y formateo adicional
ruff check .
ruff format .
```

### Type Hints

**Siempre usar type hints en funciones públicas:**

```python
# ✅ BIEN
def procesar_expediente(exp: ExpedienteResumen) -> dict[str, Any]:
    """Procesa un expediente."""
    return {"numero": exp.numero}

# ❌ MAL
def procesar_expediente(exp):
    return {"numero": exp.numero}
```

### Docstrings

**Usar Google style:**

```python
def funcion_ejemplo(param1: str, param2: int = 10) -> list[str]:
    """Descripción breve de una línea.

    Descripción detallada opcional que puede ser
    de múltiples líneas.

    Args:
        param1: Descripción del parámetro 1
        param2: Descripción del parámetro 2 (default: 10)

    Returns:
        Lista de strings procesados

    Raises:
        ValueError: Si param1 está vacío
        TypeError: Si param2 no es entero

    Example:
        >>> funcion_ejemplo("test", 5)
        ['test-1', 'test-2', 'test-3', 'test-4', 'test-5']
    """
    if not param1:
        raise ValueError("param1 no puede estar vacío")

    return [f"{param1}-{i}" for i in range(1, param2 + 1)]
```

### Imports

**Orden de imports (isort):**

```python
# 1. Standard library
from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Sequence

# 2. Third-party
import click
from pydantic import Field

# 3. Local application
from application.ports import IScraperPort
from core.domain.entities import ExpedienteResumen
from infrastructure.config import Settings
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

# Niveles de log
logger.debug("Información detallada para debugging")
logger.info("Información general del flujo")
logger.warning("Algo inesperado pero no crítico")
logger.error("Error que necesita atención")
logger.exception("Error con traceback completo")  # Solo en except blocks
```

### Manejo de Errores

```python
# ✅ BIEN: Específico y con contexto
try:
    resultado = await scraper.extraer_expedientes()
except TimeoutError as e:
    logger.warning(f"Timeout durante extracción: {e}")
    raise ExtraccionError(f"Portal no responde: {e}") from e
except ValueError as e:
    logger.error(f"Datos inválidos: {e}")
    raise

# ❌ MAL: Genérico y sin contexto
try:
    resultado = await scraper.extraer_expedientes()
except Exception:
    pass  # Silenciar errores
```

---

## 🧪 Testing

### Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Solo unit tests
pytest tests/unit/ -v

# Solo integration tests
pytest tests/integration/ -v

# Con cobertura
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Tests específicos
pytest tests/unit/core/domain/entities/test_expediente.py::test_expediente_valido -v

# Tests en paralelo (más rápido)
pytest tests/ -n auto

# Tests con output detallado
pytest tests/ -vv -s
```

### Escribir Tests

**Unit Test Example:**

```python
"""Tests unitarios para [componente]."""

import pytest
from unittest.mock import AsyncMock, Mock

from core.domain.entities import ExpedienteResumen


class TestExpedienteResumen:
    """Tests para ExpedienteResumen."""

    def test_crear_expediente_valido(self):
        """Test: crear expediente con datos válidos."""
        # Arrange
        numero = "CNM 0001/2024"
        dependencia = "CNM"
        caratula = "TEST"

        # Act
        exp = ExpedienteResumen(
            numero=numero,
            dependencia=dependencia,
            caratula=caratula,
        )

        # Assert
        assert exp.numero == numero
        assert exp.dependencia == dependencia
        assert exp.caratula == caratula

    def test_expediente_inmutable(self):
        """Test: expediente es inmutable (frozen)."""
        exp = ExpedienteResumen(
            numero="CNM 0001/2024",
            dependencia="CNM",
            caratula="TEST",
        )

        with pytest.raises(AttributeError):
            exp.numero = "OTRO"  # ❌ No se puede modificar

    @pytest.mark.parametrize(
        "numero,esperado",
        [
            ("CNM 0001/2024", "CNM"),
            ("FPA 123/2023", "FPA"),
            ("CM 456/2022", "CM"),
        ],
    )
    def test_extraer_dependencia(self, numero: str, esperado: str):
        """Test: extraer dependencia del número."""
        exp = ExpedienteResumen(
            numero=numero,
            dependencia=esperado,
            caratula="TEST",
        )

        assert exp.dependencia == esperado
```

**Integration Test Example:**

```python
"""Tests de integración para scraping."""

import pytest
import os

from infrastructure.adapters.scraping import PlaywrightScraperAdapter
from infrastructure.config import Settings


@pytest.fixture
def skip_if_no_credentials():
    """Skip test si no hay credenciales."""
    if not os.getenv("PJN_USUARIO"):
        pytest.skip("No hay credenciales PJN")


@pytest.mark.asyncio
@pytest.mark.integration
async def test_extraer_expedientes_real(skip_if_no_credentials):
    """Test: extracción real del PJN."""
    adapter = PlaywrightScraperAdapter(
        login_url="https://scw.pjn.gov.ar",
    )

    expedientes = await adapter.extraer_expedientes(headless=True)

    assert isinstance(expedientes, list)
    if expedientes:
        assert expedientes[0].numero
```

### Cobertura

```bash
# Generar reporte HTML
pytest tests/ --cov=. --cov-report=html

# Abrir reporte
open htmlcov/index.html  # Mac/Linux
start htmlcov/index.html  # Windows
```

---

## 🐛 Debugging

### VS Code Launch Configuration

`.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: CLI",
      "type": "python",
      "request": "launch",
      "module": "presentation.cli.main",
      "args": ["extraer-expedientes"],
      "console": "integratedTerminal",
      "justMyCode": false
    },
    {
      "name": "Python: API",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "presentation.api.rest.main:app",
        "--reload",
        "--port",
        "8000"
      ],
      "console": "integratedTerminal"
    },
    {
      "name": "Python: Current Test",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["${file}", "-v", "-s"],
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

### Debugging con pdb

```python
# Insertar breakpoint
import pdb; pdb.set_trace()

# O con breakpoint() (Python 3.7+)
breakpoint()

# Comandos útiles en pdb:
# n - next line
# s - step into
# c - continue
# l - list code
# p variable - print variable
# pp variable - pretty print
# q - quit
```

### Logging para Debugging

```python
# Configurar logging detallado
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Ver logs de Playwright
logger = logging.getLogger("playwright")
logger.setLevel(logging.DEBUG)
```

---

## ❓ Troubleshooting

### Playwright no funciona

```bash
# Reinstalar navegador
playwright install chromium --force

# Verificar instalación
playwright --version
```

### Import errors

```bash
# Verificar que estás en el entorno virtual
which python  # Linux/Mac
where python  # Windows

# Reinstalar dependencias
pip install -r requirements.txt --force-reinstall
```

### Tests fallan

```bash
# Limpiar cache de pytest
pytest --cache-clear

# Regenerar virtualenv
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt
```

### Type checking errors

```bash
# Limpiar cache de mypy
mypy --no-incremental .

# O eliminar cache
rm -rf .mypy_cache
```

---

## 🔄 Workflow de Contribución

### 1. Fork y Clone

```bash
# Fork en GitHub UI
# Luego clone
git clone https://github.com/TU_USUARIO/sistema-pjn-v6.git
cd sistema-pjn-v6/Sistema_v6
```

### 2. Crear Rama Feature

```bash
# Crear rama descriptiva
git checkout -b feature/agregar-notificaciones-email

# O para bugfix
git checkout -b fix/corregir-parse-fecha
```

### 3. Desarrollar

```bash
# Hacer cambios
# ...

# Formatear código
black .
isort .

# Verificar con linting
ruff check .

# Ejecutar tests
pytest tests/ -v

# Type checking
mypy .
```

### 4. Commit

```bash
# Agregar cambios
git add .

# Commit con Conventional Commits
git commit -m "feat(notifications): agregar notificaciones por email

- Implementar EmailNotificationAdapter
- Agregar tests para SMTP
- Actualizar documentación

Closes #123"
```

**Tipos de commit:**
- `feat:` - Nueva funcionalidad
- `fix:` - Corrección de bug
- `docs:` - Documentación
- `style:` - Formateo (no afecta código)
- `refactor:` - Refactorización
- `test:` - Tests
- `chore:` - Tareas de mantenimiento
- `perf:` - Mejoras de performance

### 5. Push y Pull Request

```bash
# Push a tu fork
git push origin feature/agregar-notificaciones-email

# Crear PR en GitHub UI
# Descripción clara del cambio
# Referencias a issues
```

### 6. Code Review

- Responder a comentarios
- Hacer cambios solicitados
- Push a la misma rama (actualiza el PR)

### 7. Merge

- Esperar aprobación
- Squash and merge (recomendado)

---

## 📚 Recursos Adicionales

- [Clean Architecture (Uncle Bob)](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Playwright Python](https://playwright.dev/python/)
- [Pydantic V2](https://docs.pydantic.dev/latest/)
- [Click Documentation](https://click.palletsprojects.com/)
- [Pytest Documentation](https://docs.pytest.org/)

---

**Versión:** 1.0
**Última actualización:** 2025-11-05
**Autor:** Equipo Sistema PJN
