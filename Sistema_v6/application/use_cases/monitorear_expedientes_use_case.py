"""Use Case: Monitorear Expedientes.

Este use case implementa el paso 4 del workflow:
"Monitoreo para el mantenimiento actualizado del JSON 'sistema', con cada variación actualizar el workspace"
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from application.dtos import MonitorearExpedientesCommand, Result
    from application.dtos.responses import CambioDetectado, MonitorearExpedientesResponse
    from application.ports import (
        IActuacionRepository,
        IExpedienteRepository,
        INotificacionPort,
        IScraperPort,
        IStoragePort,
        IWorkspacePort,
    )

logger = logging.getLogger(__name__)


class MonitorearExpedientesUseCase:
    """Use case para monitorear expedientes y detectar cambios.

    Este use case:
    1. Lee el JSON "sistema" con expedientes seleccionados
    2. Extrae datos actualizados del PJN
    3. Compara con los datos anteriores
    4. Detecta cambios (nuevas actuaciones, actualizaciones, archivos nuevos)
    5. Actualiza el workspace
    6. Envía notificaciones si se configuró

    Dependencies:
        scraper: Port para scraping del PJN
        expediente_repo: Repositorio de expedientes
        actuacion_repo: Repositorio de actuaciones
        storage: Port para almacenamiento
        workspace_port: Port para gestión de workspaces
        notificacion_port: Port para notificaciones (opcional)
    """

    def __init__(
        self,
        scraper: IScraperPort,
        expediente_repo: IExpedienteRepository,
        actuacion_repo: IActuacionRepository,
        storage: IStoragePort,
        workspace_port: IWorkspacePort,
        notificacion_port: INotificacionPort | None = None,
    ):
        """Inicializa el use case con sus dependencias.

        Args:
            scraper: Port para scraping
            expediente_repo: Repositorio de expedientes
            actuacion_repo: Repositorio de actuaciones
            storage: Port para almacenamiento
            workspace_port: Port para workspaces
            notificacion_port: Port para notificaciones (opcional)
        """
        self._scraper = scraper
        self._expediente_repo = expediente_repo
        self._actuacion_repo = actuacion_repo
        self._storage = storage
        self._workspace_port = workspace_port
        self._notificacion_port = notificacion_port

    async def execute(
        self, command: MonitorearExpedientesCommand
    ) -> Result[MonitorearExpedientesResponse]:
        """Ejecuta el caso de uso.

        Args:
            command: Comando con parámetros de monitoreo

        Returns:
            Result con la respuesta o error
        """
        from application.dtos import Result
        from application.dtos.responses import CambioDetectado
        from core.domain.entities import ExpedienteIdentificacion, ExpedienteResumen
        from core.domain.utils import descomponer_numero_expediente

        try:
            logger.info("Iniciando monitoreo de expedientes")

            # 1. Leer el JSON "sistema"
            logger.info(f"Leyendo expedientes a monitorear desde {command.json_sistema}")
            datos_sistema = await self._storage.leer_json(command.json_sistema)

            # Convertir a lista si es necesario
            if isinstance(datos_sistema, dict):
                lista_sistema = datos_sistema.get("expedientes", [])
            else:
                lista_sistema = datos_sistema

            expedientes = [ExpedienteResumen.from_dict(data) for data in lista_sistema]
            logger.info(f"Expedientes a monitorear: {len(expedientes)}")

            # 2. Extraer lista actualizada del PJN
            logger.info("Extrayendo datos actualizados del PJN...")
            expedientes_actualizados = await self._scraper.extraer_expedientes(
                headless=True
            )
            logger.info(f"Datos actualizados obtenidos: {len(expedientes_actualizados)}")

            # Crear diccionario para búsqueda rápida
            dict_actualizados = {
                exp.numero: exp for exp in expedientes_actualizados
            }

            # 3. Comparar y detectar cambios
            cambios_detectados: list[CambioDetectado] = []
            expedientes_verificados = 0

            for expediente_anterior in expedientes:
                try:
                    expedientes_verificados += 1
                    logger.debug(f"Verificando {expediente_anterior.numero}")

                    # Buscar versión actualizada
                    expediente_actual = dict_actualizados.get(expediente_anterior.numero)
                    if not expediente_actual:
                        logger.warning(
                            f"Expediente {expediente_anterior.numero} no encontrado en datos actualizados"
                        )
                        continue

                    # Verificar si hubo cambio en última actuación
                    if (
                        expediente_anterior.ultima_actuacion
                        != expediente_actual.ultima_actuacion
                    ):
                        logger.info(
                            f"Cambio detectado en {expediente_anterior.numero}: "
                            f"última actuación {expediente_anterior.ultima_actuacion} → "
                            f"{expediente_actual.ultima_actuacion}"
                        )

                        cambio = CambioDetectado(
                            numero_expediente=expediente_anterior.numero,
                            tipo="actuacion_nueva",
                            descripcion=f"Nueva actuación: {expediente_actual.ultima_actuacion}",
                            datos_adicionales={
                                "fecha_anterior": expediente_anterior.ultima_actuacion,
                                "fecha_nueva": expediente_actual.ultima_actuacion,
                            },
                        )
                        cambios_detectados.append(cambio)

                        # Actualizar workspace con nuevas actuaciones
                        await self._actualizar_workspace(
                            expediente_actual,
                            command.base_path,
                            command.descargar_nuevos_archivos,
                        )

                        # Actualizar repositorio
                        await self._expediente_repo.guardar(expediente_actual)

                except Exception as e:
                    logger.error(
                        f"Error al verificar {expediente_anterior.numero}: {e}"
                    )

            # 4. Actualizar JSON "sistema" si hubo cambios
            if cambios_detectados:
                logger.info(
                    f"Actualizando JSON 'sistema' con {len(cambios_detectados)} cambios"
                )
                expedientes_actualizados_filtrados = [
                    dict_actualizados[exp.numero]
                    for exp in expedientes
                    if exp.numero in dict_actualizados
                ]
                datos_nuevos = [
                    exp.to_dict() for exp in expedientes_actualizados_filtrados
                ]
                await self._storage.guardar_json(datos_nuevos, command.json_sistema)

            # 5. Enviar notificaciones si se configuró
            notificaciones_enviadas = 0
            if command.notificar_cambios and cambios_detectados and self._notificacion_port:
                logger.info(f"Enviando notificaciones de {len(cambios_detectados)} cambios")
                for cambio in cambios_detectados:
                    try:
                        await self._notificacion_port.notificar_escritorio(
                            titulo="Sistema PJN - Cambio Detectado",
                            mensaje=f"{cambio.numero_expediente}: {cambio.descripcion}",
                            urgencia="normal",
                        )
                        notificaciones_enviadas += 1
                    except Exception as e:
                        logger.warning(f"Error al enviar notificación: {e}")

            # 6. Construir respuesta
            from application.dtos.responses import MonitorearExpedientesResponse

            response = MonitorearExpedientesResponse(
                expedientes_verificados=expedientes_verificados,
                cambios_detectados=cambios_detectados,
                total_cambios=len(cambios_detectados),
                notificaciones_enviadas=notificaciones_enviadas,
            )

            logger.info(
                f"Monitoreo completado: {response.total_cambios} cambios detectados, "
                f"{response.notificaciones_enviadas} notificaciones enviadas"
            )
            return Result.ok(response)

        except FileNotFoundError as e:
            error_msg = f"Archivo no encontrado: {str(e)}"
            logger.error(error_msg)
            return Result.fail(error_msg, error_code="ARCHIVO_NO_ENCONTRADO")
        except Exception as e:
            error_msg = f"Error al monitorear expedientes: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return Result.fail(error_msg, error_code="MONITOREO_ERROR")

    async def _actualizar_workspace(
        self,
        expediente: "ExpedienteResumen",
        base_path: "Path",
        descargar_archivos: bool,
    ) -> None:
        """Actualiza el workspace de un expediente con nuevas actuaciones.

        Args:
            expediente: Expediente con datos actualizados
            base_path: Directorio base de workspaces
            descargar_archivos: Si True, descarga archivos nuevos
        """
        from pathlib import Path

        from core.domain.entities import ExpedienteIdentificacion
        from core.domain.utils import descomponer_numero_expediente

        try:
            workspace_path = await self._workspace_port.obtener_workspace(
                expediente.numero,
                base_path,
            )
            if not workspace_path:
                logger.warning(f"Workspace no existe para {expediente.numero}")
                return

            # Extraer actuaciones actualizadas
            _, numero, anio = descomponer_numero_expediente(expediente.numero)
            if not (numero and anio):
                logger.warning(f"No se pudo descomponer número: {expediente.numero}")
                return

            identificacion = ExpedienteIdentificacion(numero=numero, anio=anio)

            archivo_actuaciones = await self._scraper.extraer_actuaciones(
                identificacion,
                headless=True,
            )

            # Guardar actuaciones actualizadas
            await self._actuacion_repo.guardar_archivo(
                expediente.numero,
                archivo_actuaciones,
            )

            actuaciones_json = Path(workspace_path) / "actuaciones.json"
            await self._storage.guardar_json(
                archivo_actuaciones.to_dict(),
                actuaciones_json,
            )

            logger.info(
                f"Workspace actualizado: {expediente.numero} "
                f"({len(archivo_actuaciones.actuaciones)} actuaciones)"
            )

            # TODO: Implementar descarga de archivos nuevos si se solicitó

        except Exception as e:
            logger.error(
                f"Error al actualizar workspace de {expediente.numero}: {e}"
            )
