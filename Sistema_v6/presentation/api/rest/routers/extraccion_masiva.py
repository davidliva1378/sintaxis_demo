"""
Router REST API para Extracción Masiva.

Endpoints:
- GET /listado: Obtiene listado completo de expedientes
- POST /procesar-seleccionados: Procesa expedientes seleccionados
- GET /sesion/{session_id}: Obtiene estado de sesión
"""

import os
import traceback
import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, validator

logger = logging.getLogger(__name__)

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
    directorio_base: str = "./data/expedientes"
    # Opciones avanzadas de extracción
    detener_en_duplicado: bool = True
    omitir_duplicados: bool = True
    max_paginas: Optional[int] = None
    tiempo_maximo_segundos: Optional[int] = None

    @validator('max_paginas', 'tiempo_maximo_segundos')
    def validate_positive_or_none(cls, v):
        """Valida que los valores sean None o enteros positivos."""
        if v is not None and v <= 0:
            raise ValueError('Debe ser un valor positivo o None')
        return v


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


import asyncio
from fastapi import WebSocket, WebSocketDisconnect

# Estado global de tareas en background (para poder cancelarlas)
_tasks: dict[str, asyncio.Task] = {}

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
            # logger.info(f"📡 Callback recibido: session_id={session_id}, estado={sesion_actualizada.estado}")
            _sesiones[session_id] = sesion_actualizada
            # logger.info(f"✓ Sesión actualizada en _sesiones")

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

    except asyncio.CancelledError:
        logger.info(f"🛑 Extracción cancelada: {session_id}")
        if session_id in _sesiones:
            _sesiones[session_id].estado = "cancelado"
            _sesiones[session_id].mensaje = "Extracción cancelada por el usuario"
            # Asegurar que se guarde el estado final
            
    except Exception as e:
        # Capturar y loguear el traceback completo
        tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        logger.error(f"❌ Error completo en extracción masiva:\n{tb_str}")

        # Actualizar sesión con error
        if session_id in _sesiones:
            _sesiones[session_id].estado = "error"
            _sesiones[session_id].mensaje = f"Error en extracción: {str(e)}"
    finally:
        # Limpiar tarea del registro
        if session_id in _tasks:
            del _tasks[session_id]


@router.post("/listado", response_model=ListadoResponse)
async def extraer_listado_completo(
    request: ListadoRequest,
    # background_tasks: BackgroundTasks, # Ya no usamos BackgroundTasks de FastAPI para poder cancelar
) -> ListadoResponse:
    """
    Extrae el listado completo de expedientes del PJN.

    Flujo:
    1. Crea sesión inicial y la guarda en _sesiones
    2. Inicia extracción en background task (asyncio.create_task)
    3. Retorna inmediatamente con session_id
    4. El frontend hace polling a /sesion/{session_id} para obtener progreso
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

        # Ejecutar extracción en background (Task controlable)
        task = asyncio.create_task(
            _ejecutar_extraccion_background(
                session_id,
                username,
                password,
                config,
                request.fecha_corte,
            )
        )
        _tasks[session_id] = task

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


async def _ejecutar_procesamiento_background(
    session_id: str,
    numeros_expedientes: List[str],
    username: str,
    password: str,
    config: ConfigExtraccionMasiva,
    expediente_repo,
    monitoreo_service=None
):
    """Ejecuta el procesamiento de expedientes seleccionados en background."""
    try:
        # Obtener la sesión que ya está en _sesiones
        sesion = _sesiones.get(session_id)
        if not sesion:
            return

        # Callback para actualizar progreso en tiempo real
        def callback_progreso(actual: int, total: int, mensaje: str):
            if session_id in _sesiones:
                _sesiones[session_id].estado = "extrayendo"
                _sesiones[session_id].progreso_actual = actual
                _sesiones[session_id].progreso_total = total
                _sesiones[session_id].mensaje = mensaje

        # Cargar listado BASE para obtener carátulas
        from pathlib import Path
        import json

        caratulas_expedientes = {}
        # El listado base se guarda en data/extraccion_masiva/listados/listado_base.json
        # No en config.directorio_base (que es para los expedientes individuales)
        listado_base_path = Path("./data/extraccion_masiva/listados/listado_base.json")

        if listado_base_path.exists():
            try:
                with open(listado_base_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Crear diccionario numero -> caratula
                    expedientes = data.get("expedientes", [])
                    caratulas_expedientes = {
                        exp.get("numero"): exp.get("caratula")
                        for exp in expedientes
                        if exp.get("numero") and exp.get("caratula")
                    }
                    logger.info(f"📋 Cargadas {len(caratulas_expedientes)} carátulas desde listado BASE")
            except Exception as e:
                logger.warning(f"⚠️ No se pudo cargar listado BASE para carátulas: {e}")
        else:
            logger.warning(f"⚠️ No existe listado BASE en {listado_base_path}")

        # Crear gestor con callback y carátulas
        gestor = GestorBatch(
            config=config,
            on_progress=callback_progreso,
            expediente_repository=expediente_repo,
            caratulas=caratulas_expedientes,
            monitoreo_service=monitoreo_service
        )

        # Procesar seleccionados
        resumen = await gestor.procesar_seleccionados(
            numeros_expedientes=numeros_expedientes,
            username=username,
            password=password,
        )

        # Actualizar sesión con resultado final
        from datetime import datetime
        if session_id in _sesiones:
            _sesiones[session_id].estado = "completado"
            _sesiones[session_id].tiempo_fin = datetime.now().isoformat()
            _sesiones[session_id].progreso_actual = resumen.exitosos
            _sesiones[session_id].progreso_total = resumen.total
            _sesiones[session_id].mensaje = f"Procesados {resumen.exitosos}/{resumen.total} expedientes"
            _sesiones[session_id].archivos_descargados = resumen.archivos_descargados

    except asyncio.CancelledError:
        logger.info(f"🛑 Procesamiento cancelado: {session_id}")
        if session_id in _sesiones:
            _sesiones[session_id].estado = "cancelado"
            _sesiones[session_id].mensaje = "Procesamiento cancelado por el usuario"

    except Exception as e:
        # Capturar y loguear el traceback completo
        tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
        logger.error(f"❌ Error completo en procesamiento:\n{tb_str}")

        # Actualizar sesión con error
        if session_id in _sesiones:
            _sesiones[session_id].estado = "error"
            _sesiones[session_id].mensaje = f"Error en procesamiento: {str(e)}"
    finally:
        if session_id in _tasks:
            del _tasks[session_id]


@router.post("/procesar-seleccionados", response_model=ProcesarSeleccionadosResponse)
async def procesar_expedientes_seleccionados(
    request: ProcesarSeleccionadosRequest,
    # background_tasks: BackgroundTasks,
) -> ProcesarSeleccionadosResponse:
    """
    Procesa SOLO los expedientes seleccionados por el usuario.
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
        monitoreo_service = container.monitoreo_service

        # Crear sesión inicial
        from datetime import datetime
        from uuid import uuid4

        session_id = str(uuid4())
        sesion = SesionExtraccion(
            session_id=session_id,
            estado="iniciando",
            fase="procesamiento",
            tiempo_inicio=datetime.now().isoformat(),
            config=config.to_dict(),
            progreso_actual=0,
            progreso_total=len(request.numeros_expedientes),
            mensaje="Iniciando procesamiento de expedientes seleccionados..."
        )

        # Guardar sesión
        _sesiones[session_id] = sesion

        # Ejecutar procesamiento en background (Task controlable)
        task = asyncio.create_task(
            _ejecutar_procesamiento_background(
                session_id,
                request.numeros_expedientes,
                username,
                password,
                config,
                expediente_repo,
                monitoreo_service
            )
        )
        _tasks[session_id] = task

        return ProcesarSeleccionadosResponse(
            session_id=session_id,
            resumen={
                "total": len(request.numeros_expedientes),
                "exitosos": 0,
                "errores": 0,
                "omitidos": 0,
                "tiempo_total": 0,
                "errores_detalles": []
            },
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al iniciar procesamiento: {str(e)}"
        )


@router.post("/cancelar/{session_id}")
async def cancelar_sesion(session_id: str):
    """Cancela una sesión de extracción o procesamiento en curso."""
    if session_id not in _sesiones:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    
    if session_id in _tasks:
        task = _tasks[session_id]
        if not task.done():
            task.cancel()
            return {"mensaje": "Cancelación solicitada"}
    
    return {"mensaje": "La sesión no estaba activa o ya finalizó"}


@router.post("/pausar/{session_id}")
async def pausar_sesion(session_id: str):
    """Pausa una sesión (No implementado)."""
    raise HTTPException(status_code=501, detail="Pausa no implementada aún")


@router.post("/reanudar/{session_id}")
async def reanudar_sesion(session_id: str):
    """Reanuda una sesión (No implementado)."""
    raise HTTPException(status_code=501, detail="Reanudación no implementada aún")


@router.websocket("/sesion/{session_id}/ws")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """Endpoint WebSocket para monitoreo en tiempo real."""
    await websocket.accept()
    try:
        if session_id not in _sesiones:
            await websocket.close(code=4004, reason="Sesión no encontrada")
            return

        # Loop de envío de estado
        while True:
            sesion = _sesiones.get(session_id)
            if sesion:
                await websocket.send_json(sesion.to_dict())
                
                # Si terminó, cerrar conexión limpiamente
                if sesion.estado in ["completado", "error", "cancelado", "error_agotado"]:
                    # Esperar un poco para asegurar que el cliente reciba el último estado
                    await asyncio.sleep(1) 
                    await websocket.close(code=1000, reason="Proceso finalizado")
                    break
            else:
                await websocket.close(code=4004, reason="Sesión desapareció")
                break
            
            # Polling cada 500ms
            await asyncio.sleep(0.5)
            
    except WebSocketDisconnect:
        # Cliente se desconectó
        pass
    except Exception as e:
        logger.error(f"Error en WebSocket {session_id}: {e}")
        try:
            await websocket.close(code=1011, reason=f"Error interno: {str(e)}")
        except:
            pass


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


@router.get("/base", response_model=dict)
async def obtener_listado_base():
    """
    Obtener el listado base de expedientes (última extracción completa).
    """
    try:
        from infrastructure.config import get_settings
        settings = get_settings()
        
        # Directorio de listados
        # Usar settings.storage.base_path / "extraccion_masiva" / "listados"
        # Ojo: settings.storage.base_path apunta a "data"
        listados_dir = settings.storage.base_path / "extraccion_masiva" / "listados"
        
        # Instanciar extractor solo para usar sus métodos de carga
        extractor = ExtractorMasivo()
        
        # Buscar listado_base.json
        base_path = listados_dir / "listado_base.json"
        
        if not base_path.exists():
             # Fallback: buscar el más reciente
             if not listados_dir.exists():
                 raise HTTPException(status_code=404, detail="No hay directorio de listados")
                 
             archivos = sorted(listados_dir.glob("listado_*.json"), reverse=True)
             if not archivos:
                 raise HTTPException(status_code=404, detail="No hay listados disponibles")
             base_path = archivos[0]
             
        resultado = extractor.cargar_listado(str(base_path))
        
        # Verificar existencia en BD
        if resultado and "expedientes" in resultado:
            try:
                repo = get_container().expediente_repo
                numeros = [e["numero"] for e in resultado["expedientes"] if "numero" in e]
                
                # Usar el nuevo método optimizado
                existentes = await repo.verificar_existencia_masiva(numeros)
                
                # Marcar expedientes
                for exp in resultado["expedientes"]:
                    if exp.get("numero") in existentes:
                        exp["ya_agregado"] = True
            except Exception as e:
                logger.warning(f"Error verificando existencia en BD: {e}")
                # No fallar si la BD no está disponible, solo no marcar como agregados
        
        return resultado
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al obtener listado base: {e}")
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
