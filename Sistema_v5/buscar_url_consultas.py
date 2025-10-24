#!/usr/bin/env python3
"""Script para encontrar la URL correcta de consultas."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from pjn.scraping.base import obtener_pagina_autenticada
from pjn.utils.logging import setup_logging, get_logger

setup_logging(level="INFO")
logger = get_logger(__name__)


async def main():
    """Encuentra la URL correcta para consultas de expedientes."""

    logger.info("=== Buscando URL correcta de consultas ===")

    async with obtener_pagina_autenticada(headless=False) as (page, _, _):
        logger.info("Sesión autenticada, navegando a inicio...")

        # Navegar a inicio
        await page.goto("https://portalpjn.pjn.gov.ar/inicio")
        await page.wait_for_timeout(2000)

        logger.info("\n=== Buscando enlaces relacionados con 'consulta' o 'expediente' ===")

        # Buscar todos los enlaces
        enlaces = await page.query_selector_all("a")
        logger.info(f"Total de enlaces en la página: {len(enlaces)}")

        enlaces_consulta = []
        for enlace in enlaces:
            try:
                texto = await enlace.inner_text()
                href = await enlace.get_attribute("href")

                texto_lower = texto.lower() if texto else ""

                # Buscar palabras clave
                if any(keyword in texto_lower for keyword in ["consulta", "expediente", "mis causa", "causas"]):
                    enlaces_consulta.append({
                        "texto": texto.strip() if texto else "",
                        "href": href or ""
                    })
            except:
                pass

        logger.info(f"\nEnlaces encontrados con palabras clave: {len(enlaces_consulta)}")
        for i, enlace in enumerate(enlaces_consulta, 1):
            logger.info(f"{i}. Texto: '{enlace['texto']}'")
            logger.info(f"   URL: {enlace['href']}\n")

        # Buscar en el menú de navegación
        logger.info("=== Buscando en menús de navegación ===")
        menus = await page.query_selector_all("nav, [role='navigation']")
        logger.info(f"Menús encontrados: {len(menus)}")

        # Tomar screenshot
        await page.screenshot(path="buscar_consultas.png", full_page=True)
        logger.info("\nScreenshot guardado en buscar_consultas.png")

        logger.info("\n=== Revisa la ventana del browser ===")
        logger.info("Busca manualmente el enlace a 'Consultas' o 'Mis Expedientes'")
        logger.info("Y dime cuál es la URL correcta")
        logger.info("\nPresiona Ctrl+C para salir...")

        try:
            await asyncio.sleep(300)  # 5 minutos
        except KeyboardInterrupt:
            logger.info("Saliendo...")


if __name__ == "__main__":
    asyncio.run(main())
