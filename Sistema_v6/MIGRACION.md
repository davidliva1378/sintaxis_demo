# Migración a Sistema_v6

Documentación del proceso de migración de módulos al directorio Sistema_v6.

## 📋 Resumen de la Migración

**Fecha**: 2025-11-07
**Objetivo**: Consolidar todos los módulos necesarios en un directorio unificado Sistema_v6

## 🔄 Módulos Migrados

### 1. Módulos de `core/` → `Sistema_v6/`

| Origen | Destino | Descripción |
|--------|---------|-------------|
| `core/flujo_inicial/` | `Sistema_v6/extractor_inicial/` | Extracción incremental |
| `core/gestion_expedientes/` | `Sistema_v6/gestion_expedientes/` | Comparación de expedientes |
| `core/utils/` | `Sistema_v6/utils/` | Utilidades (logging, etc.) |
| `core/modulos_monitor/expedientes_modular/` | `Sistema_v6/pjn/monitor/` | Monitoreo de expedientes |

### 2. Módulos de `web/` → `Sistema_v6/pjn/`

| Origen | Destino | Descripción |
|--------|---------|-------------|
| `web/auto_login.py` | `Sistema_v6/pjn/auto_login.py` | Autenticación PJN |
| `web/navegador.py` | `Sistema_v6/pjn/navegador.py` | Control Playwright |
| `web/funciones_navegador_async.py` | `Sistema_v6/pjn/funciones_navegador_async.py` | Funciones async |
| `web/interfaz_web/` | `Sistema_v6/interfaz_web/` | Frontend FastAPI |

### 3. Módulos de `panel_pjn/` → `Sistema_v6/configuracion/`

| Origen | Destino | Descripción |
|--------|---------|-------------|
| `panel_pjn/acciones_pjn/urls_pjn.py` | `Sistema_v6/configuracion/urls.py` | URLs del PJN |

### 4. Scripts de Ejecución → `Sistema_v6/bin/`

| Origen | Destino | Descripción |
|--------|---------|-------------|
| `ejecutar_extraccion.py` | `Sistema_v6/bin/ejecutar_extraccion.py` | CLI extracción |
| `ejecutar_procesamiento_json.py` | `Sistema_v6/bin/ejecutar_procesamiento_json.py` | CLI procesamiento |

## 📝 Archivos Nuevos Creados

### Configuración

- `Sistema_v6/configuracion/config.py` - Configuración central del sistema
- `Sistema_v6/configuracion/estados.py` - Gestión de estados de expedientes
- `Sistema_v6/configuracion/urls.py` - URLs del PJN (copiado)

### Documentación

- `Sistema_v6/README.md` - Documentación principal
- `Sistema_v6/MIGRACION.md` - Este archivo
- `Sistema_v6/requirements.txt` - Dependencias (copiado)

### Utilidades

- `Sistema_v6/bin/actualizar_imports.py` - Script de actualización de imports

## 🔧 Cambios en Imports

Se actualizaron automáticamente los imports en todos los archivos migrados:

### Mapeo de Imports

```python
# ANTES → DESPUÉS

# Módulos core
from core.flujo_inicial → from Sistema_v6.extractor_inicial
from core.gestion_expedientes → from Sistema_v6.gestion_expedientes
from core.utils → from Sistema_v6.utils
from core.modulos_monitor.expedientes_modular → from Sistema_v6.pjn.monitor

# Módulos web
from web.auto_login → from Sistema_v6.pjn.auto_login
from web.navegador → from Sistema_v6.pjn.navegador

# URLs del PJN
from panel_pjn.acciones_pjn.urls_pjn → from Sistema_v6.configuracion.urls
```

### Estadísticas de Actualización

- **Archivos procesados**: 26
- **Archivos modificados**: 9
- **Total de cambios**: 18

## 📁 Estructura Completa

```
Sistema_v6/
├── __init__.py
├── README.md
├── MIGRACION.md
├── requirements.txt
│
├── configuracion/
│   ├── __init__.py
│   ├── config.py          # ✨ NUEVO
│   ├── urls.py            # Copiado de panel_pjn
│   └── estados.py         # ✨ NUEVO
│
├── pjn/
│   ├── __init__.py
│   ├── auto_login.py      # Copiado de web/
│   ├── navegador.py       # Copiado de web/
│   ├── funciones_navegador_async.py
│   └── monitor/
│       ├── __init__.py
│       ├── extraer_expedientes.py
│       └── verificacion_expedientes.py
│
├── extractor_inicial/
│   ├── __init__.py
│   ├── extraccion_inicial.py
│   ├── procesamiento_expedientes.py
│   ├── main_extraccion.py
│   └── procesar_actuaciones_json.py
│
├── extraccion_masiva/     # ✨ NUEVO (pendiente implementar)
│   ├── __init__.py
│   ├── extractor_masivo.py
│   ├── gestor_batch.py
│   ├── gestor_estados.py
│   └── exportadores.py
│
├── gestion_expedientes/
│   ├── __init__.py
│   ├── comparar_expedientes.py
│   ├── comparar_expedientes_monitor.py
│   └── guardar_comparacion.py
│
├── interfaz_web/
│   ├── __init__.py
│   ├── app.py
│   └── backend/
│       ├── __init__.py
│       ├── main.py
│       ├── db.py
│       ├── api/           # ✨ NUEVO (pendiente implementar)
│       │   ├── __init__.py
│       │   ├── extraccion.py
│       │   └── expedientes.py
│       └── templates/
│           ├── base.html
│           ├── base_admin.html
│           ├── index.html
│           ├── admin_dashboard.html
│           └── monitoreo.html
│
├── utils/
│   ├── __init__.py
│   └── logging.py
│
├── bin/
│   ├── __init__.py
│   ├── ejecutar_extraccion.py
│   ├── ejecutar_procesamiento_json.py
│   ├── actualizar_imports.py
│   └── README.md
│
└── data/
    ├── expedientes/
    ├── extraccion_masiva/
    │   ├── listados/
    │   ├── reportes/
    │   └── logs/
    └── monitoreo/
```

## ✅ Verificación Post-Migración

### Pasos para Verificar

1. **Verificar Imports**
   ```bash
   cd Sistema_v6
   python -c "from Sistema_v6.configuracion.config import Config; print('✅ Config OK')"
   python -c "from Sistema_v6.pjn.auto_login import reutilizar_sesion_async; print('✅ Auto Login OK')"
   python -c "from Sistema_v6.extractor_inicial.extraccion_inicial import extraccion_incremental_async; print('✅ Extraccion OK')"
   ```

2. **Verificar Estructura**
   ```bash
   find Sistema_v6 -name "*.py" -type f | grep -v __pycache__ | wc -l
   # Debe mostrar aproximadamente 26 archivos
   ```

3. **Verificar Configuración**
   ```bash
   cd Sistema_v6
   python -c "from configuracion.config import Config; Config.init_directories(); print('✅ Directorios creados')"
   ```

## 🚀 Próximos Pasos

### 1. Implementar Módulo de Extracción Masiva

Crear los siguientes archivos en `extraccion_masiva/`:
- `extractor_masivo.py` - Lógica principal
- `gestor_batch.py` - Procesamiento por lotes
- `gestor_estados.py` - Gestión de estados
- `exportadores.py` - Exportación de reportes

### 2. Implementar API REST

Crear los siguientes archivos en `interfaz_web/backend/api/`:
- `extraccion.py` - Endpoints de extracción masiva
- `expedientes.py` - Endpoints de gestión de expedientes

### 3. Frontend de Extracción Masiva

Crear:
- `interfaz_web/backend/templates/extraccion_masiva.html`
- `interfaz_web/static/js/extraccion_masiva.js`
- `interfaz_web/static/css/extraccion_masiva.css`

### 4. Testing

Crear directorio `tests/` con:
- `tests/test_extractor_inicial.py`
- `tests/test_extraccion_masiva.py`
- `tests/test_gestion_expedientes.py`

### 5. Documentación Adicional

- Guía de desarrollo
- Guía de deployment
- API documentation
- Changelog

## 🔍 Módulos Originales (No Migrados)

Los siguientes módulos se mantienen en sus ubicaciones originales:

- `Sistema_v3/` - Sistema v3 (legacy)
- `Sistema_v4/` - Sistema v4 (legacy)
- `Sistema_v5/` - Sistema v5 (referencia)
- `V3/` - Versión 3 (legacy)
- `notificaciones_v2/` - Sistema de notificaciones
- `scripts/` - Scripts de utilidad
- `tests/` - Tests del proyecto
- `docs/` - Documentación general

## 📊 Estadísticas Finales

- **Directorios creados**: 21
- **Archivos Python copiados**: 15
- **Archivos nuevos creados**: 5
- **Templates copiados**: 5
- **Imports actualizados**: 18 cambios en 9 archivos

## 🎯 Estado del Proyecto

| Componente | Estado | Notas |
|------------|--------|-------|
| Estructura de directorios | ✅ Completo | 21 directorios creados |
| Configuración | ✅ Completo | Config, Estados, URLs |
| Módulos PJN | ✅ Completo | Auto-login, Navegador, Monitor |
| Extractor Inicial | ✅ Completo | Migrado y funcional |
| Gestión Expedientes | ✅ Completo | Migrado y funcional |
| Interfaz Web | ✅ Completo | Backend básico migrado |
| Extracción Masiva | ⏳ Pendiente | Por implementar |
| API REST | ⏳ Pendiente | Por implementar |
| Frontend Masivo | ⏳ Pendiente | Por implementar |
| Testing | ⏳ Pendiente | Por crear |
| Documentación API | ⏳ Pendiente | Por crear |

---

**Versión de migración**: 1.0
**Fecha**: 2025-11-07
**Autor**: Sistema Automatizado de Migración
