# Changelog - Sistema_v5

Todos los cambios notables al Sistema_v5 serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [5.1.0] - 2025-10-15

### ⭐ Agregado

- **Sistema de Selectores Centralizados** (`pjn/selectores.py`)
  - Módulo único para todos los selectores CSS del portal PJN
  - 4 clases de selectores: `AutenticacionSelectores`, `EntradasSelectores`, `ExpedientesSelectores`, `ActuacionesSelectores`
  - Funciones auxiliares: `escapar_id_jsf_para_css()`, `escapar_id_jsf_para_js()`
  - 31 constantes de selectores centralizadas
  - Instancias globales para fácil acceso: `SEL_AUTH`, `SEL_ENTRADAS`, etc.

- **Tests de Selectores** (`tests/test_selectores.py`)
  - 20 tests comprehensivos
  - Validación de todos los selectores
  - Tests de funciones de escape JSF
  - Tests de consistencia y duplicados
  - 100% cobertura de constantes

- **Documentación de Selectores** (`documentacion/pjn_selectores_tabla.md`)
  - Tabla completa de selectores con ubicaciones
  - Código de fragilidad (🟢🟡🔴) para cada selector
  - Guía de uso y ejemplos
  - Plan de mantenimiento ante cambios en PJN
  - Lista de selectores críticos para reemplazo

### 🔧 Modificado

- **Refactorizado código para usar selectores centralizados:**
  - `pjn/scraping/entradas.py` - 8 actualizaciones
  - `pjn/scraping/base.py` - 4 actualizaciones
  - `pjn/scraping/expedientes.py` - 7 actualizaciones
  - `pjn/scraping/actuaciones.py` - Funciones de escape migradas
  - `pjn/parsers/actuaciones_parser.py` - Icono de descarga

- **Documentación actualizada:**
  - `documentacion/README.md` - Agregada sección de selectores
  - Reorganizado índice con nuevos documentos
  - Agregadas guías de estilo y contribución
  - Actualizada estructura del proyecto

### 🐛 Corregido

- **Error de doble `##` en selectores JSF**
  - Problema: `escapar_id_jsf_para_css()` agregaba `#`, causando `##` en uso
  - Solución: Función ahora solo escapa, no agrega prefijos
  - Tests actualizados para reflejar comportamiento correcto
  - Error: `Page.inner_html: Unexpected token "#"` resuelto

### 📊 Métricas

- **Archivos creados:** 3 (selectores.py, test_selectores.py, pjn_selectores_tabla.md)
- **Archivos modificados:** 7
- **Tests agregados:** 20 (todos pasando)
- **Líneas de código:** ~570 nuevas líneas
- **Constantes eliminadas:** 10 duplicados

---

## [5.0.0] - 2025-10-14

### ⭐ Agregado

- **Sistema de Excepciones Personalizado** (`pjn/exceptions.py`)
  - Jerarquía completa de excepciones específicas del dominio
  - 15 tipos de excepciones especializadas
  - Documentación completa en `documentacion/refactorizacion_excepciones.md`

- **Sistema de Logging Configurable** (`pjn/utils/logging.py`)
  - Logging con colores ANSI
  - Configuración por variables de entorno
  - Niveles configurables (DEBUG, INFO, WARNING, ERROR, CRITICAL)
  - Soporte para archivo de log opcional

- **Modelos de Datos** (`pjn/models/`)
  - `Entrada`, `Expediente`, `Actuacion`, `ActuacionesArchivo`
  - Métodos `from_dict()` y `to_dict()` para serialización
  - Validación de datos con dataclasses

- **Parsers Especializados** (`pjn/parsers/`)
  - `entradas_parser.py` - Parsing de notificaciones
  - `expedientes_parser.py` - Parsing de expedientes
  - `actuaciones_parser.py` - Parsing de actuaciones

- **Scrapers Robustos** (`pjn/scraping/`)
  - `base.py` - Autenticación y gestión de sesiones
  - `entradas.py` - Scroll infinito para bandeja de entradas
  - `expedientes.py` - Búsqueda y paginación de expedientes
  - `actuaciones.py` - Extracción de actuaciones actuales e históricas

- **Script de Prueba** (`pjn/scripts/rf_test_extraccion_completa.py`)
  - Flujo completo de extracción interactivo
  - Manejo robusto de errores con excepciones personalizadas

### 📚 Documentación

- README principal del proyecto
- Guía de logging
- Sistema de logging técnico
- Reporte de testing
- Ejemplos de uso de excepciones

### 🧪 Testing

- Tests de parsers (7 tests)
- Tests de scraping utils (11 tests)
- Tests de integración (3 tests)
- Tests de extensiones y orden (18 tests)
- **Total:** 48 tests, 93.75% pasando

---

## Leyenda de Símbolos

- ⭐ **Agregado:** Nueva funcionalidad
- 🔧 **Modificado:** Cambios en funcionalidad existente
- 🐛 **Corregido:** Bugs resueltos
- 🗑️ **Eliminado:** Funcionalidad removida
- 🔒 **Seguridad:** Correcciones de seguridad
- 📚 **Documentación:** Solo cambios en documentación
- 🧪 **Testing:** Cambios en tests

---

## Versionado

El formato de versión es `MAJOR.MINOR.PATCH`:

- **MAJOR:** Cambios incompatibles con versiones anteriores
- **MINOR:** Nueva funcionalidad compatible con versiones anteriores
- **PATCH:** Correcciones de bugs compatibles con versiones anteriores
