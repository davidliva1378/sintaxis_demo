"""Tests para el sistema de almacenamiento del monitor.

Este módulo prueba la persistencia de estado, entradas y expedientes.
"""

import json
import pytest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from pjn.models import Entrada, ExpedienteResumen
from pjn.monitor.storage import EstadoMonitor, StorageManager
from pjn.monitor.exceptions import StorageError


class TestEstadoMonitor:
    """Tests para la clase EstadoMonitor."""

    def test_estado_default_values(self):
        """Estado por defecto tiene valores None y 0."""
        estado = EstadoMonitor()

        assert estado.ultima_verificacion_expedientes is None
        assert estado.ultima_verificacion_entradas is None
        assert estado.errores_consecutivos_expedientes == 0
        assert estado.errores_consecutivos_entradas == 0

    def test_estado_custom_values(self):
        """Estado con valores personalizados."""
        estado = EstadoMonitor(
            ultima_verificacion_expedientes="2025-10-17T14:30:00",
            ultima_verificacion_entradas="2025-10-17T14:35:00",
            errores_consecutivos_expedientes=2,
            errores_consecutivos_entradas=1
        )

        assert estado.ultima_verificacion_expedientes == "2025-10-17T14:30:00"
        assert estado.ultima_verificacion_entradas == "2025-10-17T14:35:00"
        assert estado.errores_consecutivos_expedientes == 2
        assert estado.errores_consecutivos_entradas == 1

    def test_estado_to_dict(self):
        """to_dict() convierte a diccionario."""
        estado = EstadoMonitor(
            ultima_verificacion_expedientes="2025-10-17T14:30:00",
            errores_consecutivos_expedientes=3
        )

        data = estado.to_dict()

        assert isinstance(data, dict)
        assert data["ultima_verificacion_expedientes"] == "2025-10-17T14:30:00"
        assert data["errores_consecutivos_expedientes"] == 3
        assert "ultima_verificacion_entradas" in data
        assert "errores_consecutivos_entradas" in data

    def test_estado_from_dict(self):
        """from_dict() crea instancia desde diccionario."""
        data = {
            "ultima_verificacion_expedientes": "2025-10-17T14:30:00",
            "ultima_verificacion_entradas": "2025-10-17T14:35:00",
            "errores_consecutivos_expedientes": 5,
            "errores_consecutivos_entradas": 2
        }

        estado = EstadoMonitor.from_dict(data)

        assert estado.ultima_verificacion_expedientes == "2025-10-17T14:30:00"
        assert estado.ultima_verificacion_entradas == "2025-10-17T14:35:00"
        assert estado.errores_consecutivos_expedientes == 5
        assert estado.errores_consecutivos_entradas == 2

    def test_estado_from_dict_partial(self):
        """from_dict() con datos parciales usa defaults."""
        data = {
            "ultima_verificacion_expedientes": "2025-10-17T14:30:00",
        }

        estado = EstadoMonitor.from_dict(data)

        assert estado.ultima_verificacion_expedientes == "2025-10-17T14:30:00"
        assert estado.ultima_verificacion_entradas is None  # default
        assert estado.errores_consecutivos_expedientes == 0  # default


class TestStorageManager:
    """Tests para la clase StorageManager."""

    @pytest.fixture
    def temp_storage(self):
        """Fixture que proporciona un StorageManager temporal."""
        with TemporaryDirectory() as tmpdir:
            storage = StorageManager(tmpdir)
            yield storage

    @pytest.fixture
    def entradas_ejemplo(self):
        """Fixture con entradas de ejemplo."""
        return [
            Entrada(
                numero="EXP-001",
                caratula="Caso A",
                fecha="01/10/2025",
                evento="Notificación A",
                tipo_evento="N",
                leida=False
            ),
            Entrada(
                numero="EXP-002",
                caratula="Caso B",
                fecha="02/10/2025",
                evento="Notificación B",
                tipo_evento="N",
                leida=True
            ),
        ]

    @pytest.fixture
    def expedientes_ejemplo(self):
        """Fixture con expedientes de ejemplo."""
        return [
            ExpedienteResumen(
                numero="EXP-001/2025",
                caratula="Caso A",
                dependencia="Secretaría 1",
                situacion="En trámite",
                ultima_actuacion="10/10/2025"
            ),
            ExpedienteResumen(
                numero="EXP-002/2025",
                caratula="Caso B",
                dependencia="Secretaría 2",
                situacion="En trámite",
                ultima_actuacion="15/10/2025"
            ),
        ]

    # =========================================================================
    # Tests de inicialización
    # =========================================================================

    def test_storage_init_creates_directory(self):
        """StorageManager crea el directorio si no existe."""
        with TemporaryDirectory() as tmpdir:
            storage_dir = Path(tmpdir) / "nested" / "storage"

            # No existe inicialmente
            assert not storage_dir.exists()

            StorageManager(storage_dir)

            # Ahora existe
            assert storage_dir.exists()
            assert storage_dir.is_dir()

    def test_storage_init_paths(self, temp_storage):
        """StorageManager configura paths correctos."""
        assert temp_storage.archivo_estado.name == "estado_monitor.json"
        assert temp_storage.archivo_entradas.name == "historial_entradas.json"
        assert temp_storage.archivo_expedientes.name == "historial_expedientes.json"

    # =========================================================================
    # Tests de estado
    # =========================================================================

    def test_cargar_estado_sin_archivo_retorna_nuevo(self, temp_storage):
        """cargar_estado() retorna estado vacío si archivo no existe."""
        estado = temp_storage.cargar_estado()

        assert isinstance(estado, EstadoMonitor)
        assert estado.ultima_verificacion_expedientes is None
        assert estado.errores_consecutivos_expedientes == 0

    def test_guardar_y_cargar_estado(self, temp_storage):
        """Guardar y cargar estado funciona correctamente."""
        estado_original = EstadoMonitor(
            ultima_verificacion_expedientes="2025-10-17T14:30:00",
            errores_consecutivos_expedientes=3
        )

        # Guardar
        temp_storage.guardar_estado(estado_original)

        # Cargar
        estado_cargado = temp_storage.cargar_estado()

        assert estado_cargado.ultima_verificacion_expedientes == "2025-10-17T14:30:00"
        assert estado_cargado.errores_consecutivos_expedientes == 3

    def test_cargar_estado_json_corrupto_lanza_error(self, temp_storage):
        """cargar_estado() lanza StorageError si JSON inválido."""
        # Escribir JSON inválido
        temp_storage.archivo_estado.write_text("{ invalid json }")

        with pytest.raises(StorageError, match="corrupto"):
            temp_storage.cargar_estado()

    # =========================================================================
    # Tests de entradas
    # =========================================================================

    def test_cargar_entradas_sin_archivo_retorna_vacio(self, temp_storage):
        """cargar_entradas_conocidas() retorna [] si archivo no existe."""
        entradas = temp_storage.cargar_entradas_conocidas()

        assert entradas == []

    def test_guardar_y_cargar_entradas(self, temp_storage, entradas_ejemplo):
        """Guardar y cargar entradas funciona correctamente."""
        # Guardar
        temp_storage.guardar_entradas(entradas_ejemplo)

        # Cargar
        entradas_cargadas = temp_storage.cargar_entradas_conocidas()

        assert len(entradas_cargadas) == 2
        assert entradas_cargadas[0].numero == "EXP-001"
        assert entradas_cargadas[0].evento == "Notificación A"
        assert entradas_cargadas[1].numero == "EXP-002"
        assert entradas_cargadas[1].leida is True

    def test_guardar_entradas_vacias(self, temp_storage):
        """Guardar lista vacía de entradas funciona."""
        temp_storage.guardar_entradas([])

        # Archivo creado
        assert temp_storage.archivo_entradas.exists()

        # Contenido es lista vacía
        with temp_storage.archivo_entradas.open() as f:
            data = json.load(f)
        assert data == []

    def test_cargar_entradas_json_corrupto_lanza_error(self, temp_storage):
        """cargar_entradas_conocidas() lanza StorageError si JSON inválido."""
        temp_storage.archivo_entradas.write_text("{ bad json }")

        with pytest.raises(StorageError, match="corrupto"):
            temp_storage.cargar_entradas_conocidas()

    def test_cargar_entradas_formato_invalido_retorna_vacio(self, temp_storage):
        """cargar_entradas_conocidas() retorna [] si formato no es lista."""
        # JSON válido pero no es lista
        temp_storage.archivo_entradas.write_text('{"key": "value"}')

        entradas = temp_storage.cargar_entradas_conocidas()

        # Retorna lista vacía en lugar de fallar
        assert entradas == []

    def test_cargar_entradas_ignora_items_no_dict(self, temp_storage):
        """cargar_entradas_conocidas() ignora items que no son diccionarios."""
        # Lista con mix de tipos
        data = [
            {
                "numero": "EXP-001",
                "fecha": "2025-10-01T00:00:00",
                "evento": "Evento",
                "tipo": "N",
                "link": "https://example.com/1",
                "leida": False
            },
            "not a dict",  # Esto se ignora
            123,  # Esto también
        ]
        temp_storage.archivo_entradas.write_text(json.dumps(data))

        entradas = temp_storage.cargar_entradas_conocidas()

        # Solo carga el diccionario válido
        assert len(entradas) == 1
        assert entradas[0].numero == "EXP-001"

    # =========================================================================
    # Tests de expedientes
    # =========================================================================

    def test_cargar_expedientes_sin_archivo_retorna_vacio(self, temp_storage):
        """cargar_expedientes_conocidos() retorna [] si archivo no existe."""
        expedientes = temp_storage.cargar_expedientes_conocidos()

        assert expedientes == []

    def test_guardar_y_cargar_expedientes(self, temp_storage, expedientes_ejemplo):
        """Guardar y cargar expedientes funciona correctamente."""
        # Guardar
        temp_storage.guardar_expedientes(expedientes_ejemplo)

        # Cargar
        expedientes_cargados = temp_storage.cargar_expedientes_conocidos()

        assert len(expedientes_cargados) == 2
        assert expedientes_cargados[0].numero == "EXP-001/2025"
        assert expedientes_cargados[0].caratula == "Caso A"
        assert expedientes_cargados[1].numero == "EXP-002/2025"
        assert expedientes_cargados[1].ultima_actuacion == "15/10/2025"

    def test_guardar_expedientes_vacios(self, temp_storage):
        """Guardar lista vacía de expedientes funciona."""
        temp_storage.guardar_expedientes([])

        assert temp_storage.archivo_expedientes.exists()

        with temp_storage.archivo_expedientes.open() as f:
            data = json.load(f)
        assert data == []

    def test_cargar_expedientes_json_corrupto_lanza_error(self, temp_storage):
        """cargar_expedientes_conocidos() lanza StorageError si JSON inválido."""
        temp_storage.archivo_expedientes.write_text("invalid json")

        with pytest.raises(StorageError, match="corrupto"):
            temp_storage.cargar_expedientes_conocidos()

    def test_cargar_expedientes_formato_invalido_retorna_vacio(self, temp_storage):
        """cargar_expedientes_conocidos() retorna [] si formato no es lista."""
        temp_storage.archivo_expedientes.write_text('{"not": "a list"}')

        expedientes = temp_storage.cargar_expedientes_conocidos()

        assert expedientes == []

    # =========================================================================
    # Tests de edge cases y errores
    # =========================================================================

    def test_storage_con_path_string(self):
        """StorageManager acepta string como path."""
        with TemporaryDirectory() as tmpdir:
            storage = StorageManager(tmpdir)  # String, no Path

            assert storage.directorio.is_dir()

    def test_guardar_entradas_preserve_encoding(self, temp_storage):
        """Guardar entradas preserva caracteres especiales (UTF-8)."""
        entrada_especial = Entrada(
            numero="EXP-ñ001",
            caratula="Caso con ñ",
            fecha="01/10/2025",
            evento="Notificación con ñ, á, é, í, ó, ú",
            tipo_evento="N",
            leida=False
        )

        temp_storage.guardar_entradas([entrada_especial])
        entradas_cargadas = temp_storage.cargar_entradas_conocidas()

        assert entradas_cargadas[0].numero == "EXP-ñ001"
        assert "ñ" in entradas_cargadas[0].evento
        assert "á" in entradas_cargadas[0].evento

    def test_multiples_guardados_sobrescriben(self, temp_storage, entradas_ejemplo):
        """Guardar múltiples veces sobrescribe el archivo."""
        # Primer guardado
        temp_storage.guardar_entradas(entradas_ejemplo)

        # Segundo guardado con diferentes datos
        nueva_entrada = Entrada(
            numero="EXP-999",
            caratula="Caso Nuevo",
            fecha="10/10/2025",
            evento="Nueva",
            tipo_evento="N",
            leida=False
        )
        temp_storage.guardar_entradas([nueva_entrada])

        # Solo debe tener la última versión
        entradas_cargadas = temp_storage.cargar_entradas_conocidas()
        assert len(entradas_cargadas) == 1
        assert entradas_cargadas[0].numero == "EXP-999"

    def test_storage_archivos_independientes(self, temp_storage, entradas_ejemplo, expedientes_ejemplo):
        """Estado, entradas y expedientes se guardan en archivos separados."""
        estado = EstadoMonitor(errores_consecutivos_entradas=5)

        temp_storage.guardar_estado(estado)
        temp_storage.guardar_entradas(entradas_ejemplo)
        temp_storage.guardar_expedientes(expedientes_ejemplo)

        # Todos los archivos existen
        assert temp_storage.archivo_estado.exists()
        assert temp_storage.archivo_entradas.exists()
        assert temp_storage.archivo_expedientes.exists()

        # Cargar cada uno funciona independientemente
        estado_cargado = temp_storage.cargar_estado()
        entradas_cargadas = temp_storage.cargar_entradas_conocidas()
        expedientes_cargados = temp_storage.cargar_expedientes_conocidos()

        assert estado_cargado.errores_consecutivos_entradas == 5
        assert len(entradas_cargadas) == 2
        assert len(expedientes_cargados) == 2
