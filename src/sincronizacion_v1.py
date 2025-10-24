import os
from src.expedientes_v1 import obtener_expedientes
from src.configuracion_v1 import BASE_PATH


def crear_carpeta_expediente(id_expediente):
    """Crea una carpeta para el expediente con subcarpetas."""
    expediente_path = os.path.join(BASE_PATH, str(id_expediente))
    os.makedirs(os.path.join(expediente_path, "Documentos"), exist_ok=True)
    os.makedirs(os.path.join(expediente_path, "Notas"), exist_ok=True)
    os.makedirs(os.path.join(expediente_path, "Otros"), exist_ok=True)
    print(f"📂 Carpeta creada para expediente ID {id_expediente}")
    return expediente_path


def sincronizar_expedientes():
    """Sincroniza los expedientes de la base de datos con las carpetas en la PC."""
    os.makedirs(BASE_PATH, exist_ok=True)
    expedientes = obtener_expedientes()

    if not expedientes:
        print("✅ No hay expedientes en la base de datos para sincronizar.")
        return

    for expediente in expedientes:
        id_expediente = expediente["id_expediente"]
        expediente_path = os.path.join(BASE_PATH, str(id_expediente))

        if not os.path.exists(expediente_path):
            crear_carpeta_expediente(id_expediente)
        else:
            print(f"✅ La carpeta para expediente ID {id_expediente} ya existe")

def main():
    """Función principal que ejecuta la sincronización."""
    print("🔄 Iniciando sincronización de expedientes...")
    sincronizar_expedientes()
    print("✅ Sincronización completada.")

if __name__ == "__main__":
    main()