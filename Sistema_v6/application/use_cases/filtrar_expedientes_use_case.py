"""Use Case: Filtrar Expedientes.

Este use case implementa el paso 2 del workflow:
"Filtrado, el usuario decide cuáles serán añadidos a la base de datos → JSON 'sistema'"
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from application.dtos import FiltrarExpedientesCommand, Result
    from application.dtos.responses import FiltrarExpedientesResponse
    from application.ports import IExpedienteRepository, IStoragePort

logger = logging.getLogger(__name__)


class FiltrarExpedientesUseCase:
    """Use case para filtrar expedientes según selección del usuario.

    Este use case toma el JSON "base" con todos los expedientes y genera el
    JSON "sistema" con solo los expedientes seleccionados por el usuario.

    El JSON "sistema" será el que se monitoreará posteriormente.

    Dependencies:
        repository: Repositorio de expedientes
        storage: Port para almacenamiento de archivos
    """

    def __init__(
        self,
        repository: IExpedienteRepository,
        storage: IStoragePort,
    ):
        """Inicializa el use case con sus dependencias.

        Args:
            repository: Repositorio de expedientes
            storage: Port para almacenamiento
        """
        self._repository = repository
        self._storage = storage

    async def execute(
        self, command: FiltrarExpedientesCommand
    ) -> Result[FiltrarExpedientesResponse]:
        """Ejecuta el caso de uso.

        Args:
            command: Comando con parámetros de filtrado

        Returns:
            Result con la respuesta o error
        """
        from application.dtos import Result
        from core.domain.entities import ExpedienteResumen

        try:
            logger.info("Iniciando filtrado de expedientes")

            # 1. Leer el JSON "base" (origen)
            logger.info(f"Leyendo expedientes desde {command.origen}")
            datos_origen = await self._storage.leer_json(command.origen)

            # Convertir a lista si es necesario
            if isinstance(datos_origen, dict):
                lista_origen = datos_origen.get("expedientes", [])
            else:
                lista_origen = datos_origen

            expedientes_base = [
                ExpedienteResumen.from_dict(data) for data in lista_origen
            ]
            logger.info(f"Expedientes en base: {len(expedientes_base)}")

            # 2. Filtrar por números seleccionados
            numeros_set = set(command.numeros_seleccionados)
            expedientes_seleccionados = [
                exp for exp in expedientes_base if exp.numero in numeros_set
            ]
            logger.info(
                f"Expedientes seleccionados manualmente: {len(expedientes_seleccionados)}"
            )

            # 3. Añadir expedientes activos si se solicitó
            if command.incluir_activos:
                logger.info(
                    f"Incluyendo expedientes activos (últimos {command.dias_actividad} días)"
                )
                for exp in expedientes_base:
                    if exp.esta_activo(command.dias_actividad) and exp not in expedientes_seleccionados:
                        expedientes_seleccionados.append(exp)
                        logger.debug(f"Expediente activo añadido: {exp.numero}")

                logger.info(
                    f"Total con activos incluidos: {len(expedientes_seleccionados)}"
                )

            # 4. Guardar expedientes seleccionados en el repositorio
            logger.info("Guardando expedientes seleccionados en repositorio...")
            await self._repository.guardar_varios(expedientes_seleccionados)

            # 5. Guardar en JSON "sistema"
            logger.info(f"Guardando JSON 'sistema' en {command.destino}")
            datos_destino = [exp.to_dict() for exp in expedientes_seleccionados]
            await self._storage.guardar_json(datos_destino, command.destino)
            logger.info(f"JSON 'sistema' guardado: {command.destino}")

            # 6. Construir respuesta
            from application.dtos.responses import FiltrarExpedientesResponse

            response = FiltrarExpedientesResponse(
                expedientes_seleccionados=expedientes_seleccionados,
                total=len(expedientes_seleccionados),
                archivo_guardado=command.destino,
            )

            logger.info(
                f"Filtrado completado: {response.total} expedientes seleccionados"
            )
            return Result.ok(response)

        except FileNotFoundError as e:
            error_msg = f"Archivo no encontrado: {str(e)}"
            logger.error(error_msg)
            return Result.fail(error_msg, error_code="ARCHIVO_NO_ENCONTRADO")
        except Exception as e:
            error_msg = f"Error al filtrar expedientes: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Result.fail(error_msg, error_code="FILTRADO_ERROR")
