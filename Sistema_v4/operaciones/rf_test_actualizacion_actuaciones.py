"""Ejecutable interactivo para probar la actualización incremental de actuaciones."""

import asyncio
import json
import os
import re
from pathlib import Path

from playwright.async_api import Page, async_playwright

from panel_pjn.acciones_pjn.urls_pjn import URL_CONSULTAS, URL_LOGIN
from Sistema_v4.actuaciones.actuaciones_v4 import (
    actualizar_actuaciones_desde_json,
    descargar_archivos_de_json,
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


def _resolver_ruta_json(ruta: str) -> Path:
    """Devuelve una ruta existente admitiendo atajos relativos comunes."""

    cruda = Path(ruta).expanduser()

    candidatos: list[Path]
    if cruda.is_absolute():
        candidatos = [cruda]
    else:
        base_script = Path(__file__).resolve().parents[1]
        repo_root = base_script.parent
        candidatos = [Path.cwd() / cruda, base_script / cruda, repo_root / cruda]

    for candidato in candidatos:
        if candidato.exists():
            return candidato.resolve()

    # Si ninguno existe, devolver la ruta normalizada del primer candidato para el mensaje.
    return (candidatos[0] if candidatos else cruda).resolve()


def _cargar_json_existente(ruta: str) -> tuple[dict, dict, Path]:
    ruta_normalizada = _resolver_ruta_json(ruta)
    if not ruta_normalizada.exists():
        raise FileNotFoundError(f"El archivo {ruta_normalizada} no existe.")

    with ruta_normalizada.open("r", encoding="utf-8") as fh:
        data = json.load(fh)

    if not isinstance(data, dict):
        raise ValueError("El JSON debe contener un objeto en la raíz.")

    encabezado = data.get("Expediente")
    if not isinstance(encabezado, dict):
        encabezado = {}

    return data, encabezado, ruta_normalizada


def _sugerir_anio(numero_expediente: str | None) -> str | None:
    if not numero_expediente:
        return None

    match = re.search(r"(20\d{2}|19\d{2})", numero_expediente)
    return match.group(1) if match else None


async def main() -> None:
    ruta_json = input("📄 Ruta al archivo JSON existente de actuaciones: ").strip()
    if not ruta_json:
        print("❌ Debe proporcionar una ruta válida.")
        return

    try:
        _payload, encabezado, ruta_normalizada = _cargar_json_existente(ruta_json)
    except Exception as exc:  # noqa: BLE001
        print(f"❌ No se pudo leer el JSON proporcionado: {exc}")
        return

    numero_original = encabezado.get("numero", "")
    caratula_original = encabezado.get("caratula")
    anio_sugerido = encabezado.get("anio") or _sugerir_anio(numero_original)

    print("\n📄 Información del expediente (según el JSON):")
    for clave in ("numero", "caratula", "dependencia", "jurisdiccion", "situacion"):
        valor = encabezado.get(clave, "-")
        print(f"  - {clave}: {valor}")

    numero_busqueda = input(
        f"\n🔢 Número de expediente para buscar [{numero_original}]: "
    ).strip() or numero_original

    anio_busqueda = input(
        f"📆 Año del expediente para buscar [{anio_sugerido or ''}]: "
    ).strip() or (anio_sugerido or "")

    caratula_busqueda = (
        input(
            f"📝 Carátula exacta (opcional) [{caratula_original or ''}]: "
        ).strip()
        or (caratula_original or None)
    )

    if not numero_busqueda or not anio_busqueda:
        print("❌ Debe proporcionar el número y el año del expediente para continuar.")
        return

    async with async_playwright() as playwright:
        navegador = await playwright.chromium.launch(headless=False)
        page = await navegador.new_page()

        if not await login_portal(page):
            await navegador.close()
            return

        await page.goto(URL_CONSULTAS)

        filas = await buscar_expedientes(page, numero_busqueda, anio_busqueda, caratula_busqueda)
        if not filas:
            print("❌ No se encontraron expedientes que coincidan con la búsqueda.")
            await navegador.close()
            return

        datos_expediente = await mostrar_y_elegir_expediente(
            page,
            filas,
            estrategia_seleccion=ESTRATEGIA_INTERACTIVA,
            descripcion_estrategia="interactiva",
        )
        if not datos_expediente:
            print("❌ No se pudo abrir el expediente seleccionado.")
            await navegador.close()
            return

        print("\n♻️ Iniciando actualización incremental de actuaciones...")
        conteo, actualizado, error = await actualizar_actuaciones_desde_json(
            page,
            {**encabezado, **datos_expediente},
            str(ruta_normalizada),
        )

        if error:
            print(f"❌ Error durante la actualización: {error}")
        else:
            print(f"✅ Actualización completada. Actuaciones agregadas: {conteo}.")
            if isinstance(actualizado, dict):
                encabezado_resultado = actualizado.get("Expediente", encabezado)
            else:
                encabezado_resultado = encabezado

            carpeta = str(ruta_normalizada.parent)
            print(f"📁 JSON actualizado en: {ruta_normalizada}")
            if isinstance(actualizado, dict):
                exp_meta = actualizado.get("Expediente", {})
                total_actuaciones = exp_meta.get("total_actuaciones", "?")
                total_descargados = exp_meta.get("Cantidad de Archivos Descargados", "?")
                print(
                    "📊 Totales actuales: "
                    f"{total_actuaciones} actuaciones, "
                    f"{total_descargados} archivos descargados."
                )

            descargar = input("\n¿Deseás descargar los archivos nuevos? (s/n): ").strip().lower()
            if descargar == "s":
                await descargar_archivos_de_json(page, carpeta)

        await navegador.close()


if __name__ == "__main__":
    asyncio.run(main())
