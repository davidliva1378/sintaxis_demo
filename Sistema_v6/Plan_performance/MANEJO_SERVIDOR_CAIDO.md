# Plan: Manejo de Servidor PJN Caído/Inaccesible

## Objetivo
Detectar proactivamente cuando el servidor del Portal Judicial Nacional (PJN) está caído o inaccesible, y manejar la situación de forma elegante sin bloquear el sistema.

---

## Problema Actual

Cuando el servidor PJN está caído o en mantenimiento:

❌ **Síntomas:**
- Error: `[Errno 32] Broken pipe`
- Navegador se cierra inesperadamente
- Sistema queda esperando indefinidamente
- Usuario no recibe información clara sobre qué pasó

❌ **Comportamiento Actual:**
```
Usuario inicia extracción → Navegador intenta conectar → PJN no responde →
Timeout → Navegador crash → Broken pipe → Error genérico al usuario
```

---

## Solución Propuesta

### **FASE 1: Health Check Previo**

Verificar disponibilidad del PJN **ANTES** de iniciar cualquier extracción.

#### Implementación:

```python
# Archivo: pjn/health/checker.py

import asyncio
import logging
from datetime import datetime
from playwright.async_api import async_playwright, TimeoutError

logger = logging.getLogger(__name__)


class PJNHealthChecker:
    """Verifica disponibilidad del Portal Judicial Nacional."""

    def __init__(
        self,
        login_url: str = "https://portalpjn.pjn.gov.ar/inicio",
        timeout_ms: int = 15000,
    ):
        self.login_url = login_url
        self.timeout_ms = timeout_ms

    async def check_availability(self) -> tuple[bool, str]:
        """Verifica si el PJN está disponible.

        Returns:
            tuple[disponible, mensaje]:
                - disponible: True si el servidor responde
                - mensaje: Descripción del resultado
        """
        logger.info("🔍 Verificando disponibilidad del PJN...")

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                try:
                    # Intentar cargar la página de login
                    response = await page.goto(
                        self.login_url,
                        timeout=self.timeout_ms,
                        wait_until="domcontentloaded"
                    )

                    # Verificar código de respuesta
                    if response and response.status == 200:
                        logger.info("✅ PJN disponible (HTTP 200)")
                        return True, "Servidor PJN disponible"
                    elif response:
                        logger.warning(f"⚠️ PJN respondió con HTTP {response.status}")
                        return False, f"Servidor PJN respondió con código {response.status}"
                    else:
                        logger.error("❌ No se recibió respuesta del PJN")
                        return False, "Servidor PJN no respondió"

                except TimeoutError:
                    logger.error(f"❌ Timeout ({self.timeout_ms}ms) conectando al PJN")
                    return False, f"Servidor PJN no respondió en {self.timeout_ms/1000}s"

                except Exception as e:
                    logger.error(f"❌ Error verificando PJN: {e}")
                    return False, f"Error conectando al servidor: {str(e)}"

                finally:
                    await page.close()
                    await context.close()
                    await browser.close()

        except Exception as e:
            logger.error(f"❌ Error fatal en health check: {e}")
            return False, f"Error crítico: {str(e)}"
```

---

### **FASE 2: Detección de Errores Específicos**

Diferenciar entre tipos de errores para dar feedback claro al usuario.

#### Clasificación de Errores:

```python
# Archivo: pjn/errors/classifier.py

from enum import Enum
from typing import Optional


class ErrorType(Enum):
    """Tipos de errores en extracción."""
    SERVIDOR_CAIDO = "servidor_caido"
    BROKEN_PIPE = "broken_pipe"
    TIMEOUT_NAVEGACION = "timeout_navegacion"
    CREDENCIALES_INVALIDAS = "credenciales_invalidas"
    ERROR_PARSING = "error_parsing"
    ERROR_RED = "error_red"
    ERROR_DESCONOCIDO = "error_desconocido"


def clasificar_error(exception: Exception) -> tuple[ErrorType, str]:
    """Clasifica una excepción en un tipo de error específico.

    Args:
        exception: Excepción capturada

    Returns:
        tuple[tipo_error, mensaje_usuario]:
            - tipo_error: Tipo de error clasificado
            - mensaje_usuario: Mensaje legible para mostrar al usuario
    """
    error_str = str(exception).lower()

    # Broken pipe (navegador cerrado)
    if "broken pipe" in error_str or "errno 32" in error_str:
        return (
            ErrorType.BROKEN_PIPE,
            "El navegador se cerró inesperadamente. Posible causa: servidor PJN inaccesible."
        )

    # Timeout de navegación
    if "timeout" in error_str or "timed out" in error_str:
        return (
            ErrorType.TIMEOUT_NAVEGACION,
            "Timeout esperando respuesta del servidor. El PJN puede estar lento o caído."
        )

    # Errores de red
    if any(keyword in error_str for keyword in ["connection", "network", "dns", "resolve"]):
        return (
            ErrorType.ERROR_RED,
            "Error de conexión. Verifica tu conexión a internet o el estado del servidor PJN."
        )

    # Credenciales inválidas
    if "login" in error_str or "authentication" in error_str:
        return (
            ErrorType.CREDENCIALES_INVALIDAS,
            "Error de autenticación. Verifica tus credenciales del PJN."
        )

    # Error desconocido
    return (
        ErrorType.ERROR_DESCONOCIDO,
        f"Error inesperado: {str(exception)[:100]}"
    )
```

---

### **FASE 3: Reintentos Inteligentes con Backoff Exponencial**

Reintentar automáticamente con esperas crecientes.

#### Implementación:

```python
# Archivo: pjn/retry/strategy.py

import asyncio
import logging
from datetime import datetime
from typing import Callable, TypeVar, Optional

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryStrategy:
    """Estrategia de reintentos con backoff exponencial."""

    def __init__(
        self,
        max_reintentos: int = 5,
        delay_inicial_segundos: int = 30,
        factor_multiplicador: float = 2.0,
        max_delay_segundos: int = 300,  # 5 minutos
    ):
        self.max_reintentos = max_reintentos
        self.delay_inicial = delay_inicial_segundos
        self.factor = factor_multiplicador
        self.max_delay = max_delay_segundos

    def calcular_delay(self, intento: int) -> int:
        """Calcula el delay para el siguiente reintento.

        Backoff exponencial: delay = inicial * (factor ^ (intento - 1))
        Con límite máximo.

        Args:
            intento: Número de intento (1-indexed)

        Returns:
            Segundos a esperar antes del próximo intento
        """
        delay = self.delay_inicial * (self.factor ** (intento - 1))
        return min(int(delay), self.max_delay)

    async def ejecutar_con_reintentos(
        self,
        operacion: Callable[[], T],
        descripcion: str = "Operación",
        callback_antes_reintento: Optional[Callable[[int, int], None]] = None,
    ) -> T:
        """Ejecuta una operación con reintentos automáticos.

        Args:
            operacion: Función async a ejecutar
            descripcion: Descripción de la operación (para logs)
            callback_antes_reintento: Función opcional a llamar antes de cada reintento

        Returns:
            Resultado de la operación

        Raises:
            Exception: Si todos los reintentos fallan
        """
        ultimo_error = None

        for intento in range(1, self.max_reintentos + 1):
            try:
                logger.info(f"🔄 {descripcion} - Intento {intento}/{self.max_reintentos}")
                resultado = await operacion()
                logger.info(f"✅ {descripcion} - Éxito en intento {intento}")
                return resultado

            except Exception as e:
                ultimo_error = e
                logger.warning(f"❌ {descripcion} - Fallo intento {intento}: {e}")

                if intento < self.max_reintentos:
                    delay = self.calcular_delay(intento)
                    logger.info(f"⏱️ Esperando {delay}s antes del reintento {intento + 1}...")

                    if callback_antes_reintento:
                        callback_antes_reintento(intento, delay)

                    await asyncio.sleep(delay)
                else:
                    logger.error(f"💥 {descripcion} - Agotados {self.max_reintentos} reintentos")

        # Si llegamos aquí, todos los reintentos fallaron
        raise Exception(
            f"Operación '{descripcion}' falló tras {self.max_reintentos} reintentos. "
            f"Último error: {ultimo_error}"
        )


# Uso ejemplo:
# retry_strategy = RetryStrategy(max_reintentos=5, delay_inicial_segundos=30)
# resultado = await retry_strategy.ejecutar_con_reintentos(
#     operacion=lambda: verificar_servidor_pjn(),
#     descripcion="Health check del PJN",
#     callback_antes_reintento=lambda intento, delay: print(f"Reintentando en {delay}s...")
# )
```

---

### **FASE 4: Integración en ExtractorMasivo**

Modificar `extraccion_masiva/extractor_masivo.py` para usar health check.

#### Código a Agregar:

```python
# En extraccion_masiva/extractor_masivo.py

from pjn.health.checker import PJNHealthChecker
from pjn.errors.classifier import clasificar_error, ErrorType
from pjn.retry.strategy import RetryStrategy


class ExtractorMasivo:
    # ... código existente ...

    async def extraer_listado_completo(
        self,
        fecha_corte: str | None = None,
        callback_progreso: Callable[[SesionExtraccion], None] | None = None,
    ) -> SesionExtraccion:
        """Extrae expedientes con health check previo."""

        # 1. HEALTH CHECK PREVIO (con reintentos)
        health_checker = PJNHealthChecker()
        retry_strategy = RetryStrategy(
            max_reintentos=3,
            delay_inicial_segundos=60,
            max_delay_segundos=300
        )

        def notificar_reintento_health_check(intento: int, delay: int):
            """Notifica al usuario que se está reintentando el health check."""
            sesion.mensaje = (
                f"⏳ Servidor PJN no disponible. "
                f"Reintentando en {delay}s... (intento {intento}/3)"
            )
            if callback_progreso:
                callback_progreso(sesion)

        try:
            disponible, mensaje = await retry_strategy.ejecutar_con_reintentos(
                operacion=health_checker.check_availability,
                descripcion="Verificación PJN",
                callback_antes_reintento=notificar_reintento_health_check
            )

            if not disponible:
                sesion.estado = "error"
                sesion.mensaje = f"❌ Servidor PJN no disponible: {mensaje}"
                if callback_progreso:
                    callback_progreso(sesion)
                raise Exception(f"Servidor PJN inaccesible: {mensaje}")

            logger.info(f"✅ Health check exitoso: {mensaje}")

        except Exception as e:
            logger.error(f"❌ Health check falló tras reintentos: {e}")
            sesion.estado = "error"
            sesion.mensaje = (
                "❌ No se pudo conectar al servidor PJN tras múltiples intentos. "
                "El servidor puede estar en mantenimiento. Intenta más tarde."
            )
            if callback_progreso:
                callback_progreso(sesion)
            raise

        # 2. CONTINUAR CON EXTRACCIÓN NORMAL
        # ... resto del código existente ...

        # 3. MEJORAR MANEJO DE ERRORES
        except Exception as e_intento:
            # Clasificar el error
            tipo_error, mensaje_usuario = clasificar_error(e_intento)

            # Logging según tipo
            if tipo_error == ErrorType.SERVIDOR_CAIDO or tipo_error == ErrorType.BROKEN_PIPE:
                logger.error(
                    f"🔴 Servidor PJN probablemente caído. "
                    f"Error: {mensaje_usuario}"
                )
                sesion.estado = "error"
                sesion.mensaje = (
                    "❌ Servidor PJN inaccesible durante extracción. "
                    "Puede estar en mantenimiento. La extracción se detendrá."
                )
            elif tipo_error == ErrorType.TIMEOUT_NAVEGACION:
                logger.warning(f"⏱️ Timeout: {mensaje_usuario}")
                sesion.estado = "error"
                sesion.mensaje = f"⏱️ {mensaje_usuario}"
            else:
                logger.error(f"❌ Error: {mensaje_usuario}")
                sesion.estado = "error"
                sesion.mensaje = mensaje_usuario

            # Notificar al usuario
            if callback_progreso:
                callback_progreso(sesion)

            # Decidir si reintentar o abortar
            if tipo_error == ErrorType.SERVIDOR_CAIDO:
                # No reintentar, abortar completamente
                raise Exception(f"Servidor PJN caído: {mensaje_usuario}")
            elif tipo_error == ErrorType.BROKEN_PIPE:
                # Reintentar con navegador nuevo (ya implementado)
                continue
            else:
                # Otros errores: aplicar lógica existente
                # ... código existente ...
```

---

## Flujo Completo con Health Check

```
┌─────────────────────────────────────────┐
│ Usuario inicia extracción masiva       │
└────────────────┬────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────┐
│ FASE 1: Health Check del PJN           │
│ (con reintentos automáticos)            │
└────────────┬───────────────┬────────────┘
             │               │
             │               │
      ✅ Disponible    ❌ No disponible
             │               │
             │               ▼
             │    ┌──────────────────────┐
             │    │ Notificar al usuario │
             │    │ "PJN en mantenimiento│
             │    │  intenta más tarde"  │
             │    └──────────────────────┘
             │               │
             │               ▼
             │           ABORTAR
             │
             ▼
┌─────────────────────────────────────────┐
│ FASE 2: Iniciar extracción normal      │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ Durante extracción: detectar errores   │
└────────────┬───────────┬────────────────┘
             │           │
      Normal │           │ Error
             │           ▼
             │    ┌──────────────────────┐
             │    │ Clasificar error:    │
             │    │ - Servidor caído     │
             │    │ - Broken pipe        │
             │    │ - Timeout            │
             │    │ - Otros              │
             │    └──────┬───────────────┘
             │           │
             │           ▼
             │    ┌──────────────────────┐
             │    │ Mensaje claro        │
             │    │ al usuario           │
             │    └──────┬───────────────┘
             │           │
             │           ▼
             │    ┌──────────────────────┐
             │    │ Servidor caído?      │
             │    │ → ABORTAR            │
             │    │ Otros errores?       │
             │    │ → REINTENTAR         │
             │    └──────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│ Extracción completada exitosamente     │
└─────────────────────────────────────────┘
```

---

## Mensajes al Usuario

### Antes (Sin Health Check):
```
❌ "Error en extracción: [Errno 32] Broken pipe"
```
Usuario no sabe qué pasó ni qué hacer.

### Después (Con Health Check):
```
🔍 "Verificando disponibilidad del servidor PJN..."

Caso 1 - Servidor disponible:
✅ "Servidor PJN disponible. Iniciando extracción..."

Caso 2 - Servidor caído:
❌ "Servidor PJN no disponible (Timeout 15s).
    Reintentando en 60 segundos... (intento 1/3)"

Caso 3 - Servidor caído tras reintentos:
❌ "No se pudo conectar al servidor PJN tras 3 intentos.
    El servidor puede estar en mantenimiento.
    Por favor intenta más tarde."

Caso 4 - Error durante extracción:
❌ "Servidor PJN inaccesible durante extracción.
    Puede estar en mantenimiento.
    La extracción se detuvo en página 60/137."
```

Mucho más claro y útil para el usuario.

---

## Archivos a Crear/Modificar

### Nuevos Archivos:

1. **`pjn/health/checker.py`**
   - Clase `PJNHealthChecker` para verificar disponibilidad

2. **`pjn/errors/classifier.py`**
   - Enum `ErrorType` con tipos de errores
   - Función `clasificar_error()` para categorizar excepciones

3. **`pjn/retry/strategy.py`**
   - Clase `RetryStrategy` con backoff exponencial
   - Método `ejecutar_con_reintentos()`

### Archivos a Modificar:

1. **`extraccion_masiva/extractor_masivo.py`**
   - Agregar health check al inicio de `extraer_listado_completo()`
   - Mejorar clasificación de errores en el `except`
   - Mensajes más claros al usuario

---

## Testing

### Prueba 1: Servidor PJN Disponible
```python
# Simular servidor disponible
health_checker = PJNHealthChecker()
disponible, mensaje = await health_checker.check_availability()
assert disponible == True
assert "disponible" in mensaje.lower()
```

### Prueba 2: Servidor PJN Caído
```python
# Simular servidor caído (cambiar URL a una inválida)
health_checker = PJNHealthChecker(login_url="https://servidor-invalido.example.com")
disponible, mensaje = await health_checker.check_availability()
assert disponible == False
assert "timeout" in mensaje.lower() or "error" in mensaje.lower()
```

### Prueba 3: Reintentos con Backoff
```python
retry_strategy = RetryStrategy(max_reintentos=3, delay_inicial_segundos=5)

contador = [0]
async def operacion_que_falla_2_veces():
    contador[0] += 1
    if contador[0] < 3:
        raise Exception("Fallo simulado")
    return "Éxito"

resultado = await retry_strategy.ejecutar_con_reintentos(operacion_que_falla_2_veces)
assert resultado == "Éxito"
assert contador[0] == 3  # Falló 2 veces, éxito en la 3ra
```

---

## Beneficios

✅ **Detección temprana**: Saber ANTES de iniciar si el servidor está disponible
✅ **Mensajes claros**: Usuario entiende qué pasó y qué hacer
✅ **Reintentos automáticos**: No requiere intervención manual
✅ **Backoff exponencial**: No sobrecarga el servidor con reintentos rápidos
✅ **Clasificación de errores**: Diferentes estrategias según el tipo de error
✅ **Mejor UX**: Usuario informado en todo momento

---

## Próximos Pasos

1. ✅ **Documentar estrategia** (este archivo)
2. ⏳ Crear archivos nuevos (`health/checker.py`, `errors/classifier.py`, `retry/strategy.py`)
3. ⏳ Modificar `extractor_masivo.py` para integrar health check
4. ⏳ Agregar tests unitarios
5. ⏳ Probar en entorno real
6. ⏳ Ajustar timeouts y delays según comportamiento observado

---

## Notas de Implementación

- **No agregar ahora**: Esperar a que el PJN vuelva online para probar los cambios antibloqueo (v5.1.1)
- **Prioridad**: Media-baja (funcionalidad nice-to-have, no crítica)
- **Tiempo estimado**: 2-3 horas de implementación + 1 hora de testing
- **Dependencias**: Ninguna (usa librerías ya existentes)

---

**Fecha de creación**: 2025-11-15
**Autor**: Claude Code
**Estado**: Documentado, pendiente de implementación
