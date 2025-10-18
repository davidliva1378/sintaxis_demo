"""Tests para el detector de cambios del monitor.

Este módulo prueba la lógica de detección de nuevas entradas
y cambios en expedientes.
"""

import pytest
from datetime import datetime

from pjn.models import Entrada, ExpedienteResumen
from pjn.monitor.detector import DetectorCambios


class TestDetectorCambios:
    """Tests para la clase DetectorCambios."""

    @pytest.fixture
    def detector(self):
        """Fixture que proporciona una instancia del detector."""
        return DetectorCambios()

    @pytest.fixture
    def entradas_base(self):
        """Fixture con entradas de ejemplo."""
        return [
            Entrada(
                numero="EXP-001",
                caratula="Caso A vs B",
                fecha="01/10/2025",
                evento="Notificación electrónica",
                tipo_evento="N",
                leida=False
            ),
            Entrada(
                numero="EXP-002",
                caratula="Caso C vs D",
                fecha="02/10/2025",
                evento="Presentación digital",
                tipo_evento="N",
                leida=False
            ),
        ]

    @pytest.fixture
    def expedientes_base(self):
        """Fixture con expedientes de ejemplo."""
        return [
            ExpedienteResumen(
                numero="EXP-001/2025",
                caratula="Caso A vs B",
                dependencia="Secretaría 1",
                situacion="En trámite",
                ultima_actuacion="10/10/2025"
            ),
            ExpedienteResumen(
                numero="EXP-002/2025",
                caratula="Caso C vs D",
                dependencia="Secretaría 2",
                situacion="En trámite",
                ultima_actuacion="15/10/2025"
            ),
        ]

    # =========================================================================
    # Tests para detectar_nuevas_entradas
    # =========================================================================

    def test_detectar_nuevas_entradas_sin_entradas_conocidas(self, detector, entradas_base):
        """Todas las actuales son nuevas si no hay conocidas."""
        actuales = entradas_base
        conocidas = []

        nuevas = detector.detectar_nuevas_entradas(actuales, conocidas)

        assert len(nuevas) == 2
        assert nuevas == actuales

    def test_detectar_nuevas_entradas_sin_cambios(self, detector, entradas_base):
        """No hay nuevas si actuales == conocidas."""
        actuales = entradas_base
        conocidas = entradas_base.copy()

        nuevas = detector.detectar_nuevas_entradas(actuales, conocidas)

        assert len(nuevas) == 0

    def test_detectar_nuevas_entradas_con_una_nueva(self, detector, entradas_base):
        """Detecta solo la entrada nueva."""
        conocidas = entradas_base[:1]  # Solo la primera
        nueva_entrada = Entrada(
            numero="EXP-003",
            caratula="Caso E vs F",
            fecha="03/10/2025",
            evento="Nueva notificación",
            tipo_evento="N",
            leida=False
        )
        actuales = conocidas + [nueva_entrada]

        nuevas = detector.detectar_nuevas_entradas(actuales, conocidas)

        assert len(nuevas) == 1
        assert nuevas[0] == nueva_entrada

    def test_detectar_nuevas_entradas_comparacion_por_tupla(self, detector):
        """La comparación usa (numero, fecha, evento), no identidad de objeto."""
        entrada_1 = Entrada(
            numero="EXP-001",
            caratula="Caso A",
            fecha="01/10/2025",
            evento="Evento A",
            tipo_evento="N",
            leida=False
        )
        # Mismos datos clave, diferente objeto
        entrada_2 = Entrada(
            numero="EXP-001",
            caratula="Caso A",
            fecha="01/10/2025",
            evento="Evento A",
            tipo_evento="N",
            leida=True  # Diferente leida (no afecta comparación)
        )

        actuales = [entrada_1]
        conocidas = [entrada_2]

        nuevas = detector.detectar_nuevas_entradas(actuales, conocidas)

        # No debe detectar como nueva porque la tupla (numero, fecha, evento) es igual
        assert len(nuevas) == 0

    def test_detectar_nuevas_entradas_evento_diferente(self, detector):
        """Detecta entrada nueva si el evento cambió."""
        entrada_1 = Entrada(
            numero="EXP-001",
            caratula="Caso A",
            fecha="01/10/2025",
            evento="Evento A",
            tipo_evento="N",
            leida=False
        )
        entrada_2 = Entrada(
            numero="EXP-001",
            caratula="Caso A",
            fecha="01/10/2025",
            evento="Evento B",  # Diferente evento
            tipo_evento="N",
            leida=False
        )

        actuales = [entrada_2]
        conocidas = [entrada_1]

        nuevas = detector.detectar_nuevas_entradas(actuales, conocidas)

        # Debe detectar como nueva porque evento es diferente
        assert len(nuevas) == 1
        assert nuevas[0] == entrada_2

    def test_detectar_nuevas_entradas_listas_vacias(self, detector):
        """Sin actuales ni conocidas, retorna lista vacía."""
        nuevas = detector.detectar_nuevas_entradas([], [])
        assert nuevas == []

    # =========================================================================
    # Tests para detectar_cambios_expedientes
    # =========================================================================

    def test_detectar_cambios_expedientes_sin_expedientes_anteriores(
        self, detector, expedientes_base
    ):
        """Sin expedientes anteriores, no hay cambios (solo nuevos)."""
        actuales = expedientes_base
        anteriores = []

        cambios = detector.detectar_cambios_expedientes(actuales, anteriores)

        # No hay cambios porque son todos nuevos, no modificados
        assert len(cambios) == 0

    def test_detectar_cambios_expedientes_sin_cambios(self, detector, expedientes_base):
        """Sin cambios si actuales == anteriores."""
        actuales = expedientes_base
        anteriores = expedientes_base.copy()

        cambios = detector.detectar_cambios_expedientes(actuales, anteriores)

        assert len(cambios) == 0

    def test_detectar_cambios_expedientes_una_actualizacion(self, detector, expedientes_base):
        """Detecta expediente con ultima_actuacion modificada."""
        anteriores = expedientes_base.copy()

        # Crear versión actualizada del primer expediente
        exp_actualizado = ExpedienteResumen(
            numero="EXP-001/2025",
            caratula="Caso A vs B",
            dependencia="Secretaría 1",
            situacion="En trámite",
            ultima_actuacion="17/10/2025"  # Cambió la fecha
        )

        actuales = [exp_actualizado, expedientes_base[1]]

        cambios = detector.detectar_cambios_expedientes(actuales, anteriores)

        assert len(cambios) == 1
        assert cambios[0].numero == "EXP-001/2025"
        assert cambios[0].ultima_actuacion == "17/10/2025"

    def test_detectar_cambios_expedientes_multiples_cambios(self, detector, expedientes_base):
        """Detecta múltiples expedientes modificados."""
        anteriores = expedientes_base.copy()

        # Actualizar ambos expedientes
        exp_1_actualizado = ExpedienteResumen(
            numero="EXP-001/2025",
            caratula="Caso A vs B",
            juzgado="Juzgado 1",
            dependencia="Secretaría 1",
            ultima_actuacion="17/10/2025"
        )
        exp_2_actualizado = ExpedienteResumen(
            numero="EXP-002/2025",
            caratula="Caso C vs D",
            juzgado="Juzgado 2",
            dependencia="Secretaría 2",
            ultima_actuacion="18/10/2025"
        )

        actuales = [exp_1_actualizado, exp_2_actualizado]

        cambios = detector.detectar_cambios_expedientes(actuales, anteriores)

        assert len(cambios) == 2
        assert {c.numero for c in cambios} == {"EXP-001/2025", "EXP-002/2025"}

    def test_detectar_cambios_expedientes_nuevo_no_cuenta_como_cambio(self, detector):
        """Expedientes nuevos no se cuentan como cambios."""
        anterior = ExpedienteResumen(
            numero="EXP-001/2025",
            caratula="Caso A",
            juzgado="Juzgado 1",
            dependencia="Secretaría 1",
            ultima_actuacion="10/10/2025"
        )
        nuevo = ExpedienteResumen(
            numero="EXP-999/2025",  # Número diferente (nuevo)
            caratula="Caso Nuevo",
            juzgado="Juzgado 2",
            dependencia="Secretaría 2",
            ultima_actuacion="17/10/2025"
        )

        anteriores = [anterior]
        actuales = [anterior, nuevo]

        cambios = detector.detectar_cambios_expedientes(actuales, anteriores)

        # El nuevo expediente NO debe aparecer en cambios
        assert len(cambios) == 0

    def test_detectar_cambios_expedientes_misma_actuacion_no_detecta(self, detector):
        """Expediente con misma ultima_actuacion no se detecta como cambio."""
        anterior = ExpedienteResumen(
            numero="EXP-001/2025",
            caratula="Caso A",
            juzgado="Juzgado 1",
            dependencia="Secretaría 1",
            ultima_actuacion="10/10/2025"
        )
        # Mismo número, misma ultima_actuacion
        actual = ExpedienteResumen(
            numero="EXP-001/2025",
            caratula="Caso A - Modificado",  # Carátula cambió (irrelevante)
            juzgado="Juzgado 1",
            dependencia="Secretaría 1",
            ultima_actuacion="10/10/2025"  # Igual
        )

        anteriores = [anterior]
        actuales = [actual]

        cambios = detector.detectar_cambios_expedientes(actuales, anteriores)

        # No hay cambios porque ultima_actuacion es igual
        assert len(cambios) == 0

    def test_detectar_cambios_expedientes_listas_vacias(self, detector):
        """Sin actuales ni anteriores, retorna lista vacía."""
        cambios = detector.detectar_cambios_expedientes([], [])
        assert cambios == []

    # =========================================================================
    # Tests de edge cases
    # =========================================================================

    def test_detectar_nuevas_entradas_fechas_none(self, detector):
        """Maneja entradas con fecha None."""
        entrada_con_fecha = Entrada(
            numero="EXP-001",
            fecha=datetime(2025, 10, 1),
            evento="Evento",
            tipo="N",
            link="https://example.com/1",
            leida=False
        )
        entrada_sin_fecha = Entrada(
            numero="EXP-002",
            fecha=None,
            evento="Evento sin fecha",
            tipo="N",
            link="https://example.com/2",
            leida=False
        )

        actuales = [entrada_con_fecha, entrada_sin_fecha]
        conocidas = [entrada_con_fecha]

        nuevas = detector.detectar_nuevas_entradas(actuales, conocidas)

        assert len(nuevas) == 1
        assert nuevas[0].fecha is None

    def test_detectar_cambios_expedientes_ultima_actuacion_none(self, detector):
        """Maneja expedientes con ultima_actuacion None."""
        anterior = ExpedienteResumen(
            numero="EXP-001/2025",
            caratula="Caso",
            juzgado="J1",
            dependencia="D1",
            ultima_actuacion=None
        )
        actual = ExpedienteResumen(
            numero="EXP-001/2025",
            caratula="Caso",
            juzgado="J1",
            dependencia="D1",
            ultima_actuacion="17/10/2025"  # Ahora tiene fecha
        )

        anteriores = [anterior]
        actuales = [actual]

        cambios = detector.detectar_cambios_expedientes(actuales, anteriores)

        # Debe detectar cambio de None → "17/10/2025"
        assert len(cambios) == 1
        assert cambios[0].ultima_actuacion == "17/10/2025"
