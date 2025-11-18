"""Schemas para endpoints de expedientes."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field


# === Request Schemas ===


class ExtraerExpedientesRequest(BaseModel):
    """Request para extraer expedientes del PJN."""

    usuario: str | None = Field(None, description="Usuario del PJN")
    contrasena: str | None = Field(None, description="Contraseña del PJN")
    headless: bool = Field(True, description="Ejecutar navegador en modo headless")
    guardar_en: str | None = Field(None, description="Path donde guardar el JSON")

    model_config = {"json_schema_extra": {"example": {"usuario": "20123456789", "contrasena": "password123", "headless": True, "guardar_en": "datos/expedientes_base.json"}}}


class FiltrarExpedientesRequest(BaseModel):
    """Request para filtrar expedientes."""

    numeros_seleccionados: list[str] = Field(description="Lista de números de expedientes")
    origen: str = Field(description="Path del archivo JSON origen (base)")
    destino: str | None = Field(None, description="Path del archivo JSON destino (sistema)")
    incluir_activos: bool = Field(False, description="Incluir expedientes activos automáticamente")
    dias_actividad: int = Field(30, description="Días para considerar un expediente activo")

    model_config = {"json_schema_extra": {"example": {"numeros_seleccionados": ["CNM 0001/2024", "CNM 0002/2024"], "origen": "datos/expedientes_base.json", "destino": "datos/expedientes_sistema.json", "incluir_activos": False, "dias_actividad": 30}}}


# === Response Schemas ===


class ExpedienteResponse(BaseModel):
    """Response con datos de un expediente."""

    numero: str
    dependencia: str
    caratula: str
    situacion: str | None = None
    ultima_actuacion: str | None = None

    model_config = {"json_schema_extra": {"example": {"numero": "CNM 0001/2024", "dependencia": "Juzgado Federal 1", "caratula": "CASO X C/ Y S/ MATERIA", "situacion": "En trámite", "ultima_actuacion": "2024-01-15"}}}


class ActuacionResponse(BaseModel):
    """Response con datos de una actuación."""

    indice: int
    oficina: str
    tipo: str | None = None
    fecha: str | None = None
    detalle: str | None = None
    foja: str | None = None
    firmante: str | None = None
    archivos: list[str] = Field(default_factory=list)

    model_config = {"json_schema_extra": {"example": {"indice": 1, "oficina": "Secretaría 1", "tipo": "Providencia", "fecha": "2024-01-15", "detalle": "Se corre vista...", "foja": "10 / 150", "firmante": "Juan Pérez", "archivos": ["documento_123.pdf"]}}}


class ExtraerExpedientesResponse(BaseModel):
    """Response de extracción de expedientes."""

    success: bool
    total: int = Field(description="Cantidad total de expedientes extraídos")
    archivo_guardado: str | None = Field(None, description="Path donde se guardó el archivo")
    error: str | None = None

    model_config = {"json_schema_extra": {"example": {"success": True, "total": 150, "archivo_guardado": "datos/expedientes_base.json"}}}


class FiltrarExpedientesResponse(BaseModel):
    """Response de filtrado de expedientes."""

    success: bool
    total_origen: int = Field(description="Cantidad de expedientes en el origen")
    total_filtrados: int = Field(description="Cantidad de expedientes filtrados")
    archivo_guardado: str | None = Field(None, description="Path donde se guardó el archivo")
    error: str | None = None

    model_config = {"json_schema_extra": {"example": {"success": True, "total_origen": 150, "total_filtrados": 25, "archivo_guardado": "datos/expedientes_sistema.json"}}}


class ListarExpedientesResponse(BaseModel):
    """Response para listar expedientes."""

    success: bool
    total: int
    expedientes: list[ExpedienteResponse]
    pagina: int = 1
    por_pagina: int = 20
    total_paginas: int = 1
    error: str | None = None

    model_config = {"json_schema_extra": {"example": {"success": True, "total": 2, "expedientes": [{"numero": "CNM 0001/2024", "dependencia": "Juzgado Federal 1", "caratula": "CASO X C/ Y S/ MATERIA", "situacion": "En trámite", "ultima_actuacion": "2024-01-15"}], "pagina": 1, "por_pagina": 20, "total_paginas": 1}}}
