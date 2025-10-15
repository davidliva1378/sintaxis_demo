"""Script de diagnóstico para detectar problemas en la extracción de entradas.

Este script verifica:
- Si el contenedor de scroll está visible
- Si las filas de la tabla están presentes
- Si los selectores funcionan correctamente
- Qué elementos se encuentran en la página
"""

from __future__ import annotations

import asyncio
import os

from Sistema_v5.pjn.scraping import obtener_pagina_autenticada
from Sistema_v5.pjn.selectores import SEL_ENTRADAS
from Sistema_v5.pjn.utils.logging import get_logger

HEADLESS = os.getenv("PJN_HEADLESS", "false").lower() in {"1", "true", "yes", "y"}
logger = get_logger(__name__)


async def main() -> None:
    """Ejecutar diagnóstico de selectores."""

    logger.info("=" * 60)
    logger.info("🔍 DIAGNÓSTICO DE EXTRACCIÓN DE ENTRADAS")
    logger.info("=" * 60)

    try:
        async with obtener_pagina_autenticada(headless=HEADLESS) as (page, context, browser):
            logger.info("✅ Sesión autenticada")

            url_entradas = "https://portalpjn.pjn.gov.ar/inicio"
            await page.goto(url_entradas, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(3000)

            logger.info("\n" + "=" * 60)
            logger.info("📋 VERIFICANDO SELECTORES")
            logger.info("=" * 60)

            # 1. Verificar contenedor de scroll
            logger.info("\n1️⃣ Contenedor de scroll: %s", SEL_ENTRADAS.CONTENEDOR_SCROLL)
            try:
                contenedor = page.locator(SEL_ENTRADAS.CONTENEDOR_SCROLL)
                visible = await contenedor.is_visible()
                count = await contenedor.count()
                logger.info("   ✓ Visible: %s", visible)
                logger.info("   ✓ Count: %d", count)
            except Exception as e:
                logger.error("   ✗ Error: %s", e)

            # 2. Verificar tabla
            logger.info("\n2️⃣ Tabla de entradas: %s", SEL_ENTRADAS.TABLA)
            try:
                filas = await page.query_selector_all(SEL_ENTRADAS.TABLA)
                logger.info("   ✓ Filas encontradas: %d", len(filas))

                if len(filas) > 0:
                    logger.info("\n   📄 Analizando primera fila...")
                    fila = filas[0]

                    # Verificar número
                    num_elem = await fila.query_selector(SEL_ENTRADAS.EXPEDIENTE_NUMERO)
                    if num_elem:
                        num_text = await num_elem.inner_text()
                        logger.info("   ✓ Número expediente encontrado: %s", num_text.strip()[:50])
                    else:
                        logger.warning("   ✗ NO se encontró número de expediente")
                        logger.info("      Selector usado: %s", SEL_ENTRADAS.EXPEDIENTE_NUMERO)

                    # Verificar carátula
                    car_elem = await fila.query_selector(SEL_ENTRADAS.EXPEDIENTE_CARATULA)
                    if car_elem:
                        car_text = await car_elem.inner_text()
                        logger.info("   ✓ Carátula encontrada: %s", car_text.strip()[:50])
                    else:
                        logger.warning("   ✗ NO se encontró carátula")
                        logger.info("      Selector usado: %s", SEL_ENTRADAS.EXPEDIENTE_CARATULA)

                    # Verificar celdas
                    celdas = await fila.query_selector_all(SEL_ENTRADAS.CELDAS_FILA)
                    logger.info("   ✓ Celdas encontradas: %d", len(celdas))

                    if len(celdas) >= 3:
                        # Verificar fecha en celda 2
                        logger.info("\n   📅 Analizando celda de fecha (índice 2)...")
                        celda_fecha = celdas[2]

                        # Método 1: aria-label
                        fecha_elem = await celda_fecha.query_selector(SEL_ENTRADAS.FECHA_ELEMENTO)
                        if fecha_elem:
                            aria_label = await fecha_elem.get_attribute("aria-label")
                            inner_text = await fecha_elem.inner_text()
                            logger.info("   ✓ Elemento fecha encontrado:")
                            logger.info("      - aria-label: %s", aria_label)
                            logger.info("      - inner_text: %s", inner_text)
                        else:
                            logger.warning("   ✗ NO se encontró elemento con selector: %s", SEL_ENTRADAS.FECHA_ELEMENTO)

                            # Fallback: inner_text de la celda
                            celda_text = await celda_fecha.inner_text()
                            logger.info("   📝 Texto completo de celda fecha: '%s'", celda_text)

                            # Buscar todos los elementos p en la celda
                            all_p = await celda_fecha.query_selector_all("p")
                            logger.info("   📝 Elementos <p> en celda: %d", len(all_p))
                            for idx, p in enumerate(all_p):
                                p_class = await p.get_attribute("class")
                                p_aria = await p.get_attribute("aria-label")
                                p_text = await p.inner_text()
                                logger.info("      [%d] class='%s' aria-label='%s' text='%s'",
                                          idx, p_class, p_aria, p_text)

                    # Verificar indicadores de evento (N/D)
                    logger.info("\n   🔔 Verificando indicadores de evento...")
                    elementos_aria = await fila.query_selector_all(SEL_ENTRADAS.ELEMENTOS_CON_ARIA)
                    logger.info("   ✓ Elementos con aria-label: %d", len(elementos_aria))

                    evento_encontrado = False
                    for el in elementos_aria[:5]:  # Primeros 5
                        aria = await el.get_attribute("aria-label")
                        if aria and ("evento" in aria.lower() or "notificaci" in aria.lower() or "despacho" in aria.lower()):
                            logger.info("   ✓ Evento encontrado en aria-label: %s", aria)
                            evento_encontrado = True
                            break

                    if not evento_encontrado:
                        logger.warning("   ✗ NO se encontró indicador de evento en aria-labels")

                        # Verificar avatar
                        avatar = await fila.query_selector(SEL_ENTRADAS.AVATAR_LETRA)
                        if avatar:
                            letra = await avatar.inner_text()
                            logger.info("   ✓ Avatar letra encontrado: '%s'", letra)
                        else:
                            logger.warning("   ✗ NO se encontró avatar con selector: %s", SEL_ENTRADAS.AVATAR_LETRA)

                    # Mostrar HTML de la fila para inspección
                    logger.info("\n   📄 HTML completo de la primera fila:")
                    html_fila = await fila.inner_html()
                    logger.info("   %s", html_fila[:1000] + "..." if len(html_fila) > 1000 else html_fila)

            except Exception as e:
                logger.error("   ✗ Error: %s", e)
                import traceback
                traceback.print_exc()

            logger.info("\n" + "=" * 60)
            logger.info("✅ DIAGNÓSTICO COMPLETADO")
            logger.info("=" * 60)

            if not HEADLESS:
                logger.info("\n⏸️  Navegador abierto. Presione Ctrl+C para cerrar.")
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    logger.info("\n👋 Cerrando...")

    except Exception as e:
        logger.error("❌ Error: %s", e)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())