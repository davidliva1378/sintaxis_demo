"""Parser para filas del listado de expedientes del PJN.

Este módulo contiene funciones para interpretar las filas HTML
del listado de expedientes y convertirlas en objetos del dominio.

Migrado de: Sistema_v5/pjn/parsers/expedientes_parser.py
"""

from __future__ import annotations

from typing import Sequence

from core.domain.entities import ExpedienteResumen
from core.domain.utils.dates import normalizar_fecha


def parse_expediente_resumen(valores: Sequence[str]) -> ExpedienteResumen | None:
    """Interpreta la fila plana del listado de expedientes.

    Args:
        valores: Secuencia de strings con los valores de las celdas de la fila.
            Formato esperado: [numero, dependencia, caratula, situacion, ultima_actuacion]

    Returns:
        ExpedienteResumen si se pudo parsear correctamente, None si no.

    Example:
        >>> valores = ["CNM 0001/2024", "Juzgado Federal 1", "CASO X C/ Y", "En trámite", "15/01/2024"]
        >>> expediente = parse_expediente_resumen(valores)
        >>> print(expediente.numero)
        'CNM 0001/2024'
    """
    if len(valores) < 5:
        return None

    numero = valores[0].strip()
    dependencia = valores[1].strip()
    caratula = valores[2].strip()
    situacion = valores[3].strip() or None

    # Normalizar fecha de última actuación
    fecha_cruda = valores[4].strip()
    ultima_actuacion = normalizar_fecha(
        fecha_cruda, formatos_entrada=["%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"]
    )

    # Validar campos obligatorios
    if not numero or not caratula:
        return None

    return ExpedienteResumen(
        numero=numero,
        dependencia=dependencia,
        caratula=caratula,
        situacion=situacion,
        ultima_actuacion=ultima_actuacion,
    )


__all__ = ["parse_expediente_resumen"]
