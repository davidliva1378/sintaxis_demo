"""Use Case: Extraer Expedientes del PJN.

Este use case implementa el paso 1 del workflow:
"Extraer lista completa de expedientes → JSON 'base'"
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from application.dtos import ExtraerExpedientesCommand, Result
    from application.dtos.responses import ExtraerExpedientesResponse
    from application.ports import IExpedienteRepository, IScraperPort, IStoragePort

logger = logging.getLogger(__name__)


class ExtraerExpedientesUseCase:
    """Use case para extraer la lista completa de expedientes del PJN.

    Este use case orquesta el proceso de:
    1. Autenticación en el PJN
    2. Scraping de la lista de expedientes
    3. Persistencia en el repositorio
    4. Guardado opcional en archivo JSON

    Dependencies:
        scraper: Port para interactuar con el PJN
        repository: Repositorio de expedientes
        storage: Port para almacenamiento de archivos
    """

    def __init__(
        self,
        scraper: IScraperPort,
        repository: IExpedienteRepository,
        storage: IStoragePort | None = None,
    ):
        """Inicializa el use case con sus dependencias.

        Args:
            scraper: Port para scraping del PJN
            repository: Repositorio de expedientes
            storage: Port para almacenamiento (opcional)
        """
        self._scraper = scraper
        self._repository = repository
        self._storage = storage

    async def execute(
        self, command: ExtraerExpedientesCommand
    ) -> Result[ExtraerExpedientesResponse]:
        """Ejecuta el caso de uso.

        Args:
            command: Comando con parámetros de ejecución

        Returns:
            Result con la respuesta o error
        """
        from application.dtos import Result

        try:
            logger.info("Iniciando extracción de expedientes del PJN")

            # 1. Preparar credenciales
            credenciales = None
            if command.usuario and command.contrasena:
                credenciales = (command.usuario, command.contrasena)

            # 2. Extraer expedientes via scraping
            logger.info("Ejecutando scraping de expedientes...")
            expedientes = await self._scraper.extraer_expedientes(
                credenciales=credenciales,
                headless=command.headless,
            )

            logger.info(f"Scraping completado: {len(expedientes)} expedientes extraídos")

            # 3. Guardar en el repositorio
            logger.info("Guardando expedientes en repositorio...")
            await self._repository.guardar_varios(expedientes)
            logger.info("Expedientes guardados en repositorio")

            # 4. Guardar en archivo JSON si se especificó
            archivo_guardado = None
            if command.guardar_en and self._storage:
                logger.info(f"Guardando expedientes en {command.guardar_en}")
                datos = [exp.to_dict() for exp in expedientes]
                await self._storage.guardar_json(datos, command.guardar_en)
                archivo_guardado = command.guardar_en
                logger.info(f"Archivo JSON guardado: {archivo_guardado}")

            # 5. Construir respuesta
            from application.dtos.responses import ExtraerExpedientesResponse

            response = ExtraerExpedientesResponse(
                expedientes=expedientes,
                total=len(expedientes),
                archivo_guardado=archivo_guardado,
            )

            logger.info(f"Extracción completada exitosamente: {response.total} expedientes")
            return Result.ok(response)

        except Exception as e:
            error_msg = f"Error al extraer expedientes: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Result.fail(error_msg, error_code="EXTRACCION_ERROR")
