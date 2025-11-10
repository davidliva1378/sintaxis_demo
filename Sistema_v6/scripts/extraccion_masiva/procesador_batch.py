"""Procesador batch para extracción completa de expedientes."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from scripts.extraccion_masiva.models import ExpedienteInfo

logger = logging.getLogger(__name__)


@dataclass
class ResultadoExpediente:
    """Resultado del procesamiento de un expediente."""

    numero: str
    estado: str  # "success", "error", "skipped"
    mensaje: str
    datos: dict[str, Any] | None = None
    error: str | None = None
    tiempo_segundos: float = 0.0


@dataclass
class ResumenBatch:
    """Resumen del procesamiento batch."""

    total: int = 0
    exitosos: int = 0
    errores: int = 0
    omitidos: int = 0
    duracion_segundos: float = 0.0
    resultados: list[ResultadoExpediente] = field(default_factory=list)


class ExtractorCompletoBatch:
    """Procesador batch para extracción completa de expedientes con actuaciones.

    Procesa múltiples expedientes en secuencia, con manejo de errores,
    callbacks de progreso y generación de reportes.
    """

    def __init__(
        self,
        umbral_errores_consecutivos: int = 5,
        headless: bool = True,
        descargar_adjuntos: bool = False,
        directorio_base: Path | str | None = None
    ):
        """Inicializa el procesador batch.

        Args:
            umbral_errores_consecutivos: Número de errores consecutivos
                antes de pausar/preguntar
            headless: Si True, ejecuta browser en modo headless
            descargar_adjuntos: Si True, descarga adjuntos
            directorio_base: Directorio base donde guardar datos
        """
        self.umbral_errores_consecutivos = umbral_errores_consecutivos
        self.headless = headless
        self.descargar_adjuntos = descargar_adjuntos
        self.directorio_base = Path(directorio_base) if directorio_base else None

        # Callbacks opcionales
        self.callback_progreso: Callable | None = None
        self.callback_expediente_inicio: Callable | None = None
        self.callback_expediente_fin: Callable | None = None
        self.callback_error_umbral: Callable | None = None

        # Tracking interno
        self.errores_consecutivos = 0
        self.mensajes_error: list[str] = []
        self.resumen: ResumenBatch | None = None

    def set_callback_progreso(self, callback: Callable) -> None:
        """Establece callback de progreso.

        Args:
            callback: Función con firma (indice: int, total: int, expediente)
        """
        self.callback_progreso = callback

    def set_callback_expediente_inicio(self, callback: Callable) -> None:
        """Establece callback al iniciar un expediente.

        Args:
            callback: Función con firma (expediente, indice: int, total: int)
        """
        self.callback_expediente_inicio = callback

    def set_callback_expediente_fin(self, callback: Callable) -> None:
        """Establece callback al finalizar un expediente.

        Args:
            callback: Función con firma (resultado: ResultadoExpediente, tiempo: float)
        """
        self.callback_expediente_fin = callback

    def set_callback_error_umbral(self, callback: Callable) -> None:
        """Establece callback cuando se alcanza umbral de errores.

        Args:
            callback: Función con firma (num_errores: int, mensajes: list[str]) -> str
                     Debe retornar "continuar" o "detener"
        """
        self.callback_error_umbral = callback

    async def procesar_lote(
        self,
        expedientes: list[dict[str, Any]],
        page: Any,  # Playwright page
        extractor_personalizado: Callable | None = None
    ) -> ResumenBatch:
        """Procesa un lote de expedientes.

        Args:
            expedientes: Lista de diccionarios con datos de expedientes
            page: Página de Playwright para navegación
            extractor_personalizado: Función async personalizada para extraer datos
                Firma: async def extraer(expediente: ExpedienteInfo, page) -> dict

        Returns:
            ResumenBatch con estadísticas y resultados
        """
        inicio = time.time()
        total = len(expedientes)

        resumen = ResumenBatch(total=total)
        self.errores_consecutivos = 0
        self.mensajes_error = []

        for indice, exp_dict in enumerate(expedientes, 1):
            # Crear ExpedienteInfo
            try:
                expediente = ExpedienteInfo.from_dict(exp_dict)
            except Exception as e:
                logger.error(f"❌ Error al crear ExpedienteInfo: {e}")
                resultado = ResultadoExpediente(
                    numero=exp_dict.get("numero", "DESCONOCIDO"),
                    estado="error",
                    mensaje=f"Error al crear ExpedienteInfo: {e}",
                    error=str(e)
                )
                resumen.resultados.append(resultado)
                resumen.errores += 1
                continue

            # Callback de progreso
            if self.callback_progreso:
                try:
                    self.callback_progreso(indice, total, expediente)
                except Exception as e:
                    logger.warning(f"⚠️  Error en callback_progreso: {e}")

            # Callback de inicio
            if self.callback_expediente_inicio:
                try:
                    self.callback_expediente_inicio(expediente, indice, total)
                except Exception as e:
                    logger.warning(f"⚠️  Error en callback_expediente_inicio: {e}")

            # Procesar expediente
            inicio_exp = time.time()
            resultado = await self._procesar_expediente(
                expediente,
                page,
                extractor_personalizado
            )
            tiempo_exp = time.time() - inicio_exp
            resultado.tiempo_segundos = tiempo_exp

            # Actualizar estadísticas
            if resultado.estado == "success":
                resumen.exitosos += 1
                self.errores_consecutivos = 0
            elif resultado.estado == "error":
                resumen.errores += 1
                self.errores_consecutivos += 1
                self.mensajes_error.append(resultado.mensaje)
            else:
                resumen.omitidos += 1

            resumen.resultados.append(resultado)

            # Callback de fin
            if self.callback_expediente_fin:
                try:
                    self.callback_expediente_fin(resultado, tiempo_exp)
                except Exception as e:
                    logger.warning(f"⚠️  Error en callback_expediente_fin: {e}")

            # Verificar umbral de errores
            if self.errores_consecutivos >= self.umbral_errores_consecutivos:
                if self.callback_error_umbral:
                    try:
                        accion = self.callback_error_umbral(
                            self.errores_consecutivos,
                            self.mensajes_error
                        )
                        if accion == "detener":
                            logger.warning("🛑 Deteniendo procesamiento batch")
                            break
                    except Exception as e:
                        logger.warning(f"⚠️  Error en callback_error_umbral: {e}")

                # Resetear contador si se continúa
                self.errores_consecutivos = 0
                self.mensajes_error = []

        resumen.duracion_segundos = time.time() - inicio
        self.resumen = resumen

        return resumen

    async def _procesar_expediente(
        self,
        expediente: ExpedienteInfo,
        page: Any,
        extractor_personalizado: Callable | None
    ) -> ResultadoExpediente:
        """Procesa un único expediente.

        Args:
            expediente: Información del expediente
            page: Página de Playwright
            extractor_personalizado: Función de extracción personalizada

        Returns:
            ResultadoExpediente con el resultado del procesamiento
        """
        try:
            # Usar extractor personalizado si está disponible
            if extractor_personalizado:
                datos = await extractor_personalizado(expediente, page)
            else:
                # Extracción básica por defecto
                datos = {
                    "numero_expediente": expediente.numero,
                    "caratula": expediente.caratula,
                    "actuaciones": [],
                    "metadata": {
                        "fecha_extraccion": datetime.now().isoformat()
                    }
                }

            # Guardar datos si hay directorio base
            if self.directorio_base:
                await self._guardar_datos(expediente, datos)

            return ResultadoExpediente(
                numero=expediente.numero,
                estado="success",
                mensaje=f"Expediente procesado exitosamente",
                datos=datos
            )

        except Exception as e:
            logger.error(f"❌ Error al procesar expediente {expediente.numero}: {e}")
            return ResultadoExpediente(
                numero=expediente.numero,
                estado="error",
                mensaje=f"Error: {str(e)}",
                error=str(e)
            )

    async def _guardar_datos(
        self,
        expediente: ExpedienteInfo,
        datos: dict[str, Any]
    ) -> None:
        """Guarda los datos extraídos de un expediente.

        Args:
            expediente: Información del expediente
            datos: Datos extraídos a guardar
        """
        if not self.directorio_base:
            return

        try:
            # Sanitizar nombre
            nombre_sanitizado = expediente.numero.replace('/', '-').replace('\\', '-')
            dir_expediente = self.directorio_base / nombre_sanitizado

            # Crear directorio si no existe
            (dir_expediente / "actuaciones").mkdir(parents=True, exist_ok=True)

            # Guardar datos
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archivo_datos = dir_expediente / "actuaciones" / f"datos_{timestamp}.json"

            with open(archivo_datos, 'w', encoding='utf-8') as f:
                json.dump(datos, f, indent=2, ensure_ascii=False)

            logger.debug(f"💾 Datos guardados en: {archivo_datos}")

        except Exception as e:
            logger.warning(f"⚠️  Error al guardar datos de {expediente.numero}: {e}")

    def generar_reporte(self, ruta_reporte: Path) -> Path:
        """Genera un reporte JSON del procesamiento batch.

        Args:
            ruta_reporte: Ruta donde guardar el reporte

        Returns:
            Path al reporte guardado
        """
        if not self.resumen:
            raise ValueError("No hay resumen disponible. Ejecute procesar_lote() primero.")

        try:
            reporte = {
                "fecha_generacion": datetime.now().isoformat(),
                "resumen": {
                    "total": self.resumen.total,
                    "exitosos": self.resumen.exitosos,
                    "errores": self.resumen.errores,
                    "omitidos": self.resumen.omitidos,
                    "duracion_segundos": self.resumen.duracion_segundos
                },
                "configuracion": {
                    "umbral_errores_consecutivos": self.umbral_errores_consecutivos,
                    "headless": self.headless,
                    "descargar_adjuntos": self.descargar_adjuntos
                },
                "resultados": [
                    {
                        "numero": r.numero,
                        "estado": r.estado,
                        "mensaje": r.mensaje,
                        "tiempo_segundos": r.tiempo_segundos,
                        "error": r.error
                    }
                    for r in self.resumen.resultados
                ]
            }

            ruta_reporte.parent.mkdir(parents=True, exist_ok=True)

            with open(ruta_reporte, 'w', encoding='utf-8') as f:
                json.dump(reporte, f, indent=2, ensure_ascii=False)

            logger.info(f"📊 Reporte generado: {ruta_reporte}")

            return ruta_reporte

        except Exception as e:
            logger.error(f"❌ Error al generar reporte: {e}")
            raise
