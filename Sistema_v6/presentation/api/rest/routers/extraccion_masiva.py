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

from extraccion_masiva import (
    ExtractorMasivo,
    GestorBatch,
    ConfigExtraccionMasiva,
    SesionExtraccion,
    ResumenExtraccion,
)
from infrastructure.di_container import get_container


# ============================================================================
# Modelos de Request/Response
# ============================================================================

class ConfigExtraccionRequest(BaseModel):
    """Configuración para extracción."""
    headless: bool = True
    umbral_errores: int = 10
    timeout_pagina: int = 30000
    max_reintentos: int = 3
    procesar_con_pdf: bool = False
    incluir_historicas: bool = True
    min_utilidad: str = "MEDIA"
    directorio_base: str = "./Sistema_v6/data/expedientes"


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


async def _ejecutar_extraccion_background(
    session_id: str,
    username: str,
    password: str,
    config: ConfigExtraccionMasiva,
    fecha_corte: Optional[str] = None,
):
    """Ejecuta la extracción en background y actualiza la sesión en _sesiones."""
    try:
        extractor = ExtractorMasivo(config=config)

        # Obtener la sesión que ya está en _sesiones
        sesion = _sesiones.get(session_id)
        if not sesion:
            return

        # Callback para actualizar la sesión en tiempo real
        def actualizar_sesion(sesion_actualizada: SesionExtraccion):
            _sesiones[session_id] = sesion_actualizada

        # Ejecutar extracción pasando la sesión y el callback
        await extractor.extraer_listado_completo(
            username=username,
            password=password,
            fecha_corte=fecha_corte,
            sesion=sesion,
            callback_progreso=actualizar_sesion,
        )

        # Comparar con BASE si existe
        if sesion.listado_path:
            comparacion = extractor.comparar_con_base(sesion.listado_path)
            sesion.comparacion = comparacion
            _sesiones[session_id] = sesion

    except Exception as e:
        # Actualizar sesión con error
        if session_id in _sesiones:
            _sesiones[session_id].estado = "error"
            _sesiones[session_id].mensaje = f"Error en extracción: {str(e)}"


@router.post("/listado", response_model=ListadoResponse)
async def extraer_listado_completo(
    request: ListadoRequest,
    background_tasks: BackgroundTasks,
) -> ListadoResponse:
    """
    Extrae el listado completo de expedientes del PJN.

    Flujo:
    1. Crea sesión inicial y la guarda en _sesiones
    2. Inicia extracción en background task
    3. Retorna inmediatamente con session_id
    4. El frontend hace polling a /sesion/{session_id} para obtener progreso

    Args:
        request: Configuración de extracción y fecha de corte opcional

    Returns:
        ListadoResponse con session_id y estado inicial
    """
    try:
        # Obtener credenciales
        username, password = _get_credentials()

        # Crear configuración
        config = ConfigExtraccionMasiva(
            **request.config.dict()
        ) if request.config else ConfigExtraccionMasiva()

        # Crear sesión inicial
        from datetime import datetime
        from uuid import uuid4

        session_id = str(uuid4())
        sesion = SesionExtraccion(
            session_id=session_id,
            estado="iniciando",
            fase="listado",
            tiempo_inicio=datetime.now().isoformat(),
            config=config.to_dict(),
            progreso_actual=0,
            progreso_total=0,
            mensaje="Iniciando extracción masiva..."
        )

        # Guardar sesión
        _sesiones[session_id] = sesion

        # Ejecutar extracción en background
        background_tasks.add_task(
            _ejecutar_extraccion_background,
            session_id,
            username,
            password,
            config,
            request.fecha_corte,
        )

        return ListadoResponse(
            session_id=session_id,
            estado="iniciando",
            total=0,
            listado_path="",
            comparacion=None,
            mensaje="Extracción iniciada en background",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al iniciar extracción masiva: {str(e)}"
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

        # Obtener repositorio del DI Container
        container = get_container()
        expediente_repo = container.expediente_repo

        # Crear gestor con repositorio
        gestor = GestorBatch(
            config=config,
            expediente_repository=expediente_repo
        )

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


@router.get("/listado/{session_id}/expedientes", response_model=dict)
async def obtener_expedientes_listado(session_id: str) -> dict:
    """
    Obtiene los expedientes extraídos de un listado completado.

    Args:
        session_id: ID de la sesión

    Returns:
        Diccionario con los expedientes del listado
    """
    sesion = _sesiones.get(session_id)

    if not sesion:
        raise HTTPException(
            status_code=404,
            detail=f"Sesión {session_id} no encontrada"
        )

    if not sesion.listado_path:
        raise HTTPException(
            status_code=400,
            detail=f"La sesión {session_id} no tiene un listado asociado"
        )

    # Cargar el listado desde el archivo JSON
    extractor = ExtractorMasivo()

    try:
        listado_data = extractor.cargar_listado(sesion.listado_path)
        return listado_data
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail=f"Archivo de listado no encontrado: {sesion.listado_path}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al cargar listado: {str(e)}"
        )
