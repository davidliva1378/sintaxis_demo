"""Gestión de la estructura de directorios de expedientes.

El módulo expone una estructura por defecto y utilidades para
materializarla en disco. Se utiliza principalmente durante pruebas y
scripts que necesitan garantizar que el árbol base exista antes de
comenzar a procesar archivos asociados a expedientes.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
import json


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
    """Crea y mantiene la estructura de directorios de un expediente."""

    raiz: Path
    estructura: dict[str, object] = field(default_factory=lambda: deepcopy(ESTRUCTURA_POR_DEFECTO))

    def generar_arbol(self) -> dict[str, list[str]]:
        """Genera la estructura de directorios y devuelve un manifiesto."""

        self.raiz.mkdir(parents=True, exist_ok=True)
        manifest: dict[str, list[str]] = {"directories": []}
        self._crear_estructura(self.raiz, self.estructura, manifest["directories"])

        manifest_path = self.raiz / "manifest.json"
        manifest["directories"].sort()
        manifest_path.write_text(
            json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        return manifest

    def _crear_estructura(
        self,
        base: Path,
        estructura: dict[str, object] | None,
        manifest: list[str],
    ) -> None:
        """Crea recursivamente la estructura indicada."""

        if not estructura:
            return

        for nombre, subestructura in estructura.items():
            ruta = base / nombre
            ruta.mkdir(parents=True, exist_ok=True)
            manifest.append(str(ruta.relative_to(self.raiz).as_posix()))

            if isinstance(subestructura, dict):
                self._crear_estructura(ruta, subestructura, manifest)


__all__ = [
    "ESTRUCTURA_POR_DEFECTO",
    "GestorDirectoriosExpedientes",
]
