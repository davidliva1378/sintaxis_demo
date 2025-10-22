from __future__ import annotations

import sys
import json
from copy import deepcopy
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Sistema_v5.gestor_directorios import (
    ESTRUCTURA_POR_DEFECTO,
    GestorDirectoriosExpedientes,
    inicializar_directorio_base,
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


def test_generar_arbol_reescritura_manifest_es_atomica(tmp_path: Path) -> None:
    gestor = GestorDirectoriosExpedientes(tmp_path)

    manifest_primera = gestor.generar_arbol(metadata={"ronda": 1})
    manifest_segunda = gestor.generar_arbol(metadata={"ronda": 2})

    manifest_path = tmp_path / "manifest.json"
    contenido_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert contenido_manifest == manifest_segunda
    assert "directories" in contenido_manifest
    assert manifest_primera["directories"] == manifest_segunda["directories"]
    assert contenido_manifest["metadata"] == {"ronda": 2}


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

    ruta_esperada = tmp_path / "expedientes" / "000001_Exp_123_2024"
    assert ruta_expediente == ruta_esperada
    assert manifest["metadata"]["numero_expediente"] == "Exp 123/2024"
    assert manifest["metadata"]["numero_normalizado"] == "Exp_123_2024"
    assert manifest["metadata"]["id"] == 1

    manifest_path = ruta_expediente / "manifest.json"
    assert manifest_path.exists()
    contenido_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert contenido_manifest == manifest

    indice_path = tmp_path / "expedientes" / "expedientes_index.json"
    assert indice_path.exists()


def test_creacion_multiple_asigna_ids_consecutivos(tmp_path: Path) -> None:
    gestor = GestorDirectoriosExpedientes(tmp_path)

    ruta_1, manifest_1 = gestor.crear_para_expediente("Exp 1/2024")
    ruta_2, manifest_2 = gestor.crear_para_expediente("Exp 2/2024")

    assert ruta_1.name.startswith("000001_")
    assert ruta_2.name.startswith("000002_")
    assert manifest_1["metadata"]["id"] == 1
    assert manifest_2["metadata"]["id"] == 2

    indice = json.loads((tmp_path / "expedientes_index.json").read_text(encoding="utf-8"))
    assert indice["last_id"] == 2
    assert indice["expedientes"][manifest_1["metadata"]["numero_normalizado"]] == 1
    assert indice["expedientes"][manifest_2["metadata"]["numero_normalizado"]] == 2


def test_reimportacion_conserva_identificador(tmp_path: Path) -> None:
    gestor = GestorDirectoriosExpedientes(tmp_path)

    ruta_1, manifest_1 = gestor.crear_para_expediente("Exp 321/2023")
    ruta_2, manifest_2 = gestor.crear_para_expediente("Exp 321/2023")

    assert ruta_1 == ruta_2
    assert manifest_1["metadata"]["id"] == manifest_2["metadata"]["id"] == 1

    indice = json.loads((tmp_path / "expedientes_index.json").read_text(encoding="utf-8"))
    assert indice["last_id"] == 1


def test_indice_persistente_tras_reinicio(tmp_path: Path) -> None:
    gestor_inicial = GestorDirectoriosExpedientes(tmp_path)
    _, manifest_1 = gestor_inicial.crear_para_expediente("Exp 10/2024")

    gestor_recreado = GestorDirectoriosExpedientes(tmp_path)
    ruta_2, manifest_2 = gestor_recreado.crear_para_expediente("Exp 11/2024")

    assert manifest_1["metadata"]["id"] == 1
    assert manifest_2["metadata"]["id"] == 2
    assert ruta_2.name.startswith("000002_")

    indice = json.loads((tmp_path / "expedientes_index.json").read_text(encoding="utf-8"))
    assert indice["last_id"] == 2
    assert set(indice["expedientes"].values()) == {1, 2}


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
    assert ruta == tmp_path / "data" / "expedientes" / "000001_123"
    assert "documentos_usuario" in manifest["directories"]


def test_generar_arbol_rechaza_componentes_maliciosos(tmp_path: Path) -> None:
    gestor = GestorDirectoriosExpedientes(tmp_path)

    estructura_maliciosa = {"../malicioso": None}

    with pytest.raises(ValueError, match="malicioso"):
        gestor.generar_arbol(estructura=estructura_maliciosa, fusionar_estructura=False)

    objetivo = tmp_path.parent / "malicioso"
    assert not objetivo.exists()


def test_generar_arbol_rechaza_componentes_multisegmento(tmp_path: Path) -> None:
    gestor = GestorDirectoriosExpedientes(tmp_path)

    estructura_invalida = {"sub/carpeta": None}

    with pytest.raises(ValueError, match="sub/carpeta"):
        gestor.generar_arbol(estructura=estructura_invalida, fusionar_estructura=False)

    assert not (tmp_path / "sub").exists()


@pytest.mark.parametrize(
    "entradas, espera_error, mensaje, ruta_esperada, id_esperado",
    [
        pytest.param(
            [
                {
                    "numero_expediente": "Exp 123/2024",
                    "metadata": {"actor": "PJN"},
                }
            ],
            False,
            None,
            "000001_Exp_123_2024",
            1,
            id="entrada_valida",
        ),
        pytest.param(
            [
                {"numero_expediente": "Exp 123/2024"},
                {"numero_expediente": "Exp 123/2024"},
            ],
            True,
            "repetido",
            "000001_Exp_123_2024",
            1,
            id="entrada_repetida",
        ),
        pytest.param(
            [
                {"metadata": {"actor": "SinNumero"}},
            ],
            True,
            "numero_expediente",
            None,
            None,
            id="entrada_sin_numero",
        ),
    ],
)
def test_crear_desde_json(
    tmp_path: Path,
    entradas,
    espera_error,
    mensaje,
    ruta_esperada,
    id_esperado,
):
    gestor = GestorDirectoriosExpedientes(tmp_path)

    if espera_error:
        with pytest.raises(ValueError) as excinfo:
            gestor.crear_desde_json(entradas)

        assert mensaje is not None and mensaje in str(excinfo.value)
        if ruta_esperada is not None:
            manifest_path = tmp_path / ruta_esperada / "manifest.json"
            assert manifest_path.exists(), "El primer expediente debería haberse creado"
    else:
        resultados = gestor.crear_desde_json(entradas)

        assert len(resultados) == len(entradas)
        ruta, manifest = resultados[0]

        assert ruta == tmp_path / ruta_esperada
        assert manifest["metadata"]["numero_expediente"] == entradas[0]["numero_expediente"]
        assert ruta_esperada.endswith(manifest["metadata"]["numero_normalizado"])
        assert manifest["metadata"]["actor"] == "PJN"
        assert manifest["metadata"]["id"] == id_esperado
        manifest_path = ruta / "manifest.json"
        assert manifest_path.exists()


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


def test_inicializar_directorio_base_sin_config_explicit(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    config_path = tmp_path / "config" / "sistema.json"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        json.dumps({"directorio_expedientes_base": "expedientes_desde_archivo"}),
        encoding="utf-8",
    )

    manifest = inicializar_directorio_base(config_path=config_path)

    raiz = tmp_path / "expedientes_desde_archivo"
    rutas_esperadas = _listar_directorios(ESTRUCTURA_POR_DEFECTO)

    for ruta in rutas_esperadas:
        assert (raiz / ruta).is_dir(), f"No se creó el directorio esperado: {ruta}"

    manifest_path = raiz / "manifest.json"
    assert manifest_path.exists(), "Se esperaba el manifiesto en la raíz"
    assert config_path.exists(), "La configuración debería haberse materializado en disco"

    contenido_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert set(contenido_manifest["directories"]) >= rutas_esperadas
    assert manifest == contenido_manifest


def test_inicializar_directorio_base_con_base_dir_personalizado(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    config = SystemConfig()
    config.directorio_expedientes_base = "expedientes_personalizados"

    manifest = inicializar_directorio_base(
        config=config,
        base_dir=tmp_path,
    )

    raiz = tmp_path / "expedientes_personalizados"

    for ruta in _listar_directorios(ESTRUCTURA_POR_DEFECTO):
        assert (raiz / ruta).is_dir()

    manifest_path = raiz / "manifest.json"
    assert manifest_path.exists()
    contenido_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest == contenido_manifest
