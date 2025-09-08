import asyncio
from web.auto_login import reutilizar_sesion_async
from notificaciones_control_v5_async import actualizar_notificaciones_nuevas


async def main():
    page, _, _, _ = await reutilizar_sesion_async()
    if not page:
        print("❌ No se pudo iniciar sesión en el portal del PJN.")
        return

    await actualizar_notificaciones_nuevas(page)

    print("✅ Proceso finalizado. El navegador permanecerá abierto.")
    while True:
        await asyncio.sleep(1)  # Mantener el navegador abierto


if __name__ == "__main__":
    asyncio.run(main())
