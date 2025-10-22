from __future__ import annotations

import sys
import json
from copy import deepcopy
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
    assert "documentos_usuario" in contenido_manifest["directories"]
    assert "documentos_usuario" in manifest["directories"]


def test_generar_arbol_permita_extender_estructura(tmp_path: Path) -> None:
    gestor = GestorDirectoriosExpedientes(tmp_path)

    estructura_extra = {
        "documentos_usuario": {
            "firmados": None,
        },
        "audiencias": {
            "multimedia": None,
        },
    }

    manifest = gestor.generar_arbol(estructura=estructura_extra)

    estructura_combinada = deepcopy(ESTRUCTURA_POR_DEFECTO)
    estructura_combinada["documentos_usuario"] = {"firmados": None}
    estructura_combinada["audiencias"] = {"multimedia": None}

    rutas_combinadas = _listar_directorios(estructura_combinada)

    for ruta in rutas_combinadas:
        assert (tmp_path / ruta).is_dir()

    assert "audiencias" in manifest["directories"]
    assert "documentos_usuario/firmados" in manifest["directories"]


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


def test_actualizar_estructura_permita_reemplazar(tmp_path: Path) -> None:
    gestor = GestorDirectoriosExpedientes(tmp_path)
    gestor.actualizar_estructura({"personalizado": {"docs": None}}, reemplazar=True)

    manifest = gestor.generar_arbol()

    assert set(manifest["directories"]) == {
        "personalizado",
        "personalizado/docs",
    }

    assert (tmp_path / "actuaciones").exists() is False


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
    assert "documentos_usuario" in manifest["directories"]


def test_resolver_ruta_expande_home_y_variables(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("EXPEDIENTES_DIR", str(tmp_path / "desde_env"))

    ruta_env = GestorDirectoriosExpedientes._resolver_ruta(
        "$EXPEDIENTES_DIR/subcarpeta",
        base_dir=None,
        config_path=None,
    )
    assert ruta_env == tmp_path / "desde_env" / "subcarpeta"

    ruta_home = GestorDirectoriosExpedientes._resolver_ruta(
        "~/expedientes_home",
        base_dir=None,
        config_path=None,
    )
    assert ruta_home == Path.home() / "expedientes_home"
