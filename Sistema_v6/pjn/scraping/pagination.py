"""Estrategias de paginación para diferentes portales web.

Este módulo define un Protocol para estrategias de paginación y proporciona
implementaciones concretas para diferentes frameworks de paginación web.
"""

from typing import Protocol, runtime_checkable

from playwright.async_api import Locator, Page, TimeoutError, Error

import logging
logger = logging.getLogger(__name__)


@runtime_checkable
class PaginationStrategy(Protocol):
    """Protocol para estrategias de paginación en portales web.

    Una estrategia de paginación encapsula la lógica específica necesaria para
    navegar entre páginas de resultados en un portal web particular.
    """

    async def navegar_siguiente(
        self,
        page: Page,
        tbody_locator: Locator,
        fingerprint_actual: str,
    ) -> tuple[bool, str | None]:
        """Navega a la siguiente página y verifica el cambio de contenido.

        Args:
            page: Página de Playwright.
            tbody_locator: Locator del tbody para verificar cambios.
            fingerprint_actual: Fingerprint del contenido antes de la navegación.

        Returns:
            tuple[exito, motivo_fallo]:
                - exito: True si navegó correctamente y cambió el contenido.
                - motivo_fallo: Código de error si falló, None si tuvo éxito.

        Códigos de error comunes:
            - "sin_siguiente": No existe botón siguiente.
            - "sin_siguiente_habilitado": Botón siguiente deshabilitado.
            - "siguiente_timeout": Timeout esperando botón.
            - "siguiente_deshabilitado": Botón se deshabilitó al hacer clic.
            - "error_click": Error al hacer clic.
            - "fin_listado": No cambió contenido (fin natural).
        """
        ...


class PrimeFacesPaginationStrategy:
    """Estrategia de paginación para portales que usan PrimeFaces.

    PrimeFaces es un framework de componentes UI para JSF (JavaServer Faces)
    muy utilizado en portales gubernamentales y empresariales.

    Esta estrategia maneja:
    - Múltiples selectores posibles para el botón "Siguiente"
    - Verificación de estado habilitado/deshabilitado
    - Espera con polling para detectar cambio de contenido
    - Fingerprinting para confirmar que cambió la página
    """

    def __init__(
        self,
        selector_siguiente: str | None = None,
        timeout_ms: int = 10_000,
        max_wait_content_ms: int = 12_000,
        poll_interval_ms: int = 400,
    ):
        """Inicializa la estrategia PrimeFaces.

        Args:
            selector_siguiente: Selector CSS del botón siguiente.
                Si es None, usa selectores por defecto comunes en PrimeFaces.
            timeout_ms: Timeout para esperar el botón (milisegundos).
            max_wait_content_ms: Timeout máximo para esperar cambio de contenido.
            poll_interval_ms: Intervalo de polling para verificar cambios.
        """
        if selector_siguiente is None:
            # Selectores comunes en PrimeFaces
            selector_siguiente = ", ".join([
                "a[aria-label='Siguiente']",
                "button[aria-label='Siguiente']",
                "a:has(span[title='Siguiente'])",
                "button:has(span[title='Siguiente'])",
                ".pagination li.next:not(.disabled) a",
                ".pagination a:has-text('Siguiente')",
                ".rf-ds-btn-next",
            ])

        self.selector_siguiente = selector_siguiente
        self.timeout_ms = timeout_ms
        self.max_wait_content_ms = max_wait_content_ms
        self.poll_interval_ms = poll_interval_ms

    async def navegar_siguiente(
        self,
        page: Page,
        tbody_locator: Locator,
        fingerprint_actual: str,
    ) -> tuple[bool, str | None]:
        """Navega a la siguiente página usando controles PrimeFaces.

        Args:
            page: Página de Playwright.
            tbody_locator: Locator del tbody para verificar cambios.
            fingerprint_actual: Fingerprint del tbody antes de hacer clic.

        Returns:
            tuple[exito, motivo_fallo]:
                - exito: True si navegó correctamente y cambió el contenido.
                - motivo_fallo: Código de error si falló, None si tuvo éxito.
        """
        # Buscar botón siguiente
        next_btn = page.locator(self.selector_siguiente)
        btn_count = await next_btn.count()
        if btn_count <= 0:
            return False, "sin_siguiente"

        # Buscar botón habilitado y visible
        boton: Locator | None = None
        for idx in range(btn_count):
            candidato = next_btn.nth(idx)
            if await self._is_enabled(candidato) and await candidato.is_visible():
                boton = candidato
                break

        if boton is None:
            return False, "sin_siguiente_habilitado"

        # Esperar que sea visible
        try:
            await boton.wait_for(state="visible", timeout=self.timeout_ms)
        except TimeoutError as exc:
            logger.warning("Botón 'Siguiente' no visible: %s", exc)
            return False, "siguiente_timeout"

        if not await self._is_enabled(boton):
            return False, "siguiente_deshabilitado"

        # Hacer clic
        try:
            await boton.click()
        except (TimeoutError, Error) as exc:
            logger.error("Fallo al hacer clic en 'Siguiente': %s", exc)
            return False, "error_click"

        # Esperar a que cambie el tbody
        fingerprint_cambio = await self._esperar_cambio_contenido(
            page,
            tbody_locator,
            fingerprint_actual,
        )

        if not fingerprint_cambio:
            return False, "fin_listado"

        return True, None

    async def _is_enabled(self, locator: Locator) -> bool:
        """Verifica si un locator está habilitado.

        Args:
            locator: Locator a verificar.

        Returns:
            bool: True si está habilitado, False en caso contrario.
        """
        try:
            return await locator.is_enabled()
        except Exception:
            return False

    async def _esperar_cambio_contenido(
        self,
        page: Page,
        tbody_locator: Locator,
        fingerprint_actual: str,
    ) -> bool:
        """Espera con polling a que cambie el contenido del tbody.

        Args:
            page: Página de Playwright.
            tbody_locator: Locator del tbody.
            fingerprint_actual: Fingerprint antes del cambio.

        Returns:
            bool: True si cambió el contenido, False si timeout.
        """
        from .expedientes import _tbody_fingerprint

        elapsed_ms = 0
        while elapsed_ms < self.max_wait_content_ms:
            despues = await _tbody_fingerprint(tbody_locator)
            if despues != fingerprint_actual:
                return True

            wait_time = min(self.poll_interval_ms, self.max_wait_content_ms - elapsed_ms)
            if wait_time <= 0:
                break

            await page.wait_for_timeout(wait_time)
            elapsed_ms += wait_time

        return False


# Estrategia por defecto (PrimeFaces)
DEFAULT_PAGINATION_STRATEGY = PrimeFacesPaginationStrategy()
