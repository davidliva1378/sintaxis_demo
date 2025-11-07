"""
Módulo principal de extracción masiva de expedientes del PJN.

Este módulo implementa la lógica principal para extraer grandes
volúmenes de expedientes del portal del Poder Judicial de la Nación.
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Callable
import json
import asyncio
import logging

from Sistema_v6.configuracion.config import Config
from Sistema_v6.configuracion.estados import GestorEstados, EstadoExpediente
from Sistema_v6.configuracion.urls import URL_CONSULTAS
from Sistema_v6.pjn.auto_login import reutilizar_sesion_async
from Sistema_v6.pjn.scraping.expedientes import extraer_expedientes_completos
from Sistema_v6.pjn.models.extraccion_config import ExtraccionExpedientesConfig

logger = logging.getLogger(__name__)


class ConfigExtraccionMasiva:
    """Configuración para extracción masiva de expedientes."""

    def __init__(
        self,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        estados: Optional[List[EstadoExpediente]] = None,
        dependencias: Optional[List[str]] = None,
        descargar_adjuntos: bool = True,
        headless: bool = True,
        umbral_errores: int = 5,
        timeout_por_expediente: int = 120,
    ):
        """
        Inicializar configuración de extracción masiva.

        Args:
            fecha_desde: Fecha desde (formato DD/MM/YYYY)
            fecha_hasta: Fecha hasta (formato DD/MM/YYYY)
            estados: Lista de estados a filtrar
            dependencias: Lista de dependencias a filtrar
            descargar_adjuntos: Si descargar archivos adjuntos
            headless: Ejecutar navegador en modo headless
            umbral_errores: Número de errores consecutivos antes de pausar
            timeout_por_expediente: Timeout en segundos por expediente
        """
        self.fecha_desde = fecha_desde
        self.fecha_hasta = fecha_hasta
        self.estados = estados or [
            EstadoExpediente.MONITOREADO,
            EstadoExpediente.PRIORIZADO,
        ]
        self.dependencias = dependencias or []
        self.descargar_adjuntos = descargar_adjuntos
        self.headless = headless
        self.umbral_errores = umbral_errores
        self.timeout_por_expediente = timeout_por_expediente

    def to_dict(self) -> Dict:
        """Convertir configuración a diccionario."""
        # Manejar estados que pueden ser strings o enums
        if self.estados:
            estados_list = []
            for e in self.estados:
                if isinstance(e, str):
                    estados_list.append(e)
                else:
                    # Es un enum EstadoExpediente
                    estados_list.append(e.value)
        else:
            estados_list = []

        return {
            "fecha_desde": self.fecha_desde,
            "fecha_hasta": self.fecha_hasta,
            "estados": estados_list,
            "dependencias": self.dependencias,
            "descargar_adjuntos": self.descargar_adjuntos,
            "headless": self.headless,
            "umbral_errores": self.umbral_errores,
            "timeout_por_expediente": self.timeout_por_expediente,
        }


class ExtractorMasivo:
    """
    Extractor masivo de expedientes del PJN.

    Esta clase orquesta todo el proceso de extracción masiva:
    1. Extrae el listado completo de expedientes
    2. Filtra por estados si es necesario
    3. Procesa expedientes por lotes
    4. Emite eventos de progreso vía callbacks
    5. Genera reportes finales
    """

    def __init__(self, config: ConfigExtraccionMasiva, callbacks: Optional[Dict[str, Callable]] = None):
        """
        Inicializar extractor masivo.

        Args:
            config: Configuración de extracción
            callbacks: Diccionario de funciones callback para eventos (opcional)
        """
        self.config = config
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.callbacks: Dict[str, Callable] = callbacks or {}
        self.cancelado = False

        # Paths de guardado
        self.listados_dir = Config.DATA_DIR / "extraccion_masiva" / "listados"
        self.reportes_dir = Config.DATA_DIR / "extraccion_masiva" / "reportes"
        self.logs_dir = Config.DATA_DIR / "extraccion_masiva" / "logs"
        self.session_dir = Config.DATA_DIR / "extraccion_masiva" / "sesiones" / self.session_id

        # Crear directorios si no existen
        self.listados_dir.mkdir(parents=True, exist_ok=True)
        self.reportes_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.session_dir.mkdir(parents=True, exist_ok=True)

    def set_callback(self, evento: str, func: Callable):
        """
        Registrar callback para un evento.

        Args:
            evento: Nombre del evento
            func: Función callback a ejecutar
        """
        self.callbacks[evento] = func
        logger.debug(f"Callback registrado para evento: {evento}")

    def _emit(self, evento: str, data: Dict):
        """
        Emitir evento a través de callback.

        Args:
            evento: Nombre del evento
            data: Datos del evento
        """
        if evento in self.callbacks:
            try:
                import asyncio
                import inspect

                callback = self.callbacks[evento]

                # Determinar qué parámetros pasar según el evento
                if evento == "inicio_listado":
                    args = ()
                elif evento == "progreso_listado":
                    args = (data.get("pagina", 0), data.get("total_paginas", 0))
                elif evento == "fin_listado":
                    args = (data.get("expedientes", []),)
                elif evento == "inicio_batch":
                    args = (data.get("total", 0),)
                elif evento == "progreso_batch":
                    args = (data.get("idx", 0), data.get("total", 0), data.get("resultado", {}))
                elif evento == "fin_batch":
                    args = (data.get("resumen", {}),)
                elif evento == "error":
                    args = (data.get("mensaje", "Error desconocido"),)
                else:
                    args = (data,)

                # Llamar al callback (sync o async)
                if inspect.iscoroutinefunction(callback):
                    # Es async, ejecutar en el event loop
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Si ya hay un loop corriendo, crear una tarea
                            asyncio.create_task(callback(*args))
                        else:
                            # Si no hay loop, ejecutar con run_until_complete
                            loop.run_until_complete(callback(*args))
                    except RuntimeError:
                        # Si no hay event loop, crear uno nuevo
                        asyncio.run(callback(*args))
                else:
                    # Es sync, llamar directamente
                    callback(*args)

            except Exception as e:
                logger.error(f"Error en callback {evento}: {e}")
        else:
            logger.debug(f"Evento emitido (sin callback): {evento}")

    async def extraer_listado_completo(self) -> List[Dict]:
        """
        FASE 1: Extraer listado completo de expedientes del PJN.

        Extrae todas las páginas del listado de expedientes usando
        el módulo existente de extracción.

        Returns:
            Lista de diccionarios con datos de expedientes

        Raises:
            Exception: Si hay error durante la extracción
        """
        logger.info("Iniciando extracción del listado completo")
        self._emit("inicio_listado", {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "config": self.config.to_dict(),
        })

        expedientes = []
        paginas_procesadas = 0

        try:
            async with reutilizar_sesion_async() as (page, context, browser):
                logger.info(f"Navegando a {URL_CONSULTAS}")
                await page.goto(URL_CONSULTAS)
                await page.wait_for_load_state("domcontentloaded")

                # Callback de progreso para la extracción
                def callback_progreso(mensaje: str, total_acumulado: int):
                    nonlocal paginas_procesadas
                    # Detectar cuándo se procesa una nueva página
                    if "Página" in mensaje and "procesada" in mensaje:
                        paginas_procesadas += 1

                    self._emit("progreso_listado", {
                        "pagina": paginas_procesadas,
                        "total_expedientes": total_acumulado,
                        "mensaje": mensaje,
                    })

                # Configurar extracción optimizada
                config = ExtraccionExpedientesConfig(
                    omitir_duplicados=False,  # Queremos TODOS los expedientes
                    detener_en_duplicado=False,
                    fecha_corte=self.config.fecha_desde,
                    max_paginas=None,  # Sin límite
                )

                # Usar función optimizada que extrae todo automáticamente
                logger.info("Iniciando extracción masiva optimizada...")
                resultados, motivo, metadata = await extraer_expedientes_completos(
                    page=page,
                    config=config,
                    callback_progreso=callback_progreso,
                )

                # Convertir ExpedienteResumen a dict si es necesario
                expedientes = [
                    exp.to_dict() if hasattr(exp, 'to_dict') else exp
                    for exp in resultados
                ]

                logger.info(
                    f"Extracción completada: {len(expedientes)} expedientes, "
                    f"motivo: {motivo}, metadata: {metadata}"
                )

        except Exception as e:
            logger.error(f"Error durante extracción del listado: {e}")
            self._emit("error", {
                "mensaje": f"Error al extraer listado: {str(e)}",
                "timestamp": datetime.now().isoformat(),
            })
            raise

        # Guardar listado completo
        listado_path = self.listados_dir / f"listado_{self.session_id}.json"
        logger.info(f"Guardando listado en {listado_path}")

        with open(listado_path, "w", encoding="utf-8") as f:
            json.dump(expedientes, f, indent=2, ensure_ascii=False)

        self._emit("fin_listado", {
            "total": len(expedientes),
            "archivo": str(listado_path),
            "paginas_procesadas": paginas_procesadas,
        })

        logger.info(f"Extracción completa: {len(expedientes)} expedientes en {paginas_procesadas} páginas")
        return expedientes

    async def procesar_lote_expedientes(
        self,
        expedientes: List[Dict]
    ) -> Dict:
        """
        FASE 2: Procesar lote de expedientes.

        Args:
            expedientes: Lista de expedientes a procesar

        Returns:
            Diccionario con resumen del procesamiento
        """
        from Sistema_v6.extraccion_masiva.gestor_batch import GestorBatch

        logger.info(f"Iniciando procesamiento de {len(expedientes)} expedientes")
        self._emit("inicio_batch", {
            "total": len(expedientes),
            "timestamp": datetime.now().isoformat(),
        })

        # Crear gestor de batch
        gestor = GestorBatch(
            umbral_errores=self.config.umbral_errores,
            callback_progreso=lambda data: self._emit("progreso_batch", data)
        )

        # Procesar
        resumen = await gestor.procesar_lote(
            expedientes,
            descargar_adjuntos=self.config.descargar_adjuntos,
            headless=self.config.headless
        )

        resumen_dict = resumen.to_dict()
        self._emit("fin_batch", resumen_dict)

        logger.info(f"Procesamiento completado: {resumen.exitosos}/{resumen.total} exitosos")
        return resumen_dict

    async def ejecutar_extraccion_completa(self) -> Dict:
        """
        Ejecutar extracción masiva completa (listado + procesamiento).

        Este es el método principal que orquesta todo el flujo:
        1. Extrae el listado completo
        2. Filtra por estados si es necesario
        3. Procesa expedientes por lotes
        4. Genera reporte final

        Returns:
            Diccionario con resultado completo de la extracción

        Raises:
            Exception: Si hay error durante la extracción
        """
        logger.info("=" * 60)
        logger.info("INICIANDO EXTRACCIÓN MASIVA")
        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"Configuración: {self.config.to_dict()}")
        logger.info("=" * 60)

        try:
            # Fase 1: Extraer listado
            logger.info("FASE 1: Extracción del listado completo")
            expedientes = await self.extraer_listado_completo()

            if self.cancelado:
                logger.warning("Extracción cancelada por el usuario")
                return {
                    "estado": "cancelado",
                    "mensaje": "Extracción cancelada por el usuario",
                    "session_id": self.session_id,
                }

            if not expedientes:
                logger.warning("No se extrajeron expedientes")
                return {
                    "estado": "completado",
                    "mensaje": "No se encontraron expedientes",
                    "session_id": self.session_id,
                    "total": 0,
                }

            # Filtrar por estados si es necesario
            if self.config.estados:
                # Manejar estados que pueden ser strings o enums
                estados_str = []
                for e in self.config.estados:
                    if isinstance(e, str):
                        estados_str.append(e)
                    else:
                        estados_str.append(e.value)
                logger.info(f"Filtrando por estados: {estados_str}")
                gestor_estados = GestorEstados()
                gestor_estados.cargar_estados()

                # Inicializar expedientes si no existen
                numeros = [exp.get("numero") for exp in expedientes]
                gestor_estados.inicializar_expedientes(
                    numeros,
                    estado_inicial=EstadoExpediente.NUEVO,
                    auto_guardar=False
                )

                expedientes_filtrados = gestor_estados.filtrar_por_estado(
                    expedientes,
                    self.config.estados
                )

                logger.info(f"Filtrado: {len(expedientes_filtrados)}/{len(expedientes)} expedientes")
                expedientes = expedientes_filtrados

            if not expedientes:
                logger.warning("No hay expedientes después del filtrado")
                return {
                    "estado": "completado",
                    "mensaje": "No hay expedientes que cumplan los filtros",
                    "session_id": self.session_id,
                    "total": 0,
                }

            # Fase 2: Procesar lote
            logger.info("FASE 2: Procesamiento por lotes")
            resumen = await self.procesar_lote_expedientes(expedientes)

            # Guardar reporte final
            reporte_path = self.reportes_dir / f"reporte_{self.session_id}.json"
            logger.info(f"Guardando reporte final en {reporte_path}")

            reporte_completo = {
                "session_id": self.session_id,
                "fecha": datetime.now().isoformat(),
                "config": self.config.to_dict(),
                "resultado": resumen,
            }

            with open(reporte_path, "w", encoding="utf-8") as f:
                json.dump(reporte_completo, f, indent=2, ensure_ascii=False)

            logger.info("=" * 60)
            logger.info("EXTRACCIÓN MASIVA COMPLETADA")
            logger.info(f"Exitosos: {resumen.get('exitosos', 0)}/{resumen.get('total', 0)}")
            logger.info(f"Errores: {resumen.get('errores', 0)}")
            logger.info(f"Reporte: {reporte_path}")
            logger.info("=" * 60)

            return {
                "estado": "completado",
                "session_id": self.session_id,
                "resultado": resumen,
                "reporte": str(reporte_path),
            }

        except Exception as e:
            logger.exception(f"Error durante extracción masiva: {e}")
            self._emit("error", {
                "mensaje": str(e),
                "timestamp": datetime.now().isoformat(),
            })
            return {
                "estado": "error",
                "mensaje": str(e),
                "session_id": self.session_id,
            }

    def cancelar(self):
        """Cancelar extracción en curso."""
        logger.warning("Cancelación solicitada")
        self.cancelado = True
        self._emit("cancelado", {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
        })
