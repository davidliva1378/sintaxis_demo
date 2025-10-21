"""Ejecutable interactivo para probar la extracción completa en Sistema_v5."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from playwright.async_api import Page

from panel_pjn.acciones_pjn.urls_pjn import URL_CONSULTAS
from Sistema_v5.pjn import (
    CredencialesFaltantes,
    ExtraccionError,
    PJNError,
    SesionInvalida,
)
from Sistema_v5.pjn.scraping import obtener_pagina_autenticada, normalizar_numero_expediente
from Sistema_v5.pjn.services.actuaciones import procesar_actuaciones_expediente
from Sistema_v5.pjn.utils.logging import get_logger
from Sistema_v5.pjn.scraping.expedientes import (
    SeleccionEstrategia,
    buscar_expedientes,
    mostrar_y_elegir_expediente,
)


# Configuración
HEADLESS = os.getenv("PJN_HEADLESS", "false").lower() in {"1", "true", "yes", "y"}

# Configurar logging desde variables de entorno o usar defaults
# Usa LOG_LEVEL y LOG_FILE si están definidos
logger = get_logger(__name__)


def seleccionar_por_consola(opciones: list[dict[str, str]]) -> int | None:
    """Estrategia interactiva basada en la entrada del usuario por consola."""

    seleccion = input("👉 Ingrese el número de opción que desea abrir (0 para cancelar): ")
    try:
        idx = int(seleccion) - 1
    except ValueError:
        logger.error("❌ Selección inválida.")
        return None

    if idx < 0:
        logger.warning("❌ Operación cancelada por el usuario.")
        return None

    if idx >= len(opciones):
        logger.error("❌ Selección fuera de rango.")
        return None

    return idx


ESTRATEGIA_INTERACTIVA: SeleccionEstrategia = seleccionar_por_consola


async def _mostrar_credenciales_vacias(page: Page) -> bool:
    """Verifica si el portal redirigió al formulario de login por credenciales faltantes."""

    if await page.is_visible("#username"):
        logger.warning(
            "⚠️ Debe configurar las variables de entorno PJN_USUARIO y PJN_CONTRASENA "
            "con credenciales válidas antes de ejecutar el script."
        )
        return True
    return False


def _leer_dato(prompt: str) -> str:
    return input(prompt).strip()


async def _buscar_y_seleccionar_expediente(page: Page) -> dict[str, Any] | None:
    numero = _leer_dato("Número de expediente: ")
    anio = _leer_dato("Año: ")
    caratula = _leer_dato("Carátula exacta (opcional): ") or None

    filas = await buscar_expedientes(page, numero, anio, caratula)
    if not filas:
        logger.error("❌ No se encontraron expedientes.")
        return None

    return await mostrar_y_elegir_expediente(
        page,
        filas,
        estrategia_seleccion=ESTRATEGIA_INTERACTIVA,
        descripcion_estrategia="interactiva",
    )


async def _extraer_actuaciones(page: Page, datos_expediente: dict[str, Any]) -> None:
    descargar = _leer_dato(
        "\n¿Deseás descargar los archivos vinculados automáticamente después de la extracción? (s/n): "
    ).lower()
    descargar_adjuntos = descargar == "s"

    logger.info("\n📂 Extrayendo actuaciones actuales e históricas...")

    json_path, resumen = await procesar_actuaciones_expediente(
        {**datos_expediente, "page": page},
        descargar_adjuntos=descargar_adjuntos,
    )

    if resumen["error"]:
        logger.error("❌ Error en la extracción: %s", resumen["error"])
        return

    logger.info("✅ Se extrajeron %d actuaciones actuales.", resumen["actuaciones_actuales"])
    logger.info("📜 Se extrajeron %d actuaciones históricas.", resumen["actuaciones_historicas"])

    if json_path:
        logger.info("📄 JSON generado: %s", json_path)
        if resumen["descargas_ejecutadas"]:
            logger.info("📥 Descarga de adjuntos completada en: %s", json_path.parent)
    else:
        numero_normalizado = normalizar_numero_expediente(datos_expediente.get("numero"))
        logger.info(
            "📁 Carpeta generada para el expediente: %s",
            os.path.join("ActuacionesCompletas", numero_normalizado),
        )

    if descargar_adjuntos and not resumen["descargas_ejecutadas"]:
        logger.warning(
            "⚠️ No fue posible descargar adjuntos automáticamente. Revise los logs para más detalles."
        )


async def main() -> None:
    try:
        async with obtener_pagina_autenticada(headless=HEADLESS) as (page, _context, _browser):
            if await _mostrar_credenciales_vacias(page):
                return

            await page.goto(URL_CONSULTAS)

            datos_expediente = await _buscar_y_seleccionar_expediente(page)
            if not datos_expediente:
                logger.error("❌ No se pudo abrir ni extraer el expediente.")
                return

            await _extraer_actuaciones(page, datos_expediente)

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
