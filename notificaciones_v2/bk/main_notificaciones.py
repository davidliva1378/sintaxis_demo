from web.auto_login import reutilizar_sesion
from notificaciones_control_v4_bk import actualizar_notificaciones_nuevas


def main():
    page = reutilizar_sesion()
    if not page:
        print("❌ No se pudo iniciar sesión en el portal del PJN.")
        return

    actualizar_notificaciones_nuevas(page)

    print("✅ Proceso finalizado. El navegador permanecerá abierto.")
    while True:
        pass  # Mantener el navegador abierto


if __name__ == "__main__":
    main()
