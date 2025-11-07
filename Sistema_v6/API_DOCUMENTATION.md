# API Documentation - Sistema PJN v6

> **Documentación técnica completa de la API REST**

---

## 📋 Tabla de Contenidos

1. [Introducción](#introducción)
2. [Endpoints de Configuración](#endpoints-de-configuración)
3. [Schemas](#schemas)
4. [Ejemplos de Uso](#ejemplos-de-uso)
5. [Códigos de Error](#códigos-de-error)
6. [Validaciones](#validaciones)

---

## Introducción

La API REST de Sistema PJN v6 expone endpoints para gestionar la configuración del sistema de forma programática.

### Base URL

```
http://localhost:8000/api/v1
```

### Autenticación

Todos los endpoints requieren autenticación JWT:

```bash
Authorization: Bearer <token>
```

### Content-Type

```
Content-Type: application/json
```

---

## Endpoints de Configuración

### GET /config/sistema

Obtiene toda la configuración actual del sistema.

#### Request

```http
GET /api/v1/config/sistema
Authorization: Bearer <token>
```

#### Response

**Status:** `200 OK`

```json
{
  "browser": {
    "headless": true,
    "timeout_ms": 30000,
    "navigation_timeout_ms": 60000,
    "user_agent": null
  },
  "monitoreo": {
    "intervalo_segundos": 1800,
    "dias_actividad": 30,
    "max_reintentos": 3,
    "notificar_cambios": true,
    "descargar_archivos": true,
    "intervalos_laboral_expedientes": null,
    "intervalos_laboral_entradas": null,
    "intervalos_no_laboral_expedientes": null,
    "intervalos_no_laboral_entradas": null,
    "dias_laborales": ["lunes", "martes", "miercoles", "jueves", "viernes"],
    "hora_inicio": "08:00",
    "hora_fin": "18:00"
  },
  "scraping": {
    "timeout_default": 8000,
    "timeout_login": 60000,
    "timeout_descarga": 30000,
    "max_paginas_expedientes": 200,
    "max_reintentos_descarga": 3
  },
  "mcp": {
    "habilitar": true,
    "puerto": 5000,
    "mode": "stdio",
    "workspace_path": "workspace",
    "server_name": "sintaxis-actuaciones-v6",
    "enable_pdf_extraction": true,
    "enable_full_text_search": true,
    "enable_statistics": true,
    "max_pdf_pages": 100,
    "max_pdf_size_mb": 50
  },
  "storage": {
    "base_path": "data",
    "json_base_file": "expedientes_base.json",
    "json_sistema_file": "expedientes_sistema.json",
    "workspaces_dir": "workspaces",
    "downloads_dir": "descargas",
    "pretty_json": true,
    "ensure_ascii": false
  }
}
```

#### Errores

- `500 Internal Server Error`: Error al leer configuración

---

### PUT /config/sistema

Actualiza la configuración del sistema.

#### Request

**Actualización parcial:** Solo envía las secciones que quieres actualizar.

```http
PUT /api/v1/config/sistema
Authorization: Bearer <token>
Content-Type: application/json
```

**Body (Ejemplo - Solo Browser):**

```json
{
  "browser": {
    "headless": false,
    "timeout_ms": 45000,
    "navigation_timeout_ms": 90000,
    "user_agent": "Custom User Agent"
  }
}
```

**Body (Ejemplo - Múltiples secciones):**

```json
{
  "browser": {
    "headless": true,
    "timeout_ms": 30000,
    "navigation_timeout_ms": 60000,
    "user_agent": null
  },
  "monitoreo": {
    "intervalo_segundos": 3600,
    "dias_actividad": 60,
    "max_reintentos": 5,
    "notificar_cambios": false,
    "descargar_archivos": true,
    "intervalos_laboral_expedientes": 10,
    "intervalos_laboral_entradas": 15,
    "intervalos_no_laboral_expedientes": 60,
    "intervalos_no_laboral_entradas": 30,
    "dias_laborales": ["lunes", "martes", "miercoles"],
    "hora_inicio": "09:00",
    "hora_fin": "17:00"
  }
}
```

#### Response

**Status:** `200 OK`

```json
{
  "success": true,
  "message": "Configuración actualizada correctamente. Reinicia el servidor para aplicar cambios.",
  "updates": {
    "BROWSER_HEADLESS": "false",
    "BROWSER_TIMEOUT_MS": "45000",
    "BROWSER_NAVIGATION_TIMEOUT_MS": "90000",
    "BROWSER_USER_AGENT": "Custom User Agent"
  }
}
```

#### Errores

**400 Bad Request** - Validación fallida:

```json
{
  "detail": "browser.timeout_ms debe ser >= 1000ms"
}
```

**500 Internal Server Error** - Error al actualizar:

```json
{
  "detail": "Error al actualizar configuración: <detalle>"
}
```

---

## Schemas

### BrowserConfigSchema

```python
{
  "headless": bool,                    # Modo headless (sin interfaz)
  "timeout_ms": int,                   # Timeout general (>= 1000ms)
  "navigation_timeout_ms": int,        # Timeout navegación (>= 1000ms)
  "user_agent": str | null            # User agent personalizado
}
```

**Validaciones:**
- `timeout_ms >= 1000`
- `navigation_timeout_ms >= 1000`

---

### MonitoreoConfigSchema

```python
{
  "intervalo_segundos": int,                        # 0 - 86400
  "dias_actividad": int,                            # 1 - 365
  "max_reintentos": int,                            # 1 - 10
  "notificar_cambios": bool,
  "descargar_archivos": bool,

  # Modo avanzado (opcional)
  "intervalos_laboral_expedientes": int | null,     # 1 - 1440
  "intervalos_laboral_entradas": int | null,        # 1 - 1440
  "intervalos_no_laboral_expedientes": int | null,  # 1 - 1440
  "intervalos_no_laboral_entradas": int | null,     # 1 - 1440
  "dias_laborales": list[str],                      # ["lunes", ...]
  "hora_inicio": str,                               # "HH:MM"
  "hora_fin": str                                   # "HH:MM"
}
```

**Validaciones:**
- `intervalo_segundos >= 0`
- `dias_actividad >= 1` and `<= 365`
- `max_reintentos >= 1` and `<= 10`
- `intervalos_*` >= 1 and `<= 1440` (si no null)
- `hora_inicio` y `hora_fin` formato HH:MM

---

### ScrapingConfigSchema

```python
{
  "timeout_default": int,              # >= 1000ms
  "timeout_login": int,                # >= 1000ms
  "timeout_descarga": int,             # >= 1000ms
  "max_paginas_expedientes": int | null,  # 1 - 10000 o null
  "max_reintentos_descarga": int       # 1 - 10
}
```

**Validaciones:**
- `timeout_* >= 1000`
- `max_paginas_expedientes >= 1` (si no null)
- `max_reintentos_descarga >= 1` and `<= 10`

---

### MCPConfigSchema

```python
{
  "habilitar": bool,
  "puerto": int,                       # 1 - 65535
  "mode": "stdio" | "http",
  "workspace_path": str,
  "server_name": str,
  "enable_pdf_extraction": bool,
  "enable_full_text_search": bool,
  "enable_statistics": bool,
  "max_pdf_pages": int,                # >= 1
  "max_pdf_size_mb": int               # >= 1
}
```

**Validaciones:**
- `puerto >= 1` and `<= 65535`
- `mode` in ["stdio", "http"]
- `max_pdf_pages >= 1`
- `max_pdf_size_mb >= 1`

---

### StorageConfigSchema

```python
{
  "base_path": str,
  "json_base_file": str,
  "json_sistema_file": str,
  "workspaces_dir": str,
  "downloads_dir": str,
  "pretty_json": bool,
  "ensure_ascii": bool
}
```

**Validaciones:**
- Todos los campos string deben tener `len() >= 1`

---

## Ejemplos de Uso

### Ejemplo 1: Cambiar a modo visible (no headless)

```bash
curl -X PUT http://localhost:8000/api/v1/config/sistema \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "browser": {
      "headless": false,
      "timeout_ms": 30000,
      "navigation_timeout_ms": 60000,
      "user_agent": null
    }
  }'
```

---

### Ejemplo 2: Activar modo avanzado de monitoreo

```bash
curl -X PUT http://localhost:8000/api/v1/config/sistema \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "monitoreo": {
      "intervalo_segundos": 0,
      "dias_actividad": 30,
      "max_reintentos": 3,
      "notificar_cambios": true,
      "descargar_archivos": true,
      "intervalos_laboral_expedientes": 10,
      "intervalos_laboral_entradas": 15,
      "intervalos_no_laboral_expedientes": 60,
      "intervalos_no_laboral_entradas": 30,
      "dias_laborales": ["lunes", "martes", "miercoles", "jueves", "viernes"],
      "hora_inicio": "08:00",
      "hora_fin": "18:00"
    }
  }'
```

---

### Ejemplo 3: Aumentar timeouts para PJN lento

```bash
curl -X PUT http://localhost:8000/api/v1/config/sistema \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "browser": {
      "headless": true,
      "timeout_ms": 60000,
      "navigation_timeout_ms": 120000,
      "user_agent": null
    },
    "scraping": {
      "timeout_default": 15000,
      "timeout_login": 90000,
      "timeout_descarga": 60000,
      "max_paginas_expedientes": 200,
      "max_reintentos_descarga": 3
    }
  }'
```

---

### Ejemplo 4: Deshabilitar MCP Server

```bash
curl -X PUT http://localhost:8000/api/v1/config/sistema \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "mcp": {
      "habilitar": false,
      "puerto": 5000,
      "mode": "stdio",
      "workspace_path": "workspace",
      "server_name": "sintaxis-actuaciones-v6",
      "enable_pdf_extraction": true,
      "enable_full_text_search": true,
      "enable_statistics": true,
      "max_pdf_pages": 100,
      "max_pdf_size_mb": 50
    }
  }'
```

---

### Ejemplo 5: Obtener configuración actual

```bash
curl -X GET http://localhost:8000/api/v1/config/sistema \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## Códigos de Error

| Código | Descripción | Solución |
|--------|-------------|----------|
| `200` | OK | Operación exitosa |
| `400` | Bad Request | Validación fallida, verifica los valores |
| `401` | Unauthorized | Token JWT inválido o expirado |
| `500` | Internal Server Error | Error del servidor, verifica logs |

---

## Validaciones

### Validaciones de Browser

```python
# Timeouts mínimos
timeout_ms >= 1000  # Error: "browser.timeout_ms debe ser >= 1000ms"
navigation_timeout_ms >= 1000  # Error: "browser.navigation_timeout_ms debe ser >= 1000ms"
```

---

### Validaciones de Monitoreo

```python
# Intervalo
intervalo_segundos >= 0  # Error: "monitoreo.intervalo_segundos debe ser >= 0"

# Días de actividad
dias_actividad >= 1  # Error: "monitoreo.dias_actividad debe ser >= 1"

# Reintentos
max_reintentos >= 1  # Error: "monitoreo.max_reintentos debe ser >= 1"
```

---

### Validaciones de Scraping

```python
# Timeouts
timeout_default >= 1000  # Error: "scraping.timeout_default debe ser >= 1000ms"

# Reintentos
max_reintentos_descarga >= 1  # Error: "scraping.max_reintentos_descarga debe ser >= 1"
```

---

### Validaciones de MCP

```python
# Puerto
1 <= puerto <= 65535  # Error: "mcp.puerto debe estar entre 1 y 65535"

# Límites PDF
max_pdf_pages >= 1  # Error: "mcp.max_pdf_pages debe ser >= 1"
max_pdf_size_mb >= 1  # Error: "mcp.max_pdf_size_mb debe ser >= 1"
```

---

## Persistencia

Los cambios se persisten automáticamente en el archivo `.env` del sistema:

```bash
Sistema_v6/.env
```

### Formato de variables en .env

```bash
# Browser
BROWSER_HEADLESS=true
BROWSER_TIMEOUT_MS=30000
BROWSER_NAVIGATION_TIMEOUT_MS=60000
BROWSER_USER_AGENT=

# Monitoreo
MONITOREO_INTERVALO_SEGUNDOS=1800
MONITOREO_DIAS_ACTIVIDAD=30
MONITOREO_MAX_REINTENTOS=3
MONITOREO_NOTIFICAR_CAMBIOS=true
MONITOREO_DESCARGAR_ARCHIVOS=true
MONITOREO_DIAS_LABORALES=lunes,martes,miercoles,jueves,viernes
MONITOREO_HORA_INICIO=08:00
MONITOREO_HORA_FIN=18:00

# Scraping
SCRAPING_TIMEOUT_DEFAULT=8000
SCRAPING_TIMEOUT_LOGIN=60000
SCRAPING_TIMEOUT_DESCARGA=30000
SCRAPING_MAX_PAGINAS_EXPEDIENTES=200
SCRAPING_MAX_REINTENTOS_DESCARGA=3

# MCP
MCP_HABILITAR=true
MCP_PUERTO=5000
MCP_MODE=stdio
MCP_WORKSPACE_PATH=workspace
MCP_SERVER_NAME=sintaxis-actuaciones-v6
MCP_ENABLE_PDF_EXTRACTION=true
MCP_ENABLE_FULL_TEXT_SEARCH=true
MCP_ENABLE_STATISTICS=true
MCP_MAX_PDF_PAGES=100
MCP_MAX_PDF_SIZE_MB=50

# Storage
STORAGE_BASE_PATH=data
STORAGE_JSON_BASE_FILE=expedientes_base.json
STORAGE_JSON_SISTEMA_FILE=expedientes_sistema.json
STORAGE_WORKSPACES_DIR=workspaces
STORAGE_DOWNLOADS_DIR=descargas
STORAGE_PRETTY_JSON=true
STORAGE_ENSURE_ASCII=false
```

---

## Implementación del Backend

### Ubicación del Código

```
Sistema_v6/
├── presentation/api/rest/
│   ├── routers/
│   │   └── config.py              # Router de configuración
│   └── schemas/
│       └── config_schemas.py      # Schemas Pydantic
└── infrastructure/
    └── config/
        └── settings.py             # Settings con Pydantic
```

### Router Implementation

```python
# presentation/api/rest/routers/config.py

from fastapi import APIRouter, HTTPException
from infrastructure.config import get_settings
from presentation.api.rest.schemas import (
    SystemConfigResponse,
    SystemConfigUpdateRequest,
    ConfigUpdateResponse
)

router = APIRouter(prefix="/config", tags=["configuracion"])

@router.get("/sistema", response_model=SystemConfigResponse)
async def obtener_configuracion_sistema():
    """Obtiene toda la configuración del sistema."""
    settings = get_settings()
    # ... retorna config completa

@router.put("/sistema", response_model=ConfigUpdateResponse)
async def actualizar_configuracion_sistema(config: SystemConfigUpdateRequest):
    """Actualiza la configuración del sistema y la persiste en .env."""
    # ... valida y actualiza .env
```

---

## Testing

Los endpoints están completamente testeados:

```bash
# Ejecutar tests
pytest Sistema_v6/tests/test_config_router.py -v

# Tests disponibles:
# - test_get_config_sistema_success
# - test_put_config_sistema_browser_success
# - test_put_config_sistema_monitoreo_success
# - test_put_config_sistema_validation_error_timeout_too_low
# - test_put_config_sistema_validation_error_intervalo_negativo
# - test_put_config_sistema_validation_error_puerto_invalido
# ... y más
```

Ver [Tests Documentation](./tests/README.md) para más detalles.

---

## OpenAPI / Swagger

La documentación interactiva está disponible en:

```
http://localhost:8000/docs
```

O ReDoc en:

```
http://localhost:8000/redoc
```

---

## Changelog

### v6.0.0 (2025-11-06)
- ✅ Endpoints de configuración implementados
- ✅ GET /config/sistema
- ✅ PUT /config/sistema
- ✅ Validaciones completas
- ✅ Persistencia en .env
- ✅ Tests completos (23 tests backend)

---

## Referencias

- [Manual de Usuario](./MANUAL_CONFIGURACION.md)
- [Tests Documentation](./tests/README.md)
- [Frontend Components](./frontend/src/components/settings/README.md)
- [README Principal](./README.md)

---

**Versión:** 6.0.0
**Última actualización:** 2025-11-06
**Autor:** Sistema sintaXis
