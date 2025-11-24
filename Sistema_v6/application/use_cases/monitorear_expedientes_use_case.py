"""Use Case: Monitorear Expedientes.

Este use case implementa el paso 4 del workflow:
"Monitoreo para el mantenimiento actualizado del JSON 'sistema', con cada variación actualizar el workspace"

Modificado para usar ExtractorMasivo en lugar de PlaywrightScraperAdapter.
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
    from infrastructure.config import Settings

logger = logging.getLogger(__name__)


def normalizar_numero_expediente(numero: str) -> str:
    """Normaliza el formato del número de expediente.

    Convierte diferentes formatos a uno común:
    - 'FRE 004379/2021' → 'FRE-004379-2021'
    - 'FRE-004379-2021' → 'FRE-004379-2021'
    - 'FRE004379/2021' → 'FRE-004379-2021'

    Args:
        numero: Número de expediente en cualquier formato

    Returns:
        Número normalizado con formato 'XXX-NNNNNN-YYYY'
    """
    import re
    # Extraer componentes: prefijo (letras), número, año
    # Patrones posibles:
    # FRE-010171-2019, FRE 004379/2021, FRE004379/2021, FPA_005672_2014
    match = re.match(r'([A-Z]+)[\s\-_]?(\d+)[\-/_](\d{4})', numero.strip().upper())
    if match:
        prefijo = match.group(1)
        num = match.group(2).zfill(6)  # Pad con ceros a 6 dígitos
        anio = match.group(3)
        return f"{prefijo}-{num}-{anio}"
    return numero  # Devolver original si no matchea


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
        detector_cambios: "DetectorCambios | None" = None,
        gestor_estados: "GestorEstadosExpedientes | None" = None,
        settings: "Settings | None" = None,
    ):
        """Inicializa el use case con sus dependencias.

        Args:
            scraper: Port para scraping
            expediente_repo: Repositorio de expedientes
            actuacion_repo: Repositorio de actuaciones
            storage: Port para almacenamiento
            workspace_port: Port para workspaces
            notificacion_port: Port para notificaciones (opcional)
            detector_cambios: Detector de cambios multi-campo (opcional)
            gestor_estados: Gestor de estados de expedientes (opcional)
            settings: Configuración del sistema (para credenciales PJN)
        """
        self._scraper = scraper
        self._expediente_repo = expediente_repo
        self._actuacion_repo = actuacion_repo
        self._storage = storage
        self._workspace_port = workspace_port
        self._notificacion_port = notificacion_port
        self._settings = settings

        # Nuevos componentes de Fase 1
        self._detector_cambios = detector_cambios
        self._gestor_estados = gestor_estados

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

            # 2. Extraer lista actualizada del PJN usando ExtractorMasivo
            logger.info("Extrayendo datos actualizados del PJN con ExtractorMasivo...")

            # Obtener credenciales desde múltiples fuentes (en orden de prioridad)
            import os
            username = None
            password = None

            # Opción 1: desde la base de datos del usuario (credenciales encriptadas)
            try:
                from infrastructure.persistence.database import get_db, Usuario
                from infrastructure.security import decrypt_credentials

                # Obtener sesión de BD
                db = next(get_db())
                try:
                    # Por ahora usar usuario_id=1 (igual que MonitoreoService)
                    usuario = db.query(Usuario).filter(Usuario.id == 1).first()
                    if usuario and usuario.pjn_usuario_encrypted and usuario.pjn_password_encrypted:
                        username = decrypt_credentials(usuario.pjn_usuario_encrypted)
                        password = decrypt_credentials(usuario.pjn_password_encrypted)
                        if username and password:
                            logger.debug("Usando credenciales desde base de datos (desencriptadas)")
                finally:
                    db.close()
            except Exception as e:
                logger.debug(f"No se pudieron obtener credenciales de BD: {e}")

            # Opción 2: desde settings
            if not username and self._settings and self._settings.auth.usuario and self._settings.auth.password:
                username = self._settings.auth.usuario
                password = self._settings.auth.password
                logger.debug("Usando credenciales desde settings")

            # Opción 3: desde variables de entorno directamente (fallback)
            if not username:
                username = os.getenv("PJN_USER")
                password = os.getenv("PJN_PASSWORD")
                if username and password:
                    logger.debug("Usando credenciales desde variables de entorno")
                else:
                    logger.warning("No se encontraron credenciales PJN - configure en Configuración > Credenciales PJN")

            # Usar ExtractorMasivo para obtener el listado completo
            from extraccion_masiva.extractor_masivo import ExtractorMasivo
            from extraccion_masiva.models import ConfigExtraccionMasiva
            import json

            # Configurar extractor con headless según comando
            config = ConfigExtraccionMasiva(headless=command.headless)
            extractor = ExtractorMasivo(config=config)

            # Ejecutar extracción
            sesion = await extractor.extraer_listado_completo(
                username=username,
                password=password,
            )

            # Cargar expedientes del JSON generado
            expedientes_actualizados = []
            print(f"DEBUG: Sesion listado_path: {sesion.listado_path}")
            print(f"DEBUG: Sesion estado: {sesion.estado}")
            logger.info(f"Sesion listado_path: {sesion.listado_path}")
            logger.info(f"Sesion estado: {sesion.estado}")

            if sesion.listado_path:
                # El ExtractorMasivo genera la ruta relativa al CWD donde se ejecuta
                # Usar directamente la ruta proporcionada
                print(f"DEBUG: Intentando abrir archivo: {sesion.listado_path}")
                logger.info(f"Intentando abrir archivo: {sesion.listado_path}")

                try:
                    with open(sesion.listado_path, 'r', encoding='utf-8') as f:
                        datos = json.load(f)
                        lista_exp = datos.get("expedientes", [])
                        print(f"DEBUG: Archivo cargado correctamente, {len(lista_exp)} expedientes")
                except Exception as e:
                    print(f"DEBUG ERROR: Error al abrir archivo: {e}")
                    import traceback
                    traceback.print_exc()
                    lista_exp = []

                # Convertir a ExpedienteResumen
                for exp_data in lista_exp:
                    exp_resumen = ExpedienteResumen(
                        numero=exp_data.get("numero", ""),
                        caratula=exp_data.get("caratula", ""),
                        dependencia=exp_data.get("dependencia", ""),
                        situacion=exp_data.get("situacion", ""),
                        ultima_actuacion=exp_data.get("ultima_actuacion", ""),
                    )
                    expedientes_actualizados.append(exp_resumen)

            print(f"DEBUG: Expedientes actualizados cargados: {len(expedientes_actualizados)}")
            logger.info(f"Datos actualizados obtenidos: {len(expedientes_actualizados)}")

            # Crear diccionario para búsqueda rápida con números normalizados
            dict_actualizados = {
                normalizar_numero_expediente(exp.numero): exp for exp in expedientes_actualizados
            }

            # DEBUG: Mostrar información para comparación
            print(f"DEBUG: Expedientes en sistema a monitorear: {len(expedientes)}")
            if expedientes:
                nums_sistema_norm = [normalizar_numero_expediente(e.numero) for e in expedientes[:3]]
                print(f"DEBUG: Primeros 3 del sistema (normalizados): {nums_sistema_norm}")
            if expedientes_actualizados:
                nums_ext_norm = [normalizar_numero_expediente(e.numero) for e in expedientes_actualizados[:3]]
                print(f"DEBUG: Primeros 3 del extractor (normalizados): {nums_ext_norm}")

            # Verificar coincidencias con números normalizados
            nums_sistema = {normalizar_numero_expediente(e.numero) for e in expedientes}
            nums_actualizados = set(dict_actualizados.keys())
            coincidencias = nums_sistema & nums_actualizados
            print(f"DEBUG: Coincidencias encontradas: {len(coincidencias)}")
            if coincidencias:
                print(f"DEBUG: Ejemplos de coincidencias: {list(coincidencias)[:3]}")

            # 3. Filtrar expedientes por estado (si gestor disponible)
            expedientes_monitoreados = expedientes
            if self._gestor_estados:
                logger.info("Filtrando expedientes por estado...")
                estados = await self._gestor_estados.cargar_estados()
                expedientes_monitoreados = [
                    exp for exp in expedientes
                    if estados.get(exp.numero, "activo") == "activo"
                ]
                logger.info(
                    f"Expedientes activos: {len(expedientes_monitoreados)} "
                    f"de {len(expedientes)} totales"
                )

            # 4. Comparar y detectar cambios (multi-campo si detector disponible)
            cambios_detectados: list[CambioDetectado] = []
            expedientes_verificados = 0

            # Opción A: Usar DetectorCambios (detección multi-campo)
            if self._detector_cambios:
                logger.info("Usando DetectorCambios (4 campos)")

                # Filtrar expedientes actualizados que estamos monitoreando
                expedientes_actuales_filtrados = [
                    dict_actualizados[normalizar_numero_expediente(exp.numero)]
                    for exp in expedientes_monitoreados
                    if normalizar_numero_expediente(exp.numero) in dict_actualizados
                ]

                # Detectar cambios
                from application.services.detector_cambios import CambioExpediente

                cambios_multi: list[CambioExpediente] = self._detector_cambios.detectar_cambios_expedientes(
                    actuales=expedientes_actuales_filtrados,
                    anteriores=expedientes_monitoreados
                )

                # Convertir a CambioDetectado para compatibilidad
                for cambio_multi in cambios_multi:
                    cambio = CambioDetectado(
                        numero_expediente=cambio_multi.expediente.numero,
                        tipo=cambio_multi.tipo_cambio,
                        descripcion=self._generar_descripcion_cambio(cambio_multi),
                        datos_adicionales={
                            "campos_cambiados": cambio_multi.campos_cambiados,
                            "valores_anteriores": cambio_multi.valores_anteriores,
                        },
                    )
                    cambios_detectados.append(cambio)

                    # Actualizar workspace con nuevas actuaciones
                    await self._actualizar_workspace(
                        cambio_multi.expediente,
                        command.base_path,
                        command.descargar_nuevos_archivos,
                        command.headless,
                    )

                    # Actualizar repositorio
                    await self._expediente_repo.guardar(cambio_multi.expediente)

                expedientes_verificados = len(expedientes_actuales_filtrados)

            # Opción B: Comparación simple (solo última_actuación - legacy)
            else:
                logger.info("Usando comparación simple (solo última_actuación)")

                for expediente_anterior in expedientes_monitoreados:
                    try:
                        expedientes_verificados += 1
                        logger.debug(f"Verificando {expediente_anterior.numero}")

                        # Buscar versión actualizada (con número normalizado)
                        num_normalizado = normalizar_numero_expediente(expediente_anterior.numero)
                        expediente_actual = dict_actualizados.get(num_normalizado)
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
                                command.headless,
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
                    dict_actualizados[normalizar_numero_expediente(exp.numero)]
                    for exp in expedientes
                    if normalizar_numero_expediente(exp.numero) in dict_actualizados
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

    def _generar_descripcion_cambio(self, cambio: "CambioExpediente") -> str:
        """Genera una descripción legible del cambio detectado.

        Args:
            cambio: CambioExpediente con los detalles del cambio

        Returns:
            Descripción en texto del cambio
        """
        from application.services.detector_cambios import CambioExpediente

        tipo = cambio.tipo_cambio
        campos = cambio.campos_cambiados
        valores_ant = cambio.valores_anteriores

        # Descripción según tipo de cambio
        if tipo == "nueva_actuacion":
            fecha_anterior = valores_ant.get("ultima_actuacion", "")
            fecha_nueva = cambio.expediente.ultima_actuacion
            return f"Nueva actuación: {fecha_anterior} → {fecha_nueva}"

        elif tipo == "cambio_situacion":
            situacion_anterior = valores_ant.get("situacion", "")
            situacion_nueva = cambio.expediente.situacion
            return f"Cambio de situación: '{situacion_anterior}' → '{situacion_nueva}'"

        elif tipo == "cambio_dependencia":
            dep_anterior = valores_ant.get("dependencia", "")
            dep_nueva = cambio.expediente.dependencia
            return f"Cambio de dependencia: '{dep_anterior}' → '{dep_nueva}'"

        elif tipo == "cambio_caratula":
            return "Cambio en carátula del expediente"

        elif tipo == "multiples_cambios":
            descripciones = []
            if "ultima_actuacion" in campos:
                descripciones.append(
                    f"actuación ({valores_ant.get('ultima_actuacion', '')} → "
                    f"{cambio.expediente.ultima_actuacion})"
                )
            if "situacion" in campos:
                descripciones.append(
                    f"situación ('{valores_ant.get('situacion', '')}' → "
                    f"'{cambio.expediente.situacion}')"
                )
            if "dependencia" in campos:
                descripciones.append(
                    f"dependencia ('{valores_ant.get('dependencia', '')}' → "
                    f"'{cambio.expediente.dependencia}')"
                )
            if "caratula" in campos:
                descripciones.append("carátula")

            return f"Múltiples cambios: {', '.join(descripciones)}"

        else:
            # Fallback genérico
            return f"Cambio detectado en: {', '.join(campos)}"

    async def _actualizar_workspace(
        self,
        expediente: "ExpedienteResumen",
        base_path: "Path",
        descargar_archivos: bool,
        headless: bool = True,
    ) -> None:
        """Actualiza el workspace de un expediente con nuevas actuaciones.

        Args:
            expediente: Expediente con datos actualizados
            base_path: Directorio base de workspaces
            descargar_archivos: Si True, descarga archivos nuevos
            headless: Si True, ejecuta el navegador sin interfaz gráfica
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
                headless=headless,
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
