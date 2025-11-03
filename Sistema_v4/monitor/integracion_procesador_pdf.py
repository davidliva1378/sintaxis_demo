"""
Integración del Procesador PDF con el Sistema de Monitoreo PJN
===============================================================

Este módulo proporciona funciones para integrar el procesador_pdf con el
sistema de monitoreo, permitiendo:

- Clasificación automática de actuaciones por utilidad jurídica
- Detección de vencimientos urgentes en expedientes
- Análisis detallado de duplicados
- Generación de reportes enriquecidos con análisis inteligente

Autor: Sistema sintaXis
Fecha: 2025-11-03
Tarea: Integración PJN Monitor con procesador_pdf (Tarea 2)
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime

# Intentar importar procesador_pdf
try:
    from Sistema_v5.procesador_pdf import (
        ClasificadorActuaciones,
        DetectorDuplicados,
        AnalizadorVencimientos,
        procesar_expediente,
        UtilidadJuridica
    )
    PROCESADOR_DISPONIBLE = True
except ImportError:
    PROCESADOR_DISPONIBLE = False
    logging.warning("procesador_pdf no disponible. Funciones de análisis deshabilitadas.")


logger = logging.getLogger(__name__)


def clasificar_actuaciones_expedientes(
    ruta_expedientes: str | Path,
    destino_clasificaciones: str | Path,
    config: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Clasifica actuaciones de expedientes extraídos.

    Args:
        ruta_expedientes: Ruta al archivo JSON con expedientes
        destino_clasificaciones: Directorio donde guardar resultados
        config: Configuración opcional de procesador_pdf

    Returns:
        Dict con estadísticas de clasificación o None si hay error

    Ejemplo:
        >>> stats = clasificar_actuaciones_expedientes(
        ...     "datos_extraidos/monitoreo/expedientes_monitor.json",
        ...     "datos_extraidos/monitoreo/clasificaciones"
        ... )
        >>> print(f"Alta utilidad: {stats['utilidad_alta']}")
    """
    if not PROCESADOR_DISPONIBLE:
        logger.warning("procesador_pdf no está disponible")
        return None

    try:
        ruta_exp = Path(ruta_expedientes)
        if not ruta_exp.exists():
            logger.error(f"Archivo no encontrado: {ruta_expedientes}")
            return None

        # Cargar expedientes
        with ruta_exp.open("r", encoding="utf-8") as f:
            expedientes = json.load(f)

        if not isinstance(expedientes, list) or not expedientes:
            logger.warning("No hay expedientes para clasificar")
            return None

        # Inicializar clasificador
        clasificador = ClasificadorActuaciones()

        # Procesar cada expediente
        total_actuaciones = 0
        clasificaciones_por_utilidad = {
            "ALTA": [],
            "MEDIA": [],
            "BAJA": [],
            "NULA": []
        }

        for exp in expedientes:
            numero = exp.get("numero_expediente", "")
            actuaciones = exp.get("actuaciones", [])

            for idx, act in enumerate(actuaciones):
                # Clasificar cada actuación
                clasificacion = clasificador.clasificar(
                    tipo=act.get("tipo", ""),
                    detalle=act.get("descripcion", ""),
                    tiene_archivo=act.get("tiene_archivo", False)
                )

                # Agregar a resultados
                utilidad = clasificacion.utilidad.value
                clasificaciones_por_utilidad[utilidad].append({
                    "expediente": numero,
                    "actuacion_idx": idx,
                    "fecha": act.get("fecha", ""),
                    "tipo": act.get("tipo", ""),
                    "descripcion": act.get("descripcion", "")[:200],  # Truncar
                    "score": clasificacion.score,
                    "motivo": clasificacion.motivo,
                    "keywords": clasificacion.keywords_detectados
                })

                total_actuaciones += 1

        # Generar reporte
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        reporte = {
            "timestamp": datetime.now().isoformat(),
            "total_expedientes": len(expedientes),
            "total_actuaciones": total_actuaciones,
            "clasificaciones": clasificaciones_por_utilidad,
            "estadisticas": {
                "utilidad_alta": len(clasificaciones_por_utilidad["ALTA"]),
                "utilidad_media": len(clasificaciones_por_utilidad["MEDIA"]),
                "utilidad_baja": len(clasificaciones_por_utilidad["BAJA"]),
                "utilidad_nula": len(clasificaciones_por_utilidad["NULA"]),
                "porcentaje_reduccion": round(
                    (len(clasificaciones_por_utilidad["NULA"]) +
                     len(clasificaciones_por_utilidad["BAJA"])) /
                    total_actuaciones * 100, 2
                ) if total_actuaciones > 0 else 0.0
            }
        }

        # Guardar reporte
        destino = Path(destino_clasificaciones)
        destino.mkdir(parents=True, exist_ok=True)
        ruta_reporte = destino / f"clasificaciones_{timestamp}.json"

        with ruta_reporte.open("w", encoding="utf-8") as f:
            json.dump(reporte, f, ensure_ascii=False, indent=2)

        logger.info(
            f"Clasificación completada: {total_actuaciones} actuaciones clasificadas. "
            f"Reporte: {ruta_reporte}"
        )

        return reporte["estadisticas"]

    except Exception as e:
        logger.error(f"Error al clasificar actuaciones: {e}")
        return None


def detectar_vencimientos_urgentes(
    ruta_expedientes: str | Path,
    destino_alertas: str | Path,
    dias_urgentes: int = 7,
    config: Optional[Dict] = None
) -> Optional[Tuple[List[Dict], int]]:
    """
    Detecta vencimientos urgentes en expedientes.

    Args:
        ruta_expedientes: Ruta al archivo JSON con expedientes
        destino_alertas: Directorio donde guardar alertas
        dias_urgentes: Días restantes para considerar urgente
        config: Configuración opcional

    Returns:
        Tuple (vencimientos_urgentes, total_vencimientos) o None si hay error

    Ejemplo:
        >>> urgentes, total = detectar_vencimientos_urgentes(
        ...     "expedientes_monitor.json",
        ...     "datos_extraidos/monitoreo/alertas",
        ...     dias_urgentes=5
        ... )
        >>> print(f"{len(urgentes)} vencimientos urgentes de {total}")
    """
    if not PROCESADOR_DISPONIBLE:
        logger.warning("procesador_pdf no está disponible")
        return None

    try:
        ruta_exp = Path(ruta_expedientes)
        if not ruta_exp.exists():
            logger.error(f"Archivo no encontrado: {ruta_expedientes}")
            return None

        # Cargar expedientes
        with ruta_exp.open("r", encoding="utf-8") as f:
            expedientes = json.load(f)

        if not isinstance(expedientes, list):
            logger.warning("Formato de expedientes inválido")
            return None

        # Inicializar analizador
        analizador = AnalizadorVencimientos()

        vencimientos_urgentes = []
        total_vencimientos = 0

        for exp in expedientes:
            numero = exp.get("numero_expediente", "")
            actuaciones = exp.get("actuaciones", [])

            for act in actuaciones:
                # Analizar actuación para vencimientos
                vencimientos = analizador.analizar_actuacion(
                    {
                        "tipo": act.get("tipo", ""),
                        "detalle": act.get("descripcion", ""),
                        "fecha": act.get("fecha", "")
                    }
                )

                for venc in vencimientos:
                    total_vencimientos += 1

                    if venc.es_urgente and venc.dias_restantes <= dias_urgentes:
                        vencimientos_urgentes.append({
                            "expediente": numero,
                            "actuacion_fecha": act.get("fecha", ""),
                            "actuacion_tipo": act.get("tipo", ""),
                            "actuacion_descripcion": act.get("descripcion", "")[:200],
                            "tipo_vencimiento": venc.tipo.value,
                            "fecha_notificacion": venc.fecha_notificacion.isoformat() if venc.fecha_notificacion else None,
                            "fecha_vencimiento": venc.fecha_vencimiento.isoformat() if venc.fecha_vencimiento else None,
                            "dias_restantes": venc.dias_restantes,
                            "descripcion": venc.descripcion,
                            "urgente": True
                        })

        # Ordenar por días restantes (más urgente primero)
        vencimientos_urgentes.sort(key=lambda x: x["dias_restantes"])

        # Guardar alertas
        if vencimientos_urgentes:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            destino = Path(destino_alertas)
            destino.mkdir(parents=True, exist_ok=True)
            ruta_alertas = destino / f"vencimientos_urgentes_{timestamp}.json"

            reporte_alertas = {
                "timestamp": datetime.now().isoformat(),
                "dias_umbral_urgente": dias_urgentes,
                "total_vencimientos": total_vencimientos,
                "vencimientos_urgentes": len(vencimientos_urgentes),
                "alertas": vencimientos_urgentes
            }

            with ruta_alertas.open("w", encoding="utf-8") as f:
                json.dump(reporte_alertas, f, ensure_ascii=False, indent=2)

            logger.info(
                f"Detectados {len(vencimientos_urgentes)} vencimientos urgentes "
                f"de {total_vencimientos} totales. Alertas: {ruta_alertas}"
            )

        return (vencimientos_urgentes, total_vencimientos)

    except Exception as e:
        logger.error(f"Error al detectar vencimientos: {e}")
        return None


def analizar_duplicados_detallado(
    ruta_expedientes: str | Path,
    destino_analisis: str | Path,
    config: Optional[Dict] = None
) -> Optional[Dict]:
    """
    Analiza duplicados en expedientes con detalle.

    Args:
        ruta_expedientes: Ruta al archivo JSON con expedientes
        destino_analisis: Directorio donde guardar análisis
        config: Configuración opcional

    Returns:
        Dict con estadísticas de duplicados o None si hay error
    """
    if not PROCESADOR_DISPONIBLE:
        logger.warning("procesador_pdf no está disponible")
        return None

    try:
        ruta_exp = Path(ruta_expedientes)
        if not ruta_exp.exists():
            logger.error(f"Archivo no encontrado: {ruta_expedientes}")
            return None

        # Cargar expedientes
        with ruta_exp.open("r", encoding="utf-8") as f:
            expedientes = json.load(f)

        if not isinstance(expedientes, list):
            logger.warning("Formato de expedientes inválido")
            return None

        # Inicializar detector
        detector = DetectorDuplicados()

        # Preparar actuaciones para análisis
        actuaciones_para_analisis = []
        for exp in expedientes:
            numero = exp.get("numero_expediente", "")
            actuaciones = exp.get("actuaciones", [])

            for idx, act in enumerate(actuaciones):
                actuaciones_para_analisis.append({
                    "id": f"{numero}_{idx}",
                    "expediente": numero,
                    "tipo": act.get("tipo", ""),
                    "detalle": act.get("descripcion", ""),
                    "fecha": act.get("fecha", "")
                })

        # Detectar duplicados
        duplicados_exactos = detector.detectar_duplicados_exactos(actuaciones_para_analisis)
        duplicados_cedulas = detector.detectar_cedulas_duplicadas(actuaciones_para_analisis)

        # Combinar resultados
        todos_duplicados = duplicados_exactos + duplicados_cedulas

        # Generar reporte
        reporte_duplicados = {
            "timestamp": datetime.now().isoformat(),
            "total_actuaciones": len(actuaciones_para_analisis),
            "duplicados_exactos": len(duplicados_exactos),
            "duplicados_cedulas": len(duplicados_cedulas),
            "total_duplicados": len(todos_duplicados),
            "detalles": []
        }

        for dup in todos_duplicados:
            reporte_duplicados["detalles"].append({
                "tipo": dup.tipo.value,
                "actuacion_original": dup.actuacion_id_original,
                "actuacion_duplicada": dup.actuacion_id_duplicada,
                "motivo": dup.motivo
            })

        # Guardar reporte
        if todos_duplicados:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            destino = Path(destino_analisis)
            destino.mkdir(parents=True, exist_ok=True)
            ruta_reporte = destino / f"duplicados_{timestamp}.json"

            with ruta_reporte.open("w", encoding="utf-8") as f:
                json.dump(reporte_duplicados, f, ensure_ascii=False, indent=2)

            logger.info(
                f"Análisis de duplicados: {len(todos_duplicados)} encontrados. "
                f"Reporte: {ruta_reporte}"
            )

        return {
            "total_duplicados": len(todos_duplicados),
            "duplicados_exactos": len(duplicados_exactos),
            "duplicados_cedulas": len(duplicados_cedulas)
        }

    except Exception as e:
        logger.error(f"Error al analizar duplicados: {e}")
        return None


def procesar_expedientes_monitor(
    ruta_expedientes: str | Path,
    directorio_base: str | Path,
    config: Dict
) -> Dict:
    """
    Ejecuta procesamiento completo de expedientes del monitor.

    Esta es la función principal que orquesta todo el procesamiento:
    - Clasificación de actuaciones
    - Detección de vencimientos
    - Análisis de duplicados

    Args:
        ruta_expedientes: Ruta al archivo JSON con expedientes
        directorio_base: Directorio base para guardar resultados
        config: Configuración de procesador_pdf desde config_monitor.json

    Returns:
        Dict con resumen de todo el procesamiento

    Ejemplo:
        >>> config = {"habilitado": True, "clasificacion_automatica": True, ...}
        >>> resumen = procesar_expedientes_monitor(
        ...     "datos_extraidos/monitoreo/expedientes_monitor.json",
        ...     "datos_extraidos/monitoreo",
        ...     config
        ... )
        >>> print(resumen)
    """
    if not PROCESADOR_DISPONIBLE:
        return {
            "error": "procesador_pdf no disponible",
            "timestamp": datetime.now().isoformat()
        }

    if not config.get("habilitado", True):
        return {
            "mensaje": "Procesamiento deshabilitado en configuración",
            "timestamp": datetime.now().isoformat()
        }

    dir_base = Path(directorio_base)
    resumen = {
        "timestamp": datetime.now().isoformat(),
        "clasificacion": None,
        "vencimientos": None,
        "duplicados": None,
        "errores": []
    }

    # Clasificación
    if config.get("clasificacion_automatica", True):
        try:
            stats_clasificacion = clasificar_actuaciones_expedientes(
                ruta_expedientes,
                dir_base / "clasificaciones",
                config
            )
            resumen["clasificacion"] = stats_clasificacion
        except Exception as e:
            resumen["errores"].append(f"Error en clasificación: {e}")
            logger.error(f"Error en clasificación: {e}")

    # Vencimientos
    if config.get("vencimientos_automaticos", True):
        try:
            dias_urgentes = config.get("dias_urgentes", 7)
            resultado_venc = detectar_vencimientos_urgentes(
                ruta_expedientes,
                dir_base / "alertas",
                dias_urgentes,
                config
            )
            if resultado_venc:
                vencimientos_urgentes, total = resultado_venc
                resumen["vencimientos"] = {
                    "urgentes": len(vencimientos_urgentes),
                    "total": total,
                    "dias_umbral": dias_urgentes
                }
        except Exception as e:
            resumen["errores"].append(f"Error en vencimientos: {e}")
            logger.error(f"Error en vencimientos: {e}")

    # Duplicados
    if config.get("duplicados_analisis", True):
        try:
            stats_duplicados = analizar_duplicados_detallado(
                ruta_expedientes,
                dir_base / "duplicados",
                config
            )
            resumen["duplicados"] = stats_duplicados
        except Exception as e:
            resumen["errores"].append(f"Error en duplicados: {e}")
            logger.error(f"Error en duplicados: {e}")

    return resumen


# Función auxiliar para registrar en el log del monitor
def registrar_resultado_procesamiento(resumen: Dict, log_function=None):
    """
    Registra el resultado del procesamiento en el log del monitor.

    Args:
        resumen: Dict retornado por procesar_expedientes_monitor()
        log_function: Función de logging a usar (opcional)
    """
    log = log_function or logger.info

    log("="*60)
    log("📊 RESUMEN DE PROCESAMIENTO INTELIGENTE")
    log("="*60)

    if resumen.get("error"):
        log(f"❌ {resumen['error']}")
        return

    if resumen.get("mensaje"):
        log(f"ℹ️ {resumen['mensaje']}")
        return

    # Clasificación
    if resumen.get("clasificacion"):
        stats = resumen["clasificacion"]
        log(f"📋 Clasificación:")
        log(f"   • Utilidad ALTA:  {stats['utilidad_alta']}")
        log(f"   • Utilidad MEDIA: {stats['utilidad_media']}")
        log(f"   • Utilidad BAJA:  {stats['utilidad_baja']}")
        log(f"   • Utilidad NULA:  {stats['utilidad_nula']}")
        log(f"   • Reducción estimada: {stats['porcentaje_reduccion']}%")

    # Vencimientos
    if resumen.get("vencimientos"):
        venc = resumen["vencimientos"]
        log(f"⏰ Vencimientos:")
        log(f"   • Urgentes (≤{venc['dias_umbral']} días): {venc['urgentes']}")
        log(f"   • Total detectados: {venc['total']}")

    # Duplicados
    if resumen.get("duplicados"):
        dup = resumen["duplicados"]
        log(f"🔍 Duplicados:")
        log(f"   • Exactos: {dup['duplicados_exactos']}")
        log(f"   • Cédulas: {dup['duplicados_cedulas']}")
        log(f"   • Total: {dup['total_duplicados']}")

    # Errores
    if resumen.get("errores"):
        log("⚠️ Errores:")
        for error in resumen["errores"]:
            log(f"   • {error}")

    log("="*60)


__all__ = [
    "PROCESADOR_DISPONIBLE",
    "clasificar_actuaciones_expedientes",
    "detectar_vencimientos_urgentes",
    "analizar_duplicados_detallado",
    "procesar_expedientes_monitor",
    "registrar_resultado_procesamiento",
]
