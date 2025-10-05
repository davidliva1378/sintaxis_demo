"""Ejecutable interactivo para probar la extracción completa en Sistema_v4."""

import asyncio
import os

from playwright.async_api import Page, async_playwright

from panel_pjn.acciones_pjn.urls_pjn import URL_CONSULTAS, URL_LOGIN
from Sistema_v4.actuaciones.actuaciones_v4 import (
    descargar_archivos_de_json,
    extraer_actuaciones_completas,
)
from Sistema_v4.operaciones.expedientes.expedientes_v4 import (
    SeleccionEstrategia,
    buscar_expedientes,
    mostrar_y_elegir_expediente,
)

USUARIO = os.getenv("PJN_USUARIO", "20213071662")
CONTRASENA = os.getenv("PJN_CONTRASENA", "surrey1970")


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


def _mostrar_credenciales_vacias() -> bool:
    if not USUARIO or not CONTRASENA:
        print(
            "⚠️ Debe configurar las variables de entorno PJN_USUARIO y PJN_CONTRASENA "
            "con credenciales válidas antes de ejecutar el script."
        )
        return True
    return False


async def login_portal(page: Page) -> bool:
    if _mostrar_credenciales_vacias():
        return False

    try:
        await page.goto(URL_LOGIN)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ Error de conexión al intentar acceder al portal: {exc}")
        return False

    await page.fill("#username", USUARIO)
    await page.fill("#password", CONTRASENA)
    await page.click("#kc-login")

    try:
        await page.wait_for_selector("text=Consultas", timeout=8_000)
        print("✅ Login exitoso.")
        return True
    except Exception:  # noqa: BLE001
        print("❌ Error de login: no se detectó la página de inicio correctamente.")
        return False


async def main() -> None:
    numero = input("Número de expediente: ").strip()
    anio = input("Año: ").strip()
    caratula = input("Carátula exacta (opcional): ").strip() or None

    async with async_playwright() as playwright:
        navegador = await playwright.chromium.launch(headless=False)
        page = await navegador.new_page()

        if not await login_portal(page):
            await navegador.close()
            return

        await page.goto(URL_CONSULTAS)

        filas = await buscar_expedientes(page, numero, anio, caratula)
        if not filas:
            print("❌ No se encontraron expedientes.")
            await navegador.close()
            return

        datos_expediente = await mostrar_y_elegir_expediente(
            page,
            filas,
            estrategia_seleccion=ESTRATEGIA_INTERACTIVA,
            descripcion_estrategia="interactiva",
        )
        if not datos_expediente:
            print("❌ No se pudo abrir ni extraer el expediente.")
            await navegador.close()
            return

        print("\n📂 Extrayendo actuaciones actuales e históricas...")
        actuales, historicas, error = await extraer_actuaciones_completas(
            page_expediente=page,
            expediente_datos=datos_expediente,
            incluir_historicas=True,
        )

        if error:
            print(f"❌ Error en la extracción: {error}")
        else:
            print(f"✅ Se extrajeron {len(actuales)} actuaciones actuales.")
            print(f"📜 Se extrajeron {len(historicas)} actuaciones históricas.")
            numero_normalizado = datos_expediente["numero"].replace("/", "_")
            carpeta = os.path.join("ActuacionesCompletas", numero_normalizado)
            print(f"📁 JSONs guardados en: {carpeta}")

            descargar = input("\n¿Deseás descargar los archivos vinculados? (s/n): ").strip().lower()
            if descargar == "s":
                await descargar_archivos_de_json(page, carpeta)

        await navegador.close()


if __name__ == "__main__":
    asyncio.run(main())
