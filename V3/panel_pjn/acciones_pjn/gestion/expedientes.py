from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json, os

BASE_DIR = Path.cwd()
DATOS_DIR = BASE_DIR / "datos_extraidos"
MONITOREO_DIR = DATOS_DIR / "monitoreo"
ACTUACIONES_DIR = DATOS_DIR / "actuaciones"
NOTIFICACIONES_DIR = DATOS_DIR / "notificaciones"
ESCRITOS_DIR = DATOS_DIR / "escritos"
BASE_SIMULADA_DIR = BASE_DIR / "base_datos_simulada"

for d in (MONITOREO_DIR, ACTUACIONES_DIR, NOTIFICACIONES_DIR, ESCRITOS_DIR, BASE_SIMULADA_DIR):
    d.mkdir(parents=True, exist_ok=True)

def _guardar_json_atomic(obj: Any, ruta: Path) -> Path:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
    os.replace(tmp, ruta)
    return ruta

def _cargar_json(ruta: Path, default: Any) -> Any:
    if not ruta.exists():
        return default
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

@dataclass
class MetaExpediente:
    numero: str
    caratula: Optional[str] = None
    jurisdiccion: Optional[str] = None
    dependencia: Optional[str] = None
    situacion: Optional[str] = None
    fecha_inicio: Optional[str] = None
    ultima_actuacion: Optional[str] = None
    cantidad_actuaciones: Optional[int] = None
    cantidad_descargas: Optional[int] = None
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

def crear_estructura_expediente(numero: str) -> Path:
    n = numero.replace("/", "-") if numero else "sin_numero"
    for sub in (ACTUACIONES_DIR / n, NOTIFICACIONES_DIR / n, ESCRITOS_DIR / n):
        sub.mkdir(parents=True, exist_ok=True)
    return (ACTUACIONES_DIR / n).parent

def guardar_metadata_expediente(meta: MetaExpediente) -> Path:
    n = (meta.numero or "sin_numero").replace("/", "-")
    ruta = ACTUACIONES_DIR / n / "metadata.json"
    return _guardar_json_atomic(meta.to_dict(), ruta)

def exportar_expedientes_a_base(expedientes: List[Dict[str, Any]]) -> Path:
    for exp in expedientes:
        num = (exp.get("numero") or "sin_numero").replace("/", "-")
        _guardar_json_atomic(exp, BASE_SIMULADA_DIR / f"{num}.json")
    return BASE_SIMULADA_DIR

def seleccionar_expedientes(
    expedientes: List[Dict[str, Any]],
    *, incluir_jurisdicciones: Optional[Iterable[str]] = None,
    excluir_dependencias: Optional[Iterable[str]] = None,
    anio_min: Optional[int] = None, anio_max: Optional[int] = None,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    inc_j = set(map(str, incluir_jurisdicciones)) if incluir_jurisdicciones else None
    exc_d = set(map(str, excluir_dependencias)) if excluir_dependencias else None
    for e in expedientes:
        ok = True
        if inc_j: ok &= str(e.get("jurisdiccion")) in inc_j
        if exc_d: ok &= str(e.get("dependencia")) not in exc_d
        if anio_min or anio_max:
            fi = (e.get("fecha_inicio") or e.get("FechaInicio") or "")[:4]
            if fi.isdigit():
                anio = int(fi)
                if anio_min and anio < anio_min: ok = False
                if anio_max and anio > anio_max: ok = False
        if ok: out.append(e)
    return out

DESCARTADOS_JSON = MONITOREO_DIR / "expedientes_descartados.json"
def marcar_descartado(numero: str) -> None:
    lst = _cargar_json(DESCARTADOS_JSON, default=[])
    if numero not in lst:
        lst.append(numero); _guardar_json_atomic(lst, DESCARTADOS_JSON)

def desmarcar_descartado(numero: str) -> None:
    lst = _cargar_json(DESCARTADOS_JSON, default=[])
    if numero in lst:
        lst.remove(numero); _guardar_json_atomic(lst, DESCARTADOS_JSON)

def es_descartado(numero: str) -> bool:
    return numero in set(_cargar_json(DESCARTADOS_JSON, default=[]))
