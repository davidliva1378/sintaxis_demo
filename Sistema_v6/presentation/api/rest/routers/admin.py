"""
Router REST API para Administración del Sistema.

Endpoints:
- GET /stats: Obtiene estadísticas del sistema
- POST /reset: Ejecuta reseteo del sistema
- GET /backups: Lista backups disponibles
- POST /restore/{backup_id}: Restaura un backup
- DELETE /cache: Limpia cache del sistema
"""

from typing import List, Optional, Annotated
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
import json

from admin import GestorReseteo, NivelReseteo
from presentation.api.rest.routers.auth import get_current_active_user
from infrastructure.persistence.database import Usuario
from Sistema_v6.infrastructure.persistence.expedientes_mysql import get_expedientes_repository
from Sistema_v6.gestor_directorios.expedientes import GestorDirectoriosExpedientes


# ============================================================================
# Modelos de Request/Response
# ============================================================================

class EstadisticasSistemaResponse(BaseModel):
    """Response con estadísticas del sistema."""
    espacio_total_mb: float
    expedientes_procesados: int
    pdfs_descargados: int
    sesiones_activas: int
    desglose: dict
    ultimo_backup: Optional[str] = None


class ResetRequest(BaseModel):
    """Request para resetear el sistema."""
    nivel: str = Field(..., description="Nivel de reseteo: listados, pdfs, expedientes, completo, nuclear")
    confirmacion: str = Field(..., description="Confirmación: debe ser 'CONFIRMAR-{NIVEL}'")
    crear_backup: bool = Field(True, description="Crear backup antes de resetear")
    dry_run: bool = Field(False, description="Solo simular sin eliminar")
    incluir_procesamiento_mysql: bool = Field(False, description="Incluir limpieza de datos de procesamiento en MySQL")


class ResultadoReseteoResponse(BaseModel):
    """Response del reseteo."""
    nivel: str
    archivos_eliminados: int
    espacio_liberado_mb: float
    backup_path: Optional[str]
    dry_run: bool
    timestamp: str
    detalles: List[str]


class BackupInfo(BaseModel):
    """Información de un backup."""
    id: str
    nivel: Optional[str]
    timestamp: str
    archivos: int
    size_mb: float


class EstadoSincronizacionResponse(BaseModel):
    """Estado de sincronización JSON vs MySQL."""
    total_json: int
    total_mysql: int
    sincronizados: int
    pendientes: int
    porcentaje_sincronizado: float
    ultima_sincronizacion: Optional[str] = None


class DiferenciaSincronizacion(BaseModel):
    """Diferencia entre JSON y MySQL."""
    numero_normalizado: str
    estado: str  # "solo_json", "solo_mysql", "desincronizado"
    id_json: Optional[int] = None
    id_mysql: Optional[int] = None


class ComparacionSincronizacionResponse(BaseModel):
    """Comparación detallada de sincronización."""
    total_diferencias: int
    solo_en_json: int
    solo_en_mysql: int
    diferencias: List[DiferenciaSincronizacion]


class ResultadoSincronizacionResponse(BaseModel):
    """Resultado de ejecutar sincronización."""
    procesados: int
    creados: int
    actualizados: int
    errores: int
    timestamp: str


class ExpedienteMySQLResponse(BaseModel):
    """Expediente desde MySQL."""
    id: int
    numero_normalizado: str
    numero_original: str
    dependencia: Optional[str] = None
    caratula: Optional[str] = None
    situacion: Optional[str] = None
    estado_monitoreo: str
    prioridad: str
    fecha_creacion: str
    fecha_ultima_extraccion: Optional[str] = None
    total_actuaciones: int
    total_pdfs_descargados: int


# ============================================================================
# Dependencias
# ============================================================================

def get_gestor_reseteo() -> GestorReseteo:
    """Dependency para obtener instancia del gestor de reseteo."""
    return GestorReseteo()


async def verify_superuser(
    current_user: Annotated[Usuario, Depends(get_current_active_user)]
) -> Usuario:
    """
    Verifica que el usuario tenga permisos de administrador.

    Args:
        current_user: Usuario autenticado actual

    Returns:
        Usuario si es superuser

    Raises:
        HTTPException: Si el usuario no es superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="No tiene permisos de administrador para esta operación"
        )
    return current_user


# ============================================================================
# Router
# ============================================================================

router = APIRouter(
    prefix="/admin",
    tags=["Administración"]
)


@router.get("/stats", response_model=EstadisticasSistemaResponse)
async def get_estadisticas(
    gestor: GestorReseteo = Depends(get_gestor_reseteo),
    _: bool = Depends(verify_superuser)
):
    """
    Obtiene estadísticas del sistema.

    Returns:
        Estadísticas de uso de espacio, expedientes, PDFs, etc.
    """
    try:
        stats = gestor.get_estadisticas_sistema()
        return EstadisticasSistemaResponse(**stats.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estadísticas: {str(e)}")


@router.post("/reset", response_model=ResultadoReseteoResponse)
async def resetear_sistema(
    request: ResetRequest,
    gestor: GestorReseteo = Depends(get_gestor_reseteo),
    _: bool = Depends(verify_superuser)
):
    """
    Resetea el sistema según el nivel especificado.

    Niveles disponibles:
    - listados: Solo listados temporales (~5 MB)
    - pdfs: PDFs de actuaciones (~680 MB)
    - expedientes: Todos los expedientes (~695 MB)
    - completo: Todo excepto DB/config (~700 MB)
    - nuclear: Reset absoluto incluyendo DB (~700 MB)

    Requiere confirmación explícita.
    """
    # Validar nivel
    try:
        nivel = NivelReseteo(request.nivel.lower())
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"Nivel inválido. Opciones: {[n.value for n in NivelReseteo]}"
        )

    # Validar confirmación
    confirmacion_esperada = f"CONFIRMAR-{request.nivel.upper()}"
    if request.confirmacion != confirmacion_esperada:
        raise HTTPException(
            status_code=400,
            detail=f"Confirmación incorrecta. Escriba: {confirmacion_esperada}"
        )

    # Verificar sesiones activas (solo si no es dry-run)
    if not request.dry_run:
        sesiones_activas = gestor.verificar_sesiones_activas()
        if sesiones_activas > 0:
            raise HTTPException(
                status_code=409,
                detail=f"Hay {sesiones_activas} sesiones activas. Espere a que finalicen."
            )

    # Ejecutar reseteo
    try:
        resultado = gestor.resetear(
            nivel=nivel,
            dry_run=request.dry_run,
            crear_backup=request.crear_backup,
            incluir_procesamiento_mysql=request.incluir_procesamiento_mysql
        )

        # Warning si nivel COMPLETO/NUCLEAR sin limpiar MySQL
        if nivel in (NivelReseteo.COMPLETO, NivelReseteo.NUCLEAR) and not request.incluir_procesamiento_mysql:
            resultado.detalles.insert(0,
                "⚠️ ADVERTENCIA: Los datos de MySQL NO fueron eliminados. "
                "Puede haber inconsistencias entre archivos y base de datos."
            )

        return ResultadoReseteoResponse(**resultado.to_dict())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en reseteo: {str(e)}")


@router.get("/backups", response_model=List[BackupInfo])
async def listar_backups(
    gestor: GestorReseteo = Depends(get_gestor_reseteo),
    _: bool = Depends(verify_superuser)
):
    """
    Lista todos los backups disponibles.

    Returns:
        Lista de backups con información de cada uno.
    """
    try:
        backups = gestor.listar_backups()
        return [BackupInfo(**b) for b in backups]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando backups: {str(e)}")


@router.post("/restore/{backup_id}")
async def restaurar_backup(
    backup_id: str,
    gestor: GestorReseteo = Depends(get_gestor_reseteo),
    _: bool = Depends(verify_superuser)
):
    """
    Restaura un backup específico.

    Args:
        backup_id: ID del backup a restaurar

    Returns:
        Mensaje de confirmación
    """
    # Verificar sesiones activas
    sesiones_activas = gestor.verificar_sesiones_activas()
    if sesiones_activas > 0:
        raise HTTPException(
            status_code=409,
            detail=f"Hay {sesiones_activas} sesiones activas. Espere a que finalicen."
        )

    try:
        success = gestor.restaurar_backup(backup_id)
        if success:
            return {"mensaje": f"Backup {backup_id} restaurado correctamente"}
        else:
            raise HTTPException(status_code=404, detail=f"Backup no encontrado: {backup_id}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error restaurando backup: {str(e)}")


@router.delete("/cache")
async def limpiar_cache(
    gestor: GestorReseteo = Depends(get_gestor_reseteo),
    _: bool = Depends(verify_superuser)
):
    """
    Limpia el cache del sistema.

    Returns:
        Mensaje de confirmación con espacio liberado
    """
    try:
        # Usar reseteo de nivel LISTADOS para limpiar cache
        resultado = gestor.resetear(
            nivel=NivelReseteo.LISTADOS,
            dry_run=False,
            crear_backup=False
        )
        return {
            "mensaje": "Cache limpiado correctamente",
            "archivos_eliminados": resultado.archivos_eliminados,
            "espacio_liberado_mb": round(resultado.espacio_liberado_mb, 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error limpiando cache: {str(e)}")


# ============================================================================
# Endpoints de Sincronización MySQL
# ============================================================================


@router.get("/sincronizacion/estado", response_model=EstadoSincronizacionResponse)
async def get_estado_sincronizacion(
    _: bool = Depends(verify_superuser)
):
    """
    Obtiene el estado de sincronización entre JSON y MySQL.

    Returns:
        Estadísticas de sincronización: totales, sincronizados, pendientes
    """
    try:
        # Obtener datos del JSON
        gestor = GestorDirectoriosExpedientes.desde_config()
        _, expedientes_json = gestor._cargar_indice()
        total_json = len(expedientes_json)

        # Obtener datos de MySQL
        repo = get_expedientes_repository()
        total_mysql = repo.contar()

        # Calcular sincronización (expedientes que están en ambos)
        expedientes_mysql = repo.listar_todos()
        numeros_mysql = {exp['numero_normalizado'] for exp in expedientes_mysql}
        numeros_json = set(expedientes_json.keys())

        sincronizados = len(numeros_json.intersection(numeros_mysql))
        pendientes = len(numeros_json - numeros_mysql)

        porcentaje = (sincronizados / total_json * 100) if total_json > 0 else 100.0

        return EstadoSincronizacionResponse(
            total_json=total_json,
            total_mysql=total_mysql,
            sincronizados=sincronizados,
            pendientes=pendientes,
            porcentaje_sincronizado=round(porcentaje, 1),
            ultima_sincronizacion=None  # TODO: guardar timestamp de última sync
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error obteniendo estado de sincronización: {str(e)}")


@router.get("/sincronizacion/comparar", response_model=ComparacionSincronizacionResponse)
async def comparar_sincronizacion(
    limite: int = Query(100, description="Límite de diferencias a mostrar"),
    _: bool = Depends(verify_superuser)
):
    """
    Compara en detalle JSON vs MySQL y muestra diferencias.

    Returns:
        Lista de diferencias encontradas
    """
    try:
        # Obtener datos del JSON
        gestor = GestorDirectoriosExpedientes.desde_config()
        _, expedientes_json = gestor._cargar_indice()

        # Obtener datos de MySQL
        repo = get_expedientes_repository()
        expedientes_mysql = repo.listar_todos()

        numeros_mysql = {exp['numero_normalizado']: exp['id'] for exp in expedientes_mysql}
        numeros_json = set(expedientes_json.keys())

        diferencias = []

        # Solo en JSON (pendientes de sincronizar)
        solo_json = numeros_json - set(numeros_mysql.keys())
        for numero in list(solo_json)[:limite]:
            diferencias.append(DiferenciaSincronizacion(
                numero_normalizado=numero,
                estado="solo_json",
                id_json=expedientes_json[numero],
                id_mysql=None
            ))

        # Solo en MySQL (huérfanos - no deberían existir)
        solo_mysql = set(numeros_mysql.keys()) - numeros_json
        for numero in list(solo_mysql)[:limite - len(diferencias)]:
            diferencias.append(DiferenciaSincronizacion(
                numero_normalizado=numero,
                estado="solo_mysql",
                id_json=None,
                id_mysql=numeros_mysql[numero]
            ))

        return ComparacionSincronizacionResponse(
            total_diferencias=len(solo_json) + len(solo_mysql),
            solo_en_json=len(solo_json),
            solo_en_mysql=len(solo_mysql),
            diferencias=diferencias[:limite]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error comparando sincronización: {str(e)}")


@router.post("/sincronizacion/ejecutar", response_model=ResultadoSincronizacionResponse)
async def ejecutar_sincronizacion(
    _: bool = Depends(verify_superuser)
):
    """
    Ejecuta sincronización masiva desde JSON a MySQL.

    Returns:
        Estadísticas del resultado: procesados, creados, actualizados, errores
    """
    try:
        # Obtener ruta del índice
        gestor = GestorDirectoriosExpedientes.desde_config()
        ruta_indice = gestor._indice_path()

        # Ejecutar sincronización
        repo = get_expedientes_repository()
        stats = repo.sincronizar_desde_json(ruta_indice)

        return ResultadoSincronizacionResponse(
            procesados=stats['procesados'],
            creados=stats['creados'],
            actualizados=stats['actualizados'],
            errores=stats['errores'],
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error ejecutando sincronización: {str(e)}")


@router.get("/expedientes-mysql", response_model=List[ExpedienteMySQLResponse])
async def listar_expedientes_mysql(
    estado: Optional[str] = Query(None, description="Filtrar por estado: activo, pausado, omitido, archivado"),
    limite: int = Query(100, description="Límite de resultados"),
    offset: int = Query(0, description="Offset para paginación"),
    _: bool = Depends(verify_superuser)
):
    """
    Lista expedientes desde MySQL con filtros opcionales.

    Returns:
        Lista de expedientes con sus datos
    """
    try:
        repo = get_expedientes_repository()
        expedientes = repo.listar_todos(estado=estado)

        # Aplicar paginación
        expedientes_paginados = expedientes[offset:offset + limite]

        # Convertir a response model
        resultado = []
        for exp in expedientes_paginados:
            resultado.append(ExpedienteMySQLResponse(
                id=exp['id'],
                numero_normalizado=exp['numero_normalizado'],
                numero_original=exp['numero_original'],
                dependencia=exp.get('dependencia'),
                caratula=exp.get('caratula'),
                situacion=exp.get('situacion'),
                estado_monitoreo=exp.get('estado_monitoreo', 'activo'),
                prioridad=exp.get('prioridad', 'normal'),
                fecha_creacion=str(exp['fecha_creacion']) if exp.get('fecha_creacion') else '',
                fecha_ultima_extraccion=str(exp['fecha_ultima_extraccion']) if exp.get('fecha_ultima_extraccion') else None,
                total_actuaciones=exp.get('total_actuaciones', 0),
                total_pdfs_descargados=exp.get('total_pdfs_descargados', 0)
            ))

        return resultado

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listando expedientes: {str(e)}")


@router.get("/expedientes-mysql/count")
async def contar_expedientes_mysql(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    _: bool = Depends(verify_superuser)
):
    """
    Obtiene el conteo de expedientes en MySQL.

    Returns:
        Conteo total de expedientes
    """
    try:
        repo = get_expedientes_repository()

        if estado:
            expedientes = repo.listar_todos(estado=estado)
            count = len(expedientes)
        else:
            count = repo.contar()

        return {"count": count, "estado": estado}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error contando expedientes: {str(e)}")
