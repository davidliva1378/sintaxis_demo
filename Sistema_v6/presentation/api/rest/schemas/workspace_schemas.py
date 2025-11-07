"""Schemas para endpoints de workspaces."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CrearWorkspacesRequest(BaseModel):
    """Request para crear workspaces."""

    archivo_sistema: str = Field(description="Path del archivo JSON sistema")
    workspaces_dir: str | None = Field(None, description="Directorio base para workspaces")
    extraer_actuaciones: bool = Field(False, description="Extraer actuaciones al crear")
    descargar_archivos: bool = Field(False, description="Descargar archivos adjuntos")

    model_config = {"json_schema_extra": {"example": {"archivo_sistema": "datos/expedientes_sistema.json", "workspaces_dir": "datos/workspaces", "extraer_actuaciones": True, "descargar_archivos": False}}}


class CrearWorkspacesResponse(BaseModel):
    """Response de creación de workspaces."""

    success: bool
    total_expedientes: int = Field(description="Total de expedientes procesados")
    workspaces_creados: int = Field(description="Cantidad de workspaces creados")
    errores: int = Field(0, description="Cantidad de errores")
    error: str | None = None

    model_config = {"json_schema_extra": {"example": {"success": True, "total_expedientes": 25, "workspaces_creados": 25, "errores": 0}}}
