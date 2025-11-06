# Scripts de Ejemplo - Sistema PJN v6

Este directorio contiene scripts de ejemplo que demuestran cómo usar el Sistema PJN v6 de diferentes formas.

## Contenido

### 1. `ejemplo_completo.py`

Demuestra el flujo completo de 4 fases del sistema:

1. **Extracción**: Obtiene expedientes del PJN → JSON "base"
2. **Filtrado**: Filtra por selección → JSON "sistema"
3. **Workspaces**: Crea directorios organizados
4. **Monitoreo**: Detecta cambios periódicamente

**Uso:**
```bash
python scripts/ejemplo_completo.py
```

**Nota:** Crea datos de ejemplo si el scraping no está implementado.

### 2. `ejemplo_api_rest.py`

Muestra cómo consumir la API REST usando `requests`.

**Prerrequisitos:**
- Instalar: `pip install requests`
- Servidor corriendo: `uvicorn presentation.api.rest.main:app --reload`

**Uso:**
```bash
python scripts/ejemplo_api_rest.py
```

**Endpoints demostrados:**
- `GET /api/v1/health` - Health check
- `GET /api/v1/expedientes` - Listar expedientes
- `GET /api/v1/expedientes/{numero}` - Obtener expediente
- `POST /api/v1/expedientes/extraer` - Extraer del PJN
- `POST /api/v1/expedientes/filtrar` - Filtrar expedientes
- `POST /api/v1/workspaces/crear` - Crear workspaces
- `POST /api/v1/monitoreo/iniciar` - Monitorear cambios

### 3. `ejemplo_uso_cli.sh`

Script bash con ejemplos de comandos del CLI.

**Uso:**
```bash
bash scripts/ejemplo_uso_cli.sh
```

**Comandos demostrados:**
- `pjn --help` - Ayuda general
- `pjn info` - Información del sistema
- `pjn extraer` - Extraer expedientes
- `pjn filtrar` - Filtrar expedientes
- `pjn workspace` - Crear workspaces
- `pjn monitorear` - Monitorear cambios

## Requisitos

Todos los scripts requieren:

1. **Python 3.10+** instalado
2. **Dependencias** instaladas:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configuración** en `.env` (copiar desde `.env.example`):
   ```bash
   cp .env.example .env
   # Editar .env con tus credenciales
   ```

## Ejecución desde raíz del proyecto

Todos los scripts deben ejecutarse desde el directorio raíz de Sistema_v6:

```bash
cd Sistema_v6

# Ejemplo completo
python scripts/ejemplo_completo.py

# API REST (requiere servidor corriendo)
python scripts/ejemplo_api_rest.py

# CLI
bash scripts/ejemplo_uso_cli.sh
```

## Limitaciones actuales

**Scraping no completamente implementado:**
- Los scripts relacionados con extracción del PJN mostrarán `NotImplementedError`
- Se puede usar datos de ejemplo para demostración
- Migración pendiente desde Sistema_v5 (~2,350 líneas)

**Funcionalidad disponible sin scraping:**
- ✓ Filtrado de expedientes existentes
- ✓ Creación de workspaces
- ✓ Listado y consultas
- ✗ Extracción del portal PJN (pendiente)
- ✗ Monitoreo de cambios reales (pendiente)

## Más información

- **Documentación completa**: `docs/`
- **Arquitectura**: `docs/V6_ARCHITECTURE.md`
- **API Docs**: http://localhost:8000/docs (con servidor corriendo)
- **CLI Help**: `python -m presentation.cli.main --help`

## Contribuir

Para agregar nuevos scripts de ejemplo:

1. Crear archivo en `scripts/`
2. Agregar shebang: `#!/usr/bin/env python3`
3. Documentar uso en este README
4. Incluir logging para seguimiento
5. Manejar `NotImplementedError` cuando corresponda
