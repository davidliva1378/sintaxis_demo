"""
Router REST API para gestión de feriados.

Endpoints para:
- CRUD de feriados nacionales/judiciales
- Consulta de feriados por año/rango
- Gestión de períodos de feria judicial
- Verificación de días hábiles
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from datetime import date
from enum import Enum
import logging

from application.services.feriados_service import get_feriados_service

logger = logging.getLogger(__name__)


# ============================================================================
# Enums
# ============================================================================

class TipoFeriado(str, Enum):
    nacional = "nacional"
    judicial = "judicial"
    provincial = "provincial"
    feria_judicial = "feria_judicial"


# ============================================================================
# Modelos de Request/Response
# ============================================================================

class FeriadoBase(BaseModel):
    """Base para feriado."""
    fecha: date
    nombre: str
    tipo: TipoFeriado = TipoFeriado.nacional
    es_trasladable: bool = False


class FeriadoCreate(FeriadoBase):
    """Request para crear feriado."""
    pass


class FeriadoUpdate(BaseModel):
    """Request para actualizar feriado."""
    nombre: Optional[str] = None
    tipo: Optional[TipoFeriado] = None
    es_trasladable: Optional[bool] = None
    activo: Optional[bool] = None


class FeriadoResponse(FeriadoBase):
    """Response con feriado completo."""
    id: int
    año: int
    activo: bool


class FeriaJudicialCreate(BaseModel):
    """Request para crear feria judicial."""
    año: int
    fecha_inicio: date
    fecha_fin: date
    nombre: str = "Feria Judicial de Verano"


class FeriaJudicialResponse(BaseModel):
    """Response con feria judicial."""
    id: int
    año: int
    fecha_inicio: date
    fecha_fin: date
    nombre: str
    activo: bool


class VerificacionDiaHabil(BaseModel):
    """Response de verificación de día hábil."""
    fecha: date
    es_habil: bool
    es_feriado: bool
    nombre_feriado: Optional[str] = None
    es_feria_judicial: bool
    es_fin_semana: bool


class CalculoVencimiento(BaseModel):
    """Response de cálculo de vencimiento."""
    fecha_inicio: date
    dias_plazo: int
    fecha_vencimiento: date
    dias_corridos: int


class ResumenFeriados(BaseModel):
    """Resumen de feriados de un año."""
    año: int
    total_feriados: int
    total_nacionales: int
    total_judiciales: int
    feria_judicial: Optional[FeriaJudicialResponse] = None
    proximos_feriados: List[FeriadoResponse]


# ============================================================================
# Router
# ============================================================================

router = APIRouter(
    prefix="/config/feriados",
    tags=["Configuración - Feriados"]
)


@router.get("", response_model=List[FeriadoResponse])
async def listar_feriados(
    año: Optional[int] = Query(None, description="Filtrar por año"),
    fecha_desde: Optional[date] = Query(None, description="Fecha desde"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha hasta"),
    tipo: Optional[TipoFeriado] = Query(None, description="Filtrar por tipo")
):
    """
    Lista feriados con filtros opcionales.

    - Si se especifica año, devuelve todos los feriados del año
    - Si se especifica rango de fechas, devuelve feriados en ese rango
    """
    try:
        service = get_feriados_service()

        if fecha_desde and fecha_hasta:
            feriados = service.obtener_feriados_rango(fecha_desde, fecha_hasta)
        elif año:
            feriados = service.obtener_feriados_año(año)
        else:
            # Por defecto, año actual
            from datetime import datetime
            feriados = service.obtener_feriados_año(datetime.now().year)

        # Filtrar por tipo si se especifica
        if tipo:
            feriados = [f for f in feriados if f.get('tipo') == tipo.value]

        return [
            FeriadoResponse(
                id=f['id'],
                fecha=f['fecha'],
                nombre=f['nombre'],
                tipo=f['tipo'],
                es_trasladable=f.get('es_trasladable', False),
                año=f['fecha'].year if isinstance(f['fecha'], date) else int(f['fecha'][:4]),
                activo=f.get('activo', True)
            )
            for f in feriados
        ]

    except Exception as e:
        logger.error(f"Error listando feriados: {e}")
        raise HTTPException(status_code=500, detail=f"Error al listar feriados: {str(e)}")


@router.get("/resumen/{año}", response_model=ResumenFeriados)
async def obtener_resumen(año: int):
    """
    Obtiene resumen de feriados de un año.
    """
    try:
        service = get_feriados_service()
        feriados = service.obtener_feriados_año(año)
        feria = service.obtener_feria_judicial(año)

        # Contar por tipo
        nacionales = [f for f in feriados if f.get('tipo') == 'nacional']
        judiciales = [f for f in feriados if f.get('tipo') in ('judicial', 'feria_judicial')]

        # Próximos feriados (desde hoy)
        from datetime import datetime
        hoy = datetime.now().date()
        proximos = [
            f for f in feriados
            if isinstance(f['fecha'], date) and f['fecha'] >= hoy
        ][:5]

        return ResumenFeriados(
            año=año,
            total_feriados=len(feriados),
            total_nacionales=len(nacionales),
            total_judiciales=len(judiciales),
            feria_judicial=FeriaJudicialResponse(**feria) if feria else None,
            proximos_feriados=[
                FeriadoResponse(
                    id=f['id'],
                    fecha=f['fecha'],
                    nombre=f['nombre'],
                    tipo=f['tipo'],
                    es_trasladable=f.get('es_trasladable', False),
                    año=año,
                    activo=True
                )
                for f in proximos
            ]
        )

    except Exception as e:
        logger.error(f"Error obteniendo resumen de feriados: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen: {str(e)}")


@router.post("", response_model=FeriadoResponse)
async def crear_feriado(request: FeriadoCreate):
    """
    Crea un nuevo feriado.
    """
    try:
        service = get_feriados_service()

        feriado = service.crear_feriado(
            fecha=request.fecha,
            nombre=request.nombre,
            tipo=request.tipo.value,
            es_trasladable=request.es_trasladable
        )

        return FeriadoResponse(
            id=feriado['id'],
            fecha=feriado['fecha'],
            nombre=feriado['nombre'],
            tipo=feriado['tipo'],
            es_trasladable=feriado.get('es_trasladable', False),
            año=feriado['año'],
            activo=feriado.get('activo', True)
        )

    except Exception as e:
        logger.error(f"Error creando feriado: {e}")
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=409, detail="Ya existe un feriado en esa fecha")
        raise HTTPException(status_code=500, detail=f"Error al crear feriado: {str(e)}")


@router.put("/{feriado_id}", response_model=FeriadoResponse)
async def actualizar_feriado(feriado_id: int, request: FeriadoUpdate):
    """
    Actualiza un feriado existente.
    """
    try:
        service = get_feriados_service()

        # Construir kwargs solo con valores no None
        kwargs = {}
        if request.nombre is not None:
            kwargs['nombre'] = request.nombre
        if request.tipo is not None:
            kwargs['tipo'] = request.tipo.value
        if request.es_trasladable is not None:
            kwargs['es_trasladable'] = request.es_trasladable
        if request.activo is not None:
            kwargs['activo'] = request.activo

        if not kwargs:
            raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")

        feriado = service.actualizar_feriado(feriado_id, **kwargs)

        if not feriado:
            raise HTTPException(status_code=404, detail="Feriado no encontrado")

        return FeriadoResponse(
            id=feriado['id'],
            fecha=feriado['fecha'],
            nombre=feriado['nombre'],
            tipo=feriado['tipo'],
            es_trasladable=feriado.get('es_trasladable', False),
            año=feriado['año'],
            activo=feriado.get('activo', True)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error actualizando feriado: {e}")
        raise HTTPException(status_code=500, detail=f"Error al actualizar feriado: {str(e)}")


@router.delete("/{feriado_id}")
async def eliminar_feriado(feriado_id: int):
    """
    Elimina (desactiva) un feriado.
    """
    try:
        service = get_feriados_service()
        eliminado = service.eliminar_feriado(feriado_id)

        if not eliminado:
            raise HTTPException(status_code=404, detail="Feriado no encontrado")

        return {"mensaje": "Feriado eliminado", "id": feriado_id}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error eliminando feriado: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar feriado: {str(e)}")


# ============================================================================
# Endpoints de Feria Judicial
# ============================================================================

@router.get("/feria-judicial", response_model=List[FeriaJudicialResponse])
async def listar_ferias_judiciales(
    año_desde: Optional[int] = Query(None, description="Año desde"),
    año_hasta: Optional[int] = Query(None, description="Año hasta")
):
    """
    Lista períodos de feria judicial.
    """
    try:
        service = get_feriados_service()
        from datetime import datetime

        # Por defecto, últimos 3 años
        if año_desde is None:
            año_desde = datetime.now().year - 1
        if año_hasta is None:
            año_hasta = datetime.now().year + 2

        ferias = []
        for año in range(año_desde, año_hasta + 1):
            feria = service.obtener_feria_judicial(año)
            if feria:
                ferias.append(FeriaJudicialResponse(**feria))

        return ferias

    except Exception as e:
        logger.error(f"Error listando ferias judiciales: {e}")
        raise HTTPException(status_code=500, detail=f"Error al listar ferias: {str(e)}")


@router.post("/feria-judicial", response_model=FeriaJudicialResponse)
async def crear_feria_judicial(request: FeriaJudicialCreate):
    """
    Crea un nuevo período de feria judicial.
    """
    try:
        service = get_feriados_service()

        feria = service.crear_feria_judicial(
            año=request.año,
            fecha_inicio=request.fecha_inicio,
            fecha_fin=request.fecha_fin,
            nombre=request.nombre
        )

        return FeriaJudicialResponse(**feria)

    except Exception as e:
        logger.error(f"Error creando feria judicial: {e}")
        if "Duplicate entry" in str(e):
            raise HTTPException(status_code=409, detail="Ya existe feria judicial para ese año")
        raise HTTPException(status_code=500, detail=f"Error al crear feria: {str(e)}")


# ============================================================================
# Endpoints de Verificación y Cálculo
# ============================================================================

@router.get("/verificar-dia", response_model=VerificacionDiaHabil)
async def verificar_dia_habil(fecha: date = Query(..., description="Fecha a verificar")):
    """
    Verifica si una fecha es día hábil.
    """
    try:
        service = get_feriados_service()

        es_habil = service.es_dia_habil(fecha)
        es_feriado, nombre_feriado = service.es_feriado(fecha)
        es_feria = service.es_feria_judicial(fecha)
        es_fin_semana = fecha.weekday() >= 5

        return VerificacionDiaHabil(
            fecha=fecha,
            es_habil=es_habil,
            es_feriado=es_feriado,
            nombre_feriado=nombre_feriado,
            es_feria_judicial=es_feria,
            es_fin_semana=es_fin_semana
        )

    except Exception as e:
        logger.error(f"Error verificando día: {e}")
        raise HTTPException(status_code=500, detail=f"Error al verificar día: {str(e)}")


@router.get("/calcular-vencimiento", response_model=CalculoVencimiento)
async def calcular_vencimiento(
    fecha_inicio: date = Query(..., description="Fecha de inicio del plazo"),
    dias_plazo: int = Query(..., ge=1, le=365, description="Días hábiles del plazo")
):
    """
    Calcula la fecha de vencimiento considerando días hábiles.
    """
    try:
        service = get_feriados_service()

        fecha_vencimiento = service.calcular_fecha_vencimiento(fecha_inicio, dias_plazo)
        dias_corridos = (fecha_vencimiento - fecha_inicio).days

        return CalculoVencimiento(
            fecha_inicio=fecha_inicio,
            dias_plazo=dias_plazo,
            fecha_vencimiento=fecha_vencimiento,
            dias_corridos=dias_corridos
        )

    except Exception as e:
        logger.error(f"Error calculando vencimiento: {e}")
        raise HTTPException(status_code=500, detail=f"Error al calcular vencimiento: {str(e)}")


@router.get("/dias-habiles", response_model=dict)
async def contar_dias_habiles(
    fecha_desde: date = Query(..., description="Fecha inicial"),
    fecha_hasta: date = Query(..., description="Fecha final")
):
    """
    Cuenta los días hábiles entre dos fechas.
    """
    try:
        service = get_feriados_service()
        dias = service.contar_dias_habiles(fecha_desde, fecha_hasta)

        return {
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "dias_habiles": dias,
            "dias_corridos": (fecha_hasta - fecha_desde).days
        }

    except Exception as e:
        logger.error(f"Error contando días hábiles: {e}")
        raise HTTPException(status_code=500, detail=f"Error al contar días: {str(e)}")


@router.post("/limpiar-cache")
async def limpiar_cache():
    """
    Limpia el caché de feriados.

    Útil después de importar feriados o hacer cambios masivos.
    """
    try:
        service = get_feriados_service()
        service.limpiar_cache()
        return {"mensaje": "Caché de feriados limpiado"}

    except Exception as e:
        logger.error(f"Error limpiando caché: {e}")
        raise HTTPException(status_code=500, detail=f"Error al limpiar caché: {str(e)}")
