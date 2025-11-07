"""Tests para modelos de actuaciones."""

import pytest

from core.domain.entities.actuacion import Actuacion, ActuacionesArchivo


class TestActuacion:
    """Tests para la entidad Actuacion."""

    def test_crear_actuacion_basica(self):
        """Debe crear una actuación con datos básicos."""
        actuacion = Actuacion(
            indice=1,
            oficina="JUZGADO FEDERAL N°1",
        )

        assert actuacion.indice == 1
        assert actuacion.oficina == "JUZGADO FEDERAL N°1"
        assert actuacion.oficina_completa is None
        assert actuacion.fecha is None
        assert actuacion.tipo is None
        assert actuacion.detalle is None
        assert actuacion.tiene_archivo is False
        assert actuacion.descargado is False

    def test_crear_actuacion_completa(self):
        """Debe crear una actuación con todos los datos."""
        actuacion = Actuacion(
            indice=1,
            oficina="JUZGADO FEDERAL N°1",
            oficina_completa="JUZGADO FEDERAL N°1 DE LA PLATA",
            fecha="2025-01-15",
            tipo="Resolución",
            detalle="Se resuelve hacer lugar a...",
            foja="123",
            archivo="https://example.com/archivo.pdf",
            nombre_archivo="resolución_123.pdf",
            tiene_archivo=True,
            tipo_archivo="pdf",
            hash="abc123",
            extraida_en="2025-01-15T10:30:00",
            es_historica=False,
            descargado=True,
        )

        assert actuacion.indice == 1
        assert actuacion.oficina == "JUZGADO FEDERAL N°1"
        assert actuacion.oficina_completa == "JUZGADO FEDERAL N°1 DE LA PLATA"
        assert actuacion.fecha == "2025-01-15"
        assert actuacion.tipo == "Resolución"
        assert actuacion.detalle == "Se resuelve hacer lugar a..."
        assert actuacion.foja == "123"
        assert actuacion.archivo == "https://example.com/archivo.pdf"
        assert actuacion.nombre_archivo == "resolución_123.pdf"
        assert actuacion.tiene_archivo is True
        assert actuacion.tipo_archivo == "pdf"
        assert actuacion.hash == "abc123"
        assert actuacion.extraida_en == "2025-01-15T10:30:00"
        assert actuacion.es_historica is False
        assert actuacion.descargado is True

    def test_from_dict_con_claves_minusculas(self):
        """Debe crear actuación desde dict con claves minúsculas."""
        data = {
            "indice": 1,
            "oficina": "JUZGADO",
            "fecha": "2025-01-15",
            "tipo": "Resolución",
            "detalle": "Detalle de la actuación",
            "tiene_archivo": True,
            "tipo_archivo": "pdf",
        }

        actuacion = Actuacion.from_dict(data)

        assert actuacion.indice == 1
        assert actuacion.oficina == "JUZGADO"
        assert actuacion.fecha == "2025-01-15"
        assert actuacion.tipo == "Resolución"
        assert actuacion.detalle == "Detalle de la actuación"
        assert actuacion.tiene_archivo is True
        assert actuacion.tipo_archivo == "pdf"

    def test_from_dict_con_claves_mayusculas(self):
        """Debe crear actuación desde dict con claves mayúsculas (legacy)."""
        data = {
            "Indice": 1,
            "Oficina": "JUZGADO",
            "OficinaCompleta": "JUZGADO FEDERAL N°1",
            "Fecha": "2025-01-15",
            "Tipo": "Resolución",
            "TieneArchivo": True,
        }

        actuacion = Actuacion.from_dict(data)

        assert actuacion.indice == 1
        assert actuacion.oficina == "JUZGADO"
        assert actuacion.oficina_completa == "JUZGADO FEDERAL N°1"
        assert actuacion.fecha == "2025-01-15"
        assert actuacion.tipo == "Resolución"
        assert actuacion.tiene_archivo is True

    def test_from_dict_con_claves_camelcase(self):
        """Debe soportar claves en camelCase."""
        data = {
            "indice": 1,
            "oficina": "JUZGADO",
            "oficinaCompleta": "JUZGADO FEDERAL N°1",
            "nombreArchivo": "archivo.pdf",
            "tipoArchivo": "pdf",
            "tieneArchivo": True,
        }

        actuacion = Actuacion.from_dict(data)

        assert actuacion.oficina_completa == "JUZGADO FEDERAL N°1"
        assert actuacion.nombre_archivo == "archivo.pdf"
        assert actuacion.tipo_archivo == "pdf"
        assert actuacion.tiene_archivo is True

    def test_from_dict_con_extension_como_tipo_archivo(self):
        """Debe soportar 'extension' como alias de 'tipo_archivo'."""
        data = {
            "indice": 1,
            "oficina": "JUZGADO",
            "extension": "pdf",
        }

        actuacion = Actuacion.from_dict(data)

        assert actuacion.tipo_archivo == "pdf"

    def test_from_dict_indice_default_cero(self):
        """Debe usar 0 como default para indice si no está presente o es inválido."""
        data1 = {"oficina": "JUZGADO"}
        data2 = {"indice": None, "oficina": "JUZGADO"}

        actuacion1 = Actuacion.from_dict(data1)
        actuacion2 = Actuacion.from_dict(data2)

        assert actuacion1.indice == 0
        assert actuacion2.indice == 0

    def test_from_dict_booleans_default_false(self):
        """Debe usar False como default para booleanos."""
        data = {
            "indice": 1,
            "oficina": "JUZGADO",
        }

        actuacion = Actuacion.from_dict(data)

        assert actuacion.tiene_archivo is False
        assert actuacion.es_historica is False
        assert actuacion.descargado is False

    def test_to_dict(self):
        """Debe convertir actuación a diccionario con claves minúsculas."""
        actuacion = Actuacion(
            indice=1,
            oficina="JUZGADO",
            fecha="2025-01-15",
            tipo="Resolución",
            tiene_archivo=True,
            descargado=False,
        )

        data = actuacion.to_dict()

        assert data["indice"] == 1
        assert data["oficina"] == "JUZGADO"
        assert data["fecha"] == "2025-01-15"
        assert data["tipo"] == "Resolución"
        assert data["tiene_archivo"] is True
        assert data["descargado"] is False

    def test_to_legacy_dict(self):
        """Debe convertir actuación a diccionario con claves mayúsculas (legacy)."""
        actuacion = Actuacion(
            indice=1,
            oficina="JUZGADO",
            fecha="2025-01-15",
            tipo="Resolución",
            tiene_archivo=True,
            descargado=False,
        )

        data = actuacion.to_legacy_dict()

        assert data["Indice"] == 1
        assert data["Oficina"] == "JUZGADO"
        assert data["Fecha"] == "2025-01-15"
        assert data["Tipo"] == "Resolución"
        assert data["TieneArchivo"] is True
        assert data["Descargado"] is False

    def test_marcar_como_descargado(self):
        """Debe crear nueva actuación marcada como descargada."""
        actuacion = Actuacion(
            indice=1,
            oficina="JUZGADO",
            fecha="2025-01-15",
            descargado=False,
        )

        actuacion_descargada = actuacion.marcar_como_descargado()

        assert actuacion_descargada.descargado is True
        assert actuacion.descargado is False  # Original no cambia
        assert actuacion_descargada.indice == actuacion.indice
        assert actuacion_descargada.oficina == actuacion.oficina
        assert actuacion_descargada.fecha == actuacion.fecha

    def test_igualdad_por_indice_y_hash(self):
        """Dos actuaciones con mismo índice y hash deben ser iguales."""
        actuacion1 = Actuacion(
            indice=1,
            oficina="JUZGADO A",
            fecha="2025-01-15",
            hash="abc123",
        )
        actuacion2 = Actuacion(
            indice=1,
            oficina="JUZGADO B",  # Diferente oficina
            fecha="2025-01-16",  # Diferente fecha
            hash="abc123",
        )

        assert actuacion1 == actuacion2

    def test_desigualdad_por_indice(self):
        """Dos actuaciones con diferente índice deben ser diferentes."""
        actuacion1 = Actuacion(indice=1, oficina="JUZGADO", hash="abc123")
        actuacion2 = Actuacion(indice=2, oficina="JUZGADO", hash="abc123")

        assert actuacion1 != actuacion2

    def test_desigualdad_por_hash(self):
        """Dos actuaciones con diferente hash deben ser diferentes."""
        actuacion1 = Actuacion(indice=1, oficina="JUZGADO", hash="abc123")
        actuacion2 = Actuacion(indice=1, oficina="JUZGADO", hash="xyz789")

        assert actuacion1 != actuacion2

    def test_igualdad_con_hash_none(self):
        """Dos actuaciones con mismo índice y ambos hash None deben ser iguales."""
        actuacion1 = Actuacion(indice=1, oficina="JUZGADO", hash=None)
        actuacion2 = Actuacion(indice=1, oficina="JUZGADO", hash=None)

        assert actuacion1 == actuacion2

    def test_hash_consistente(self):
        """El hash debe ser consistente para mismo índice y hash."""
        actuacion1 = Actuacion(indice=1, oficina="JUZGADO A", hash="abc123")
        actuacion2 = Actuacion(indice=1, oficina="JUZGADO B", hash="abc123")

        assert hash(actuacion1) == hash(actuacion2)

    def test_inmutabilidad(self):
        """La actuación debe ser inmutable (frozen)."""
        actuacion = Actuacion(indice=1, oficina="JUZGADO")

        with pytest.raises(AttributeError):
            actuacion.indice = 2  # type: ignore

        with pytest.raises(AttributeError):
            actuacion.descargado = True  # type: ignore

    def test_repr(self):
        """Debe tener una representación string útil."""
        actuacion = Actuacion(
            indice=1,
            oficina="JUZGADO",
            fecha="2025-01-15",
            tipo="Resolución",
            detalle="Detalle de la actuación",
        )

        repr_str = repr(actuacion)

        assert "Actuacion" in repr_str
        assert "indice=1" in repr_str
        assert "JUZGADO" in repr_str
        assert "2025-01-15" in repr_str
        assert "Resolución" in repr_str

    def test_repr_con_detalle_largo(self):
        """Debe truncar detalles largos en la representación."""
        detalle_largo = "Este es un detalle muy largo que debería ser truncado " * 5
        actuacion = Actuacion(
            indice=1,
            oficina="JUZGADO",
            detalle=detalle_largo,
        )

        repr_str = repr(actuacion)

        # Debe contener los primeros caracteres y "..."
        assert len(repr_str) < len(detalle_largo)
        assert "..." in repr_str


class TestActuacionesArchivo:
    """Tests para la entidad ActuacionesArchivo."""

    def test_crear_archivo_basico(self):
        """Debe crear un archivo de actuaciones."""
        encabezado = {
            "numero": "FPA-000632-2017",
            "caratula": "EXPEDIENTE JUDICIAL",
        }
        actuaciones = (
            Actuacion(indice=1, oficina="JUZGADO", fecha="2025-01-15"),
            Actuacion(indice=2, oficina="JUZGADO", fecha="2025-01-16"),
        )

        archivo = ActuacionesArchivo(encabezado=encabezado, actuaciones=actuaciones)

        assert archivo.encabezado == encabezado
        assert len(archivo.actuaciones) == 2
        assert archivo.actuaciones[0].indice == 1
        assert archivo.actuaciones[1].indice == 2

    def test_to_dict(self):
        """Debe convertir a diccionario con claves minúsculas."""
        encabezado = {"numero": "FPA-000632-2017"}
        actuaciones = (Actuacion(indice=1, oficina="JUZGADO"),)

        archivo = ActuacionesArchivo(encabezado=encabezado, actuaciones=actuaciones)
        data = archivo.to_dict()

        assert "expediente" in data
        assert "actuaciones" in data
        assert data["expediente"]["numero"] == "FPA-000632-2017"
        assert len(data["actuaciones"]) == 1
        assert data["actuaciones"][0]["indice"] == 1

    def test_to_legacy_dict(self):
        """Debe convertir a diccionario con claves mayúsculas (legacy)."""
        encabezado = {"numero": "FPA-000632-2017"}
        actuaciones = (Actuacion(indice=1, oficina="JUZGADO"),)

        archivo = ActuacionesArchivo(encabezado=encabezado, actuaciones=actuaciones)
        data = archivo.to_legacy_dict()

        assert "Expediente" in data
        assert "Actuaciones" in data
        assert data["Expediente"]["numero"] == "FPA-000632-2017"
        assert len(data["Actuaciones"]) == 1
        assert data["Actuaciones"][0]["Indice"] == 1

    def test_contar_con_archivo(self):
        """Debe contar actuaciones con archivo adjunto."""
        encabezado = {"numero": "FPA-000632-2017"}
        actuaciones = (
            Actuacion(indice=1, oficina="JUZGADO", tiene_archivo=True),
            Actuacion(indice=2, oficina="JUZGADO", tiene_archivo=False),
            Actuacion(indice=3, oficina="JUZGADO", tiene_archivo=True),
            Actuacion(indice=4, oficina="JUZGADO", tiene_archivo=True),
        )

        archivo = ActuacionesArchivo(encabezado=encabezado, actuaciones=actuaciones)

        assert archivo.contar_con_archivo() == 3

    def test_contar_descargados(self):
        """Debe contar actuaciones con archivo descargado."""
        encabezado = {"numero": "FPA-000632-2017"}
        actuaciones = (
            Actuacion(indice=1, oficina="JUZGADO", descargado=True),
            Actuacion(indice=2, oficina="JUZGADO", descargado=False),
            Actuacion(indice=3, oficina="JUZGADO", descargado=True),
        )

        archivo = ActuacionesArchivo(encabezado=encabezado, actuaciones=actuaciones)

        assert archivo.contar_descargados() == 2

    def test_filtrar_por_tipo(self):
        """Debe filtrar actuaciones por tipo."""
        encabezado = {"numero": "FPA-000632-2017"}
        actuaciones = (
            Actuacion(indice=1, oficina="JUZGADO", tipo="Resolución"),
            Actuacion(indice=2, oficina="JUZGADO", tipo="Oficio"),
            Actuacion(indice=3, oficina="JUZGADO", tipo="Resolución"),
            Actuacion(indice=4, oficina="JUZGADO", tipo="Cédula"),
        )

        archivo = ActuacionesArchivo(encabezado=encabezado, actuaciones=actuaciones)
        resoluciones = archivo.filtrar_por_tipo("Resolución")

        assert len(resoluciones) == 2
        assert all(act.tipo == "Resolución" for act in resoluciones)
        assert resoluciones[0].indice == 1
        assert resoluciones[1].indice == 3

    def test_filtrar_por_tipo_sin_resultados(self):
        """Debe retornar tupla vacía si no hay actuaciones del tipo."""
        encabezado = {"numero": "FPA-000632-2017"}
        actuaciones = (
            Actuacion(indice=1, oficina="JUZGADO", tipo="Resolución"),
        )

        archivo = ActuacionesArchivo(encabezado=encabezado, actuaciones=actuaciones)
        oficios = archivo.filtrar_por_tipo("Oficio")

        assert len(oficios) == 0
        assert isinstance(oficios, tuple)

    def test_len(self):
        """Debe retornar el número de actuaciones."""
        encabezado = {"numero": "FPA-000632-2017"}
        actuaciones = tuple(
            Actuacion(indice=i, oficina="JUZGADO") for i in range(1, 6)
        )

        archivo = ActuacionesArchivo(encabezado=encabezado, actuaciones=actuaciones)

        assert len(archivo) == 5

    def test_len_con_archivo_vacio(self):
        """Debe retornar 0 si no hay actuaciones."""
        encabezado = {"numero": "FPA-000632-2017"}
        actuaciones = ()

        archivo = ActuacionesArchivo(encabezado=encabezado, actuaciones=actuaciones)

        assert len(archivo) == 0

    def test_repr(self):
        """Debe tener una representación string útil."""
        encabezado = {"numero": "FPA-000632-2017"}
        actuaciones = (
            Actuacion(indice=1, oficina="JUZGADO"),
            Actuacion(indice=2, oficina="JUZGADO"),
        )

        archivo = ActuacionesArchivo(encabezado=encabezado, actuaciones=actuaciones)
        repr_str = repr(archivo)

        assert "ActuacionesArchivo" in repr_str
        assert "FPA-000632-2017" in repr_str
        assert "actuaciones=2" in repr_str

    def test_repr_con_numero_en_formato_legacy(self):
        """Debe soportar número en formato legacy (Numero con mayúscula)."""
        encabezado = {"Numero": "FPA-000632-2017"}
        actuaciones = (Actuacion(indice=1, oficina="JUZGADO"),)

        archivo = ActuacionesArchivo(encabezado=encabezado, actuaciones=actuaciones)
        repr_str = repr(archivo)

        assert "FPA-000632-2017" in repr_str

    def test_inmutabilidad(self):
        """El archivo debe ser inmutable (frozen)."""
        encabezado = {"numero": "FPA-000632-2017"}
        actuaciones = (Actuacion(indice=1, oficina="JUZGADO"),)

        archivo = ActuacionesArchivo(encabezado=encabezado, actuaciones=actuaciones)

        with pytest.raises(AttributeError):
            archivo.encabezado = {}  # type: ignore

        with pytest.raises(AttributeError):
            archivo.actuaciones = ()  # type: ignore
