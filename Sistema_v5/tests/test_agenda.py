"""Tests para el módulo de agenda y gestión de plazos."""

from datetime import date

import pytest

from Sistema_v5.agenda import (
    AgendaQuery,
    AgendaService,
    calcular_fecha_plazo,
    contar_dias_corridos,
    contar_dias_habiles,
    crear_agenda_default,
    dias_corridos_entre,
    dias_habiles_entre,
    obtener_agenda_global,
)


class TestUtilidadesPlazos:
    """Valida las funciones utilitarias de fechas."""

    def test_calcular_fecha_plazo_habiles(self):
        feriados = {date(2024, 1, 9)}
        fecha_inicio = date(2024, 1, 5)  # Viernes

        fecha_vencimiento = calcular_fecha_plazo(
            fecha_inicio,
            3,
            "habiles",
            feriados=feriados,
        )

        assert fecha_vencimiento == date(2024, 1, 11)

    def test_calcular_fecha_plazo_corridos(self):
        fecha_inicio = date(2024, 2, 28)

        fecha_vencimiento = calcular_fecha_plazo(fecha_inicio, 3, "corridos")

        assert fecha_vencimiento == date(2024, 3, 2)

    def test_contar_dias_habiles_inclusive(self):
        feriados = {date(2024, 1, 10)}
        inicio = date(2024, 1, 8)
        fin = date(2024, 1, 12)

        total = contar_dias_habiles(inicio, fin, feriados=feriados)

        assert total == 4  # Se excluye el feriado dentro de la semana

    def test_dias_corridos_inclusive(self):
        inicio = date(2024, 5, 1)
        fin = date(2024, 5, 3)

        assert contar_dias_corridos(inicio, fin) == 3
        assert dias_corridos_entre(inicio, fin) == 3

    def test_alias_dias_habiles(self):
        inicio = date(2024, 1, 8)
        fin = date(2024, 1, 9)

        assert dias_habiles_entre(inicio, fin) == 2

    def test_error_fecha_fin_anterior(self):
        inicio = date(2024, 1, 10)
        fin = date(2024, 1, 9)

        with pytest.raises(ValueError):
            contar_dias_corridos(inicio, fin)

        with pytest.raises(ValueError):
            contar_dias_habiles(inicio, fin)


class TestAgendaService:
    """Cubre casos de uso del servicio de agenda."""

    def setup_method(self):
        self.agenda = crear_agenda_default(feriados={date(2024, 1, 1)})

    def test_registrar_vencimiento(self):
        item = self.agenda.registrar_vencimiento(
            titulo="Presentar escrito",
            fecha_inicio=date(2024, 1, 2),
            dias=2,
        )

        assert item.tipo == "vencimiento"
        assert item.fecha_vencimiento == date(2024, 1, 4)
        assert item.metadata is None

    def test_agregar_categoria_personalizada(self):
        self.agenda.agregar_categoria("capacitacion")

        item = self.agenda.registrar_item(
            tipo="capacitacion",
            titulo="Curso IA",
            fecha_inicio=date(2024, 3, 1),
            descripcion="Repasar jurisprudencia",
        )

        assert item.tipo == "capacitacion"
        assert "capacitacion" in self.agenda.categorias_disponibles()

    def test_buscar_por_texto_y_etiquetas(self):
        self.agenda.registrar_tarea(
            titulo="Revisar expediente 123",
            fecha_inicio=date(2024, 4, 10),
            fecha_vencimiento=date(2024, 4, 12),
            etiquetas=["expediente", "prioridad"],
            descripcion="Completar informe"
        )
        self.agenda.registrar_nota(
            titulo="Reunión con perito",
            fecha=date(2024, 4, 11),
            etiquetas=["reunion"],
        )

        query = AgendaQuery(
            tipos=("tarea",),
            etiquetas=("prioridad",),
            texto="informe",
        )

        resultados = self.agenda.buscar(query)

        assert len(resultados) == 1
        assert resultados[0].titulo == "Revisar expediente 123"

    def test_eliminar_item(self):
        item = self.agenda.registrar_recordatorio(
            titulo="Llamar a cliente",
            fecha=date(2024, 6, 3),
        )

        self.agenda.eliminar(item.id)

        assert self.agenda.obtener(item.id) is None

    def test_consultas_de_dias_desde_servicio(self):
        inicio = date(2024, 1, 2)
        fin = date(2024, 1, 5)

        assert self.agenda.contar_dias_habiles(inicio, fin) == 4
        assert self.agenda.contar_dias_corridos(inicio, fin) == 4

    def test_registrar_audiencia_metadatos(self):
        item = self.agenda.registrar_audiencia(
            titulo="Audiencia preliminar",
            fecha=date(2024, 7, 15),
            metadata={"expediente": "2024/12345"},
        )

        assert item.tipo == "audiencia"
        assert item.metadata == {"expediente": "2024/12345"}

    def test_prevenir_categoria_desconocida(self):
        with pytest.raises(ValueError):
            self.agenda.registrar_item(
                tipo="desconocida",
                titulo="Evento",
                fecha_inicio=date(2024, 1, 1),
            )

    def test_validar_titulo_obligatorio(self):
        with pytest.raises(ValueError):
            self.agenda.registrar_tarea(
                titulo="   ",
                fecha_inicio=date(2024, 1, 1),
            )

    def test_validar_fecha_vencimiento(self):
        with pytest.raises(ValueError):
            self.agenda.registrar_tarea(
                titulo="Prueba",
                fecha_inicio=date(2024, 1, 10),
                fecha_vencimiento=date(2024, 1, 9),
            )


class TestIntegracionCompartida:
    """Confirma que la agenda global puede reutilizarse."""

    def test_obtener_agenda_global(self):
        agenda_1 = obtener_agenda_global()
        agenda_2 = obtener_agenda_global()

        assert agenda_1 is agenda_2
        assert isinstance(agenda_1, AgendaService)
