
import os
import sys
from pathlib import Path

# Agregar root al path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.procesador_pdf.extractor_texto import ExtractorTexto

def test_extraccion():
    print("=== Iniciando Prueba de Extracción de Texto ===")
    
    # PDF específico encontrado
    pdf_path = Path("data/expedientes/000001_FPA_001961_2024/actuaciones/2025-11-28_cedula_electronica_tribunal_b44422.pdf")
    
    if not pdf_path.exists():
        print(f"❌ El archivo {pdf_path} no existe.")
        return

    print(f"📄 Probando con archivo: {pdf_path}")
    
    try:
        extractor = ExtractorTexto(usar_ocr=True)
        resultado = extractor.extraer(str(pdf_path))
        
        print("\n--- Resultados ---")
        print(f"Método usado: {resultado.metodo_extraccion}")
        print(f"Tiene texto embebido: {resultado.tiene_texto_embebido}")
        print(f"Longitud caracteres: {resultado.longitud_caracteres}")
        print(f"Longitud palabras: {resultado.longitud_palabras}")
        print(f"Hash contenido: {resultado.hash_contenido}")
        
        print("\n--- Primeros 500 caracteres ---")
        print(resultado.texto_normalizado[:500])
        print("-------------------------------")
        
        if resultado.longitud_caracteres > 0:
            print("✅ Extracción EXITOSA: Se obtuvo texto.")
        else:
            print("⚠️ Extracción VACÍA: El archivo no devolvió texto.")
            
    except Exception as e:
        print(f"❌ Error durante la extracción: {e}")

if __name__ == "__main__":
    test_extraccion()
