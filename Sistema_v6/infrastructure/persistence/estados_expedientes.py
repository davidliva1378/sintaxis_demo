"""
Gestor de Estados de Expedientes.

Gestiona los estados de monitoreo de expedientes:
- activo: En seguimiento activo
- pausado: Temporalmente suspendido
- omitido: Excluido del monitoreo
- archivado: No requiere seguimiento

Similar a Sistema_v5/pjn/monitor/storage.py:estados_usuario
"""

from pathlib import Path
import json
from typing import Literal
import logging

logger = logging.getLogger(__name__)

# Tipos de estado válidos
EstadoExpediente = Literal["activo", "pausado", "omitido", "archivado"]

ESTADOS_VALIDOS: set[str] = {"activo", "pausado", "omitido", "archivado"}
ESTADO_DEFAULT: EstadoExpediente = "activo"


class GestorEstadosExpedientes:
    """
    Gestiona los estados de monitoreo de expedientes.

    Almacena el estado de cada expediente en un archivo JSON:
    {
        "123456": "activo",
        "789012": "pausado",
        "345678": "omitido"
    }

    Estados:
        - activo: Expediente en monitoreo activo (default)
        - pausado: Monitoreo temporalmente suspendido
        - omitido: Excluido permanentemente del monitoreo
        - archivado: Expediente archivado, no requiere seguimiento

    Example:
        >>> gestor = GestorEstadosExpedientes(Path("data"))
        >>> await gestor.guardar_estado("123456", "activo")
        >>> estado = await gestor.obtener_estado("123456")
        >>> estado
        'activo'
        >>> activos = await gestor.obtener_activos()
        >>> "123456" in activos
        True
    """

    def __init__(self, data_dir: Path):
        """
        Inicializa el gestor de estados.

        Args:
            data_dir: Directorio donde se almacenará el archivo de estados
        """
        self.data_dir = Path(data_dir)
        self.archivo = self.data_dir / "estados_expedientes.json"
        self._asegurar_archivo()
        logger.info(f"GestorEstadosExpedientes inicializado: {self.archivo}")

    def _asegurar_archivo(self):
        """Crea el archivo de estados si no existe"""
        self.data_dir.mkdir(parents=True, exist_ok=True)

        if not self.archivo.exists():
            self.archivo.write_text("{}", encoding="utf-8")
            logger.info(f"Archivo de estados creado: {self.archivo}")

    async def cargar_estados(self) -> dict[str, str]:
        """
        Carga todos los estados desde el archivo.

        Returns:
            Diccionario {numero_expediente: estado}

        Example:
            >>> estados = await gestor.cargar_estados()
            >>> estados
            {'123456': 'activo', '789012': 'pausado'}
        """
        try:
            with open(self.archivo, encoding="utf-8") as f:
                estados = json.load(f)

            if not isinstance(estados, dict):
                logger.warning(f"Archivo de estados inválido, reiniciando")
                return {}

            logger.debug(f"Cargados {len(estados)} estados de expedientes")
            return estados

        except json.JSONDecodeError as e:
            logger.error(f"Error al decodificar JSON de estados: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error al cargar estados: {e}")
            return {}

    async def guardar_estado(self, numero: str, estado: str) -> None:
        """
        Guarda o actualiza el estado de un expediente.

        Args:
            numero: Número del expediente
            estado: Estado a asignar (activo, pausado, omitido, archivado)

        Raises:
            ValueError: Si el estado no es válido

        Example:
            >>> await gestor.guardar_estado("123456", "pausado")
        """
        if estado not in ESTADOS_VALIDOS:
            raise ValueError(
                f"Estado '{estado}' inválido. "
                f"Debe ser uno de: {', '.join(ESTADOS_VALIDOS)}"
            )

        estados = await self.cargar_estados()
        estados[numero] = estado

        try:
            with open(self.archivo, "w", encoding="utf-8") as f:
                json.dump(estados, f, indent=2, ensure_ascii=False)

            logger.info(f"Estado de expediente {numero} actualizado a: {estado}")

        except Exception as e:
            logger.error(f"Error al guardar estado: {e}")
            raise

    async def obtener_estado(self, numero: str) -> str:
        """
        Obtiene el estado de un expediente.

        Si el expediente no tiene estado asignado, retorna 'activo' (default).

        Args:
            numero: Número del expediente

        Returns:
            Estado del expediente

        Example:
            >>> estado = await gestor.obtener_estado("123456")
            >>> estado
            'activo'
        """
        estados = await self.cargar_estados()
        estado = estados.get(numero, ESTADO_DEFAULT)

        logger.debug(f"Estado de expediente {numero}: {estado}")
        return estado

    async def obtener_activos(self) -> list[str]:
        """
        Retorna números de todos los expedientes activos.

        Returns:
            Lista de números de expedientes con estado 'activo'

        Example:
            >>> activos = await gestor.obtener_activos()
            >>> activos
            ['123456', '234567', '345678']
        """
        estados = await self.cargar_estados()
        activos = [
            numero
            for numero, estado in estados.items()
            if estado == "activo"
        ]

        logger.info(f"Expedientes activos: {len(activos)}")
        return activos

    async def obtener_por_estado(self, estado: str) -> list[str]:
        """
        Retorna números de expedientes con un estado específico.

        Args:
            estado: Estado a filtrar (activo, pausado, omitido, archivado)

        Returns:
            Lista de números de expedientes con ese estado

        Raises:
            ValueError: Si el estado no es válido

        Example:
            >>> pausados = await gestor.obtener_por_estado("pausado")
            >>> pausados
            ['789012', '890123']
        """
        if estado not in ESTADOS_VALIDOS:
            raise ValueError(
                f"Estado '{estado}' inválido. "
                f"Debe ser uno de: {', '.join(ESTADOS_VALIDOS)}"
            )

        estados = await self.cargar_estados()
        expedientes = [
            numero
            for numero, est in estados.items()
            if est == estado
        ]

        logger.info(f"Expedientes con estado '{estado}': {len(expedientes)}")
        return expedientes

    async def remover_estado(self, numero: str) -> None:
        """
        Elimina el estado de un expediente (volverá a default 'activo').

        Args:
            numero: Número del expediente

        Example:
            >>> await gestor.remover_estado("123456")
        """
        estados = await self.cargar_estados()

        if numero in estados:
            del estados[numero]

            try:
                with open(self.archivo, "w", encoding="utf-8") as f:
                    json.dump(estados, f, indent=2, ensure_ascii=False)

                logger.info(f"Estado de expediente {numero} removido")

            except Exception as e:
                logger.error(f"Error al remover estado: {e}")
                raise
        else:
            logger.warning(f"Expediente {numero} no tiene estado asignado")

    async def obtener_estadisticas(self) -> dict[str, int]:
        """
        Retorna estadísticas de estados.

        Returns:
            Diccionario con contadores por estado

        Example:
            >>> stats = await gestor.obtener_estadisticas()
            >>> stats
            {
                'activo': 10,
                'pausado': 3,
                'omitido': 2,
                'archivado': 1,
                'total': 16
            }
        """
        estados = await self.cargar_estados()

        stats = {
            "activo": 0,
            "pausado": 0,
            "omitido": 0,
            "archivado": 0,
            "total": len(estados)
        }

        for estado in estados.values():
            if estado in stats:
                stats[estado] += 1

        logger.debug(f"Estadísticas de estados: {stats}")
        return stats

    async def actualizar_multiples(
        self,
        actualizaciones: dict[str, str]
    ) -> None:
        """
        Actualiza múltiples estados en una sola operación.

        Args:
            actualizaciones: Diccionario {numero: estado}

        Raises:
            ValueError: Si algún estado no es válido

        Example:
            >>> await gestor.actualizar_multiples({
            ...     "123456": "pausado",
            ...     "789012": "activo",
            ...     "345678": "omitido"
            ... })
        """
        # Validar todos los estados primero
        for numero, estado in actualizaciones.items():
            if estado not in ESTADOS_VALIDOS:
                raise ValueError(
                    f"Estado '{estado}' inválido para expediente {numero}. "
                    f"Debe ser uno de: {', '.join(ESTADOS_VALIDOS)}"
                )

        # Cargar estados actuales
        estados = await self.cargar_estados()

        # Aplicar actualizaciones
        estados.update(actualizaciones)

        # Guardar
        try:
            with open(self.archivo, "w", encoding="utf-8") as f:
                json.dump(estados, f, indent=2, ensure_ascii=False)

            logger.info(
                f"Actualizados {len(actualizaciones)} estados de expedientes"
            )

        except Exception as e:
            logger.error(f"Error al actualizar múltiples estados: {e}")
            raise
