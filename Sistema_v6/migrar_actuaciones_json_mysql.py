import os
import json
import mysql.connector
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

def get_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        port=int(os.getenv('MYSQL_PORT', '3306')),
        database=os.getenv('MYSQL_DATABASE', 'sintaxis'),
        user=os.getenv('MYSQL_USER', 'root'),
        password=os.getenv('MYSQL_PASSWORD', ''),
    )

def migrar_actuaciones(json_path, expediente_numero_target):
    print(f"Migrando desde {json_path} para expediente {expediente_numero_target}...")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    actuaciones = data.get('Actuaciones', [])
    print(f"Encontradas {len(actuaciones)} actuaciones en JSON.")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si ya existen para evitar duplicados masivos (aunque ON DUPLICATE KEY ayuda)
    cursor.execute("SELECT COUNT(*) FROM actuaciones WHERE expediente_numero = %s", (expediente_numero_target,))
    count = cursor.fetchone()[0]
    if count > 0:
        print(f"⚠️ Ya existen {count} actuaciones para {expediente_numero_target} en MySQL. Se omitirá la migración para evitar duplicados o inconsistencias.")
        # Opcional: Borrar y reinsertar? Mejor no destruir datos sin confirmar.
        # Pero el usuario dice que "no muestra texto", así que quizás están vacías o mal linkeadas.
        # El debug script dijo 0 actuaciones. Así que count debería ser 0.
    
    if count == 0:
        sql = """
            INSERT INTO actuaciones (
                expediente_numero,
                tipo,
                detalle,
                fecha,
                tiene_archivo,
                ruta_pdf,
                hash_contenido,
                texto_extraido,
                tiene_texto_extraido,
                created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """
        
        inserted = 0
        for act in actuaciones:
            # Parse fecha
            fecha_str = act.get('Fecha')
            fecha_obj = None
            if fecha_str:
                try:
                    fecha_obj = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                except:
                    pass
            
            # Texto extraido? El JSON de actuaciones suele tener metadatos.
            # El texto extraido suele estar en archivos separados (.txt) en la carpeta 'actuaciones'.
            # Pero a veces se guarda en el JSON si es corto.
            # En este formato parece que no está el texto en el JSON principal.
            # Tendré que buscar el .txt correspondiente si existe.
            
            texto = act.get('Texto', '')
            tiene_texto = bool(texto)
            
            # Si no hay texto en JSON, intentar leer del archivo txt si existe
            if not tiene_texto and act.get('NombreArchivo'):
                base_name = act['NombreArchivo']
                # Asumir estructura de carpetas: data/expedientes/.../actuaciones/
                # json_path es .../json/actuaciones-....json
                # txt path sería .../actuaciones/{base_name}.txt (o .pdf.txt)
                
                # Intentar deducir ruta
                json_dir = Path(json_path).parent
                exp_dir = json_dir.parent
                act_dir = exp_dir / "actuaciones"
                
                txt_name = base_name + ".txt"
                txt_path = act_dir / txt_name
                
                if txt_path.exists():
                    try:
                        with open(txt_path, 'r', encoding='utf-8') as ft:
                            texto = ft.read()
                            tiene_texto = True
                    except Exception as e:
                        print(f"Error leyendo texto {txt_path}: {e}")
            
            val = (
                expediente_numero_target,
                act.get('Tipo'),
                act.get('Detalle'),
                fecha_obj,
                1 if act.get('TieneArchivo') else 0,
                act.get('NombreArchivo'), # ruta_pdf
                act.get('Hash'), # hash_contenido
                texto,
                1 if tiene_texto else 0
            )
            
            try:
                cursor.execute(sql, val)
                inserted += 1
            except Exception as e:
                print(f"Error insertando actuacion {act.get('Indice')}: {e}")
        
        conn.commit()
        print(f"✅ Insertadas {inserted} actuaciones para {expediente_numero_target}.")
        
        # Actualizar fecha_ultimo_procesamiento en expedientes
        cursor.execute("UPDATE expedientes SET fecha_ultimo_procesamiento = NOW() WHERE numero_normalizado = %s", (expediente_numero_target,))
        conn.commit()
        print("✅ Actualizado fecha_ultimo_procesamiento.")

    conn.close()

if __name__ == "__main__":
    # Ruta hardcodeada para el caso específico
    json_file = "data/expedientes/000001_FPA_001961_2024/json/actuaciones-FPA_001961_2024.json"
    target_numero = "FPA_001961_2024" # Usar normalizado
    
    if os.path.exists(json_file):
        migrar_actuaciones(json_file, target_numero)
    else:
        print(f"Archivo no encontrado: {json_file}")
