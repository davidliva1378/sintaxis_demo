"""
Script de testing para procesar un expediente completo con todas las opciones.
"""
import requests
import json
import time

API_BASE = "http://127.0.0.1:8000/api/v1"

# Expediente de prueba
EXPEDIENTE_TEST = "FPA 024925/2018"

# Configuración completa
config = {
    "headless": True,
    "umbral_errores": 10,
    "timeout_pagina": 30000,
    "max_reintentos": 3,
    "procesar_con_pdf": True,  # Activar descarga de PDFs
    "incluir_historicas": True,
    "min_utilidad": "MEDIA",
    "directorio_base": "./Sistema_v6/data/expedientes"
}

print(f"=== Test de Procesamiento de Expediente ===")
print(f"Expediente: {EXPEDIENTE_TEST}")
print(f"Config: procesar_con_pdf={config['procesar_con_pdf']}")
print()

# Procesar expediente
print("📤 Enviando solicitud de procesamiento...")
response = requests.post(
    f"{API_BASE}/extraccion-masiva/procesar-seleccionados",
    json={
        "numeros_expedientes": [EXPEDIENTE_TEST],
        "config": config
    },
    timeout=300  # 5 minutos timeout
)

if response.status_code == 200:
    data = response.json()
    session_id = data.get("session_id")
    resumen = data.get("resumen", {})

    print(f"✅ Procesamiento completado")
    print(f"Session ID: {session_id}")
    print()
    print("📊 Resumen:")
    print(f"  - Total: {resumen.get('total', 0)}")
    print(f"  - Exitosos: {resumen.get('exitosos', 0)}")
    print(f"  - Errores: {resumen.get('errores', 0)}")
    print(f"  - Omitidos: {resumen.get('omitidos', 0)}")
    print(f"  - Tiempo total: {resumen.get('tiempo_total', 0):.2f}s")
    print(f"  - Tasa de éxito: {resumen.get('tasa_exito', 0)*100:.1f}%")

    if resumen.get('errores_detalles'):
        print()
        print("⚠️ Errores:")
        for error in resumen['errores_detalles']:
            print(f"  - {error['numero']}: {error['error']}")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text)
