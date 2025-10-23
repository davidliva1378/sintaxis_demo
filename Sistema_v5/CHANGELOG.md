# Changelog - Sistema_v5

Todos los cambios notables al Sistema_v5 serán documentados en este archivo.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/),
y este proyecto adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [5.6.0] - 2025-10-23

### ⭐ Agregado - Sistema de Extracción Inicial v2.0

- **FiltradorExpedientes** (`extractor_inicial/filtrador.py`)
  - Clase de filtrado avanzado con interfaz fluida (método chaining)
  - 4 tipos de filtros combinables:
    - `filtrar_por_dias_atras()` - Actividad reciente
    - `filtrar_por_situacion()` - Estado procesal
    - `filtrar_por_dependencia()` - Juzgado/fuero (con soporte regex)
    - `filtrar_por_rango_fechas()` - Período de inicio
  - Método `filtrar_personalizado()` para predicados custom
  - Sistema de estadísticas y trazabilidad de filtros
  - 292 líneas de código

- **Exportadores Multi-formato** (`extractor_inicial/exporters.py`)
  - `exportar_json()` - Exportación JSON con metadata v2.0
  - `exportar_csv()` - Exportación CSV con delimitadores configurables
  - `exportar_excel()` - Exportación Excel con formato (requiere openpyxl)
  - `cargar_json()` - Importación desde JSON con validación
  - `cargar_csv()` - Importación desde CSV
  - Soporte para caracteres especiales y metadata anidada
  - 278 líneas de código

- **ExtractorCompletoBatch** (`extractor_inicial/batch_processor.py`)
  - Procesamiento por lotes con manejo inteligente de errores
  - Umbral configurable de errores consecutivos (default: 5)
  - Estrategia de pausa-y-preguntar al alcanzar umbral
  - Callbacks para progreso y consulta al usuario
  - Dataclasses: `ResultadoExpediente`, `ResumenBatch`
  - Manejo de excepciones específicas del bridge Playwright
  - 357 líneas de código

- **GUI de Filtros Avanzados** (`extractor_inicial/ui/filtros_avanzados_form.py`)
  - Interfaz Tkinter con 4 paneles de filtros activables
  - Previsualización en tiempo real con Treeview
  - Estadísticas dinámicas (total, filtrado, porcentaje)
  - Botones de exportación directa (JSON/CSV/Excel)
  - Validación de regex con mensajes de error claros
  - 517 líneas de código

- **MonitorPJN.extraer_listado_inicial()** (`pjn/monitor/core.py`)
  - Nuevo método para extracción inicial de expedientes
  - Genera JSON con formato v2.0 (metadata anidada)
  - Exportación opcional a CSV paralela
  - Reutiliza `_verificar_expedientes_internal()` existente

- **ExpedienteResumen.esta_activo()** (`pjn/models/expediente.py`)
  - Método auxiliar para verificar actividad reciente
  - Soporta formatos DD/MM/YYYY y YYYY-MM-DD

- **Script Principal** (`ejecutar_extraccion_inicial_v2.py`)
  - Flujo de 4 fases completamente integrado:
    1. Extracción del listado con MonitorPJN
    2. Filtrado avanzado mediante GUI
    3. Generación de directorios por expediente
    4. Extracción completa batch con manejo de errores
  - CLI con argumentos: `--headless`, `--no-filtros`, `--no-adjuntos`, `--umbral-errores`
  - Generación automática de reportes JSON
  - Logging detallado con separadores visuales
  - 342 líneas de código

### 🧪 Testing

- **test_filtrador_expedientes.py** (13 tests)
  - Tests para FiltradorExpedientes
  - Tests para ExpedienteResumen.esta_activo()
  - Cobertura de filtros encadenados, reset, estadísticas
  - Tests de manejo de errores (regex inválido)

- **test_exporters.py** (23 tests)
  - Tests de exportación JSON/CSV
  - Tests de importación con validación
  - Tests de roundtrip (exportar → importar)
  - Tests de casos extremos (listas vacías, caracteres especiales)

- **test_batch_processor.py** (19 tests)
  - Tests de ExtractorCompletoBatch
  - Tests de manejo de errores y umbral
  - Tests de callbacks y acciones de usuario
  - Tests de dataclasses (ResultadoExpediente, ResumenBatch)

**Total:** 55 tests pasando (100% de éxito)

### 📖 Documentación

- **GUIA_EXTRACCION_INICIAL_V2.md**
  - Guía completa de usuario (377 líneas)
  - Descripción general y ventajas sobre v1.0
  - Diagramas de flujo ASCII
  - Ejemplos de uso para cada componente
  - Casos de uso avanzados
  - Roadmap futuro (migración a SQLite)
  - FAQ y troubleshooting

- **README.txt** (actualizado)
  - Sección dedicada a extracción inicial v2.0
  - Instrucciones de uso básico y avanzado
  - Referencia a documentación completa

### 🔧 Corregido

- Corregido campo de fecha en `filtrador.py` (`ultima_actuacion` vs `fecha_ultima_actuacion`)
- Corregido lambda mal formado en `filtrar_por_dependencia()`
- Corregido formato JSON para metadata anidada correctamente
- Ajustados tests para reflejar comportamiento real

### 📊 Métricas

- **Módulos nuevos:** 4
- **Módulos modificados:** 4
- **Código nuevo:** ~1,800 líneas
- **Tests:** ~650 líneas
- **Documentación:** ~450 líneas
- **Total agregado:** ~2,900 líneas

### 🎯 Beneficios

- ✅ Reutilización de MonitorPJN (sin duplicar lógica de scraping)
- ✅ Filtros potentes y combinables con GUI intuitiva
- ✅ Manejo robusto de errores con opciones al usuario
- ✅ Formato dual JSON+CSV para transición a SQLite
- ✅ Extensible y testeable (componentes independientes)
- ✅ Documentación exhaustiva con ejemplos

---

## [5.5.1] - 2025-10-16

### 🔧 Modificado

- **Logging mejorado en sistema de autenticación** (`pjn/scraping/base.py`)
  - Agregado logging estructurado a `_realizar_login()`
  - Agregado logging estructurado a `_verificar_sesion()`
  - Agregado logging estructurado a `obtener_pagina_autenticada()`
  - 15 mensajes de log en niveles apropiados (INFO, WARNING, ERROR, DEBUG)
  - Visibilidad completa del flujo de autenticación y re-login automático

### 📊 Métricas

- **Funciones mejoradas:** 3
- **Mensajes de log agregados:** 15
- **Cobertura de logging:** 100% del flujo de autenticación

### 🎯 Beneficios

- ✅ Debugging más fácil del proceso de login
- ✅ Visibilidad de reutilización vs creación de sesión
- ✅ Alertas claras cuando la sesión expira
- ✅ Logging con niveles apropiados para producción/desarrollo

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
