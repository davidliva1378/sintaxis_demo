# Sistema v5 - Extracción de Datos del Portal PJN

Sistema moderno y robusto para extracción de datos del Portal del Poder Judicial de la Nación (PJN) usando Playwright.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/Tests-48%20(93.75%25%20passing)-yellow.svg)](./documentacion/reporte_testing.md)
[![Coverage](https://img.shields.io/badge/Coverage-32%25-orange.svg)](./documentacion/reporte_testing.md)

---

## 🌟 Características Principales

### ⭐ Nuevo en v5.1: Sistema de Selectores Centralizados

```python
from Sistema_v5.pjn.selectores import SEL_ENTRADAS, SEL_EXPEDIENTES

# Un solo lugar para todos los selectores CSS
await page.wait_for_selector(SEL_ENTRADAS.CONTENEDOR_SCROLL)
filas = await page.query_selector_all(SEL_ENTRADAS.TABLA)
```

**Ventajas:**
- ✅ Mantenimiento simplificado ante cambios en el sitio
- ✅ Autocomplete en IDEs
- ✅ Tests automáticos de validación
- ✅ Documentación de fragilidad incluida

[Ver tabla completa de selectores →](./documentacion/pjn_selectores_tabla.md)

### 🛡️ Sistema de Excepciones Robusto

```python
from Sistema_v5.pjn import CredencialesFaltantes, ExtraccionError

try:
    await extraer_actuaciones(page, expediente)
except CredencialesFaltantes:
    logger.error("Configure PJN_USER y PJN_PASSWORD")
except ExtraccionError as e:
    logger.error(f"Error en extracción: {e}")
```

### 📊 Logging Configurable

```python
from Sistema_v5.pjn.utils.logging import setup_logging

# Configurar con variables de entorno o programáticamente
setup_logging(level="INFO", log_file="logs/sistema.log")
```

### 🎯 Modelos de Datos Tipados

```python
from Sistema_v5.pjn.models import Expediente, Actuacion, Entrada

expediente = Expediente.from_dict(datos)
actuacion = Actuacion(
    fecha="2025-10-15",
    tipo="Providencia",
    detalle="Se provee...",
)
```

---

## 📁 Estructura del Proyecto

```
Sistema_v5/
├── pjn/
│   ├── __init__.py              # Exporta excepciones
│   ├── exceptions.py            # Sistema de excepciones personalizado
│   ├── selectores.py            # ⭐ Selectores CSS centralizados
│   │
│   ├── models/                  # Modelos de datos (dataclasses)
│   │   ├── __init__.py
│   │   ├── actuacion.py
│   │   ├── entrada.py
│   │   ├── expediente.py
│   │   └── _utils.py
│   │
│   ├── parsers/                 # Transformación HTML → Modelos
│   │   ├── __init__.py
│   │   ├── actuaciones_parser.py
│   │   ├── entradas_parser.py
│   │   └── expedientes_parser.py
│   │
│   ├── scraping/                # Lógica de extracción con Playwright
│   │   ├── __init__.py
│   │   ├── base.py              # Autenticación y utilidades
│   │   ├── actuaciones.py       # Actuaciones actuales e históricas
│   │   ├── actuaciones_utils.py
│   │   ├── entradas.py          # Bandeja de notificaciones (scroll infinito)
│   │   └── expedientes.py       # Búsqueda y paginación
│   │
│   ├── scripts/                 # Scripts ejecutables
│   │   ├── __init__.py
│   │   └── rf_test_extraccion_completa.py
│   │
│   ├── services/                # Servicios de alto nivel (futuro)
│   │   └── __init__.py
│   │
│   └── utils/                   # Utilidades generales
│       ├── __init__.py
│       └── logging.py           # Sistema de logging con colores
│
├── documentacion/               # 📚 Documentación completa
│   ├── README.md                # Índice de documentación
│   ├── pjn_selectores_tabla.md # ⭐ Tabla de selectores
│   ├── refactorizacion_excepciones.md
│   ├── reporte_testing.md
│   ├── guia_logging.md
│   └── sistema_logging.md
│
├── CHANGELOG.md                 # Historial de cambios
└── README.md                    # Este archivo
```

---

## 🚀 Inicio Rápido

### Prerrequisitos

```bash
# Python 3.11 o superior
python --version

# Instalar dependencias
pip install playwright python-dotenv

# Instalar navegadores de Playwright
playwright install chromium
```

### Configuración

```bash
# Crear archivo .env en la raíz del proyecto
echo "PJN_USER=tu_usuario" >> .env
echo "PJN_PASSWORD=tu_contraseña" >> .env
```

### Uso Básico

```python
import asyncio
from Sistema_v5.pjn.scraping import obtener_pagina_autenticada
from Sistema_v5.pjn.scraping.entradas import extraer_entradas_pjn
from Sistema_v5.pjn import CredencialesFaltantes

async def main():
    try:
        async with obtener_pagina_autenticada() as (page, ctx, browser):
            # Navegar a la bandeja de entradas
            await page.goto("https://portalpjn.pjn.gov.ar/entradas")

            # Extraer entradas
            cantidad = await extraer_entradas_pjn(
                page,
                destino="./datos_extraidos",
                incluir_tipos=("N", "D"),  # Notificaciones y Despachos
            )

            print(f"✅ Extraídas {cantidad} entradas nuevas")

    except CredencialesFaltantes:
        print("❌ Configure PJN_USER y PJN_PASSWORD en .env")

if __name__ == "__main__":
    asyncio.run(main())
```

### Script de Prueba Completo

```bash
# Ejecutar el script interactivo
python Sistema_v5/pjn/scripts/rf_test_extraccion_completa.py
```

---

## 🧪 Testing

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar solo tests de Sistema_v5
pytest tests/test_pjn_*.py tests/test_selectores.py -v

# Con cobertura
pytest tests/ --cov=Sistema_v5 --cov-report=html

# Ver reporte de cobertura
# Windows
start htmlcov/index.html

# Linux/Mac
open htmlcov/index.html
```

**Estado actual:**
- ✅ 48 tests totales
- ✅ 45 tests pasando (93.75%)
- ⚠️ 3 tests fallando (en proceso de corrección)
- 📊 32% cobertura general

[Ver reporte completo de testing →](./documentacion/reporte_testing.md)

---

## 📖 Documentación

### Documentos Principales

| Documento | Descripción |
|-----------|-------------|
| [📋 Tabla de Selectores](./documentacion/pjn_selectores_tabla.md) | Selectores CSS centralizados del portal PJN |
| [🛡️ Sistema de Excepciones](./documentacion/refactorizacion_excepciones.md) | Jerarquía y uso de excepciones |
| [📊 Reporte de Testing](./documentacion/reporte_testing.md) | Estado de tests y plan de acción |
| [📝 Guía de Logging](./documentacion/guia_logging.md) | Configuración y uso del sistema de logs |
| [📜 CHANGELOG](./CHANGELOG.md) | Historial de cambios versión por versión |

### Guías Rápidas

- **[Inicio Rápido](./documentacion/README.md#inicio-rápido)** - Primeros pasos con Sistema_v5
- **[Estructura del Proyecto](./documentacion/README.md#estructura-del-sistema_v5)** - Organización de módulos
- **[Contribuir](./documentacion/README.md#contribuir)** - Guías de estilo y mejores prácticas

---

## 🔄 Migración desde Versiones Anteriores

### Sistema_v3/v4 → Sistema_v5

**Antes (v3/v4):**
```python
SELEC_TABLA = "div.MuiTableContainer-root tr"
filas = await page.query_selector_all(SELEC_TABLA)
```

**Después (v5):**
```python
from Sistema_v5.pjn.selectores import SEL_ENTRADAS
filas = await page.query_selector_all(SEL_ENTRADAS.TABLA)
```

**Ventajas de migrar:**
- ✅ Mantenimiento centralizado
- ✅ Tests automáticos
- ✅ Mejor IDE support
- ✅ Documentación integrada

---

## 🤝 Contribuir

Contribuciones son bienvenidas! Por favor sigue estas guías:

### 1. Agregar Nuevos Selectores

```python
# En pjn/selectores.py
@dataclass(frozen=True)
class NuevoModuloSelectores:
    """Selectores para nuevo módulo del PJN."""

    SELECTOR_NUEVO: ClassVar[str] = ".clase-css"
```

### 2. Usar Excepciones Apropiadas

```python
from Sistema_v5.pjn import ExtraccionError

if not elemento:
    raise ExtraccionError("No se encontró el elemento esperado")
```

### 3. Agregar Tests

```python
# En tests/test_nuevo_modulo.py
def test_nueva_funcionalidad():
    resultado = nueva_funcion()
    assert resultado == esperado
```

### 4. Documentar

- Agregar docstrings a funciones públicas
- Actualizar CHANGELOG.md
- Incluir ejemplos si es relevante

### Guías de Estilo

- **Selectores:** Siempre usar constantes de `selectores.py`
- **Logging:** Usar emojis consistentes (✅ 🐛 ⚠️ 📄)
- **Excepciones:** Heredar de `PJNError` o sus subclases
- **Type hints:** Usar anotaciones en funciones públicas

---

## 📊 Métricas del Proyecto

| Métrica | Valor |
|---------|-------|
| **Líneas de código** | ~3,944 |
| **Módulos principales** | 15 |
| **Tests** | 48 (20 nuevos de selectores) |
| **Coverage** | 32% (objetivo: 80%) |
| **Selectores centralizados** | 31 |
| **Excepciones personalizadas** | 15 |

---

## 🐛 Problemas Conocidos

- ⚠️ 3 tests fallando (corrección en progreso)
- ⚠️ Selectores frágiles marcados con 🔴 en documentación
- ⚠️ Cobertura de scrapers principales <25%

[Ver issues completos →](./documentacion/reporte_testing.md#problemas-identificados)

---

## 📜 Licencia

Este proyecto es parte de sintaXis. Ver licencia del proyecto principal.

---

## 📞 Soporte

- **Documentación:** [./documentacion/README.md](./documentacion/README.md)
- **Issues:** Reportar en el repositorio principal
- **Changelog:** [CHANGELOG.md](./CHANGELOG.md)

---

## 🔗 Enlaces Útiles

- [Portal PJN](https://portalpjn.pjn.gov.ar)
- [Playwright Documentation](https://playwright.dev/python/)
- [Documentación del Proyecto Principal](../docs/)

---

**Última actualización:** 15 Octubre 2025
**Versión:** 5.1.0
**Estado:** ✅ En producción
