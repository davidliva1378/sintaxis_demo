"""Tests para la configuración unificada del sistema.

Este módulo prueba SystemConfig con todas sus opciones de directorios,
monitoreo, extracción y sistema.
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from configuracion.core import SystemConfig, ModoMonitor, ModoComparacion, FormatoReporte, NivelLog
from configuracion.monitor.exceptions import (
    ValidationError,
    IntervalError,
    DateRangeError,
    WorkHoursError,
)


class TestSystemConfigDefaults:
    """Tests para valores por defecto de SystemConfig."""

    def test_config_default_values(self):
        """Configuración se crea con valores por defecto correctos."""
        config = SystemConfig()

        # Directorios
        assert config.directorio_extraccion_inicial == "data/inicial"
        assert config.directorio_expedientes_base == "data/expedientes"
        assert config.directorio_monitor_datos == "data/monitor"
        assert config.directorio_logs == "logs"
        assert config.directorio_cache == ".cache"

        # Monitoreo
        assert config.modo_monitor == "automatico"
        assert config.intervalos_laboral_expedientes == 15
        assert config.intervalos_laboral_entradas == 10
        assert config.hora_inicio == "08:00"
        assert config.hora_fin == "18:00"
        assert config.dias_laborales == ["lunes", "martes", "miercoles", "jueves", "viernes"]

        # Extracción
        assert config.headless is True
        assert config.max_paginas_expedientes == 200
        assert config.timeout_default == 8_000
        assert config.max_reintentos_descarga == 3

        # Sistema
        assert config.nivel_log == "INFO"
        assert config.rotacion_logs is True
        assert config.max_tamaño_log_mb == 50

    def test_config_fecha_inicio_auto_generada(self):
        """fecha_inicio_sistema se genera automáticamente."""
        config = SystemConfig()

        assert config.fecha_inicio_sistema is not None
        # Debe ser fecha válida en formato YYYY-MM-DD
        datetime.strptime(config.fecha_inicio_sistema, "%Y-%m-%d")


class TestSystemConfigCustom:
    """Tests para configuración personalizada."""

    def test_config_custom_directorios(self):
        """Directorios personalizados se asignan correctamente."""
        config = SystemConfig(
            directorio_extraccion_inicial="mi_data/inicial",
            directorio_expedientes_base="mi_data/exp",
            directorio_logs="mis_logs"
        )

        assert config.directorio_extraccion_inicial == "mi_data/inicial"
        assert config.directorio_expedientes_base == "mi_data/exp"
        assert config.directorio_logs == "mis_logs"

    def test_config_custom_monitoreo(self):
        """Configuración de monitoreo personalizada."""
        config = SystemConfig(
            modo_monitor="laboral",
            intervalos_laboral_expedientes=30,
            hora_inicio="09:00",
            hora_fin="17:00",
            dias_laborales=["lunes", "miercoles", "viernes"]
        )

        assert config.modo_monitor == "laboral"
        assert config.intervalos_laboral_expedientes == 30
        assert config.hora_inicio == "09:00"
        assert config.dias_laborales == ["lunes", "miercoles", "viernes"]

    def test_config_custom_sistema(self):
        """Configuración de sistema personalizada."""
        config = SystemConfig(
            nivel_log="DEBUG",
            max_tamaño_log_mb=100,
            intervalo_backup_automatico=14,
            formato_reportes="excel"
        )

        assert config.nivel_log == "DEBUG"
        assert config.max_tamaño_log_mb == 100
        assert config.intervalo_backup_automatico == 14
        assert config.formato_reportes == "excel"


class TestSystemConfigValidation:
    """Tests para validación de configuración."""

    def test_config_intervalo_invalido_lanza_error(self):
        """Intervalo inválido lanza IntervalError."""
        with pytest.raises(IntervalError):
            SystemConfig(intervalos_laboral_expedientes=0)

        with pytest.raises(IntervalError):
            SystemConfig(intervalos_laboral_entradas=2000)  # > 24 horas

    def test_config_hora_invalida_lanza_error(self):
        """Hora inválida lanza WorkHoursError."""
        with pytest.raises(WorkHoursError):
            SystemConfig(hora_inicio="25:00")

        with pytest.raises(WorkHoursError):
            SystemConfig(hora_fin="08:70")

    def test_config_rango_horas_invertido_lanza_error(self):
        """Rango de horas invertido lanza WorkHoursError."""
        with pytest.raises(WorkHoursError):
            SystemConfig(hora_inicio="18:00", hora_fin="08:00")

    def test_config_dias_invalidos_lanza_error(self):
        """Días laborales inválidos lanzan ValidationError."""
        with pytest.raises(ValidationError):
            SystemConfig(dias_laborales=["monday", "tuesday"])

        with pytest.raises(ValidationError):
            SystemConfig(dias_laborales=[])

    def test_config_fecha_invalida_lanza_error(self):
        """Fecha inválida lanza DateRangeError."""
        with pytest.raises(DateRangeError):
            SystemConfig(fecha_desde_entradas="2025/01/01")  # Formato incorrecto

        with pytest.raises(DateRangeError):
            SystemConfig(fecha_corte_expedientes="32/13/2025")  # Fecha inválida

    def test_config_rango_fechas_invertido_lanza_error(self):
        """Rango de fechas invertido lanza DateRangeError."""
        with pytest.raises(DateRangeError):
            SystemConfig(
                fecha_desde_expedientes="2025-12-31",
                fecha_hasta_expedientes="2025-01-01"
            )

    def test_config_reintentos_invalidos_lanza_error(self):
        """Reintentos inválidos lanzan IntervalError."""
        with pytest.raises(IntervalError):
            SystemConfig(max_reintentos_expedientes=0)

        with pytest.raises(IntervalError):
            SystemConfig(max_reintentos_entradas=25)  # > 20


class TestSystemConfigFileOperations:
    """Tests para operaciones con archivos."""

    def test_config_to_dict(self, tmp_path):
        """to_dict() convierte correctamente a diccionario."""
        config = SystemConfig(
            modo_monitor="laboral",
            headless=False
        )

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["modo_monitor"] == "laboral"
        assert config_dict["headless"] is False
        assert "directorio_extraccion_inicial" in config_dict

    def test_config_to_file(self, tmp_path):
        """to_file() guarda correctamente a JSON."""
        config = SystemConfig(
            modo_monitor="no_laboral",
            nivel_log="DEBUG"
        )

        config_file = tmp_path / "test_sistema.json"
        config.to_file(config_file)

        assert config_file.exists()

        # Verificar contenido
        with config_file.open("r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["modo_monitor"] == "no_laboral"
        assert data["nivel_log"] == "DEBUG"

    def test_from_file_uses_project_root_for_relative_path(self, tmp_path, monkeypatch):
        """from_file() resuelve rutas relativas desde la raíz del proyecto."""
        project_root = Path(__file__).resolve().parents[2]
        project_config = project_root / "config" / "sistema.json"
        assert project_config.exists(), "La plantilla de sistema debe existir en la raíz del proyecto"

        # Cambiar el directorio de trabajo para simular ejecución desde otra ubicación
        monkeypatch.chdir(tmp_path)

        config = SystemConfig.from_file("config/sistema.json")

        # Verificar que se cargan valores esperados sin crear archivos alternos
        assert config.modo_monitor == "automatico"

        tmp_config = tmp_path / "config" / "sistema.json"
        assert not tmp_config.exists()

        # No debe crearse un archivo dentro de Sistema_v5/config
        internal_config = Path(__file__).resolve().parents[1] / "config" / "sistema.json"
        assert not internal_config.exists()


class TestSystemConfigFromEnv:
    """Tests para la carga de configuración desde variables de entorno."""

    def test_from_env_reads_directories_and_numbers(self, monkeypatch):
        """from_env() mapea directorios, enteros y booleanos."""

        monkeypatch.setenv("SISTEMA_DIRECTORIO_LOGS", "/var/log/pjn")
        monkeypatch.setenv("SISTEMA_INTERVALO_BACKUP_AUTOMATICO", "14")
        monkeypatch.setenv("SISTEMA_ROTACION_LOGS", "0")
        monkeypatch.setenv("SISTEMA_DIAS_LABORALES", "lunes,viernes")
        monkeypatch.setenv("SISTEMA_NIVEL_LOG", "warning")

        config = SystemConfig.from_env()

        assert config.directorio_logs == "/var/log/pjn"
        assert config.intervalo_backup_automatico == 14
        assert config.rotacion_logs is False
        assert config.dias_laborales == ["lunes", "viernes"]
        assert config.nivel_log == "WARNING"

    def test_from_env_optional_fields_accept_none(self, monkeypatch):
        """from_env() interpreta valores nulos para campos opcionales."""

        monkeypatch.setenv("SISTEMA_FECHA_DESDE_ENTRADAS", "none")
        monkeypatch.setenv("SISTEMA_FECHA_ULTIMO_BACKUP", "")

        config = SystemConfig.from_env()

        assert config.fecha_desde_entradas is None
        assert config.fecha_ultimo_backup is None

    def test_from_env_custom_prefix(self, monkeypatch):
        """from_env() permite personalizar el prefijo."""

        monkeypatch.setenv("CUSTOM_HEADLESS", "false")
        monkeypatch.setenv("CUSTOM_MAX_PAGINAS_EXPEDIENTES", "75")

        config = SystemConfig.from_env(prefix="CUSTOM_")

        assert config.headless is False
        assert config.max_paginas_expedientes == 75

    def test_config_from_file(self, tmp_path):
        """from_file() carga correctamente desde JSON."""
        config_file = tmp_path / "test_sistema.json"

        # Crear config y guardar
        original = SystemConfig(
            modo_monitor="laboral",
            intervalos_laboral_expedientes=45,
            headless=False
        )
        original.to_file(config_file)

        # Cargar desde archivo
        loaded = SystemConfig.from_file(config_file)

        assert loaded.modo_monitor == "laboral"
        assert loaded.intervalos_laboral_expedientes == 45
        assert loaded.headless is False

    def test_config_from_file_crea_default_si_no_existe(self, tmp_path):
        """from_file() crea config por defecto si archivo no existe."""
        config_file = tmp_path / "no_existe.json"

        config = SystemConfig.from_file(config_file)

        # Debe crear archivo con config por defecto
        assert config_file.exists()
        assert config.modo_monitor == "automatico"

    def test_config_roundtrip(self, tmp_path):
        """Guardar y cargar preserva todos los valores."""
        config_file = tmp_path / "roundtrip.json"

        original = SystemConfig(
            directorio_extraccion_inicial="custom/inicial",
            modo_monitor="laboral",
            intervalos_laboral_expedientes=20,
            hora_inicio="09:30",
            dias_laborales=["lunes", "miercoles"],
            headless=False,
            nivel_log="WARNING",
            max_tamaño_log_mb=75
        )

        original.to_file(config_file)
        loaded = SystemConfig.from_file(config_file)

        assert loaded.directorio_extraccion_inicial == "custom/inicial"
        assert loaded.modo_monitor == "laboral"
        assert loaded.intervalos_laboral_expedientes == 20
        assert loaded.hora_inicio == "09:30"
        assert loaded.dias_laborales == ["lunes", "miercoles"]
        assert loaded.headless is False
        assert loaded.nivel_log == "WARNING"
        assert loaded.max_tamaño_log_mb == 75


class TestSystemConfigMigration:
    """Tests para migración desde monitor.json."""

    def test_from_monitor_config(self, tmp_path):
        """from_monitor_config() migra correctamente desde monitor.json."""
        monitor_file = tmp_path / "monitor.json"

        # Crear archivo monitor.json
        monitor_data = {
            "modo": "laboral",
            "headless": False,
            "directorio_datos": "data/mi_monitor",
            "intervalos_laboral_expedientes": 20,
            "hora_inicio": "09:00",
            "hora_fin": "17:00",
            "notificar_nuevas_entradas": False
        }

        with monitor_file.open("w", encoding="utf-8") as f:
            json.dump(monitor_data, f)

        # Migrar
        config = SystemConfig.from_monitor_config(monitor_file)

        assert config.modo_monitor == "laboral"
        assert config.headless is False
        assert config.directorio_monitor_datos == "data/mi_monitor"
        assert config.intervalos_laboral_expedientes == 20
        assert config.hora_inicio == "09:00"
        assert config.notificar_nuevas_entradas is False

    def test_from_monitor_config_no_existe_retorna_default(self, tmp_path):
        """from_monitor_config() retorna config default si archivo no existe."""
        monitor_file = tmp_path / "no_existe.json"

        config = SystemConfig.from_monitor_config(monitor_file)

        # Debe retornar config por defecto
        assert config.modo_monitor == "automatico"
        assert config.headless is True


class TestSystemConfigHelpers:
    """Tests para métodos helper de SystemConfig."""

    def test_crear_directorios(self, tmp_path):
        """crear_directorios() crea todos los directorios."""
        base = tmp_path / "test_sistema"

        config = SystemConfig(
            directorio_extraccion_inicial=str(base / "inicial"),
            directorio_expedientes_base=str(base / "expedientes"),
            directorio_logs=str(base / "logs"),
            directorio_cache=str(base / ".cache")
        )

        config.crear_directorios()

        assert Path(config.directorio_extraccion_inicial).exists()
        assert Path(config.directorio_expedientes_base).exists()
        assert Path(config.directorio_logs).exists()
        assert Path(config.directorio_cache).exists()

    def test_hacer_backup(self, tmp_path):
        """hacer_backup() crea backup de la configuración."""
        config = SystemConfig(
            directorio_backups=str(tmp_path / "backups"),
            modo_monitor="laboral"
        )

        backup_path = config.hacer_backup()

        assert backup_path.exists()
        assert backup_path.parent == Path(config.directorio_backups)
        assert "sistema_" in backup_path.name

        # Verificar contenido
        with backup_path.open("r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["modo_monitor"] == "laboral"

    def test_hacer_backup_actualiza_fecha(self, tmp_path):
        """hacer_backup() actualiza fecha_ultimo_backup."""
        config = SystemConfig(
            directorio_backups=str(tmp_path / "backups")
        )

        assert config.fecha_ultimo_backup is None

        config.hacer_backup()

        assert config.fecha_ultimo_backup is not None
        # Debe ser fecha de hoy
        hoy = datetime.now().strftime("%Y-%m-%d")
        assert config.fecha_ultimo_backup == hoy

    def test_hacer_backup_destino_custom(self, tmp_path):
        """hacer_backup() acepta destino personalizado."""
        config = SystemConfig()

        destino = tmp_path / "mi_backup.json"
        backup_path = config.hacer_backup(destino)

        assert backup_path == destino
        assert destino.exists()


class TestSystemConfigTypes:
    """Tests para tipos Literal."""

    def test_modo_monitor_acepta_valores_validos(self):
        """ModoMonitor acepta valores válidos."""
        config1 = SystemConfig(modo_monitor="automatico")
        config2 = SystemConfig(modo_monitor="laboral")
        config3 = SystemConfig(modo_monitor="no_laboral")

        assert config1.modo_monitor == "automatico"
        assert config2.modo_monitor == "laboral"
        assert config3.modo_monitor == "no_laboral"

    def test_modo_comparacion_acepta_valores_validos(self):
        """ModoComparacion acepta valores válidos."""
        config1 = SystemConfig(modo_comparacion="automatico")
        config2 = SystemConfig(modo_comparacion="manual")
        config3 = SystemConfig(modo_comparacion="deshabilitado")

        assert config1.modo_comparacion == "automatico"
        assert config2.modo_comparacion == "manual"
        assert config3.modo_comparacion == "deshabilitado"

    def test_formato_reportes_acepta_valores_validos(self):
        """FormatoReporte acepta valores válidos."""
        config1 = SystemConfig(formato_reportes="json")
        config2 = SystemConfig(formato_reportes="excel")
        config3 = SystemConfig(formato_reportes="pdf")

        assert config1.formato_reportes == "json"
        assert config2.formato_reportes == "excel"
        assert config3.formato_reportes == "pdf"

    def test_nivel_log_acepta_valores_validos(self):
        """NivelLog acepta valores válidos."""
        config1 = SystemConfig(nivel_log="DEBUG")
        config2 = SystemConfig(nivel_log="INFO")
        config3 = SystemConfig(nivel_log="WARNING")
        config4 = SystemConfig(nivel_log="ERROR")
        config5 = SystemConfig(nivel_log="CRITICAL")

        assert config1.nivel_log == "DEBUG"
        assert config2.nivel_log == "INFO"
        assert config3.nivel_log == "WARNING"
        assert config4.nivel_log == "ERROR"
        assert config5.nivel_log == "CRITICAL"


class TestSystemConfigEdgeCases:
    """Tests para casos edge."""

    def test_config_con_todas_fechas_none(self):
        """Config con todas las fechas en None es válida."""
        config = SystemConfig(
            fecha_desde_entradas=None,
            fecha_hasta_entradas=None,
            fecha_desde_expedientes=None,
            fecha_hasta_expedientes=None,
            fecha_corte_expedientes=None,
            fecha_ultimo_backup=None
        )

        # No debe lanzar excepción
        assert config.fecha_desde_entradas is None

    def test_config_con_fechas_formato_argentino(self):
        """Config acepta fechas en formato argentino."""
        config = SystemConfig(
            fecha_desde_entradas="01/01/2025",
            fecha_hasta_entradas="31/12/2025"
        )

        assert config.fecha_desde_entradas == "01/01/2025"
        assert config.fecha_hasta_entradas == "31/12/2025"

    def test_config_con_dias_con_tilde(self):
        """Config acepta días con tilde."""
        config = SystemConfig(
            dias_laborales=["lunes", "miércoles", "sábado"]
        )

        assert "miércoles" in config.dias_laborales
        assert "sábado" in config.dias_laborales

    def test_config_limites_cero_deshabilitados(self):
        """Límites en 0 significan sin límite."""
        config = SystemConfig(
            limite_memoria_mb=0,
            max_archivos_cache=0
        )

        assert config.limite_memoria_mb == 0
        assert config.max_archivos_cache == 0
