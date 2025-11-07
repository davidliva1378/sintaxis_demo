"""Use Case: Crear Workspaces.

Este use case implementa el paso 3 del workflow:
"Generar directorios de cada expediente (crear workspace)"
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from application.dtos import CrearWorkspacesCommand, Result
    from application.dtos.responses import CrearWorkspacesResponse
    from application.ports import (
        IActuacionRepository,
        IScraperPort,
        IStoragePort,
        IWorkspacePort,
    )

logger = logging.getLogger(__name__)


class CrearWorkspacesUseCase:
    """Use case para crear workspaces para expedientes seleccionados.

    Este use case lee el JSON "sistema" y crea la estructura de directorios
    (workspace) para cada expediente, opcionalmente extrayendo actuaciones
    y descargando archivos adjuntos.

    Dependencies:
        workspace_port: Port para gestión de workspaces
        storage: Port para almacenamiento de archivos
        scraper: Port para scraping (si se extraen actuaciones)
        actuacion_repo: Repositorio de actuaciones (si se extraen actuaciones)
    """

    def __init__(
        self,
        workspace_port: IWorkspacePort,
        storage: IStoragePort,
        scraper: IScraperPort | None = None,
        actuacion_repo: IActuacionRepository | None = None,
    ):
        """Inicializa el use case con sus dependencias.

        Args:
            workspace_port: Port para gestión de workspaces
            storage: Port para almacenamiento
            scraper: Port para scraping (opcional, necesario si extraer_actuaciones=True)
            actuacion_repo: Repositorio de actuaciones (opcional)
        """
        self._workspace_port = workspace_port
        self._storage = storage
        self._scraper = scraper
        self._actuacion_repo = actuacion_repo

    async def execute(
        self, command: CrearWorkspacesCommand
    ) -> Result[CrearWorkspacesResponse]:
        """Ejecuta el caso de uso.

        Args:
            command: Comando con parámetros de creación

        Returns:
            Result con la respuesta o error
        """
        from application.dtos import Result
        from core.domain.entities import ExpedienteIdentificacion, ExpedienteResumen
        from core.domain.utils import descomponer_numero_expediente

        try:
            logger.info("Iniciando creación de workspaces")

            # 1. Leer el JSON "sistema"
            logger.info(f"Leyendo expedientes seleccionados desde {command.json_sistema}")
            datos_sistema = await self._storage.leer_json(command.json_sistema)

            # Convertir a lista si es necesario
            if isinstance(datos_sistema, dict):
                lista_sistema = datos_sistema.get("expedientes", [])
            else:
                lista_sistema = datos_sistema

            expedientes = [ExpedienteResumen.from_dict(data) for data in lista_sistema]
            logger.info(f"Expedientes a procesar: {len(expedientes)}")

            # 2. Crear workspace para cada expediente
            workspaces_creados = []
            errores = []

            for i, expediente in enumerate(expedientes, 1):
                try:
                    logger.info(
                        f"[{i}/{len(expedientes)}] Procesando expediente: {expediente.numero}"
                    )

                    # Crear workspace
                    workspace_path = await self._workspace_port.crear_workspace(
                        expediente.numero,
                        command.base_path,
                    )
                    logger.info(f"Workspace creado: {workspace_path}")

                    # Extraer actuaciones si se solicitó
                    if command.extraer_actuaciones and self._scraper and self._actuacion_repo:
                        logger.info(f"Extrayendo actuaciones de {expediente.numero}")

                        # Descomponer número para obtener identificación
                        _, numero, anio = descomponer_numero_expediente(expediente.numero)
                        if numero and anio:
                            identificacion = ExpedienteIdentificacion(
                                numero=numero, anio=anio
                            )

                            try:
                                archivo_actuaciones = await self._scraper.extraer_actuaciones(
                                    identificacion,
                                    headless=True,
                                )

                                # Guardar actuaciones en repositorio
                                await self._actuacion_repo.guardar_archivo(
                                    expediente.numero,
                                    archivo_actuaciones,
                                )

                                # Guardar actuaciones en JSON dentro del workspace
                                actuaciones_json = workspace_path / "actuaciones.json"
                                await self._storage.guardar_json(
                                    archivo_actuaciones.to_dict(),
                                    actuaciones_json,
                                )
                                logger.info(
                                    f"Actuaciones extraídas: {len(archivo_actuaciones.actuaciones)}"
                                )

                                # TODO: Descargar archivos si se solicitó
                                # Esta funcionalidad se implementará cuando sea necesaria

                            except Exception as e:
                                logger.warning(
                                    f"Error al extraer actuaciones de {expediente.numero}: {e}"
                                )
                        else:
                            logger.warning(
                                f"No se pudo descomponer número: {expediente.numero}"
                            )

                    workspaces_creados.append(workspace_path)

                except Exception as e:
                    error_msg = f"Error al crear workspace para {expediente.numero}: {str(e)}"
                    logger.error(error_msg)
                    errores.append((expediente.numero, str(e)))

            # 3. Construir respuesta
            from application.dtos.responses import CrearWorkspacesResponse

            response = CrearWorkspacesResponse(
                workspaces_creados=workspaces_creados,
                total_creados=len(workspaces_creados),
                total_fallidos=len(errores),
                errores=errores,
            )

            logger.info(
                f"Creación completada: {response.total_creados} exitosos, "
                f"{response.total_fallidos} fallidos"
            )
            return Result.ok(response)

        except FileNotFoundError as e:
            error_msg = f"Archivo no encontrado: {str(e)}"
            logger.error(error_msg)
            return Result.fail(error_msg, error_code="ARCHIVO_NO_ENCONTRADO")
        except Exception as e:
            error_msg = f"Error al crear workspaces: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Result.fail(error_msg, error_code="CREACION_ERROR")
