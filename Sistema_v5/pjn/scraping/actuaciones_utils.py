import re
import hashlib
from datetime import datetime

def limpiar_texto(texto: str) -> str:
    if not texto:
        return ""
    return re.sub(r'^(Oficina:|Fecha:|Tipo actuacion:|Detalle:|Foja:)?\s*', '', texto.strip().replace("\n", " "))

def normalizar_fecha(texto: str) -> str:
    try:
        return datetime.strptime(texto, "%d/%m/%Y").strftime("%Y-%m-%d")
    except Exception:
        return texto

def generar_hash_archivo(fecha: str, tipo: str, detalle: str, longitud: int = 6) -> str:
    base_str = f"{fecha}_{tipo}_{detalle}"
    return hashlib.sha256(base_str.encode("utf-8")).hexdigest()[:longitud]

