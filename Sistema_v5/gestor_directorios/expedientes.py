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
from collections.abc import Iterable
from typing import Any, TYPE_CHECKING

try:  # Compatibilidad con imports absolutos y relativos
    from ..pjn.scraping.base import normalizar_numero_expediente
except ImportError:  # pragma: no cover - fallback cuando se ejecuta fuera del paquete
    from Sistema_v5.pjn.scraping.base import normalizar_numero_expediente  # type: ignore

if TYPE_CHECKING:  # pragma: no cover - solo para hints
    from ..configuracion.core.system_config import SystemConfig


ESTRUCTURA_POR_DEFECTO: dict[str, dict[str, object] | None] = {
    "actuaciones": {
        "adjuntos": None,
    },
    "json": None,
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
    index_filename: str = "expedientes_index.json"

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
        self._persistir_manifest(manifest_path, manifest)
        return manifest

    def actualizar_expediente(
        self,
        numero_expediente: str,
        metadata_nueva: dict[str, Any],
        estructura: dict[str, object] | None = None,
    ) -> dict[str, Any]:
        """Actualiza el manifiesto y estructura de un expediente existente."""

        numero_normalizado = normalizar_numero_expediente(numero_expediente)
        identificador = self._obtener_o_registrar_identificador(numero_normalizado)
        destino_preferido = self._obtener_ruta_expediente(
            numero_normalizado, identificador
        )
        legado = self.raiz / numero_normalizado
        if destino_preferido.exists():
            destino = destino_preferido
        elif legado.exists() and legado.is_dir():
            destino = legado
        else:
            destino_preferido.mkdir(parents=True, exist_ok=True)
            destino = destino_preferido

        manifest_path = destino / self.manifest_filename
        manifest_existente: dict[str, Any] = {}

        if manifest_path.exists():
            try:
                manifest_existente = json.loads(
                    manifest_path.read_text(encoding="utf-8")
                )
            except json.JSONDecodeError:
                manifest_existente = {}

        directories_previos = set(manifest_existente.get("directories", []))
        directories_actuales: list[str] = []

        estructura_a_usar = self._obtener_estructura_efectiva(estructura, True)
        self._crear_estructura(destino, estructura_a_usar, directories_actuales, destino)

        directories_combinados = sorted(directories_previos | set(directories_actuales))

        metadata_previos = {}
        if isinstance(manifest_existente.get("metadata"), dict):
            metadata_previos = deepcopy(manifest_existente["metadata"])

        metadata_final = deepcopy(metadata_previos)
        metadata_final.update(metadata_nueva)
        metadata_final["id"] = identificador

        manifest_final: dict[str, Any] = {"directories": directories_combinados}
        if metadata_final:
            manifest_final["metadata"] = metadata_final

        self._persistir_manifest(manifest_path, manifest_final)
        return manifest_final

    def crear_para_expediente(self, numero_expediente: str) -> tuple[Path, dict[str, Any]]:
        """Genera el árbol estándar para un expediente específico."""

        numero_normalizado = normalizar_numero_expediente(numero_expediente)
        identificador = self._obtener_o_registrar_identificador(numero_normalizado)
        destino = self._obtener_ruta_expediente(numero_normalizado, identificador)

        metadata = {
            "numero_expediente": numero_expediente,
            "numero_normalizado": numero_normalizado,
            "id": identificador,
        }

        manifest = self.generar_arbol(destino, metadata=metadata)
        return destino, manifest

    def crear_desde_json(
        self, expedientes: Iterable[dict[str, Any]]
    ) -> list[tuple[Path, dict[str, Any]]]:
        """Crea múltiples expedientes a partir de una estructura JSON.

        Cada elemento del iterable debe ser un diccionario con la clave
        obligatoria ``"numero_expediente"`` (cadena). Opcionalmente puede
        incluir ``"metadata"`` (diccionario con información adicional que se
        fusionará con la metadata estándar), ``"estructura"`` (diccionario con
        una estructura personalizada a aplicar) y ``"fusionar_estructura"``
        (bandera booleana propagada a :meth:`generar_arbol`). Cualquier otra
        clave se ignora.

        Returns:
            list[tuple[Path, dict[str, Any]]]: Tuplas con la ruta creada y el
            manifiesto retornado por :meth:`generar_arbol` para cada expediente
            procesado correctamente.

        Raises:
            ValueError: Si alguna entrada no puede procesarse. El mensaje del
            error detalla los expedientes afectados y la causa. Es posible que
            algunos expedientes se hayan creado antes de que se acumule el
            error.
        """

        resultados: list[tuple[Path, dict[str, Any]]] = []
        errores: dict[str, str] = {}
        vistos: set[str] = set()

        for indice, entrada in enumerate(expedientes):
            numero_expediente = entrada.get("numero_expediente")
            if not isinstance(numero_expediente, str) or not numero_expediente.strip():
                errores[f"entrada_{indice}"] = (
                    "Falta la clave obligatoria 'numero_expediente'"
                )
                continue

            numero_normalizado = normalizar_numero_expediente(numero_expediente)
            if numero_normalizado in vistos:
                errores[numero_expediente] = "Expediente repetido en la fuente"
                continue
            vistos.add(numero_normalizado)

            metadata_extra = entrada.get("metadata")
            if metadata_extra is not None and not isinstance(metadata_extra, dict):
                errores[numero_expediente] = "La metadata adicional debe ser un diccionario"
                continue

            estructura = entrada.get("estructura")
            if estructura is not None and not isinstance(estructura, dict):
                errores[numero_expediente] = (
                    "La estructura personalizada debe ser un diccionario"
                )
                continue

            fusionar = entrada.get("fusionar_estructura", True)
            if not isinstance(fusionar, bool):
                errores[numero_expediente] = "'fusionar_estructura' debe ser un booleano"
                continue

            identificador = self._obtener_o_registrar_identificador(numero_normalizado)
            destino = self._obtener_ruta_expediente(numero_normalizado, identificador)
            metadata_manifest = {
                "numero_expediente": numero_expediente,
                "numero_normalizado": numero_normalizado,
            }
            if metadata_extra:
                metadata_manifest.update(deepcopy(metadata_extra))
            metadata_manifest["id"] = identificador

            try:
                manifest = self.generar_arbol(
                    destino,
                    metadata=metadata_manifest,
                    estructura=estructura,
                    fusionar_estructura=fusionar,
                )
            except Exception as exc:  # pragma: no cover - propagado en pruebas
                errores[numero_expediente] = str(exc)
                continue

            resultados.append((destino, manifest))

        if errores:
            detalles = "; ".join(f"{clave}: {mensaje}" for clave, mensaje in errores.items())
            raise ValueError(
                f"No se pudieron crear {len(errores)} expedientes: {detalles}"
            )

        return resultados

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

    def _persistir_manifest(self, manifest_path: Path, manifest: dict[str, Any]) -> None:
        """Escribe el manifiesto usando una operación atómica."""
        self._persistir_json_atomico(manifest_path, manifest)

    def _obtener_ruta_expediente(
        self, numero_normalizado: str, identificador: int
    ) -> Path:
        """Calcula la ruta destino para un expediente dado su identificador."""

        nombre_directorio = f"{identificador:06d}_{numero_normalizado}"
        return self.raiz / nombre_directorio

    def _indice_path(self) -> Path:
        """Devuelve la ruta al archivo de índice de expedientes."""

        return self.raiz / self.index_filename

    def _cargar_indice(self) -> tuple[int, dict[str, int]]:
        """Lee el índice de expedientes desde disco si está disponible."""

        indice_path = self._indice_path()
        if not indice_path.exists():
            return 0, {}

        try:
            contenido = json.loads(indice_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return 0, {}

        expedientes_brutos = contenido.get("expedientes", {})
        if not isinstance(expedientes_brutos, dict):
            expedientes_brutos = {}

        expedientes: dict[str, int] = {}
        max_id = 0
        for numero, identificador in expedientes_brutos.items():
            if isinstance(numero, str) and isinstance(identificador, int) and identificador > 0:
                expedientes[numero] = identificador
                if identificador > max_id:
                    max_id = identificador

        last_id = contenido.get("last_id", 0)
        if not isinstance(last_id, int) or last_id < max_id:
            last_id = max_id

        return last_id, expedientes

    def _guardar_indice(self, last_id: int, expedientes: dict[str, int]) -> None:
        """Persiste el índice de expedientes de manera atómica."""

        indice_path = self._indice_path()
        indice_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "last_id": last_id,
            "expedientes": expedientes,
        }
        self._persistir_json_atomico(indice_path, payload)

    def _obtener_o_registrar_identificador(self, numero_normalizado: str) -> int:
        """Obtiene el identificador del expediente o registra uno nuevo."""

        last_id, expedientes = self._cargar_indice()
        if numero_normalizado in expedientes:
            return expedientes[numero_normalizado]

        nuevo_id = last_id + 1
        expedientes[numero_normalizado] = nuevo_id
        self._guardar_indice(nuevo_id, expedientes)
        return nuevo_id

    def _persistir_json_atomico(self, destino: Path, contenido: dict[str, Any]) -> None:
        """Escribe un archivo JSON en disco utilizando reemplazo atómico."""

        destino.parent.mkdir(parents=True, exist_ok=True)
        contenido_serializado = json.dumps(contenido, indent=2, ensure_ascii=False)
        temp_path: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=destino.parent,
                delete=False,
            ) as tmp_file:
                temp_path = Path(tmp_file.name)
                tmp_file.write(contenido_serializado)
            os.replace(temp_path, destino)
        except Exception:
            if temp_path is not None:
                try:
                    temp_path.unlink(missing_ok=True)
                except Exception:
                    pass
            raise


def inicializar_directorio_base(
    config: "SystemConfig | None" = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Genera la estructura base de expedientes y devuelve su manifiesto.

    Este es el punto de entrada recomendado tras ejecutar el instalador, ya
    que crea la estructura inicial utilizando la configuración del sistema.

    Args:
        config: Instancia opcional de :class:`SystemConfig` ya cargada.
        **kwargs: Parámetros adicionales propagados a
            :meth:`GestorDirectoriosExpedientes.desde_config`, como
            ``base_dir`` o ``config_path``.

    Returns:
        dict[str, Any]: El manifiesto generado por :meth:`generar_arbol`.
    """

    gestor = GestorDirectoriosExpedientes.desde_config(config, **kwargs)
    return gestor.generar_arbol()


__all__ = [
    "ESTRUCTURA_POR_DEFECTO",
    "GestorDirectoriosExpedientes",
    "inicializar_directorio_base",
]
