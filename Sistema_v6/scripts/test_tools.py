import sys
import os
import json

# Agregar directorio raíz al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from application.services.ia.tools_service import ToolsService

def test_tools():
    service = ToolsService()
    
    print("--- Test: listar_expedientes (default: activos) ---")
    try:
        expedientes = service.listar_expedientes()
        print(f"Expedientes encontrados: {len(expedientes)}")
        for exp in expedientes:
            print(f" - {exp['numero_normalizado']} ({exp['caratula'][:50]}...)")
            
        if len(expedientes) == 1 and expedientes[0]['numero_normalizado'] == 'FRE_004321_2021':
            print("✅ Resultado correcto: 1 expediente activo.")
        else:
            print(f"⚠️ Resultado inesperado: Se esperaban 1, se encontraron {len(expedientes)}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n--- Test: listar_expedientes (pendientes) ---")
    try:
        expedientes = service.listar_expedientes(estado="pendiente", limite=5)
        print(f"Expedientes pendientes (top 5): {len(expedientes)}")
        for exp in expedientes:
            print(f" - {exp['numero_normalizado']}")
            
        if len(expedientes) > 0:
            print("✅ Resultado correcto: Se encontraron expedientes pendientes.")
    except Exception as e:
        print(f"❌ Error: {e}")

    print("\n--- Test: listar_entidades ---")
    try:
        entidades = service.listar_entidades(expediente_numero="FRE_004321_2021")
        print(f"Entidades encontradas: {len(entidades)}")
        for ent in entidades[:5]:
            print(f" - {ent['tipo']}: {ent['valor']} (Score: {ent['score']})")
            
        if len(entidades) > 0:
            print("✅ Resultado correcto: Se encontraron entidades.")
        else:
            print("⚠️ Resultado inesperado: No se encontraron entidades.")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_tools()
