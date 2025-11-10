"""Adapter de gestión de workspaces.

Implementa IWorkspacePort para crear y gestionar la estructura de directorios
de los expedientes.
"""

from __future__ import annotations

from pathlib import Path

from application.ports import IWorkspacePort
from core.domain.utils import normalizar_numero_expediente


class WorkspaceAdapter(IWorkspacePort):
    """Implementación de IWorkspacePort para gestión de workspaces.

    Este adapter crea y mantiene la estructura de directorios para cada
    expediente seleccionado.

    Estructura típica de un workspace:
    ```
    base_path/
    └── FPA-000632-2017/
        ├── actuaciones.json          # Lista de actuaciones
        ├── metadata.json              # Metadatos del expediente
        └── archivos/                  # Archivos adjuntos descargados
            ├── actuacion_001.pdf
            └── actuacion_002.pdf
    ```
    """

    async def crear_workspace(
        self,
        numero_expediente: str,
        base_path: Path,
    ) -> Path:
        """Crea la estructura de directorios para un expediente.

        Args:
            numero_expediente: Número del expediente
            base_path: Directorio base donde crear el workspace

        Returns:
            Path del workspace creado

        Raises:
            OSError: Si ocurre un error al crear los directorios
        """
        # Normalizar número de expediente para nombre de directorio seguro
        nombre_dir = normalizar_numero_expediente(numero_expediente)

        # Crear path del workspace
        workspace_path = base_path / nombre_dir

        # Crear directorio principal
        workspace_path.mkdir(parents=True, exist_ok=True)

        # Crear subdirectorio para archivos
        archivos_dir = workspace_path / "archivos"
        archivos_dir.mkdir(exist_ok=True)

        return workspace_path

    async def obtener_workspace(
        self,
        numero_expediente: str,
        base_path: Path,
    ) -> Path | None:
        """Obtiene el path del workspace de un expediente.

        Args:
            numero_expediente: Número del expediente
            base_path: Directorio base donde buscar

        Returns:
            Path del workspace o None si no existe
        """
        nombre_dir = normalizar_numero_expediente(numero_expediente)
        workspace_path = base_path / nombre_dir

        if workspace_path.exists() and workspace_path.is_dir():
            return workspace_path

        return None

    async def existe_workspace(
        self,
        numero_expediente: str,
        base_path: Path,
    ) -> bool:
        """Verifica si existe el workspace de un expediente.

        Args:
            numero_expediente: Número del expediente
            base_path: Directorio base donde buscar

        Returns:
            True si existe, False en caso contrario
        """
        workspace_path = await self.obtener_workspace(numero_expediente, base_path)
        return workspace_path is not None

    async def listar_workspaces(self, base_path: Path) -> list[str]:
        """Lista todos los workspaces existentes.

        Args:
            base_path: Directorio base donde buscar

        Returns:
            Lista de números de expediente con workspace.
            Los nombres de directorio se retornan tal como están
            (pueden tener guiones bajos en lugar de caracteres especiales).
        """
        if not base_path.exists() or not base_path.is_dir():
            return []

        # Listar todos los subdirectorios
        workspaces = []
        for item in base_path.iterdir():
            if item.is_dir():
                # Retornar el nombre del directorio
                # (corresponde al número de expediente normalizado)
                workspaces.append(item.name)

        return sorted(workspaces)
