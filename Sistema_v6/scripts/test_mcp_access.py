#!/usr/bin/env python3
"""
Script de prueba para verificar acceso al expediente 4134/2020 via ToolsService.
"""
import sys
import os

# Cargar variables de entorno ANTES de importar módulos
from dotenv import load_dotenv
load_dotenv()

# Agregar path del proyecto
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from application.services.ia.tools_service import ToolsService

# Crear instancia del servicio
tools = ToolsService()

print("=== Prueba 1: buscar_expedientes ===")
try:
    result = tools.buscar_expedientes("4134/2020")
    print(f"Resultados: {len(result)}")
    for exp in result:
        print(f"  - {exp.get('numero')} | Estado: {exp.get('estado')}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Prueba 2: obtener_expediente ===")
try:
    result = tools.obtener_expediente("4134/2020")
    if result:
        print(f"Encontrado: {result.get('numero')}")
        print(f"Estado: {result.get('estado_monitoreo')}")
        print(f"Actuaciones: {result.get('total_actuaciones')}")
        print(f"Entidades: {result.get('total_entidades')}")
    else:
        print("No encontrado")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Prueba 3: listar_expedientes (activos) ===")
try:
    result = tools.listar_expedientes(estado="activo", limite=10)
    print(f"Expedientes activos: {len(result)}")
    for exp in result:
        print(f"  - {exp.get('numero')} | {exp.get('caratula') or 'Sin carátula'}")
except Exception as e:
    print(f"Error: {e}")

print("\n=== Prueba 4: listar_expedientes (todos) ===")
try:
    result = tools.listar_expedientes(estado=None, limite=10)
    print(f"Total expedientes: {len(result)}")
    for exp in result:
        print(f"  - {exp.get('numero')} | Estado: {exp.get('estado')}")
except Exception as e:
    print(f"Error: {e}")
