"""Repositorio de actuaciones usando almacenamiento JSON.

Implementa IActuacionRepository usando archivos JSON como almacenamiento.
"""

from __future__ import annotations

import logging
from pathlib import Path

from application.ports import IActuacionRepository, IStoragePort
from core.domain.entities import Actuacion, ActuacionesArchivo

logger = logging.getLogger(__name__)


class JsonActuacionRepository(IActuacionRepository):
    """Implementación de IActuacionRepository usando archivos JSON.

    Este repositorio almacena las actuaciones de cada expediente en archivos
    JSON separados dentro de los workspaces.

    El path típico es:
    base_path/workspaces/{numero_expediente}/actuaciones.json

    Attributes:
        storage: Adapter de almacenamiento para operaciones de archivo
        workspaces_base: Path base de los workspaces
    """

    def __init__(
        self,
        storage: IStoragePort,
        workspaces_base: Path,
    ):
        """Inicializa el repositorio.

        Args:
            storage: Adapter de almacenamiento
            workspaces_base: Path base de los workspaces
        """
        self._storage = storage
        self._workspaces_base = workspaces_base

    def _get_archivo_path(self, numero_expediente: str) -> Path:
        """Obtiene el path del archivo de actuaciones para un expediente.

        Args:
            numero_expediente: Número del expediente

        Returns:
            Path del archivo actuaciones.json
        """
        from core.domain.utils import normalizar_numero_expediente

        nombre_normalizado = normalizar_numero_expediente(numero_expediente)
        # Los directorios usan guiones bajos, no guiones
        nombre_busqueda = nombre_normalizado.replace('-', '_')

        logger.info(f"Buscando actuaciones para: '{numero_expediente}' -> normalizado: '{nombre_busqueda}'")
        logger.info(f"Workspaces base: {self._workspaces_base} (existe: {self._workspaces_base.exists()})")

        # Buscar el directorio que contenga el número normalizado
        # Los directorios tienen formato: {numero}_{nombre_normalizado}
        if self._workspaces_base.exists():
            # Usar glob para búsqueda más flexible
            pattern = f"*{nombre_busqueda}*"
            for dir_path in self._workspaces_base.glob(pattern):
                if dir_path.is_dir():
                    logger.info(f"Directorio encontrado: {dir_path.name}")
                    # Intentar encontrar el archivo de actuaciones
                    # Formato: {dir}/json/actuaciones-{nombre}.json
                    json_dir = dir_path / "json"
                    if json_dir.exists():
                        # Buscar cualquier archivo que comience con "actuaciones-"
                        for archivo in json_dir.glob("actuaciones-*.json"):
                            logger.info(f"Archivo JSON encontrado: {archivo}")
                            return archivo
                        logger.warning(f"Directorio json existe pero no hay archivos actuaciones-*.json en {json_dir}")
                    else:
                        logger.warning(f"No existe directorio json en {dir_path}")
        else:
            logger.error(f"El directorio workspaces_base no existe: {self._workspaces_base}")

        # Fallback al path original si no se encuentra
        fallback = self._workspaces_base / nombre_normalizado / "json" / f"actuaciones-{nombre_normalizado}.json"
        logger.warning(f"No se encontró archivo, usando fallback: {fallback}")
        return fallback

    async def guardar_archivo(
        self, numero_expediente: str, archivo: ActuacionesArchivo
    ) -> None:
        """Guarda un archivo completo de actuaciones para un expediente."""
        archivo_path = self._get_archivo_path(numero_expediente)

        # Asegurar que el directorio existe
        await self._storage.crear_directorio(archivo_path.parent)

        # Guardar archivo
        datos = archivo.to_dict()
        await self._storage.guardar_json(datos, archivo_path)
        logger.debug(
            f"Actuaciones guardadas para {numero_expediente}: "
            f"{len(archivo.actuaciones)} actuaciones"
        )

    async def obtener_archivo(
        self, numero_expediente: str
    ) -> ActuacionesArchivo | None:
        """Obtiene el archivo de actuaciones de un expediente."""
        archivo_path = self._get_archivo_path(numero_expediente)

        if not await self._storage.existe_archivo(archivo_path):
            return None

        try:
            datos = await self._storage.leer_json(archivo_path)

            # Extraer encabezado y actuaciones
            if isinstance(datos, dict):
                encabezado = datos.get("expediente", datos.get("Expediente", {}))
                lista_actuaciones = datos.get("actuaciones", datos.get("Actuaciones", []))
            else:
                logger.warning(
                    f"Formato inesperado en {archivo_path}: esperaba dict, obtuvo {type(datos)}"
                )
                return None

            # Convertir actuaciones
            actuaciones = tuple(
                Actuacion.from_dict(act_data) for act_data in lista_actuaciones
            )

            return ActuacionesArchivo(
                encabezado=encabezado,
                actuaciones=actuaciones,
            )

        except Exception as e:
            logger.error(f"Error al leer actuaciones de {numero_expediente}: {e}")
            return None

    async def obtener_actuaciones(
        self, numero_expediente: str
    ) -> tuple[Actuacion, ...] | None:
        """Obtiene solo las actuaciones de un expediente (sin encabezado)."""
        archivo = await self.obtener_archivo(numero_expediente)
        if archivo:
            return archivo.actuaciones
        return None

    async def obtener_por_indice(
        self, numero_expediente: str, indice: int
    ) -> Actuacion | None:
        """Obtiene una actuación específica por índice."""
        actuaciones = await self.obtener_actuaciones(numero_expediente)
        if not actuaciones:
            return None

        # Buscar actuación con el índice especificado
        for act in actuaciones:
            if act.indice == indice:
                return act

        return None

    async def obtener_con_archivo(
        self, numero_expediente: str
    ) -> tuple[Actuacion, ...]:
        """Obtiene actuaciones que tienen archivo adjunto."""
        actuaciones = await self.obtener_actuaciones(numero_expediente)
        if not actuaciones:
            return ()

        return tuple(act for act in actuaciones if act.tiene_archivo)

    async def existe(self, numero_expediente: str) -> bool:
        """Verifica si existen actuaciones para un expediente."""
        archivo_path = self._get_archivo_path(numero_expediente)
        return await self._storage.existe_archivo(archivo_path)
