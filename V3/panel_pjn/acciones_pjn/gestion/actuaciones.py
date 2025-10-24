from __future__ import annotations
from typing import List, Dict, Optional, Any
import json
import hashlib


def _hash_row(row: Dict[str, Any]) -> str:
    """Genera un hash SHA1 determinístico para una fila de actuación."""
    return hashlib.sha1(
        json.dumps(row, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def comparar_actuaciones(actuales: List[Dict[str, Any]], nuevas: List[Dict[str, Any]]):
    """Compara listas de actuaciones y clasifica diferencias detectadas."""
    map_act = {_hash_row(a): a for a in actuales}
    map_nue = {_hash_row(a): a for a in nuevas}
    agregadas = [v for k, v in map_nue.items() if k not in map_act]
    eliminadas = [v for k, v in map_act.items() if k not in map_nue]

    def idx(a: Dict[str, Any]):
        return (a.get("Indice"), a.get("Fecha"), a.get("Tipo"))

    ia, in_ = {idx(a): a for a in actuales}, {idx(a): a for a in nuevas}
    modificadas = [
        in_[k]
        for k in (ia.keys() & in_.keys())
        if _hash_row(ia[k]) != _hash_row(in_[k])
    ]
    return {
        "agregadas": agregadas,
        "modificadas": modificadas,
        "eliminadas": eliminadas,
    }


async def ingresar_actuaciones(
    expediente_id: str,
    acts: List[Dict[str, Any]],
    descargar: bool = False,
    downloader=None,
):
    """Persiste las actuaciones y opcionalmente descarga los adjuntos."""
    # Hook para persistir (y descargar si hace falta). Completar luego.
    pass


def eliminar_actuaciones_obsoletas(expediente_id: str, criterio: Optional[Any] = None):
    """Borra actuaciones que ya no cumplan con el criterio dado."""
    pass
