"""Schemas para endpoints de monitoreo."""

from __future__ import annotations

from typing import Optional, Any
from pydantic import BaseModel, Field, field_validator, model_validator


class IniciarMonitoreoRequest(BaseModel):
    """Request para iniciar monitoreo de expedientes."""

    archivo_sistema: str = Field(description="Path del archivo JSON sistema")
    workspaces_dir: str | None = Field(None, description="Directorio base para workspaces")
    intervalo_minutos: int = Field(60, description="Intervalo de verificación en minutos")
    notificar: bool = Field(True, description="Enviar notificaciones de cambios")

    model_config = {"json_schema_extra": {"example": {"archivo_sistema": "datos/expedientes_sistema.json", "workspaces_dir": "datos/workspaces", "intervalo_minutos": 60, "notificar": True}}}


class CambioDetectadoResponse(BaseModel):
    """Response con información de un cambio detectado."""

    numero_expediente: str
    tipo_cambio: str = Field(description="Tipo de cambio: nueva_actuacion, actualizacion_estado, etc.")
    descripcion: str
    fecha_deteccion: str

    model_config = {"json_schema_extra": {"example": {"numero_expediente": "CNM 0001/2024", "tipo_cambio": "nueva_actuacion", "descripcion": "Nueva actuación: Providencia - Se corre vista", "fecha_deteccion": "2024-01-15T10:30:00"}}}


class MonitoreoResponse(BaseModel):
    """Response de monitoreo de expedientes."""

    success: bool
    total_expedientes: int = Field(description="Total de expedientes monitoreados")
    cambios_detectados: int = Field(description="Cantidad de cambios detectados")
    cambios: list[CambioDetectadoResponse] = Field(default_factory=list, description="Lista de cambios")
    error: str | None = None

    model_config = {"json_schema_extra": {"example": {"success": True, "total_expedientes": 25, "cambios_detectados": 3, "cambios": [{"numero_expediente": "CNM 0001/2024", "tipo_cambio": "nueva_actuacion", "descripcion": "Nueva actuación detectada", "fecha_deteccion": "2024-01-15T10:30:00"}]}}}


class EstadoMonitoreoResponse(BaseModel):
    """Response con el estado actual del scheduler de monitoreo."""

    activo: bool = Field(description="Si el scheduler está activo")
    ejecutando: bool = Field(description="Si hay una verificación en curso")
    intervalo_actual_minutos: int | None = Field(
        description="Intervalo actual de verificación en minutos"
    )
    es_horario_laboral: bool = Field(description="Si está en horario laboral")
    proxima_ejecucion: str | None = Field(description="Timestamp de próxima ejecución")
    jobs_programados: int = Field(description="Número de jobs programados")

    model_config = {
        "json_schema_extra": {
            "example": {
                "activo": True,
                "ejecutando": False,
                "intervalo_actual_minutos": 15,
                "es_horario_laboral": True,
                "proxima_ejecucion": "2025-11-17T19:00:00",
                "jobs_programados": 1,
            }
        }
    }


class StartSchedulerResponse(BaseModel):
    """Response al iniciar el scheduler."""

    success: bool
    mensaje: str
    intervalo_minutos: int | None = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "mensaje": "Scheduler iniciado correctamente",
                "intervalo_minutos": 15,
            }
        }
    }


class StopSchedulerResponse(BaseModel):
    """Response al detener el scheduler."""

    success: bool
    mensaje: str

    model_config = {
        "json_schema_extra": {
            "example": {"success": True, "mensaje": "Scheduler detenido correctamente"}
        }
    }


# ============================================================================
# NUEVOS SCHEMAS PARA CRUD DE MONITOREO
# ============================================================================


class ConfiguracionMonitoreoResponse(BaseModel):
    """Response con la configuración de monitoreo."""

    id: int
    usuario_id: int
    activo: bool
    frecuencia: str
    notificar_email: bool
    notificar_sistema: bool
    hora_inicio: str | None = None
    hora_fin: str | None = None
    dias_semana: list[int] | None = None
    ultima_ejecucion: str | None = None
    proxima_ejecucion: str | None = None
    created_at: str
    updated_at: str


class ActualizarConfiguracionRequest(BaseModel):
    """Request para actualizar configuración de monitoreo."""

    activo: bool | None = None
    frecuencia: str | None = Field(None, description="5min, 15min, 30min, 1hora, etc.")
    notificar_email: bool | None = None
    notificar_sistema: bool | None = None
    hora_inicio: str | None = Field(None, description="HH:MM formato")
    hora_fin: str | None = Field(None, description="HH:MM formato")
    dias_semana: list[int] | None = Field(None, description="Lista de días 0-6")

    @field_validator('frecuencia')
    @classmethod
    def validar_frecuencia(cls, v: str | None) -> str | None:
        """Valida que la frecuencia sea válida."""
        if v is None:
            return v
        frecuencias_validas = ['5min', '15min', '30min', '1hora', '2horas', '3horas', '4horas', '6horas', '12horas', '24horas']
        if v not in frecuencias_validas:
            raise ValueError(f'Frecuencia debe ser una de: {", ".join(frecuencias_validas)}')
        return v

    @field_validator('hora_inicio', 'hora_fin')
    @classmethod
    def validar_formato_hora(cls, v: str | None) -> str | None:
        """Valida que las horas tengan formato HH:MM."""
        if v is None:
            return v
        import re
        if not re.match(r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$', v):
            raise ValueError('Hora debe tener formato HH:MM (ej: 08:00, 18:30)')
        return v

    @field_validator('dias_semana')
    @classmethod
    def validar_dias_semana(cls, v: list[int] | None) -> list[int] | None:
        """Valida que los días de la semana sean válidos (0-6)."""
        if v is None:
            return v
        if not all(0 <= dia <= 6 for dia in v):
            raise ValueError('Los días de la semana deben estar entre 0 (domingo) y 6 (sábado)')
        if len(v) == 0:
            raise ValueError('Debe seleccionar al menos un día')
        return v

    @model_validator(mode='after')
    def validar_consistencia_horarios(self) -> 'ActualizarConfiguracionRequest':
        """Valida que hora_inicio y hora_fin no sean idénticas.

        Nota: Permite hora_inicio > hora_fin para soportar horarios que cruzan medianoche.
        Ejemplos válidos:
        - 08:00 - 18:00 (horario normal de 10 horas)
        - 22:00 - 06:00 (horario nocturno de 8 horas, cruza medianoche)
        - 06:00 - 05:59 (monitoreo casi 24 horas, cruza medianoche)

        Ejemplo inválido:
        - 10:00 - 10:00 (0 horas, sin sentido)
        """
        # Solo validar si ambos campos están presentes
        if self.hora_inicio is not None and self.hora_fin is not None:
            # Convertir a minutos para comparar
            inicio_partes = self.hora_inicio.split(':')
            fin_partes = self.hora_fin.split(':')

            minutos_inicio = int(inicio_partes[0]) * 60 + int(inicio_partes[1])
            minutos_fin = int(fin_partes[0]) * 60 + int(fin_partes[1])

            # Solo rechazar si son exactamente iguales (0 horas de monitoreo)
            if minutos_inicio == minutos_fin:
                raise ValueError('Las horas de inicio y fin no pueden ser idénticas')

        return self


class ExpedienteMonitoreado(BaseModel):
    """Datos de un expediente monitoreado."""

    id: int
    usuario_id: int
    expediente_numero: str
    expediente_caratula: str | None = None
    expediente_dependencia: str | None = None
    activo: bool
    ultima_verificacion: str | None = None
    ultima_actuacion_fecha: str | None = None
    ultima_actuacion_id: int | None = None
    total_cambios_detectados: int
    notas: str | None = None
    prioridad: str
    created_at: str
    updated_at: str


class AgregarExpedienteRequest(BaseModel):
    """Request para agregar expediente al monitoreo."""

    expediente_numero: str = Field(..., description="Número del expediente")
    expediente_caratula: str | None = None
    expediente_dependencia: str | None = None
    prioridad: str = Field("media", description="baja, media, alta")
    notas: str | None = None


class ActualizarExpedienteRequest(BaseModel):
    """Request para actualizar expediente monitoreado."""

    activo: bool | None = None
    prioridad: str | None = None
    notas: str | None = None


class ListaExpedientesResponse(BaseModel):
    """Response con lista paginada de expedientes monitoreados."""

    expedientes: list[ExpedienteMonitoreado]
    total: int
    pagina: int
    por_pagina: int
    total_paginas: int


class CambioDetectadoCompleto(BaseModel):
    """Cambio detectado con información completa."""

    id: int
    expediente_monitoreado_id: int
    expediente_numero: str
    expediente_caratula: str | None = None
    tipo_cambio: str
    descripcion: str
    detalles: dict[str, Any] | None = None
    notificado: bool
    leido: bool
    fecha_deteccion: str
    created_at: str


class ListaCambiosResponse(BaseModel):
    """Response con lista de cambios detectados."""

    cambios: list[CambioDetectadoCompleto]
    total_no_leidos: int
    pagina: int
    por_pagina: int


class EstadisticasMonitoreoResponse(BaseModel):
    """Response con estadísticas de monitoreo."""

    total_expedientes: int
    expedientes_activos: int
    expedientes_pausados: int
    cambios_hoy: int
    cambios_semana: int
    cambios_mes: int
    cambios_sin_leer: int
    ultima_ejecucion: str | None = None
    proxima_ejecucion: str | None = None


class MarcarLeidoResponse(BaseModel):
    """Response al marcar cambios como leídos."""

    success: bool
    cantidad_marcados: int = 0
