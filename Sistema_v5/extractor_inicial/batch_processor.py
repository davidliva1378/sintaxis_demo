"""Procesamiento por lotes de expedientes con manejo inteligente de errores.

Este módulo implementa la extracción completa de actuaciones para múltiples
expedientes, con umbral de errores configurable y estrategia de reintentos.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Callable, Literal

from ..pjn.models.expediente import ExpedienteResumen
from ..pjn.services import ResultadoProcesamiento, procesar_actuaciones_expediente
from ..ui.gui_playwright_bridge import (
    ExpedienteNavigationError,
    ExpedienteNotFoundError,
    GUIPlaywrightBridge,
    PlaywrightBridgeError,
    PlaywrightSessionError,
)


@dataclass
class ResultadoExpediente:
    """Resultado del procesamiento de un expediente individual."""

    expediente: ExpedienteResumen
    estado: Literal["success", "error", "skipped"]
    mensaje: str
    json_path: Path | None = None
    resumen: ResultadoProcesamiento | None = None
    error: str | None = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ResumenBatch:
    """Resumen agregado del procesamiento por lotes."""

    total: int
    exitosos: int
    errores: int
    omitidos: int
    resultados: list[ResultadoExpediente]
    tiempo_inicio: str
    tiempo_fin: str
    duracion_segundos: float

    def __post_init__(self) -> None:
        """Valida consistencia de los totales."""
        calculado = self.exitosos + self.errores + self.omitidos
        if calculado != self.total:
            raise ValueError(
                f"Inconsistencia: total={self.total} pero "
                f"exitosos+errores+omitidos={calculado}"
            )


class AccionUsuarioError(Exception):
    """Se lanza cuando el usuario decide cancelar el procesamiento."""

    pass


class ExtractorCompletoBatch:
    """Procesador por lotes con manejo inteligente de errores.

    Implementa un sistema de umbral de errores consecutivos que pausa el
    procesamiento y consulta al usuario si desea continuar, saltar lote o
    cancelar completamente.

    Attributes:
        umbral_errores_consecutivos: Número de errores seguidos antes de pausar
        headless: Si True, ejecuta Playwright sin interfaz gráfica
        descargar_adjuntos: Si True, descarga archivos adjuntos de actuaciones
    """

    def __init__(
        self,
        *,
        umbral_errores_consecutivos: int = 5,
        headless: bool = True,
        descargar_adjuntos: bool = False,
    ):
        """Inicializa el procesador batch.

        Args:
            umbral_errores_consecutivos: Número de fallos antes de pausar y preguntar
            headless: Modo de Playwright (True = sin GUI, False = con navegador visible)
            descargar_adjuntos: Si True, descarga adjuntos de actuaciones
        """
        self.umbral_errores_consecutivos = umbral_errores_consecutivos
        self.headless = headless
        self.descargar_adjuntos = descargar_adjuntos

        self._errores_consecutivos = 0
        self._resultados: list[ResultadoExpediente] = []
        self._callback_progreso: Callable[[int, int, ExpedienteResumen], None] | None = None
        self._callback_error_umbral: Callable[[int, list[str]], str] | None = None

    def set_callback_progreso(
        self,
        callback: Callable[[int, int, ExpedienteResumen], None],
    ) -> None:
        """Configura callback para reportar progreso.

        Args:
            callback: Función que recibe (indice_actual, total, expediente)
        """
        self._callback_progreso = callback

    def set_callback_error_umbral(
        self,
        callback: Callable[[int, list[str]], str],
    ) -> None:
        """Configura callback para consultar al usuario cuando se alcanza el umbral.

        Args:
            callback: Función que recibe (num_errores, lista_mensajes_error)
                      y retorna "continuar", "saltar" o "cancelar"
        """
        self._callback_error_umbral = callback

    async def procesar_lote(
        self,
        expedientes: list[ExpedienteResumen],
    ) -> ResumenBatch:
        """Procesa un lote de expedientes con manejo inteligente de errores.

        Args:
            expedientes: Lista de expedientes a procesar

        Returns:
            ResumenBatch con resultados detallados

        Raises:
            AccionUsuarioError: Si el usuario cancela el procesamiento

        Example:
            >>> batch = ExtractorCompletoBatch(umbral_errores_consecutivos=5)
            >>> batch.set_callback_progreso(lambda i, t, e: print(f"{i}/{t}: {e.numero}"))
            >>> resumen = await batch.procesar_lote(expedientes)
            >>> print(f"Éxito: {resumen.exitosos}/{resumen.total}")
        """
        tiempo_inicio = datetime.now()
        tiempo_inicio_str = tiempo_inicio.isoformat(timespec="seconds")

        self._resultados = []
        self._errores_consecutivos = 0
        errores_recientes: list[str] = []

        bridge = GUIPlaywrightBridge(headless=self.headless)
        try:
            bridge.start()
        except Exception as exc:
            bridge.close()
            raise RuntimeError(f"No se pudo iniciar GUIPlaywrightBridge: {exc}") from exc

        try:
            total = len(expedientes)

            for indice, expediente in enumerate(expedientes, start=1):
                # Reportar progreso
                if self._callback_progreso:
                    self._callback_progreso(indice, total, expediente)

                # Procesar expediente
                try:
                    resultado = await self._procesar_expediente_individual(
                        bridge,
                        expediente,
                        indice,
                        total,
                    )
                    self._resultados.append(resultado)

                    if resultado.estado == "success":
                        self._errores_consecutivos = 0
                        errores_recientes.clear()
                    elif resultado.estado == "error":
                        self._errores_consecutivos += 1
                        errores_recientes.append(f"{expediente.numero}: {resultado.error}")

                        # Verificar umbral de errores
                        if self._errores_consecutivos >= self.umbral_errores_consecutivos:
                            accion = self._consultar_usuario_umbral(
                                self._errores_consecutivos,
                                errores_recientes,
                            )

                            if accion == "cancelar":
                                raise AccionUsuarioError("Procesamiento cancelado por el usuario")
                            elif accion == "saltar":
                                # Saltar expedientes restantes del lote actual
                                expedientes_restantes = len(expedientes) - indice
                                for exp_restante in expedientes[indice:]:
                                    self._resultados.append(
                                        ResultadoExpediente(
                                            expediente=exp_restante,
                                            estado="skipped",
                                            mensaje=f"Omitido por usuario tras {self._errores_consecutivos} errores",
                                        )
                                    )
                                break
                            elif accion == "continuar":
                                self._errores_consecutivos = 0
                                errores_recientes.clear()

                except AccionUsuarioError:
                    raise
                except Exception as exc:
                    # Error inesperado
                    self._resultados.append(
                        ResultadoExpediente(
                            expediente=expediente,
                            estado="error",
                            mensaje=f"Error inesperado: {exc}",
                            error=str(exc),
                        )
                    )
                    self._errores_consecutivos += 1

        finally:
            bridge.close()

        tiempo_fin = datetime.now()
        tiempo_fin_str = tiempo_fin.isoformat(timespec="seconds")
        duracion = (tiempo_fin - tiempo_inicio).total_seconds()

        # Calcular estadísticas
        exitosos = sum(1 for r in self._resultados if r.estado == "success")
        errores = sum(1 for r in self._resultados if r.estado == "error")
        omitidos = sum(1 for r in self._resultados if r.estado == "skipped")

        return ResumenBatch(
            total=len(expedientes),
            exitosos=exitosos,
            errores=errores,
            omitidos=omitidos,
            resultados=self._resultados,
            tiempo_inicio=tiempo_inicio_str,
            tiempo_fin=tiempo_fin_str,
            duracion_segundos=duracion,
        )

    async def _procesar_expediente_individual(
        self,
        bridge: GUIPlaywrightBridge,
        expediente: ExpedienteResumen,
        indice: int,
        total: int,
    ) -> ResultadoExpediente:
        """Procesa un expediente individual con manejo de errores específicos."""
        try:
            # Obtener payload del expediente
            datos_expediente = bridge.get_expediente_payload(expediente)

            if not isinstance(datos_expediente, dict):
                raise TypeError("El puente retornó un payload inválido")

            # Procesar actuaciones
            json_path, resumen = bridge.run_coroutine(
                procesar_actuaciones_expediente(
                    datos_expediente,
                    descargar_adjuntos=self.descargar_adjuntos,
                )
            )

            mensaje = self._build_mensaje_exito(expediente, resumen)

            return ResultadoExpediente(
                expediente=expediente,
                estado="success",
                mensaje=mensaje,
                json_path=Path(json_path) if json_path else None,
                resumen=resumen,
            )

        except PlaywrightSessionError as exc:
            # Error crítico de sesión → debe detener todo
            raise RuntimeError(f"Error crítico de sesión Playwright: {exc}") from exc

        except ExpedienteNotFoundError as exc:
            return ResultadoExpediente(
                expediente=expediente,
                estado="error",
                mensaje=f"⚠️  Expediente no encontrado: {exc}",
                error=str(exc),
            )

        except ExpedienteNavigationError as exc:
            return ResultadoExpediente(
                expediente=expediente,
                estado="error",
                mensaje=f"❌ Error de navegación: {exc}",
                error=str(exc),
            )

        except PlaywrightBridgeError as exc:
            return ResultadoExpediente(
                expediente=expediente,
                estado="error",
                mensaje=f"❌ Error del puente Playwright: {exc}",
                error=str(exc),
            )

        except Exception as exc:
            return ResultadoExpediente(
                expediente=expediente,
                estado="error",
                mensaje=f"❌ Error inesperado: {exc}",
                error=str(exc),
            )

    def _build_mensaje_exito(
        self,
        expediente: ExpedienteResumen,
        resumen: ResultadoProcesamiento | None,
    ) -> str:
        """Construye mensaje de éxito con detalles del procesamiento."""
        if not resumen:
            return f"✓ {expediente.numero} — Procesado sin detalles"

        actuaciones_actuales = resumen.get("actuaciones_actuales", 0)
        actuaciones_historicas = resumen.get("actuaciones_historicas", 0)
        descargas = "Sí" if resumen.get("descargas_ejecutadas") else "No"

        return (
            f"✓ {expediente.numero} — "
            f"Act.: {actuaciones_actuales}/{actuaciones_historicas} — "
            f"Descargas: {descargas}"
        )

    def _consultar_usuario_umbral(
        self,
        num_errores: int,
        mensajes_error: list[str],
    ) -> Literal["continuar", "saltar", "cancelar"]:
        """Consulta al usuario qué hacer tras alcanzar el umbral de errores."""
        if self._callback_error_umbral:
            respuesta = self._callback_error_umbral(num_errores, mensajes_error)
            if respuesta in ("continuar", "saltar", "cancelar"):
                return respuesta

        # Fallback: continuar automáticamente (modo no interactivo)
        return "continuar"


__all__ = [
    "ExtractorCompletoBatch",
    "ResultadoExpediente",
    "ResumenBatch",
    "AccionUsuarioError",
]
