# Tests - Sistema PJN v6

Este directorio contiene los tests automatizados para el Sistema PJN v6.

## 📋 Estructura

```
tests/
├── __init__.py
├── conftest.py                  # Configuración de pytest
├── test_config_router.py        # Tests del router de configuración
└── test_config_schemas.py       # Tests de schemas de configuración
```

## 🧪 Tests Implementados

### Backend Tests

#### `test_config_router.py`
Tests para el router de configuración (`/api/v1/config/sistema`):

- ✅ **test_get_config_sistema_success**: Verifica que GET retorna la configuración completa
- ✅ **test_put_config_sistema_browser_success**: Actualización de configuración del navegador
- ✅ **test_put_config_sistema_monitoreo_success**: Actualización de configuración de monitoreo
- ✅ **test_put_config_sistema_mcp_success**: Actualización de configuración de MCP
- ✅ **test_put_config_sistema_storage_success**: Actualización de configuración de Storage
- ✅ **test_put_config_sistema_partial_update**: Actualización parcial de configuración
- ✅ **test_put_config_sistema_validation_error_timeout_too_low**: Validación de timeout mínimo
- ✅ **test_put_config_sistema_validation_error_intervalo_negativo**: Validación de intervalo negativo
- ✅ **test_put_config_sistema_validation_error_puerto_invalido**: Validación de puerto inválido

**Total: 10 tests**

#### `test_config_schemas.py`
Tests para schemas Pydantic de configuración:

**BrowserConfigSchema:**
- ✅ test_valid_browser_config
- ✅ test_browser_config_with_null_user_agent

**MonitoreoConfigSchema:**
- ✅ test_valid_monitoreo_config_basico
- ✅ test_valid_monitoreo_config_avanzado

**ScrapingConfigSchema:**
- ✅ test_valid_scraping_config
- ✅ test_scraping_config_sin_limite_paginas

**MCPConfigSchema:**
- ✅ test_valid_mcp_config
- ✅ test_mcp_config_mode_http

**StorageConfigSchema:**
- ✅ test_valid_storage_config

**SystemConfigResponse:**
- ✅ test_valid_system_config_response

**SystemConfigUpdateRequest:**
- ✅ test_update_request_solo_browser
- ✅ test_update_request_multiple_sections
- ✅ test_update_request_all_null

**Total: 13 tests**

## 🚀 Ejecutar Tests

### Requisitos previos

```bash
cd Sistema_v6
pip install -r requirements-dev.txt
```

### Ejecutar todos los tests

```bash
pytest tests/
```

### Ejecutar tests específicos

```bash
# Solo tests del router
pytest tests/test_config_router.py -v

# Solo tests de schemas
pytest tests/test_config_schemas.py -v

# Ejecutar un test específico
pytest tests/test_config_router.py::TestConfigRouter::test_get_config_sistema_success -v
```

### Ejecutar con cobertura

```bash
pytest tests/ --cov=presentation.api.rest --cov-report=html
```

Luego abrir `htmlcov/index.html` en el navegador.

## 📊 Cobertura de Tests

### Backend (Configuración)

| Componente | Cobertura | Tests |
|------------|-----------|-------|
| config.py (router) | ~90% | 10 tests |
| config_schemas.py | 100% | 13 tests |

### Características Testeadas

✅ **Lectura de configuración**
- GET endpoint retorna estructura correcta
- Todos los campos presentes
- Valores correctos desde .env

✅ **Actualización de configuración**
- PUT endpoint acepta actualizaciones
- Actualización completa funciona
- Actualización parcial funciona
- Persiste cambios en .env

✅ **Validaciones**
- Timeouts mínimos
- Valores negativos rechazados
- Puertos fuera de rango rechazados
- Campos opcionales permitidos

✅ **Schemas Pydantic**
- Validación de tipos
- Valores por defecto
- Campos opcionales/nullable
- Estructura completa de respuesta

## 🔧 Configuración de Fixtures

### `temp_env_file`
Fixture que crea un archivo `.env` temporal para tests, con valores de prueba.
Se ejecuta antes de cada test y restaura el `.env` original al finalizar.

### `client`
Cliente de pruebas de FastAPI (`TestClient`) para hacer peticiones HTTP a la API.

## 📝 Notas

- Los tests usan un archivo `.env` temporal para no afectar la configuración real
- Se hace backup y restore del `.env` original automáticamente
- Todos los tests son independientes y pueden ejecutarse en cualquier orden
- Se usa `pytest` como framework de testing
- Los tests siguen el patrón AAA (Arrange, Act, Assert)

## 🐛 Debugging

Para ejecutar tests con output detallado:

```bash
pytest tests/ -v -s
```

Para ejecutar solo tests que fallaron:

```bash
pytest tests/ --lf
```

Para ejecutar hasta el primer fallo:

```bash
pytest tests/ -x
```

## 📈 Próximos Tests a Implementar

- [ ] Tests E2E (integración completa)
- [ ] Tests de frontend (componentes React)
- [ ] Tests de performance
- [ ] Tests de carga
- [ ] Tests de seguridad

## 🤝 Contribuir

Para agregar nuevos tests:

1. Crear archivo `test_*.py` en este directorio
2. Seguir convenciones de naming (test_*)
3. Usar fixtures existentes cuando sea posible
4. Documentar qué se está testeando
5. Ejecutar todos los tests antes de commit

## 📚 Referencias

- [pytest documentation](https://docs.pytest.org/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pydantic validation](https://docs.pydantic.dev/latest/concepts/validation/)
