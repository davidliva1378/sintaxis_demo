"""Sistema v5 de extracción de datos del Portal PJN."""

# Exportar excepciones para fácil acceso
from .exceptions import (
    ActuacionesNoDisponibles,
    ArchivoNoDisponible,
    AutenticacionError,
    ConfiguracionError,
    CredencialesFaltantes,
    DatosIncompletos,
    DescargaError,
    DescargaFallida,
    EstadoInvalido,
    ExpedienteNoEncontrado,
    ExtraccionError,
    FormatoInvalido,
    ParametroInvalido,
    ParsingError,
    PJNError,
    SesionInvalida,
    SistemaError,
    TimeoutExtraccion,
    ValidacionError,
)

__all__ = [
    # Excepciones
    "PJNError",
    "AutenticacionError",
    "CredencialesFaltantes",
    "SesionInvalida",
    "ExtraccionError",
    "ExpedienteNoEncontrado",
    "ActuacionesNoDisponibles",
    "TimeoutExtraccion",
    "ParsingError",
    "FormatoInvalido",
    "DatosIncompletos",
    "DescargaError",
    "ArchivoNoDisponible",
    "DescargaFallida",
    "ValidacionError",
    "ParametroInvalido",
    "SistemaError",
    "ConfiguracionError",
    "EstadoInvalido",
]