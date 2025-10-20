from __future__ import annotations

from pathlib import Path
import sys
import json

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.gestor_directorios_expedientes import (
    ESTRUCTURA_POR_DEFECTO,
    GestorDirectoriosExpedientes,
)


def _listar_directorios(estructura: dict[str, object], prefijo: str = "") -> set[str]:
    """Devuelve el conjunto de rutas relativas esperado."""

    rutas: set[str] = set()
    for nombre, subestructura in estructura.items():
        ruta = f"{prefijo}{nombre}" if not prefijo else f"{prefijo}/{nombre}"
        rutas.add(ruta)
        if isinstance(subestructura, dict):
            rutas.update(_listar_directorios(subestructura, ruta))
    return rutas


def test_generar_arbol_crea_estructura_basica(tmp_path: Path) -> None:
    gestor = GestorDirectoriosExpedientes(tmp_path)
    manifest = gestor.generar_arbol()

    rutas_esperadas = _listar_directorios(ESTRUCTURA_POR_DEFECTO)
    for ruta in rutas_esperadas:
        assert (tmp_path / ruta).is_dir(), f"Falta el directorio: {ruta}"

    manifest_path = tmp_path / "manifest.json"
    assert manifest_path.exists(), "Se esperaba el archivo manifest.json"

    contenido_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert "directories" in contenido_manifest
    assert set(contenido_manifest["directories"]) >= rutas_esperadas
    assert "actuaciones/documentos_usuario" in contenido_manifest["directories"]
    assert "actuaciones/documentos_usuario" in manifest["directories"]
