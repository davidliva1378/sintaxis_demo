#!/usr/bin/env python3
"""Ejemplo de uso de la API REST del Sistema PJN v6.

Este script demuestra cómo consumir la API REST usando requests.
Requiere que el servidor FastAPI esté corriendo.

Iniciar servidor:
    uvicorn presentation.api.rest.main:app --reload
"""

import json

import requests

# URL base de la API
BASE_URL = "http://localhost:8000"
API_V1 = f"{BASE_URL}/api/v1"


def health_check():
    """Verifica que la API esté funcionando."""
    print("=== Health Check ===")
    response = requests.get(f"{API_V1}/health")
    print(f"Status: {response.status_code}")
    print(json.dumps(response.json(), indent=2))
    print()


def extraer_expedientes():
    """Extrae expedientes del PJN."""
    print("=== Extraer Expedientes ===")

    payload = {
        "usuario": None,  # Usar credenciales de .env
        "contrasena": None,
        "headless": True,
        "guardar_en": "datos/expedientes_base.json",
    }

    response = requests.post(f"{API_V1}/expedientes/extraer", json=payload)

    print(f"Status: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))

    if result.get("success"):
        print(f"✓ Extraídos {result['total']} expedientes")
    else:
        print(f"✗ Error: {result.get('error')}")
    print()


def filtrar_expedientes():
    """Filtra expedientes por selección."""
    print("=== Filtrar Expedientes ===")

    payload = {
        "numeros_seleccionados": ["CNM 0001/2024", "CNM 0002/2024"],
        "origen": "datos/expedientes_base.json",
        "destino": "datos/expedientes_sistema.json",
        "incluir_activos": True,
        "dias_actividad": 30,
    }

    response = requests.post(f"{API_V1}/expedientes/filtrar", json=payload)

    print(f"Status: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))

    if result.get("success"):
        print(f"✓ Filtrados {result['total_filtrados']}/{result['total_origen']} expedientes")
    else:
        print(f"✗ Error: {result.get('error')}")
    print()


def listar_expedientes():
    """Lista expedientes almacenados."""
    print("=== Listar Expedientes ===")

    response = requests.get(f"{API_V1}/expedientes")

    print(f"Status: {response.status_code}")
    result = response.json()

    if result.get("success"):
        print(f"Total: {result['total']} expedientes")
        for exp in result.get("expedientes", []):
            print(f"  - {exp['numero']}: {exp['caratula']}")
    else:
        print(f"✗ Error: {result.get('error')}")
    print()


def obtener_expediente(numero: str):
    """Obtiene detalles de un expediente específico."""
    print(f"=== Obtener Expediente: {numero} ===")

    response = requests.get(f"{API_V1}/expedientes/{numero}")

    print(f"Status: {response.status_code}")

    if response.status_code == 200:
        result = response.json()
        print(json.dumps(result, indent=2))
    else:
        print(f"✗ Error: {response.json()}")
    print()


def crear_workspaces():
    """Crea workspaces para expedientes."""
    print("=== Crear Workspaces ===")

    payload = {
        "archivo_sistema": "datos/expedientes_sistema.json",
        "workspaces_dir": "datos/workspaces",
        "extraer_actuaciones": False,
        "descargar_archivos": False,
    }

    response = requests.post(f"{API_V1}/workspaces/crear", json=payload)

    print(f"Status: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))

    if result.get("success"):
        print(f"✓ Creados {result['workspaces_creados']}/{result['total_expedientes']} workspaces")
    else:
        print(f"✗ Error: {result.get('error')}")
    print()


def monitorear_expedientes():
    """Ejecuta monitoreo de expedientes (una verificación)."""
    print("=== Monitorear Expedientes ===")

    payload = {
        "archivo_sistema": "datos/expedientes_sistema.json",
        "workspaces_dir": "datos/workspaces",
        "intervalo_minutos": 60,
        "notificar": False,
    }

    response = requests.post(f"{API_V1}/monitoreo/iniciar", json=payload)

    print(f"Status: {response.status_code}")
    result = response.json()
    print(json.dumps(result, indent=2))

    if result.get("success"):
        print(f"✓ Monitoreo completado: {result['cambios_detectados']} cambios")
        for cambio in result.get("cambios", []):
            print(f"  - {cambio['numero_expediente']}: {cambio['descripcion']}")
    else:
        print(f"✗ Error: {result.get('error')}")
    print()


def main():
    """Ejecuta ejemplos de uso de la API."""
    print("=" * 60)
    print("Ejemplos de uso de la API REST - Sistema PJN v6")
    print("=" * 60)
    print()

    try:
        # 1. Health check
        health_check()

        # 2. Listar expedientes
        listar_expedientes()

        # 3. Obtener expediente específico (si existe)
        # obtener_expediente("CNM 0001/2024")

        # 4. Extraer expedientes (requiere scraping implementado)
        # extraer_expedientes()

        # 5. Filtrar expedientes
        # filtrar_expedientes()

        # 6. Crear workspaces
        # crear_workspaces()

        # 7. Monitorear cambios
        # monitorear_expedientes()

        print("=" * 60)
        print("Ejemplos completados")
        print("=" * 60)

    except requests.exceptions.ConnectionError:
        print("✗ Error: No se puede conectar a la API")
        print("  Asegúrate de que el servidor esté corriendo:")
        print("  uvicorn presentation.api.rest.main:app --reload")


if __name__ == "__main__":
    main()
