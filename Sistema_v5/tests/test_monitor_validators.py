"""Tests para los validadores de configuración del monitor.

Este módulo prueba todas las funciones de validación para parámetros
de configuración del monitor PJN.
"""

from pathlib import Path

import pytest

from pjn.monitor.validators import (
    validar_intervalo,
    validar_max_reintentos,
    validar_formato_fecha,
    validar_rango_fechas,
    validar_formato_hora,
    validar_rango_horas,
    validar_dias_laborales,
    validar_directorio,
)
from pjn.monitor.exceptions import (
    IntervalError,
    DateRangeError,
    WorkHoursError,
    ValidationError,
)


class TestValidarIntervalo:
    """Tests para validar_intervalo()."""

    # =========================================================================
    # Casos exitosos
    # =========================================================================

    def test_intervalo_valido_rango_normal(self):
        """Intervalo válido dentro del rango normal."""
        # No debe lanzar excepción
        validar_intervalo(60, "test_intervalo")  # 1 minuto
        validar_intervalo(300, "test_intervalo")  # 5 minutos
        validar_intervalo(3600, "test_intervalo")  # 1 hora

    def test_intervalo_en_limites(self):
        """Intervalo en los límites exactos."""
        validar_intervalo(1, "test", min_val=1, max_val=100)
        validar_intervalo(100, "test", min_val=1, max_val=100)

    # =========================================================================
    # Casos de error
    # =========================================================================

    def test_intervalo_menor_que_minimo(self):
        """Intervalo menor que el mínimo lanza IntervalError."""
        with pytest.raises(IntervalError, match="debe ser al menos"):
            validar_intervalo(0, "test_intervalo", min_val=1)

    def test_intervalo_mayor_que_maximo(self):
        """Intervalo mayor que el máximo lanza IntervalError."""
        with pytest.raises(IntervalError, match="no puede exceder"):
            validar_intervalo(100000, "test_intervalo", max_val=86400)

    def test_intervalo_tipo_incorrecto(self):
        """Intervalo con tipo incorrecto lanza IntervalError."""
        with pytest.raises(IntervalError, match="debe ser un entero"):
            validar_intervalo(3.14, "test_intervalo")  # type: ignore

        with pytest.raises(IntervalError, match="debe ser un entero"):
            validar_intervalo("60", "test_intervalo")  # type: ignore

    def test_intervalo_negativo(self):
        """Intervalo negativo lanza IntervalError."""
        with pytest.raises(IntervalError, match="debe ser al menos"):
            validar_intervalo(-10, "test_intervalo")


class TestValidarMaxReintentos:
    """Tests para validar_max_reintentos()."""

    # =========================================================================
    # Casos exitosos
    # =========================================================================

    def test_reintentos_validos(self):
        """Número de reintentos válido."""
        validar_max_reintentos(1, "test_reintentos")
        validar_max_reintentos(3, "test_reintentos")
        validar_max_reintentos(10, "test_reintentos")
        validar_max_reintentos(20, "test_reintentos")

    # =========================================================================
    # Casos de error
    # =========================================================================

    def test_reintentos_cero(self):
        """Cero reintentos lanza IntervalError."""
        with pytest.raises(IntervalError, match="debe ser al menos 1"):
            validar_max_reintentos(0, "test_reintentos")

    def test_reintentos_excesivos(self):
        """Más de 20 reintentos lanza IntervalError."""
        with pytest.raises(IntervalError, match="no puede exceder 20"):
            validar_max_reintentos(21, "test_reintentos")

    def test_reintentos_tipo_incorrecto(self):
        """Tipo incorrecto lanza IntervalError."""
        with pytest.raises(IntervalError, match="debe ser un entero"):
            validar_max_reintentos("3", "test_reintentos")  # type: ignore


class TestValidarFormatoFecha:
    """Tests para validar_formato_fecha()."""

    # =========================================================================
    # Casos exitosos
    # =========================================================================

    def test_fecha_none_valida(self):
        """None es un valor válido."""
        validar_formato_fecha(None, "test_fecha")  # No debe lanzar

    def test_fecha_formato_iso_valida(self):
        """Fecha en formato ISO 8601 (YYYY-MM-DD)."""
        validar_formato_fecha("2025-10-18", "test_fecha")
        validar_formato_fecha("2025-01-01", "test_fecha")
        validar_formato_fecha("2025-12-31", "test_fecha")

    def test_fecha_formato_argentino_valida(self):
        """Fecha en formato argentino (DD/MM/YYYY)."""
        validar_formato_fecha("18/10/2025", "test_fecha")
        validar_formato_fecha("01/01/2025", "test_fecha")
        validar_formato_fecha("31/12/2025", "test_fecha")

    # =========================================================================
    # Casos de error
    # =========================================================================

    def test_fecha_formato_invalido(self):
        """Formato de fecha inválido lanza DateRangeError."""
        with pytest.raises(DateRangeError, match="debe estar en formato"):
            validar_formato_fecha("2025/10/18", "test_fecha")

        with pytest.raises(DateRangeError, match="debe estar en formato"):
            validar_formato_fecha("18-10-2025", "test_fecha")

        # Formato US con mes inválido (detectado en parsing)
        with pytest.raises(DateRangeError, match="contiene fecha inválida"):
            validar_formato_fecha("10/18/2025", "test_fecha")  # Mes 18 inválido

    def test_fecha_invalida_valores(self):
        """Fecha con valores inválidos lanza DateRangeError."""
        with pytest.raises(DateRangeError, match="contiene fecha inválida"):
            validar_formato_fecha("2025-13-01", "test_fecha")  # Mes 13

        with pytest.raises(DateRangeError, match="contiene fecha inválida"):
            validar_formato_fecha("2025-02-30", "test_fecha")  # 30 de febrero

    def test_fecha_tipo_incorrecto(self):
        """Tipo incorrecto lanza DateRangeError."""
        with pytest.raises(DateRangeError, match="debe ser un string"):
            validar_formato_fecha(20251018, "test_fecha")  # type: ignore


class TestValidarRangoFechas:
    """Tests para validar_rango_fechas()."""

    # =========================================================================
    # Casos exitosos
    # =========================================================================

    def test_rango_fechas_valido_iso(self):
        """Rango de fechas válido en formato ISO."""
        validar_rango_fechas(
            "2025-01-01", "2025-12-31",
            "fecha_desde", "fecha_hasta"
        )

    def test_rango_fechas_valido_argentino(self):
        """Rango de fechas válido en formato argentino."""
        validar_rango_fechas(
            "01/01/2025", "31/12/2025",
            "fecha_desde", "fecha_hasta"
        )

    def test_rango_fechas_mismo_dia(self):
        """Rango con misma fecha es válido."""
        validar_rango_fechas(
            "2025-10-18", "2025-10-18",
            "fecha_desde", "fecha_hasta"
        )

    def test_rango_con_none(self):
        """Rango con None en alguna fecha es válido."""
        validar_rango_fechas(None, "2025-12-31", "desde", "hasta")
        validar_rango_fechas("2025-01-01", None, "desde", "hasta")
        validar_rango_fechas(None, None, "desde", "hasta")

    # =========================================================================
    # Casos de error
    # =========================================================================

    def test_rango_fechas_invertido(self):
        """Fecha desde posterior a fecha hasta lanza DateRangeError."""
        with pytest.raises(DateRangeError, match="no puede ser posterior"):
            validar_rango_fechas(
                "2025-12-31", "2025-01-01",
                "fecha_desde", "fecha_hasta"
            )


class TestValidarFormatoHora:
    """Tests para validar_formato_hora()."""

    # =========================================================================
    # Casos exitosos
    # =========================================================================

    def test_hora_none_valida(self):
        """None es un valor válido."""
        validar_formato_hora(None, "test_hora")

    def test_hora_formato_valido(self):
        """Hora en formato HH:MM válido."""
        validar_formato_hora("00:00", "test_hora")
        validar_formato_hora("08:30", "test_hora")
        validar_formato_hora("12:00", "test_hora")
        validar_formato_hora("18:45", "test_hora")
        validar_formato_hora("23:59", "test_hora")

    # =========================================================================
    # Casos de error
    # =========================================================================

    def test_hora_formato_invalido(self):
        """Formato de hora inválido lanza WorkHoursError."""
        with pytest.raises(WorkHoursError, match="debe estar en formato HH:MM"):
            validar_formato_hora("8:30", "test_hora")  # Sin cero inicial

        with pytest.raises(WorkHoursError, match="debe estar en formato HH:MM"):
            validar_formato_hora("08:5", "test_hora")  # Minuto sin cero

        with pytest.raises(WorkHoursError, match="debe estar en formato HH:MM"):
            validar_formato_hora("08.30", "test_hora")  # Punto en vez de :

    def test_hora_valores_invalidos(self):
        """Valores de hora inválidos lanzan WorkHoursError."""
        with pytest.raises(WorkHoursError, match="debe estar en formato HH:MM"):
            validar_formato_hora("24:00", "test_hora")  # Hora 24

        with pytest.raises(WorkHoursError, match="debe estar en formato HH:MM"):
            validar_formato_hora("12:60", "test_hora")  # Minuto 60

    def test_hora_tipo_incorrecto(self):
        """Tipo incorrecto lanza WorkHoursError."""
        with pytest.raises(WorkHoursError, match="debe ser un string"):
            validar_formato_hora(830, "test_hora")  # type: ignore


class TestValidarRangoHoras:
    """Tests para validar_rango_horas()."""

    # =========================================================================
    # Casos exitosos
    # =========================================================================

    def test_rango_horas_valido(self):
        """Rango de horas válido."""
        validar_rango_horas("08:00", "18:00")
        validar_rango_horas("00:00", "23:59")
        validar_rango_horas("09:30", "17:45")

    def test_rango_con_none(self):
        """Rango con None en alguna hora es válido."""
        validar_rango_horas(None, "18:00")
        validar_rango_horas("08:00", None)
        validar_rango_horas(None, None)

    # =========================================================================
    # Casos de error
    # =========================================================================

    def test_rango_horas_invertido(self):
        """Hora inicio >= hora fin lanza WorkHoursError."""
        with pytest.raises(WorkHoursError, match="debe ser anterior"):
            validar_rango_horas("18:00", "08:00")

    def test_rango_horas_iguales(self):
        """Horas iguales lanza WorkHoursError."""
        with pytest.raises(WorkHoursError, match="debe ser anterior"):
            validar_rango_horas("08:00", "08:00")


class TestValidarDiasLaborales:
    """Tests para validar_dias_laborales()."""

    # =========================================================================
    # Casos exitosos
    # =========================================================================

    def test_dias_none_valido(self):
        """None es un valor válido."""
        validar_dias_laborales(None)

    def test_dias_validos(self):
        """Lista de días válidos."""
        validar_dias_laborales(["lunes", "martes", "miercoles", "jueves", "viernes"])
        validar_dias_laborales(["lunes"])
        validar_dias_laborales(["sabado", "domingo"])

    def test_dias_con_tilde(self):
        """Días con tilde son válidos."""
        validar_dias_laborales(["lunes", "miércoles", "sábado"])

    def test_dias_sin_tilde(self):
        """Días sin tilde son válidos."""
        validar_dias_laborales(["lunes", "miercoles", "sabado"])

    # =========================================================================
    # Casos de error
    # =========================================================================

    def test_dias_lista_vacia(self):
        """Lista vacía lanza ValidationError."""
        with pytest.raises(ValidationError, match="no puede estar vacío"):
            validar_dias_laborales([])

    def test_dias_tipo_incorrecto(self):
        """Tipo incorrecto lanza ValidationError."""
        with pytest.raises(ValidationError, match="debe ser una lista"):
            validar_dias_laborales("lunes")  # type: ignore

    def test_dias_elemento_invalido(self):
        """Elemento que no es string lanza ValidationError."""
        with pytest.raises(ValidationError, match="debe contener strings"):
            validar_dias_laborales([1, 2, 3])  # type: ignore

    def test_dias_nombre_invalido(self):
        """Nombre de día inválido lanza ValidationError."""
        with pytest.raises(ValidationError, match="contiene días inválidos"):
            validar_dias_laborales(["monday", "tuesday"])  # En inglés

        with pytest.raises(ValidationError, match="contiene días inválidos"):
            validar_dias_laborales(["lunes", "martes", "miercoles", "xxx"])

    def test_dias_duplicados(self):
        """Días duplicados lanzan ValidationError."""
        with pytest.raises(ValidationError, match="contiene día duplicado"):
            validar_dias_laborales(["lunes", "martes", "lunes"])

    def test_dias_duplicados_con_tilde(self):
        """Días duplicados con/sin tilde lanzan ValidationError."""
        with pytest.raises(ValidationError, match="contiene día duplicado"):
            validar_dias_laborales(["miercoles", "miércoles"])


class TestValidarDirectorio:
    """Tests para validar_directorio()."""

    # =========================================================================
    # Casos exitosos
    # =========================================================================

    def test_directorio_pathlike_valido(self, tmp_path):
        """Permite PathLike y devuelve la ruta absoluta normalizada."""
        carpeta = tmp_path / "monitor"
        carpeta.mkdir()

        resultado = validar_directorio(carpeta)

        assert isinstance(resultado, str)
        assert resultado == str(carpeta.resolve())

    def test_directorio_relativo_se_normaliza(self, tmp_path, monkeypatch):
        """Las rutas relativas se resuelven contra el cwd actual."""
        monkeypatch.chdir(tmp_path)

        ruta_relativa = Path("./sub/../datos/monitor")
        resultado = validar_directorio(ruta_relativa)

        esperado = (tmp_path / "datos" / "monitor").resolve()
        assert resultado == str(esperado)
        assert not esperado.exists()

    def test_directorio_con_home_se_expande(self, tmp_path, monkeypatch):
        """El caracter ~ se expande usando HOME."""
        monkeypatch.setenv("HOME", str(tmp_path))

        resultado = validar_directorio("~/monitor_datos", create=True)

        esperado = (tmp_path / "monitor_datos").resolve()
        assert resultado == str(esperado)
        assert esperado.exists()

    def test_directorio_inexistente_se_crea(self, tmp_path):
        """Con create=True se crea la carpeta (y padres)."""
        destino = tmp_path / "nuevo" / "monitor"

        resultado = validar_directorio(destino, create=True)

        assert resultado == str(destino.resolve())
        assert destino.exists()

    # =========================================================================
    # Casos de error
    # =========================================================================

    def test_directorio_vacio(self):
        """Directorio vacío lanza ValidationError."""
        with pytest.raises(ValidationError, match="no puede estar vacío"):
            validar_directorio("")

        with pytest.raises(ValidationError, match="no puede estar vacío"):
            validar_directorio("   ")

    def test_directorio_tipo_incorrecto(self):
        """Tipo incorrecto lanza ValidationError."""
        with pytest.raises(ValidationError, match="string o PathLike"):
            validar_directorio(123)  # type: ignore

    def test_directorio_caracteres_invalidos(self):
        """Caracteres inválidos lanzan ValidationError."""
        with pytest.raises(ValidationError, match="contiene caracteres inválidos"):
            validar_directorio("data/monitor\0")  # Null byte

        with pytest.raises(ValidationError, match="contiene caracteres inválidos"):
            validar_directorio("data/monitor\n")  # Newline


class TestIntegracionMonitorConfig:
    """Tests de integración con MonitorConfig."""

    def test_config_default_valida(self):
        """Configuración por defecto es válida."""
        from pjn.monitor.config import MonitorConfig

        # No debe lanzar excepción
        config = MonitorConfig()

        assert config.intervalos_laboral_expedientes == 15
        assert config.hora_inicio == "08:00"
        assert config.hora_fin == "18:00"

    def test_config_custom_valida(self):
        """Configuración personalizada válida."""
        from pjn.monitor.config import MonitorConfig

        config = MonitorConfig(
            intervalos_laboral_expedientes=30,
            intervalos_laboral_entradas=20,
            dias_laborales=["lunes", "martes", "miércoles"],
            hora_inicio="09:00",
            hora_fin="17:00",
            fecha_desde_entradas="2025-01-01",
            fecha_hasta_entradas="2025-12-31"
        )

        assert config.intervalos_laboral_expedientes == 30
        assert config.dias_laborales == ["lunes", "martes", "miércoles"]

    def test_config_intervalo_invalido_lanza_error(self):
        """Intervalo inválido lanza IntervalError al crear config."""
        from pjn.monitor.config import MonitorConfig

        with pytest.raises(IntervalError):
            MonitorConfig(intervalos_laboral_expedientes=0)

    def test_config_hora_invalida_lanza_error(self):
        """Hora inválida lanza WorkHoursError al crear config."""
        from pjn.monitor.config import MonitorConfig

        with pytest.raises(WorkHoursError):
            MonitorConfig(hora_inicio="25:00")

    def test_config_rango_horas_invertido_lanza_error(self):
        """Rango de horas invertido lanza WorkHoursError."""
        from pjn.monitor.config import MonitorConfig

        with pytest.raises(WorkHoursError):
            MonitorConfig(hora_inicio="18:00", hora_fin="08:00")

    def test_config_dias_invalidos_lanza_error(self):
        """Días laborales inválidos lanzan ValidationError."""
        from pjn.monitor.config import MonitorConfig

        with pytest.raises(ValidationError):
            MonitorConfig(dias_laborales=["monday"])

    def test_config_fecha_invalida_lanza_error(self):
        """Fecha inválida lanza DateRangeError al crear config."""
        from pjn.monitor.config import MonitorConfig

        with pytest.raises(DateRangeError):
            MonitorConfig(fecha_desde_entradas="2025/01/01")  # Formato incorrecto

    def test_config_rango_fechas_invertido_lanza_error(self):
        """Rango de fechas invertido lanza DateRangeError."""
        from pjn.monitor.config import MonitorConfig

        with pytest.raises(DateRangeError):
            MonitorConfig(
                fecha_desde_entradas="2025-12-31",
                fecha_hasta_entradas="2025-01-01"
            )
