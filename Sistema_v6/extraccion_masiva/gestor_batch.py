"""
Gestor de procesamiento por lotes de expedientes.

Este módulo maneja el procesamiento de grandes volúmenes de expedientes
en lotes, con control de errores, estadísticas y capacidad de pausar/reanudar.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Callable, Optional
import asyncio
import time
import logging

logger = logging.getLogger(__name__)


@dataclass
class ResultadoProcesamiento:
    """Resultado del procesamiento de un expediente individual."""

    expediente: Dict
    estado: str  # "success", "error", "skipped"
    mensaje: str
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    duracion_segundos: float = 0.0

    def to_dict(self) -> Dict:
        """Convertir a diccionario."""
        return {
            "numero": self.expediente.get("numero"),
            "estado": self.estado,
            "mensaje": self.mensaje,
            "error": self.error,
            "timestamp": self.timestamp,
            "duracion_segundos": self.duracion_segundos,
        }


@dataclass
class ResumenBatch:
    """Resumen del procesamiento batch."""

    total: int
    exitosos: int
    errores: int
    omitidos: int
    duracion_segundos: float
    resultados: List[ResultadoProcesamiento]
    tiempo_inicio: str = field(default_factory=lambda: datetime.now().isoformat())
    tiempo_fin: str = field(default_factory=lambda: datetime.now().isoformat())
    velocidad_promedio: float = 0.0  # expedientes por minuto

    def to_dict(self) -> Dict:
        """Convertir a diccionario."""
        return {
            "total": self.total,
            "exitosos": self.exitosos,
            "errores": self.errores,
            "omitidos": self.omitidos,
            "duracion_segundos": self.duracion_segundos,
            "tiempo_inicio": self.tiempo_inicio,
            "tiempo_fin": self.tiempo_fin,
            "velocidad_promedio": self.velocidad_promedio,
            "resultados": [r.to_dict() for r in self.resultados],
        }


class GestorBatch:
    """
    Gestor de procesamiento por lotes de expedientes.

    Características:
    - Procesamiento secuencial de expedientes
    - Control de errores consecutivos con umbral
    - Estadísticas en tiempo real
    - Capacidad de pausar/reanudar/cancelar
    - Callbacks para reportar progreso
    """

    def __init__(
        self,
        umbral_errores: int = 5,
        callback_progreso: Optional[Callable] = None,
        timeout_por_expediente: int = 120,
    ):
        """
        Inicializar gestor de batch.

        Args:
            umbral_errores: Número de errores consecutivos antes de alertar
            callback_progreso: Función callback para reportar progreso
            timeout_por_expediente: Timeout en segundos por expediente
        """
        self.umbral_errores = umbral_errores
        self.callback_progreso = callback_progreso
        self.timeout_por_expediente = timeout_por_expediente

        self.resultados: List[ResultadoProcesamiento] = []
        self.errores_consecutivos = 0
        self.pausado = False
        self.cancelado = False

    async def procesar_lote(
        self,
        expedientes: List[Dict],
        descargar_adjuntos: bool = True,
        headless: bool = True
    ) -> ResumenBatch:
        """
        Procesar lote de expedientes.

        Args:
            expedientes: Lista de expedientes a procesar
            descargar_adjuntos: Si descargar archivos adjuntos
            headless: Modo headless de Playwright

        Returns:
            ResumenBatch con resultados del procesamiento
        """
        logger.info(f"Iniciando procesamiento de lote: {len(expedientes)} expedientes")
        tiempo_inicio = time.time()
        tiempo_inicio_str = datetime.now().isoformat()

        total = len(expedientes)
        exitosos = 0
        errores = 0
        omitidos = 0

        for i, expediente in enumerate(expedientes):
            # Verificar cancelación
            if self.cancelado:
                logger.warning("Procesamiento cancelado por el usuario")
                break

            # Manejar pausa
            while self.pausado and not self.cancelado:
                await asyncio.sleep(0.5)

            try:
                logger.debug(f"Procesando expediente {i+1}/{total}: {expediente.get('numero')}")

                # Emitir progreso
                if self.callback_progreso:
                    velocidad = self._calcular_velocidad(i + 1, tiempo_inicio)
                    tiempo_estimado = self._estimar_tiempo_restante(i + 1, total, tiempo_inicio)

                    self.callback_progreso({
                        "expediente_actual": expediente.get("numero"),
                        "procesados": i + 1,
                        "total": total,
                        "exitosos": exitosos,
                        "errores": errores,
                        "omitidos": omitidos,
                        "velocidad": velocidad,
                        "tiempo_estimado": tiempo_estimado,
                        "porcentaje": ((i + 1) / total) * 100,
                    })

                # Procesar expediente individual
                inicio_proc = time.time()
                resultado = await self._procesar_expediente(
                    expediente,
                    descargar_adjuntos,
                    headless
                )
                duracion_proc = time.time() - inicio_proc
                resultado.duracion_segundos = duracion_proc

                self.resultados.append(resultado)

                # Actualizar contadores
                if resultado.estado == "success":
                    exitosos += 1
                    self.errores_consecutivos = 0
                    logger.debug(f"✅ Expediente procesado: {expediente.get('numero')}")
                elif resultado.estado == "error":
                    errores += 1
                    self.errores_consecutivos += 1
                    logger.warning(f"❌ Error procesando {expediente.get('numero')}: {resultado.error}")

                    # Verificar umbral de errores
                    if self.errores_consecutivos >= self.umbral_errores:
                        logger.error(f"Umbral de errores alcanzado: {self.errores_consecutivos}")
                        # Por ahora solo logueamos, pero se podría pausar o pedir confirmación
                        self.errores_consecutivos = 0
                else:
                    omitidos += 1
                    logger.info(f"⊘ Expediente omitido: {expediente.get('numero')}")

            except asyncio.TimeoutError:
                logger.error(f"Timeout procesando {expediente.get('numero')}")
                errores += 1
                self.resultados.append(ResultadoProcesamiento(
                    expediente=expediente,
                    estado="error",
                    mensaje="Timeout al procesar expediente",
                    error="TimeoutError"
                ))
            except Exception as e:
                logger.exception(f"Error inesperado procesando {expediente.get('numero')}: {e}")
                errores += 1
                self.resultados.append(ResultadoProcesamiento(
                    expediente=expediente,
                    estado="error",
                    mensaje="Error inesperado",
                    error=str(e)
                ))

            # Pequeño delay entre expedientes para no sobrecargar
            await asyncio.sleep(0.2)

        # Calcular tiempos y velocidades finales
        tiempo_fin = time.time()
        duracion = tiempo_fin - tiempo_inicio
        velocidad_promedio = (len(self.resultados) / duracion * 60) if duracion > 0 else 0

        logger.info(f"Procesamiento completado: {exitosos}/{total} exitosos, {errores} errores, {omitidos} omitidos")
        logger.info(f"Duración: {duracion:.2f}s, Velocidad: {velocidad_promedio:.2f} exp/min")

        return ResumenBatch(
            total=total,
            exitosos=exitosos,
            errores=errores,
            omitidos=omitidos,
            duracion_segundos=duracion,
            resultados=self.resultados,
            tiempo_inicio=tiempo_inicio_str,
            tiempo_fin=datetime.now().isoformat(),
            velocidad_promedio=velocidad_promedio,
        )

    async def _procesar_expediente(
        self,
        expediente: Dict,
        descargar_adjuntos: bool,
        headless: bool
    ) -> ResultadoProcesamiento:
        """
        Procesar un expediente individual.

        Args:
            expediente: Datos del expediente
            descargar_adjuntos: Si descargar adjuntos
            headless: Modo headless

        Returns:
            ResultadoProcesamiento
        """
        try:
            # TODO: Aquí iría la lógica real de procesamiento del expediente
            # Por ahora, simulamos el procesamiento exitoso
            await asyncio.sleep(0.1)  # Simular tiempo de procesamiento

            return ResultadoProcesamiento(
                expediente=expediente,
                estado="success",
                mensaje="Expediente procesado correctamente"
            )

        except asyncio.TimeoutError:
            return ResultadoProcesamiento(
                expediente=expediente,
                estado="error",
                mensaje="Timeout al procesar expediente",
                error="TimeoutError"
            )
        except Exception as e:
            return ResultadoProcesamiento(
                expediente=expediente,
                estado="error",
                mensaje="Error al procesar expediente",
                error=str(e)
            )

    def _calcular_velocidad(self, procesados: int, tiempo_inicio: float) -> float:
        """
        Calcular velocidad de procesamiento (expedientes/minuto).

        Args:
            procesados: Número de expedientes procesados
            tiempo_inicio: Timestamp de inicio

        Returns:
            Velocidad en expedientes por minuto
        """
        tiempo_transcurrido = time.time() - tiempo_inicio
        if tiempo_transcurrido > 0:
            return (procesados / tiempo_transcurrido) * 60
        return 0.0

    def _estimar_tiempo_restante(
        self,
        procesados: int,
        total: int,
        tiempo_inicio: float
    ) -> int:
        """
        Estimar tiempo restante en segundos.

        Args:
            procesados: Número de expedientes procesados
            total: Total de expedientes
            tiempo_inicio: Timestamp de inicio

        Returns:
            Tiempo estimado restante en segundos
        """
        if procesados == 0:
            return 0

        tiempo_transcurrido = time.time() - tiempo_inicio
        tiempo_por_expediente = tiempo_transcurrido / procesados
        restantes = total - procesados

        return int(restantes * tiempo_por_expediente)

    def pausar(self):
        """Pausar procesamiento."""
        logger.info("Pausando procesamiento")
        self.pausado = True

    def reanudar(self):
        """Reanudar procesamiento."""
        logger.info("Reanudando procesamiento")
        self.pausado = False

    def cancelar(self):
        """Cancelar procesamiento."""
        logger.warning("Cancelando procesamiento")
        self.cancelado = True
        self.pausado = False

    def obtener_estadisticas(self) -> Dict:
        """
        Obtener estadísticas actuales del procesamiento.

        Returns:
            Diccionario con estadísticas
        """
        exitosos = sum(1 for r in self.resultados if r.estado == "success")
        errores = sum(1 for r in self.resultados if r.estado == "error")
        omitidos = sum(1 for r in self.resultados if r.estado == "skipped")

        return {
            "procesados": len(self.resultados),
            "exitosos": exitosos,
            "errores": errores,
            "omitidos": omitidos,
            "errores_consecutivos": self.errores_consecutivos,
            "pausado": self.pausado,
            "cancelado": self.cancelado,
        }
