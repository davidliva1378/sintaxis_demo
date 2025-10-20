from __future__ import annotations

import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Sistema_v5.gestor_directorios import (
    ESTRUCTURA_POR_DEFECTO,
    GestorDirectoriosExpedientes,
)
from Sistema_v5.configuracion.core.system_config import SystemConfig


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


def test_crear_para_expediente_normaliza_y_agrega_metadata(tmp_path: Path) -> None:
    gestor = GestorDirectoriosExpedientes(tmp_path / "expedientes")

    ruta_expediente, manifest = gestor.crear_para_expediente("Exp 123/2024")

    assert ruta_expediente == tmp_path / "expedientes" / "Exp_123_2024"
    assert manifest["numero_expediente"] == "Exp 123/2024"
    assert manifest["numero_normalizado"] == "Exp_123_2024"

    manifest_path = ruta_expediente / "manifest.json"
    assert manifest_path.exists()
    contenido_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert contenido_manifest == manifest


def test_desde_config_resuelve_ruta_relativa(tmp_path: Path) -> None:
    config = SystemConfig()
    config.directorio_expedientes_base = "data/expedientes"

    gestor = GestorDirectoriosExpedientes.desde_config(
        config,
        base_dir=tmp_path,
    )

    assert gestor.raiz == tmp_path / "data" / "expedientes"

    ruta, manifest = gestor.crear_para_expediente("123")
    assert ruta == tmp_path / "data" / "expedientes" / "123"
    assert "actuaciones/documentos_usuario" in manifest["directories"]
