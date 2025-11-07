"""Schemas para endpoints de monitoreo."""

from __future__ import annotations

from pydantic import BaseModel, Field


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
