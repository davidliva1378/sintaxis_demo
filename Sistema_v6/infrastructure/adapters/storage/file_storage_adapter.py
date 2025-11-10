"""Adapter de almacenamiento en sistema de archivos.

Implementa IStoragePort para operaciones de lectura/escritura de archivos.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Mapping, Sequence

from application.ports import IStoragePort


class FileStorageAdapter(IStoragePort):
    """Implementación de IStoragePort usando sistema de archivos.

    Este adapter maneja operaciones de archivos JSON y sistema de archivos
    local.

    Attributes:
        pretty_json: Si True, formatea el JSON con indentación
        ensure_ascii: Si True, escapa caracteres no-ASCII en JSON
    """

    def __init__(
        self,
        *,
        pretty_json: bool = True,
        ensure_ascii: bool = False,
    ):
        """Inicializa el adapter.

        Args:
            pretty_json: Si True, formatea el JSON con indentación
            ensure_ascii: Si True, escapa caracteres no-ASCII en JSON
        """
        self._pretty_json = pretty_json
        self._ensure_ascii = ensure_ascii

    async def guardar_json(
        self,
        datos: Mapping[str, Any] | Sequence[Mapping[str, Any]],
        archivo: Path,
    ) -> None:
        """Guarda datos en formato JSON.

        Args:
            datos: Datos a guardar (dict o lista de dicts)
            archivo: Ruta del archivo JSON

        Raises:
            OSError: Si ocurre un error al guardar
        """
        # Asegurar que el directorio existe
        archivo.parent.mkdir(parents=True, exist_ok=True)

        # Configurar indentación
        indent = 2 if self._pretty_json else None

        # Guardar JSON
        with archivo.open("w", encoding="utf-8") as f:
            json.dump(
                datos,
                f,
                indent=indent,
                ensure_ascii=self._ensure_ascii,
            )

    async def leer_json(self, archivo: Path) -> Mapping[str, Any] | list[Any]:
        """Lee datos desde un archivo JSON.

        Args:
            archivo: Ruta del archivo JSON

        Returns:
            Datos leídos (dict o lista)

        Raises:
            FileNotFoundError: Si el archivo no existe
            json.JSONDecodeError: Si el archivo no es JSON válido
        """
        if not archivo.exists():
            raise FileNotFoundError(f"Archivo no encontrado: {archivo}")

        with archivo.open("r", encoding="utf-8") as f:
            return json.load(f)

    async def existe_archivo(self, archivo: Path) -> bool:
        """Verifica si existe un archivo.

        Args:
            archivo: Ruta del archivo

        Returns:
            True si existe, False en caso contrario
        """
        return archivo.exists() and archivo.is_file()

    async def crear_directorio(self, directorio: Path) -> None:
        """Crea un directorio (y sus padres si no existen).

        Args:
            directorio: Ruta del directorio a crear

        Raises:
            OSError: Si ocurre un error al crear
        """
        directorio.mkdir(parents=True, exist_ok=True)

    async def listar_archivos(
        self, directorio: Path, patron: str = "*"
    ) -> list[Path]:
        """Lista archivos en un directorio que coinciden con un patrón.

        Args:
            directorio: Ruta del directorio
            patron: Patrón glob (default: "*" para todos)

        Returns:
            Lista de rutas de archivos encontrados

        Raises:
            FileNotFoundError: Si el directorio no existe
        """
        if not directorio.exists():
            raise FileNotFoundError(f"Directorio no encontrado: {directorio}")

        if not directorio.is_dir():
            raise NotADirectoryError(f"No es un directorio: {directorio}")

        # Listar archivos que coinciden con el patrón
        return sorted([p for p in directorio.glob(patron) if p.is_file()])

    async def copiar_archivo(self, origen: Path, destino: Path) -> None:
        """Copia un archivo de origen a destino.

        Args:
            origen: Ruta del archivo origen
            destino: Ruta del archivo destino

        Raises:
            FileNotFoundError: Si el archivo origen no existe
            OSError: Si ocurre un error al copiar
        """
        if not origen.exists():
            raise FileNotFoundError(f"Archivo origen no encontrado: {origen}")

        # Asegurar que el directorio destino existe
        destino.parent.mkdir(parents=True, exist_ok=True)

        # Copiar archivo
        shutil.copy2(origen, destino)

    async def mover_archivo(self, origen: Path, destino: Path) -> None:
        """Mueve un archivo de origen a destino.

        Args:
            origen: Ruta del archivo origen
            destino: Ruta del archivo destino

        Raises:
            FileNotFoundError: Si el archivo origen no existe
            OSError: Si ocurre un error al mover
        """
        if not origen.exists():
            raise FileNotFoundError(f"Archivo origen no encontrado: {origen}")

        # Asegurar que el directorio destino existe
        destino.parent.mkdir(parents=True, exist_ok=True)

        # Mover archivo
        shutil.move(str(origen), str(destino))
