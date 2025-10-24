#!/usr/bin/env python3
"""Script para debuggear el acceso a /consultas."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pjn.scraping.base import obtener_pagina_autenticada
from pjn.utils.logging import setup_logging, get_logger

setup_logging(level="DEBUG")
logger = get_logger(__name__)


async def main():
    """Investiga qué pasa al navegar a /consultas."""

    logger.info("=== DEBUG: Navegando a /consultas ===")

    async with obtener_pagina_autenticada(headless=False) as (page, _, _):
        logger.info("Sesión autenticada, navegando a /consultas...")

        # Navegar a consultas
        await page.goto("https://portalpjn.pjn.gov.ar/consultas")
        logger.info("Navegación completada")

        # Esperar un poco para que cargue
        await page.wait_for_timeout(3000)

        # Ver qué hay en la página
        logger.info("\n=== Verificando elementos en la página ===")

        # Verificar si hay tabla
        tabla = page.locator("table.table-striped")
        tabla_count = await tabla.count()
        logger.info(f"Tablas con clase 'table-striped': {tabla_count}")

        # Verificar cualquier tabla
        todas_tablas = page.locator("table")
        todas_count = await todas_tablas.count()
        logger.info(f"Total de tablas: {todas_count}")

        # Ver título de la página
        titulo = await page.title()
        logger.info(f"Título de la página: {titulo}")

        # Ver URL actual
        url_actual = page.url
        logger.info(f"URL actual: {url_actual}")

        # Ver si hay mensajes de error
        error_elem = page.locator("text=/error|Error|ERROR/i")
        error_count = await error_elem.count()
        if error_count > 0:
            logger.warning(f"Encontrados {error_count} elementos con 'error'")
            for i in range(min(error_count, 3)):
                texto = await error_elem.nth(i).text_content()
                logger.warning(f"  Error {i+1}: {texto}")

        # Ver si hay botones o formularios
        botones = page.locator("button")
        botones_count = await botones.count()
        logger.info(f"Botones en la página: {botones_count}")

        # Tomar screenshot
        await page.screenshot(path="debug_consultas.png")
        logger.info("Screenshot guardado en debug_consultas.png")

        # Esperar para que puedas ver
        logger.info("\n=== Revisa la ventana del browser ===")
        logger.info("Presiona Ctrl+C para salir...")

        try:
            await asyncio.sleep(300)  # 5 minutos
        except KeyboardInterrupt:
            logger.info("Saliendo...")


if __name__ == "__main__":
    asyncio.run(main())
