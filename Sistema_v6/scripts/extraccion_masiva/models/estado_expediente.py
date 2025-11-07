"""Enum para estados de expedientes en el sistema de extracción masiva."""

from enum import Enum


class EstadoExpediente(str, Enum):
    """Estados posibles de un expediente en el proceso de extracción masiva."""

    # Estados iniciales
    PENDIENTE_REVISION = "pendiente_revision"  # Nuevo expediente, necesita revisión
    MONITOREADO = "monitoreado"  # Expediente activo para seguimiento

    # Estados de procesamiento
    EN_PROCESO = "en_proceso"  # Actualmente siendo procesado
    COMPLETADO = "completado"  # Procesamiento exitoso
    ERROR = "error"  # Falló el procesamiento

    # Estados especiales
    OMITIDO = "omitido"  # Expediente omitido manualmente
    URGENTE = "urgente"  # Requiere atención prioritaria
    ARCHIVADO = "archivado"  # Expediente finalizado/archivado

    def __str__(self) -> str:
        return self.value

    @classmethod
    def estados_activos(cls) -> list["EstadoExpediente"]:
        """Retorna los estados considerados activos para procesamiento."""
        return [
            cls.PENDIENTE_REVISION,
            cls.MONITOREADO,
            cls.URGENTE,
            cls.ERROR  # Reintentar errores
        ]

    @classmethod
    def estados_finales(cls) -> list["EstadoExpediente"]:
        """Retorna los estados considerados finales."""
        return [
            cls.COMPLETADO,
            cls.OMITIDO,
            cls.ARCHIVADO
        ]
