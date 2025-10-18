"""Tests de integración entre SystemConfig y el monitor.

Este módulo verifica que:
1. MonitorPJN acepta tanto SystemConfig como MonitorConfig
2. La conversión entre configs preserva todos los valores
3. Los scripts de ejecución funcionan con ambos tipos
4. No hay regresiones en la funcionalidad existente
"""

import pytest
from pathlib import Path
import json

from pjn import SystemConfig
from pjn.monitor.config import MonitorConfig
from pjn.monitor.core import MonitorPJN


class TestSystemConfigToMonitorConfig:
    """Tests de conversión entre SystemConfig y MonitorConfig."""

    def test_from_system_config_preserva_todos_los_valores(self):
        """Verifica que la conversión preserva todos los valores."""
        # Crear SystemConfig con valores personalizados
        system_config = SystemConfig(
            # Monitoreo
            modo_monitor="laboral",
            intervalos_laboral_expedientes=20,
            intervalos_laboral_entradas=15,
            intervalos_no_laboral_expedientes=90,
            intervalos_no_laboral_entradas=45,
            dias_laborales=["lunes", "miercoles", "viernes"],
            hora_inicio="09:00",
            hora_fin="17:00",
            verificar_entradas=False,
            verificar_expedientes=True,
            notificar_nuevas_entradas=False,
            notificar_cambios_expedientes=True,
            notificar_errores=False,

            # Extracción
            headless=False,
            max_reintentos_expedientes=5,
            espera_reintentos_expedientes=45,
            max_reintentos_entradas=4,
            espera_reintentos_entradas=35,

            # Directorios
            directorio_monitor_datos="test_data/monitor",

            # Fechas
            fecha_desde_entradas="2025-01-01",
            fecha_hasta_entradas="2025-12-31",
            fecha_desde_expedientes="2024-06-01",
            fecha_hasta_expedientes="2025-12-31",
            fecha_corte_expedientes="2024-01-01",
        )

        # Convertir a MonitorConfig
        monitor_config = MonitorConfig.from_system_config(system_config)

        # Verificar valores de monitoreo
        assert monitor_config.modo == "laboral"
        assert monitor_config.intervalos_laboral_expedientes == 20
        assert monitor_config.intervalos_laboral_entradas == 15
        assert monitor_config.intervalos_no_laboral_expedientes == 90
        assert monitor_config.intervalos_no_laboral_entradas == 45
        assert monitor_config.dias_laborales == ["lunes", "miercoles", "viernes"]
        assert monitor_config.hora_inicio == "09:00"
        assert monitor_config.hora_fin == "17:00"
        assert monitor_config.verificar_entradas is False
        assert monitor_config.verificar_expedientes is True
        assert monitor_config.notificar_nuevas_entradas is False
        assert monitor_config.notificar_cambios_expedientes is True
        assert monitor_config.notificar_errores is False

        # Verificar valores de extracción
        assert monitor_config.headless is False
        assert monitor_config.max_reintentos_expedientes == 5
        assert monitor_config.espera_reintentos_expedientes == 45
        assert monitor_config.max_reintentos_entradas == 4
        assert monitor_config.espera_reintentos_entradas == 35

        # Verificar directorios
        assert monitor_config.directorio_datos == "test_data/monitor"

        # Verificar fechas
        assert monitor_config.fecha_desde_entradas == "2025-01-01"
        assert monitor_config.fecha_hasta_entradas == "2025-12-31"
        assert monitor_config.fecha_desde_expedientes == "2024-06-01"
        assert monitor_config.fecha_hasta_expedientes == "2025-12-31"
        assert monitor_config.fecha_corte_expedientes == "2024-01-01"

    def test_from_system_config_con_valores_default(self):
        """Verifica conversión con valores por defecto."""
        system_config = SystemConfig()
        monitor_config = MonitorConfig.from_system_config(system_config)

        # Verificar algunos defaults
        assert monitor_config.modo == "automatico"
        assert monitor_config.intervalos_laboral_expedientes == 15
        assert monitor_config.intervalos_laboral_entradas == 10
        assert monitor_config.headless is True
        assert monitor_config.verificar_entradas is True
        assert monitor_config.verificar_expedientes is True


class TestMonitorPJNWithSystemConfig:
    """Tests de MonitorPJN con SystemConfig."""

    def test_monitor_acepta_system_config(self, tmp_path):
        """Verifica que MonitorPJN acepta SystemConfig."""
        config = SystemConfig(
            directorio_monitor_datos=str(tmp_path / "monitor")
        )

        # No debe lanzar excepción
        monitor = MonitorPJN(config)

        # Verificar que se creó correctamente
        assert monitor is not None
        assert monitor.config is not None
        # MonitorPJN convierte internamente a MonitorConfig
        assert isinstance(monitor.config, MonitorConfig)

    def test_monitor_acepta_monitor_config(self, tmp_path):
        """Verifica que MonitorPJN aún acepta MonitorConfig (legacy)."""
        config = MonitorConfig(
            directorio_datos=str(tmp_path / "monitor")
        )

        # No debe lanzar excepción
        monitor = MonitorPJN(config)

        # Verificar que se creó correctamente
        assert monitor is not None
        assert monitor.config is not None
        assert isinstance(monitor.config, MonitorConfig)

    def test_monitor_convierte_system_config_internamente(self, tmp_path):
        """Verifica que MonitorPJN convierte SystemConfig internamente."""
        system_config = SystemConfig(
            directorio_monitor_datos=str(tmp_path / "monitor"),
            modo_monitor="laboral",
            intervalos_laboral_expedientes=30,
            headless=False,
        )

        monitor = MonitorPJN(system_config)

        # Verificar que internamente usa MonitorConfig
        assert isinstance(monitor.config, MonitorConfig)
        assert monitor.config.modo == "laboral"
        assert monitor.config.intervalos_laboral_expedientes == 30
        assert monitor.config.headless is False


class TestConfigFilesCompatibility:
    """Tests de compatibilidad con archivos de configuración."""

    def test_monitor_carga_desde_sistema_json(self, tmp_path):
        """Verifica que se puede cargar sistema.json y crear monitor."""
        # Crear archivo sistema.json
        sistema_path = tmp_path / "sistema.json"
        config = SystemConfig(
            directorio_monitor_datos=str(tmp_path / "monitor"),
            modo_monitor="laboral",
        )
        config.to_file(sistema_path)

        # Cargar y crear monitor
        loaded_config = SystemConfig.from_file(sistema_path)
        monitor = MonitorPJN(loaded_config)

        assert monitor is not None
        assert monitor.config.modo == "laboral"

    def test_monitor_carga_desde_monitor_json(self, tmp_path):
        """Verifica que se puede cargar monitor.json (legacy)."""
        # Crear archivo monitor.json
        monitor_path = tmp_path / "monitor.json"
        config = MonitorConfig(
            directorio_datos=str(tmp_path / "monitor"),
            modo="laboral",
        )
        config.to_file(monitor_path)

        # Cargar y crear monitor
        loaded_config = MonitorConfig.from_file(monitor_path)
        monitor = MonitorPJN(loaded_config)

        assert monitor is not None
        assert monitor.config.modo == "laboral"

    def test_migracion_de_monitor_a_sistema(self, tmp_path):
        """Verifica que la migración de monitor.json a sistema.json funciona."""
        # Crear monitor.json con valores personalizados
        monitor_path = tmp_path / "monitor.json"
        monitor_data = {
            "modo": "laboral",
            "headless": False,
            "directorio_datos": str(tmp_path / "monitor"),
            "intervalos_laboral_expedientes": 25,
            "intervalos_laboral_entradas": 20,
            "verificar_entradas": False,
            "verificar_expedientes": True,
            "notificar_nuevas_entradas": True,
            "notificar_cambios_expedientes": False,
        }

        with monitor_path.open("w", encoding="utf-8") as f:
            json.dump(monitor_data, f, indent=2)

        # Migrar a SystemConfig
        system_config = SystemConfig.from_monitor_config(monitor_path)

        # Verificar valores migrados
        assert system_config.modo_monitor == "laboral"
        assert system_config.headless is False
        assert system_config.directorio_monitor_datos == str(tmp_path / "monitor")
        assert system_config.intervalos_laboral_expedientes == 25
        assert system_config.intervalos_laboral_entradas == 20
        assert system_config.verificar_entradas is False
        assert system_config.verificar_expedientes is True
        assert system_config.notificar_nuevas_entradas is True
        assert system_config.notificar_cambios_expedientes is False

        # Guardar como sistema.json
        sistema_path = tmp_path / "sistema.json"
        system_config.to_file(sistema_path)

        # Cargar sistema.json y crear monitor
        loaded_config = SystemConfig.from_file(sistema_path)
        monitor = MonitorPJN(loaded_config)

        # Verificar que el monitor funciona correctamente
        assert monitor is not None
        assert monitor.config.modo == "laboral"
        assert monitor.config.headless is False


class TestBackwardCompatibility:
    """Tests de retrocompatibilidad."""

    def test_codigo_legacy_con_monitor_config_sigue_funcionando(self, tmp_path):
        """Verifica que código antiguo que usa MonitorConfig aún funciona."""
        # Simular código legacy
        config = MonitorConfig.from_file("config/monitor.json")  # Puede fallar si no existe
        # Pero si creamos uno temporal, debe funcionar
        temp_config = MonitorConfig(
            directorio_datos=str(tmp_path / "monitor")
        )
        temp_config.to_file(tmp_path / "monitor.json")

        # Cargar y usar
        loaded = MonitorConfig.from_file(tmp_path / "monitor.json")
        monitor = MonitorPJN(loaded)

        assert monitor is not None

    def test_nuevo_codigo_con_system_config_funciona(self, tmp_path):
        """Verifica que nuevo código con SystemConfig funciona."""
        config = SystemConfig(
            directorio_monitor_datos=str(tmp_path / "monitor")
        )
        config.to_file(tmp_path / "sistema.json")

        # Cargar y usar
        loaded = SystemConfig.from_file(tmp_path / "sistema.json")
        monitor = MonitorPJN(loaded)

        assert monitor is not None

    def test_mezcla_de_configs_no_causa_problemas(self, tmp_path):
        """Verifica que tener ambos tipos de config no causa problemas."""
        # Crear ambos archivos
        monitor_config = MonitorConfig(
            directorio_datos=str(tmp_path / "monitor_legacy")
        )
        monitor_config.to_file(tmp_path / "monitor.json")

        system_config = SystemConfig(
            directorio_monitor_datos=str(tmp_path / "monitor_nuevo")
        )
        system_config.to_file(tmp_path / "sistema.json")

        # Cargar cada uno por separado y verificar que funcionan
        loaded_monitor = MonitorConfig.from_file(tmp_path / "monitor.json")
        monitor1 = MonitorPJN(loaded_monitor)
        assert monitor1.config.directorio_datos == str(tmp_path / "monitor_legacy")

        loaded_system = SystemConfig.from_file(tmp_path / "sistema.json")
        monitor2 = MonitorPJN(loaded_system)
        assert monitor2.config.directorio_datos == str(tmp_path / "monitor_nuevo")


class TestEdgeCases:
    """Tests de casos extremos."""

    def test_system_config_con_todos_los_campos_opcionales_none(self, tmp_path):
        """Verifica conversión cuando campos opcionales son None."""
        config = SystemConfig(
            directorio_monitor_datos=str(tmp_path / "monitor"),
            fecha_desde_entradas=None,
            fecha_hasta_entradas=None,
            fecha_desde_expedientes=None,
            fecha_hasta_expedientes=None,
            fecha_corte_expedientes=None,
        )

        monitor_config = MonitorConfig.from_system_config(config)
        monitor = MonitorPJN(monitor_config)

        assert monitor is not None
        assert monitor.config.fecha_desde_entradas is None
        assert monitor.config.fecha_hasta_entradas is None

    def test_system_config_con_valores_extremos(self, tmp_path):
        """Verifica manejo de valores extremos."""
        config = SystemConfig(
            directorio_monitor_datos=str(tmp_path / "monitor"),
            intervalos_laboral_expedientes=1,  # Mínimo
            intervalos_no_laboral_expedientes=1440,  # Máximo (24h)
            max_reintentos_expedientes=10,
            espera_reintentos_expedientes=1,
        )

        monitor_config = MonitorConfig.from_system_config(config)
        monitor = MonitorPJN(monitor_config)

        assert monitor is not None
        assert monitor.config.intervalos_laboral_expedientes == 1
        assert monitor.config.intervalos_no_laboral_expedientes == 1440
