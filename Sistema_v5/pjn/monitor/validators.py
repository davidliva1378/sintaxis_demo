"""Validadores para la configuración del monitor.

Este módulo proporciona funciones de validación para parámetros
de configuración del monitor PJN.
"""

from __future__ import annotations

import re
from datetime import datetime, time
from typing import Any

from .exceptions import ValidationError, IntervalError, DateRangeError, WorkHoursError


# ============================================================================
# Validación de intervalos
# ============================================================================

def validar_intervalo(valor: int, nombre: str, min_val: int = 1, max_val: int = 86400) -> None:
    """Valida que un intervalo esté dentro de rangos razonables.

    Args:
        valor: Valor del intervalo en segundos
        nombre: Nombre del parámetro para mensajes de error
        min_val: Valor mínimo permitido (default: 1 segundo)
        max_val: Valor máximo permitido (default: 86400 = 24 horas)

    Raises:
        IntervalError: Si el valor está fuera de rango
    """
    if not isinstance(valor, int):
        raise IntervalError(
            f"{nombre} debe ser un entero, recibido: {type(valor).__name__}"
        )

    if valor < min_val:
        raise IntervalError(
            f"{nombre} debe ser al menos {min_val} segundos, recibido: {valor}"
        )

    if valor > max_val:
        raise IntervalError(
            f"{nombre} no puede exceder {max_val} segundos (24h), recibido: {valor}"
        )


def validar_max_reintentos(valor: int, nombre: str) -> None:
    """Valida el número máximo de reintentos.

    Args:
        valor: Número de reintentos
        nombre: Nombre del parámetro para mensajes de error

    Raises:
        IntervalError: Si el valor está fuera de rango
    """
    if not isinstance(valor, int):
        raise IntervalError(
            f"{nombre} debe ser un entero, recibido: {type(valor).__name__}"
        )

    if valor < 1:
        raise IntervalError(
            f"{nombre} debe ser al menos 1, recibido: {valor}"
        )

    if valor > 20:
        raise IntervalError(
            f"{nombre} no puede exceder 20 reintentos, recibido: {valor}"
        )


# ============================================================================
# Validación de fechas
# ============================================================================

def validar_formato_fecha(fecha_str: str | None, nombre: str) -> None:
    """Valida el formato de una fecha.

    Acepta formatos:
    - YYYY-MM-DD (ISO 8601)
    - DD/MM/YYYY (formato argentino)

    Args:
        fecha_str: String de fecha a validar (None es válido)
        nombre: Nombre del parámetro para mensajes de error

    Raises:
        DateRangeError: Si el formato es inválido
    """
    if fecha_str is None:
        return  # None es válido

    if not isinstance(fecha_str, str):
        raise DateRangeError(
            f"{nombre} debe ser un string, recibido: {type(fecha_str).__name__}"
        )

    # Formato ISO 8601: YYYY-MM-DD
    iso_pattern = r"^\d{4}-\d{2}-\d{2}$"
    # Formato argentino: DD/MM/YYYY
    arg_pattern = r"^\d{2}/\d{2}/\d{4}$"

    if not (re.match(iso_pattern, fecha_str) or re.match(arg_pattern, fecha_str)):
        raise DateRangeError(
            f"{nombre} debe estar en formato YYYY-MM-DD o DD/MM/YYYY, recibido: {fecha_str}"
        )

    # Intentar parsear para validar fecha válida
    try:
        if "-" in fecha_str:
            datetime.strptime(fecha_str, "%Y-%m-%d")
        else:
            datetime.strptime(fecha_str, "%d/%m/%Y")
    except ValueError as e:
        raise DateRangeError(
            f"{nombre} contiene fecha inválida: {fecha_str} ({e})"
        ) from e


def validar_rango_fechas(
    fecha_desde: str | None,
    fecha_hasta: str | None,
    nombre_desde: str,
    nombre_hasta: str
) -> None:
    """Valida que fecha_desde <= fecha_hasta.

    Args:
        fecha_desde: Fecha de inicio (None es válido)
        fecha_hasta: Fecha de fin (None es válido)
        nombre_desde: Nombre del parámetro desde
        nombre_hasta: Nombre del parámetro hasta

    Raises:
        DateRangeError: Si el rango es inválido
    """
    if fecha_desde is None or fecha_hasta is None:
        return  # Si alguna es None, no validar rango

    # Parsear fechas
    try:
        if "-" in fecha_desde:
            dt_desde = datetime.strptime(fecha_desde, "%Y-%m-%d")
        else:
            dt_desde = datetime.strptime(fecha_desde, "%d/%m/%Y")

        if "-" in fecha_hasta:
            dt_hasta = datetime.strptime(fecha_hasta, "%Y-%m-%d")
        else:
            dt_hasta = datetime.strptime(fecha_hasta, "%d/%m/%Y")

    except ValueError as e:
        raise DateRangeError(
            f"Error parseando rango de fechas: {e}"
        ) from e

    if dt_desde > dt_hasta:
        raise DateRangeError(
            f"{nombre_desde} ({fecha_desde}) no puede ser posterior a "
            f"{nombre_hasta} ({fecha_hasta})"
        )


# ============================================================================
# Validación de horas
# ============================================================================

def validar_formato_hora(hora_str: str | None, nombre: str) -> None:
    """Valida el formato de una hora.

    Acepta formato HH:MM (24 horas).

    Args:
        hora_str: String de hora a validar (None es válido)
        nombre: Nombre del parámetro para mensajes de error

    Raises:
        WorkHoursError: Si el formato es inválido
    """
    if hora_str is None:
        return  # None es válido

    if not isinstance(hora_str, str):
        raise WorkHoursError(
            f"{nombre} debe ser un string, recibido: {type(hora_str).__name__}"
        )

    # Formato HH:MM
    pattern = r"^([01]\d|2[0-3]):([0-5]\d)$"

    if not re.match(pattern, hora_str):
        raise WorkHoursError(
            f"{nombre} debe estar en formato HH:MM (00:00-23:59), recibido: {hora_str}"
        )


def validar_rango_horas(
    hora_inicio: str | None,
    hora_fin: str | None,
    nombre_inicio: str = "hora_inicio",
    nombre_fin: str = "hora_fin"
) -> None:
    """Valida que hora_inicio < hora_fin.

    Args:
        hora_inicio: Hora de inicio (None es válido)
        hora_fin: Hora de fin (None es válido)
        nombre_inicio: Nombre del parámetro inicio
        nombre_fin: Nombre del parámetro fin

    Raises:
        WorkHoursError: Si el rango es inválido
    """
    if hora_inicio is None or hora_fin is None:
        return  # Si alguna es None, no validar rango

    # Parsear horas
    try:
        t_inicio = datetime.strptime(hora_inicio, "%H:%M").time()
        t_fin = datetime.strptime(hora_fin, "%H:%M").time()
    except ValueError as e:
        raise WorkHoursError(
            f"Error parseando rango de horas: {e}"
        ) from e

    if t_inicio >= t_fin:
        raise WorkHoursError(
            f"{nombre_inicio} ({hora_inicio}) debe ser anterior a "
            f"{nombre_fin} ({hora_fin})"
        )


# ============================================================================
# Validación de días laborales
# ============================================================================

DIAS_VALIDOS = {
    "lunes", "martes", "miercoles", "miércoles",
    "jueves", "viernes", "sabado", "sábado", "domingo"
}


def validar_dias_laborales(dias: list[str] | None, nombre: str = "dias_laborales") -> None:
    """Valida que los días laborales sean válidos.

    Acepta nombres de días en español (con o sin tilde).

    Args:
        dias: Lista de días de la semana (None es válido)
        nombre: Nombre del parámetro para mensajes de error

    Raises:
        ValidationError: Si la lista es inválida
    """
    if dias is None:
        return  # None es válido

    if not isinstance(dias, list):
        raise ValidationError(
            f"{nombre} debe ser una lista, recibido: {type(dias).__name__}"
        )

    if len(dias) == 0:
        raise ValidationError(
            f"{nombre} no puede estar vacío"
        )

    # Validar cada día
    invalidos = []
    for dia in dias:
        if not isinstance(dia, str):
            raise ValidationError(
                f"{nombre} debe contener strings, encontrado: {type(dia).__name__}"
            )

        dia_lower = dia.lower()
        if dia_lower not in DIAS_VALIDOS:
            invalidos.append(dia)

    if invalidos:
        raise ValidationError(
            f"{nombre} contiene días inválidos: {', '.join(invalidos)}. "
            f"Días válidos: lunes, martes, miércoles, jueves, viernes, sábado, domingo"
        )

    # Validar no duplicados (ignorando tildes)
    dias_normalizados = set()
    for dia in dias:
        dia_norm = dia.lower().replace("á", "a").replace("é", "e").replace("í", "i")
        if dia_norm in dias_normalizados:
            raise ValidationError(
                f"{nombre} contiene día duplicado: {dia}"
            )
        dias_normalizados.add(dia_norm)


# ============================================================================
# Validación de directorios
# ============================================================================

def validar_directorio(directorio: str, nombre: str = "directorio_datos") -> None:
    """Valida que un directorio sea una ruta válida.

    Args:
        directorio: Ruta del directorio
        nombre: Nombre del parámetro para mensajes de error

    Raises:
        ValidationError: Si la ruta es inválida
    """
    if not isinstance(directorio, str):
        raise ValidationError(
            f"{nombre} debe ser un string, recibido: {type(directorio).__name__}"
        )

    if not directorio or directorio.isspace():
        raise ValidationError(
            f"{nombre} no puede estar vacío"
        )

    # Validar caracteres inválidos para rutas
    caracteres_invalidos = ["\0", "\n", "\r"]
    for char in caracteres_invalidos:
        if char in directorio:
            raise ValidationError(
                f"{nombre} contiene caracteres inválidos"
            )


__all__ = [
    "validar_intervalo",
    "validar_max_reintentos",
    "validar_formato_fecha",
    "validar_rango_fechas",
    "validar_formato_hora",
    "validar_rango_horas",
    "validar_dias_laborales",
    "validar_directorio",
]
