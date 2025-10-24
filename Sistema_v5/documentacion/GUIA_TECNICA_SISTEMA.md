# Guía Técnica - Sistema_v5

**Versión:** 5.6
**Última actualización:** 17 de octubre, 2025
**Estado:** Producción Ready ✅

---

## Índice

1. [Sistema de Logging](#1-sistema-de-logging)
2. [Sistema de Autenticación](#2-sistema-de-autenticación)
3. [Selectores CSS](#3-selectores-css)
4. [Sistema de Excepciones](#4-sistema-de-excepciones)
5. [Testing](#5-testing)

---

## 1. Sistema de Logging

### 1.1 Descripción

Sistema de logging configurable con colores, niveles ajustables y soporte para archivo y consola.

### 1.2 Uso Básico

```python
from pjn.utils.logging import setup_logging, get_logger

# Configurar logging (una vez al inicio)
setup_logging(level="INFO", log_file="logs/sistema.log")

# Obtener logger en tu módulo
logger = get_logger(__name__)

# Usar en código
logger.info("✅ Operación exitosa")
logger.warning("⚠️ Advertencia")
logger.error("❌ Error crítico")
logger.debug("🔍 Detalle de debugging")
```

### 1.3 Configuración Avanzada

```python
# Solo consola (sin archivo)
setup_logging(level="DEBUG")

# Solo archivo (sin consola)
setup_logging(level="INFO", log_file="app.log", use_colors=False)

# Personalizado
setup_logging(
    level="DEBUG",
    log_file="logs/sistema.log",
    use_colors=True,
    log_format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### 1.4 Configuración vía Variables de Entorno

```bash
# En .env o shell
export LOG_LEVEL=DEBUG
export LOG_FILE=logs/sistema.log
export LOG_COLORS=true

# Python usará automáticamente estas variables
python mi_script.py
```

**Variables soportadas:**
- `LOG_LEVEL`: DEBUG, INFO, WARNING, ERROR, CRITICAL
- `LOG_FILE`: Ruta al archivo de log (opcional)
- `LOG_COLORS`: true/false para colores en consola

### 1.5 Mejores Prácticas

#### ✅ Hacer
```python
# Mensajes descriptivos con emojis
logger.info("✅ Expediente %s extraído correctamente", numero)
logger.error("❌ Error al conectar con %s: %s", url, error)

# Context managers para timing
import time
start = time.time()
# ... operación
logger.info("⏱️ Operación completada en %.2fs", time.time() - start)

# Logging de excepciones
try:
    resultado = operacion_riesgosa()
except Exception as e:
    logger.error("❌ Falló operación: %s", e, exc_info=True)
```

#### ❌ Evitar
```python
# NO: Logging en loop sin control
for item in items:
    logger.info("Procesando %s", item)  # Spam de logs

# NO: Datos sensibles en logs
logger.info("Password: %s", password)  # ¡NUNCA!

# NO: Logging excesivo de detalles
logger.debug("Variable x=%s y=%s z=%s ...", x, y, z)  # Innecesario
```

### 1.6 Niveles de Log y Uso

| Nivel | Uso | Ejemplo |
|-------|-----|---------|
| **DEBUG** | Detalles internos | "Selectores encontrados: 5" |
| **INFO** | Operaciones normales | "✅ 10 expedientes extraídos" |
| **WARNING** | Situaciones inusuales | "⚠️ Timeout, reintentando..." |
| **ERROR** | Errores recuperables | "❌ No se pudo descargar PDF" |
| **CRITICAL** | Errores fatales | "💥 Sistema no disponible" |

### 1.7 Formato de Mensajes

**Emojis recomendados:**
- ✅ Éxito
- ❌ Error
- ⚠️ Advertencia
- 🔍 Debug/investigación
- ⏱️ Timing/performance
- 📄 Archivo/documento
- 🌐 Red/HTTP
- 💾 Base de datos/persistencia
- 🔐 Autenticación/seguridad

---

## 2. Sistema de Autenticación

### 2.1 Descripción

Sistema automático de autenticación con persistencia de sesión, re-login transparente y logging completo.

### 2.2 Uso Básico

```python
from pjn.scraping import obtener_pagina_autenticada

# Context manager (recomendado)
async with obtener_pagina_autenticada() as page:
    await page.goto("https://portalpjn.pjn.gov.ar/...")
    # Tu código aquí
    # Sesión se cierra automáticamente al salir
```

### 2.3 Uso Avanzado

```python
# Reutilizar sesión guardada
async with obtener_pagina_autenticada(
    archivo_sesion=Path("mi_sesion.json"),
    intentar_reutilizar=True  # Intenta usar sesión existente
) as page:
    # Si sesión válida, no hace login
    # Si expiró, hace login automáticamente
    await page.goto("...")
```

```python
# Login forzado (siempre nuevo)
async with obtener_pagina_autenticada(
    intentar_reutilizar=False
) as page:
    # Siempre hace login nuevo
    await page.goto("...")
```

```python
# Credenciales custom
async with obtener_pagina_autenticada(
    usuario="mi_usuario",
    contraseña="mi_password"
) as page:
    await page.goto("...")
```

### 2.4 Configuración de Credenciales

**Opción 1: Variables de entorno** (recomendado)
```bash
# En .env
PJN_USER=tu_usuario
PJN_PASSWORD=tu_password

# Código Python
async with obtener_pagina_autenticada() as page:
    # Usa automáticamente PJN_USER y PJN_PASSWORD
    ...
```

**Opción 2: Parámetros directos**
```python
async with obtener_pagina_autenticada(
    usuario="tu_usuario",
    contraseña="tu_password"
) as page:
    ...
```

### 2.5 Persistencia de Sesión

**Ubicación default:**
```
pjn/scraping/session_pjn.json
```

**Contenido:**
```json
{
  "cookies": [...],
  "origins": [...]
}
```

**Ciclo de vida:**
1. Primera ejecución: Login → Guarda sesión
2. Siguientes ejecuciones: Carga sesión → Valida → Usa
3. Si sesión inválida: Re-login → Actualiza sesión

### 2.6 Verificación de Sesión

El sistema verifica automáticamente navegando a la página principal y detectando si aparece el login form:

```python
# Internamente hace:
await page.goto(PJN_LOGIN_URL)
login_form = await page.query_selector(SEL_AUTH.LOGIN_FORM)

if login_form:
    # Sesión inválida, hacer login
else:
    # Sesión válida, continuar
```

### 2.7 Modo Headless

```python
# Headless (sin interfaz gráfica)
async with obtener_pagina_autenticada(headless=True) as page:
    # Más rápido, para producción
    ...

# Con interfaz (debugging)
async with obtener_pagina_autenticada(headless=False) as page:
    # Ver qué pasa, para desarrollo
    ...
```

### 2.8 Logging de Autenticación

El sistema loggea cada paso:

```
INFO: 🔐 Intentando reutilizar sesión desde session_pjn.json
INFO: ✅ Sesión existente válida, no es necesario hacer login
```

```
WARNING: ⚠️ Sesión expirada, realizando login nuevamente
INFO: 🔐 Iniciando sesión con usuario: mi_usuario
INFO: ✅ Login exitoso, sesión guardada
```

---

## 3. Selectores CSS

### 3.1 Descripción

Todos los selectores CSS del portal PJN centralizados en `pjn/selectores.py` con documentación de fragilidad.

### 3.2 Uso

```python
from pjn.selectores import SEL_AUTH, SEL_ENTRADAS, SEL_EXPEDIENTES, SEL_ACTUACIONES

# Autenticación
await page.fill(SEL_AUTH.USERNAME, "usuario")
await page.fill(SEL_AUTH.PASSWORD, "contraseña")
await page.click(SEL_AUTH.LOGIN_BUTTON)

# Entradas
contenedor = await page.query_selector(SEL_ENTRADAS.CONTENEDOR_SCROLL)
filas = await page.query_selector_all(SEL_ENTRADAS.FILA_ENTRADA)

# Expedientes
tabla = await page.query_selector(SEL_EXPEDIENTES.TABLA)
siguiente = await page.query_selector(SEL_EXPEDIENTES.BOTON_SIGUIENTE)

# Actuaciones
await page.click(SEL_ACTUACIONES.TAB_ACTUACIONES)
filas_act = await page.query_selector_all(SEL_ACTUACIONES.FILA_ACTUACION)
```

### 3.3 Códigos de Fragilidad

Cada selector tiene un código de fragilidad documentado:

| Código | Significado | Acción |
|--------|-------------|--------|
| **🟢 ESTABLE** | CSS estándar, improbable que cambie | Usar directamente |
| **🟡 MODERADO** | Puede cambiar con actualizaciones | Agregar test |
| **🔴 FRÁGIL** | Framework-specific, puede cambiar | Monitorear |
| **⚫ CRÍTICO** | Generado dinámicamente | Considerar alternativa |

### 3.4 Mantenimiento

Si el portal PJN cambia:

1. Actualizar solo `pjn/selectores.py`
2. Todo el código usa automáticamente el nuevo selector
3. Tests alertan si selector roto

**Ejemplo:**
```python
# Si PJN cambia de #j_id1234 a #j_id5678
# Antes: 50 lugares para actualizar ❌
# Ahora: 1 lugar (selectores.py) ✅
```

---

## 4. Sistema de Excepciones

### 4.1 Jerarquía

```
PJNError (base)
├── AutenticacionError
│   ├── CredencialesFaltantes
│   └── SesionInvalida
├── ExtraccionError
│   ├── ExpedienteNoEncontrado
│   ├── ActuacionesNoDisponibles
│   └── TimeoutExtraccion
├── ParsingError
│   ├── FormatoInvalido
│   └── DatosIncompletos
├── DescargaError
│   ├── ArchivoNoDisponible
│   └── DescargaFallida
├── ValidacionError
│   └── ParametroInvalido
└── SistemaError
    ├── ConfiguracionError
    └── EstadoInvalido
```

### 4.2 Uso

```python
from pjn import (
    PJNError,
    CredencialesFaltantes,
    ExpedienteNoEncontrado,
    TimeoutExtraccion,
)

try:
    async with obtener_pagina_autenticada() as page:
        expediente = await extraer_expediente(page, numero)

except CredencialesFaltantes:
    logger.error("❌ Configure PJN_USER y PJN_PASSWORD")

except ExpedienteNoEncontrado:
    logger.warning("⚠️ Expediente %s no existe", numero)

except TimeoutExtraccion as e:
    logger.error("⏱️ Timeout: %s", e)

except PJNError as e:
    # Captura cualquier error del sistema
    logger.error("❌ Error PJN: %s", e)
```

### 4.3 Excepciones con Contexto

```python
# ParametroInvalido con detalles
raise ParametroInvalido(
    parametro="max_paginas",
    valor=-5,
    razon="debe ser > 0"
)

# DescargaFallida con reintentos
raise DescargaFallida(
    mensaje="No se pudo descargar archivo",
    intentos=3,
    error_original=exception
)
```

---

## 5. Testing

### 5.1 Estado Actual

```
Tests: 71/71 pasando (100%)
Cobertura: 32% (target: 80%)
```

### 5.2 Ejecutar Tests

```bash
# Todos los tests
pytest tests/ -v

# Solo tests rápidos
pytest tests/ -v -m "not slow"

# Con cobertura
pytest tests/ --cov=pjn --cov-report=html

# Tests específicos
pytest tests/test_models.py -v
pytest tests/test_config.py -v
```

### 5.3 Escribir Tests

```python
# tests/test_mi_modulo.py
import pytest
from pjn.mi_modulo import mi_funcion

class TestMiFuncion:
    def test_caso_basico(self):
        resultado = mi_funcion(input="test")
        assert resultado == "esperado"

    def test_caso_error(self):
        with pytest.raises(ValueError):
            mi_funcion(input="invalido")

    @pytest.mark.asyncio
    async def test_caso_async(self):
        resultado = await mi_funcion_async()
        assert resultado is not None
```

### 5.4 Fixtures

```python
@pytest.fixture
def config_basica():
    return ExtraccionExpedientesConfig(max_paginas=5)

def test_con_fixture(config_basica):
    assert config_basica.max_paginas == 5
```

---

## Apéndice: Comandos Útiles

### Desarrollo

```bash
# Instalar dependencias
pip install -r requirements.txt

# Linter
ruff check pjn/

# Type checking
mypy pjn/

# Format code
black pjn/

# Run tests
pytest tests/ -v

# Performance benchmarks
python scripts/performance_benchmark.py

# Memory profiling
python scripts/memory_profiler.py
```

### Producción

```bash
# Set environment
export PJN_USER=usuario
export PJN_PASSWORD=password
export LOG_LEVEL=INFO
export LOG_FILE=logs/produccion.log

# Run
python mi_script_produccion.py
```

---

**Referencias:**
- [README.md](README.md) - Inicio rápido
- [SPRINT_2_REPORTE_FINAL.md](SPRINT_2_REPORTE_FINAL.md) - Últimas mejoras
- [TRACKING_SPRINTS.md](TRACKING_SPRINTS.md) - Roadmap completo

---

**Última actualización:** 17 de octubre, 2025
**Versión:** 5.6
