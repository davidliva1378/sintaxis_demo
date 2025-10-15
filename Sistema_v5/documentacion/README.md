# Documentación Sistema_v5

Esta carpeta contiene la documentación técnica y guías de uso para Sistema_v5 del proyecto sintaXis.

## Índice de Documentación

### 📋 Documentos Técnicos

- **[refactorizacion_excepciones.md](./refactorizacion_excepciones.md)** - Detalle completo de la refactorización del sistema de manejo de excepciones, incluyendo la jerarquía de excepciones, cambios realizados y mejoras implementadas.

### 💻 Ejemplos de Código

- **[ejemplos_uso_excepciones.py](./ejemplos_uso_excepciones.py)** - Ejemplos prácticos de cómo usar el sistema de excepciones personalizado en diferentes escenarios.

## Estructura del Sistema_v5

```
Sistema_v5/
├── pjn/
│   ├── exceptions.py        # Sistema de excepciones personalizado
│   ├── models/              # Modelos de datos (Actuacion, Expediente, etc.)
│   ├── parsers/             # Parsers para transformar datos HTML
│   ├── scraping/            # Lógica de extracción con Playwright
│   │   ├── base.py          # Utilidades base y autenticación
│   │   ├── actuaciones.py   # Extracción de actuaciones
│   │   ├── expedientes.py   # Búsqueda y selección de expedientes
│   │   └── entradas.py      # Extracción de entradas
│   └── scripts/             # Scripts ejecutables
│       └── rf_test_extraccion_completa.py
└── documentacion/           # Esta carpeta
```

## Sistema de Excepciones

Sistema_v5 implementa un sistema robusto de excepciones personalizadas:

- **PJNError** - Excepción base para todos los errores del sistema
- **AutenticacionError** - Errores de login y credenciales
- **ExtraccionError** - Errores durante scraping de datos
- **ParsingError** - Errores al procesar/transformar datos
- **DescargaError** - Errores al descargar archivos
- **ValidacionError** - Errores de validación de entrada
- **SistemaError** - Errores de configuración o estado interno

Ver [refactorizacion_excepciones.md](./refactorizacion_excepciones.md) para detalles completos.

## Uso Rápido

### Importar Excepciones

```python
from Sistema_v5.pjn import (
    PJNError,
    CredencialesFaltantes,
    ExtraccionError,
)
```

### Manejo de Errores

```python
try:
    # Tu código aquí
    pass
except CredencialesFaltantes:
    print("Configure PJN_USER y PJN_PASSWORD")
except ExtraccionError as e:
    print(f"Error extrayendo datos: {e}")
except PJNError as e:
    print(f"Error del sistema PJN: {e}")
```

## Recursos Adicionales

- **Documentación general del proyecto:** `/docs/`
- **Inventario de funciones:** `/docs/Sistema_v5_modulos_pjn.md`
- **Documentación Sistema_v4:** `/Sistema_v4/documentacion/`

## Contribuir

Al agregar nueva funcionalidad al Sistema_v5:

1. Usa las excepciones personalizadas apropiadas
2. Documenta funciones públicas con docstrings
3. Agrega ejemplos de uso si es relevante
4. Actualiza esta documentación según corresponda

---

**Última actualización:** Octubre 2025
**Mantenido por:** Equipo sintaXis