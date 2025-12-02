"""Servicio de Alertas de Vencimientos.

Gestiona la creación, programación y envío de alertas para vencimientos próximos.

Características:
- Generación de alertas según configuración del usuario
- Soporte multi-canal: in_app, email, push, webhook
- Scheduler para verificación periódica
- Registro de historial de alertas
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Optional
from enum import Enum

if TYPE_CHECKING:
    from infrastructure.persistence.alertas_repository import AlertasRepository
    from infrastructure.persistence.vencimientos_repository import VencimientosRepository

logger = logging.getLogger(__name__)


class TipoAlerta(str, Enum):
    """Tipos de alerta según proximidad al vencimiento."""
    TRES_DIAS = "3_dias"
    UN_DIA = "1_dia"
    HOY = "hoy"
    VENCIDO = "vencido"


class CanalAlerta(str, Enum):
    """Canales de envío de alertas."""
    EMAIL = "email"
    PUSH = "push"
    WEBHOOK = "webhook"
    IN_APP = "in_app"


class PrioridadNotificacion(str, Enum):
    """Prioridad de notificaciones."""
    BAJA = "baja"
    NORMAL = "normal"
    ALTA = "alta"
    URGENTE = "urgente"


class AlertasService:
    """Servicio para gestión de alertas de vencimientos.

    Responsabilidades:
    - Generar alertas para vencimientos próximos
    - Programar envío de alertas según configuración
    - Crear notificaciones in-app
    - Gestionar configuración de alertas por usuario

    Example:
        >>> service = AlertasService(alertas_repo, vencimientos_repo)
        >>> await service.verificar_y_generar_alertas(usuario_id=1)
        >>> notificaciones = service.obtener_notificaciones_pendientes(usuario_id=1)
    """

    def __init__(
        self,
        alertas_repository: "AlertasRepository",
        vencimientos_repository: "VencimientosRepository",
    ):
        """Inicializa el servicio.

        Args:
            alertas_repository: Repositorio para alertas y notificaciones
            vencimientos_repository: Repositorio para consultar vencimientos
        """
        self._alertas_repo = alertas_repository
        self._vencimientos_repo = vencimientos_repository
        logger.info("AlertasService inicializado")

    # =========================================================================
    # Generación de alertas
    # =========================================================================

    async def verificar_y_generar_alertas(self, usuario_id: int = 1) -> dict:
        """Verifica vencimientos y genera alertas según configuración.

        Este método debería ejecutarse periódicamente (ej: cada hora).

        Args:
            usuario_id: ID del usuario para obtener su configuración

        Returns:
            Resumen de alertas generadas
        """
        logger.info(f"Verificando vencimientos para generar alertas (usuario={usuario_id})")

        # Obtener configuración del usuario
        config = self._alertas_repo.obtener_configuracion_usuario(usuario_id)
        if not config or not config.get("activo", True):
            logger.debug(f"Alertas deshabilitadas para usuario {usuario_id}")
            return {"alertas_generadas": 0, "motivo": "alertas deshabilitadas"}

        # Obtener días de anticipación configurados
        dias_anticipacion = config.get("dias_anticipacion") or [3, 1, 0]
        expedientes_excluidos = config.get("expedientes_excluidos") or []

        # Obtener vencimientos próximos
        max_dias = max(dias_anticipacion) if dias_anticipacion else 3
        vencimientos = self._vencimientos_repo.listar_vencimientos(
            estado="pendiente",
            dias_hasta=max_dias + 1,  # +1 para incluir vencidos recientes
            dias_desde=-1,  # Incluir vencidos de hoy
            limite=500
        )

        alertas_generadas = 0
        notificaciones_creadas = 0

        for venc in vencimientos:
            # Saltar expedientes excluidos
            if venc.get("expediente_numero") in expedientes_excluidos:
                continue

            # Calcular días restantes
            fecha_venc = venc.get("fecha_vencimiento")
            if isinstance(fecha_venc, str):
                fecha_venc = datetime.fromisoformat(fecha_venc.replace("Z", "+00:00"))

            hoy = datetime.now().date()
            dias_restantes = (fecha_venc.date() - hoy).days if hasattr(fecha_venc, 'date') else (fecha_venc - hoy).days

            # Determinar tipo de alerta
            tipo_alerta = self._determinar_tipo_alerta(dias_restantes)
            if not tipo_alerta:
                continue

            # Verificar si corresponde generar alerta según configuración
            if tipo_alerta == TipoAlerta.TRES_DIAS and 3 not in dias_anticipacion:
                continue
            if tipo_alerta == TipoAlerta.UN_DIA and 1 not in dias_anticipacion:
                continue
            if tipo_alerta == TipoAlerta.HOY and 0 not in dias_anticipacion:
                continue

            vencimiento_id = venc.get("id")

            # Verificar si ya existe alerta de este tipo para este vencimiento
            if self._alertas_repo.existe_alerta(vencimiento_id, tipo_alerta.value):
                continue

            # Crear alerta programada
            alerta_id = self._alertas_repo.crear_alerta(
                vencimiento_id=vencimiento_id,
                tipo_alerta=tipo_alerta.value,
                canal=CanalAlerta.IN_APP.value,  # Por defecto in_app
                fecha_programada=datetime.now(),
            )
            alertas_generadas += 1

            # Crear notificación in-app si está habilitado
            if config.get("alertas_in_app", True):
                self._crear_notificacion_vencimiento(
                    usuario_id=usuario_id,
                    vencimiento=venc,
                    tipo_alerta=tipo_alerta,
                    dias_restantes=dias_restantes
                )
                notificaciones_creadas += 1

                # Marcar alerta como enviada
                self._alertas_repo.marcar_alerta_enviada(alerta_id)

        resultado = {
            "alertas_generadas": alertas_generadas,
            "notificaciones_creadas": notificaciones_creadas,
            "vencimientos_evaluados": len(vencimientos),
            "timestamp": datetime.now().isoformat()
        }

        logger.info(f"Verificación completada: {alertas_generadas} alertas, {notificaciones_creadas} notificaciones")
        return resultado

    def _determinar_tipo_alerta(self, dias_restantes: int) -> Optional[TipoAlerta]:
        """Determina el tipo de alerta según días restantes.

        Args:
            dias_restantes: Días hasta el vencimiento (negativo si vencido)

        Returns:
            Tipo de alerta correspondiente o None
        """
        if dias_restantes < 0:
            return TipoAlerta.VENCIDO
        elif dias_restantes == 0:
            return TipoAlerta.HOY
        elif dias_restantes == 1:
            return TipoAlerta.UN_DIA
        elif dias_restantes <= 3:
            return TipoAlerta.TRES_DIAS
        return None

    def _crear_notificacion_vencimiento(
        self,
        usuario_id: int,
        vencimiento: dict,
        tipo_alerta: TipoAlerta,
        dias_restantes: int
    ) -> int:
        """Crea una notificación in-app para un vencimiento.

        Args:
            usuario_id: ID del usuario destinatario
            vencimiento: Datos del vencimiento
            tipo_alerta: Tipo de alerta
            dias_restantes: Días hasta vencimiento

        Returns:
            ID de la notificación creada
        """
        expediente = vencimiento.get("expediente_numero", "N/A")
        descripcion = vencimiento.get("descripcion", vencimiento.get("tipo", ""))

        # Determinar título y prioridad según tipo
        if tipo_alerta == TipoAlerta.VENCIDO:
            titulo = f"VENCIDO: {expediente}"
            mensaje = f"El plazo '{descripcion}' ha vencido hace {abs(dias_restantes)} día(s)"
            prioridad = PrioridadNotificacion.URGENTE
        elif tipo_alerta == TipoAlerta.HOY:
            titulo = f"VENCE HOY: {expediente}"
            mensaje = f"El plazo '{descripcion}' vence hoy"
            prioridad = PrioridadNotificacion.URGENTE
        elif tipo_alerta == TipoAlerta.UN_DIA:
            titulo = f"Vence mañana: {expediente}"
            mensaje = f"El plazo '{descripcion}' vence mañana"
            prioridad = PrioridadNotificacion.ALTA
        else:
            titulo = f"Próximo vencimiento: {expediente}"
            mensaje = f"El plazo '{descripcion}' vence en {dias_restantes} días"
            prioridad = PrioridadNotificacion.NORMAL

        return self._alertas_repo.crear_notificacion(
            usuario_id=usuario_id,
            tipo="vencimiento",
            titulo=titulo,
            mensaje=mensaje,
            prioridad=prioridad.value,
            url_accion=f"/expedientes/{expediente}",
            datos_extra={
                "vencimiento_id": vencimiento.get("id"),
                "expediente_numero": expediente,
                "tipo_alerta": tipo_alerta.value,
                "dias_restantes": dias_restantes,
                "fecha_vencimiento": str(vencimiento.get("fecha_vencimiento"))
            }
        )

    # =========================================================================
    # Gestión de notificaciones
    # =========================================================================

    def obtener_notificaciones(
        self,
        usuario_id: int,
        solo_no_leidas: bool = False,
        limite: int = 50,
        offset: int = 0
    ) -> list[dict]:
        """Obtiene notificaciones para un usuario.

        Args:
            usuario_id: ID del usuario
            solo_no_leidas: Si True, solo retorna no leídas
            limite: Máximo de notificaciones a retornar
            offset: Offset para paginación

        Returns:
            Lista de notificaciones
        """
        return self._alertas_repo.listar_notificaciones(
            usuario_id=usuario_id,
            solo_no_leidas=solo_no_leidas,
            limite=limite,
            offset=offset
        )

    def contar_no_leidas(self, usuario_id: int) -> int:
        """Cuenta notificaciones no leídas.

        Args:
            usuario_id: ID del usuario

        Returns:
            Número de notificaciones no leídas
        """
        return self._alertas_repo.contar_notificaciones_no_leidas(usuario_id)

    def marcar_como_leida(self, notificacion_id: int, usuario_id: int) -> bool:
        """Marca una notificación como leída.

        Args:
            notificacion_id: ID de la notificación
            usuario_id: ID del usuario (para verificación)

        Returns:
            True si se marcó correctamente
        """
        return self._alertas_repo.marcar_notificacion_leida(notificacion_id, usuario_id)

    def marcar_todas_leidas(self, usuario_id: int) -> int:
        """Marca todas las notificaciones como leídas.

        Args:
            usuario_id: ID del usuario

        Returns:
            Número de notificaciones marcadas
        """
        return self._alertas_repo.marcar_todas_leidas(usuario_id)

    def obtener_estadisticas(self, usuario_id: int) -> dict:
        """Obtiene estadísticas de notificaciones.

        Args:
            usuario_id: ID del usuario

        Returns:
            Diccionario con estadísticas
        """
        return self._alertas_repo.obtener_estadisticas_notificaciones(usuario_id)

    # =========================================================================
    # Configuración de alertas
    # =========================================================================

    def obtener_configuracion(self, usuario_id: int) -> dict:
        """Obtiene la configuración de alertas de un usuario.

        Args:
            usuario_id: ID del usuario

        Returns:
            Configuración de alertas
        """
        config = self._alertas_repo.obtener_configuracion_usuario(usuario_id)
        if not config:
            # Crear configuración por defecto
            config = self._alertas_repo.crear_configuracion_usuario(usuario_id)
        return config

    def actualizar_configuracion(
        self,
        usuario_id: int,
        alertas_email: Optional[bool] = None,
        alertas_push: Optional[bool] = None,
        alertas_in_app: Optional[bool] = None,
        dias_anticipacion: Optional[list[int]] = None,
        hora_envio: Optional[str] = None,
        expedientes_excluidos: Optional[list[str]] = None,
        activo: Optional[bool] = None
    ) -> dict:
        """Actualiza la configuración de alertas.

        Args:
            usuario_id: ID del usuario
            alertas_email: Habilitar alertas por email
            alertas_push: Habilitar alertas push
            alertas_in_app: Habilitar notificaciones in-app
            dias_anticipacion: Lista de días antes para alertar [3, 1, 0]
            hora_envio: Hora preferida de envío (HH:MM:SS)
            expedientes_excluidos: Lista de expedientes a excluir
            activo: Si las alertas están activas

        Returns:
            Configuración actualizada
        """
        return self._alertas_repo.actualizar_configuracion_usuario(
            usuario_id=usuario_id,
            alertas_email=alertas_email,
            alertas_push=alertas_push,
            alertas_in_app=alertas_in_app,
            dias_anticipacion=dias_anticipacion,
            hora_envio=hora_envio,
            expedientes_excluidos=expedientes_excluidos,
            activo=activo
        )

    # =========================================================================
    # Utilidades
    # =========================================================================

    def crear_notificacion_sistema(
        self,
        usuario_id: int,
        titulo: str,
        mensaje: str,
        tipo: str = "sistema",
        prioridad: str = "normal",
        url_accion: Optional[str] = None,
        datos_extra: Optional[dict] = None
    ) -> int:
        """Crea una notificación de sistema.

        Útil para notificar sobre eventos del sistema como:
        - Extracción completada
        - Errores de monitoreo
        - Cambios detectados

        Args:
            usuario_id: ID del usuario destinatario
            titulo: Título de la notificación
            mensaje: Mensaje descriptivo
            tipo: Tipo de notificación (sistema, monitoreo, extraccion, error)
            prioridad: Prioridad (baja, normal, alta, urgente)
            url_accion: URL para redirigir al hacer clic
            datos_extra: Datos adicionales en JSON

        Returns:
            ID de la notificación creada
        """
        return self._alertas_repo.crear_notificacion(
            usuario_id=usuario_id,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            prioridad=prioridad,
            url_accion=url_accion,
            datos_extra=datos_extra
        )

    def eliminar_notificaciones_expiradas(self) -> int:
        """Elimina notificaciones que han expirado.

        Returns:
            Número de notificaciones eliminadas
        """
        return self._alertas_repo.eliminar_expiradas()
