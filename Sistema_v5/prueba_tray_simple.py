#!/usr/bin/env python3
"""Test simple del system tray - Solo muestra el icono."""

import time
import pystray
from PIL import Image, ImageDraw


def create_test_icon():
    """Crea un icono de prueba grande y visible."""
    size = 64

    # Fondo transparente
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    # Círculo verde grande
    margin = 6
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=(0, 200, 0, 255),
        outline=(0, 0, 0, 255),
        width=3
    )

    # Punto blanco en el centro
    center = size // 2
    radius = size // 6
    draw.ellipse(
        [center - radius, center - radius, center + radius, center + radius],
        fill=(255, 255, 255, 200)
    )

    return image


def on_quit(icon, item):
    """Handler para salir."""
    print("Saliendo...")
    icon.stop()


# Crear icono
icon = pystray.Icon(
    name="test_pjn",
    icon=create_test_icon(),
    title="TEST Monitor PJN - ¡Click aquí!",
    menu=pystray.Menu(
        pystray.MenuItem("Estado", lambda: print("Estado clicked")),
        pystray.MenuItem("Salir", on_quit)
    )
)

print("=" * 60)
print("🧪 TEST SYSTEM TRAY")
print("=" * 60)
print("")
print("🔍 BUSCA EL ICONO:")
print("   - Mira en la barra superior DERECHA de tu Mac")
print("   - Al lado del reloj, WiFi, batería, etc.")
print("   - Es un CÍRCULO VERDE con punto blanco")
print("")
print("   Si NO lo ves:")
print("   1. Busca el icono de flecha >> (Control Center)")
print("   2. Haz click para expandir iconos ocultos")
print("   3. Debería aparecer 'TEST Monitor PJN'")
print("")
print("   Si lo VES:")
print("   - Haz CLICK (o Control+Click) para ver el menú")
print("   - Selecciona 'Salir' para cerrar")
print("")
print("⏳ Esperando 30 segundos...")
print("   (Ctrl+C para cancelar)")
print("=" * 60)

# Iniciar icono en thread
icon.run_detached()

# Esperar 30 segundos
try:
    for i in range(30, 0, -1):
        print(f"\r⏰ Cerrando automáticamente en {i} segundos... (o usa 'Salir' del menú)", end="", flush=True)
        time.sleep(1)
    print("\n\n⏰ Tiempo agotado - Cerrando...")
    icon.stop()
except KeyboardInterrupt:
    print("\n\n⚠️  Cancelado por usuario - Cerrando...")
    icon.stop()

print("✅ Test completado")
