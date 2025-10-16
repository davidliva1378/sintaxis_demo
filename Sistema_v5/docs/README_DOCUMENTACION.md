# 📚 Sistema_v5 - Índice de Documentación

**Versión:** 5.5
**Última actualización:** 2025-10-15
**Estado:** Producción Ready ✅
**Líneas de código:** ~5,776 líneas Python

---

## 🎯 Inicio Rápido

### ¿Qué es Sistema_v5?

Sistema_v5 es un framework completo de web scraping para el Portal Judicial Nacional (PJN) de Argentina, diseñado con arquitectura modular, altamente reutilizable y fácilmente extensible a otros portales.

### Características Principales

- ✅ **Arquitectura Modular**: Separación clara de responsabilidades
- ✅ **Funciones Puras**: Extracción sin side effects, ideal para composición
- ✅ **Manejo de Errores Estandarizado**: Excepciones jerárquicas con stack traces
- ✅ **Configuración Centralizada**: Un solo punto de configuración
- ✅ **Estrategias de Paginación**: Adaptable a diferentes frameworks web
- ✅ **Persistencia Separada**: Funciones de I/O independientes
- ✅ **Type Hints Completos**: Completamente tipado para mejor IDE support
- ✅ **Logging Estructurado**: Sistema de logging configurable
- ✅ **Retrocompatible**: Código legacy sigue funcionando

### Estado del Proyecto

```
🔴 CRÍTICA:  [████] 100% (4/4 completadas) ✅
🟠 ALTA:     [████] 100% (3/3 completadas) ✅
🟡 MEDIA:    [██░] 67% (2/3 completadas)
🟢 BAJA:     [░░░] 0% (0/5 completadas)

TOTAL: 60% (9/15 mejoras)
```

---

## 📖 Documentación Disponible

### 1. DOCUMENTACION_COMPLETA.md

**📘 Referencia completa del sistema**

Contiene:
- Arquitectura del sistema
- API Reference de todos los módulos
- Modelos de datos
- Configuración
- Excepciones
- Descripción detallada de cada función pública

**Cuándo usar:**
- Necesitas entender cómo funciona un módulo específico
- Buscas la signatura exacta de una función
- Quieres conocer qué excepciones puede lanzar una función
- Necesitas documentación de referencia técnica

**[→ Ver DOCUMENTACION_COMPLETA.md](DOCUMENTACION_COMPLETA.md)**

---

### 2. DOCUMENTACION_GUIAS.md

**📗 Guías prácticas y casos de uso**

Contiene:
- Inicio rápido
- Guías paso a paso por caso de uso:
  - Monitoreo diario de notificaciones
  - Extracción completa de expediente
  - Búsqueda masiva con filtros
  - Pipeline completo con procesamiento
- Patrones de diseño recomendados
- Ejemplos completos funcionales
- Testing
- Troubleshooting

**Cuándo usar:**
- Es tu primera vez usando el sistema
- Quieres ver ejemplos completos de código
- Necesitas resolver un problema específico (troubleshooting)
- Buscas mejores prácticas

**[→ Ver DOCUMENTACION_GUIAS.md](DOCUMENTACION_GUIAS.md)**

---

### 3. INVENTARIO_FUNCIONES.md

**📋 Inventario exhaustivo de todas las funciones**

Contiene:
- Lista completa de todas las funciones del sistema
- Signaturas completas con tipos
- Descripción de cada función
- Parámetros y valores de retorno
- Excepciones que puede lanzar
- Clasificación por módulo y estado
- Estadísticas del código

**Cuándo usar:**
- Buscas una función específica
- Quieres ver todas las funciones disponibles de un módulo
- Necesitas un "mapa" rápido del código
- Quieres estadísticas del proyecto

**[→ Ver INVENTARIO_FUNCIONES.md](INVENTARIO_FUNCIONES.md)**

---

### 4. ROADMAP.md

**🗺️ Hoja de ruta de mejoras**

Contiene:
- Todas las mejoras planificadas y completadas
- Estado de cada mejora
- Progreso general del proyecto
- Archivos modificados por mejora
- Ejemplos de uso de nuevas features

**Cuándo usar:**
- Quieres saber qué mejoras se han implementado
- Necesitas ver el progreso del proyecto
- Buscas ejemplos de nuevas funcionalidades
- Quieres contribuir al proyecto

**[→ Ver ROADMAP.md](ROADMAP.md)**

---

### 5. MEJORAS_IMPLEMENTADAS.md

**📝 Documentación detallada de mejoras**

Contiene:
- Descripción completa de cada mejora
- Ejemplos de código antes/después
- Motivación de cada cambio
- Impacto en el sistema

**Cuándo usar:**
- Quieres entender por qué se hizo un cambio
- Necesitas migrar código legacy a nuevas funciones
- Buscas ejemplos de refactoring

**[→ Ver MEJORAS_IMPLEMENTADAS.md](MEJORAS_IMPLEMENTADAS.md)**

---

### 6. MEJORA_6_EJEMPLO.md

**🔄 Ejemplos de estrategias de paginación**

Contiene:
- Uso básico (retrocompatible)
- Uso con estrategia PrimeFaces
- Crear estrategias personalizadas
- Ejemplos para Bootstrap, infinite scroll, etc.
- Estrategias mock para testing

**Cuándo usar:**
- Necesitas adaptar el scraper a otro portal
- Quieres customizar la paginación
- Necesitas testing sin browser real

**[→ Ver MEJORA_6_EJEMPLO.md](MEJORA_6_EJEMPLO.md)**

---

## 🚀 Flujo de Aprendizaje Recomendado

### Para Principiantes

1. **Inicio:** Lee la introducción en [DOCUMENTACION_COMPLETA.md](DOCUMENTACION_COMPLETA.md)
2. **Primer script:** Sigue "Inicio Rápido" en [DOCUMENTACION_GUIAS.md](DOCUMENTACION_GUIAS.md)
3. **Caso de uso:** Encuentra tu caso en [DOCUMENTACION_GUIAS.md](DOCUMENTACION_GUIAS.md)
4. **Referencia:** Consulta funciones específicas en [DOCUMENTACION_COMPLETA.md](DOCUMENTACION_COMPLETA.md)

### Para Usuarios Avanzados

1. **Explorar:** Revisa [INVENTARIO_FUNCIONES.md](INVENTARIO_FUNCIONES.md) para ver todas las funciones
2. **Patrones:** Lee "Patrones de Diseño" en [DOCUMENTACION_GUIAS.md](DOCUMENTACION_GUIAS.md)
3. **Customizar:** Usa [MEJORA_6_EJEMPLO.md](MEJORA_6_EJEMPLO.md) para estrategias personalizadas
4. **Troubleshooting:** Consulta "Troubleshooting" en [DOCUMENTACION_GUIAS.md](DOCUMENTACION_GUIAS.md)

### Para Contribuidores

1. **Roadmap:** Revisa [ROADMAP.md](ROADMAP.md) para ver qué falta
2. **Arquitectura:** Entiende la estructura en [DOCUMENTACION_COMPLETA.md](DOCUMENTACION_COMPLETA.md)
3. **Mejoras:** Lee [MEJORAS_IMPLEMENTADAS.md](MEJORAS_IMPLEMENTADAS.md) para entender el estilo
4. **Testing:** Sigue ejemplos de testing en [DOCUMENTACION_GUIAS.md](DOCUMENTACION_GUIAS.md)

---

## 📊 Estructura del Proyecto

```
Sistema_v5/
├── pjn/                          # 🎯 Código principal
│   ├── config.py                 # Configuración
│   ├── exceptions.py             # Excepciones
│   ├── selectores.py             # Selectores CSS
│   │
│   ├── models/                   # Modelos de datos
│   │   ├── actuacion.py
│   │   ├── entrada.py
│   │   └── expediente.py
│   │
│   ├── parsers/                  # Parsers HTML → Models
│   │   ├── actuaciones_parser.py
│   │   ├── entradas_parser.py
│   │   └── expedientes_parser.py
│   │
│   ├── scraping/                 # Módulo de scraping
│   │   ├── base.py
│   │   ├── actuaciones.py        # Extracción de actuaciones
│   │   ├── entradas.py           # Extracción de entradas
│   │   ├── expedientes.py        # Extracción de expedientes
│   │   └── pagination.py         # Estrategias de paginación
│   │
│   ├── persistence/              # Persistencia de datos
│   │   └── actuaciones.py
│   │
│   └── utils/                    # Utilidades
│       └── logging.py
│
├── 📚 DOCUMENTACIÓN              # Toda la documentación
│   ├── README_DOCUMENTACION.md   # 👈 Este archivo
│   ├── DOCUMENTACION_COMPLETA.md # Referencia completa
│   ├── DOCUMENTACION_GUIAS.md    # Guías y ejemplos
│   ├── INVENTARIO_FUNCIONES.md   # Inventario de funciones
│   ├── ROADMAP.md                # Hoja de ruta
│   ├── MEJORAS_IMPLEMENTADAS.md  # Mejoras detalladas
│   └── MEJORA_6_EJEMPLO.md       # Ejemplos de paginación
│
└── datos_extraidos/              # Datos extraídos (gitignored)
```

---

## 🔑 Conceptos Clave

### Funciones Puras vs Deprecated

**✅ Funciones Puras (Recomendadas):**
- No guardan archivos automáticamente
- Retornan modelos de datos
- Fáciles de testear y componer
- Ejemplo: `extraer_actuaciones_datos()`

**⚠️ Funciones Deprecated:**
- Guardan archivos automáticamente
- Mezclan extracción y persistencia
- Mantienen retrocompatibilidad
- Ejemplo: `extraer_actuaciones_completas()`

### Manejo de Excepciones

```
Exception
└── PJNError (base)
    └── ExtraccionError
        ├── TimeoutExtraccion
        └── ActuacionesNoDisponibles
```

Todas las funciones modernas lanzan excepciones específicas que puedes capturar.

### Estrategias de Paginación

El sistema usa el patrón Strategy para paginación, permitiendo:
- Adaptar a diferentes frameworks (PrimeFaces, Bootstrap, etc.)
- Testing con mocks
- Customización sin modificar código core

---

## 💡 Ejemplos Rápidos

### Extraer Expedientes

```python
from pjn.scraping.expedientes import extraer_expedientes_completos_modelos

expedientes, motivo, metadata = await extraer_expedientes_completos_modelos(
    page,
    max_paginas=10,
    fecha_corte="2024-01-01",
)

for exp in expedientes:
    print(f"{exp.numero}: {exp.caratula}")
```

### Extraer Actuaciones

```python
from pjn.scraping.actuaciones import extraer_actuaciones_datos

archivo = await extraer_actuaciones_datos(page, expediente_datos)

for act in archivo.actuaciones:
    print(f"{act.fecha}: {act.tipo} - {act.detalle}")
```

### Extraer Entradas

```python
from pjn.scraping.entradas import extraer_entradas_datos

entradas = await extraer_entradas_datos(
    page,
    incluir_tipos=("N",),  # Solo notificaciones
    fecha_desde="2024-01-01",
)
```

---

## 🛠️ Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd Sistema_v5

# Instalar dependencias
pip install playwright pandas
playwright install chromium

# Opcional: configurar .env
cp .env.example .env
```

---

## 📞 Soporte

### Tengo una pregunta sobre cómo usar una función

→ Consulta [DOCUMENTACION_COMPLETA.md](DOCUMENTACION_COMPLETA.md) para API reference

### Necesito un ejemplo completo de código

→ Ve a [DOCUMENTACION_GUIAS.md](DOCUMENTACION_GUIAS.md) para ejemplos por caso de uso

### No encuentro la función que necesito

→ Revisa [INVENTARIO_FUNCIONES.md](INVENTARIO_FUNCIONES.md) para ver todas las funciones

### Algo no funciona como esperaba

→ Consulta "Troubleshooting" en [DOCUMENTACION_GUIAS.md](DOCUMENTACION_GUIAS.md)

### Quiero adaptar el sistema a otro portal

→ Lee [MEJORA_6_EJEMPLO.md](MEJORA_6_EJEMPLO.md) sobre estrategias de paginación

### Tengo código legacy que usar funciones deprecadas

→ Lee [MEJORAS_IMPLEMENTADAS.md](MEJORAS_IMPLEMENTADAS.md) para migrar

---

## 📈 Estadísticas del Proyecto

- **Total líneas de código:** ~5,776 líneas Python
- **Funciones públicas:** 42
- **Funciones deprecated:** 6
- **Clases:** 15
- **Protocols:** 1
- **Módulos:** 11
- **Tests:** Ejemplos completos disponibles
- **Documentación:** 7 archivos completos
- **Estado:** Producción Ready ✅

---

## 🎯 Próximos Pasos

1. **Lee la introducción:** [DOCUMENTACION_COMPLETA.md](DOCUMENTACION_COMPLETA.md)
2. **Prueba el primer script:** [DOCUMENTACION_GUIAS.md → Inicio Rápido](DOCUMENTACION_GUIAS.md#inicio-rápido)
3. **Explora casos de uso:** [DOCUMENTACION_GUIAS.md → Guías](DOCUMENTACION_GUIAS.md#guías-por-caso-de-uso)
4. **Consulta funciones:** [INVENTARIO_FUNCIONES.md](INVENTARIO_FUNCIONES.md)

---

## ✅ Checklist de Lectura

- [ ] He leído la introducción en DOCUMENTACION_COMPLETA.md
- [ ] He probado el script de inicio rápido
- [ ] Conozco la diferencia entre funciones puras y deprecated
- [ ] Sé cómo manejar excepciones del sistema
- [ ] He revisado los ejemplos de mi caso de uso
- [ ] Conozco las mejores prácticas
- [ ] Sé dónde buscar troubleshooting

---

**¿Listo para comenzar? → [DOCUMENTACION_GUIAS.md → Inicio Rápido](DOCUMENTACION_GUIAS.md#inicio-rápido)**

---

**Última actualización:** 2025-10-15
**Versión de documentación:** 1.0
**Mantenido por:** Sistema_v5 Team
