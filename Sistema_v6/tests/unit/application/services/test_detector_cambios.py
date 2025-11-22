"""Tests para DetectorCambios.

Tests unitarios para el servicio de detección de cambios en expedientes.
"""

import pytest

from application.services.detector_cambios import CambioExpediente, DetectorCambios
from core.domain.entities.expediente import ExpedienteResumen


class TestDetectorCambios:
    """Tests para la clase DetectorCambios."""

    def test_sin_cambios_cuando_expedientes_identicos(self):
        """No debe detectar cambios cuando los expedientes son idénticos."""
        detector = DetectorCambios()

        expedientes_ant = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPEDIENTE JUDICIAL",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            )
        ]

        expedientes_act = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPEDIENTE JUDICIAL",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            )
        ]

        cambios = detector.detectar_cambios_expedientes(
            actuales=expedientes_act,
            anteriores=expedientes_ant,
        )

        assert len(cambios) == 0

    def test_detecta_cambio_ultima_actuacion(self):
        """Debe detectar cambio solo en última actuación."""
        detector = DetectorCambios()

        expedientes_ant = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPEDIENTE JUDICIAL",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            )
        ]

        expedientes_act = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPEDIENTE JUDICIAL",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-20",  # Cambió
            )
        ]

        cambios = detector.detectar_cambios_expedientes(
            actuales=expedientes_act,
            anteriores=expedientes_ant,
        )

        assert len(cambios) == 1
        assert cambios[0].tipo_cambio == "nueva_actuacion"
        assert cambios[0].campos_cambiados == ["ultima_actuacion"]
        assert cambios[0].valores_anteriores["ultima_actuacion"] == "2025-01-15"
        assert cambios[0].expediente.ultima_actuacion == "2025-01-20"

    def test_detecta_cambio_situacion(self):
        """Debe detectar cambio solo en situación."""
        detector = DetectorCambios()

        expedientes_ant = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPEDIENTE JUDICIAL",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            )
        ]

        expedientes_act = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPEDIENTE JUDICIAL",
                situacion="EN LETRA",  # Cambió
                ultima_actuacion="2025-01-15",
            )
        ]

        cambios = detector.detectar_cambios_expedientes(
            actuales=expedientes_act,
            anteriores=expedientes_ant,
        )

        assert len(cambios) == 1
        assert cambios[0].tipo_cambio == "cambio_situacion"
        assert cambios[0].campos_cambiados == ["situacion"]
        assert cambios[0].valores_anteriores["situacion"] == "EN TRAMITE"
        assert cambios[0].expediente.situacion == "EN LETRA"

    def test_detecta_cambio_dependencia(self):
        """Debe detectar cambio solo en dependencia."""
        detector = DetectorCambios()

        expedientes_ant = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPEDIENTE JUDICIAL",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            )
        ]

        expedientes_act = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°2",  # Cambió
                caratula="EXPEDIENTE JUDICIAL",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            )
        ]

        cambios = detector.detectar_cambios_expedientes(
            actuales=expedientes_act,
            anteriores=expedientes_ant,
        )

        assert len(cambios) == 1
        assert cambios[0].tipo_cambio == "cambio_dependencia"
        assert cambios[0].campos_cambiados == ["dependencia"]
        assert cambios[0].valores_anteriores["dependencia"] == "JUZGADO FEDERAL N°1"
        assert cambios[0].expediente.dependencia == "JUZGADO FEDERAL N°2"

    def test_detecta_cambio_caratula(self):
        """Debe detectar cambio solo en carátula."""
        detector = DetectorCambios()

        expedientes_ant = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPEDIENTE JUDICIAL",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            )
        ]

        expedientes_act = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPEDIENTE JUDICIAL MODIFICADO",  # Cambió
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            )
        ]

        cambios = detector.detectar_cambios_expedientes(
            actuales=expedientes_act,
            anteriores=expedientes_ant,
        )

        assert len(cambios) == 1
        assert cambios[0].tipo_cambio == "cambio_caratula"
        assert cambios[0].campos_cambiados == ["caratula"]
        assert cambios[0].valores_anteriores["caratula"] == "EXPEDIENTE JUDICIAL"
        assert cambios[0].expediente.caratula == "EXPEDIENTE JUDICIAL MODIFICADO"

    def test_detecta_multiples_cambios(self):
        """Debe detectar múltiples cambios en varios campos."""
        detector = DetectorCambios()

        expedientes_ant = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPEDIENTE JUDICIAL",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            )
        ]

        expedientes_act = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°2",  # Cambió
                caratula="EXPEDIENTE JUDICIAL",
                situacion="EN LETRA",  # Cambió
                ultima_actuacion="2025-01-20",  # Cambió
            )
        ]

        cambios = detector.detectar_cambios_expedientes(
            actuales=expedientes_act,
            anteriores=expedientes_ant,
        )

        assert len(cambios) == 1
        assert cambios[0].tipo_cambio == "multiples_cambios"
        assert len(cambios[0].campos_cambiados) == 3
        assert "ultima_actuacion" in cambios[0].campos_cambiados
        assert "situacion" in cambios[0].campos_cambiados
        assert "dependencia" in cambios[0].campos_cambiados

    def test_detecta_cambios_en_varios_expedientes(self):
        """Debe detectar cambios en múltiples expedientes."""
        detector = DetectorCambios()

        expedientes_ant = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPEDIENTE A",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            ),
            ExpedienteResumen(
                numero="FPA-000633-2017",
                dependencia="JUZGADO FEDERAL N°2",
                caratula="EXPEDIENTE B",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-10",
            ),
        ]

        expedientes_act = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPEDIENTE A",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-20",  # Cambió
            ),
            ExpedienteResumen(
                numero="FPA-000633-2017",
                dependencia="JUZGADO FEDERAL N°2",
                caratula="EXPEDIENTE B",
                situacion="EN LETRA",  # Cambió
                ultima_actuacion="2025-01-10",
            ),
        ]

        cambios = detector.detectar_cambios_expedientes(
            actuales=expedientes_act,
            anteriores=expedientes_ant,
        )

        assert len(cambios) == 2

        # Primer expediente: cambió última actuación
        cambio1 = [c for c in cambios if c.expediente.numero == "FPA-000632-2017"][0]
        assert cambio1.tipo_cambio == "nueva_actuacion"

        # Segundo expediente: cambió situación
        cambio2 = [c for c in cambios if c.expediente.numero == "FPA-000633-2017"][0]
        assert cambio2.tipo_cambio == "cambio_situacion"

    def test_ignora_expedientes_nuevos(self):
        """No debe reportar cambios en expedientes que no existían antes."""
        detector = DetectorCambios()

        expedientes_ant = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPEDIENTE A",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            )
        ]

        expedientes_act = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPEDIENTE A",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            ),
            ExpedienteResumen(
                numero="FPA-000999-2025",  # Nuevo, no existía antes
                dependencia="JUZGADO FEDERAL N°3",
                caratula="EXPEDIENTE NUEVO",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-20",
            ),
        ]

        cambios = detector.detectar_cambios_expedientes(
            actuales=expedientes_act,
            anteriores=expedientes_ant,
        )

        assert len(cambios) == 0

    def test_normaliza_valores_none_y_vacios(self):
        """Debe normalizar None y cadenas vacías al comparar."""
        detector = DetectorCambios()

        # Caso 1: None → ""
        expedientes_ant = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO",
                caratula="EXPTE",
                situacion=None,
                ultima_actuacion="2025-01-15",
            )
        ]

        expedientes_act = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO",
                caratula="EXPTE",
                situacion="",  # Equivalente a None
                ultima_actuacion="2025-01-15",
            )
        ]

        cambios = detector.detectar_cambios_expedientes(
            actuales=expedientes_act,
            anteriores=expedientes_ant,
        )

        assert len(cambios) == 0

    def test_normaliza_espacios_en_blanco(self):
        """Debe normalizar espacios en blanco al comparar."""
        detector = DetectorCambios()

        expedientes_ant = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO FEDERAL N°1",
                caratula="EXPTE",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            )
        ]

        expedientes_act = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="  JUZGADO FEDERAL N°1  ",  # Con espacios
                caratula="EXPTE",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            )
        ]

        cambios = detector.detectar_cambios_expedientes(
            actuales=expedientes_act,
            anteriores=expedientes_ant,
        )

        assert len(cambios) == 0

    def test_obtener_resumen_cambios(self):
        """Debe generar resumen estadístico de cambios."""
        detector = DetectorCambios()

        expedientes_ant = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO",
                caratula="A",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-15",
            ),
            ExpedienteResumen(
                numero="FPA-000633-2017",
                dependencia="JUZGADO",
                caratula="B",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-10",
            ),
            ExpedienteResumen(
                numero="FPA-000634-2017",
                dependencia="JUZGADO",
                caratula="C",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-05",
            ),
        ]

        expedientes_act = [
            ExpedienteResumen(
                numero="FPA-000632-2017",
                dependencia="JUZGADO",
                caratula="A",
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-20",  # Nueva actuación
            ),
            ExpedienteResumen(
                numero="FPA-000633-2017",
                dependencia="JUZGADO",
                caratula="B",
                situacion="EN LETRA",  # Cambio situación
                ultima_actuacion="2025-01-10",
            ),
            ExpedienteResumen(
                numero="FPA-000634-2017",
                dependencia="JUZGADO 2",  # Cambio dependencia
                caratula="C MODIFICADO",  # Cambio carátula
                situacion="EN TRAMITE",
                ultima_actuacion="2025-01-05",
            ),
        ]

        cambios = detector.detectar_cambios_expedientes(
            actuales=expedientes_act,
            anteriores=expedientes_ant,
        )

        resumen = detector.obtener_resumen_cambios(cambios)

        assert resumen["total"] == 3
        assert resumen["por_tipo"]["nueva_actuacion"] == 1
        assert resumen["por_tipo"]["cambio_situacion"] == 1
        assert resumen["por_tipo"]["multiples_cambios"] == 1
        assert len(resumen["expedientes_afectados"]) == 3
        assert "FPA-000632-2017" in resumen["expedientes_afectados"]
        assert "FPA-000633-2017" in resumen["expedientes_afectados"]
        assert "FPA-000634-2017" in resumen["expedientes_afectados"]


class TestCambioExpediente:
    """Tests para la clase CambioExpediente."""

    def test_crear_cambio_expediente(self):
        """Debe crear un CambioExpediente correctamente."""
        expediente = ExpedienteResumen(
            numero="FPA-000632-2017",
            dependencia="JUZGADO",
            caratula="EXPTE",
            situacion="EN TRAMITE",
            ultima_actuacion="2025-01-20",
        )

        cambio = CambioExpediente(
            expediente=expediente,
            tipo_cambio="nueva_actuacion",
            campos_cambiados=["ultima_actuacion"],
            valores_anteriores={"ultima_actuacion": "2025-01-15"},
        )

        assert cambio.expediente == expediente
        assert cambio.tipo_cambio == "nueva_actuacion"
        assert cambio.campos_cambiados == ["ultima_actuacion"]
        assert cambio.valores_anteriores["ultima_actuacion"] == "2025-01-15"

    def test_string_representation(self):
        """Debe tener una representación string útil."""
        expediente = ExpedienteResumen(
            numero="FPA-000632-2017",
            dependencia="JUZGADO",
            caratula="EXPTE",
        )

        cambio = CambioExpediente(
            expediente=expediente,
            tipo_cambio="cambio_situacion",
            campos_cambiados=["situacion"],
            valores_anteriores={"situacion": "EN TRAMITE"},
        )

        str_repr = str(cambio)

        assert "FPA-000632-2017" in str_repr
        assert "cambio_situacion" in str_repr
        assert "situacion" in str_repr
