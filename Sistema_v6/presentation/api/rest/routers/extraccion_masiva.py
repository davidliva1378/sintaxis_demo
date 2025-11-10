"""
Router REST API para Extracción Masiva.

Endpoints:
- GET /listado: Obtiene listado completo de expedientes
- POST /procesar-seleccionados: Procesa expedientes seleccionados
- GET /sesion/{session_id}: Obtiene estado de sesión
"""

import os
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel

from Sistema_v6.extraccion_masiva import (
    ExtractorMasivo,
    GestorBatch,
    ConfigExtraccionMasiva,
    SesionExtraccion,
    ResumenExtraccion,
)


# ============================================================================
# Modelos de Request/Response
# ============================================================================

class ConfigExtraccionRequest(BaseModel):
    """Configuración para extracción."""
    headless: bool = True
    umbral_errores: int = 10
    timeout_pagina: int = 30000
    max_reintentos: int = 3


class ListadoRequest(BaseModel):
    """Request para extraer listado completo."""
    fecha_corte: Optional[str] = None
    config: Optional[ConfigExtraccionRequest] = None


class ListadoResponse(BaseModel):
    """Response con listado extraído."""
    session_id: str
    estado: str
    total: int
    listado_path: str
    comparacion: Optional[dict] = None
    mensaje: str


class ProcesarSeleccionadosRequest(BaseModel):
    """Request para procesar expedientes seleccionados."""
    numeros_expedientes: List[str]
    config: Optional[ConfigExtraccionRequest] = None


class ProcesarSeleccionadosResponse(BaseModel):
    """Response del procesamiento."""
    session_id: str
    resumen: dict


# ============================================================================
# Router
# ============================================================================

router = APIRouter(
    prefix="/extraccion-masiva",
    tags=["Extracción Masiva"]
)


# Estado global de sesiones (en producción usar Redis/DB)
_sesiones: dict[str, SesionExtraccion] = {}


def _get_credentials() -> tuple[str, str]:
    """Obtiene credenciales del PJN desde variables de entorno."""
    username = os.getenv("PJN_USER")
    password = os.getenv("PJN_PASSWORD")

    if not username or not password:
        raise HTTPException(
            status_code=500,
            detail="Credenciales PJN no configuradas. Configure PJN_USER y PJN_PASSWORD."
        )

    return username, password


@router.post("/listado", response_model=ListadoResponse)
async def extraer_listado_completo(
    request: ListadoRequest,
    background_tasks: BackgroundTasks,
) -> ListadoResponse:
    """
    Extrae el listado completo de expedientes del PJN.

    Flujo:
    1. Inicia extracción completa de todas las páginas
    2. Guarda JSON con metadata básica
    3. Compara automáticamente con JSON BASE si existe
    4. Retorna session_id y path al archivo

    Args:
        request: Configuración de extracción y fecha de corte opcional

    Returns:
        ListadoResponse con información de la extracción
    """
    try:
        # Obtener credenciales
        username, password = _get_credentials()

        # Crear configuración
        config = ConfigExtraccionMasiva(
            **request.config.dict()
        ) if request.config else ConfigExtraccionMasiva()

        # Crear extractor
        extractor = ExtractorMasivo(config=config)

        # Ejecutar extracción
        sesion = await extractor.extraer_listado_completo(
            username=username,
            password=password,
            fecha_corte=request.fecha_corte,
        )

        # Guardar sesión
        _sesiones[sesion.session_id] = sesion

        # Comparar con BASE (Tarea 1B)
        comparacion = None
        if sesion.listado_path:
            comparacion = extractor.comparar_con_base(sesion.listado_path)
            sesion.comparacion = comparacion

        return ListadoResponse(
            session_id=sesion.session_id,
            estado=sesion.estado,
            total=sesion.progreso_total,
            listado_path=sesion.listado_path or "",
            comparacion=comparacion,
            mensaje=sesion.mensaje,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en extracción masiva: {str(e)}"
        )


@router.post("/procesar-seleccionados", response_model=ProcesarSeleccionadosResponse)
async def procesar_expedientes_seleccionados(
    request: ProcesarSeleccionadosRequest,
) -> ProcesarSeleccionadosResponse:
    """
    Procesa SOLO los expedientes seleccionados por el usuario.

    Flujo:
    1. Recibe lista de números de expediente
    2. Procesa cada uno individualmente
    3. Actualiza estados en tiempo real
    4. Guarda solo los procesados exitosamente

    Args:
        request: Lista de números de expediente a procesar

    Returns:
        ProcesarSeleccionadosResponse con resumen del procesamiento
    """
    try:
        # Obtener credenciales
        username, password = _get_credentials()

        # Crear configuración
        config = ConfigExtraccionMasiva(
            **request.config.dict()
        ) if request.config else ConfigExtraccionMasiva()

        # Crear gestor
        gestor = GestorBatch(config=config)

        # Procesar seleccionados
        resumen = await gestor.procesar_seleccionados(
            numeros_expedientes=request.numeros_expedientes,
            username=username,
            password=password,
        )

        # Crear sesión para tracking
        from datetime import datetime
        from uuid import uuid4

        session_id = str(uuid4())
        sesion = SesionExtraccion(
            session_id=session_id,
            estado="completado",
            fase="procesamiento",
            tiempo_inicio=datetime.now().isoformat(),
            tiempo_fin=datetime.now().isoformat(),
            progreso_actual=resumen.exitosos,
            progreso_total=resumen.total,
            mensaje=f"Procesados {resumen.exitosos}/{resumen.total} expedientes",
        )

        _sesiones[session_id] = sesion

        return ProcesarSeleccionadosResponse(
            session_id=session_id,
            resumen=resumen.to_dict(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error procesando expedientes: {str(e)}"
        )


@router.get("/sesion/{session_id}", response_model=dict)
async def obtener_estado_sesion(session_id: str) -> dict:
    """
    Obtiene el estado de una sesión de extracción/procesamiento.

    Args:
        session_id: ID de la sesión

    Returns:
        Estado actual de la sesión
    """
    sesion = _sesiones.get(session_id)

    if not sesion:
        raise HTTPException(
            status_code=404,
            detail=f"Sesión {session_id} no encontrada"
        )

    return sesion.to_dict()


@router.get("/sesiones", response_model=List[dict])
async def listar_sesiones() -> List[dict]:
    """
    Lista todas las sesiones activas.

    Returns:
        Lista de sesiones
    """
    return [sesion.to_dict() for sesion in _sesiones.values()]
