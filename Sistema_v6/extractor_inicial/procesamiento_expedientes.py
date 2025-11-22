"""
Módulo de procesamiento de expedientes para el flujo de extracción inicial.

Este módulo integra procesador_pdf en el flujo de extracción inicial para
proporcionar:
- Clasificación automática de actuaciones
- Detección de vencimientos urgentes
- Análisis de duplicados
- Generación de reportes enriquecidos

Integración: Tarea 4 - procesador_pdf2.1
Fecha: 2025-11-03
"""

import json
import asyncio
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
import logging

# Intentar importar procesador_pdf (opcional)
try:
    from core.procesador_pdf import (
        ClasificadorActuaciones,
        DetectorDuplicados,
        AnalizadorVencimientos,
        UtilidadJuridica
    )
    PROCESADOR_DISPONIBLE = True
except ImportError:
    PROCESADOR_DISPONIBLE = False
    logging.warning(
        "procesador_pdf no disponible. El procesamiento de actuaciones no estará disponible."
    )

# Importar módulos de extracción de actuaciones
try:
    from panel_pjn.acciones_pjn.gestion_actuaciones import extraer_actuaciones_completas
    EXTRACCION_DISPONIBLE = True
except ImportError:
    EXTRACCION_DISPONIBLE = False
    logging.warning("Módulo de extracción de actuaciones no disponible.")


logger = logging.getLogger(__name__)


class ProcesadorExpedientesInicial:
    """
    Procesador de expedientes para el flujo de extracción inicial.

    Integra procesador_pdf para clasificar y analizar actuaciones
    automáticamente durante la extracción inicial.
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el procesador.

        Args:
            config: Configuración opcional con:
                - clasificar: bool (default: True)
                - analizar_vencimientos: bool (default: True)
                - detectar_duplicados: bool (default: False)
                - dias_urgentes: int (default: 7)
                - min_utilidad: str (default: "MEDIA") - BAJA, MEDIA, ALTA
                - extraer_actuaciones: bool (default: False)
                - guardar_reportes: bool (default: True)

        Raises:
            ImportError: Si procesador_pdf no está disponible
        """
        if not PROCESADOR_DISPONIBLE:
            raise ImportError(
                "procesador_pdf no disponible. No se puede inicializar el procesador."
            )

        self.config = {
            "clasificar": True,
            "analizar_vencimientos": True,
            "detectar_duplicados": False,
            "dias_urgentes": 7,
            "min_utilidad": "MEDIA",
            "extraer_actuaciones": False,
            "guardar_reportes": True,
        }

        if config:
            self.config.update(config)

        # Inicializar componentes de procesador_pdf
        self.clasificador = ClasificadorActuaciones()
        self.analizador_vencimientos = AnalizadorVencimientos()

        if self.config["detectar_duplicados"]:
            self.detector_duplicados = DetectorDuplicados()
        else:
            self.detector_duplicados = None

    async def procesar_expedientes_extraidos(
        self,
        expedientes: List[Dict],
        page=None,
        carpeta_base: str = "datos_extraidos/extraccion_inicial"
    ) -> Dict:
        """
        Procesa una lista de expedientes extraídos.

        Args:
            expedientes: Lista de expedientes con estructura:
                {
                    "numero": str,
                    "caratula": str,
                    "dependencia": str,
                    "situacion": str,
                    "ultima_actuacion": str,
                }
            page: Objeto Page de Playwright (opcional, para extraer actuaciones)
            carpeta_base: Carpeta donde guardar resultados

        Returns:
            Dict con estadísticas y resultados:
            {
                "total_expedientes": int,
                "expedientes_procesados": int,
                "estadisticas_clasificacion": {...},
                "vencimientos_urgentes": [...],
                "errores": [...]
            }
        """
        if not expedientes:
            logger.warning("No hay expedientes para procesar")
            return self._resultado_vacio()

        logger.info(f"Iniciando procesamiento de {len(expedientes)} expedientes")

        carpeta_base_path = Path(carpeta_base)
        carpeta_base_path.mkdir(parents=True, exist_ok=True)

        # Estructuras para resultados
        estadisticas = {
            "total": len(expedientes),
            "procesados": 0,
            "con_actuaciones": 0,
            "sin_actuaciones": 0,
            "errores": 0,
            "utilidad_alta": 0,
            "utilidad_media": 0,
            "utilidad_baja": 0,
            "utilidad_nula": 0,
        }

        vencimientos_urgentes = []
        duplicados_encontrados = []
        errores = []

        # Procesar cada expediente
        for i, expediente in enumerate(expedientes, 1):
            numero = expediente.get("numero", "DESCONOCIDO")
            logger.info(f"[{i}/{len(expedientes)}] Procesando expediente {numero}")

            try:
                # Si se debe extraer actuaciones y tenemos page
                if self.config["extraer_actuaciones"] and page and EXTRACCION_DISPONIBLE:
                    resultado_extraccion = await self._extraer_y_procesar_actuaciones(
                        expediente, page, carpeta_base_path
                    )

                    if resultado_extraccion:
                        estadisticas["con_actuaciones"] += 1
                        # Agregar estadísticas de este expediente
                        self._agregar_estadisticas(
                            estadisticas,
                            resultado_extraccion.get("clasificaciones", [])
                        )

                        # Recopilar vencimientos urgentes
                        venc_urgentes = resultado_extraccion.get("vencimientos_urgentes", [])
                        if venc_urgentes:
                            for venc in venc_urgentes:
                                venc["expediente"] = numero
                            vencimientos_urgentes.extend(venc_urgentes)

                        # Recopilar duplicados
                        dups = resultado_extraccion.get("duplicados", [])
                        if dups:
                            duplicados_encontrados.extend(dups)
                    else:
                        estadisticas["sin_actuaciones"] += 1
                else:
                    # Solo clasificar expediente sin extraer actuaciones
                    estadisticas["sin_actuaciones"] += 1

                estadisticas["procesados"] += 1

            except Exception as e:
                logger.error(f"Error procesando expediente {numero}: {e}")
                estadisticas["errores"] += 1
                errores.append({
                    "expediente": numero,
                    "error": str(e)
                })

        # Generar reportes
        if self.config["guardar_reportes"]:
            await self._guardar_reportes(
                carpeta_base_path,
                estadisticas,
                vencimientos_urgentes,
                duplicados_encontrados,
                errores
            )

        resultado = {
            "total_expedientes": estadisticas["total"],
            "expedientes_procesados": estadisticas["procesados"],
            "estadisticas": estadisticas,
            "vencimientos_urgentes": vencimientos_urgentes,
            "duplicados": duplicados_encontrados,
            "errores": errores,
        }

        logger.info(f"Procesamiento completado: {estadisticas['procesados']}/{estadisticas['total']} expedientes")

        return resultado

    async def _extraer_y_procesar_actuaciones(
        self,
        expediente: Dict,
        page,
        carpeta_base: Path
    ) -> Optional[Dict]:
        """
        Extrae actuaciones de un expediente y las procesa.

        Args:
            expediente: Dict con datos del expediente
            page: Playwright Page object
            carpeta_base: Path donde guardar actuaciones

        Returns:
            Dict con resultados del procesamiento o None si falla
        """
        # TODO: Implementar navegación al expediente y extracción de actuaciones
        # Por ahora, retornamos None ya que requiere integración más profunda
        # con el sistema de navegación de Playwright
        logger.warning(
            f"Extracción de actuaciones no implementada para expediente {expediente.get('numero')}"
        )
        return None

    def clasificar_actuaciones_json(
        self,
        ruta_json: str | Path
    ) -> Dict:
        """
        Clasifica actuaciones desde un archivo JSON ya extraído.

        Args:
            ruta_json: Ruta al archivo JSON con actuaciones

        Returns:
            Dict con estadísticas y clasificaciones
        """
        ruta_json = Path(ruta_json)

        if not ruta_json.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {ruta_json}")

        with open(ruta_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        actuaciones = data.get("Actuaciones", [])

        if not actuaciones:
            logger.warning(f"No hay actuaciones en {ruta_json}")
            return self._resultado_vacio()

        logger.info(f"Clasificando {len(actuaciones)} actuaciones de {ruta_json}")

        # Clasificar cada actuación
        clasificaciones = []
        for act in actuaciones:
            clasificacion = self.clasificador.clasificar(
                tipo=act.get("Tipo", ""),
                detalle=act.get("Detalle", ""),
                tiene_archivo=act.get("TieneArchivo", False),
                texto_completo=""
            )

            clasificaciones.append({
                "fecha": act.get("Fecha"),
                "tipo": act.get("Tipo"),
                "detalle": act.get("Detalle"),
                "utilidad": clasificacion.utilidad.value,
                "score": clasificacion.score_confianza,
                "motivo": clasificacion.motivo_clasificacion,
                "tiene_plazo": clasificacion.tiene_plazo_probable,
            })

        # Generar estadísticas
        estadisticas = self._generar_estadisticas_clasificacion(clasificaciones)

        # Analizar vencimientos si está habilitado
        vencimientos = []
        if self.config["analizar_vencimientos"]:
            vencimientos = self._analizar_vencimientos_actuaciones(actuaciones)

        return {
            "archivo": str(ruta_json),
            "total_actuaciones": len(actuaciones),
            "clasificaciones": clasificaciones,
            "estadisticas": estadisticas,
            "vencimientos": vencimientos,
        }

    def _analizar_vencimientos_actuaciones(
        self,
        actuaciones: List[Dict]
    ) -> List[Dict]:
        """Analiza vencimientos en actuaciones."""
        vencimientos = []

        for act in actuaciones:
            # Analizar vencimiento
            resultado = self.analizador_vencimientos.analizar_actuacion(act)

            if resultado and resultado.fecha_vencimiento:
                vencimientos.append({
                    "fecha": act.get("Fecha"),
                    "tipo": act.get("Tipo"),
                    "detalle": act.get("Detalle"),
                    "fecha_notificacion": resultado.fecha_notificacion.isoformat() if resultado.fecha_notificacion else None,
                    "fecha_vencimiento": resultado.fecha_vencimiento.isoformat() if resultado.fecha_vencimiento else None,
                    "dias_restantes": resultado.dias_restantes,
                    "es_urgente": resultado.dias_restantes <= self.config["dias_urgentes"],
                    "tipo_plazo": resultado.tipo_plazo,
                })

        return vencimientos

    def _generar_estadisticas_clasificacion(
        self,
        clasificaciones: List[Dict]
    ) -> Dict:
        """Genera estadísticas de clasificaciones."""
        total = len(clasificaciones)

        if total == 0:
            return {
                "total": 0,
                "alta": 0,
                "media": 0,
                "baja": 0,
                "nula": 0,
                "porcentajes": {}
            }

        conteo = {
            "alta": sum(1 for c in clasificaciones if c["utilidad"] == "ALTA"),
            "media": sum(1 for c in clasificaciones if c["utilidad"] == "MEDIA"),
            "baja": sum(1 for c in clasificaciones if c["utilidad"] == "BAJA"),
            "nula": sum(1 for c in clasificaciones if c["utilidad"] == "NULA"),
        }

        return {
            "total": total,
            **conteo,
            "porcentajes": {
                "alta": round(conteo["alta"] / total * 100, 2),
                "media": round(conteo["media"] / total * 100, 2),
                "baja": round(conteo["baja"] / total * 100, 2),
                "nula": round(conteo["nula"] / total * 100, 2),
            }
        }

    def _agregar_estadisticas(
        self,
        estadisticas: Dict,
        clasificaciones: List[Dict]
    ):
        """Agrega estadísticas de clasificaciones al dict de estadísticas."""
        for c in clasificaciones:
            utilidad = c.get("utilidad", "").lower()
            key = f"utilidad_{utilidad}"
            if key in estadisticas:
                estadisticas[key] += 1

    async def _guardar_reportes(
        self,
        carpeta_base: Path,
        estadisticas: Dict,
        vencimientos_urgentes: List[Dict],
        duplicados: List[Dict],
        errores: List[Dict]
    ):
        """Guarda reportes de procesamiento."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        carpeta_reportes = carpeta_base / "reportes"
        carpeta_reportes.mkdir(parents=True, exist_ok=True)

        # Reporte de estadísticas
        reporte_stats = carpeta_reportes / f"estadisticas_{timestamp}.json"
        with open(reporte_stats, "w", encoding="utf-8") as f:
            json.dump(estadisticas, f, indent=2, ensure_ascii=False)
        logger.info(f"Estadísticas guardadas en {reporte_stats}")

        # Reporte de vencimientos urgentes
        if vencimientos_urgentes:
            reporte_venc = carpeta_reportes / f"vencimientos_urgentes_{timestamp}.json"
            with open(reporte_venc, "w", encoding="utf-8") as f:
                json.dump(vencimientos_urgentes, f, indent=2, ensure_ascii=False)
            logger.info(f"⚠️ {len(vencimientos_urgentes)} vencimientos urgentes guardados en {reporte_venc}")

        # Reporte de duplicados
        if duplicados:
            reporte_dups = carpeta_reportes / f"duplicados_{timestamp}.json"
            with open(reporte_dups, "w", encoding="utf-8") as f:
                json.dump(duplicados, f, indent=2, ensure_ascii=False)
            logger.info(f"Duplicados guardados en {reporte_dups}")

        # Reporte de errores
        if errores:
            reporte_err = carpeta_reportes / f"errores_{timestamp}.json"
            with open(reporte_err, "w", encoding="utf-8") as f:
                json.dump(errores, f, indent=2, ensure_ascii=False)
            logger.warning(f"❌ {len(errores)} errores guardados en {reporte_err}")

    def _resultado_vacio(self) -> Dict:
        """Retorna un resultado vacío."""
        return {
            "total_expedientes": 0,
            "expedientes_procesados": 0,
            "estadisticas": {},
            "vencimientos_urgentes": [],
            "duplicados": [],
            "errores": [],
        }


# Función auxiliar para uso desde CLI
def clasificar_actuaciones_desde_json(
    ruta_json: str | Path,
    config: Optional[Dict] = None
) -> Dict:
    """
    Función auxiliar para clasificar actuaciones desde un JSON.

    Args:
        ruta_json: Ruta al archivo JSON con actuaciones
        config: Configuración opcional

    Returns:
        Dict con resultados de clasificación

    Example:
        >>> resultado = clasificar_actuaciones_desde_json(
        ...     "datos_extraidos/expediente_123.json",
        ...     config={"dias_urgentes": 5}
        ... )
        >>> print(f"Actuaciones de utilidad ALTA: {resultado['estadisticas']['alta']}")
    """
    if not PROCESADOR_DISPONIBLE:
        raise ImportError("procesador_pdf no disponible")

    procesador = ProcesadorExpedientesInicial(config)
    return procesador.clasificar_actuaciones_json(ruta_json)
