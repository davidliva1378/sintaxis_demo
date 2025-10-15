# Reporte de Testing - Sistema_v5

**Fecha de análisis:** 15 de Octubre 2025
**Total de tests:** 48
**Tests fallidos:** 3 (6.25%)
**Tests pasando:** 45 (93.75%)
**Cobertura general:** 32%

---

## Estado Actual de Testing

### ✅ Tests Exitosos (45/48)

#### Parsers (7 tests)
- ✅ `test_parse_entrada_normaliza_fecha_y_trim_campos`
- ✅ `test_normalizar_fecha_entrada_devuelve_original_si_formato_desconocido`
- ✅ `test_deduplicar_historial_identifica_claves_unicas`
- ✅ `test_parse_expediente_resumen_normaliza_fecha_y_descarta_incompletos`
- ✅ `test_normalizar_fecha_actuacion_deja_valor_si_no_puede_convertir`
- ✅ `test_construir_encabezado_actuaciones_calcula_metricas`
- ✅ `test_normalizar_nombre_expediente_generar_slug_seguro`

#### Scraping Utils (11 tests)
- ✅ `test_limpiar_texto_elimina_saltos_y_trim`
- ✅ `test_normalizar_texto_minusculas_sin_acentos`
- ✅ `test_normalizar_fecha_admite_varios_formatos`
- ✅ `test_normalizar_fecha_retorna_original_si_no_identifica_formato`
- ✅ `test_generar_hash_identificador_deterministico`
- ✅ `test_normalizar_numero_expediente_reemplaza_caracteres_no_seguros`
- ✅ `test_actualizar_metricas_descargas_en_json_recalcula_encabezado`
- ✅ `test_to_iso_acepta_varios_formatos`
- ✅ `test_parse_fechas_exactas_convierte_a_set_iso`
- ✅ `test_parse_fecha_limite_devuelve_date`
- ✅ `test_base_key_y_event_key_normalizan_correctamente`

#### Integración (3 tests)
- ✅ `test_obtener_actuaciones_modelos_async_convierte_dicts`
- ✅ `test_extraer_expedientes_completos_modelos_envuelve_resumenes`
- ✅ `test_extraer_entradas_pjn_modelos_retorna_dataclasses`

#### Extensiones y Orden (18 tests)
- ✅ Tests de manejo de extensiones de archivos
- ✅ Tests de orden de expedientes (v3 y v4)

---

## ❌ Tests Fallidos (3/48)

### 1. `test_historicas_continuan_numeracion`
**Archivo:** `tests/test_actuaciones_indices.py`
**Error:** `KeyError: 'Hash'`

```python
assert "Error general: KeyError: 'Hash'" is None
```

**Causa:** La función `extraer_actuaciones_completas` espera que los dicts de actuaciones incluyan el campo `Hash`, pero el mock en el test no lo proporciona.

**Solución:**
```python
# En el test, agregar el campo Hash a los mocks:
{"Indice": 1, "TieneArchivo": False, "Hash": "mock_hash_1"}
```

---

### 2. `test_construir_nombre_archivo_prioriza_nombre_descarga`
**Archivo:** `tests/test_pjn_parsers.py`

```python
assert '2024-02-01_deo_hash123.pdf' == '2024-02-01-deo-hash123.pdf'
# Esperado: guiones, Real: guiones bajos
```

**Causa:** La función `construir_nombre_archivo_normalizado` cambió para usar guiones bajos (`_`) en lugar de guiones (`-`).

**Solución:** Actualizar la expectativa del test para reflejar el comportamiento actual:
```python
assert nombre == "2024-02-01_deo_hash123.pdf"
```

---

### 3. `test_construir_nombre_archivo_usa_extension_de_url_si_no_hay_descarga`
**Archivo:** `tests/test_pjn_parsers.py`

```python
assert 'jsp' == '.jsp'
# Esperado: con punto, Real: sin punto
```

**Causa:** La función ahora retorna extensiones sin el punto inicial.

**Solución:** Actualizar el test:
```python
assert extension == "jsp"
```

---

## Análisis de Cobertura por Módulo

### 🟢 Alta Cobertura (>80%)

| Módulo | Cobertura | Tests |
|--------|-----------|-------|
| `models/entrada.py` | 100% | ✅ Completo |
| `models/actuacion.py` | 97% | ✅ Casi completo |
| `parsers/expedientes_parser.py` | 93% | ✅ Muy bueno |
| `parsers/entradas_parser.py` | 92% | ✅ Muy bueno |
| `models/expediente.py` | 88% | ✅ Bueno |
| `exceptions.py` | 83% | ✅ Bueno |

### 🟡 Cobertura Media (40-70%)

| Módulo | Cobertura | Gaps Identificados |
|--------|-----------|-------------------|
| `parsers/actuaciones_parser.py` | 68% | Falta testing de funciones de construcción de archivos |
| `utils/logging.py` | 64% | Falta testing de configuración avanzada |
| `scraping/actuaciones_utils.py` | 55% | Faltan tests de utilidades específicas |
| `models/_utils.py` | 46% | Varios helpers sin tests |
| `scraping/base.py` | 40% | Faltan tests de autenticación y navegación |

### 🔴 Cobertura Baja (<25%)

| Módulo | Cobertura | Estado |
|--------|-----------|--------|
| `scraping/entradas.py` | 24% | ❌ Crítico - core scraping sin tests |
| `scraping/actuaciones.py` | 15% | ❌ Crítico - core scraping sin tests |
| `scraping/expedientes.py` | 16% | ❌ Crítico - core scraping sin tests |
| `scripts/rf_test_extraccion_completa.py` | 0% | ⚠️ Script manual (ok) |
| `test_logging_demo.py` | 0% | ⚠️ Script de demo (ok) |

---

## Áreas Sin Tests

### 🚨 Crítico - Requiere Atención Inmediata

1. **Scrapers principales (actuaciones, entradas, expedientes)**
   - Cobertura: 15-24%
   - **Riesgo:** Alto - son el core del sistema
   - **Impacto:** Bugs pueden pasar desapercibidos en producción

2. **Autenticación (`scraping/base.py`)**
   - Funciones sin tests:
     - `obtener_pagina_autenticada()`
     - `verificar_sesion_valida()`
     - Manejo de storage state

3. **Manejo de errores y excepciones**
   - Falta testing de:
     - Cadenas de excepciones (exception chaining)
     - Recovery de errores
     - Timeouts y reintentos

### ⚠️ Importante - Planificar

4. **Descargas de archivos**
   - `descargar_archivos_actuaciones()` - 0% cobertura
   - `descargar_archivos_de_json()` - 0% cobertura
   - Manejo de reintentos y timeouts

5. **Paginación y navegación**
   - `extraer_expedientes_completos()` - Sin tests
   - Manejo de cambios de página
   - Detección de fin de listado

6. **Sistema de logging**
   - `setup_logging()` - Parcial
   - Configuración desde env vars
   - Rotación de archivos

### 💡 Deseable - Mejoras Futuras

7. **Tests de integración end-to-end**
   - Flujo completo: búsqueda → extracción → descarga
   - Tests con datos reales (staging)
   - Tests de regresión

8. **Tests de performance**
   - Benchmarks de parsers
   - Memoria con grandes datasets
   - Concurrencia de descargas

---

## Fixtures Disponibles

### Datos de Prueba (`tests/fixtures/pjn/`)

```
pjn/
├── actuacion.json        ✅ Estructura completa de actuación
├── entrada.json          ✅ Estructura de entrada/notificación
└── expediente_resumen.json ✅ Resumen de expediente
```

**Recomendación:** Agregar más fixtures para:
- Actuaciones históricas
- Expedientes con múltiples páginas
- Casos edge (datos faltantes, formatos raros)
- Respuestas de error del servidor

---

## Plan de Acción Recomendado

### Fase 1: Arreglar Tests Fallidos (Inmediato)
- [ ] Fix `test_historicas_continuan_numeracion` - Agregar campo Hash
- [ ] Fix `test_construir_nombre_archivo_prioriza_nombre_descarga` - Actualizar expectativa
- [ ] Fix `test_construir_nombre_archivo_usa_extension_de_url_si_no_hay_descarga` - Actualizar expectativa

**Prioridad:** 🔴 ALTA
**Tiempo estimado:** 30 minutos

---

### Fase 2: Tests Críticos de Scrapers (1-2 días)

#### 2.1 Actuaciones (`scraping/actuaciones.py`)
- [ ] Test de extracción de página única
- [ ] Test de paginación múltiple
- [ ] Test de actuaciones históricas
- [ ] Test de descarga de archivos (mock)
- [ ] Test de reintentos en timeout

#### 2.2 Entradas (`scraping/entradas.py`)
- [ ] Test de scroll infinito
- [ ] Test de filtros por fecha
- [ ] Test de filtros por tipo (N/D)
- [ ] Test de deduplicación
- [ ] Test de detección de "No hay más eventos"

#### 2.3 Expedientes (`scraping/expedientes.py`)
- [ ] Test de búsqueda por número/año
- [ ] Test de extracción completa con paginación
- [ ] Test de ordenamiento
- [ ] Test de detección de duplicados
- [ ] Test de límites (tiempo, páginas, fecha)

**Prioridad:** 🔴 ALTA
**Tiempo estimado:** 2 días

---

### Fase 3: Autenticación y Base (1 día)

#### 3.1 Autenticación (`scraping/base.py`)
- [ ] Test de login exitoso
- [ ] Test de credenciales inválidas
- [ ] Test de sesión expirada
- [ ] Test de storage state
- [ ] Test de verificación de sesión

#### 3.2 Utilidades Base
- [ ] Tests de normalización adicionales
- [ ] Tests de generación de hashes
- [ ] Tests de manejo de fechas edge cases

**Prioridad:** 🟡 MEDIA
**Tiempo estimado:** 1 día

---

### Fase 4: Coverage Completo (2-3 días)

#### 4.1 Parsers faltantes
- [ ] Completar tests de `actuaciones_parser.py` (68% → 90%)
- [ ] Tests de casos edge en parsers

#### 4.2 Modelos
- [ ] Tests de validaciones
- [ ] Tests de conversiones (to_dict, from_dict)
- [ ] Tests de modelos anidados

#### 4.3 Excepciones
- [ ] Tests de jerarquía completa
- [ ] Tests de exception chaining
- [ ] Tests de mensajes contextuales

**Prioridad:** 🟢 BAJA
**Tiempo estimado:** 2-3 días

---

### Fase 5: Tests de Integración (2 días)

- [ ] Test E2E: Búsqueda → Extracción → JSON
- [ ] Test E2E: Búsqueda → Extracción → Descarga
- [ ] Test E2E: Monitoreo de entradas
- [ ] Tests con mocks de Playwright
- [ ] Tests con datos de staging

**Prioridad:** 🟢 BAJA
**Tiempo estimado:** 2 días

---

## Métricas Objetivo

| Métrica | Actual | Objetivo Fase 2 | Objetivo Final |
|---------|--------|-----------------|----------------|
| **Cobertura Total** | 32% | 60% | 80%+ |
| **Tests Pasando** | 93.75% | 100% | 100% |
| **Scrapers** | 15-24% | 70%+ | 85%+ |
| **Parsers** | 68-93% | 85%+ | 95%+ |
| **Models** | 88-97% | 95%+ | 98%+ |

---

## Herramientas Recomendadas

### Testing
- ✅ `pytest` - Framework principal
- ✅ `pytest-cov` - Cobertura de código
- ⏳ `pytest-asyncio` - Tests async/await
- ⏳ `pytest-mock` - Mocks avanzados
- ⏳ `playwright-pytest` - Tests con Playwright

### CI/CD
- ⏳ GitHub Actions para tests automáticos
- ⏳ Pre-commit hooks para tests locales
- ⏳ Reportes de cobertura en PRs

### Calidad
- ⏳ `ruff` - Linting
- ⏳ `mypy` - Type checking
- ⏳ `black` - Formatting

---

## Comandos Útiles

```bash
# Ejecutar todos los tests
python -m pytest tests/ -v

# Tests con cobertura
python -m pytest tests/ --cov=Sistema_v5 --cov-report=html

# Solo tests fallidos
python -m pytest tests/ --lf

# Tests de un módulo específico
python -m pytest tests/test_pjn_parsers.py -v

# Ver cobertura en navegador
python -m pytest tests/ --cov=Sistema_v5 --cov-report=html && start htmlcov/index.html
```

---

## Conclusión

**Estado general:** 🟡 **ACEPTABLE pero necesita mejoras**

### Fortalezas
✅ Parsers bien testeados (68-93%)
✅ Modelos con alta cobertura (88-100%)
✅ Tests de integración básicos funcionando
✅ Fixtures bien estructurados

### Debilidades Críticas
❌ Scrapers principales con <25% cobertura
❌ Sin tests de autenticación
❌ Sin tests de descargas
❌ 3 tests fallando actualmente

### Recomendación

**Prioridad inmediata:** Arreglar los 3 tests fallidos (30 min) y luego enfocarse en **Fase 2** (tests de scrapers) que son el core del sistema y tienen cobertura crítica.

Con 2-3 días de trabajo enfocado en testing, se puede llevar la cobertura de **32% → 60%** y eliminar los riesgos críticos.
