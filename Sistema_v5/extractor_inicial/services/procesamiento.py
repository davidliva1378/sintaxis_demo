"""Procesamiento automatizado de expedientes seleccionados del extractor inicial.

Este módulo coordina la interacción con :class:`~Sistema_v5.ui.gui_playwright_bridge.GUIPlaywrightBridge`
para reutilizar la sesión autenticada de Playwright y delega la extracción de
actuaciones en :func:`~Sistema_v5.pjn.services.procesar_actuaciones_expediente`.

La estructura de directorios creada por
:class:`Sistema_v5.gestor_directorios.GestorDirectoriosExpedientes` es
transparente para quien invoca este servicio, ya que se gestiona internamente en
el servicio de actuaciones y no requiere intervención manual.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol, TypedDict

from ...pjn.models import ExpedienteResumen
from ...pjn.services import ResultadoProcesamiento, procesar_actuaciones_expediente
from ...ui.gui_playwright_bridge import (
    ExpedienteNavigationError,
    ExpedienteNotFoundError,
    GUIPlaywrightBridge,
    PlaywrightBridgeError,
    PlaywrightSessionError,
)


class ResultadoExpedienteProcesado(TypedDict, total=False):
    """Resultado individual del procesamiento de un expediente."""

    expediente: dict[str, str | None]
    estado: Literal["success", "error"]
    mensaje: str
    json_path: str | None
    resumen: ResultadoProcesamiento | None
    error: str | None


class ResumenProcesamientoExpedientes(TypedDict, total=False):
    """Resumen agregador del procesamiento masivo de expedientes."""

    total: int
    exitosos: int
    con_error: int
    resultados: list[ResultadoExpedienteProcesado]
    errores: list[str]
    no_encontrados: list[dict[str, str | None]]
    carpetas_expedientes: list[str]
    carpetas_json: list[str]
    carpetas_actuaciones: list[str]
    carpetas_adjuntos: list[str]


@dataclass(slots=True)
class ProcessingEvent:
    """Evento emitido durante el procesamiento de expedientes."""

    tipo: Literal["progress", "success", "error", "done"]
    expediente: ExpedienteResumen | None
    mensaje: str
    resumen: ResultadoProcesamiento | None = None
    json_path: str | None = None
    alert: Literal["info", "warning", "error"] | None = None
    error: BaseException | None = None


class EventCallback(Protocol):
    """Protocolo para callbacks de eventos de procesamiento."""

    def __call__(self, event: ProcessingEvent, /) -> object:
        ...


def procesar_expedientes_iniciales(
    seleccion: list[ExpedienteResumen],
    *,
    headless: bool,
    descargar_adjuntos: bool,
    on_event: EventCallback | None = None,
) -> ResumenProcesamientoExpedientes:
    """Procesa una lista de expedientes utilizando Playwright."""

    resultados: list[ResultadoExpedienteProcesado] = []
    errores: list[str] = []
    no_encontrados: list[dict[str, str | None]] = []
    carpetas_expedientes: set[str] = set()
    carpetas_json: set[str] = set()
    carpetas_actuaciones: set[str] = set()
    carpetas_adjuntos: set[str] = set()

    def _emit(event: ProcessingEvent) -> None:
        if on_event is not None:
            on_event(event)

    bridge = GUIPlaywrightBridge(headless=headless)
    try:
        bridge.start()
    except Exception:  # noqa: BLE001 - se propaga tras cerrar la sesión
        bridge.close()
        raise

    try:
        total = len(seleccion)
        for index, expediente in enumerate(seleccion, start=1):
            _emit(
                ProcessingEvent(
                    tipo="progress",
                    expediente=expediente,
                    mensaje=f"Procesando expediente {expediente.numero} ({index}/{total})...",
                )
            )

            try:
                datos_expediente = bridge.get_expediente_payload(expediente)
                if not isinstance(datos_expediente, dict):  # seguridad extra
                    raise TypeError(
                        "El puente de Playwright devolvió un payload inválido para el expediente."
                    )
            except PlaywrightSessionError as exc:
                mensaje = str(exc) or "Error de sesión de Playwright"
                errores.append(mensaje)
                resultados.append(_build_resultado_error(expediente, mensaje))
                _emit(
                    ProcessingEvent(
                        tipo="error",
                        expediente=expediente,
                        mensaje=mensaje,
                        alert="error",
                        error=exc,
                    )
                )
                break
            except ExpedienteNotFoundError as exc:
                mensaje = str(exc) or "Expediente no encontrado"
                errores.append(mensaje)
                resultados.append(_build_resultado_error(expediente, mensaje))
                no_encontrados.append(expediente.to_dict())
                _emit(
                    ProcessingEvent(
                        tipo="error",
                        expediente=expediente,
                        mensaje=mensaje,
                        alert="warning",
                        error=exc,
                    )
                )
                continue
            except ExpedienteNavigationError as exc:
                mensaje = str(exc) or "No se pudo navegar al expediente"
                errores.append(mensaje)
                resultados.append(_build_resultado_error(expediente, mensaje))
                _emit(
                    ProcessingEvent(
                        tipo="error",
                        expediente=expediente,
                        mensaje=mensaje,
                        alert="error",
                        error=exc,
                    )
                )
                continue
            except PlaywrightBridgeError as exc:
                mensaje = str(exc) or "Error del puente de Playwright"
                errores.append(mensaje)
                resultados.append(_build_resultado_error(expediente, mensaje))
                _emit(
                    ProcessingEvent(
                        tipo="error",
                        expediente=expediente,
                        mensaje=mensaje,
                        alert="error",
                        error=exc,
                    )
                )
                continue

            try:
                json_path, resumen = bridge.run_coroutine(
                    procesar_actuaciones_expediente(
                        datos_expediente,
                        descargar_adjuntos=descargar_adjuntos,
                    )
                )
            except PlaywrightSessionError as exc:
                mensaje = str(exc) or "Error de sesión de Playwright"
                errores.append(mensaje)
                resultados.append(_build_resultado_error(expediente, mensaje))
                _emit(
                    ProcessingEvent(
                        tipo="error",
                        expediente=expediente,
                        mensaje=mensaje,
                        alert="error",
                        error=exc,
                    )
                )
                break
            except PlaywrightBridgeError as exc:
                mensaje = str(exc) or "Error del puente de Playwright"
                errores.append(mensaje)
                resultados.append(_build_resultado_error(expediente, mensaje))
                _emit(
                    ProcessingEvent(
                        tipo="error",
                        expediente=expediente,
                        mensaje=mensaje,
                        alert="error",
                        error=exc,
                    )
                )
                continue
            except Exception as exc:  # noqa: BLE001 - propagación controlada
                mensaje = str(exc) or "Error inesperado durante el procesamiento"
                errores.append(mensaje)
                resultados.append(_build_resultado_error(expediente, mensaje))
                _emit(
                    ProcessingEvent(
                        tipo="error",
                        expediente=expediente,
                        mensaje=mensaje,
                        alert="error",
                        error=exc,
                    )
                )
                continue

            resumen = resumen or {}
            json_path_str = str(json_path) if isinstance(json_path, Path) else (
                json_path if json_path is None else str(json_path)
            )

            _track_carpetas(
                resumen,
                carpetas_expedientes,
                carpetas_json,
                carpetas_actuaciones,
                carpetas_adjuntos,
            )

            mensaje_resultado = _build_mensaje_resumen(expediente, resumen)
            if resumen.get("error"):
                errores.append(resumen["error"] or "Error desconocido del procesamiento")
                estado: Literal["success", "error"] = "error"
            else:
                estado = "success"

            resultado = ResultadoExpedienteProcesado(
                expediente=expediente.to_dict(),
                estado=estado,
                mensaje=mensaje_resultado,
                json_path=json_path_str,
                resumen=resumen,
                error=resumen.get("error"),
            )
            resultados.append(resultado)

            _emit(
                ProcessingEvent(
                    tipo="success",
                    expediente=expediente,
                    mensaje=mensaje_resultado,
                    resumen=resumen,
                    json_path=json_path_str,
                    alert="error" if estado == "error" else None,
                )
            )

        _emit(
            ProcessingEvent(
                tipo="done",
                expediente=None,
                mensaje="Procesamiento finalizado.",
            )
        )

        return ResumenProcesamientoExpedientes(
            total=len(seleccion),
            exitosos=sum(1 for r in resultados if r.get("estado") == "success"),
            con_error=sum(1 for r in resultados if r.get("estado") == "error"),
            resultados=resultados,
            errores=errores,
            no_encontrados=no_encontrados,
            carpetas_expedientes=sorted(carpetas_expedientes),
            carpetas_json=sorted(carpetas_json),
            carpetas_actuaciones=sorted(carpetas_actuaciones),
            carpetas_adjuntos=sorted(carpetas_adjuntos),
        )
    finally:
        bridge.close()


def _build_resultado_error(expediente: ExpedienteResumen, mensaje: str) -> ResultadoExpedienteProcesado:
    return ResultadoExpedienteProcesado(
        expediente=expediente.to_dict(),
        estado="error",
        mensaje=mensaje,
        json_path=None,
        resumen=None,
        error=mensaje,
    )


def _build_mensaje_resumen(
    expediente: ExpedienteResumen,
    resumen: ResultadoProcesamiento,
) -> str:
    if resumen.get("error"):
        return f"✗ {expediente.numero} — Error: {resumen['error']}"

    descargas = "Sí" if resumen.get("descargas_ejecutadas") else "No"
    return (
        f"✓ {expediente.numero} — "
        f"Act.: {resumen.get('actuaciones_actuales', 0)}/"
        f"{resumen.get('actuaciones_historicas', 0)} — Descargas: {descargas}"
    )


def _track_carpetas(
    resumen: ResultadoProcesamiento,
    carpetas_expedientes: set[str],
    carpetas_json: set[str],
    carpetas_actuaciones: set[str],
    carpetas_adjuntos: set[str],
) -> None:
    carpeta_expediente = resumen.get("carpeta_expediente")
    if isinstance(carpeta_expediente, str):
        carpetas_expedientes.add(carpeta_expediente)

    carpeta_json = resumen.get("carpeta_json")
    if isinstance(carpeta_json, str):
        carpetas_json.add(carpeta_json)

    carpeta_actuaciones = resumen.get("carpeta_actuaciones")
    if isinstance(carpeta_actuaciones, str):
        carpetas_actuaciones.add(carpeta_actuaciones)

    carpeta_adjuntos = resumen.get("carpeta_adjuntos")
    if isinstance(carpeta_adjuntos, str):
        carpetas_adjuntos.add(carpeta_adjuntos)


__all__ = [
    "procesar_expedientes_iniciales",
    "ProcessingEvent",
    "ResumenProcesamientoExpedientes",
    "ResultadoExpedienteProcesado",
]
