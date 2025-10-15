# Documentación Sistema_v5

Esta carpeta contiene la documentación técnica y guías de uso para Sistema_v5 del proyecto sintaXis.

## Índice de Documentación

### 📋 Documentos Técnicos

- **[pjn_selectores_tabla.md](./pjn_selectores_tabla.md)** - ⭐ **NUEVO** - Tabla centralizada de selectores CSS del portal PJN. Incluye guía de uso, código de fragilidad y plan de mantenimiento.
- **[refactorizacion_excepciones.md](./refactorizacion_excepciones.md)** - Detalle completo de la refactorización del sistema de manejo de excepciones, incluyendo la jerarquía de excepciones, cambios realizados y mejoras implementadas.
- **[reporte_testing.md](./reporte_testing.md)** - Estado actual de tests, cobertura y plan de acción para mejorar la calidad del código.
- **[guia_logging.md](./guia_logging.md)** - Guía de uso del sistema de logging con colores y niveles configurables.
- **[sistema_logging.md](./sistema_logging.md)** - Documentación técnica del sistema de logging implementado.

### 💻 Ejemplos de Código

- **[ejemplos_uso_excepciones.py](./ejemplos_uso_excepciones.py)** - Ejemplos prácticos de cómo usar el sistema de excepciones personalizado en diferentes escenarios.

## Estructura del Sistema_v5

```
Sistema_v5/
├── pjn/
│   ├── exceptions.py        # Sistema de excepciones personalizado
│   ├── selectores.py        # ⭐ NUEVO - Selectores CSS centralizados
│   ├── models/              # Modelos de datos (Actuacion, Expediente, etc.)
│   ├── parsers/             # Parsers para transformar datos HTML
│   ├── scraping/            # Lógica de extracción con Playwright
│   │   ├── base.py          # Utilidades base y autenticación
│   │   ├── actuaciones.py   # Extracción de actuaciones
│   │   ├── expedientes.py   # Búsqueda y selección de expedientes
│   │   └── entradas.py      # Extracción de entradas
│   ├── scripts/             # Scripts ejecutables
│   │   └── rf_test_extraccion_completa.py
│   └── utils/               # Utilidades (logging, etc.)
└── documentacion/           # Esta carpeta
```

## Características Principales

### 🎯 Sistema de Selectores Centralizados (NUEVO)

Sistema_v5 centraliza todos los selectores CSS del portal PJN en un solo módulo:

```python
from Sistema_v5.pjn.selectores import SEL_ENTRADAS, SEL_EXPEDIENTES, SEL_ACTUACIONES

# Usar selectores centralizados
await page.wait_for_selector(SEL_ENTRADAS.CONTENEDOR_SCROLL)
filas = await page.query_selector_all(SEL_ENTRADAS.TABLA)
```

**Ventajas:**
- ✅ Un solo lugar para actualizar cuando cambie el sitio PJN
- ✅ Autocomplete en IDEs
- ✅ Tests automáticos validan integridad
- ✅ Documentación de fragilidad de cada selector

Ver [pjn_selectores_tabla.md](./pjn_selectores_tabla.md) para detalles completos.

### 🛡️ Sistema de Excepciones

Sistema_v5 implementa un sistema robusto de excepciones personalizadas:

- **PJNError** - Excepción base para todos los errores del sistema
- **AutenticacionError** - Errores de login y credenciales
- **ExtraccionError** - Errores durante scraping de datos
- **ParsingError** - Errores al procesar/transformar datos
- **DescargaError** - Errores al descargar archivos
- **ValidacionError** - Errores de validación de entrada
- **SistemaError** - Errores de configuración o estado interno

Ver [refactorizacion_excepciones.md](./refactorizacion_excepciones.md) para detalles completos.

### 📊 Sistema de Logging

Logging configurable con colores y niveles:

```python
from Sistema_v5.pjn.utils.logging import setup_logging, get_logger

# Configurar logging
setup_logging(level="INFO", log_file="logs/sistema.log")

# Usar en tu módulo
logger = get_logger(__name__)
logger.info("✅ Operación exitosa")
```

Ver [guia_logging.md](./guia_logging.md) para más detalles.

## Inicio Rápido

### 1. Importar Selectores

```python
from Sistema_v5.pjn.selectores import (
    SEL_AUTH,
    SEL_ENTRADAS,
    SEL_EXPEDIENTES,
    SEL_ACTUACIONES,
)
```

### 2. Importar Excepciones

```python
from Sistema_v5.pjn import (
    PJNError,
    CredencialesFaltantes,
    ExtraccionError,
)
```

### 3. Manejo de Errores

```python
try:
    async with obtener_pagina_autenticada() as (page, ctx, browser):
        await page.goto("https://portalpjn.pjn.gov.ar")
        # Tu código aquí
except CredencialesFaltantes:
    print("Configure PJN_USER y PJN_PASSWORD")
except ExtraccionError as e:
    print(f"Error extrayendo datos: {e}")
except PJNError as e:
    print(f"Error del sistema PJN: {e}")
```

## Testing

Sistema_v5 incluye tests automáticos:

```bash
# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar tests de selectores
pytest tests/test_selectores.py -v

# Ejecutar con cobertura
pytest tests/ --cov=Sistema_v5 --cov-report=term-missing
```

**Estado actual:** 48 tests, 93.75% pasando, 32% cobertura
Ver [reporte_testing.md](./reporte_testing.md) para plan de acción.

## Recursos Adicionales

- **Documentación general del proyecto:** `/docs/`
- **Tests:** `/tests/test_selectores.py`, `/tests/test_pjn_*.py`
- **Documentación Sistema_v4:** `/Sistema_v4/documentacion/`

## Contribuir

Al agregar nueva funcionalidad al Sistema_v5:

1. **Selectores:** Agregar nuevos selectores a `pjn/selectores.py`
2. **Excepciones:** Usar las excepciones personalizadas apropiadas
3. **Documentación:** Documentar funciones públicas con docstrings
4. **Tests:** Agregar tests para nueva funcionalidad
5. **Actualizar:** Esta documentación según corresponda

### Guías de Estilo

- **Selectores:** Usar constantes de `selectores.py`, no strings hardcodeados
- **Logging:** Usar emojis consistentes (✅ éxito, ❌ error, ⚠️ advertencia, 📄 info)
- **Excepciones:** Siempre heredar de `PJNError` o sus subclases
- **Type hints:** Usar anotaciones de tipo en funciones públicas

---

**Última actualización:** 15 Octubre 2025
**Versión:** 5.0
**Mantenido por:** Equipo sintaXis