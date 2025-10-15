"""Ejecutable interactivo para probar la extracción completa en Sistema_v5."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from playwright.async_api import Page

from panel_pjn.acciones_pjn.urls_pjn import URL_CONSULTAS
from Sistema_v5.pjn.scraping import obtener_pagina_autenticada, normalizar_numero_expediente
from Sistema_v5.pjn.scraping.actuaciones import (
    descargar_archivos_de_json,
    extraer_actuaciones_completas,
)
from Sistema_v5.pjn.scraping.expedientes import (
    SeleccionEstrategia,
    buscar_expedientes,
    mostrar_y_elegir_expediente,
)


HEADLESS = os.getenv("PJN_HEADLESS", "false").lower() in {"1", "true", "yes", "y"}


def seleccionar_por_consola(opciones: list[dict[str, str]]) -> int | None:
    """Estrategia interactiva basada en la entrada del usuario por consola."""

    seleccion = input("👉 Ingrese el número de opción que desea abrir (0 para cancelar): ")
    try:
        idx = int(seleccion) - 1
    except ValueError:
        print("❌ Selección inválida.")
        return None

    if idx < 0:
        print("❌ Operación cancelada por el usuario.")
        return None

    if idx >= len(opciones):
        print("❌ Selección fuera de rango.")
        return None

    return idx


ESTRATEGIA_INTERACTIVA: SeleccionEstrategia = seleccionar_por_consola


async def _mostrar_credenciales_vacias(page: Page) -> bool:
    """Verifica si el portal redirigió al formulario de login por credenciales faltantes."""

    if await page.is_visible("#username"):
        print(
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
        print("❌ No se encontraron expedientes.")
        return None

    return await mostrar_y_elegir_expediente(
        page,
        filas,
        estrategia_seleccion=ESTRATEGIA_INTERACTIVA,
        descripcion_estrategia="interactiva",
    )


async def _extraer_actuaciones(page: Page, datos_expediente: dict[str, Any]) -> None:
    print("\n📂 Extrayendo actuaciones actuales e históricas...")
    actuales, historicas, error = await extraer_actuaciones_completas(
        page_expediente=page,
        expediente_datos=datos_expediente,
        incluir_historicas=True,
    )

    if error:
        print(f"❌ Error en la extracción: {error}")
        return

    print(f"✅ Se extrajeron {len(actuales)} actuaciones actuales.")
    print(f"📜 Se extrajeron {len(historicas)} actuaciones históricas.")

    numero_normalizado = normalizar_numero_expediente(datos_expediente.get("numero"))
    carpeta = os.path.join("ActuacionesCompletas", numero_normalizado)
    print(f"📁 JSONs guardados en: {carpeta}")

    descargar = _leer_dato("\n¿Deseás descargar los archivos vinculados? (s/n): ").lower()
    if descargar == "s":
        await descargar_archivos_de_json(page, carpeta)


async def main() -> None:
    async with obtener_pagina_autenticada(headless=HEADLESS) as (page, _context, _browser):
        if await _mostrar_credenciales_vacias(page):
            return

        await page.goto(URL_CONSULTAS)

        datos_expediente = await _buscar_y_seleccionar_expediente(page)
        if not datos_expediente:
            print("❌ No se pudo abrir ni extraer el expediente.")
            return

        await _extraer_actuaciones(page, datos_expediente)


if __name__ == "__main__":
    asyncio.run(main())
