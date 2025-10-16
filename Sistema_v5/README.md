# Sistema_v5 - Web Scraping Framework para PJN

**Versión:** 5.5.1
**Estado:** ✅ Producción Ready
**Líneas de código:** ~5,800 líneas Python

---

## 🎯 ¿Qué es Sistema_v5?

Framework completo de web scraping para el **Portal Judicial Nacional (PJN)** de Argentina, diseñado con arquitectura modular, altamente reutilizable y fácilmente extensible a otros portales.

### ✨ Características Principales

- ✅ **Arquitectura Modular** - Separación clara de responsabilidades
- ✅ **Funciones Puras** - Sin side effects, ideal para composición
- ✅ **Manejo de Errores Estandarizado** - Excepciones jerárquicas con stack traces
- ✅ **Configuración Centralizada** - Un solo punto de configuración
- ✅ **Estrategias de Paginación** - Adaptable a diferentes frameworks web
- ✅ **Persistencia Separada** - Funciones de I/O independientes
- ✅ **Type Hints Completos** - Totalmente tipado
- ✅ **Retrocompatible** - Código legacy sigue funcionando

---

## 🚀 Inicio Rápido

### Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd Sistema_v5

# Instalar dependencias
pip install playwright pandas
playwright install chromium
```

### Primer Script

```python
import asyncio
from playwright.async_api import async_playwright
from pjn.scraping.expedientes import extraer_expedientes_completos_modelos

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()

        # Login y navegación al listado
        # ... (implementar según tu flujo)

        # Extraer expedientes
        expedientes, motivo, metadata = await extraer_expedientes_completos_modelos(
            page,
            max_paginas=5,
        )

        print(f"✅ Extraídos: {len(expedientes)} expedientes")
        for exp in expedientes:
            print(f"  {exp.numero}: {exp.caratula}")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 📚 Documentación

Toda la documentación está organizada en la carpeta [`docs/`](docs/):

### 🎯 [Empezar Aquí - Índice de Documentación](docs/README_DOCUMENTACION.md)

Guía completa para navegar toda la documentación según tus necesidades.

### 📖 Documentos Principales

| Documento | Tamaño | Descripción | Cuándo usar |
|-----------|--------|-------------|-------------|
| **[README_DOCUMENTACION.md](docs/README_DOCUMENTACION.md)** | 12K | Índice principal y guía de navegación | 👈 **Empezar aquí** |
| **[DOCUMENTACION_COMPLETA.md](docs/DOCUMENTACION_COMPLETA.md)** | 28K | API Reference completa del sistema | Referencia técnica |
| **[DOCUMENTACION_GUIAS.md](docs/DOCUMENTACION_GUIAS.md)** | 22K | Guías prácticas y ejemplos completos | Casos de uso |
| **[INVENTARIO_FUNCIONES.md](docs/INVENTARIO_FUNCIONES.md)** | 19K | Inventario exhaustivo de funciones | Buscar funciones |
| **[ROADMAP.md](docs/ROADMAP.md)** | 12K | Hoja de ruta y progreso | Estado del proyecto |

---

## 📊 Estado del Proyecto

```
🔴 CRÍTICA:  [████] 100% (4/4 completadas) ✅
🟠 ALTA:     [████] 100% (3/3 completadas) ✅
🟡 MEDIA:    [██░] 67% (2/3 completadas)
🟢 BAJA:     [░░░] 0% (0/5 completadas)

TOTAL: 60% (9/15 mejoras)
```

**✅ Todas las mejoras CRÍTICAS y ALTAS están completadas**

---

## 🏗️ Estructura del Proyecto

```
Sistema_v5/
├── pjn/                          # Código principal
│   ├── config.py                 # Configuración centralizada
│   ├── exceptions.py             # Excepciones personalizadas
│   ├── selectores.py             # Selectores CSS
│   │
│   ├── models/                   # Modelos de datos
│   ├── parsers/                  # Parsers HTML → Models
│   ├── scraping/                 # Módulo de scraping
│   │   ├── actuaciones.py        # Extracción de actuaciones
│   │   ├── entradas.py           # Extracción de entradas
│   │   ├── expedientes.py        # Extracción de expedientes
│   │   └── pagination.py         # Estrategias de paginación
│   ├── persistence/              # Persistencia de datos
│   └── utils/                    # Utilidades
│
├── docs/                         # 📚 Documentación completa
│   ├── README_DOCUMENTACION.md   # 👈 Índice de documentación
│   ├── DOCUMENTACION_COMPLETA.md # API Reference
│   ├── DOCUMENTACION_GUIAS.md    # Guías y ejemplos
│   ├── INVENTARIO_FUNCIONES.md   # Inventario de funciones
│   ├── ROADMAP.md                # Roadmap de mejoras
│   ├── MEJORAS_IMPLEMENTADAS.md  # Mejoras detalladas
│   └── MEJORA_*.md               # Ejemplos específicos
│
└── datos_extraidos/              # Datos extraídos (gitignored)
```

---

## 💡 Ejemplos Rápidos

### Extraer Expedientes con Filtros

```python
from pjn.scraping.expedientes import extraer_expedientes_completos_modelos

expedientes, motivo, metadata = await extraer_expedientes_completos_modelos(
    page,
    max_paginas=10,
    fecha_corte="2024-01-01",    # Solo desde esta fecha
    orden="fecha",                # Ordenar por fecha
    omitir_duplicados=True,       # Sin duplicados
)
```

### Extraer Actuaciones de un Expediente

```python
from pjn.scraping.actuaciones import extraer_actuaciones_datos

archivo = await extraer_actuaciones_datos(page, expediente_datos)

for act in archivo.actuaciones:
    print(f"{act.fecha}: {act.tipo} - {act.detalle}")
    print(f"  Archivos: {len(act.archivos)}")
```

### Monitorear Notificaciones

```python
from pjn.scraping.entradas import extraer_entradas_datos

entradas = await extraer_entradas_datos(
    page,
    incluir_tipos=("N",),         # Solo notificaciones
    historial_existente=historial, # Deduplicar
)

print(f"📬 Nuevas notificaciones: {len(entradas)}")
```

**Más ejemplos →** [docs/DOCUMENTACION_GUIAS.md](docs/DOCUMENTACION_GUIAS.md)

---

## 🔑 Conceptos Clave

### Funciones Puras (Recomendadas)

✅ No guardan archivos automáticamente
✅ Retornan modelos de datos
✅ Fáciles de testear y componer
✅ Ejemplo: `extraer_actuaciones_datos()`

### Estrategias de Paginación

El sistema usa el patrón Strategy para adaptar la paginación a diferentes frameworks:

```python
from pjn.scraping.pagination import PrimeFacesPaginationStrategy

strategy = PrimeFacesPaginationStrategy(timeout_ms=15_000)

expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    pagination_strategy=strategy,  # Estrategia personalizada
)
```

### Manejo de Excepciones

```python
from pjn.exceptions import TimeoutExtraccion, ExtraccionError

try:
    datos = await extraer_actuaciones_datos(page, expediente)
except TimeoutExtraccion:
    # Manejo específico de timeout
    logger.warning("Timeout - reintentando...")
except ExtraccionError as e:
    # Manejo genérico
    logger.error(f"Error: {e}")
```

---

## 📈 Estadísticas

- **Líneas de código:** ~5,776 líneas Python
- **Funciones públicas:** 42
- **Clases:** 15
- **Protocols:** 1
- **Módulos:** 11
- **Documentación:** 8 archivos (~81K)
- **Elementos documentados:** 84

---

## 🛠️ Configuración

### Variables de Entorno (Opcional)

```bash
# .env
PJN_TIMEOUT_DEFAULT=20000
PJN_MAX_PAGINAS=100
PJN_HEADLESS=false
PJN_CUIL=20123456789
PJN_PASSWORD=mi_password
```

### Configuración Programática

```python
from pjn.config import Config, ScrapingConfig, set_config

config = Config(
    scraping=ScrapingConfig(
        timeout_default=20_000,
        max_paginas_expedientes=50,
    )
)
set_config(config)
```

---

## 📞 Necesitas Ayuda?

### Tengo una pregunta sobre cómo usar una función
→ [docs/DOCUMENTACION_COMPLETA.md](docs/DOCUMENTACION_COMPLETA.md) - API Reference

### Necesito un ejemplo completo
→ [docs/DOCUMENTACION_GUIAS.md](docs/DOCUMENTACION_GUIAS.md) - Guías y ejemplos

### Algo no funciona
→ [docs/DOCUMENTACION_GUIAS.md - Troubleshooting](docs/DOCUMENTACION_GUIAS.md#troubleshooting)

### Quiero adaptar a otro portal
→ [docs/MEJORA_6_EJEMPLO.md](docs/MEJORA_6_EJEMPLO.md) - Estrategias de paginación

---

## 🎯 Roadmap

**Completadas (60%):**
- ✅ Separación extracción/persistencia
- ✅ Manejo de errores estandarizado
- ✅ Eliminación de side effects
- ✅ Configuración centralizada
- ✅ Módulo de persistencia
- ✅ Estrategias de paginación
- ✅ Refactorización de funciones gigantes

**Ver progreso completo →** [docs/ROADMAP.md](docs/ROADMAP.md)

---

## 👥 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Lee [docs/ROADMAP.md](docs/ROADMAP.md) para ver mejoras pendientes
2. Revisa [docs/MEJORAS_IMPLEMENTADAS.md](docs/MEJORAS_IMPLEMENTADAS.md) para el estilo
3. Sigue los patrones de [docs/DOCUMENTACION_GUIAS.md](docs/DOCUMENTACION_GUIAS.md)

---

**¿Listo para empezar?** → [docs/README_DOCUMENTACION.md](docs/README_DOCUMENTACION.md)

---

**Última actualización:** 2025-10-16
**Versión:** 5.5.1
