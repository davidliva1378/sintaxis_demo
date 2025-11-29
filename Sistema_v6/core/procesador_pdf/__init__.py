"""
Módulo procesador_pdf - Procesamiento inteligente de actuaciones judiciales.

Este módulo provee herramientas para:
- Clasificar actuaciones por utilidad jurídica
- Detectar duplicados exactos y semánticos
- Extraer texto de PDFs (embebido + OCR)
- Analizar vencimientos y plazos procesales

Uso básico:
    from core.procesador_pdf import (
        ClasificadorActuaciones,
        DetectorDuplicados,
        ExtractorTexto,
        AnalizadorVencimientos
    )

    # Clasificar actuaciones
    clasificador = ClasificadorActuaciones()
    clasificacion = clasificador.clasificar(
        tipo="SENTENCIA",
        detalle="Sentencia definitiva resolviendo el fondo del asunto"
    )

    # Detectar duplicados
    detector = DetectorDuplicados()
    duplicados = detector.detectar_duplicados_exactos(actuaciones)

    # Extraer texto de PDF
    extractor = ExtractorTexto()
    texto = extractor.extraer("ruta/al/archivo.pdf")

    # Analizar vencimientos
    analizador = AnalizadorVencimientos()
    vencimientos = analizador.analizar_texto(texto_cedula)

Versión: 1.0.0 (MVP - Fase 1)
Autor: Sistema jurídico sintaXis
"""

from .models import (
    # Enums
    UtilidadJuridica,
    TipoDuplicado,
    TipoVencimiento,
    # Dataclasses
    ClasificacionActuacion,
    DuplicadoDetectado,
    Vencimiento,
    TextoExtraido,
    ResultadoProcesamiento,
)

from .clasificador import ClasificadorActuaciones
from .detector_duplicados import DetectorDuplicados
from .extractor_texto import ExtractorTexto
from .analizador_vencimientos import AnalizadorVencimientos


__version__ = "1.0.0"
__author__ = "Sistema jurídico sintaXis"

__all__ = [
    # Modelos
    "UtilidadJuridica",
    "TipoDuplicado",
    "TipoVencimiento",
    "ClasificacionActuacion",
    "DuplicadoDetectado",
    "Vencimiento",
    "TextoExtraido",
    "ResultadoProcesamiento",
    # Clases principales
    "ClasificadorActuaciones",
    "DetectorDuplicados",
    "ExtractorTexto",
    "AnalizadorVencimientos",
    # Función helper principal
    "procesar_actuacion",
]


def procesar_actuacion(
    actuacion: dict,
    ruta_pdf: str = None,
    analizar_vencimientos: bool = True,
    detectar_duplicados: bool = False,
    actuaciones_comparar: list = None,
    usar_ocr: bool = True
) -> ResultadoProcesamiento:
    """
    Función helper para procesar una actuación completa.

    Ejecuta clasificación, extracción de texto (si hay PDF),
    análisis de vencimientos y detección de duplicados.

    Args:
        actuacion: Dict con datos de la actuación
            Debe contener: id, tipo, detalle, tiene_archivo
        ruta_pdf: Ruta al PDF (opcional, si tiene_archivo=True)
        analizar_vencimientos: Si analizar vencimientos
        detectar_duplicados: Si detectar duplicados
        actuaciones_comparar: Lista de actuaciones para comparar duplicados
        usar_ocr: Si usar OCR cuando no hay texto embebido (default: True)

    Returns:
        ResultadoProcesamiento con todos los análisis

    Example:
        >>> actuacion = {
        ...     "id": 1,
        ...     "tipo": "CEDULA_ELECTRONICA",
        ...     "detalle": "Notificación del 15/03/2024...",
        ...     "tiene_archivo": True
        ... }
        >>> resultado = procesar_actuacion(
        ...     actuacion,
        ...     ruta_pdf="/path/to/cedula.pdf",
        ...     analizar_vencimientos=True
        ... )
        >>> print(resultado.clasificacion.utilidad)
        UtilidadJuridica.ALTA
        >>> print(len(resultado.vencimientos))
        1
    """
    act_id = actuacion.get("id") or actuacion.get("Indice")
    errores = []

    # 1. Clasificación
    try:
        clasificador = ClasificadorActuaciones()
        clasificacion = clasificador.clasificar(
            tipo=actuacion.get("tipo") or actuacion.get("Tipo", ""),
            detalle=actuacion.get("detalle") or actuacion.get("Detalle", ""),
            tiene_archivo=actuacion.get("tiene_archivo") or actuacion.get("TieneArchivo", False)
        )
    except Exception as e:
        errores.append(f"Error en clasificación: {str(e)}")
        # Clasificación por defecto
        clasificacion = ClasificacionActuacion(
            utilidad=UtilidadJuridica.MEDIA,
            score=50,
            motivo="Error en clasificación automática"
        )

    # 2. Extracción de texto (si hay PDF)
    texto_extraido = None
    if ruta_pdf:
        try:
            extractor = ExtractorTexto(usar_ocr=usar_ocr)  # OCR configurable
            texto_extraido = extractor.extraer(ruta_pdf)
        except Exception as e:
            errores.append(f"Error en extracción de texto: {str(e)}")

    # 3. Análisis de vencimientos
    vencimientos = []
    if analizar_vencimientos and clasificacion.tiene_plazo_probable:
        try:
            analizador = AnalizadorVencimientos()
            vencimientos = analizador.analizar_actuacion(
                actuacion,
                extraer_de_pdf=bool(ruta_pdf),
                ruta_pdf=ruta_pdf
            )
        except Exception as e:
            errores.append(f"Error en análisis de vencimientos: {str(e)}")

    # 4. Detección de duplicados
    duplicados = []
    if detectar_duplicados and actuaciones_comparar:
        try:
            detector = DetectorDuplicados()
            # Agregar la actuación actual a la lista para comparar
            todas = actuaciones_comparar + [actuacion]
            todos_duplicados = detector.detectar_duplicados_exactos(todas)
            # Filtrar solo los que involucran a esta actuación
            duplicados = [
                d for d in todos_duplicados
                if d.actuacion_id_original == act_id or d.actuacion_id_duplicada == act_id
            ]
        except Exception as e:
            errores.append(f"Error en detección de duplicados: {str(e)}")

    return ResultadoProcesamiento(
        actuacion_id=act_id,
        clasificacion=clasificacion,
        texto=texto_extraido,
        duplicados=duplicados,
        vencimientos=vencimientos,
        errores=errores
    )


def procesar_expediente(
    actuaciones: list,
    rutas_pdf: dict = None,
    analizar_vencimientos: bool = True,
    detectar_duplicados: bool = True
) -> dict:
    """
    Procesa todas las actuaciones de un expediente.

    Args:
        actuaciones: Lista de actuaciones del expediente
        rutas_pdf: Dict {actuacion_id: ruta_pdf}
        analizar_vencimientos: Si analizar vencimientos
        detectar_duplicados: Si detectar duplicados

    Returns:
        Dict con resultados y estadísticas:
        {
            "resultados": {act_id: ResultadoProcesamiento},
            "estadisticas": {...},
            "vencimientos_urgentes": [...],
            "duplicados_detectados": [...]
        }

    Example:
        >>> actuaciones = [...]  # Lista de actuaciones
        >>> resultados = procesar_expediente(
        ...     actuaciones,
        ...     rutas_pdf={1: "path1.pdf", 2: "path2.pdf"}
        ... )
        >>> print(resultados["estadisticas"]["reduccion_estimada"])
        35.5
    """
    resultados = {}
    rutas_pdf = rutas_pdf or {}

    # Procesar cada actuación
    for actuacion in actuaciones:
        act_id = actuacion.get("id") or actuacion.get("Indice")
        
        # Robust lookup for ruta_pdf
        ruta_pdf = rutas_pdf.get(act_id)
        if not ruta_pdf and act_id is not None:
            # Try casting to int/str if direct lookup failed
            try:
                ruta_pdf = rutas_pdf.get(int(act_id)) or rutas_pdf.get(str(act_id))
            except (ValueError, TypeError):
                pass
        
        resultado = procesar_actuacion(
            actuacion=actuacion,
            ruta_pdf=ruta_pdf,
            analizar_vencimientos=analizar_vencimientos,
            detectar_duplicados=False,  # Lo hacemos después en batch
            actuaciones_comparar=None
        )
        resultados[act_id] = resultado

    # Detección de duplicados en batch
    duplicados_globales = []
    if detectar_duplicados:
        try:
            detector = DetectorDuplicados()
            duplicados_globales = detector.detectar_duplicados_exactos(actuaciones)
            duplicados_cedulas = detector.detectar_cedulas_duplicadas(actuaciones)
            duplicados_globales.extend(duplicados_cedulas)

            # Actualizar resultados con duplicados
            for dup in duplicados_globales:
                if dup.actuacion_id_original in resultados:
                    resultados[dup.actuacion_id_original].duplicados.append(dup)
                if dup.actuacion_id_duplicada in resultados:
                    resultados[dup.actuacion_id_duplicada].duplicados.append(dup)
        except Exception as e:
            pass  # Error en duplicados no es crítico

    # Recopilar todos los vencimientos
    todos_vencimientos = []
    for resultado in resultados.values():
        todos_vencimientos.extend(resultado.vencimientos)

    # Filtrar vencimientos urgentes
    analizador = AnalizadorVencimientos()
    vencimientos_urgentes = analizador.filtrar_vencimientos_urgentes(todos_vencimientos)

    # Generar estadísticas
    clasificador = ClasificadorActuaciones()
    clasificaciones = {
        act_id: res.clasificacion
        for act_id, res in resultados.items()
    }
    estadisticas = clasificador.estadisticas_clasificacion(clasificaciones)

    # Estadísticas de duplicados
    if duplicados_globales:
        detector = DetectorDuplicados()
        stats_duplicados = detector.estadisticas_duplicados(duplicados_globales)
        estadisticas["duplicados"] = stats_duplicados

    return {
        "resultados": resultados,
        "estadisticas": estadisticas,
        "vencimientos_urgentes": vencimientos_urgentes,
        "vencimientos_totales": len(todos_vencimientos),
        "duplicados_detectados": duplicados_globales,
        "total_actuaciones": len(actuaciones),
        "con_errores": len([r for r in resultados.values() if r.tiene_errores])
    }
