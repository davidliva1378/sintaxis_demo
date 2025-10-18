"""Script de demostración para ejercitar la agenda con repositorio JSON."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from Sistema_v5.agenda import AgendaService, JSONAgendaRepository


def crear_agenda(ruta: Path) -> AgendaService:
    repo = JSONAgendaRepository(ruta)
    agenda = AgendaService(repository=repo)
    agenda.agregar_categoria("capacitación")
    return agenda


def poblar_agenda(agenda: AgendaService) -> None:
    agenda.sincronizar_feriados({date(2024, 1, 1), date(2024, 3, 24)})

    agenda.registrar_vencimiento(
        titulo="Presentar descargo",
        fecha_inicio=date.today(),
        dias=5,
        etiquetas=["expediente", "prioridad"],
        metadata={"expediente": "5555/2024"},
    )

    audiencia = agenda.registrar_audiencia(
        titulo="Audiencia conciliatoria",
        fecha=date.today().replace(day=max(1, date.today().day - 1)),
        etiquetas=["conciliación"],
    )

    agenda.actualizar_item(
        audiencia.id,
        descripcion="Confirmar sala 3 y notificar a las partes",
        metadata={"sala": "3", "juez": "Dra. López"},
    )

    agenda.registrar_tarea(
        titulo="Capacitación IA aplicada",
        fecha_inicio=date.today(),
        fecha_vencimiento=date.today(),
        etiquetas=["capacitación"],
        metadata={"modalidad": "virtual"},
    )


def mostrar_resumen(agenda: AgendaService) -> None:
    print("=== Agenda persistida ===")
    for item in agenda.listar():
        print(f"[{item.tipo}] {item.titulo} - {item.fecha_inicio} -> {item.fecha_vencimiento}")
        if item.descripcion:
            print(f"  Descripción: {item.descripcion}")
        if item.etiquetas:
            print(f"  Etiquetas: {', '.join(item.etiquetas)}")
        if item.metadata:
            print(f"  Metadata: {item.metadata}")
        print()

    print("Feriados configurados:")
    for feriado in agenda.listar_feriados():
        print(f"  - {feriado}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "archivo",
        type=Path,
        help="Ruta del archivo JSON donde se almacenará la agenda",
    )
    args = parser.parse_args()

    agenda = crear_agenda(args.archivo)
    poblar_agenda(agenda)
    mostrar_resumen(agenda)


if __name__ == "__main__":
    main()
