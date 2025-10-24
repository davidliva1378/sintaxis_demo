"""Excepciones específicas del módulo de monitoreo.

Este módulo define una jerarquía clara de excepciones para el monitor,
permitiendo un manejo de errores más granular y específico.
"""

from __future__ import annotations


class MonitorError(Exception):
    """Excepción base para todos los errores del monitor.

    Todas las excepciones específicas del monitor heredan de esta clase.
    """
    pass


class ConfigurationError(MonitorError):
    """Error en la configuración del monitor.

    Se lanza cuando:
    - El archivo de configuración es inválido
    - Valores de configuración fuera de rango
    - Campos requeridos faltantes
    """
    pass


class StorageError(MonitorError):
    """Error relacionado con persistencia de datos.

    Se lanza cuando:
    - No se puede leer/escribir archivos JSON
    - Datos corruptos o con formato inválido
    - Problemas de permisos en filesystem
    """
    pass


class VerificationError(MonitorError):
    """Error durante la verificación de entradas/expedientes.

    Excepción base para errores durante el proceso de verificación.
    """
    pass


class AuthenticationError(VerificationError):
    """Error de autenticación con el portal PJN.

    Se lanza cuando:
    - Credenciales inválidas
    - Sesión expirada
    - Portal rechaza login
    """
    pass


class ExtractionError(VerificationError):
    """Error durante la extracción de datos del portal.

    Se lanza cuando:
    - Selectores no encontrados (cambios en el portal)
    - Timeout esperando elementos
    - Datos en formato inesperado
    """
    pass


class NetworkError(VerificationError):
    """Error de red al acceder al portal PJN.

    Se lanza cuando:
    - Portal no accesible (timeout, DNS, etc.)
    - Conexión interrumpida
    - Rate limiting
    """
    pass


class NotificationError(MonitorError):
    """Error al enviar notificaciones.

    Se lanza cuando:
    - Backend de notificación no disponible
    - Error al enviar notificación
    - Configuración de notificaciones inválida
    """
    pass


class SchedulerError(MonitorError):
    """Error en el scheduler.

    Se lanza cuando:
    - Error al programar jobs
    - Error al iniciar/detener scheduler
    - Problemas con el event loop
    """
    pass


# Excepciones de validación
class ValidationError(MonitorError):
    """Error de validación de datos.

    Se lanza cuando:
    - Datos de entrada inválidos
    - Validación de esquema falla
    - Constraints violados
    """
    pass


class IntervalError(ValidationError):
    """Error en validación de intervalos.

    Se lanza cuando:
    - Intervalos negativos o cero
    - Intervalos fuera de rango permitido
    """
    pass


class DateRangeError(ValidationError):
    """Error en validación de rangos de fechas.

    Se lanza cuando:
    - Formato de fecha inválido
    - Fecha desde > fecha hasta
    - Fechas fuera de rango lógico
    """
    pass


class WorkHoursError(ValidationError):
    """Error en validación de horarios laborales.

    Se lanza cuando:
    - Formato de hora inválido (no HH:MM)
    - Hora inicio >= hora fin
    - Días laborales inválidos
    """
    pass


__all__ = [
    # Base
    "MonitorError",

    # Configuración
    "ConfigurationError",

    # Storage
    "StorageError",

    # Verificación
    "VerificationError",
    "AuthenticationError",
    "ExtractionError",
    "NetworkError",

    # Notificaciones
    "NotificationError",

    # Scheduler
    "SchedulerError",

    # Validación
    "ValidationError",
    "IntervalError",
    "DateRangeError",
    "WorkHoursError",
]
