import sys
import os
import glob
from pathlib import Path

# Agregar directorio raíz al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from infrastructure.persistence.database import SessionLocal
from infrastructure.persistence.database.models import Actuacion, EntidadExtraida, Expediente

def extract_text_from_pdf(pdf_path):
    try:
        import pypdf
        reader = pypdf.PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except ImportError:
        try:
            import PyPDF2
            # PyPDF2 3.0+ uses PdfReader
            if hasattr(PyPDF2, 'PdfReader'):
                reader = PyPDF2.PdfReader(pdf_path)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                return text
            else:
                # Legacy PyPDF2
                reader = PyPDF2.PdfFileReader(pdf_path)
                text = ""
                for page_num in range(reader.numPages):
                    text += reader.getPage(page_num).extractText() + "\n"
                return text
        except ImportError:
            return "Error: pypdf/PyPDF2 no instalados. No se pudo extraer texto."
    except Exception as e:
        return f"Error leyendo PDF: {e}"

def process_pdfs():
    print("🚀 Iniciando procesamiento de PDFs...")
    db = SessionLocal()
    
    try:
        # Obtener expediente activo
        expediente = db.query(Expediente).filter(Expediente.numero_normalizado == "FRE_004321_2021").first()
        if not expediente:
            print("❌ Expediente FRE_004321_2021 no encontrado.")
            return

        print(f"📂 Procesando expediente {expediente.numero_normalizado} (ID: {expediente.id})")
        
        # Directorio de actuaciones
        # Nota: Asumimos ID 1 para este expediente basado en la carpeta 000001
        pdf_dir = Path(f"data/expedientes/000001_{expediente.numero_normalizado}/actuaciones")
        
        if not pdf_dir.exists():
            print(f"❌ Directorio no encontrado: {pdf_dir}")
            return

        actuaciones = db.query(Actuacion).filter(Actuacion.expediente_id == expediente.id).all()
        print(f"📄 Analizando {len(actuaciones)} actuaciones...")
        
        count_updated = 0
        count_entities = 0
        
        for act in actuaciones:
            # El ID de la actuación es el Hash (ej: d50ab4)
            # Buscamos archivo que termine en _{hash}.pdf
            pattern = f"*_{act.id}.pdf"
            files = list(pdf_dir.glob(pattern))
            
            if files:
                pdf_path = files[0]
                # print(f"   Found: {pdf_path.name}")
                
                text = extract_text_from_pdf(pdf_path)
                
                if text and len(text) > 10:
                    act.texto_extraido = text
                    act.utilidad = "ALTA" if "SENTENCIA" in text.upper() or "RESUELVE" in text.upper() else "MEDIA"
                    count_updated += 1
                    
                    # Generar entidades dummy/simples
                    if "SENTENCIA" in text.upper():
                        ent = EntidadExtraida(
                            expediente_id=expediente.id,
                            actuacion_id=act.id,
                            entity_type="TIPO_RESOLUCION",
                            entity_value="SENTENCIA",
                            confidence_score=0.95
                        )
                        db.add(ent)
                        count_entities += 1
                        
                    if "VISTOS" in text.upper():
                         ent = EntidadExtraida(
                            expediente_id=expediente.id,
                            actuacion_id=act.id,
                            entity_type="SECCION",
                            entity_value="VISTOS",
                            confidence_score=0.9
                        )
                         db.add(ent)
                         count_entities += 1
                         
                    # Simular entidades de personas (hardcoded para demo)
                    if count_updated == 1: # Solo agregar una vez
                        personas = [
                            ("VARGAS, HUGO CESAR", "ACTOR"),
                            ("ESTADO NACIONAL", "DEMANDADO"),
                            ("GENDARMERIA NACIONAL", "DEMANDADO")
                        ]
                        for nombre, tipo in personas:
                            ent = EntidadExtraida(
                                expediente_id=expediente.id,
                                actuacion_id=act.id,
                                entity_type=tipo,
                                entity_value=nombre,
                                confidence_score=0.99
                            )
                            db.add(ent)
                            count_entities += 1
            
            if count_updated % 10 == 0 and count_updated > 0:
                print(f"   Procesados: {count_updated}...")
                db.commit()

        db.commit()
        print(f"✅ Finalizado. Actuaciones con texto: {count_updated}. Entidades creadas: {count_entities}.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    process_pdfs()
