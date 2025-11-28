"""Repositorio de expedientes usando almacenamiento JSON.

Implementa IExpedienteRepository usando archivos JSON como almacenamiento.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Sequence

from application.ports import IExpedienteRepository, IStoragePort
from core.domain.entities import ExpedienteResumen
from core.domain.expediente_utils import normalizar_numero_expediente

logger = logging.getLogger(__name__)


class JsonExpedienteRepository(IExpedienteRepository):
    """Implementación de IExpedienteRepository usando archivos JSON.

    Este repositorio mantiene los expedientes en memoria y los persiste
    en un archivo JSON. Es adecuado para cantidades moderadas de expedientes
    (hasta varios miles).

    Attributes:
        storage: Adapter de almacenamiento para operaciones de archivo
        archivo_json: Path del archivo JSON donde persistir los datos
        _expedientes: Diccionario en memoria {numero: ExpedienteResumen}
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
        self._expedientes: dict[str, ExpedienteResumen] = {}
        self._cargado = False

    async def _cargar(self, forzar: bool = False) -> None:
        """Carga expedientes desde el archivo JSON si existe.

        Args:
            forzar: Si True, recarga los datos incluso si ya están cargados
        """
        if self._cargado and not forzar:
            return

        # Limpiar expedientes existentes si estamos recargando
        if forzar:
            self._expedientes.clear()

        if await self._storage.existe_archivo(self._archivo_json):
            logger.debug(f"Cargando expedientes desde {self._archivo_json}")
            try:
                datos = await self._storage.leer_json(self._archivo_json)

                # Convertir a lista si es dict
                if isinstance(datos, dict):
                    lista_datos = datos.get("expedientes", [])
                else:
                    lista_datos = datos

                # Cargar expedientes
                for data in lista_datos:
                    exp = ExpedienteResumen.from_dict(data)
                    self._expedientes[exp.numero] = exp

                logger.info(f"Cargados {len(self._expedientes)} expedientes")
            except Exception as e:
                logger.error(f"Error al cargar expedientes: {e}")

        self._cargado = True

    async def recargar(self) -> None:
        """Recarga los expedientes desde el archivo JSON, invalidando la caché."""
        logger.info("Recargando expedientes desde archivo")
        await self._cargar(forzar=True)

    async def _persistir(self) -> None:
        """Persiste los expedientes en el archivo JSON."""
        try:
            datos = [exp.to_dict() for exp in self._expedientes.values()]
            await self._storage.guardar_json(datos, self._archivo_json)
            logger.debug(f"Expedientes persistidos en {self._archivo_json}")
        except Exception as e:
            logger.error(f"Error al persistir expedientes: {e}")
            raise

    async def guardar(self, expediente: ExpedienteResumen) -> None:
        """Guarda un expediente en el repositorio."""
        await self._cargar()
        self._expedientes[expediente.numero] = expediente
        await self._persistir()

    async def save(self, expediente: ExpedienteResumen) -> None:
        """Alias de guardar() para compatibilidad."""
        await self.guardar(expediente)

    async def guardar_varios(self, expedientes: Sequence[ExpedienteResumen]) -> None:
        """Guarda múltiples expedientes en el repositorio."""
        await self._cargar()
        for exp in expedientes:
            self._expedientes[exp.numero] = exp
        await self._persistir()

    async def obtener_por_numero(self, numero: str) -> ExpedienteResumen | None:
        """Obtiene un expediente por su número."""
        await self._cargar()
        numero_normalizado = normalizar_numero_expediente(numero)
        return self._expedientes.get(numero_normalizado)

    async def obtener_todos(self) -> list[ExpedienteResumen]:
        """Obtiene todos los expedientes del repositorio."""
        await self._cargar()
        return list(self._expedientes.values())

    async def obtener_por_estado(self, estado: str) -> list[ExpedienteResumen]:
        """Obtiene expedientes filtrados por estado (no soportado en JSON, devuelve todos)."""
        logger.warning("Filtrado por estado no soportado en JsonExpedienteRepository, devolviendo todos")
        return await self.obtener_todos()

    async def obtener_activos(self, dias: int = 30) -> list[ExpedienteResumen]:
        """Obtiene expedientes con movimientos recientes."""
        await self._cargar()
        return [exp for exp in self._expedientes.values() if exp.esta_activo(dias)]

    async def filtrar_por_dependencia(self, dependencia: str) -> list[ExpedienteResumen]:
        """Filtra expedientes por dependencia."""
        await self._cargar()
        dependencia_lower = dependencia.lower()
        return [
            exp
            for exp in self._expedientes.values()
            if dependencia_lower in exp.dependencia.lower()
        ]

    async def existe(self, numero: str) -> bool:
        """Verifica si existe un expediente con el número dado."""
        await self._cargar()
        numero_normalizado = normalizar_numero_expediente(numero)
        return numero_normalizado in self._expedientes

    async def eliminar(self, numero: str) -> bool:
        """Elimina un expediente del repositorio."""
        await self._cargar()
        if numero in self._expedientes:
            del self._expedientes[numero]
            await self._persistir()
            return True
        return False

    async def contar(self) -> int:
        """Cuenta el total de expedientes en el repositorio."""
        await self._cargar()
        return len(self._expedientes)
