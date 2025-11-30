# Guía de Contribución

¡Gracias por tu interés en contribuir al Sistema v6! Esta guía te ayudará a entender el proceso de desarrollo y las mejores prácticas del proyecto.

## 📋 Tabla de Contenidos

- [Configuración del Entorno](#configuración-del-entorno)
- [Proceso de Desarrollo](#proceso-de-desarrollo)
- [Estándares de Código](#estándares-de-código)
- [Testing](#testing)
- [Pull Requests](#pull-requests)
- [Reportar Bugs](#reportar-bugs)

## 🛠️ Configuración del Entorno

### 1. Clonar el Repositorio

```bash
git clone https://github.com/USER/REPO.git
cd REPO/Sistema_v6
```

### 2. Crear Entorno Virtual

```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
# Dependencias de producción
pip install -r requirements.txt

# Dependencias de desarrollo
pip install -r requirements-dev.txt

# Instalar navegador Playwright
playwright install chromium
```

### 4. Configurar Pre-commit Hooks (Opcional)

```bash
pip install pre-commit
pre-commit install
```

## 🔄 Proceso de Desarrollo

### 1. Crear una Rama

```bash
git checkout -b feature/nombre-descriptivo
# o
git checkout -b fix/descripcion-del-bug
```

### 2. Hacer Cambios

- Escribe código limpio y bien documentado
- Sigue los estándares de código del proyecto
- Agrega tests para nuevas funcionalidades
- Actualiza la documentación si es necesario

### 3. Ejecutar Tests

Antes de hacer commit, asegúrate de que todos los tests pasen:

```bash
# Ejecutar todos los tests
pytest

# Verificar cobertura
pytest --cov=. --cov-report=term-missing

# Ejecutar linters
ruff check .
black --check .
mypy . --ignore-missing-imports
```

### 4. Hacer Commit

```bash
git add .
git commit -m "tipo: descripción breve del cambio"
```

#### Tipos de Commit

- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `style`: Cambios de formato (no afectan el código)
- `refactor`: Refactorización de código
- `test`: Agregar o modificar tests
- `chore`: Tareas de mantenimiento

Ejemplos:
```
feat: agregar endpoint para exportar expedientes a Excel
fix: corregir error en normalización de números de expediente
docs: actualizar README con instrucciones de instalación
test: agregar tests para servicio RAG
```

### 5. Push y Pull Request

```bash
git push origin feature/nombre-descriptivo
```

Luego crea un Pull Request en GitHub.

## 📏 Estándares de Código

### Python

#### Estilo de Código

- **Formateador**: [Black](https://github.com/psf/black) (configuración por defecto)
- **Linter**: [Ruff](https://github.com/astral-sh/ruff)
- **Type Checking**: [MyPy](https://mypy.readthedocs.io/)

#### Convenciones

1. **Nombres**:
   - Clases: `PascalCase`
   - Funciones/métodos: `snake_case`
   - Constantes: `UPPER_SNAKE_CASE`
   - Variables privadas: `_prefijo_con_guion_bajo`

2. **Docstrings**:
   ```python
   def funcion_ejemplo(param1: str, param2: int) -> bool:
       """
       Descripción breve de la función.

       Args:
           param1: Descripción del parámetro 1
           param2: Descripción del parámetro 2

       Returns:
           Descripción del valor de retorno

       Raises:
           ValueError: Cuando ocurre X condición
       """
       pass
   ```

3. **Type Hints**:
   - Usar type hints en todas las funciones públicas
   - Usar `Optional[T]` para valores que pueden ser None
   - Usar `List[T]`, `Dict[K, V]` para colecciones

4. **Imports**:
   ```python
   # Imports estándar
   import os
   import sys
   from pathlib import Path

   # Imports de terceros
   from fastapi import FastAPI
   from pydantic import BaseModel

   # Imports locales
   from core.domain.entities import Expediente
   from application.services import ExpedienteService
   ```

### TypeScript/React

#### Estilo de Código

- **Formateador**: Prettier
- **Linter**: ESLint

#### Convenciones

1. **Componentes**: `PascalCase`
2. **Hooks personalizados**: `useCamelCase`
3. **Constantes**: `UPPER_SNAKE_CASE`
4. **Props**: Definir interfaces con sufijo `Props`

```typescript
interface ButtonProps {
  label: string;
  onClick: () => void;
  disabled?: boolean;
}

export const Button: React.FC<ButtonProps> = ({ label, onClick, disabled = false }) => {
  return (
    <button onClick={onClick} disabled={disabled}>
      {label}
    </button>
  );
};
```

## 🧪 Testing

### Requisitos

Todos los PRs deben:
- ✅ Pasar todos los tests existentes
- ✅ Mantener o mejorar la cobertura de código (>80%)
- ✅ Incluir tests para nuevas funcionalidades
- ✅ Pasar todos los linters sin errores

### Escribir Tests

#### Tests Unitarios

```python
import pytest
from core.domain.utils import normalizar_numero_expediente

class TestNormalizacion:
    """Tests para normalización de expedientes."""

    def test_normalizar_con_padding(self):
        """Debe agregar padding de ceros."""
        assert normalizar_numero_expediente("FPA 3449/2020") == "FPA_003449_2020"

    def test_normalizar_formato_invalido(self):
        """Debe lanzar ValueError para formato inválido."""
        with pytest.raises(ValueError):
            normalizar_numero_expediente("INVALIDO")
```

#### Tests de Integración

```python
import pytest

@pytest.mark.integration
@pytest.mark.asyncio
async def test_rag_query_con_filtro():
    """Test de integración para RAG con filtro de expediente."""
    # Setup
    service = RAGService()

    # Execute
    result = await service.query(
        question="Dame un resumen",
        filter_expediente="FPA 3449/2020"
    )

    # Assert
    assert result is not None
    assert result.expediente_numero == "FPA_003449_2020"
```

#### Markers

Usa markers para categorizar tests:

```python
@pytest.mark.unit  # Test unitario
@pytest.mark.integration  # Test de integración
@pytest.mark.slow  # Test lento
@pytest.mark.rag  # Requiere servicios RAG
@pytest.mark.db  # Requiere base de datos
@pytest.mark.browser  # Requiere navegador
```

### Ejecutar Tests Localmente

```bash
# Todos los tests
pytest

# Solo tests unitarios (rápidos)
pytest -m unit

# Con cobertura
pytest --cov=. --cov-report=html

# En paralelo
pytest -n auto

# Verbose
pytest -v
```

## 🔍 Pull Requests

### Checklist antes de crear PR

- [ ] Los tests pasan localmente (`pytest`)
- [ ] La cobertura es >80% (`pytest --cov=.`)
- [ ] El código pasa los linters (`ruff check . && black .`)
- [ ] La documentación está actualizada
- [ ] Los commits siguen el formato convencional
- [ ] El PR tiene una descripción clara

### Plantilla de PR

```markdown
## Descripción

Breve descripción de los cambios realizados.

## Tipo de cambio

- [ ] Bug fix
- [ ] Nueva funcionalidad
- [ ] Breaking change
- [ ] Documentación

## Checklist

- [ ] Tests agregados/actualizados
- [ ] Documentación actualizada
- [ ] Linters pasan
- [ ] Cobertura >80%

## Screenshots (si aplica)

[Agregar screenshots si hay cambios visuales]
```

### Proceso de Revisión

1. El CI/CD ejecutará automáticamente todos los tests
2. Un reviewer revisará el código
3. Se solicitarán cambios si es necesario
4. Una vez aprobado, se hará merge a la rama principal

## 🐛 Reportar Bugs

### Antes de Reportar

1. Verifica que el bug no haya sido reportado antes
2. Asegúrate de estar usando la última versión
3. Intenta reproducir el bug en un entorno limpio

### Plantilla de Bug Report

```markdown
## Descripción del Bug

Descripción clara y concisa del bug.

## Pasos para Reproducir

1. Ir a '...'
2. Hacer clic en '....'
3. Scroll down to '....'
4. Ver error

## Comportamiento Esperado

Descripción de lo que debería pasar.

## Comportamiento Actual

Descripción de lo que realmente pasa.

## Screenshots

Si aplica, agregar screenshots.

## Entorno

- OS: [e.g. macOS 14.0]
- Python: [e.g. 3.10.5]
- Versión: [e.g. 6.0.0]

## Logs

```
[Pegar logs relevantes aquí]
```

## Contexto Adicional

Cualquier otra información relevante.
```

## 📚 Recursos Adicionales

- [Documentación de Python](https://docs.python.org/3/)
- [Guía de Black](https://black.readthedocs.io/)
- [Guía de Ruff](https://docs.astral.sh/ruff/)
- [Guía de Pytest](https://docs.pytest.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)

## 💬 Contacto

Si tienes preguntas, no dudes en:
- Abrir un issue en GitHub
- Contactar al equipo de desarrollo

---

¡Gracias por contribuir al Sistema v6! 🎉
