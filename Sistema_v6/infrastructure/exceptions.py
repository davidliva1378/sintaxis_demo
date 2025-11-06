"""Excepciones personalizadas para el sistema de scraping del PJN - Sistema v6.

Este módulo define una jerarquía de excepciones que permite un manejo
más granular y específico de errores en diferentes capas del sistema.

Migrado de: Sistema_v5/pjn/exceptions.py
"""

from __future__ import annotations


class PJNError(Exception):
    """Excepción base para todos los errores del sistema PJN.

    Todos los errores específicos del sistema heredan de esta clase,
    permitiendo capturar cualquier error relacionado con PJN con un
    solo handler si es necesario.
    """

    pass


# === Errores de Autenticación y Sesión ===


class AutenticacionError(PJNError):
    """Error relacionado con autenticación en el portal PJN."""

    pass


class CredencialesFaltantes(AutenticacionError):
    """Se lanza cuando no se encuentran credenciales para el portal."""

    pass


class SesionInvalida(AutenticacionError):
    """Se lanza cuando no puede verificarse un login válido."""

    pass


# === Errores de Extracción ===


class ExtraccionError(PJNError):
    """Error durante la extracción de datos del portal."""

    pass


class ExpedienteNoEncontrado(ExtraccionError):
    """El expediente solicitado no fue encontrado en el portal."""

    pass


class ActuacionesNoDisponibles(ExtraccionError):
    """No se pudieron extraer actuaciones del expediente."""

    pass


class TimeoutExtraccion(ExtraccionError):
    """Se agotó el tiempo de espera durante la extracción."""

    pass


# === Errores de Parsing ===


class ParsingError(PJNError):
    """Error durante el procesamiento de datos extraídos."""

    pass


class FormatoInvalido(ParsingError):
    """Los datos no tienen el formato esperado."""

    pass


class DatosIncompletos(ParsingError):
    """Faltan datos requeridos en la estructura."""

    pass


# === Errores de Descarga ===


class DescargaError(PJNError):
    """Error durante la descarga de archivos."""

    pass


class ArchivoNoDisponible(DescargaError):
    """El archivo solicitado no está disponible para descarga."""

    pass


class DescargaFallida(DescargaError):
    """La descarga del archivo falló después de todos los reintentos."""

    def __init__(
        self,
        mensaje: str,
        intentos: int = 3,
        error_original: Exception | None = None,
    ):
        """Inicializa la excepción con detalles sobre los reintentos.

        Args:
            mensaje: Descripción del error
            intentos: Número de intentos realizados
            error_original: La excepción original que causó el fallo
        """
        super().__init__(mensaje)
        self.intentos = intentos
        self.error_original = error_original


# === Errores de Validación ===


class ValidacionError(PJNError):
    """Error de validación de datos de entrada."""

    pass


class ParametroInvalido(ValidacionError):
    """Un parámetro recibido no es válido."""

    def __init__(self, parametro: str, valor: object, razon: str):
        """Inicializa la excepción con detalles del parámetro inválido.

        Args:
            parametro: Nombre del parámetro inválido
            valor: Valor recibido
            razon: Explicación de por qué es inválido
        """
        mensaje = f"Parámetro '{parametro}' inválido: {razon} (valor recibido: {valor!r})"
        super().__init__(mensaje)
        self.parametro = parametro
        self.valor = valor
        self.razon = razon


# === Errores de Sistema ===


class SistemaError(PJNError):
    """Error interno del sistema."""

    pass


class ConfiguracionError(SistemaError):
    """Error en la configuración del sistema."""

    pass


class EstadoInvalido(SistemaError):
    """El sistema está en un estado inválido para la operación solicitada."""

    pass


# === Storage/Notificaciones ===


class StorageError(PJNError):
    """Error en operaciones de almacenamiento."""

    pass


class NotificacionError(PJNError):
    """Error al enviar notificación."""

    pass


__all__ = [
    # Base
    "PJNError",
    # Autenticación
    "AutenticacionError",
    "CredencialesFaltantes",
    "SesionInvalida",
    # Extracción
    "ExtraccionError",
    "ExpedienteNoEncontrado",
    "ActuacionesNoDisponibles",
    "TimeoutExtraccion",
    # Parsing
    "ParsingError",
    "FormatoInvalido",
    "DatosIncompletos",
    # Descarga
    "DescargaError",
    "ArchivoNoDisponible",
    "DescargaFallida",
    # Validación
    "ValidacionError",
    "ParametroInvalido",
    # Sistema
    "SistemaError",
    "ConfiguracionError",
    "EstadoInvalido",
    # Storage
    "StorageError",
    "NotificacionError",
]
