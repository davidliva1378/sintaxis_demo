"""Tests para el módulo de exportación/importación de expedientes."""

from __future__ import annotations

import json
import pytest
from datetime import datetime
from pathlib import Path
from typing import Any

from Sistema_v5.pjn.models.expediente import ExpedienteResumen
from Sistema_v5.extractor_inicial.exporters import (
    exportar_json,
    exportar_csv,
    cargar_json,
    cargar_csv,
)


@pytest.fixture
def expedientes_muestra() -> list[ExpedienteResumen]:
    """Genera expedientes de prueba."""
    return [
        ExpedienteResumen(
            numero="123/2024",
            dependencia="JUZ. CIV. Y COM. FED. 1",
            caratula="TEST S/ PRUEBA",
            situacion="En trámite",
            ultima_actuacion="15/01/2025",
        ),
        ExpedienteResumen(
            numero="456/2024",
            dependencia="JUZ. CIV. Y COM. FED. 2",
            caratula="OTRO S/ DEMANDA",
            situacion="Archivado",
            ultima_actuacion="10/01/2025",
        ),
        ExpedienteResumen(
            numero="789/2024",
            dependencia="JUZ. CONTENCIOSO ADMINISTRATIVO 1",
            caratula="AMPARO S/ ACCIÓN",
            situacion="Sentenciado",
            ultima_actuacion=None,  # Sin última actuación
        ),
    ]


@pytest.fixture
def temp_dir(tmp_path) -> Path:
    """Genera directorio temporal para tests."""
    return tmp_path


class TestExportarJSON:
    """Tests para la función exportar_json."""

    def test_exportar_json_con_metadata(self, expedientes_muestra, temp_dir):
        """Verifica exportación JSON con metadata."""
        output_path = temp_dir / "expedientes.json"

        exportar_json(expedientes_muestra, output_path, incluir_metadata=True)

        assert output_path.exists()

        # Cargar y verificar estructura
        with output_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        assert "metadata" in data
        assert "expedientes" in data
        assert data["metadata"]["total_expedientes"] == 3
        assert len(data["expedientes"]) == 3

    def test_exportar_json_sin_metadata(self, expedientes_muestra, temp_dir):
        """Verifica exportación JSON sin metadata."""
        output_path = temp_dir / "expedientes_simple.json"

        exportar_json(expedientes_muestra, output_path, incluir_metadata=False)

        assert output_path.exists()

        with output_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Debe ser array directo sin wrapper
        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["numero"] == "123/2024"

    def test_exportar_json_formato_indentado(self, expedientes_muestra, temp_dir):
        """Verifica que el JSON tiene indentación correcta."""
        output_path = temp_dir / "expedientes_indented.json"

        exportar_json(expedientes_muestra, output_path, indent=4)

        content = output_path.read_text(encoding="utf-8")

        # El JSON indentado debe contener saltos de línea
        assert "\n" in content
        assert "    " in content  # 4 espacios de indentación

    def test_exportar_json_caracteres_especiales(self, temp_dir):
        """Verifica que maneja correctamente caracteres especiales."""
        expedientes_especiales = [
            ExpedienteResumen(
                numero="123/2024",
                dependencia="JUZ. CIVIL",
                caratula="PÉREZ S/ ÑANDÚ — CARÁCTER ESPECIAL",
            )
        ]

        output_path = temp_dir / "especiales.json"
        exportar_json(expedientes_especiales, output_path)

        with output_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Verificar que preserva caracteres especiales
        assert "PÉREZ" in data["expedientes"][0]["caratula"]
        assert "ÑANDÚ" in data["expedientes"][0]["caratula"]

    def test_exportar_json_sobrescribe_archivo_existente(self, expedientes_muestra, temp_dir):
        """Verifica que sobrescribe archivos existentes."""
        output_path = temp_dir / "sobrescribir.json"

        # Primera exportación
        exportar_json(expedientes_muestra[:1], output_path)

        # Segunda exportación con más datos
        exportar_json(expedientes_muestra, output_path)

        with output_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        # Debe tener 3 expedientes, no 1
        assert len(data["expedientes"]) == 3


class TestCargarJSON:
    """Tests para la función cargar_json."""

    def test_cargar_json_con_metadata(self, expedientes_muestra, temp_dir):
        """Verifica carga de JSON con metadata."""
        output_path = temp_dir / "test.json"

        # Exportar primero
        exportar_json(expedientes_muestra, output_path, incluir_metadata=True)

        # Cargar
        expedientes, metadata = cargar_json(output_path)

        assert len(expedientes) == 3
        assert metadata["total_expedientes"] == 3
        assert expedientes[0].numero == "123/2024"

    def test_cargar_json_sin_metadata(self, temp_dir):
        """Verifica carga de JSON sin metadata (array directo)."""
        output_path = temp_dir / "simple.json"

        # Crear JSON manual sin metadata
        data = [
            {
                "numero": "100/2024",
                "dependencia": "JUZ. TEST",
                "caratula": "TEST",
            }
        ]

        with output_path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

        # Cargar
        expedientes, metadata = cargar_json(output_path)

        assert len(expedientes) == 1
        assert expedientes[0].numero == "100/2024"
        assert metadata == {}  # Metadata vacía cuando no existe

    def test_cargar_json_archivo_no_existe(self, temp_dir):
        """Verifica error cuando el archivo no existe."""
        non_existent = temp_dir / "no_existe.json"

        with pytest.raises(FileNotFoundError):
            cargar_json(non_existent)

    def test_cargar_json_formato_invalido(self, temp_dir):
        """Verifica error con JSON inválido."""
        invalid_path = temp_dir / "invalid.json"
        invalid_path.write_text("{ invalid json }", encoding="utf-8")

        with pytest.raises(json.JSONDecodeError):
            cargar_json(invalid_path)


class TestExportarCSV:
    """Tests para la función exportar_csv."""

    def test_exportar_csv_con_header(self, expedientes_muestra, temp_dir):
        """Verifica exportación CSV con encabezado."""
        output_path = temp_dir / "expedientes.csv"

        exportar_csv(expedientes_muestra, output_path, incluir_header=True)

        assert output_path.exists()

        lines = output_path.read_text(encoding="utf-8").strip().split("\n")

        # Header + 3 expedientes
        assert len(lines) == 4

        # Verificar header
        header = lines[0]
        assert "numero" in header
        assert "dependencia" in header
        assert "caratula" in header

        # Verificar datos
        assert "123/2024" in lines[1]

    def test_exportar_csv_sin_header(self, expedientes_muestra, temp_dir):
        """Verifica exportación CSV sin encabezado."""
        output_path = temp_dir / "sin_header.csv"

        exportar_csv(expedientes_muestra, output_path, incluir_header=False)

        lines = output_path.read_text(encoding="utf-8").strip().split("\n")

        # Solo 3 expedientes (sin header)
        assert len(lines) == 3
        assert "numero" not in lines[0]  # No debe haber header

    def test_exportar_csv_delimitador_custom(self, expedientes_muestra, temp_dir):
        """Verifica uso de delimitador personalizado."""
        output_path = temp_dir / "custom_delimiter.csv"

        exportar_csv(expedientes_muestra, output_path, delimiter=";")

        content = output_path.read_text(encoding="utf-8")

        # Debe contener puntos y coma como separador
        assert ";" in content
        assert content.count(";") > 0

    def test_exportar_csv_campo_vacio(self, temp_dir):
        """Verifica manejo de campos vacíos/None."""
        expedientes_vacios = [
            ExpedienteResumen(
                numero="123/2024",
                dependencia="JUZ. TEST",
                caratula="TEST",
                situacion=None,
                ultima_actuacion=None,
            )
        ]

        output_path = temp_dir / "vacios.csv"
        exportar_csv(expedientes_vacios, output_path)

        content = output_path.read_text(encoding="utf-8")

        # Campos None deben aparecer como vacíos (,, o al final)
        assert content.count(",,") > 0 or content.endswith(",\n")


class TestCargarCSV:
    """Tests para la función cargar_csv."""

    def test_cargar_csv_con_header(self, expedientes_muestra, temp_dir):
        """Verifica carga de CSV con encabezado."""
        output_path = temp_dir / "test.csv"

        # Exportar primero
        exportar_csv(expedientes_muestra, output_path, incluir_header=True)

        # Cargar
        expedientes = cargar_csv(output_path)

        assert len(expedientes) == 3
        assert expedientes[0].numero == "123/2024"
        assert expedientes[0].dependencia == "JUZ. CIV. Y COM. FED. 1"

    def test_cargar_csv_archivo_no_existe(self, temp_dir):
        """Verifica error cuando el archivo no existe."""
        non_existent = temp_dir / "no_existe.csv"

        with pytest.raises(FileNotFoundError):
            cargar_csv(non_existent)

    def test_cargar_csv_delimitador_custom(self, expedientes_muestra, temp_dir):
        """Verifica carga con delimitador personalizado."""
        output_path = temp_dir / "custom.csv"

        # Exportar con delimitador custom
        exportar_csv(expedientes_muestra, output_path, delimiter=";")

        # Cargar con mismo delimitador
        expedientes = cargar_csv(output_path, delimiter=";")

        assert len(expedientes) == 3
        assert expedientes[0].numero == "123/2024"

    def test_cargar_csv_campos_vacios(self, temp_dir):
        """Verifica manejo de campos vacíos al cargar."""
        output_path = temp_dir / "vacios.csv"

        # Crear CSV manual con campos vacíos
        content = """numero,dependencia,caratula,situacion,ultima_actuacion
123/2024,JUZ. TEST,TEST,,
"""
        output_path.write_text(content, encoding="utf-8")

        expedientes = cargar_csv(output_path)

        assert len(expedientes) == 1
        assert expedientes[0].situacion is None
        assert expedientes[0].ultima_actuacion is None


class TestRoundtrip:
    """Tests de ciclo completo: exportar → cargar."""

    def test_roundtrip_json_con_metadata(self, expedientes_muestra, temp_dir):
        """Verifica que exportar → cargar preserva datos (JSON con metadata)."""
        path = temp_dir / "roundtrip.json"

        # Exportar
        exportar_json(expedientes_muestra, path, incluir_metadata=True)

        # Cargar
        expedientes_cargados, metadata = cargar_json(path)

        # Verificar que los datos son iguales
        assert len(expedientes_cargados) == len(expedientes_muestra)
        for original, cargado in zip(expedientes_muestra, expedientes_cargados):
            assert original.numero == cargado.numero
            assert original.dependencia == cargado.dependencia
            assert original.caratula == cargado.caratula
            assert original.situacion == cargado.situacion
            assert original.ultima_actuacion == cargado.ultima_actuacion

    def test_roundtrip_json_sin_metadata(self, expedientes_muestra, temp_dir):
        """Verifica roundtrip JSON sin metadata."""
        path = temp_dir / "roundtrip_simple.json"

        exportar_json(expedientes_muestra, path, incluir_metadata=False)
        expedientes_cargados, metadata = cargar_json(path)

        assert len(expedientes_cargados) == len(expedientes_muestra)
        assert metadata == {}

    def test_roundtrip_csv(self, expedientes_muestra, temp_dir):
        """Verifica que exportar → cargar preserva datos (CSV)."""
        path = temp_dir / "roundtrip.csv"

        # Exportar
        exportar_csv(expedientes_muestra, path)

        # Cargar
        expedientes_cargados = cargar_csv(path)

        # Verificar
        assert len(expedientes_cargados) == len(expedientes_muestra)
        for original, cargado in zip(expedientes_muestra, expedientes_cargados):
            assert original.numero == cargado.numero
            assert original.dependencia == cargado.dependencia


class TestEdgeCases:
    """Tests de casos extremos."""

    def test_exportar_lista_vacia(self, temp_dir):
        """Verifica manejo de lista vacía de expedientes."""
        path = temp_dir / "vacio.json"

        exportar_json([], path)

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["metadata"]["total_expedientes"] == 0
        assert data["expedientes"] == []

    def test_cargar_json_vacio(self, temp_dir):
        """Verifica carga de archivo JSON con expedientes vacíos."""
        path = temp_dir / "vacio.json"

        data = {"metadata": {"total_expedientes": 0}, "expedientes": []}
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f)

        expedientes, metadata = cargar_json(path)

        assert len(expedientes) == 0
        assert metadata["total_expedientes"] == 0

    def test_csv_con_comas_en_caratula(self, temp_dir):
        """Verifica manejo de comas dentro de campos CSV."""
        expedientes = [
            ExpedienteResumen(
                numero="123/2024",
                dependencia="JUZ. CIVIL",
                caratula="GARCÍA, JUAN S/ PÉREZ, MARÍA",
            )
        ]

        path = temp_dir / "comas.csv"
        exportar_csv(expedientes, path)
        cargados = cargar_csv(path)

        # El CSV debe usar comillas para preservar comas internas
        assert cargados[0].caratula == "GARCÍA, JUAN S/ PÉREZ, MARÍA"
