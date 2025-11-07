"""Repositorio de entradas usando almacenamiento JSON.

Implementa IEntradaRepository usando archivos JSON como almacenamiento.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

from application.ports import IEntradaRepository, IStoragePort
from core.domain.entities import Entrada

logger = logging.getLogger(__name__)


class JsonEntradaRepository(IEntradaRepository):
    """Implementación de IEntradaRepository usando archivos JSON.

    Este repositorio mantiene las entradas en memoria y las persiste
    en un archivo JSON.

    Attributes:
        storage: Adapter de almacenamiento para operaciones de archivo
        archivo_json: Path del archivo JSON donde persistir los datos
        _entradas: Lista de entradas en memoria
    """

    def __init__(
        self,
        storage: IStoragePort,
        archivo_json: Path,
    ):
        """Inicializa el repositorio.

        Args:
            storage: Adapter de almacenamiento
            archivo_json: Path del archivo JSON
        """
        self._storage = storage
        self._archivo_json = archivo_json
        self._entradas: list[Entrada] = []
        self._cargado = False

    async def _cargar(self) -> None:
        """Carga entradas desde el archivo JSON si existe."""
        if self._cargado:
            return

        if await self._storage.existe_archivo(self._archivo_json):
            logger.debug(f"Cargando entradas desde {self._archivo_json}")
            try:
                datos = await self._storage.leer_json(self._archivo_json)

                # Convertir a lista si es dict
                if isinstance(datos, dict):
                    lista_datos = datos.get("entradas", [])
                else:
                    lista_datos = datos

                # Cargar entradas
                self._entradas = [Entrada.from_dict(data) for data in lista_datos]

                logger.info(f"Cargadas {len(self._entradas)} entradas")
            except Exception as e:
                logger.error(f"Error al cargar entradas: {e}")

        self._cargado = True

    async def _persistir(self) -> None:
        """Persiste las entradas en el archivo JSON."""
        try:
            datos = [entrada.to_dict() for entrada in self._entradas]
            await self._storage.guardar_json(datos, self._archivo_json)
            logger.debug(f"Entradas persistidas en {self._archivo_json}")
        except Exception as e:
            logger.error(f"Error al persistir entradas: {e}")
            raise

    async def guardar(self, entrada: Entrada) -> None:
        """Guarda una entrada en el repositorio."""
        await self._cargar()

        # Verificar si ya existe (por número, fecha y evento)
        existe = any(e == entrada for e in self._entradas)

        if not existe:
            self._entradas.append(entrada)
            await self._persistir()

    async def guardar_varias(self, entradas: Sequence[Entrada]) -> None:
        """Guarda múltiples entradas en el repositorio."""
        await self._cargar()

        # Añadir solo las que no existen
        entradas_existentes = set(self._entradas)
        nuevas_entradas = [e for e in entradas if e not in entradas_existentes]

        if nuevas_entradas:
            self._entradas.extend(nuevas_entradas)
            await self._persistir()

    async def obtener_todas(self) -> list[Entrada]:
        """Obtiene todas las entradas del repositorio."""
        await self._cargar()
        return list(self._entradas)

    async def obtener_por_expediente(self, numero: str) -> list[Entrada]:
        """Obtiene todas las entradas de un expediente específico."""
        await self._cargar()
        return [e for e in self._entradas if e.numero == numero]

    async def obtener_no_leidas(self) -> list[Entrada]:
        """Obtiene entradas que no han sido marcadas como leídas."""
        await self._cargar()
        return [e for e in self._entradas if not e.leida]

    async def marcar_como_leida(self, entrada: Entrada) -> None:
        """Marca una entrada como leída."""
        await self._cargar()

        # Buscar y reemplazar la entrada
        for i, e in enumerate(self._entradas):
            if e == entrada:
                # Marcar como leída (crea nueva instancia por inmutabilidad)
                self._entradas[i] = entrada.marcar_como_leida()
                await self._persistir()
                return

    async def contar(self) -> int:
        """Cuenta el total de entradas en el repositorio."""
        await self._cargar()
        return len(self._entradas)

    async def contar_no_leidas(self) -> int:
        """Cuenta el total de entradas no leídas."""
        await self._cargar()
        return sum(1 for e in self._entradas if not e.leida)
