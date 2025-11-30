"""
Servicio de Monitoreo - Business logic para el sistema de monitoreo.

Este servicio proporciona operaciones CRUD sobre:
- Configuracion de monitoreo por usuario
- Expedientes monitoreados
- Cambios detectados
- Estadisticas

Usa el MonitoreoRepository para persistencia en MySQL.
"""

from __future__ import annotations

import logging
from typing import Optional, Dict, Any, List

from infrastructure.persistence.monitoreo_repository import MonitoreoRepository

logger = logging.getLogger(__name__)


class MonitoreoService:
    """
    Servicio para gestionar el sistema de monitoreo de expedientes.

    Proporciona una fachada sobre MonitoreoRepository con lógica de negocio.
    """

    def __init__(self, repository: Optional[MonitoreoRepository] = None):
        """
        Inicializa el servicio.

        Args:
            repository: Repositorio de monitoreo (se crea uno por defecto si no se provee)
        """
        self._repo = repository or MonitoreoRepository()

    @property
    def repository(self) -> MonitoreoRepository:
        """
        Expone el repositorio para casos donde se necesita acceso directo.

        Returns:
            Repositorio de monitoreo
        """
        return self._repo

    # =========================================================================
    # CONFIGURACION
    # =========================================================================

    def obtener_configuracion(self, usuario_id: int) -> Dict[str, Any]:
        """
        Obtiene la configuración de monitoreo de un usuario.

        Si no existe, crea una configuración por defecto.

        Args:
            usuario_id: ID del usuario

        Returns:
            Configuración del usuario
        """
        return self._repo.obtener_o_crear_configuracion(usuario_id)

    def actualizar_configuracion(
        self,
        usuario_id: int,
        activo: Optional[bool] = None,
        frecuencia: Optional[str] = None,
        notificar_email: Optional[bool] = None,
        notificar_sistema: Optional[bool] = None,
        hora_inicio: Optional[str] = None,
        hora_fin: Optional[str] = None,
        dias_semana: Optional[List[int]] = None,
        # Opciones de extracción
        fecha_corte_dias: Optional[int] = None,
        max_paginas_monitoreo: Optional[int] = None,
        tiempo_maximo_extraccion: Optional[int] = None,
        detener_en_duplicado: Optional[bool] = None,
        orden_extraccion: Optional[str] = None,
        mostrar_navegador_monitoreo: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Actualiza la configuración de monitoreo.

        Args:
            usuario_id: ID del usuario
            **kwargs: Campos a actualizar

        Returns:
            Configuración actualizada
        """
        # Asegurar que existe la configuración
        self._repo.obtener_o_crear_configuracion(usuario_id)

        # Actualizar campos proporcionados
        kwargs = {}
        if activo is not None:
            kwargs['activo'] = activo
        if frecuencia is not None:
            kwargs['frecuencia'] = frecuencia
        if notificar_email is not None:
            kwargs['notificar_email'] = notificar_email
        if notificar_sistema is not None:
            kwargs['notificar_sistema'] = notificar_sistema
        if hora_inicio is not None:
            kwargs['hora_inicio'] = hora_inicio
        if hora_fin is not None:
            kwargs['hora_fin'] = hora_fin
        if dias_semana is not None:
            kwargs['dias_semana'] = dias_semana
        # Opciones de extracción
        if fecha_corte_dias is not None:
            kwargs['fecha_corte_dias'] = fecha_corte_dias
        if max_paginas_monitoreo is not None:
            kwargs['max_paginas_monitoreo'] = max_paginas_monitoreo
        if tiempo_maximo_extraccion is not None:
            kwargs['tiempo_maximo_extraccion'] = tiempo_maximo_extraccion
        if detener_en_duplicado is not None:
            kwargs['detener_en_duplicado'] = detener_en_duplicado
        if orden_extraccion is not None:
            kwargs['orden_extraccion'] = orden_extraccion
        if mostrar_navegador_monitoreo is not None:
            kwargs['mostrar_navegador_monitoreo'] = mostrar_navegador_monitoreo

        if kwargs:
            self._repo.actualizar_configuracion(usuario_id, **kwargs)

        return self._repo.obtener_configuracion(usuario_id)

    # =========================================================================
    # EXPEDIENTES MONITOREADOS
    # =========================================================================

    def agregar_expediente(
        self,
        usuario_id: int,
        expediente_numero: str,
        expediente_caratula: Optional[str] = None,
        expediente_dependencia: Optional[str] = None,
        prioridad: str = 'media',
        notas: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Agrega un expediente al monitoreo.

        Args:
            usuario_id: ID del usuario
            expediente_numero: Número del expediente
            expediente_caratula: Carátula
            expediente_dependencia: Dependencia
            prioridad: 'baja', 'media', 'alta'
            notas: Notas del usuario

        Returns:
            Expediente agregado

        Raises:
            ValueError: Si el expediente ya está siendo monitoreado
        """
        exp_id = self._repo.agregar_expediente(
            usuario_id=usuario_id,
            expediente_numero=expediente_numero,
            expediente_caratula=expediente_caratula,
            expediente_dependencia=expediente_dependencia,
            prioridad=prioridad,
            notas=notas
        )

        return self._repo.obtener_expediente_por_id(exp_id)

    def listar_expedientes(
        self,
        usuario_id: Optional[int] = None,
        solo_activos: bool = False,
        prioridad: Optional[str] = None,
        busqueda: Optional[str] = None,
        pagina: int = 1,
        por_pagina: int = 50
    ) -> Dict[str, Any]:
        """
        Lista los expedientes monitoreados con paginación.
        
        Si usuario_id es None, lista todos los expedientes del sistema (modo compartido).

        Args:
            usuario_id: ID del usuario (opcional para modo compartido)
            solo_activos: Solo listar expedientes activos
            pagina: Número de página
            por_pagina: Elementos por página

        Returns:
            Dict con expedientes y metadatos de paginación
        """
        offset = (pagina - 1) * por_pagina
        
        # Si usuario_id es None, pasamos None al repo para que traiga todo
        # NOTA: El repositorio debe soportar usuario_id=None para traer todo
        expedientes = self._repo.obtener_expedientes(
            usuario_id=usuario_id,
            solo_activos=solo_activos,
            prioridad=prioridad,
            busqueda=busqueda,
            limit=por_pagina,
            offset=offset
        )
        total = self._repo.contar_expedientes(
            usuario_id=usuario_id, 
            solo_activos=solo_activos,
            prioridad=prioridad,
            busqueda=busqueda
        )

        return {
            'expedientes': expedientes,
            'total': total,
            'pagina': pagina,
            'por_pagina': por_pagina,
            'total_paginas': (total + por_pagina - 1) // por_pagina
        }

    def obtener_expediente(
        self,
        usuario_id: int,
        expediente_numero: str
    ) -> Optional[Dict[str, Any]]:
        """
        Obtiene un expediente monitoreado específico.

        Args:
            usuario_id: ID del usuario
            expediente_numero: Número del expediente

        Returns:
            Expediente o None si no existe
        """
        return self._repo.obtener_expediente(usuario_id, expediente_numero)

    def actualizar_expediente(
        self,
        usuario_id: int,
        expediente_numero: str,
        activo: Optional[bool] = None,
        prioridad: Optional[str] = None,
        notas: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Actualiza un expediente monitoreado.

        Args:
            usuario_id: ID del usuario
            expediente_numero: Número del expediente
            activo: Nuevo estado activo
            prioridad: Nueva prioridad
            notas: Nuevas notas

        Returns:
            Expediente actualizado o None si no existe
        """
        exp = self._repo.obtener_expediente(usuario_id, expediente_numero)
        if not exp:
            return None

        kwargs = {}
        if activo is not None:
            kwargs['activo'] = activo
        if prioridad is not None:
            kwargs['prioridad'] = prioridad
        if notas is not None:
            kwargs['notas'] = notas

        if kwargs:
            self._repo.actualizar_expediente(exp['id'], **kwargs)

        return self._repo.obtener_expediente(usuario_id, expediente_numero)

    def eliminar_expediente(self, usuario_id: int, expediente_numero: str) -> bool:
        """
        Elimina un expediente del monitoreo.

        Args:
            usuario_id: ID del usuario
            expediente_numero: Número del expediente

        Returns:
            True si se eliminó
        """
        return self._repo.eliminar_expediente(usuario_id, expediente_numero)

    def pausar_expediente(self, usuario_id: int, expediente_numero: str) -> Optional[Dict[str, Any]]:
        """
        Pausa el monitoreo de un expediente.

        Args:
            usuario_id: ID del usuario
            expediente_numero: Número del expediente

        Returns:
            Expediente actualizado
        """
        return self.actualizar_expediente(usuario_id, expediente_numero, activo=False)

    def reanudar_expediente(self, usuario_id: int, expediente_numero: str) -> Optional[Dict[str, Any]]:
        """
        Reanuda el monitoreo de un expediente.

        Args:
            usuario_id: ID del usuario
            expediente_numero: Número del expediente

        Returns:
            Expediente actualizado
        """
        return self.actualizar_expediente(usuario_id, expediente_numero, activo=True)

    # =========================================================================
    # CAMBIOS DETECTADOS
    # =========================================================================

    def listar_cambios(
        self,
        usuario_id: int,
        solo_no_leidos: bool = False,
        tipo_cambio: Optional[str] = None,
        expediente_numero: Optional[str] = None,
        pagina: int = 1,
        por_pagina: int = 50
    ) -> Dict[str, Any]:
        """
        Lista los cambios detectados con filtros y paginación.

        Args:
            usuario_id: ID del usuario
            solo_no_leidos: Solo cambios sin leer
            tipo_cambio: Filtrar por tipo
            expediente_numero: Filtrar por expediente
            pagina: Número de página
            por_pagina: Elementos por página

        Returns:
            Dict con cambios y metadatos
        """
        offset = (pagina - 1) * por_pagina
        cambios = self._repo.obtener_cambios(
            usuario_id=usuario_id,
            solo_no_leidos=solo_no_leidos,
            tipo_cambio=tipo_cambio,
            expediente_numero=expediente_numero,
            limit=por_pagina,
            offset=offset
        )

        # Contar total de no leídos
        no_leidos = self._repo.contar_cambios_no_leidos(usuario_id)

        return {
            'cambios': cambios,
            'total_no_leidos': no_leidos,
            'pagina': pagina,
            'por_pagina': por_pagina
        }

    def marcar_leido(self, cambio_id: int) -> bool:
        """
        Marca un cambio como leído.

        Args:
            cambio_id: ID del cambio

        Returns:
            True si se marcó
        """
        return self._repo.marcar_cambio_leido(cambio_id)

    def marcar_todos_leidos(self, usuario_id: int) -> int:
        """
        Marca todos los cambios del usuario como leídos.

        Args:
            usuario_id: ID del usuario

        Returns:
            Cantidad de cambios marcados
        """
        return self._repo.marcar_todos_leidos(usuario_id)

    def contar_no_leidos(self, usuario_id: int) -> int:
        """
        Cuenta los cambios no leídos del usuario.

        Args:
            usuario_id: ID del usuario

        Returns:
            Total de cambios no leídos
        """
        return self._repo.contar_cambios_no_leidos(usuario_id)

    # =========================================================================
    # ESTADISTICAS
    # =========================================================================

    def obtener_estadisticas(self, usuario_id: int) -> Dict[str, Any]:
        """
        Obtiene estadísticas del monitoreo de un usuario.

        Args:
            usuario_id: ID del usuario

        Returns:
            Dict con estadísticas
        """
        return self._repo.obtener_estadisticas(usuario_id)

    # =========================================================================
    # UTILIDADES
    # =========================================================================

    def registrar_cambio(
        self,
        usuario_id: int,
        expediente_numero: str,
        tipo_cambio: str,
        descripcion: str,
        detalles: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Registra un cambio detectado en un expediente.

        Args:
            usuario_id: ID del usuario
            expediente_numero: Número del expediente
            tipo_cambio: Tipo de cambio
            descripcion: Descripción
            detalles: Detalles adicionales

        Returns:
            ID del cambio registrado

        Raises:
            ValueError: Si el expediente no está siendo monitoreado
        """
        exp = self._repo.obtener_expediente(usuario_id, expediente_numero)
        if not exp:
            raise ValueError(f"Expediente {expediente_numero} no está siendo monitoreado")

        return self._repo.registrar_cambio(
            expediente_monitoreado_id=exp['id'],
            expediente_numero=expediente_numero,
            tipo_cambio=tipo_cambio,
            descripcion=descripcion,
            expediente_caratula=exp.get('expediente_caratula'),
            detalles=detalles
        )

    def obtener_expedientes_para_verificar(self, usuario_id: int) -> List[Dict[str, Any]]:
        """
        Obtiene los expedientes activos que deben ser verificados.

        Args:
            usuario_id: ID del usuario

        Returns:
            Lista de expedientes activos
        """
        return self._repo.obtener_expedientes(
            usuario_id=usuario_id,
            solo_activos=True
        )

    def exportar_expedientes(
        self,
        usuario_id: Optional[int] = None,
        solo_activos: bool = False,
        prioridad: Optional[str] = None,
        busqueda: Optional[str] = None,
        formato: str = 'csv'
    ) -> str:
        """
        Exporta los expedientes monitoreados a CSV.

        Args:
            usuario_id: ID del usuario (opcional)
            solo_activos: Filtrar solo activos
            prioridad: Filtrar por prioridad
            busqueda: Filtrar por búsqueda
            formato: Formato de exportación ('csv')

        Returns:
            Contenido del archivo exportado
        """
        # Obtener todos (limit alto para traer todo)
        expedientes = self._repo.obtener_expedientes(
            usuario_id=usuario_id,
            solo_activos=solo_activos,
            prioridad=prioridad,
            busqueda=busqueda,
            limit=100000,
            offset=0
        )

        if formato == 'csv':
            import csv
            import io

            output = io.StringIO()
            writer = csv.writer(output)

            # Headers
            writer.writerow([
                'Expediente', 'Carátula', 'Dependencia', 'Estado',
                'Prioridad', 'Última Verificación', 'Cambios Detectados', 'Notas'
            ])

            for exp in expedientes:
                writer.writerow([
                    exp['expediente_numero'],
                    exp.get('expediente_caratula', ''),
                    exp.get('expediente_dependencia', ''),
                    'Activo' if exp['activo'] else 'Pausado',
                    exp['prioridad'],
                    exp.get('ultima_verificacion', ''),
                    exp['total_cambios_detectados'],
                    exp.get('notas', '')
                ])

            return output.getvalue()

        raise ValueError(f"Formato {formato} no soportado")

