"""
Router REST para Tools del sistema.

Expone todas las herramientas de ToolsService como endpoints REST.
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime

from application.services.ia.tools_service import ToolsService

router = APIRouter(prefix="/tools", tags=["tools"])

# Instancia del servicio
tools_service = ToolsService()


# ============================================================
# EXPEDIENTES
# ============================================================

@router.get("/estadisticas-sistema")
async def get_estadisticas_sistema():
    """Obtiene estadisticas generales del sistema."""
    try:
        return tools_service.estadisticas_sistema()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/contar-expedientes")
async def contar_expedientes(
    estado: Optional[str] = Query(None, description="Estado: activo, pausado, archivado"),
    dependencia: Optional[str] = Query(None, description="Juzgado/dependencia"),
    desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)")
):
    """Cuenta expedientes con filtros."""
    try:
        desde_dt = datetime.fromisoformat(desde) if desde else None
        hasta_dt = datetime.fromisoformat(hasta) if hasta else None
        return tools_service.contar_expedientes(estado, dependencia, desde_dt, hasta_dt)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expedientes")
async def listar_expedientes(
    estado: Optional[str] = Query(None),
    dependencia: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    limite: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    orden: str = Query("updated_at DESC")
):
    """Lista expedientes con paginacion y filtros."""
    try:
        return tools_service.listar_expedientes(
            estado, dependencia, prioridad, limite, offset, orden
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expediente/{numero}")
async def obtener_expediente(numero: str):
    """Obtiene detalle de un expediente."""
    try:
        result = tools_service.obtener_expediente(numero)
        if not result:
            raise HTTPException(status_code=404, detail=f"Expediente {numero} no encontrado")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buscar-expedientes")
async def buscar_expedientes(
    texto: str = Query(..., min_length=2),
    limite: int = Query(20, le=100)
):
    """Busca expedientes por texto."""
    try:
        return tools_service.buscar_expedientes(texto, limite=limite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expedientes-por-dependencia")
async def expedientes_por_dependencia():
    """Agrupa expedientes por dependencia."""
    try:
        return tools_service.expedientes_por_dependencia()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/expedientes-recientes")
async def expedientes_recientes(
    dias: int = Query(7, ge=1, le=90),
    limite: int = Query(20, le=100)
):
    """Expedientes con actividad reciente."""
    try:
        return tools_service.expedientes_recientes(dias, limite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ACTUACIONES
# ============================================================

@router.get("/actuaciones/{expediente_numero}")
async def listar_actuaciones(
    expediente_numero: str,
    tipo: Optional[str] = Query(None),
    desde: Optional[str] = Query(None),
    hasta: Optional[str] = Query(None),
    limite: int = Query(50, le=200)
):
    """Lista actuaciones de un expediente."""
    try:
        desde_dt = datetime.fromisoformat(desde) if desde else None
        hasta_dt = datetime.fromisoformat(hasta) if hasta else None
        return tools_service.listar_actuaciones(
            expediente_numero, tipo, desde_dt, hasta_dt, limite
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buscar-actuaciones")
async def buscar_actuaciones(
    texto: str = Query(..., min_length=2),
    expediente_numero: Optional[str] = Query(None),
    limite: int = Query(20, le=100)
):
    """Busca actuaciones por texto."""
    try:
        return tools_service.buscar_actuaciones(texto, expediente_numero, limite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actuaciones-por-tipo")
async def actuaciones_por_tipo(
    expediente_numero: Optional[str] = Query(None)
):
    """Agrupa actuaciones por tipo."""
    try:
        return tools_service.actuaciones_por_tipo(expediente_numero)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actuaciones-con-texto/{expediente_numero}")
async def actuaciones_con_texto(
    expediente_numero: str,
    limite: int = Query(20, le=100)
):
    """Actuaciones que tienen texto extraido."""
    try:
        return tools_service.actuaciones_con_texto(expediente_numero, limite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/texto-actuacion/{actuacion_id}")
async def obtener_texto_actuacion(actuacion_id: str):
    """Obtiene texto de una actuacion."""
    try:
        result = tools_service.obtener_texto_actuacion(actuacion_id)
        if not result:
            raise HTTPException(status_code=404, detail="Actuacion no encontrada")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# VENCIMIENTOS
# ============================================================

@router.get("/vencimientos-pendientes")
async def vencimientos_pendientes(
    expediente_numero: Optional[str] = Query(None),
    limite: int = Query(50, le=200)
):
    """Lista vencimientos pendientes."""
    try:
        return tools_service.vencimientos_pendientes(expediente_numero, limite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vencimientos-urgentes")
async def vencimientos_urgentes(
    dias: int = Query(7, ge=1, le=30),
    limite: int = Query(20, le=100)
):
    """Vencimientos proximos a vencer."""
    try:
        return tools_service.vencimientos_urgentes(dias, limite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vencimientos-vencidos")
async def vencimientos_vencidos(
    expediente_numero: Optional[str] = Query(None),
    limite: int = Query(20, le=100)
):
    """Vencimientos ya pasados."""
    try:
        return tools_service.vencimientos_vencidos(expediente_numero, limite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proximos-vencimientos")
async def proximos_vencimientos(
    dias: int = Query(30, ge=1, le=90),
    agrupar_por: str = Query("semana", regex="^(dia|semana|mes)$")
):
    """Calendario de vencimientos."""
    try:
        return tools_service.proximos_vencimientos(dias, agrupar_por)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resumen-vencimientos")
async def resumen_vencimientos():
    """Estadisticas de vencimientos."""
    try:
        return tools_service.resumen_vencimientos()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ENTIDADES NER
# ============================================================

@router.get("/entidades/{expediente_numero}")
async def listar_entidades(
    expediente_numero: str,
    tipo: Optional[str] = Query(None),
    limite: int = Query(100, le=500)
):
    """Lista entidades de un expediente."""
    try:
        return tools_service.listar_entidades(expediente_numero, tipo, limite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/buscar-entidades")
async def buscar_entidades(
    valor: str = Query(..., min_length=2),
    tipo: Optional[str] = Query(None),
    limite: int = Query(20, le=100)
):
    """Busca entidades por valor."""
    try:
        return tools_service.buscar_entidades(valor, tipo, limite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/entidades-por-tipo")
async def entidades_por_tipo(
    expediente_numero: Optional[str] = Query(None)
):
    """Agrupa entidades por tipo."""
    try:
        return tools_service.entidades_por_tipo(expediente_numero)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estadisticas-entidades")
async def estadisticas_entidades():
    """Estadisticas de entidades."""
    try:
        return tools_service.estadisticas_entidades()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/personas/{expediente_numero}")
async def personas_expediente(
    expediente_numero: str,
    score_minimo: float = Query(0.5, ge=0, le=1)
):
    """Personas mencionadas en expediente."""
    try:
        return tools_service.personas_expediente(expediente_numero, score_minimo)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ESTADISTICAS
# ============================================================

@router.get("/estadisticas-expediente/{expediente_numero}")
async def estadisticas_expediente(expediente_numero: str):
    """Estadisticas de un expediente."""
    try:
        result = tools_service.estadisticas_expediente(expediente_numero)
        if not result:
            raise HTTPException(status_code=404, detail="Expediente no encontrado")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/estadisticas-procesamiento")
async def estadisticas_procesamiento():
    """Estadisticas de procesamiento IA."""
    try:
        return tools_service.estadisticas_procesamiento()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actividad-reciente")
async def actividad_reciente(
    dias: int = Query(7, ge=1, le=30),
    limite: int = Query(50, le=200)
):
    """Timeline de actividad."""
    try:
        return tools_service.actividad_reciente(dias, limite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# ANALISIS
# ============================================================

@router.get("/duplicados")
async def duplicados_detectados(
    expediente_numero: Optional[str] = Query(None),
    limite: int = Query(20, le=100)
):
    """Lista duplicados detectados."""
    try:
        return tools_service.duplicados_detectados(expediente_numero, limite)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/clasificacion-ia/{expediente_numero}")
async def clasificacion_ia(expediente_numero: str):
    """Resultados de clasificacion IA."""
    try:
        return tools_service.clasificacion_ia(expediente_numero)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/actuaciones-importantes")
async def actuaciones_importantes(
    expediente_numero: Optional[str] = Query(None),
    utilidad_minima: str = Query("alta", regex="^(alta|media)$"),
    limite: int = Query(20, le=100)
):
    """Actuaciones de alta utilidad."""
    try:
        return tools_service.actuaciones_importantes(
            expediente_numero, utilidad_minima, limite
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/resumen-expediente/{expediente_numero}")
async def resumen_expediente(
    expediente_numero: str,
    incluir_actuaciones: bool = Query(True),
    incluir_vencimientos: bool = Query(True),
    incluir_entidades: bool = Query(True)
):
    """Resumen completo de expediente."""
    try:
        result = tools_service.resumen_expediente(
            expediente_numero,
            incluir_actuaciones,
            incluir_vencimientos,
            incluir_entidades
        )
        if "error" in result:
            raise HTTPException(status_code=404, detail=result["error"])
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# UTILIDADES
# ============================================================

@router.get("/definiciones")
async def get_tool_definitions():
    """Retorna definiciones de tools para function calling."""
    try:
        return {"tools": tools_service.get_tool_definitions()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ejecutar/{tool_name}")
async def ejecutar_tool(tool_name: str, params: dict = {}):
    """Ejecuta una tool por nombre."""
    try:
        result = tools_service.execute_tool(tool_name, params)
        return {"result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
