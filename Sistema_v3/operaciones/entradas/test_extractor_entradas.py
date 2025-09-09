import asyncio
from playwright.async_api import async_playwright
from datetime import datetime
from web.auto_login import reutilizar_sesion_async
from extractor_entradas import extraer_entradas_pjn



async def main():
    page, _, _, _ = await reutilizar_sesion_async()
    if not page:
        print("❌ No se pudo iniciar sesión en el portal del PJN.")
        return

    nuevas = await extraer_entradas_pjn(page, destino="./datos_extraidos/monitoreo",
            duplicados=False,
            incluir_tipos=("N","D"),
            fechas=None,
            fecha_desde=None,
            fecha_hasta=None,)

    print(f"✅ Nuevas agregadas en esta corrida: {nuevas}")

    print("✅ Proceso finalizado. El navegador permanecerá abierto.")
    while True:
        await asyncio.sleep(1)  # Mantener el navegador abierto


if __name__ == "__main__":
    asyncio.run(main())
