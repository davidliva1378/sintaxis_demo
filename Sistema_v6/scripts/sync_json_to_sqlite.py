#!/usr/bin/env python3
"""
Script de sincronización de JSON a SQLite.
Puebla la base de datos SQLite con la información de los archivos JSON generados por el scraper.
"""

import json
import os
import sys
import glob
from datetime import datetime
from pathlib import Path

# Agregar directorio raíz al path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from infrastructure.persistence.database import SessionLocal, engine
from infrastructure.persistence.database.models import Expediente, Actuacion

def normalize_number(numero: str) -> str:
    """Normaliza el número de expediente (ej: 'FRE 123/2021' -> 'FRE_123_2021')."""
    return numero.replace(" ", "_").replace("/", "_")

def parse_date(date_str: str):
    """Parsea fecha en formato YYYY-MM-DD o DD/MM/YYYY."""
    if not date_str:
        return None
    for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S"]:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None

def sync():
    print(f"🔄 Iniciando sincronización a {engine.url}...")
    db = SessionLocal()
    
    try:
        # 1. Cargar Índice de Expedientes (Mapping Numero -> ID)
        index_path = Path("data/expedientes/expedientes_index.json")
        exp_id_map = {}
        if index_path.exists():
            with open(index_path, 'r', encoding='utf-8') as f:
                index_data = json.load(f)
                # Invertir el mapa: {numero_normalizado: id}
                exp_id_map = index_data.get("expedientes", {})
            print(f"📋 Índice cargado: {len(exp_id_map)} expedientes mapeados.")

        # 2. Sincronizar Expedientes desde Listado Base
        base_path = Path("data/extraccion_masiva/listados/listado_base.json")
        count_exp = 0
        if base_path.exists():
            with open(base_path, 'r', encoding='utf-8') as f:
                base_data = json.load(f)
            
            print(f"📂 Procesando {len(base_data.get('expedientes', []))} expedientes del listado base...")
            
            for item in base_data.get("expedientes", []):
                numero_original = item.get("numero")
                numero_norm = normalize_number(numero_original)
                
                # Buscar si ya existe en DB
                exp_db = db.query(Expediente).filter(Expediente.numero_normalizado == numero_norm).first()
                
                if not exp_db:
                    # Si no existe, creamos instancia
                    exp_db = Expediente()
                    exp_db.numero_normalizado = numero_norm
                    
                    # Intentar asignar ID del índice si existe
                    if numero_norm in exp_id_map:
                        desired_id = exp_id_map[numero_norm]
                        # Verificar si ese ID ya está usado por OTRO expediente (caso raro de colisión)
                        existing_id = db.query(Expediente).filter(Expediente.id == desired_id).first()
                        if not existing_id:
                            exp_db.id = desired_id
                        else:
                            print(f"⚠️ ID {desired_id} ya existe para otro expediente. Dejando que SQLite asigne uno nuevo para {numero_norm}.")
                
                # Actualizar campos
                exp_db.numero_original = numero_original
                exp_db.caratula = item.get("caratula")
                exp_db.dependencia = item.get("dependencia")
                exp_db.situacion = item.get("situacion")
                exp_db.ultima_actuacion = parse_date(item.get("ultima_actuacion"))
                exp_db.fecha_creacion = parse_date(item.get("fecha_inicio")) or datetime.utcnow()
                
                # Por defecto, si viene del listado base y no tiene carpeta, es 'pendiente' (detectado pero no procesado)
                # Si ya estaba 'activo', lo mantenemos (la lógica de carpetas lo confirmará o no)
                if not exp_db.estado_monitoreo or exp_db.estado_monitoreo == 'activo':
                     exp_db.estado_monitoreo = 'pendiente'

                # Usar merge para manejar el estado de la sesión correctamente
                db.add(exp_db)
                db.flush() # Forzar flush para que la próxima query lo vea
                count_exp += 1
            
            db.commit()
            print(f"✅ {count_exp} expedientes sincronizados desde listado base (marcados como pendientes).")
        else:
            print("⚠️ No se encontró listado_base.json")

        # 3. Sincronizar Actuaciones desde Carpetas
        print("📂 Buscando actuaciones en carpetas...")
        exp_dir = Path("data/expedientes")
        count_act = 0
        count_active_exp = 0
        
        # Iterar sobre carpetas de expedientes
        for folder in exp_dir.iterdir():
            if folder.is_dir() and "_" in folder.name:
                # Intentar obtener el ID y numero del nombre de la carpeta
                try:
                    parts = folder.name.split("_", 1)
                    if not parts[0].isdigit():
                        continue
                        
                    folder_id = int(parts[0])
                    folder_num_norm = parts[1]
                    
                    # Buscar el expediente en DB
                    exp_db = db.query(Expediente).filter(Expediente.numero_normalizado == folder_num_norm).first()
                    
                    if not exp_db:
                        # Si no estaba en el listado base pero sí tiene carpeta, lo creamos
                        exp_db = Expediente(
                            id=folder_id,
                            numero_normalizado=folder_num_norm,
                            numero_original=folder_num_norm.replace("_", " ") # Aproximación
                        )
                    
                    # Si tiene carpeta, está ACTIVO
                    exp_db.estado_monitoreo = 'activo'
                    count_active_exp += 1
                    
                    db.add(exp_db)
                    db.commit()
                    db.refresh(exp_db)

                    # Buscar archivo de actuaciones JSON
                    json_files = list(folder.glob("json/actuaciones-*.json"))
                    if not json_files:
                        continue
                        
                    json_path = json_files[0]
                    with open(json_path, 'r', encoding='utf-8') as f:
                        act_data = json.load(f)
                    
                    actuaciones_list = act_data.get("Actuaciones", [])
                    
                    for act in actuaciones_list:
                        act_id = act.get("Hash") or str(act.get("Indice"))
                        
                        # Buscar si existe
                        act_db = db.query(Actuacion).filter(Actuacion.id == act_id).first()
                        
                        if not act_db:
                            act_db = Actuacion(id=act_id)
                        
                        act_db.expediente_id = exp_db.id
                        act_db.fecha = parse_date(act.get("Fecha"))
                        act_db.tipo_ia = act.get("Tipo")
                        act_db.detalle = act.get("Detalle")
                        act_db.utilidad = "MEDIA" # Default
                        
                        # Check if text exists (simple check based on file existence logic could be added here)
                        # For now, leave text null
                        
                        db.add(act_db)
                        count_act += 1
                        
                except Exception as e:
                    print(f"⚠️ Error procesando carpeta {folder.name}: {e}")
                    continue

        db.commit()
        print(f"✅ {count_act} actuaciones sincronizadas.")
        
    except Exception as e:
        print(f"❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    sync()
