# 📚 Documentación Sistema_v5

**Versión:** 5.6
**Última actualización:** 17 de octubre, 2025
**Estado:** ✅ Producción Ready

---

## 🎯 Inicio Rápido

### ¿Qué es Sistema_v5?

Sistema de web scraping profesional para el Portal Judicial Nacional (PJN) con arquitectura modular, alta performance y código de producción.

**Características principales:**
- ✅ **Performance**: 29,532 expedientes/segundo
- ✅ **Memoria eficiente**: 90.6% menos que dict tradicional
- ✅ **Tests**: 71/71 pasando (100%)
- ✅ **Type hints**: 93% cobertura
- ✅ **Calidad**: 4.6/5.0 ⭐⭐⭐⭐⭐

---

## 📖 Documentación Disponible

### 1. [GUIA_TECNICA_SISTEMA.md](GUIA_TECNICA_SISTEMA.md) → **START HERE**

📗 **Guía técnica completa y consolidada**

Contenido:
- Sistema de Logging (configuración, uso, mejores prácticas)
- Sistema de Autenticación (persistencia, re-login automático)
- Selectores CSS (centralizados, fragilidad documentada)
- Sistema de Excepciones (jerarquía completa)
- Testing (guía completa)

**🎯 Lee esto primero si eres nuevo**

---

### 2. Reportes de Sprints

#### [SPRINT_1_REPORTE_FINAL.md](SPRINT_1_REPORTE_FINAL.md)
📄 Sprint 1: Estabilización (Oct 16)
- Eliminación de código duplicado
- Mejora de manejo de errores
- Validación de recursos I/O

#### [SPRINT_2_REPORTE_FINAL.md](SPRINT_2_REPORTE_FINAL.md) → **LATEST**
📄 Sprint 2: Refactorización (Oct 17)
- 7 tareas completadas
- Calidad: 4.6/5.0
- Performance: ⭐⭐⭐⭐⭐ 5.0/5.0
- Sin regresiones

---

### 3. Documentación de Referencia

#### [SPRINT_2_TAREA_2.6_CODE_REVIEW.md](SPRINT_2_TAREA_2.6_CODE_REVIEW.md)
📋 Code review exhaustivo (1,176 líneas)
- Arquitectura y diseño
- Calidad del código
- Seguridad
- Performance
- Recomendaciones Sprint 3

#### [SPRINT_2_TAREA_2.7_PERFORMANCE_TESTING.md](SPRINT_2_TAREA_2.7_PERFORMANCE_TESTING.md)
⚡ Performance testing completo (904 líneas)
- Benchmarks detallados
- Análisis de memoria
- Cuellos de botella
- Proyecciones de escalabilidad

#### [TRACKING_SPRINTS.md](TRACKING_SPRINTS.md)
📊 Tracking de todos los sprints
- Sprint 1: ✅ Completado
- Sprint 2: ✅ Completado
- Sprint 3: ⏳ Planificado
- Métricas y progreso

---

## 🚀 Uso Rápido

### Instalación

```bash
cd Sistema_v5
pip install -r requirements.txt

# Configurar credenciales
export PJN_USER=tu_usuario
export PJN_PASSWORD=tu_password
```

### Ejemplo Básico

```python
from pjn.scraping import obtener_pagina_autenticada
from pjn.scraping.expedientes import extraer_expedientes_completos
from pjn.models import ExtraccionExpedientesConfig

# Configuración simple
config = ExtraccionExpedientesConfig.rapido()  # 5 páginas max

# Extracción
async with obtener_pagina_autenticada() as page:
    expedientes, motivo, meta = await extraer_expedientes_completos(page, config)
    print(f"✅ Extraídos {len(expedientes)} expedientes")
    print(f"Motivo: {motivo}")
    print(f"Páginas: {meta['paginas_extraidas']}")
```

### Ejemplo Avanzado

```python
from pjn.scraping.actuaciones import extraer_actuaciones_datos
from pjn.utils.logging import setup_logging, get_logger

# Configurar logging
setup_logging(level="INFO", log_file="logs/extraccion.log")
logger = get_logger(__name__)

# Extracción con logging
async with obtener_pagina_autenticada() as page:
    try:
        actuaciones = await extraer_actuaciones_datos(
            page,
            numero="FPA_012345_2025"
        )
        logger.info("✅ %d actuaciones extraídas", len(actuaciones))

    except ExpedienteNoEncontrado:
        logger.warning("⚠️ Expediente no encontrado")

    except PJNError as e:
        logger.error("❌ Error: %s", e)
```

---

## 📊 Estado del Proyecto

### Sprint 2 - Completado ✅

```
Mejoras logradas:
├─ Código duplicado: -100%
├─ Constantes mágicas: -100%
├─ Funciones grandes: -62%
├─ Parámetros/función: -92%
├─ Memoria: -90.6%
├─ Type hints: +17%
└─ Performance: ⭐⭐⭐⭐⭐
```

### Métricas Actuales

| Métrica | Valor | Estado |
|---------|-------|--------|
| Tests pasando | 71/71 | ✅ 100% |
| Type hints (return) | 93% | ✅ Excelente |
| Docstrings | 86% | ✅ Muy bueno |
| Performance (parseo) | 29,532 ops/s | ⭐⭐⭐⭐⭐ |
| Memoria (dataclass) | 72 bytes | ⭐⭐⭐⭐⭐ |
| Calidad global | 4.6/5.0 | ⭐⭐⭐⭐⭐ |
| Seguridad | 0 vulnerabilidades | ✅ Perfecto |

---

## 🗂️ Estructura del Proyecto

```
Sistema_v5/
├── pjn/                          # Código principal
│   ├── scraping/                 # Lógica de extracción
│   │   ├── base.py              # Autenticación y utilidades
│   │   ├── expedientes.py       # Búsqueda de expedientes
│   │   ├── actuaciones.py       # Extracción de actuaciones
│   │   └── entradas.py          # Extracción de entradas
│   ├── models/                   # Modelos de datos
│   │   ├── expediente.py
│   │   ├── actuacion.py
│   │   ├── entrada.py
│   │   └── extraccion_config.py # ⭐ NUEVO en Sprint 2
│   ├── parsers/                  # Transformación de datos
│   ├── utils/                    # Utilidades
│   │   └── logging.py           # Sistema de logging
│   ├── constants.py              # ⭐ NUEVO en Sprint 2 (47 constantes)
│   ├── config.py                 # Configuración centralizada
│   ├── exceptions.py             # Sistema de excepciones
│   └── selectores.py            # Selectores CSS centralizados
├── tests/                        # Tests (71 tests)
├── scripts/                      # Scripts de utilidad
│   ├── performance_benchmark.py  # ⭐ NUEVO - Benchmarking
│   └── memory_profiler.py       # ⭐ NUEVO - Memory profiling
└── documentacion/                # Esta carpeta
    ├── README.md                 # Este archivo
    ├── GUIA_TECNICA_SISTEMA.md   # Guía técnica consolidada
    ├── SPRINT_1_REPORTE_FINAL.md # Reporte Sprint 1
    ├── SPRINT_2_REPORTE_FINAL.md # Reporte Sprint 2
    └── TRACKING_SPRINTS.md       # Tracking completo
```

---

## 🎯 Próximos Pasos (Sprint 3)

### Prioridad ALTA 🔴

1. **Sistema de Caché** (4h)
   - Cache con TTL para expedientes
   - -50% requests al portal

2. **Rate Limiting** (3h)
   - Protección contra ban
   - Extracción más segura

3. **Retry con Backoff** (2h)
   - Retry automático inteligente
   - +95% tasa de éxito

### Prioridad MEDIA 🟡

4. **Refactorizar funciones complejas** (4h)
   - 5 funciones con >10 branches
   - Target: todas <10 branches

5. **Tests de integración** (6h)
   - End-to-end con portal real
   - 80% cobertura total

6. **Completar type hints** (2h)
   - De 59% a 90%+ en parámetros

---

## 🛠️ Comandos Útiles

### Desarrollo

```bash
# Tests
pytest tests/ -v

# Tests con cobertura
pytest tests/ --cov=pjn --cov-report=html

# Performance benchmarks
python scripts/performance_benchmark.py

# Memory profiling
python scripts/memory_profiler.py

# Linter
ruff check pjn/

# Type checking
mypy pjn/
```

### Producción

```bash
# Variables de entorno
export PJN_USER=usuario
export PJN_PASSWORD=password
export LOG_LEVEL=INFO
export LOG_FILE=logs/produccion.log

# Ejecutar
python tu_script.py
```

---

## 📞 Soporte

### Documentación Completa

- **Guía técnica:** [GUIA_TECNICA_SISTEMA.md](GUIA_TECNICA_SISTEMA.md)
- **Sprint 2:** [SPRINT_2_REPORTE_FINAL.md](SPRINT_2_REPORTE_FINAL.md)
- **Code review:** [SPRINT_2_TAREA_2.6_CODE_REVIEW.md](SPRINT_2_TAREA_2.6_CODE_REVIEW.md)
- **Performance:** [SPRINT_2_TAREA_2.7_PERFORMANCE_TESTING.md](SPRINT_2_TAREA_2.7_PERFORMANCE_TESTING.md)

### Recursos Externos

- Documentación general: `/docs/`
- Documentación web_app: `/web_app/docs/`
- Tests: `/tests/`

---

## 🏆 Logros del Proyecto

✅ **Sprint 1 Completado** (Oct 16)
- Código duplicado eliminado
- Manejo de errores mejorado
- Validaciones de I/O implementadas

✅ **Sprint 2 Completado** (Oct 17)
- Performance: ⭐⭐⭐⭐⭐ 5.0/5.0
- Calidad: ⭐⭐⭐⭐⭐ 4.6/5.0
- Sin regresiones
- Listo para producción

⏳ **Sprint 3 Planificado**
- Sistema de caché
- Rate limiting
- Retry con backoff
- Tests de integración

---

**Mantenido por:** Equipo sintaXis
**Última actualización:** 17 de octubre, 2025
**Versión:** 5.6
**Estado:** ✅ Producción Ready
