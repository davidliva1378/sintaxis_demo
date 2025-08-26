from __future__ import annotations
from typing import List, Dict, Optional, Any
import json, hashlib

def _hash_row(row: Dict[str, Any]) -> str:
    return hashlib.sha1(json.dumps(row, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

def comparar_actuaciones(actuales: List[Dict[str, Any]], nuevas: List[Dict[str, Any]]):
    map_act = { _hash_row(a): a for a in actuales }
    map_nue = { _hash_row(a): a for a in nuevas }
    agregadas  = [v for k,v in map_nue.items() if k not in map_act]
    eliminadas = [v for k,v in map_act.items() if k not in map_nue]
    idx = lambda a: (a.get("Indice"), a.get("Fecha"), a.get("Tipo"))
    ia, in_ = {idx(a): a for a in actuales}, {idx(a): a for a in nuevas}
    modificadas = [in_[k] for k in (ia.keys() & in_.keys()) if _hash_row(ia[k]) != _hash_row(in_[k])]
    return {"agregadas": agregadas, "modificadas": modificadas, "eliminadas": eliminadas}

async def ingresar_actuaciones(expediente_id: str, acts: List[Dict[str, Any]], descargar: bool=False, downloader=None):
    # Hook para persistir (y descargar si hace falta). Completar luego.
    pass

def eliminar_actuaciones_obsoletas(expediente_id: str, criterio: Optional[Any]=None):
    pass
