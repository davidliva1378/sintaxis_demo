# Mejora #6: Ejemplos de Uso - Estrategias de Paginación

## Uso Básico (Sin cambios para código existente)

```python
from pjn.scraping.expedientes import extraer_expedientes_completos

# El código existente funciona exactamente igual (retrocompatible)
expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    max_paginas=10,
    fecha_corte="2024-01-01",
)
```

## Uso con Estrategia PrimeFaces (Por Defecto)

```python
from pjn.scraping.expedientes import extraer_expedientes_completos
from pjn.scraping.pagination import PrimeFacesPaginationStrategy

# Usar estrategia PrimeFaces con configuración personalizada
strategy = PrimeFacesPaginationStrategy(
    timeout_ms=15_000,           # Esperar 15s para botón (vs 10s default)
    max_wait_content_ms=20_000,  # Esperar 20s para cambio de contenido
    poll_interval_ms=500,        # Polling cada 500ms (vs 400ms default)
)

expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    max_paginas=10,
    pagination_strategy=strategy,
)
```

## Crear Estrategia Personalizada

### Ejemplo: Estrategia para Bootstrap Pagination

```python
from typing import Protocol
from playwright.async_api import Page, Locator, TimeoutError, Error
from pjn.scraping.pagination import PaginationStrategy

class BootstrapPaginationStrategy:
    """Estrategia para paginación con Bootstrap."""

    def __init__(self, timeout_ms: int = 10_000):
        self.timeout_ms = timeout_ms

    async def navegar_siguiente(
        self,
        page: Page,
        tbody_locator: Locator,
        fingerprint_actual: str,
    ) -> tuple[bool, str | None]:
        """Navega usando controles de Bootstrap."""

        # Bootstrap usa clase .page-link para botones de paginación
        next_btn = page.locator('.pagination .page-item:not(.disabled) .page-link:has-text("›")')

        try:
            # Verificar que existe
            if await next_btn.count() == 0:
                return False, "sin_siguiente"

            # Hacer clic
            await next_btn.click(timeout=self.timeout_ms)

            # Esperar cambio de contenido (simplificado para ejemplo)
            await page.wait_for_timeout(1000)

            # Verificar cambio con fingerprint
            from pjn.scraping.expedientes import _tbody_fingerprint
            nuevo_fingerprint = await _tbody_fingerprint(tbody_locator)

            if nuevo_fingerprint == fingerprint_actual:
                return False, "fin_listado"

            return True, None

        except TimeoutError:
            return False, "siguiente_timeout"
        except Error as e:
            return False, "error_click"


# Usar la estrategia personalizada
from pjn.scraping.expedientes import extraer_expedientes_completos

custom_strategy = BootstrapPaginationStrategy(timeout_ms=15_000)

expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    max_paginas=10,
    pagination_strategy=custom_strategy,
)
```

### Ejemplo: Estrategia para Infinite Scroll

```python
class InfiniteScrollStrategy:
    """Estrategia para portales con scroll infinito."""

    async def navegar_siguiente(
        self,
        page: Page,
        tbody_locator: Locator,
        fingerprint_actual: str,
    ) -> tuple[bool, str | None]:
        """Navega haciendo scroll al final de la página."""

        # Hacer scroll hasta el fondo
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")

        # Esperar a que cargue más contenido
        await page.wait_for_timeout(2000)

        # Verificar si cambió el contenido
        from pjn.scraping.expedientes import _tbody_fingerprint
        nuevo_fingerprint = await _tbody_fingerprint(tbody_locator)

        if nuevo_fingerprint == fingerprint_actual:
            return False, "fin_listado"

        return True, None


# Usar
scroll_strategy = InfiniteScrollStrategy()

expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    max_paginas=50,
    pagination_strategy=scroll_strategy,
)
```

## Testing con Estrategias Mock

```python
class MockPaginationStrategy:
    """Estrategia de paginación para testing."""

    def __init__(self, max_pages: int = 3):
        self.current_page = 0
        self.max_pages = max_pages

    async def navegar_siguiente(
        self,
        page: Page,
        tbody_locator: Locator,
        fingerprint_actual: str,
    ) -> tuple[bool, str | None]:
        """Simula navegación sin hacer clic real."""

        self.current_page += 1

        if self.current_page >= self.max_pages:
            return False, "fin_listado"

        # Simular cambio de fingerprint
        return True, None


# Test
mock_strategy = MockPaginationStrategy(max_pages=2)

# Esto solo navegará 2 páginas sin importar lo que haya en el portal
expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    max_paginas=100,  # Aunque se configure 100, solo navegará 2
    pagination_strategy=mock_strategy,
)

assert motivo == "fin_listado"
```

## Ventajas del Diseño

1. **Retrocompatibilidad**: Código existente funciona sin cambios
2. **Flexibilidad**: Fácil adaptar a nuevos portales sin modificar código core
3. **Testabilidad**: Estrategias mock para testing sin browser
4. **Separación de responsabilidades**: Lógica de paginación aislada
5. **Extensibilidad**: Protocol permite crear estrategias sin herencia

## Migración Gradual

```python
# Paso 1: Código actual (sigue funcionando)
expedientes, motivo, metadata = await extraer_expedientes_completos(page)

# Paso 2: Agregar estrategia cuando sea necesario
from pjn.scraping.pagination import PrimeFacesPaginationStrategy

strategy = PrimeFacesPaginationStrategy()
expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    pagination_strategy=strategy,  # Solo este parámetro nuevo
)

# Paso 3: Eventualmente los selectores se pueden ignorar
# (la estrategia maneja sus propios selectores)
expedientes, motivo, metadata = await extraer_expedientes_completos(
    page,
    pagination_strategy=strategy,
    # sel_siguiente ya no es relevante con estrategia
)
```
