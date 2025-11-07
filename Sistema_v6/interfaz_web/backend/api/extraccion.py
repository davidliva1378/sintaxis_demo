"""
API REST para extracción masiva de expedientes.

Este módulo proporciona endpoints REST y WebSocket para:
- Iniciar extracciones masivas
- Monitorear progreso en tiempo real
- Pausar/reanudar/cancelar extracciones
- Descargar reportes generados
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from Sistema_v6.extraccion_masiva import (
    ExtractorMasivo,
    ConfigExtraccionMasiva,
    exportar_json,
    exportar_excel,
)

logger = logging.getLogger(__name__)

# Router para los endpoints de extracción
router = APIRouter(prefix="/api/extraccion/masiva", tags=["extraccion_masiva"])

# ==================== Modelos Pydantic ====================

class ConfiguracionExtraccion(BaseModel):
    """Configuración para iniciar una extracción masiva."""
    fecha_desde: Optional[str] = Field(None, description="Fecha desde (YYYY-MM-DD)")
    fecha_hasta: Optional[str] = Field(None, description="Fecha hasta (YYYY-MM-DD)")
    estados: Optional[List[str]] = Field(None, description="Estados a filtrar")
    dependencias: Optional[List[str]] = Field(None, description="Dependencias a filtrar")
    umbral_errores: int = Field(10, description="Máximo de errores consecutivos")
    headless: bool = Field(True, description="Ejecutar navegador en modo headless")
    exportar_formatos: List[str] = Field(["json"], description="Formatos: json, excel, csv")


class RespuestaInicio(BaseModel):
    """Respuesta al iniciar una extracción."""
    session_id: str
    mensaje: str
    estado: str


class ProgresoExtraccion(BaseModel):
    """Estado del progreso de una extracción."""
    session_id: str
    estado: str
    fase: str
    progreso_actual: int
    progreso_total: int
    porcentaje: float
    mensaje: str
    errores: int
    tiempo_transcurrido: float
    tiempo_estimado: Optional[float]
    velocidad: Optional[float]


class ResumenExtraccion(BaseModel):
    """Resumen final de una extracción."""
    session_id: str
    estado: str
    total: int
    exitosos: int
    errores: int
    omitidos: int
    duracion_segundos: float
    velocidad_promedio: float
    archivos_generados: List[str]


# ==================== Gestión de Sesiones ====================

class GestorSesiones:
    """Gestor de sesiones de extracción activas."""

    def __init__(self):
        self.sesiones: Dict[str, Dict] = {}
        self.websockets: Dict[str, Set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def crear_sesion(self, session_id: str, config: ConfiguracionExtraccion) -> Dict:
        """Crear una nueva sesión de extracción."""
        async with self.lock:
            sesion = {
                "session_id": session_id,
                "config": config.dict(),
                "estado": "iniciando",
                "fase": "configuracion",
                "progreso_actual": 0,
                "progreso_total": 0,
                "porcentaje": 0.0,
                "mensaje": "Iniciando extracción...",
                "errores": 0,
                "tiempo_inicio": datetime.now().isoformat(),
                "tiempo_fin": None,
                "resultados": None,
                "archivos": [],
                "extractor": None,
                "task": None,
            }
            self.sesiones[session_id] = sesion
            self.websockets[session_id] = set()
            return sesion

    async def actualizar_progreso(self, session_id: str, **kwargs):
        """Actualizar el progreso de una sesión."""
        async with self.lock:
            if session_id in self.sesiones:
                self.sesiones[session_id].update(kwargs)

                # Calcular tiempo transcurrido
                inicio = datetime.fromisoformat(self.sesiones[session_id]["tiempo_inicio"])
                transcurrido = (datetime.now() - inicio).total_seconds()
                self.sesiones[session_id]["tiempo_transcurrido"] = transcurrido

                # Enviar actualización por WebSocket
                await self._broadcast(session_id, self.sesiones[session_id])

    async def obtener_sesion(self, session_id: str) -> Optional[Dict]:
        """Obtener información de una sesión."""
        async with self.lock:
            return self.sesiones.get(session_id)

    async def finalizar_sesion(self, session_id: str, resultados: Dict):
        """Finalizar una sesión con resultados."""
        async with self.lock:
            if session_id in self.sesiones:
                self.sesiones[session_id].update({
                    "estado": "completado",
                    "tiempo_fin": datetime.now().isoformat(),
                    "resultados": resultados,
                })
                await self._broadcast(session_id, self.sesiones[session_id])

    async def marcar_error(self, session_id: str, error: str):
        """Marcar una sesión como error."""
        async with self.lock:
            if session_id in self.sesiones:
                self.sesiones[session_id].update({
                    "estado": "error",
                    "mensaje": f"Error: {error}",
                    "tiempo_fin": datetime.now().isoformat(),
                })
                await self._broadcast(session_id, self.sesiones[session_id])

    async def registrar_websocket(self, session_id: str, websocket: WebSocket):
        """Registrar un WebSocket para una sesión."""
        async with self.lock:
            if session_id not in self.websockets:
                self.websockets[session_id] = set()
            self.websockets[session_id].add(websocket)

    async def desregistrar_websocket(self, session_id: str, websocket: WebSocket):
        """Desregistrar un WebSocket."""
        async with self.lock:
            if session_id in self.websockets:
                self.websockets[session_id].discard(websocket)

    async def _broadcast(self, session_id: str, data: Dict):
        """Enviar datos a todos los WebSockets de una sesión."""
        if session_id in self.websockets:
            # Crear copia para evitar problemas con modificaciones concurrentes
            websockets_copy = self.websockets[session_id].copy()

            for websocket in websockets_copy:
                try:
                    # Filtrar datos para enviar solo lo necesario
                    mensaje = {
                        "session_id": data["session_id"],
                        "estado": data["estado"],
                        "fase": data["fase"],
                        "progreso_actual": data["progreso_actual"],
                        "progreso_total": data["progreso_total"],
                        "porcentaje": data["porcentaje"],
                        "mensaje": data["mensaje"],
                        "errores": data["errores"],
                        "tiempo_transcurrido": data.get("tiempo_transcurrido", 0),
                    }
                    await websocket.send_json(mensaje)
                except Exception as e:
                    logger.error(f"Error enviando a WebSocket: {e}")
                    await self.desregistrar_websocket(session_id, websocket)


# Instancia global del gestor
gestor = GestorSesiones()


# ==================== Funciones de Callbacks ====================

def crear_callbacks(session_id: str):
    """Crear callbacks para conectar el extractor con el gestor de sesiones."""

    async def on_inicio_listado():
        await gestor.actualizar_progreso(
            session_id,
            estado="en_progreso",
            fase="listado",
            mensaje="Extrayendo listado de expedientes..."
        )

    async def on_progreso_listado(pagina_actual: int, total_paginas: int):
        porcentaje = (pagina_actual / total_paginas * 50) if total_paginas > 0 else 0
        await gestor.actualizar_progreso(
            session_id,
            progreso_actual=pagina_actual,
            progreso_total=total_paginas,
            porcentaje=porcentaje,
            mensaje=f"Extrayendo página {pagina_actual} de {total_paginas}..."
        )

    async def on_fin_listado(expedientes: List[Dict]):
        await gestor.actualizar_progreso(
            session_id,
            mensaje=f"Listado completo: {len(expedientes)} expedientes encontrados",
            porcentaje=50.0
        )

    async def on_inicio_batch(total: int):
        await gestor.actualizar_progreso(
            session_id,
            fase="procesamiento",
            progreso_total=total,
            mensaje=f"Iniciando procesamiento de {total} expedientes..."
        )

    async def on_progreso_batch(idx: int, total: int, resultado: Dict):
        porcentaje = 50 + (idx / total * 50) if total > 0 else 50
        await gestor.actualizar_progreso(
            session_id,
            progreso_actual=idx + 1,
            progreso_total=total,
            porcentaje=porcentaje,
            mensaje=f"Procesando {idx + 1}/{total}: {resultado.get('numero', 'N/A')}"
        )

    async def on_fin_batch(resumen: Dict):
        await gestor.actualizar_progreso(
            session_id,
            mensaje=f"Procesamiento completo: {resumen.get('exitosos', 0)} exitosos, {resumen.get('errores', 0)} errores",
            porcentaje=100.0
        )

    async def on_error(error: str):
        sesion = await gestor.obtener_sesion(session_id)
        if sesion:
            errores = sesion.get("errores", 0) + 1
            await gestor.actualizar_progreso(
                session_id,
                errores=errores,
                mensaje=f"Error: {error}"
            )

    return {
        "inicio_listado": on_inicio_listado,
        "progreso_listado": on_progreso_listado,
        "fin_listado": on_fin_listado,
        "inicio_batch": on_inicio_batch,
        "progreso_batch": on_progreso_batch,
        "fin_batch": on_fin_batch,
        "error": on_error,
    }


# ==================== Tarea de Extracción en Background ====================

async def ejecutar_extraccion_background(session_id: str, config: ConfiguracionExtraccion):
    """Ejecutar extracción en background."""
    try:
        # Crear configuración del extractor
        config_extractor = ConfigExtraccionMasiva(
            fecha_desde=config.fecha_desde,
            fecha_hasta=config.fecha_hasta,
            estados=config.estados,
            dependencias=config.dependencias,
            umbral_errores=config.umbral_errores,
            headless=config.headless,
        )

        # Crear extractor con callbacks
        callbacks = crear_callbacks(session_id)
        extractor = ExtractorMasivo(config_extractor, callbacks=callbacks)

        # Guardar extractor en la sesión para poder cancelarlo
        await gestor.actualizar_progreso(session_id, extractor=extractor)

        # Ejecutar extracción
        logger.info(f"Iniciando extracción para sesión {session_id}")
        resultado = await extractor.ejecutar_extraccion_completa()

        # Exportar resultados
        archivos = []
        base_path = extractor.session_dir

        for formato in config.exportar_formatos:
            try:
                if formato == "json":
                    archivo = exportar_json(resultado, base_path / "reporte.json")
                    archivos.append(str(archivo))
                elif formato == "excel":
                    archivo = exportar_excel(resultado, base_path / "reporte.xlsx")
                    archivos.append(str(archivo))
                # CSV se exporta automáticamente en ejecutar_extraccion_completa
            except Exception as e:
                logger.error(f"Error exportando {formato}: {e}")

        # Actualizar sesión con archivos generados
        await gestor.actualizar_progreso(session_id, archivos=archivos)

        # Finalizar sesión
        await gestor.finalizar_sesion(session_id, resultado)

        logger.info(f"Extracción completada para sesión {session_id}")

    except Exception as e:
        logger.error(f"Error en extracción {session_id}: {e}", exc_info=True)
        await gestor.marcar_error(session_id, str(e))


# ==================== Endpoints REST ====================

@router.post("/iniciar", response_model=RespuestaInicio)
async def iniciar_extraccion(config: ConfiguracionExtraccion, background_tasks: BackgroundTasks):
    """
    Iniciar una nueva extracción masiva.

    Args:
        config: Configuración de la extracción
        background_tasks: Gestor de tareas en background de FastAPI

    Returns:
        RespuestaInicio con session_id y estado
    """
    # Generar session_id único
    session_id = f"ext_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Crear sesión
    await gestor.crear_sesion(session_id, config)

    # Ejecutar extracción en background
    background_tasks.add_task(ejecutar_extraccion_background, session_id, config)

    logger.info(f"Extracción iniciada: {session_id}")

    return RespuestaInicio(
        session_id=session_id,
        mensaje="Extracción iniciada correctamente",
        estado="iniciando"
    )


@router.get("/progreso/{session_id}", response_model=ProgresoExtraccion)
async def obtener_progreso(session_id: str):
    """
    Obtener el progreso actual de una extracción.

    Args:
        session_id: ID de la sesión

    Returns:
        ProgresoExtraccion con estado actual
    """
    sesion = await gestor.obtener_sesion(session_id)

    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    # Calcular tiempo transcurrido
    inicio = datetime.fromisoformat(sesion["tiempo_inicio"])
    transcurrido = (datetime.now() - inicio).total_seconds()

    # Estimar tiempo restante
    tiempo_estimado = None
    velocidad = None

    if sesion["progreso_actual"] > 0 and sesion["progreso_total"] > 0:
        velocidad = sesion["progreso_actual"] / transcurrido if transcurrido > 0 else 0
        if velocidad > 0:
            restante = sesion["progreso_total"] - sesion["progreso_actual"]
            tiempo_estimado = restante / velocidad

    return ProgresoExtraccion(
        session_id=session_id,
        estado=sesion["estado"],
        fase=sesion["fase"],
        progreso_actual=sesion["progreso_actual"],
        progreso_total=sesion["progreso_total"],
        porcentaje=sesion["porcentaje"],
        mensaje=sesion["mensaje"],
        errores=sesion["errores"],
        tiempo_transcurrido=transcurrido,
        tiempo_estimado=tiempo_estimado,
        velocidad=velocidad
    )


@router.post("/cancelar/{session_id}")
async def cancelar_extraccion(session_id: str):
    """
    Cancelar una extracción en progreso.

    Args:
        session_id: ID de la sesión

    Returns:
        Mensaje de confirmación
    """
    sesion = await gestor.obtener_sesion(session_id)

    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    if sesion["estado"] not in ["en_progreso", "pausado"]:
        raise HTTPException(status_code=400, detail="La sesión no se puede cancelar")

    # Cancelar extractor si existe
    extractor = sesion.get("extractor")
    if extractor:
        extractor.cancelar()

    # Actualizar estado
    await gestor.actualizar_progreso(
        session_id,
        estado="cancelado",
        mensaje="Extracción cancelada por el usuario",
        tiempo_fin=datetime.now().isoformat()
    )

    logger.info(f"Extracción cancelada: {session_id}")

    return {"mensaje": "Extracción cancelada", "session_id": session_id}


@router.post("/pausar/{session_id}")
async def pausar_extraccion(session_id: str):
    """
    Pausar una extracción en progreso.

    Args:
        session_id: ID de la sesión

    Returns:
        Mensaje de confirmación
    """
    sesion = await gestor.obtener_sesion(session_id)

    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    if sesion["estado"] != "en_progreso":
        raise HTTPException(status_code=400, detail="La sesión no está en progreso")

    # Pausar extractor
    extractor = sesion.get("extractor")
    if extractor and hasattr(extractor, "gestor_batch"):
        extractor.gestor_batch.pausar()

    await gestor.actualizar_progreso(session_id, estado="pausado", mensaje="Extracción pausada")

    logger.info(f"Extracción pausada: {session_id}")

    return {"mensaje": "Extracción pausada", "session_id": session_id}


@router.post("/reanudar/{session_id}")
async def reanudar_extraccion(session_id: str):
    """
    Reanudar una extracción pausada.

    Args:
        session_id: ID de la sesión

    Returns:
        Mensaje de confirmación
    """
    sesion = await gestor.obtener_sesion(session_id)

    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    if sesion["estado"] != "pausado":
        raise HTTPException(status_code=400, detail="La sesión no está pausada")

    # Reanudar extractor
    extractor = sesion.get("extractor")
    if extractor and hasattr(extractor, "gestor_batch"):
        extractor.gestor_batch.reanudar()

    await gestor.actualizar_progreso(session_id, estado="en_progreso", mensaje="Extracción reanudada")

    logger.info(f"Extracción reanudada: {session_id}")

    return {"mensaje": "Extracción reanudada", "session_id": session_id}


@router.get("/descargar/{session_id}/{formato}")
async def descargar_reporte(session_id: str, formato: str):
    """
    Descargar reporte de una extracción finalizada.

    Args:
        session_id: ID de la sesión
        formato: Formato del reporte (json, excel, csv)

    Returns:
        Archivo del reporte
    """
    sesion = await gestor.obtener_sesion(session_id)

    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    if sesion["estado"] != "completado":
        raise HTTPException(status_code=400, detail="La extracción no ha finalizado")

    # Buscar archivo según formato
    from Sistema_v6.configuracion.config import Config
    base_path = Config.EXTRACCION_MASIVA_DIR / session_id

    archivos_map = {
        "json": base_path / "reporte.json",
        "excel": base_path / "reporte.xlsx",
        "csv": base_path / "resultados.csv",
        "html": base_path / "reporte.html",
    }

    if formato not in archivos_map:
        raise HTTPException(status_code=400, detail="Formato no válido")

    archivo = archivos_map[formato]

    if not archivo.exists():
        raise HTTPException(status_code=404, detail=f"Archivo {formato} no encontrado")

    return FileResponse(
        path=str(archivo),
        filename=f"extraccion_{session_id}.{formato}",
        media_type="application/octet-stream"
    )


@router.get("/resumen/{session_id}", response_model=ResumenExtraccion)
async def obtener_resumen(session_id: str):
    """
    Obtener resumen final de una extracción completada.

    Args:
        session_id: ID de la sesión

    Returns:
        ResumenExtraccion con estadísticas finales
    """
    sesion = await gestor.obtener_sesion(session_id)

    if not sesion:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")

    if sesion["estado"] != "completado":
        raise HTTPException(status_code=400, detail="La extracción no ha finalizado")

    resultados = sesion.get("resultados", {})
    resumen_batch = resultados.get("resultado", {})

    return ResumenExtraccion(
        session_id=session_id,
        estado=sesion["estado"],
        total=resumen_batch.get("total", 0),
        exitosos=resumen_batch.get("exitosos", 0),
        errores=resumen_batch.get("errores", 0),
        omitidos=resumen_batch.get("omitidos", 0),
        duracion_segundos=resumen_batch.get("duracion_segundos", 0),
        velocidad_promedio=resumen_batch.get("velocidad_promedio", 0),
        archivos_generados=sesion.get("archivos", [])
    )


# ==================== WebSocket ====================

@router.websocket("/ws/{session_id}")
async def websocket_progreso(websocket: WebSocket, session_id: str):
    """
    WebSocket para recibir actualizaciones de progreso en tiempo real.

    Args:
        websocket: Conexión WebSocket
        session_id: ID de la sesión a monitorear
    """
    await websocket.accept()

    # Verificar que la sesión existe
    sesion = await gestor.obtener_sesion(session_id)
    if not sesion:
        await websocket.send_json({"error": "Sesión no encontrada"})
        await websocket.close()
        return

    # Registrar WebSocket
    await gestor.registrar_websocket(session_id, websocket)

    try:
        # Enviar estado actual inmediatamente
        await websocket.send_json({
            "session_id": sesion["session_id"],
            "estado": sesion["estado"],
            "fase": sesion["fase"],
            "progreso_actual": sesion["progreso_actual"],
            "progreso_total": sesion["progreso_total"],
            "porcentaje": sesion["porcentaje"],
            "mensaje": sesion["mensaje"],
            "errores": sesion["errores"],
        })

        # Mantener conexión abierta
        while True:
            # Esperar mensajes del cliente (ping/pong)
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                # Echo del mensaje recibido (para keep-alive)
                if data == "ping":
                    await websocket.send_text("pong")
            except asyncio.TimeoutError:
                # Timeout normal, continuar
                pass

            # Verificar si la sesión terminó
            sesion_actual = await gestor.obtener_sesion(session_id)
            if sesion_actual and sesion_actual["estado"] in ["completado", "cancelado", "error"]:
                # Enviar estado final
                await websocket.send_json({
                    "session_id": sesion_actual["session_id"],
                    "estado": sesion_actual["estado"],
                    "mensaje": sesion_actual["mensaje"],
                })
                break

    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado para sesión {session_id}")
    except Exception as e:
        logger.error(f"Error en WebSocket {session_id}: {e}")
    finally:
        # Desregistrar WebSocket
        await gestor.desregistrar_websocket(session_id, websocket)
