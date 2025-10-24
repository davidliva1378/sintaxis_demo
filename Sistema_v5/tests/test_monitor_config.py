"""Tests para la configuración del monitor.

Este módulo prueba la carga, guardado y validación de configuración.
"""

import json
import os
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory

from configuracion.monitor import MonitorConfig


class TestMonitorConfig:
    """Tests para la clase MonitorConfig."""

    # =========================================================================
    # Tests de creación e inicialización
    # =========================================================================

    def test_config_default_values(self):
        """Configuración por defecto tiene valores esperados."""
        config = MonitorConfig()

        assert config.modo == "automatico"
        assert config.headless is True
        assert config.directorio_datos == "data/monitor"
        assert config.intervalos_laboral_expedientes == 15
        assert config.intervalos_laboral_entradas == 10
        assert config.intervalos_no_laboral_expedientes == 60
        assert config.intervalos_no_laboral_entradas == 30
        assert config.dias_laborales == ["lunes", "martes", "miercoles", "jueves", "viernes"]
        assert config.hora_inicio == "08:00"
        assert config.hora_fin == "18:00"
        assert config.max_reintentos_expedientes == 3
        assert config.max_reintentos_entradas == 3
        assert config.notificar_nuevas_entradas is True
        assert config.notificar_cambios_expedientes is True
        assert config.verificar_entradas is True
        assert config.verificar_expedientes is True

    def test_config_custom_values(self):
        """Crear configuración con valores personalizados."""
        config = MonitorConfig(
            modo="laboral",
            headless=False,
            intervalos_laboral_expedientes=20,
            notificar_errores=False
        )

        assert config.modo == "laboral"
        assert config.headless is False
        assert config.intervalos_laboral_expedientes == 20
        assert config.notificar_errores is False

    def test_config_to_dict(self):
        """Convertir config a diccionario."""
        config = MonitorConfig(
            modo="no_laboral",
            headless=True,
            intervalos_laboral_expedientes=25
        )

        data = config.to_dict()

        assert isinstance(data, dict)
        assert data["modo"] == "no_laboral"
        assert data["headless"] is True
        assert data["intervalos_laboral_expedientes"] == 25
        assert "dias_laborales" in data

    # =========================================================================
    # Tests de carga/guardado de archivos
    # =========================================================================

    def test_to_file_creates_json(self):
        """to_file() crea archivo JSON válido."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "test_config.json"
            config = MonitorConfig(
                modo="laboral",
                intervalos_laboral_expedientes=30
            )

            config.to_file(config_path)

            assert config_path.exists()

            # Verificar que es JSON válido
            with config_path.open("r") as f:
                data = json.load(f)
            assert data["modo"] == "laboral"
            assert data["intervalos_laboral_expedientes"] == 30

    def test_to_file_creates_parent_directory(self):
        """to_file() crea el directorio padre si no existe."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "subdir" / "nested" / "config.json"
            config = MonitorConfig()

            config.to_file(config_path)

            assert config_path.exists()
            assert config_path.parent.exists()

    def test_from_file_loads_config(self):
        """from_file() carga configuración correctamente."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.json"

            # Crear archivo de configuración
            data = {
                "modo": "no_laboral",
                "headless": False,
                "intervalos_laboral_expedientes": 45,
                "notificar_nuevas_entradas": False,
                "dias_laborales": ["lunes", "miercoles"],
            }
            with config_path.open("w") as f:
                json.dump(data, f)

            # Cargar
            config = MonitorConfig.from_file(config_path)

            assert config.modo == "no_laboral"
            assert config.headless is False
            assert config.intervalos_laboral_expedientes == 45
            assert config.notificar_nuevas_entradas is False
            assert config.dias_laborales == ["lunes", "miercoles"]

    def test_from_file_creates_default_if_not_exists(self):
        """from_file() crea config por defecto si archivo no existe."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "nonexistent.json"

            # No existe inicialmente
            assert not config_path.exists()

            # Cargar (debería crear uno por defecto)
            config = MonitorConfig.from_file(config_path)

            # Archivo creado
            assert config_path.exists()

            # Valores por defecto
            assert config.modo == "automatico"
            assert config.headless is True

    def test_from_file_partial_config(self):
        """from_file() con config parcial usa defaults para campos faltantes."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "partial.json"

            # Solo algunos campos
            data = {
                "modo": "laboral",
                "intervalos_laboral_expedientes": 20,
            }
            with config_path.open("w") as f:
                json.dump(data, f)

            config = MonitorConfig.from_file(config_path)

            # Campos especificados
            assert config.modo == "laboral"
            assert config.intervalos_laboral_expedientes == 20

            # Campos por defecto
            assert config.headless is True  # default
            assert config.hora_inicio == "08:00"  # default

    def test_from_file_detects_project_root_with_relative_path(self, tmp_path, monkeypatch):
        """from_file() busca la configuración relativa en la raíz del proyecto."""
        project_root = Path(__file__).resolve().parents[2]
        project_config = project_root / "config" / "monitor.json"
        assert project_config.exists(), "La plantilla de monitor debe existir en la raíz del proyecto"

        monkeypatch.chdir(tmp_path)

        config = MonitorConfig.from_file("config/monitor.json")

        assert config.modo == "automatico"

        tmp_config = tmp_path / "config" / "monitor.json"
        assert not tmp_config.exists()

        internal_config = Path(__file__).resolve().parents[1] / "config" / "monitor.json"
        assert not internal_config.exists()

    # =========================================================================
    # Tests de carga desde variables de entorno
    # =========================================================================

    def test_from_env_default_if_no_env_vars(self):
        """from_env() retorna defaults si no hay variables de entorno."""
        # Limpiar variables de entorno relevantes
        env_vars = [
            "MONITOR_MODO", "MONITOR_HEADLESS",
            "MONITOR_INTERVALO_LAB_EXP", "MONITOR_INTERVALO_LAB_ENT",
            "MONITOR_NOTIF_ENTRADAS", "MONITOR_NOTIF_EXPEDIENTES"
        ]
        for var in env_vars:
            os.environ.pop(var, None)

        config = MonitorConfig.from_env()

        assert config.modo == "automatico"
        assert config.headless is True
        assert config.intervalos_laboral_expedientes == 15

    def test_from_env_modo(self):
        """from_env() lee MONITOR_MODO."""
        os.environ["MONITOR_MODO"] = "laboral"

        try:
            config = MonitorConfig.from_env()
            assert config.modo == "laboral"
        finally:
            os.environ.pop("MONITOR_MODO", None)

    def test_from_env_headless_true_variations(self):
        """from_env() reconoce variaciones de 'true' para headless."""
        test_cases = ["1", "true", "TRUE", "yes", "YES", "y", "Y"]

        for value in test_cases:
            os.environ["MONITOR_HEADLESS"] = value
            try:
                config = MonitorConfig.from_env()
                assert config.headless is True, f"Failed for value: {value}"
            finally:
                os.environ.pop("MONITOR_HEADLESS", None)

    def test_from_env_headless_false(self):
        """from_env() reconoce valores falsy para headless."""
        os.environ["MONITOR_HEADLESS"] = "0"

        try:
            config = MonitorConfig.from_env()
            assert config.headless is False
        finally:
            os.environ.pop("MONITOR_HEADLESS", None)

    def test_from_env_intervalos(self):
        """from_env() lee intervalos de env vars."""
        os.environ["MONITOR_INTERVALO_LAB_EXP"] = "25"
        os.environ["MONITOR_INTERVALO_LAB_ENT"] = "12"

        try:
            config = MonitorConfig.from_env()
            assert config.intervalos_laboral_expedientes == 25
            assert config.intervalos_laboral_entradas == 12
        finally:
            os.environ.pop("MONITOR_INTERVALO_LAB_EXP", None)
            os.environ.pop("MONITOR_INTERVALO_LAB_ENT", None)

    def test_from_env_notificaciones(self):
        """from_env() lee configuración de notificaciones."""
        os.environ["MONITOR_NOTIF_ENTRADAS"] = "false"
        os.environ["MONITOR_NOTIF_EXPEDIENTES"] = "1"

        try:
            config = MonitorConfig.from_env()
            assert config.notificar_nuevas_entradas is False
            assert config.notificar_cambios_expedientes is True
        finally:
            os.environ.pop("MONITOR_NOTIF_ENTRADAS", None)
            os.environ.pop("MONITOR_NOTIF_EXPEDIENTES", None)

    def test_from_env_invalid_modo_ignored(self):
        """from_env() ignora valores inválidos de MONITOR_MODO."""
        os.environ["MONITOR_MODO"] = "invalid_mode"

        try:
            config = MonitorConfig.from_env()
            # Debe usar default porque 'invalid_mode' no es válido
            assert config.modo == "automatico"
        finally:
            os.environ.pop("MONITOR_MODO", None)

    # =========================================================================
    # Tests de edge cases
    # =========================================================================

    def test_config_with_none_dates(self):
        """Config acepta None para fechas opcionales."""
        config = MonitorConfig(
            fecha_corte_expedientes=None,
            fecha_desde_entradas=None,
            fecha_hasta_entradas=None
        )

        assert config.fecha_corte_expedientes is None
        assert config.fecha_desde_entradas is None
        assert config.fecha_hasta_entradas is None

    def test_config_with_date_strings(self):
        """Config acepta strings de fechas."""
        config = MonitorConfig(
            fecha_corte_expedientes="2025-01-01",
            fecha_desde_entradas="01/01/2025",
            fecha_hasta_entradas="31/01/2025"
        )

        assert config.fecha_corte_expedientes == "2025-01-01"
        assert config.fecha_desde_entradas == "01/01/2025"
        assert config.fecha_hasta_entradas == "31/01/2025"

    def test_config_to_file_and_load_roundtrip(self):
        """Guardar y cargar config produce el mismo resultado."""
        with TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "roundtrip.json"

            # Configuración original
            original = MonitorConfig(
                modo="no_laboral",
                headless=False,
                intervalos_laboral_expedientes=40,
                dias_laborales=["lunes", "viernes"],
                fecha_desde_entradas="01/01/2025"
            )

            # Guardar
            original.to_file(config_path)

            # Cargar
            loaded = MonitorConfig.from_file(config_path)

            # Verificar igualdad
            assert loaded.modo == original.modo
            assert loaded.headless == original.headless
            assert loaded.intervalos_laboral_expedientes == original.intervalos_laboral_expedientes
            assert loaded.dias_laborales == original.dias_laborales
            assert loaded.fecha_desde_entradas == original.fecha_desde_entradas

    def test_config_verificaciones_flags(self):
        """Config permite deshabilitar verificaciones."""
        config = MonitorConfig(
            verificar_entradas=False,
            verificar_expedientes=False
        )

        assert config.verificar_entradas is False
        assert config.verificar_expedientes is False

    def test_config_comparacion_automatica(self):
        """Config soporta flag de comparación automática."""
        config = MonitorConfig(comparacion_automatica=True)
        assert config.comparacion_automatica is True

        config_default = MonitorConfig()
        assert config_default.comparacion_automatica is False
