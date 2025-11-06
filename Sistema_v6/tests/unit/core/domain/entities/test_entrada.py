"""Tests para modelos de entradas y notificaciones."""

import pytest

from core.domain.entities.entrada import Entrada


class TestEntrada:
    """Tests para la entidad Entrada."""

    def test_crear_entrada_basica(self):
        """Debe crear una entrada con datos básicos."""
        entrada = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE JUDICIAL",
            fecha="2025-01-15",
        )

        assert entrada.numero == "FPA-000632-2017"
        assert entrada.caratula == "EXPEDIENTE JUDICIAL"
        assert entrada.fecha == "2025-01-15"
        assert entrada.evento is None
        assert entrada.tipo_evento is None
        assert entrada.leida is False
        assert entrada.extraida_en is None

    def test_crear_entrada_completa(self):
        """Debe crear una entrada con todos los datos."""
        entrada = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE JUDICIAL",
            fecha="2025-01-15",
            evento="Notificación de despacho",
            tipo_evento="DESPACHO",
            leida=True,
            extraida_en="2025-01-15T10:30:00",
        )

        assert entrada.numero == "FPA-000632-2017"
        assert entrada.evento == "Notificación de despacho"
        assert entrada.tipo_evento == "DESPACHO"
        assert entrada.leida is True
        assert entrada.extraida_en == "2025-01-15T10:30:00"

    def test_from_dict_con_claves_minusculas(self):
        """Debe crear entrada desde dict con claves minúsculas."""
        data = {
            "numero": "FPA-000632-2017",
            "caratula": "EXPEDIENTE JUDICIAL",
            "fecha": "2025-01-15",
            "evento": "Notificación",
            "tipo_evento": "DESPACHO",
            "leida": True,
            "extraida_en": "2025-01-15T10:30:00",
        }

        entrada = Entrada.from_dict(data)

        assert entrada.numero == "FPA-000632-2017"
        assert entrada.caratula == "EXPEDIENTE JUDICIAL"
        assert entrada.fecha == "2025-01-15"
        assert entrada.evento == "Notificación"
        assert entrada.tipo_evento == "DESPACHO"
        assert entrada.leida is True
        assert entrada.extraida_en == "2025-01-15T10:30:00"

    def test_from_dict_con_claves_mayusculas(self):
        """Debe crear entrada desde dict con claves mayúsculas (legacy)."""
        data = {
            "Numero": "FPA-000632-2017",
            "Caratula": "EXPEDIENTE",
            "Fecha": "2025-01-15",
            "Evento": "Notificación",
            "TipoEvento": "DESPACHO",
            "Leida": True,
        }

        entrada = Entrada.from_dict(data)

        assert entrada.numero == "FPA-000632-2017"
        assert entrada.caratula == "EXPEDIENTE"
        assert entrada.fecha == "2025-01-15"
        assert entrada.evento == "Notificación"
        assert entrada.tipo_evento == "DESPACHO"
        assert entrada.leida is True

    def test_from_dict_con_claves_camelcase(self):
        """Debe soportar claves en camelCase."""
        data = {
            "numero": "FPA-000632-2017",
            "caratula": "EXPEDIENTE",
            "fecha": "2025-01-15",
            "tipoEvento": "DESPACHO",
            "extraidaEn": "2025-01-15T10:30:00",
        }

        entrada = Entrada.from_dict(data)

        assert entrada.tipo_evento == "DESPACHO"
        assert entrada.extraida_en == "2025-01-15T10:30:00"

    def test_from_dict_con_valores_vacios(self):
        """Debe manejar valores vacíos correctamente."""
        data = {
            "numero": "",
            "caratula": "",
            "fecha": "",
            "evento": None,
            "tipo_evento": None,
            "leida": False,
        }

        entrada = Entrada.from_dict(data)

        assert entrada.numero == ""
        assert entrada.evento is None
        assert entrada.tipo_evento is None
        assert entrada.leida is False

    def test_from_dict_leida_default_false(self):
        """Debe usar False como default para 'leida' si no está presente."""
        data = {
            "numero": "FPA-000632-2017",
            "caratula": "EXPEDIENTE",
            "fecha": "2025-01-15",
        }

        entrada = Entrada.from_dict(data)

        assert entrada.leida is False

    def test_to_dict(self):
        """Debe convertir entrada a diccionario."""
        entrada = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            evento="Notificación",
            tipo_evento="DESPACHO",
            leida=True,
            extraida_en="2025-01-15T10:30:00",
        )

        data = entrada.to_dict()

        assert data == {
            "numero": "FPA-000632-2017",
            "caratula": "EXPEDIENTE",
            "fecha": "2025-01-15",
            "evento": "Notificación",
            "tipo_evento": "DESPACHO",
            "leida": True,
            "extraida_en": "2025-01-15T10:30:00",
        }

    def test_marcar_como_leida(self):
        """Debe crear nueva entrada marcada como leída."""
        entrada = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            leida=False,
        )

        entrada_leida = entrada.marcar_como_leida()

        assert entrada_leida.leida is True
        assert entrada.leida is False  # Original no cambia (inmutabilidad)
        assert entrada_leida.numero == entrada.numero
        assert entrada_leida.caratula == entrada.caratula
        assert entrada_leida.fecha == entrada.fecha

    def test_marcar_como_leida_preserva_campos(self):
        """Debe preservar todos los campos al marcar como leída."""
        entrada = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            evento="Notificación",
            tipo_evento="DESPACHO",
            leida=False,
            extraida_en="2025-01-15T10:30:00",
        )

        entrada_leida = entrada.marcar_como_leida()

        assert entrada_leida.evento == entrada.evento
        assert entrada_leida.tipo_evento == entrada.tipo_evento
        assert entrada_leida.extraida_en == entrada.extraida_en

    def test_igualdad_por_numero_fecha_evento(self):
        """Dos entradas con mismo número, fecha y evento deben ser iguales."""
        entrada1 = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE A",
            fecha="2025-01-15",
            evento="Notificación",
            leida=False,
        )
        entrada2 = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE B",
            fecha="2025-01-15",
            evento="Notificación",
            leida=True,  # Diferente estado de lectura
        )

        assert entrada1 == entrada2

    def test_desigualdad_por_numero(self):
        """Dos entradas con diferente número deben ser diferentes."""
        entrada1 = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            evento="Notificación",
        )
        entrada2 = Entrada(
            numero="FPA-000633-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            evento="Notificación",
        )

        assert entrada1 != entrada2

    def test_desigualdad_por_fecha(self):
        """Dos entradas con diferente fecha deben ser diferentes."""
        entrada1 = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            evento="Notificación",
        )
        entrada2 = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-16",
            evento="Notificación",
        )

        assert entrada1 != entrada2

    def test_desigualdad_por_evento(self):
        """Dos entradas con diferente evento deben ser diferentes."""
        entrada1 = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            evento="Notificación A",
        )
        entrada2 = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            evento="Notificación B",
        )

        assert entrada1 != entrada2

    def test_hash_consistente(self):
        """El hash debe ser consistente para mismos número, fecha y evento."""
        entrada1 = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE A",
            fecha="2025-01-15",
            evento="Notificación",
            leida=False,
        )
        entrada2 = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE B",
            fecha="2025-01-15",
            evento="Notificación",
            leida=True,
        )

        assert hash(entrada1) == hash(entrada2)

    def test_hash_diferente_para_diferentes_entradas(self):
        """El hash debe ser diferente para entradas diferentes."""
        entrada1 = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            evento="Notificación A",
        )
        entrada2 = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            evento="Notificación B",
        )

        assert hash(entrada1) != hash(entrada2)

    def test_inmutabilidad(self):
        """La entrada debe ser inmutable (frozen)."""
        entrada = Entrada(
            numero="FPA-000632-2017", caratula="EXPEDIENTE", fecha="2025-01-15"
        )

        with pytest.raises(AttributeError):
            entrada.numero = "OTRO-NUMERO"  # type: ignore

        with pytest.raises(AttributeError):
            entrada.leida = True  # type: ignore

    def test_repr(self):
        """Debe tener una representación string útil."""
        entrada = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            evento="Notificación de despacho",
            leida=False,
        )

        repr_str = repr(entrada)

        assert "FPA-000632-2017" in repr_str
        assert "2025-01-15" in repr_str
        assert "Notificación" in repr_str
        assert "leida=False" in repr_str
        assert "Entrada" in repr_str

    def test_repr_con_evento_largo(self):
        """Debe truncar eventos largos en la representación."""
        evento_largo = "Este es un evento muy largo que debería ser truncado en la representación"
        entrada = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            evento=evento_largo,
        )

        repr_str = repr(entrada)

        # Debe contener los primeros caracteres y "..."
        assert len(repr_str) < len(evento_largo) + 100
        assert "..." in repr_str

    def test_entrada_puede_usarse_en_set(self):
        """Las entradas deben poder usarse en conjuntos (hashable)."""
        entrada1 = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            evento="Notificación A",
        )
        entrada2 = Entrada(
            numero="FPA-000632-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            evento="Notificación A",
        )
        entrada3 = Entrada(
            numero="FPA-000633-2017",
            caratula="EXPEDIENTE",
            fecha="2025-01-15",
            evento="Notificación B",
        )

        conjunto = {entrada1, entrada2, entrada3}

        # entrada1 y entrada2 son iguales, solo debe haber 2 elementos
        assert len(conjunto) == 2
