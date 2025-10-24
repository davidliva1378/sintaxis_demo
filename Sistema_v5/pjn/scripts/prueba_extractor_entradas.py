"""Script de prueba para el extractor de entradas del PJN - Sistema v5.

Este script permite probar la extracción de entradas/notificaciones desde el portal
del PJN utilizando el módulo actualizado de Sistema_v5.

Uso:
    python prueba_extractor_entradas.py

Variables de entorno necesarias:
    - PJN_USER: Usuario para el portal PJN
    - PJN_PASSWORD: Contraseña para el portal PJN
    - PJN_HEADLESS: (opcional) "true" para modo headless, "false" para ver el navegador

Características:
    - Extrae entradas con el nuevo selector de fecha (aria-label)
    - Permite filtrar por tipo de evento (N/D)
    - Permite filtrar por fechas exactas o rangos
    - Soporta modo duplicados on/off
    - Mantiene el navegador abierto al finalizar para inspección
"""

from __future__ import annotations

import asyncio
import os
from datetime import datetime

from Sistema_v5.pjn import CredencialesFaltantes, ExtraccionError, PJNError, SesionInvalida
from Sistema_v5.pjn.scraping import obtener_pagina_autenticada
from Sistema_v5.pjn.scraping.entradas import extraer_entradas_pjn
from Sistema_v5.pjn.utils.logging import get_logger

# Configuración
HEADLESS = os.getenv("PJN_HEADLESS", "false").lower() in {"1", "true", "yes", "y"}

logger = get_logger(__name__)


async def main() -> None:
    """Función principal de prueba del extractor de entradas."""

    logger.info("=" * 60)
    logger.info("🧪 PRUEBA DE EXTRACTOR DE ENTRADAS - Sistema v5")
    logger.info("=" * 60)
    logger.info("Inicio: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    try:
        # Obtener página autenticada usando el sistema v5
        async with obtener_pagina_autenticada(headless=HEADLESS) as (page, context, browser):
            logger.info("✅ Sesión autenticada correctamente")

            # Navegar a la página de entradas/notificaciones
            # URL típica del PJN para bandeja de entradas
            url_entradas = "https://portalpjn.pjn.gov.ar/inicio"
            logger.info("🔗 Navegando a: %s", url_entradas)

            await page.goto(url_entradas, wait_until="domcontentloaded", timeout=30_000)
            await page.wait_for_timeout(2000)  # Esperar carga inicial

            logger.info("\n" + "=" * 60)
            logger.info("🚀 Iniciando extracción de entradas...")
            logger.info("=" * 60)

            # Configuración de la extracción
            destino = "./datos_extraidos/monitoreo"
            duplicados = False  # False = deduplicación activa
            incluir_tipos = ("N", "D")  # Notificaciones y Despachos
            fechas = None  # Fechas exactas (ejemplo: ["15/10/2025"])
            fecha_desde = None  # Rango desde (ejemplo: "01/10/2025")
            fecha_hasta = None  # Rango hasta (ejemplo: "15/10/2025")

            logger.info("\n📋 Configuración de extracción:")
            logger.info("   - Destino: %s", destino)
            logger.info("   - Duplicados: %s", duplicados)
            logger.info("   - Tipos incluidos: %s", incluir_tipos)
            logger.info("   - Fechas exactas: %s", fechas or "Todas")
            logger.info("   - Rango desde: %s", fecha_desde or "Sin límite")
            logger.info("   - Rango hasta: %s", fecha_hasta or "Sin límite")
            logger.info("")

            # Ejecutar extracción
            nuevas = await extraer_entradas_pjn(
                page=page,
                destino=destino,
                duplicados=duplicados,
                incluir_tipos=incluir_tipos,
                fechas=fechas,
                fecha_desde=fecha_desde,
                fecha_hasta=fecha_hasta,
            )

            logger.info("\n" + "=" * 60)
            logger.info("✅ EXTRACCIÓN COMPLETADA")
            logger.info("=" * 60)
            logger.info("📊 Nuevas entradas agregadas: %d", nuevas)
            logger.info("📁 Archivos guardados en: %s", os.path.abspath(destino))
            logger.info("   - historial_notificaciones.json")
            logger.info("   - historial_notificaciones.csv")
            logger.info("")
            logger.info("Fin: %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            logger.info("=" * 60)

            # Mantener el navegador abierto para inspección
            if not HEADLESS:
                logger.info("\n⏸️  El navegador permanecerá abierto para inspección.")
                logger.info("   Presione Ctrl+C para cerrar y finalizar.")
                try:
                    while True:
                        await asyncio.sleep(1)
                except KeyboardInterrupt:
                    logger.info("\n👋 Cerrando navegador...")

    except CredencialesFaltantes as e:
        logger.error("\n❌ Error de credenciales: %s", e)
        logger.info("💡 Configure las variables de entorno PJN_USER y PJN_PASSWORD")
        return
    except SesionInvalida as e:
        logger.error("\n❌ Error de sesión: %s", e)
        logger.info("💡 Intente eliminar el archivo pjn_storage_state.json y vuelva a intentar")
        return
    except ExtraccionError as e:
        logger.error("\n❌ Error durante la extracción: %s", e)
        return
    except PJNError as e:
        logger.error("\n❌ Error del sistema PJN: %s", e)
        return
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️ Operación cancelada por el usuario")
        return
    except Exception as e:
        logger.error("\n❌ Error inesperado: %s: %s", type(e).__name__, e)
        import traceback
        traceback.print_exc()
        return


if __name__ == "__main__":
    asyncio.run(main())
