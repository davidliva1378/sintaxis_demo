"""Use Case de Extracción Masiva de Expedientes."""
from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Callable, Dict, List

from application.dtos import (
    IniciarExtraccionMasivaCommand,
    IniciarExtraccionMasivaResponse,
    Result,
)
from application.ports import IExpedienteRepository, IStoragePort

logger = logging.getLogger(__name__)


class ExtraccionMasivaUseCase:
    """Use case para extracción masiva de expedientes.

    Integra el ExtractorMasivo existente con la arquitectura limpia,
    proporcionando gestión de sesiones, callbacks y exportación.

    Attributes:
        storage: Port de almacenamiento
        repository: Repositorio de expedientes
        gestor_sesiones: Gestor de sesiones de extracción
    """

    def __init__(
        self,
        storage: IStoragePort,
        repository: IExpedienteRepository,
        gestor_sesiones: Any,  # GestorSesiones
    ):
        """Inicializa el use case.

        Args:
            storage: Port de almacenamiento
            repository: Repositorio de expedientes
            gestor_sesiones: Gestor de sesiones de extracción
        """
        self.storage = storage
        self.repository = repository
        self.gestor_sesiones = gestor_sesiones

    async def iniciar_extraccion(
        self,
        command: IniciarExtraccionMasivaCommand,
    ) -> Result[IniciarExtraccionMasivaResponse]:
        """Inicia una extracción masiva.

        Args:
            command: Comando con configuración de extracción

        Returns:
            Result con respuesta de inicio
        """
        try:
            # Generar session_id único
            session_id = f"ext_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Crear configuración para el gestor
            config = {
                "usuario": command.usuario,
                "formatos": command.exportar_formatos,
                "fecha_desde": command.fecha_desde,
                "fecha_hasta": command.fecha_hasta,
                "estados": command.estados,
                "dependencias": command.dependencias,
                "umbral_errores": command.umbral_errores,
                "headless": command.headless,
            }

            # Crear sesión
            await self.gestor_sesiones.crear_sesion(session_id, config)

            # Crear respuesta
            response = IniciarExtraccionMasivaResponse(
                session_id=session_id,
                mensaje="Extracción iniciada correctamente",
                estado="iniciando",
            )

            logger.info(f"Extracción masiva iniciada: {session_id}")
            return Result.success(response)

        except Exception as e:
            logger.exception("Error al iniciar extracción masiva")
            return Result.failure(f"Error al iniciar extracción: {str(e)}")

    def crear_callbacks(self, session_id: str) -> Dict[str, Callable]:
        """Crear callbacks para conectar el extractor con el gestor de sesiones.

        Args:
            session_id: ID de la sesión

        Returns:
            Dict con callbacks
        """

        async def on_inicio_listado():
            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                estado="en_progreso",
                fase="listado",
                mensaje="Extrayendo listado de expedientes...",
            )

        async def on_progreso_listado(pagina_actual: int, total_paginas: int):
            porcentaje = (
                (pagina_actual / total_paginas * 50) if total_paginas > 0 else 0
            )
            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                progreso_actual=pagina_actual,
                progreso_total=total_paginas,
                porcentaje=porcentaje,
                mensaje=f"Extrayendo página {pagina_actual} de {total_paginas}...",
            )

        async def on_fin_listado(expedientes: List[Dict]):
            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                mensaje=f"Listado completo: {len(expedientes)} expedientes encontrados",
                porcentaje=50.0,
            )

        async def on_inicio_batch(total: int):
            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                fase="procesamiento",
                progreso_total=total,
                mensaje=f"Iniciando procesamiento de {total} expedientes...",
            )

        async def on_progreso_batch(idx: int, total: int, resultado: Dict):
            porcentaje = 50 + (idx / total * 50) if total > 0 else 50
            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                progreso_actual=idx + 1,
                progreso_total=total,
                porcentaje=porcentaje,
                mensaje=f"Procesando {idx + 1}/{total}: {resultado.get('numero', 'N/A')}",
            )

        async def on_fin_batch(resumen: Dict):
            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                mensaje=f"Procesamiento completo: {resumen.get('exitosos', 0)} exitosos, {resumen.get('errores', 0)} errores",
                porcentaje=100.0,
            )

        async def on_error(error: str):
            sesion = await self.gestor_sesiones.obtener_sesion(session_id)
            if sesion:
                errores = sesion.get("errores", 0) + 1
                await self.gestor_sesiones.actualizar_progreso(
                    session_id,
                    errores=errores,
                    mensaje=f"Error: {error}",
                )

        return {
            "inicio_listado": on_inicio_listado,
            "progreso_listado": on_progreso_listado,
            "fin_listado": on_fin_listado,
            "inicio_batch": on_inicio_batch,
            "progreso_batch": on_progreso_batch,
            "fin_batch": on_fin_batch,
            "error": on_error,
        }

    async def ejecutar_extraccion_background(
        self,
        session_id: str,
        config_extractor: Any,  # ConfigExtraccionMasiva
        formatos_exportacion: List[str],
    ):
        """Ejecutar extracción en background.

        Args:
            session_id: ID de la sesión
            config_extractor: Configuración del extractor
            formatos_exportacion: Formatos para exportar
        """
        try:
            # Importar módulos necesarios
            from extraccion_masiva import (
                ExtractorMasivo,
                exportar_excel,
                exportar_json,
            )

            # Crear callbacks
            callbacks = self.crear_callbacks(session_id)

            # Crear extractor
            extractor = ExtractorMasivo(config_extractor, callbacks=callbacks)

            # Guardar extractor en la sesión
            await self.gestor_sesiones.actualizar_progreso(
                session_id, extractor=extractor
            )

            # Ejecutar extracción
            logger.info(f"Iniciando extracción para sesión {session_id}")
            resultado = await extractor.ejecutar_extraccion_completa()

            # Exportar resultados
            archivos = []
            base_path = extractor.session_dir

            for formato in formatos_exportacion:
                try:
                    if formato == "json":
                        archivo = exportar_json(resultado, base_path / "reporte.json")
                        archivos.append(str(archivo))
                    elif formato == "excel":
                        archivo = exportar_excel(
                            resultado, base_path / "reporte.xlsx"
                        )
                        archivos.append(str(archivo))
                    # CSV se exporta automáticamente en ejecutar_extraccion_completa
                except Exception as e:
                    logger.error(f"Error exportando {formato}: {e}")

            # Actualizar sesión con archivos
            await self.gestor_sesiones.actualizar_progreso(
                session_id, archivos=archivos
            )

            # Finalizar sesión
            await self.gestor_sesiones.finalizar_sesion(session_id, resultado)

            logger.info(f"Extracción completada para sesión {session_id}")

        except Exception as e:
            logger.error(f"Error en extracción {session_id}: {e}", exc_info=True)
            await self.gestor_sesiones.marcar_error(session_id, str(e))

    async def pausar_extraccion(self, session_id: str) -> Result[Dict[str, str]]:
        """Pausar una extracción en progreso.

        Args:
            session_id: ID de la sesión

        Returns:
            Result con confirmación
        """
        try:
            sesion = await self.gestor_sesiones.obtener_sesion(session_id)

            if not sesion:
                return Result.failure("Sesión no encontrada")

            if sesion["estado"] != "en_progreso":
                return Result.failure("La sesión no está en progreso")

            # Pausar extractor
            extractor = sesion.get("extractor")
            if extractor and hasattr(extractor, "gestor_batch"):
                extractor.gestor_batch.pausar()

            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                estado="pausado",
                mensaje="Extracción pausada",
            )

            logger.info(f"Extracción pausada: {session_id}")
            return Result.success(
                {"mensaje": "Extracción pausada", "session_id": session_id}
            )

        except Exception as e:
            logger.exception(f"Error al pausar extracción {session_id}")
            return Result.failure(str(e))

    async def reanudar_extraccion(self, session_id: str) -> Result[Dict[str, str]]:
        """Reanudar una extracción pausada.

        Args:
            session_id: ID de la sesión

        Returns:
            Result con confirmación
        """
        try:
            sesion = await self.gestor_sesiones.obtener_sesion(session_id)

            if not sesion:
                return Result.failure("Sesión no encontrada")

            if sesion["estado"] != "pausado":
                return Result.failure("La sesión no está pausada")

            # Reanudar extractor
            extractor = sesion.get("extractor")
            if extractor and hasattr(extractor, "gestor_batch"):
                extractor.gestor_batch.reanudar()

            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                estado="en_progreso",
                mensaje="Extracción reanudada",
            )

            logger.info(f"Extracción reanudada: {session_id}")
            return Result.success(
                {"mensaje": "Extracción reanudada", "session_id": session_id}
            )

        except Exception as e:
            logger.exception(f"Error al reanudar extracción {session_id}")
            return Result.failure(str(e))

    async def cancelar_extraccion(self, session_id: str) -> Result[Dict[str, str]]:
        """Cancelar una extracción.

        Args:
            session_id: ID de la sesión

        Returns:
            Result con confirmación
        """
        try:
            sesion = await self.gestor_sesiones.obtener_sesion(session_id)

            if not sesion:
                return Result.failure("Sesión no encontrada")

            if sesion["estado"] not in ["en_progreso", "pausado"]:
                return Result.failure("La sesión no se puede cancelar")

            # Cancelar extractor
            extractor = sesion.get("extractor")
            if extractor and hasattr(extractor, "cancelar"):
                extractor.cancelar()

            await self.gestor_sesiones.actualizar_progreso(
                session_id,
                estado="cancelado",
                mensaje="Extracción cancelada por el usuario",
                tiempo_fin=datetime.now().isoformat(),
            )

            logger.info(f"Extracción cancelada: {session_id}")
            return Result.success(
                {"mensaje": "Extracción cancelada", "session_id": session_id}
            )

        except Exception as e:
            logger.exception(f"Error al cancelar extracción {session_id}")
            return Result.failure(str(e))
