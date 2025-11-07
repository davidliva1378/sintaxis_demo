"""Tests para modelos de expedientes."""

from datetime import datetime, timedelta

import pytest

from core.domain.entities.expediente import ExpedienteIdentificacion, ExpedienteResumen


class TestExpedienteResumen:
    """Tests para la entidad ExpedienteResumen."""

    def test_crear_expediente_basico(self):
        """Debe crear un expediente con datos básicos."""
        exp = ExpedienteResumen(
            numero="FPA-000632-2017",
            dependencia="JUZGADO FEDERAL N°1",
            caratula="EXPEDIENTE JUDICIAL",
        )

        assert exp.numero == "FPA-000632-2017"
        assert exp.dependencia == "JUZGADO FEDERAL N°1"
        assert exp.caratula == "EXPEDIENTE JUDICIAL"
        assert exp.situacion is None
        assert exp.ultima_actuacion is None

    def test_crear_expediente_completo(self):
        """Debe crear un expediente con todos los datos."""
        exp = ExpedienteResumen(
            numero="FPA-000632-2017",
            dependencia="JUZGADO FEDERAL N°1",
            caratula="EXPEDIENTE JUDICIAL",
            situacion="EN TRAMITE",
            ultima_actuacion="2025-01-15",
        )

        assert exp.numero == "FPA-000632-2017"
        assert exp.situacion == "EN TRAMITE"
        assert exp.ultima_actuacion == "2025-01-15"

    def test_from_dict_con_claves_minusculas(self):
        """Debe crear expediente desde dict con claves minúsculas."""
        data = {
            "numero": "FPA-000632-2017",
            "dependencia": "JUZGADO",
            "caratula": "EXPTE",
            "situacion": "EN TRAMITE",
            "ultima_actuacion": "2025-01-15",
        }

        exp = ExpedienteResumen.from_dict(data)

        assert exp.numero == "FPA-000632-2017"
        assert exp.dependencia == "JUZGADO"
        assert exp.caratula == "EXPTE"
        assert exp.situacion == "EN TRAMITE"
        assert exp.ultima_actuacion == "2025-01-15"

    def test_from_dict_con_claves_mayusculas(self):
        """Debe crear expediente desde dict con claves en mayúsculas (legacy)."""
        data = {
            "Numero": "FPA-000632-2017",
            "Dependencia": "JUZGADO",
            "Caratula": "EXPTE",
            "Situacion": "EN TRAMITE",
            "UltimaActuacion": "2025-01-15",
        }

        exp = ExpedienteResumen.from_dict(data)

        assert exp.numero == "FPA-000632-2017"
        assert exp.dependencia == "JUZGADO"

    def test_from_dict_con_valores_vacios(self):
        """Debe manejar valores vacíos correctamente."""
        data = {
            "numero": "",
            "dependencia": "",
            "caratula": "",
            "situacion": None,
            "ultima_actuacion": None,
        }

        exp = ExpedienteResumen.from_dict(data)

        assert exp.numero == ""
        assert exp.situacion is None
        assert exp.ultima_actuacion is None

    def test_to_dict(self):
        """Debe convertir expediente a diccionario."""
        exp = ExpedienteResumen(
            numero="FPA-000632-2017",
            dependencia="JUZGADO",
            caratula="EXPTE",
            situacion="EN TRAMITE",
            ultima_actuacion="2025-01-15",
        )

        data = exp.to_dict()

        assert data == {
            "numero": "FPA-000632-2017",
            "dependencia": "JUZGADO",
            "caratula": "EXPTE",
            "situacion": "EN TRAMITE",
            "ultima_actuacion": "2025-01-15",
        }

    def test_esta_activo_con_fecha_reciente(self):
        """Debe retornar True para expediente con actuación reciente."""
        # Fecha de hace 10 días
        fecha_reciente = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

        exp = ExpedienteResumen(
            numero="FPA-000632-2017",
            dependencia="JUZGADO",
            caratula="EXPTE",
            ultima_actuacion=fecha_reciente,
        )

        assert exp.esta_activo(dias=30) is True
        assert exp.esta_activo(dias=15) is True

    def test_esta_activo_con_fecha_antigua(self):
        """Debe retornar False para expediente con actuación antigua."""
        # Fecha de hace 40 días
        fecha_antigua = (datetime.now() - timedelta(days=40)).strftime("%Y-%m-%d")

        exp = ExpedienteResumen(
            numero="FPA-000632-2017",
            dependencia="JUZGADO",
            caratula="EXPTE",
            ultima_actuacion=fecha_antigua,
        )

        assert exp.esta_activo(dias=30) is False

    def test_esta_activo_con_fecha_formato_ddmmyyyy(self):
        """Debe soportar formato DD/MM/YYYY para última actuación."""
        # Fecha de hace 10 días en formato DD/MM/YYYY
        fecha = datetime.now() - timedelta(days=10)
        fecha_formateada = fecha.strftime("%d/%m/%Y")

        exp = ExpedienteResumen(
            numero="FPA-000632-2017",
            dependencia="JUZGADO",
            caratula="EXPTE",
            ultima_actuacion=fecha_formateada,
        )

        assert exp.esta_activo(dias=30) is True

    def test_esta_activo_sin_fecha(self):
        """Debe retornar False si no hay fecha de última actuación."""
        exp = ExpedienteResumen(
            numero="FPA-000632-2017", dependencia="JUZGADO", caratula="EXPTE"
        )

        assert exp.esta_activo(dias=30) is False

    def test_esta_activo_con_fecha_invalida(self):
        """Debe retornar False si la fecha es inválida."""
        exp = ExpedienteResumen(
            numero="FPA-000632-2017",
            dependencia="JUZGADO",
            caratula="EXPTE",
            ultima_actuacion="fecha-invalida",
        )

        assert exp.esta_activo(dias=30) is False

    def test_igualdad_por_numero(self):
        """Dos expedientes con mismo número deben ser iguales."""
        exp1 = ExpedienteResumen(
            numero="FPA-000632-2017", dependencia="JUZGADO A", caratula="EXPTE A"
        )
        exp2 = ExpedienteResumen(
            numero="FPA-000632-2017", dependencia="JUZGADO B", caratula="EXPTE B"
        )

        assert exp1 == exp2

    def test_desigualdad_por_numero(self):
        """Dos expedientes con diferente número deben ser diferentes."""
        exp1 = ExpedienteResumen(
            numero="FPA-000632-2017", dependencia="JUZGADO", caratula="EXPTE"
        )
        exp2 = ExpedienteResumen(
            numero="FPA-000633-2017", dependencia="JUZGADO", caratula="EXPTE"
        )

        assert exp1 != exp2

    def test_hash_consistente(self):
        """El hash debe ser consistente para el mismo número."""
        exp1 = ExpedienteResumen(
            numero="FPA-000632-2017", dependencia="JUZGADO A", caratula="EXPTE A"
        )
        exp2 = ExpedienteResumen(
            numero="FPA-000632-2017", dependencia="JUZGADO B", caratula="EXPTE B"
        )

        assert hash(exp1) == hash(exp2)

    def test_inmutabilidad(self):
        """El expediente debe ser inmutable (frozen)."""
        exp = ExpedienteResumen(
            numero="FPA-000632-2017", dependencia="JUZGADO", caratula="EXPTE"
        )

        with pytest.raises(AttributeError):
            exp.numero = "OTRO-NUMERO"  # type: ignore

    def test_repr(self):
        """Debe tener una representación string útil."""
        exp = ExpedienteResumen(
            numero="FPA-000632-2017", dependencia="JUZGADO", caratula="EXPEDIENTE JUDICIAL"
        )

        repr_str = repr(exp)

        assert "FPA-000632-2017" in repr_str
        assert "JUZGADO" in repr_str
        assert "ExpedienteResumen" in repr_str


class TestExpedienteIdentificacion:
    """Tests para la entidad ExpedienteIdentificacion."""

    def test_crear_identificacion(self):
        """Debe crear identificación con número y año."""
        ident = ExpedienteIdentificacion(numero="000632", anio="2017")

        assert ident.numero == "000632"
        assert ident.anio == "2017"

    def test_from_dict_con_claves_minusculas(self):
        """Debe crear identificación desde dict con claves minúsculas."""
        data = {"numero": "000632", "anio": "2017"}

        ident = ExpedienteIdentificacion.from_dict(data)

        assert ident.numero == "000632"
        assert ident.anio == "2017"

    def test_from_dict_con_claves_mayusculas(self):
        """Debe crear identificación desde dict con claves mayúsculas."""
        data = {"Numero": "000632", "Anio": "2017"}

        ident = ExpedienteIdentificacion.from_dict(data)

        assert ident.numero == "000632"
        assert ident.anio == "2017"

    def test_from_dict_con_anio_con_tilde(self):
        """Debe soportar 'año' con tilde."""
        data = {"numero": "000632", "año": "2017"}

        ident = ExpedienteIdentificacion.from_dict(data)

        assert ident.anio == "2017"

    def test_to_dict(self):
        """Debe convertir identificación a diccionario."""
        ident = ExpedienteIdentificacion(numero="000632", anio="2017")

        data = ident.to_dict()

        assert data == {"numero": "000632", "anio": "2017"}

    def test_inmutabilidad(self):
        """La identificación debe ser inmutable."""
        ident = ExpedienteIdentificacion(numero="000632", anio="2017")

        with pytest.raises(AttributeError):
            ident.numero = "999999"  # type: ignore

    def test_repr(self):
        """Debe tener representación string útil."""
        ident = ExpedienteIdentificacion(numero="000632", anio="2017")

        repr_str = repr(ident)

        assert "000632" in repr_str
        assert "2017" in repr_str
        assert "ExpedienteIdentificacion" in repr_str
