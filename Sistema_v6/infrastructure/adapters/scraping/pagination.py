"""Estrategias de paginación para diferentes frameworks web.

Este módulo define un Protocol para estrategias de paginación y proporciona
implementaciones concretas para diferentes frameworks de paginación web.

Actualmente soporta:
- **PrimeFaces**: Framework JSF común en portales gubernamentales

Migrado de: Sistema_v5/pjn/scraping/pagination.py
"""

from __future__ import annotations

import logging
import re
from typing import Protocol, runtime_checkable

from playwright.async_api import Error, Locator, Page, TimeoutError

logger = logging.getLogger(__name__)

# Constantes para verificación de elementos habilitados
_FORM_CONTROL_TAGS = {
    "button",
    "input",
    "select",
    "textarea",
    "option",
    "optgroup",
}


async def _is_locator_enabled(locator: Locator) -> bool:
    """Determina si un locator corresponde a un control habilitado.

    Verifica múltiples condiciones para determinar si un elemento está
    realmente habilitado y listo para interactuar:

    1. Si es un form control (button, input, etc.), usa .is_enabled()
    2. Verifica atributo aria-disabled
    3. Verifica atributo disabled
    4. Verifica clase CSS "disabled"

    Args:
        locator: Locator de Playwright a verificar

    Returns:
        bool: True si el elemento está habilitado, False en caso contrario

    Example:
        >>> boton = page.locator("button.siguiente")
        >>> if await _is_locator_enabled(boton):
        ...     await boton.click()

    Note:
        Esta función es más robusta que el simple .is_enabled() porque
        verifica múltiples indicadores de estado deshabilitado que son
        comunes en frameworks web modernos (especialmente PrimeFaces).
    """
    try:
        # Obtener tag name del elemento
        tag_name = await locator.evaluate("el => el.tagName.toLowerCase()")
    except Error:
        # Si falla al obtener el tag, asumir deshabilitado
        logger.debug("No se pudo obtener tag name del locator")
        return False

    # Si es un form control nativo, usar is_enabled() de Playwright
    if tag_name in _FORM_CONTROL_TAGS:
        try:
            return await locator.is_enabled()
        except Error:
            pass  # Continuar con verificaciones manuales

    # Verificar aria-disabled (usado por frameworks de accesibilidad)
    try:
        aria_disabled = (await locator.get_attribute("aria-disabled")) or ""
        if aria_disabled.strip().lower() in {"true", "1"}:
            logger.debug("Elemento deshabilitado por aria-disabled")
            return False

        # Verificar atributo disabled (HTML estándar)
        if await locator.get_attribute("disabled") is not None:
            logger.debug("Elemento deshabilitado por atributo disabled")
            return False

        # Verificar clase "disabled" (común en Bootstrap, PrimeFaces, etc.)
        class_attr = (await locator.get_attribute("class")) or ""
    except Error:
        # Si falla cualquier verificación de atributos, asumir deshabilitado
        logger.debug("Error verificando atributos del locator")
        return False

    # Buscar palabra "disabled" en las clases (respetando límites de palabra)
    if re.search(r"\bdisabled\b", class_attr, re.IGNORECASE):
        logger.debug("Elemento deshabilitado por clase CSS 'disabled'")
        return False

    # Si pasó todas las verificaciones, está habilitado
    logger.debug("Elemento verificado como habilitado")
    return True


@runtime_checkable
class PaginationStrategy(Protocol):
    """Protocol para estrategias de paginación en portales web.

    Una estrategia de paginación encapsula la lógica específica necesaria para
    navegar entre páginas de resultados en un portal web particular.

    Este Protocol permite implementar diferentes estrategias para distintos
    frameworks de paginación (PrimeFaces, Bootstrap, Material UI, etc.)
    """

    async def navegar_siguiente(
        self,
        page: Page,
        tbody_locator: Locator,
        fingerprint_actual: str,
    ) -> tuple[bool, str | None]:
        """Navega a la siguiente página y verifica el cambio de contenido.

        Args:
            page: Página de Playwright
            tbody_locator: Locator del tbody para verificar cambios
            fingerprint_actual: Fingerprint del contenido antes de la navegación

        Returns:
            Tupla (exito, motivo_fallo):
                - exito: True si navegó correctamente y cambió el contenido
                - motivo_fallo: Código de error si falló, None si tuvo éxito

        Códigos de error comunes:
            - "sin_siguiente": No existe botón siguiente
            - "sin_siguiente_habilitado": Botón siguiente deshabilitado
            - "siguiente_timeout": Timeout esperando botón
            - "siguiente_deshabilitado": Botón se deshabilitó al hacer clic
            - "error_click": Error al hacer clic
            - "fin_listado": No cambió contenido (fin natural)
        """
        ...


class PrimeFacesPaginationStrategy:
    """Estrategia de paginación robusta para portales que usan PrimeFaces.

    PrimeFaces es un framework de componentes UI para JSF (JavaServer Faces)
    muy utilizado en portales gubernamentales y empresariales argentinos.

    Esta estrategia maneja:
    - Múltiples selectores con fallback automático
    - Verificación de estado habilitado/deshabilitado robusta
    - Espera con polling para detectar cambio de contenido
    - Fingerprinting para confirmar que cambió la página

    La estrategia prueba cada selector en orden hasta encontrar un botón
    válido (visible y habilitado), lo que la hace resiliente ante cambios
    en la estructura HTML del portal.

    Example:
        >>> strategy = PrimeFacesPaginationStrategy()
        >>> exito, error = await strategy.navegar_siguiente(
        ...     page, tbody_locator, fingerprint_anterior
        ... )
        >>> if exito:
        ...     # Procesar nueva página
        ... else:
        ...     print(f"Error: {error}")
    """

    # Selectores por defecto ordenados por probabilidad (más común primero)
    DEFAULT_SELECTORES_SIGUIENTE = [
        "a[aria-label='Siguiente']",
        "button[aria-label='Siguiente']",
        "a:has(span[title='Siguiente'])",
        "button:has(span[title='Siguiente'])",
        ".pagination li.next:not(.disabled) a",
        ".pagination a:has-text('Siguiente')",
        ".rf-ds-btn-next",
        ".ui-paginator-next:not(.ui-state-disabled)",
        "a[class*='paginator'][class*='next']:not([class*='disabled'])",
    ]

    def __init__(
        self,
        selectores_siguiente: list[str] | None = None,
        timeout_ms: int = 10_000,
        max_wait_content_ms: int = 12_000,
        poll_interval_ms: int = 400,
    ):
        """Inicializa la estrategia PrimeFaces con múltiples selectores fallback.

        Args:
            selectores_siguiente: Lista de selectores CSS a probar en orden.
                Si es None, usa DEFAULT_SELECTORES_SIGUIENTE.
                Los selectores se prueban secuencialmente hasta encontrar
                un botón válido (visible y habilitado).
            timeout_ms: Timeout para esperar el botón (milisegundos)
            max_wait_content_ms: Timeout máximo para esperar cambio de contenido
            poll_interval_ms: Intervalo de polling para verificar cambios

        Note:
            La estrategia de múltiples selectores es más robusta que usar
            un solo selector con "," porque permite manejar errores por
            selector individual sin fallar toda la búsqueda.
        """
        self.selectores_siguiente = selectores_siguiente or self.DEFAULT_SELECTORES_SIGUIENTE
        self.timeout_ms = timeout_ms
        self.max_wait_content_ms = max_wait_content_ms
        self.poll_interval_ms = poll_interval_ms

    async def navegar_siguiente(
        self,
        page: Page,
        tbody_locator: Locator,
        fingerprint_actual: str,
    ) -> tuple[bool, str | None]:
        """Navega a la siguiente página usando múltiples selectores fallback.

        Prueba cada selector en orden hasta encontrar un botón válido.
        Esta estrategia es más robusta que un selector único porque:
        - Maneja cambios en la estructura HTML del portal
        - Permite detectar diferentes variantes de botones
        - No falla si un selector específico es inválido

        Args:
            page: Página de Playwright
            tbody_locator: Locator del tbody para verificar cambios
            fingerprint_actual: Fingerprint del tbody antes de hacer clic

        Returns:
            Tupla (exito, motivo_fallo):
                - exito: True si navegó correctamente y cambió el contenido
                - motivo_fallo: Código de error si falló, None si tuvo éxito

            Códigos de error:
                - "sin_siguiente": No se encontró botón con ningún selector
                - "sin_siguiente_habilitado": Botones encontrados pero deshabilitados
                - "siguiente_timeout": Timeout esperando visibilidad del botón
                - "siguiente_deshabilitado": Botón se deshabilitó antes del clic
                - "error_click": Error al hacer clic
                - "fin_listado": No cambió el contenido (fin natural)
        """
        # Intentar cada selector en orden
        boton: Locator | None = None
        selector_exitoso: str | None = None

        for selector in self.selectores_siguiente:
            try:
                logger.debug(f"Probando selector: {selector}")
                next_btn = page.locator(selector)
                btn_count = await next_btn.count()

                if btn_count <= 0:
                    logger.debug(f"  └─ Sin resultados, probando siguiente selector")
                    continue  # Probar siguiente selector

                # Buscar botón habilitado y visible
                for idx in range(btn_count):
                    candidato = next_btn.nth(idx)

                    # Verificar que esté visible primero (más rápido)
                    if not await candidato.is_visible():
                        continue

                    # Verificar que esté habilitado (usa verificación robusta)
                    if await self._is_enabled(candidato):
                        boton = candidato
                        selector_exitoso = selector
                        logger.info(f"✅ Botón 'Siguiente' encontrado con: {selector}")
                        break

                if boton is not None:
                    break  # Encontramos botón válido, salir del loop

            except Exception as e:
                logger.debug(f"  └─ Error con selector {selector}: {e}")
                continue  # Probar siguiente selector

        # Si no encontramos ningún botón válido
        if boton is None:
            logger.debug("❌ No se encontró botón 'Siguiente' habilitado con ningún selector")
            return False, "sin_siguiente_habilitado"

        # Esperar que el botón sea visible (doble verificación)
        try:
            await boton.wait_for(state="visible", timeout=self.timeout_ms)
        except TimeoutError:
            logger.warning("⏱️ Botón 'Siguiente' no se volvió visible en timeout")
            return False, "siguiente_timeout"

        # Verificar nuevamente que esté habilitado antes de hacer clic
        if not await self._is_enabled(boton):
            logger.debug("❌ Botón 'Siguiente' se deshabilitó antes del clic")
            return False, "siguiente_deshabilitado"

        # Hacer clic en el botón
        try:
            logger.debug(f"🖱️ Haciendo clic en botón 'Siguiente' ({selector_exitoso})")
            await boton.click()
        except (TimeoutError, Error) as exc:
            logger.error(f"❌ Fallo al hacer clic en 'Siguiente': {exc}")
            return False, "error_click"

        # Esperar a que cambie el contenido del tbody
        fingerprint_cambio = await self._esperar_cambio_contenido(
            page,
            tbody_locator,
            fingerprint_actual,
        )

        if not fingerprint_cambio:
            logger.debug("📄 No cambió el contenido después del clic - fin del listado")
            return False, "fin_listado"

        logger.debug("✅ Navegación exitosa - contenido cambió")
        return True, None

    async def _is_enabled(self, locator: Locator) -> bool:
        """Verifica si un locator está habilitado.

        Delega a la función _is_locator_enabled que realiza verificación robusta.

        Args:
            locator: Locator a verificar

        Returns:
            bool: True si está habilitado, False en caso contrario
        """
        return await _is_locator_enabled(locator)

    async def _esperar_cambio_contenido(
        self,
        page: Page,
        tbody_locator: Locator,
        fingerprint_actual: str,
    ) -> bool:
        """Espera con polling a que cambie el contenido del tbody.

        Usa polling activo para detectar cambios en el contenido,
        comparando fingerprints del tbody antes y después.

        Args:
            page: Página de Playwright
            tbody_locator: Locator del tbody
            fingerprint_actual: Fingerprint antes del cambio

        Returns:
            bool: True si cambió el contenido, False si timeout
        """
        elapsed_ms = 0
        while elapsed_ms < self.max_wait_content_ms:
            # Calcular fingerprint actual
            despues = await self._calcular_fingerprint(tbody_locator)
            if despues != fingerprint_actual:
                logger.debug(f"Contenido cambió después de {elapsed_ms}ms")
                return True

            # Esperar antes del siguiente check
            wait_time = min(self.poll_interval_ms, self.max_wait_content_ms - elapsed_ms)
            if wait_time <= 0:
                break

            await page.wait_for_timeout(wait_time)
            elapsed_ms += wait_time

        logger.debug(f"Timeout esperando cambio de contenido ({elapsed_ms}ms)")
        return False

    async def _calcular_fingerprint(
        self,
        tbody_locator: Locator,
        max_len: int = 4096
    ) -> str:
        """Calcula un fingerprint robusto del contenido del tbody.

        El fingerprint usa longitud + HTML interno para detectar cambios
        de forma más confiable que solo el texto visible. Este enfoque
        detecta cambios en atributos, estructura HTML, y contenido oculto.

        Args:
            tbody_locator: Locator del tbody
            max_len: Longitud máxima del fingerprint (default: 4096)

        Returns:
            str: Fingerprint en formato "{longitud}::{html_truncado}"

        Note:
            Usar inner_html en lugar de inner_text permite detectar:
            - Cambios en atributos HTML (class, id, data-*, etc.)
            - Elementos ocultos con display:none o visibility:hidden
            - Cambios en la estructura del DOM
        """
        try:
            # Usar inner_HTML en lugar de inner_text para mayor sensibilidad
            html = await tbody_locator.inner_html()

            # Formato: longitud + :: + contenido HTML
            signature = f"{len(html)}::{html}"

            # Truncar si excede max_len
            if max_len is not None and len(signature) > max_len:
                signature = signature[:max_len]

            return signature

        except Exception as e:
            logger.debug(f"Error calculando fingerprint: {e}")
            return ""


# Estrategia por defecto (PrimeFaces)
DEFAULT_PAGINATION_STRATEGY = PrimeFacesPaginationStrategy()


__all__ = [
    "PaginationStrategy",
    "PrimeFacesPaginationStrategy",
    "DEFAULT_PAGINATION_STRATEGY",
    "_is_locator_enabled",
]
