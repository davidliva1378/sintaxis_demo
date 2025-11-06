# 🚀 Guía de Uso - Sistema PJN v6

Esta guía te muestra cómo ejecutar y usar el Sistema PJN v6 de forma práctica.

## ✅ Verificación Rápida

El sistema funciona correctamente si este comando muestra la información:

```bash
cd "F:\RESPALDO DAVID\Sistema_v2\Sistema_v6"
python -m presentation.cli.main info
```

## 📋 Formas de Ejecutar el Sistema

### 1️⃣ Script de Ejemplo Completo (Recomendado)

La forma más simple de ver todo el sistema en acción:

```bash
cd "F:\RESPALDO DAVID\Sistema_v2\Sistema_v6"
python ejecutar_ejemplo.py
```

**Qué hace:**
- ✅ Crea 3 expedientes de ejemplo en `data/expedientes_base.json`
- ✅ Filtra 2 expedientes → `data/expedientes_sistema.json`
- ✅ Crea workspaces organizados en `data/workspaces/`
- ✅ Muestra logging detallado de cada fase

**Resultado:** Archivos y directorios creados automáticamente.

---

### 2️⃣ CLI - Comandos Individuales

#### Ver información del sistema:
```bash
python -m presentation.cli.main info
```

#### Comandos disponibles:

**a) Extraer expedientes del PJN:**
```bash
python -m presentation.cli.main extraer --usuario TU_CUIL --password TU_PASSWORD
```
⚠️ Requiere credenciales y scraping implementado.

**b) Filtrar expedientes:**
```bash
python -m presentation.cli.main filtrar \
  --origen data/expedientes_base.json \
  --destino data/expedientes_sistema.json \
  --numeros "CNM 0001/2024" "CNM 0003/2024" \
  --activos
```

**c) Crear workspaces:**
```bash
python -m presentation.cli.main workspace \
  --sistema data/expedientes_sistema.json \
  --workspaces-dir data/workspaces
```

**d) Monitorear cambios:**
```bash
python -m presentation.cli.main monitorear \
  --sistema data/expedientes_sistema.json \
  --intervalo 60 \
  --notificar
```
⚠️ Requiere scraping implementado.

---

### 3️⃣ API REST

#### Iniciar servidor:
```bash
cd "F:\RESPALDO DAVID\Sistema_v2\Sistema_v6"
uvicorn presentation.api.rest.main:app --reload
```

**Acceso:**
- API: http://localhost:8000
- Documentación interactiva: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

#### Ejemplos de uso:

**Health check:**
```bash
curl http://localhost:8000/api/v1/health
```

**Listar expedientes:**
```bash
curl http://localhost:8000/api/v1/expedientes
```

**Obtener un expediente:**
```bash
curl http://localhost:8000/api/v1/expedientes/CNM%200001/2024
```

**Script de ejemplo Python:**
```bash
# Instalar requests si no lo tienes
pip install requests

# Ejecutar ejemplo
python scripts/ejemplo_api_rest.py
```

---

### 4️⃣ MCP Server (Para LLMs)

El MCP Server permite que Claude Desktop, Cline u otros clientes MCP interactúen con el sistema.

#### Iniciar servidor:
```bash
python -m presentation.api.mcp.server
```

El servidor escucha en **modo stdio** (entrada/salida estándar).

**Herramientas disponibles:**
- `extraer_expedientes` - Extrae del PJN
- `filtrar_expedientes` - Filtra expedientes
- `listar_expedientes` - Lista todos
- `obtener_expediente` - Obtiene uno específico
- `crear_workspaces` - Crea directorios
- `monitorear_expedientes` - Detecta cambios

---

## 📁 Estructura de Datos Creada

Después de ejecutar el ejemplo, tendrás:

```
Sistema_v6/
└── data/
    ├── expedientes_base.json       # JSON "base" con todos los expedientes
    ├── expedientes_sistema.json    # JSON "sistema" con filtrados
    └── workspaces/                 # Workspaces organizados
        ├── CNM_0001_2024/
        │   └── archivos/
        └── CNM_0003_2024/
            └── archivos/
```

### Contenido de los JSON:

**expedientes_base.json:**
```json
[
  {
    "numero": "CNM 0001/2024",
    "dependencia": "Juzgado Federal 1",
    "caratula": "CASO EJEMPLO A C/ B S/ MATERIA",
    "situacion": "En tramite",
    "ultima_actuacion": "2024-11-05"
  },
  ...
]
```

---

## ⚙️ Configuración

### Archivo `.env`

Copia el ejemplo y personaliza:

```bash
cp .env.example .env
# Edita .env con tu editor favorito
```

**Configuración importante:**
```env
# Credenciales PJN
PJN_USUARIO=tu_cuil
PJN_PASSWORD=tu_password

# Rutas
BASE_PATH=F:\RESPALDO DAVID\Sistema_v2\Sistema_v6\data

# Logging
LOG_LEVEL=INFO
```

---

## 🔍 Verificar que Todo Funciona

### Test básico:
```bash
python ejecutar_ejemplo.py
```

✅ **Debe mostrar:**
```
=== Iniciando ejemplo completo Sistema PJN v6 ===
=== FASE 1: Extraccion de expedientes ===
Archivo de ejemplo creado: data\expedientes_base.json
Total expedientes: 3

=== FASE 2: Filtrado de expedientes ===
Filtrado exitoso: 2 expedientes seleccionados

=== FASE 3: Creacion de workspaces ===
Workspaces creados: 2

=== Ejemplo completo finalizado ===
```

### Verificar archivos creados:
```bash
# Windows
dir data

# Linux/Mac
ls -la data/
```

---

## ⚠️ Limitaciones Actuales

### Funcionalidad Completa:
- ✅ Filtrado de expedientes
- ✅ Creación de workspaces
- ✅ Listado y consultas
- ✅ Arquitectura completa
- ✅ CLI, API REST y MCP

### Pendiente (Scraping):
- ⏳ Extracción real del portal PJN
- ⏳ Monitoreo de cambios reales
- ⏳ Descarga de archivos

**Motivo:** Migración de ~2,350 líneas de scraping desde Sistema_v5 pendiente.

**Solución temporal:** Todos los ejemplos usan datos de prueba.

---

## 🐛 Solución de Problemas

### Error: "No module named 'application'"

**Solución:** Ejecuta desde el directorio correcto:
```bash
cd "F:\RESPALDO DAVID\Sistema_v2\Sistema_v6"
python ejecutar_ejemplo.py
```

### Error: "ModuleNotFoundError: No module named 'click'"

**Solución:** Instala dependencias:
```bash
pip install -r requirements.txt
```

### Error de codificación Unicode en Windows

**Solución:** Usa el script de ejemplo en lugar del CLI directo:
```bash
python ejecutar_ejemplo.py  # ✅ Funciona
python -m presentation.cli.main --help  # ❌ Puede fallar
```

### API REST no inicia

**Solución:** Instala uvicorn:
```bash
pip install uvicorn
```

---

## 📚 Más Información

- **Arquitectura completa:** `docs/V6_ARCHITECTURE.md`
- **Roadmap del proyecto:** `docs/V6_ROADMAP.md`
- **README principal:** `README.md`
- **Scripts de ejemplo:** `scripts/README.md`

---

## 🎯 Flujo Típico de Uso

### 1. Desarrollo / Testing:
```bash
# Ejecutar ejemplo completo
python ejecutar_ejemplo.py

# Ver archivos creados
ls data/
```

### 2. Uso con API REST:
```bash
# Terminal 1: Iniciar API
uvicorn presentation.api.rest.main:app --reload

# Terminal 2: Consumir API
python scripts/ejemplo_api_rest.py
```

### 3. Uso Programático:
```python
import sys
from pathlib import Path

# Agregar Sistema_v6 al path
sys.path.insert(0, str(Path("F:/RESPALDO DAVID/Sistema_v2/Sistema_v6")))

from infrastructure.di_container import get_container

# Obtener container
container = get_container()

# Usar repositorios
repo = container.expediente_repo
expedientes = await repo.obtener_todos()
print(f"Total: {len(expedientes)}")
```

---

## 📞 Soporte

Si tienes problemas:

1. Verifica que Python 3.10+ esté instalado
2. Instala dependencias: `pip install -r requirements.txt`
3. Ejecuta el script de ejemplo: `python ejecutar_ejemplo.py`
4. Revisa logs en `data/sistema_pjn.log`

---

**Versión del sistema:** 6.0.0
**Última actualización:** 2024-11-05
