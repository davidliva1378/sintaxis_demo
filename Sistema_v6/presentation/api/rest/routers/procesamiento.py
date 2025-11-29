"""
Router REST API para Procesamiento de Actuaciones.

Endpoints para:
- Procesar actuaciones individuales
- Procesar expedientes completos
- Obtener vencimientos urgentes
- Consultar estadísticas de procesamiento
- Obtener actuaciones por utilidad
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Request
from pydantic import BaseModel, Field
from datetime import date, datetime
import logging
import os

from presentation.api.rest.rate_limiter import limiter

from application.services.procesador_actuaciones_service import ProcesadorActuacionesService

logger = logging.getLogger(__name__)


# ============================================================================
# Modelos de Request/Response
# ============================================================================


class ActuacionInput(BaseModel):
    """Datos de actuación para procesar"""
    id: int
    tipo: str
    detalle: str
    tiene_archivo: bool = False
    expediente_numero: Optional[str] = None


class ProcesarActuacionRequest(BaseModel):
    """Request para procesar una actuación individual"""
    actuacion: ActuacionInput
    ruta_pdf: Optional[str] = None
    guardar_en_bd: bool = True


class ClasificacionResponse(BaseModel):
    """Response con clasificación de actuación"""
    utilidad: str  # nula, baja, media, alta
    score: int
    motivo: str
    requiere_pdf: bool
    tiene_plazo_probable: bool
    keywords_detectados: List[str]


class VencimientoResponse(BaseModel):
    """Response con datos de vencimiento"""
    tipo: str
    fecha_notificacion: date
    plazo_dias: int
    fecha_vencimiento: date
    dias_habiles: bool
    descripcion: Optional[str]
    confianza: float


class ResultadoProcesamientoResponse(BaseModel):
    """Response con resultado de procesamiento de actuación"""
    actuacion_id: int
    clasificacion: ClasificacionResponse
    vencimientos: List[VencimientoResponse]
    duplicados_detectados: int
    tiene_errores: bool
    errores: List[str]


class ProcesarExpedienteRequest(BaseModel):
    """Request para procesar expediente completo"""
    numero_expediente: str
    actuaciones: List[ActuacionInput]
    rutas_pdf: Optional[dict[int, str]] = None
    guardar_en_bd: bool = True
    usar_ocr: bool = True


class EstadisticasExpedienteResponse(BaseModel):
    """Response con estadísticas de procesamiento"""
    total_actuaciones: int
    actuaciones_alta: int
    actuaciones_media: int
    actuaciones_baja: int
    actuaciones_nula: int
    reduccion_estimada_pct: float
    vencimientos_detectados: int
    vencimientos_urgentes: int
    duplicados_detectados: int
    tiempo_procesamiento_seg: float


class EntidadNormalizadaResponse(BaseModel):
    """Entidad extraída y normalizada del texto"""
    original: str
    normalized: str
    label: str
    score: float
    normalization_type: Optional[str] = None


class ResultadoExpedienteResponse(BaseModel):
    """Response con resultado de procesamiento de expediente"""
    expediente_numero: str
    estadisticas: EstadisticasExpedienteResponse
    vencimientos_urgentes: List[dict]
    con_errores: int
    entidades_por_actuacion: Optional[dict[int, List[EntidadNormalizadaResponse]]] = None


class VencimientoUrgenteResponse(BaseModel):
    """Response con vencimiento urgente"""
    id: int
    actuacion_id: int
    expediente_numero: str
    tipo: str
    fecha_vencimiento: date
    dias_restantes: int
    nivel_urgencia: str  # vencido, critico, urgente, proximo, normal
    descripcion: Optional[str]
    actuacion_tipo: str
    actuacion_detalle: str


class ActuacionPorUtilidadResponse(BaseModel):
    """Response con actuación filtrada por utilidad"""
    id: int
    expediente_numero: str
    tipo: str
    detalle: str
    utilidad: str
    score: int
    tiene_vencimiento: bool
    fecha_vencimiento: Optional[date]
    dias_restantes: Optional[int]


class EstadisticasGlobalesResponse(BaseModel):
    """Response con estadísticas globales del sistema"""
    total_expedientes_procesados: int
    total_actuaciones_procesadas: int
    total_vencimientos_detectados: int
    total_vencimientos_urgentes: int
    total_duplicados_detectados: int
    reduccion_promedio_pct: float
    ultima_actualizacion: Optional[datetime]


# ============================================================================
# Dependencias
# ============================================================================


def get_db_config() -> dict:
    """
    Obtiene la configuración de base de datos desde variables de entorno.

    Returns:
        Dict con configuración de MySQL
    """
    return {
        "host": os.getenv("MYSQL_HOST", "localhost"),
        "port": int(os.getenv("MYSQL_PORT", "3306")),
        "database": os.getenv("MYSQL_DATABASE", "sintaxis"),
        "user": os.getenv("MYSQL_USER", "root"),
        "password": os.getenv("MYSQL_PASSWORD", ""),
    }


def get_procesador_service() -> ProcesadorActuacionesService:
    """
    Dependency para obtener instancia del servicio de procesamiento.

    Returns:
        ProcesadorActuacionesService configurado
    """
    db_config = get_db_config()
    return ProcesadorActuacionesService(db_config)


# ============================================================================
# Router
# ============================================================================


router = APIRouter(
    prefix="/procesamiento",
    tags=["Procesamiento de Actuaciones"]
)


@router.post("/actuacion", response_model=ResultadoProcesamientoResponse)
@limiter.limit("10/minute")
async def procesar_actuacion(
    request: Request,
    data: ProcesarActuacionRequest,
    servicio: ProcesadorActuacionesService = Depends(get_procesador_service)
):
    """
    Procesa una actuación individual.

    Ejecuta:
    - Clasificación por utilidad jurídica
    - Análisis de vencimientos (si corresponde)
    - Extracción de texto de PDF (si se proporciona)
    - Persistencia en BD (opcional)

    Returns:
        Resultado del procesamiento con clasificación y vencimientos
    """
    try:
        actuacion_dict = data.actuacion.model_dump()

        resultado = await servicio.procesar_actuacion_individual(
            actuacion=actuacion_dict,
            ruta_pdf=data.ruta_pdf,
            guardar_en_bd=data.guardar_en_bd
        )

        # Convertir resultado a response
        clasificacion = ClasificacionResponse(
            utilidad=resultado.clasificacion.utilidad.value,
            score=resultado.clasificacion.score,
            motivo=resultado.clasificacion.motivo,
            requiere_pdf=resultado.clasificacion.requiere_pdf,
            tiene_plazo_probable=resultado.clasificacion.tiene_plazo_probable,
            keywords_detectados=resultado.clasificacion.keywords_detectados or []
        )

        vencimientos = [
            VencimientoResponse(
                tipo=v.tipo.value,
                fecha_notificacion=v.fecha_notificacion,
                plazo_dias=v.plazo_dias,
                fecha_vencimiento=v.fecha_vencimiento,
                dias_habiles=v.dias_habiles,
                descripcion=v.descripcion,
                confianza=v.confianza
            )
            for v in resultado.vencimientos
        ]

        return ResultadoProcesamientoResponse(
            actuacion_id=resultado.actuacion_id,
            clasificacion=clasificacion,
            vencimientos=vencimientos,
            duplicados_detectados=len(resultado.duplicados),
            tiene_errores=resultado.tiene_errores,
            errores=resultado.errores
        )

    except Exception as e:
        logger.error(f"Error procesando actuación: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al procesar actuación: {str(e)}"
        )


@router.post("/expediente", response_model=ResultadoExpedienteResponse)
@limiter.limit("5/minute")
async def procesar_expediente(
    request: Request,
    data: ProcesarExpedienteRequest,
    background_tasks: BackgroundTasks,
    servicio: ProcesadorActuacionesService = Depends(get_procesador_service)
):
    """
    Procesa todas las actuaciones de un expediente.

    Ejecuta:
    - Clasificación de todas las actuaciones
    - Detección de duplicados
    - Análisis de vencimientos
    - Generación de estadísticas
    - Persistencia en BD

    Args:
        request: Datos del expediente y actuaciones
        background_tasks: Para procesamiento en background (opcional)

    Returns:
        Resultado del procesamiento con estadísticas y vencimientos urgentes
    """
    try:
        actuaciones_dict = [act.model_dump() for act in data.actuaciones]

        resultado = await servicio.procesar_expediente_completo(
            numero_expediente=data.numero_expediente,
            actuaciones=actuaciones_dict,
            rutas_pdf=data.rutas_pdf,
            guardar_en_bd=data.guardar_en_bd,
            usar_ocr=data.usar_ocr
        )

        # Convertir estadísticas a response
        stats = resultado['estadisticas']
        estadisticas = EstadisticasExpedienteResponse(
            total_actuaciones=resultado['total_actuaciones'],
            actuaciones_alta=stats.get('conteo_por_utilidad', {}).get('ALTA', 0),
            actuaciones_media=stats.get('conteo_por_utilidad', {}).get('MEDIA', 0),
            actuaciones_baja=stats.get('conteo_por_utilidad', {}).get('BAJA', 0),
            actuaciones_nula=stats.get('conteo_por_utilidad', {}).get('NULA', 0),
            reduccion_estimada_pct=stats.get('reduccion_estimada', 0.0),
            vencimientos_detectados=resultado['vencimientos_totales'],
            vencimientos_urgentes=len(resultado['vencimientos_urgentes']),
            duplicados_detectados=len(resultado['duplicados_detectados']),
            tiempo_procesamiento_seg=0.0  # Se calcula en el servicio
        )

        # Convertir vencimientos a formato VencimientoUrgente
        from datetime import date as date_type
        vencimientos_urgentes = []
        for i, v in enumerate(resultado['vencimientos_urgentes']):
            # Buscar actuación asociada
            act_info = resultado.get('resultados', {})
            actuacion_id = None
            actuacion_tipo = ""
            actuacion_detalle = ""

            # Intentar encontrar la actuación que generó este vencimiento
            for act_id, res in act_info.items():
                if hasattr(res, 'vencimientos') and v in res.vencimientos:
                    actuacion_id = act_id
                    # Buscar en lista original de actuaciones
                    for act in data.actuaciones:
                        if act.id == act_id:
                            actuacion_tipo = act.tipo
                            actuacion_detalle = act.detalle
                            break
                    break

            # Extraer datos del vencimiento
            if hasattr(v, 'model_dump'):
                v_dict = v.model_dump()
            elif isinstance(v, dict):
                v_dict = v
            else:
                v_dict = vars(v) if hasattr(v, '__dict__') else {}

            # Calcular días restantes
            fecha_venc = v_dict.get('fecha_vencimiento')
            if isinstance(fecha_venc, date_type):
                dias_restantes = (fecha_venc - date_type.today()).days
            else:
                dias_restantes = 0

            # Determinar nivel de urgencia
            if dias_restantes < 0:
                nivel_urgencia = 'vencido'
            elif dias_restantes <= 1:
                nivel_urgencia = 'critico'
            elif dias_restantes <= 3:
                nivel_urgencia = 'urgente'
            elif dias_restantes <= 7:
                nivel_urgencia = 'proximo'
            else:
                nivel_urgencia = 'normal'

            # Obtener tipo como string
            tipo_str = v_dict.get('tipo', '')
            if hasattr(tipo_str, 'value'):
                tipo_str = tipo_str.value

            vencimientos_urgentes.append({
                'id': i + 1,
                'actuacion_id': actuacion_id or 0,
                'expediente_numero': data.numero_expediente,
                'tipo': tipo_str,
                'fecha_vencimiento': str(fecha_venc) if fecha_venc else None,
                'dias_restantes': dias_restantes,
                'nivel_urgencia': nivel_urgencia,
                'descripcion': v_dict.get('descripcion'),
                'actuacion_tipo': actuacion_tipo,
                'actuacion_detalle': actuacion_detalle[:200] if actuacion_detalle else ""
            })

        # Convertir entidades a response (convertir keys de int a str para JSON)
        entidades_response = None
        if resultado.get('entidades_por_actuacion'):
            entidades_response = {
                act_id: [
                    EntidadNormalizadaResponse(**ent)
                    for ent in entidades
                ]
                for act_id, entidades in resultado['entidades_por_actuacion'].items()
            }

        return ResultadoExpedienteResponse(
            expediente_numero=data.numero_expediente,
            estadisticas=estadisticas,
            vencimientos_urgentes=vencimientos_urgentes,
            con_errores=resultado['con_errores'],
            entidades_por_actuacion=entidades_response
        )

    except Exception as e:
        logger.error(f"Error procesando expediente {data.numero_expediente}: {e}")
        raise HTTPException(
            status_code=500,
        )


@router.post("/expediente/stream")
@limiter.limit("5/minute")
async def procesar_expediente_stream(
    request: Request,
    data: ProcesarExpedienteRequest,
    servicio: ProcesadorActuacionesService = Depends(get_procesador_service)
):
    """
    Procesa un expediente con respuesta en streaming (NDJSON).

    Retorna eventos de progreso en tiempo real:
    - start: Inicio del proceso
    - progress: Progreso de cada actuación
    - saving: Guardando en BD
    - complete: Resultado final
    - error: Error ocurrido

    Args:
        data: Datos del expediente y actuaciones

    Returns:
        StreamingResponse con eventos JSON
    """
    from fastapi.responses import StreamingResponse

    try:
        actuaciones_dict = [act.model_dump() for act in data.actuaciones]

        return StreamingResponse(
            servicio.procesar_expediente_stream(
                numero_expediente=data.numero_expediente,
                actuaciones=actuaciones_dict,
                rutas_pdf=data.rutas_pdf,
                guardar_en_bd=data.guardar_en_bd,
                usar_ocr=data.usar_ocr
            ),
            media_type="application/x-ndjson"
        )

    except Exception as e:
        logger.error(f"Error iniciando stream expediente {data.numero_expediente}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al iniciar stream: {str(e)}"
        )


@router.get("/vencimientos/urgentes", response_model=List[VencimientoUrgenteResponse])
async def obtener_vencimientos_urgentes(
    dias_adelante: int = 7,
    servicio: ProcesadorActuacionesService = Depends(get_procesador_service)
):
    """
    Obtiene todos los vencimientos urgentes del sistema.

    Args:
        dias_adelante: Días hacia adelante a considerar (default: 7)

    Returns:
        Lista de vencimientos urgentes ordenados por fecha
    """
    try:
        vencimientos = await servicio.obtener_vencimientos_urgentes(dias_adelante)

        return [
            VencimientoUrgenteResponse(**v)
            for v in vencimientos
        ]

    except Exception as e:
        logger.error(f"Error obteniendo vencimientos urgentes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener vencimientos urgentes: {str(e)}"
        )


@router.get("/expediente/{numero}/vencimientos", response_model=List[VencimientoUrgenteResponse])
async def obtener_vencimientos_expediente(
    numero: str,
    servicio: ProcesadorActuacionesService = Depends(get_procesador_service)
):
    """
    Obtiene todos los vencimientos de un expediente específico.

    Args:
        numero: Número del expediente

    Returns:
        Lista de vencimientos del expediente ordenados por fecha
    """
    try:
        conn = servicio.repository._get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                v.id,
                v.actuacion_id,
                v.expediente_numero,
                v.tipo,
                v.fecha_vencimiento,
                DATEDIFF(v.fecha_vencimiento, CURDATE()) as dias_restantes,
                CASE
                    WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) < 0 THEN 'vencido'
                    WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 1 THEN 'critico'
                    WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 3 THEN 'urgente'
                    WHEN DATEDIFF(v.fecha_vencimiento, CURDATE()) <= 7 THEN 'proximo'
                    ELSE 'normal'
                END as nivel_urgencia,
                v.descripcion,
                COALESCE(a.tipo, 'N/A') as actuacion_tipo,
                COALESCE(a.detalle, 'Sin detalle') as actuacion_detalle
            FROM vencimientos v
            LEFT JOIN actuaciones a ON v.actuacion_id = a.id
            WHERE v.expediente_numero = %s
            ORDER BY v.fecha_vencimiento ASC
        """

        cursor.execute(query, (numero,))
        vencimientos = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            VencimientoUrgenteResponse(
                id=v['id'],
                actuacion_id=v['actuacion_id'] or 0,
                expediente_numero=v['expediente_numero'] or numero,
                tipo=v['tipo'] or '',
                fecha_vencimiento=v['fecha_vencimiento'],
                dias_restantes=v['dias_restantes'] or 0,
                nivel_urgencia=v['nivel_urgencia'],
                descripcion=v['descripcion'],
                actuacion_tipo=v['actuacion_tipo'][:200] if v['actuacion_tipo'] else 'N/A',
                actuacion_detalle=v['actuacion_detalle'][:200] if v['actuacion_detalle'] else ''
            )
            for v in vencimientos
        ]

    except Exception as e:
        logger.error(f"Error obteniendo vencimientos del expediente {numero}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener vencimientos: {str(e)}"
        )


@router.get("/expediente/{numero}/actuaciones-clasificadas", response_model=List[ActuacionPorUtilidadResponse])
async def obtener_actuaciones_clasificadas_expediente(
    numero: str,
    servicio: ProcesadorActuacionesService = Depends(get_procesador_service)
):
    """
    Obtiene todas las actuaciones clasificadas de un expediente específico.

    Args:
        numero: Número del expediente

    Returns:
        Lista de actuaciones con su clasificación de utilidad
    """
    try:
        conn = servicio.repository._get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                a.id,
                a.expediente_numero,
                a.tipo,
                a.detalle,
                a.utilidad,
                COALESCE(a.score, 0) as score,
                v.fecha_vencimiento IS NOT NULL as tiene_vencimiento,
                v.fecha_vencimiento,
                DATEDIFF(v.fecha_vencimiento, CURDATE()) as dias_restantes
            FROM actuaciones a
            LEFT JOIN vencimientos v ON a.id = v.actuacion_id
            WHERE a.expediente_numero = %s
              AND a.utilidad IS NOT NULL
            ORDER BY
                CASE a.utilidad
                    WHEN 'alta' THEN 1
                    WHEN 'media' THEN 2
                    WHEN 'baja' THEN 3
                    WHEN 'nula' THEN 4
                END,
                a.score DESC
        """

        cursor.execute(query, (numero,))
        actuaciones = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            ActuacionPorUtilidadResponse(
                id=act['id'],
                expediente_numero=act['expediente_numero'] or numero,
                tipo=act['tipo'] or '',
                detalle=act['detalle'] or '',
                utilidad=act['utilidad'],
                score=act['score'] or 0,
                tiene_vencimiento=bool(act['tiene_vencimiento']),
                fecha_vencimiento=act['fecha_vencimiento'],
                dias_restantes=act['dias_restantes']
            )
            for act in actuaciones
        ]

    except Exception as e:
        logger.error(f"Error obteniendo actuaciones clasificadas del expediente {numero}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener actuaciones clasificadas: {str(e)}"
        )


@router.get("/expediente/{numero}/estadisticas", response_model=EstadisticasExpedienteResponse)
async def obtener_estadisticas_expediente(
    numero: str,
    servicio: ProcesadorActuacionesService = Depends(get_procesador_service)
):
    """
    Obtiene las estadísticas de procesamiento de un expediente.

    Args:
        numero: Número del expediente

    Returns:
        Estadísticas del último procesamiento
    """
    try:
        estadisticas = await servicio.obtener_estadisticas_expediente(numero)

        if not estadisticas:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontraron estadísticas para el expediente {numero}"
            )

        return EstadisticasExpedienteResponse(
            total_actuaciones=estadisticas['total_actuaciones'],
            actuaciones_alta=estadisticas['actuaciones_alta'],
            actuaciones_media=estadisticas['actuaciones_media'],
            actuaciones_baja=estadisticas['actuaciones_baja'],
            actuaciones_nula=estadisticas['actuaciones_nula'],
            reduccion_estimada_pct=estadisticas['reduccion_estimada_pct'],
            vencimientos_detectados=estadisticas['vencimientos_detectados'],
            vencimientos_urgentes=estadisticas['vencimientos_urgentes'],
            duplicados_detectados=estadisticas['duplicados_detectados'],
            tiempo_procesamiento_seg=estadisticas['tiempo_procesamiento_seg']
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error obteniendo estadísticas del expediente {numero}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas: {str(e)}"
        )


@router.get("/actuaciones/utilidad/{nivel}", response_model=List[ActuacionPorUtilidadResponse])
async def obtener_actuaciones_por_utilidad(
    nivel: str,
    limite: int = 100,
    servicio: ProcesadorActuacionesService = Depends(get_procesador_service)
):
    """
    Obtiene actuaciones filtradas por nivel de utilidad.

    Args:
        nivel: Nivel de utilidad (alta, media, baja, nula)
        limite: Máximo de resultados (default: 100)

    Returns:
        Lista de actuaciones del nivel especificado
    """
    # Validar nivel
    niveles_validos = ['alta', 'media', 'baja', 'nula']
    if nivel.lower() not in niveles_validos:
        raise HTTPException(
            status_code=400,
            detail=f"Nivel inválido. Opciones: {', '.join(niveles_validos)}"
        )

    try:
        # Consulta directa a la vista actuaciones_alta_utilidad o filtro por utilidad
        conn = servicio.repository._get_connection()
        cursor = conn.cursor(dictionary=True)

        if nivel.lower() in ['alta', 'media']:
            # Usar vista optimizada para alta/media
            query = """
                SELECT *
                FROM actuaciones_alta_utilidad
                WHERE utilidad = %s
                ORDER BY ISNULL(fecha_vencimiento), fecha_vencimiento ASC
                LIMIT %s
            """
        else:
            # Consulta directa para baja/nula
            query = """
                SELECT
                    id,
                    expediente_numero,
                    tipo,
                    detalle,
                    utilidad,
                    score,
                    FALSE as tiene_vencimiento,
                    NULL as fecha_vencimiento,
                    NULL as dias_restantes
                FROM actuaciones
                WHERE utilidad = %s
                ORDER BY score DESC
                LIMIT %s
            """

        cursor.execute(query, (nivel.lower(), limite))
        actuaciones = cursor.fetchall()

        cursor.close()
        conn.close()

        return [
            ActuacionPorUtilidadResponse(
                id=act['id'],
                expediente_numero=act.get('expediente_numero', ''),
                tipo=act.get('tipo', ''),
                detalle=act.get('detalle', ''),
                utilidad=act['utilidad'],
                score=act.get('score', 0),
                tiene_vencimiento=act.get('tiene_vencimiento', False),
                fecha_vencimiento=act.get('fecha_vencimiento'),
                dias_restantes=act.get('dias_restantes')
            )
            for act in actuaciones
        ]

    except Exception as e:
        logger.error(f"Error obteniendo actuaciones por utilidad {nivel}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener actuaciones: {str(e)}"
        )


@router.get("/estadisticas/globales", response_model=EstadisticasGlobalesResponse)
async def obtener_estadisticas_globales(
    servicio: ProcesadorActuacionesService = Depends(get_procesador_service)
):
    """
    Obtiene estadísticas globales del sistema de procesamiento.

    Returns:
        Estadísticas agregadas de todos los procesamientos
    """
    try:
        conn = servicio.repository._get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT
                COUNT(DISTINCT expediente_numero) as total_expedientes_procesados,
                SUM(total_actuaciones) as total_actuaciones_procesadas,
                SUM(vencimientos_detectados) as total_vencimientos_detectados,
                SUM(vencimientos_urgentes) as total_vencimientos_urgentes,
                SUM(duplicados_detectados) as total_duplicados_detectados,
                AVG(reduccion_estimada_pct) as reduccion_promedio_pct,
                MAX(fecha_procesamiento) as ultima_actualizacion
            FROM procesamiento_estadisticas
        """

        cursor.execute(query)
        stats = cursor.fetchone()

        cursor.close()
        conn.close()

        return EstadisticasGlobalesResponse(
            total_expedientes_procesados=stats['total_expedientes_procesados'] or 0,
            total_actuaciones_procesadas=stats['total_actuaciones_procesadas'] or 0,
            total_vencimientos_detectados=stats['total_vencimientos_detectados'] or 0,
            total_vencimientos_urgentes=stats['total_vencimientos_urgentes'] or 0,
            total_duplicados_detectados=stats['total_duplicados_detectados'] or 0,
            reduccion_promedio_pct=stats['reduccion_promedio_pct'] or 0.0,
            ultima_actualizacion=stats['ultima_actualizacion']
        )

    except Exception as e:
        logger.error(f"Error obteniendo estadísticas globales: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error al obtener estadísticas globales: {str(e)}"
        )
