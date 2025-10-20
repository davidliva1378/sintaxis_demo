"""Gestión de la estructura de directorios de expedientes.

El módulo expone una estructura por defecto y utilidades para
materializarla en disco. Se integra con :class:`~Sistema_v5.configuracion.core.system_config.SystemConfig`
para respetar los directorios configurados del sistema PJN y ofrece
helpers para generar árboles por expediente.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TYPE_CHECKING

try:  # Compatibilidad con imports absolutos y relativos
    from .pjn.scraping.base import normalizar_numero_expediente
except ImportError:  # pragma: no cover - fallback cuando se ejecuta fuera del paquete
    from Sistema_v5.pjn.scraping.base import normalizar_numero_expediente  # type: ignore

if TYPE_CHECKING:  # pragma: no cover - solo para hints
    from .configuracion.core.system_config import SystemConfig


ESTRUCTURA_POR_DEFECTO: dict[str, dict[str, object] | None] = {
    "actuaciones": {
        "json": None,
        "adjuntos": None,
        "documentos_usuario": None,
    },
    "expedientes": {
        "json": None,
        "reportes": None,
    },
    "entradas": {
        "json": None,
    },
}


@dataclass
class GestorDirectoriosExpedientes:
    """Crea y mantiene la estructura de directorios de expedientes.

    El gestor parte de una carpeta ``raiz`` (por ejemplo ``data/expedientes``)
    y genera dentro de ella un árbol de subdirectorios consistente con la
    convención del sistema.
    """

    raiz: Path
    estructura: dict[str, object] = field(default_factory=lambda: deepcopy(ESTRUCTURA_POR_DEFECTO))
    manifest_filename: str = "manifest.json"

    @classmethod
    def desde_config(
        cls,
        config: "SystemConfig | None" = None,
        *,
        base_dir: Path | str | None = None,
        config_path: Path | str = "config/sistema.json",
    ) -> "GestorDirectoriosExpedientes":
        """Crea un gestor usando la configuración del sistema.

        Args:
            config: Instancia ya cargada de :class:`SystemConfig`. Si no se
                proporciona se lee del archivo indicado por ``config_path``.
            base_dir: Carpeta base desde la que se resolverán rutas relativas
                configuradas (por ejemplo la raíz del proyecto).
            config_path: Ruta al archivo de configuración unificada.
        """

        if config is None:
            from .configuracion.core.system_config import SystemConfig as _SystemConfig

            config = _SystemConfig.from_file(config_path)

        raiz = cls._resolver_ruta(config.directorio_expedientes_base, base_dir, config_path)
        return cls(raiz=raiz)

    @staticmethod
    def _resolver_ruta(
        ruta: str | Path,
        base_dir: Path | str | None,
        config_path: Path | str | None,
    ) -> Path:
        """Resuelve rutas relativas usando un directorio base apropiado."""

        path = Path(ruta)
        if path.is_absolute():
            return path

        if base_dir is not None:
            base = Path(base_dir)
        elif config_path is not None:
            resolved = Path(config_path).resolve()
            config_dir = resolved.parent
            base = config_dir.parent if config_dir.name == "config" else config_dir
        else:
            base = Path.cwd()

        return base / path

    def generar_arbol(
        self,
        destino: Path | str | None = None,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Genera la estructura de directorios y devuelve un manifiesto.

        Args:
            destino: Carpeta donde crear la estructura. Si se omite se utiliza
                ``self.raiz``.
            metadata: Campos adicionales a incluir en ``manifest.json``.
        """

        raiz = Path(destino) if destino is not None else self.raiz
        raiz.mkdir(parents=True, exist_ok=True)

        directories: list[str] = []
        self._crear_estructura(raiz, self.estructura, directories, raiz)

        manifest: dict[str, Any] = {"directories": sorted(directories)}
        if metadata:
            manifest.update(metadata)

        manifest_path = raiz / self.manifest_filename
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return manifest

    def crear_para_expediente(self, numero_expediente: str) -> tuple[Path, dict[str, Any]]:
        """Genera el árbol estándar para un expediente específico."""

        numero_normalizado = normalizar_numero_expediente(numero_expediente)
        destino = self.raiz / numero_normalizado

        metadata = {
            "numero_expediente": numero_expediente,
            "numero_normalizado": numero_normalizado,
        }

        manifest = self.generar_arbol(destino, metadata=metadata)
        return destino, manifest

    def _crear_estructura(
        self,
        base: Path,
        estructura: dict[str, object] | None,
        manifest: list[str],
        raiz_manifest: Path,
    ) -> None:
        """Crea recursivamente la estructura indicada."""

        if not estructura:
            return

        for nombre, subestructura in estructura.items():
            ruta = base / nombre
            ruta.mkdir(parents=True, exist_ok=True)
            manifest.append(str(ruta.relative_to(raiz_manifest).as_posix()))

            if isinstance(subestructura, dict):
                self._crear_estructura(ruta, subestructura, manifest, raiz_manifest)


__all__ = [
    "ESTRUCTURA_POR_DEFECTO",
    "GestorDirectoriosExpedientes",
]
