"""Gestión de la estructura de directorios de expedientes.

El módulo expone una estructura por defecto y utilidades para
materializarla en disco. Se integra con :class:`~Sistema_v5.configuracion.core.system_config.SystemConfig`
para respetar los directorios configurados del sistema PJN y ofrece
helpers para generar árboles por expediente.
"""

from __future__ import annotations

import os
import json
import tempfile
from copy import deepcopy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TYPE_CHECKING

try:  # Compatibilidad con imports absolutos y relativos
    from ..pjn.scraping.base import normalizar_numero_expediente
except ImportError:  # pragma: no cover - fallback cuando se ejecuta fuera del paquete
    from Sistema_v5.pjn.scraping.base import normalizar_numero_expediente  # type: ignore

if TYPE_CHECKING:  # pragma: no cover - solo para hints
    from ..configuracion.core.system_config import SystemConfig


ESTRUCTURA_POR_DEFECTO: dict[str, dict[str, object] | None] = {
    "actuaciones": {
        "json": None,
        "adjuntos": None,
    },
    "documentos_usuario": None,
    "reportes": None,
}


def _fusionar_estructuras(
    base: dict[str, object] | None,
    extra: dict[str, object] | None,
) -> dict[str, object] | None:
    """Devuelve una nueva estructura combinando ``base`` y ``extra``.

    Si ``extra`` es ``None`` se devuelve una copia profunda de ``base``. Cuando
    ambos diccionarios comparten claves y sus valores son a su vez diccionarios,
    la fusión se realiza recursivamente, permitiendo añadir o sobreescribir
    subniveles concretos.
    """

    if extra is None:
        return deepcopy(base) if base is not None else None

    if base is None:
        return deepcopy(extra)

    combinada: dict[str, object] = deepcopy(base)
    for nombre, valor_extra in extra.items():
        valor_base = combinada.get(nombre)
        if isinstance(valor_base, dict) and isinstance(valor_extra, dict):
            combinada[nombre] = _fusionar_estructuras(valor_base, valor_extra) or {}
        else:
            combinada[nombre] = deepcopy(valor_extra)
    return combinada


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
            from ..configuracion.core.system_config import SystemConfig as _SystemConfig

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

        expanded = os.path.expandvars(str(ruta))
        path = Path(expanded).expanduser()
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
        estructura: dict[str, object] | None = None,
        fusionar_estructura: bool = True,
    ) -> dict[str, Any]:
        """Genera la estructura de directorios y devuelve un manifiesto.

        Args:
            destino: Carpeta donde crear la estructura. Si se omite se utiliza
                ``self.raiz``.
            metadata: Campos adicionales a incluir en ``manifest.json``.
            estructura: Estructura personalizada a aplicar en lugar de la
                almacenada en ``self.estructura``.
            fusionar_estructura: Cuando ``True`` (por defecto) la estructura
                personalizada se fusiona con la existente, permitiendo añadir
                o modificar secciones puntuales. Si es ``False`` la estructura
                proporcionada reemplaza completamente a la actual para esta
                invocación.
        """

        raiz = Path(destino) if destino is not None else self.raiz
        raiz.mkdir(parents=True, exist_ok=True)

        directories: list[str] = []
        estructura_a_usar = self._obtener_estructura_efectiva(
            estructura, fusionar_estructura
        )
        self._crear_estructura(raiz, estructura_a_usar, directories, raiz)

        manifest: dict[str, Any] = {"directories": sorted(directories)}
        if metadata is not None:
            manifest["metadata"] = deepcopy(metadata)

        manifest_path = raiz / self.manifest_filename
        contenido_manifest = json.dumps(manifest, indent=2, ensure_ascii=False)
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=manifest_path.parent,
                delete=False,
            ) as tmp_file:
                temp_path = Path(tmp_file.name)
                tmp_file.write(contenido_manifest)
            os.replace(temp_path, manifest_path)
        except Exception:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except Exception:
                    pass
            raise
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

    def actualizar_estructura(
        self,
        estructura_personalizada: dict[str, object],
        *,
        reemplazar: bool = False,
    ) -> None:
        """Actualiza la estructura interna del gestor.

        Args:
            estructura_personalizada: Árbol de directorios a incorporar.
            reemplazar: Cuando es ``True`` sustituye completamente la
                estructura actual. Si es ``False`` (por defecto) se fusiona con
                la estructura existente, lo que permite añadir carpetas nuevas o
                redefinir sólo algunas ramas.
        """

        if reemplazar:
            self.estructura = deepcopy(estructura_personalizada)
        else:
            self.estructura = _fusionar_estructuras(
                self.estructura, estructura_personalizada
            ) or {}

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
            componente = Path(nombre)

            if componente.is_absolute():
                raise ValueError(
                    f"No se permiten componentes absolutos en la estructura: '{nombre}'"
                )

            partes = componente.parts
            if any(parte == ".." for parte in partes):
                raise ValueError(
                    f"No se permite el uso de '..' en la estructura: '{nombre}'"
                )

            if len(partes) != 1:
                raise ValueError(
                    "Los componentes de la estructura deben ser simples, "
                    f"se recibió: '{nombre}'"
                )

            nombre_normalizado = partes[0]

            ruta = base / nombre_normalizado
            ruta.mkdir(parents=True, exist_ok=True)
            manifest.append(str(ruta.relative_to(raiz_manifest).as_posix()))

            if isinstance(subestructura, dict):
                self._crear_estructura(ruta, subestructura, manifest, raiz_manifest)

    def _obtener_estructura_efectiva(
        self,
        estructura_personalizada: dict[str, object] | None,
        fusionar: bool,
    ) -> dict[str, object] | None:
        """Determina la estructura a utilizar en una generación concreta."""

        if estructura_personalizada is None:
            return deepcopy(self.estructura)

        if fusionar:
            return _fusionar_estructuras(self.estructura, estructura_personalizada)

        return deepcopy(estructura_personalizada)


__all__ = [
    "ESTRUCTURA_POR_DEFECTO",
    "GestorDirectoriosExpedientes",
]
