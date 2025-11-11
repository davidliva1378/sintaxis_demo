"""Gestor de archivos del usuario dentro de expedientes.

Este módulo maneja archivos propios del usuario en la carpeta documentos_usuario/
del expediente, permitiendo organización por categorías, tags y búsqueda.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .expedientes import GestorDirectoriosExpedientes


CATEGORIAS_VALIDAS = {"notas", "borradores", "evidencia", "correspondencia", "otros"}


class GestorArchivosUsuario:
    """Gestiona archivos del usuario dentro del expediente."""

    def __init__(self, gestor_expedientes: GestorDirectoriosExpedientes):
        """Inicializa el gestor.

        Args:
            gestor_expedientes: Instancia del gestor de expedientes
        """
        self.gestor = gestor_expedientes

    def agregar_archivo(
        self,
        numero_expediente: str,
        archivo_origen: Path | str,
        categoria: str = "otros",
        tags: list[str] | None = None,
        descripcion: str = "",
        calcular_hash: bool = True,
        copiar: bool = True,
    ) -> dict:
        """Agrega un archivo a documentos_usuario del expediente.

        Args:
            numero_expediente: Número del expediente
            archivo_origen: Ruta al archivo a agregar
            categoria: Categoría (notas, borradores, evidencia, correspondencia, otros)
            tags: Tags para clasificación
            descripcion: Descripción del archivo
            calcular_hash: Si calcular SHA-256
            copiar: Si copiar (True) o mover (False) el archivo

        Returns:
            Diccionario con información del archivo agregado

        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si la categoría es inválida
        """
        archivo_origen = Path(archivo_origen)

        if not archivo_origen.exists():
            raise FileNotFoundError(f"El archivo no existe: {archivo_origen}")

        if not archivo_origen.is_file():
            raise ValueError(f"La ruta no es un archivo: {archivo_origen}")

        if categoria not in CATEGORIAS_VALIDAS:
            raise ValueError(
                f"Categoría inválida: {categoria}. "
                f"Debe ser una de: {', '.join(CATEGORIAS_VALIDAS)}"
            )

        # Obtener ruta del expediente
        from .expedientes import normalizar_numero_expediente

        numero_normalizado = normalizar_numero_expediente(numero_expediente)
        identificador = self.gestor._obtener_o_registrar_identificador(numero_normalizado)
        ruta_expediente = self.gestor._obtener_ruta_expediente(numero_normalizado, identificador)

        # Crear directorio de categoría
        dir_categoria = ruta_expediente / "documentos_usuario" / categoria
        dir_categoria.mkdir(parents=True, exist_ok=True)

        # Destino del archivo
        archivo_destino = dir_categoria / archivo_origen.name

        # Evitar sobrescritura
        if archivo_destino.exists():
            # Agregar timestamp al nombre
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_sin_ext = archivo_origen.stem
            extension = archivo_origen.suffix
            archivo_destino = dir_categoria / f"{nombre_sin_ext}_{timestamp}{extension}"

        # Copiar o mover archivo
        if copiar:
            shutil.copy2(archivo_origen, archivo_destino)
        else:
            shutil.move(str(archivo_origen), archivo_destino)

        # Obtener información del archivo
        stat = archivo_destino.stat()
        extension = archivo_destino.suffix.lower()
        tipo_mime = mimetypes.guess_type(archivo_destino)[0] or "application/octet-stream"

        # Calcular hash
        hash_sha256 = None
        if calcular_hash:
            hash_sha256 = self._calcular_sha256(archivo_destino)

        # Crear registro
        info_archivo = {
            "nombre": archivo_destino.name,
            "ruta_relativa": str(archivo_destino.relative_to(ruta_expediente)),
            "ruta_absoluta": str(archivo_destino.resolve()),
            "tamano_bytes": stat.st_size,
            "tamano_mb": round(stat.st_size / 1024 / 1024, 2),
            "extension": extension,
            "tipo_mime": tipo_mime,
            "categoria": categoria,
            "fecha_creacion": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "fecha_modificacion": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "fecha_agregado": datetime.now().isoformat(),
            "hash_sha256": hash_sha256,
            "tags": tags or [],
            "descripcion": descripcion,
        }

        # Actualizar índice en manifest
        self._actualizar_indice_archivo(numero_expediente, categoria, info_archivo)

        return info_archivo

    def listar_archivos(
        self,
        numero_expediente: str,
        categoria: str | None = None,
        tags: list[str] | None = None,
        extension: str | None = None,
    ) -> list[dict]:
        """Lista archivos del usuario con filtros opcionales.

        Args:
            numero_expediente: Número del expediente
            categoria: Filtrar por categoría
            tags: Filtrar por tags (incluye archivos que tengan cualquiera de los tags)
            extension: Filtrar por extensión (ej: ".pdf")

        Returns:
            Lista de diccionarios con información de archivos
        """
        from .expedientes import normalizar_numero_expediente

        numero_normalizado = normalizar_numero_expediente(numero_expediente)
        identificador = self.gestor._obtener_o_registrar_identificador(numero_normalizado)
        ruta_expediente = self.gestor._obtener_ruta_expediente(numero_normalizado, identificador)

        manifest_path = ruta_expediente / self.gestor.manifest_filename

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            archivos_usuario = manifest.get("archivos_usuario", {})
            categorias = archivos_usuario.get("categorias", {})

            archivos = []

            # Filtrar por categoría si se especifica
            categorias_a_buscar = [categoria] if categoria else categorias.keys()

            for cat in categorias_a_buscar:
                if cat not in categorias:
                    continue

                for archivo in categorias[cat].get("archivos", []):
                    # Aplicar filtros
                    if tags and not any(t in archivo.get("tags", []) for t in tags):
                        continue

                    if extension and archivo.get("extension") != extension:
                        continue

                    archivos.append(archivo)

            # Incluir archivos de directorios externos
            directorios_externos = manifest.get("directorios_externos", [])
            for dir_ext in directorios_externos:
                if not dir_ext.get("activo", True):
                    continue

                for archivo in dir_ext.get("archivos", []):
                    # Aplicar filtros
                    if tags and not any(t in archivo.get("tags", []) for t in tags):
                        continue

                    if extension and archivo.get("extension") != extension:
                        continue

                    # Agregar información del directorio de origen
                    archivo_con_origen = archivo.copy()
                    archivo_con_origen["origen"] = "directorio_externo"
                    archivo_con_origen["directorio_id"] = dir_ext.get("id")
                    archivo_con_origen["directorio_nombre"] = dir_ext.get("nombre")

                    archivos.append(archivo_con_origen)

            return archivos

        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def eliminar_archivo(
        self,
        numero_expediente: str,
        ruta_relativa: str,
        permanente: bool = False,
    ) -> bool:
        """Elimina un archivo del usuario.

        Args:
            numero_expediente: Número del expediente
            ruta_relativa: Ruta relativa del archivo dentro del expediente
            permanente: Si eliminar permanentemente (True) o mover a papelera (False)

        Returns:
            True si se eliminó correctamente
        """
        from .expedientes import normalizar_numero_expediente

        numero_normalizado = normalizar_numero_expediente(numero_expediente)
        identificador = self.gestor._obtener_o_registrar_identificador(numero_normalizado)
        ruta_expediente = self.gestor._obtener_ruta_expediente(numero_normalizado, identificador)

        archivo_path = ruta_expediente / ruta_relativa

        if not archivo_path.exists():
            return False

        if permanente:
            # Eliminar permanentemente
            archivo_path.unlink()
        else:
            # Mover a papelera
            papelera = ruta_expediente / ".metadata" / "papelera"
            papelera.mkdir(parents=True, exist_ok=True)

            # Guardar metadata de eliminación
            metadata_eliminacion = {
                "archivo_original": str(ruta_relativa),
                "fecha_eliminacion": datetime.now().isoformat(),
                "categoria_original": ruta_relativa.split("/")[1] if "/" in ruta_relativa else "otros",
            }

            archivo_destino = papelera / archivo_path.name
            metadata_path = papelera / f"{archivo_path.name}.metadata.json"

            shutil.move(str(archivo_path), archivo_destino)
            metadata_path.write_text(
                json.dumps(metadata_eliminacion, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )

        # Actualizar índice
        self._eliminar_de_indice(numero_expediente, ruta_relativa)

        return True

    def actualizar_indice(self, numero_expediente: str) -> dict:
        """Reconstruye el índice de archivos escaneando el directorio.

        Args:
            numero_expediente: Número del expediente

        Returns:
            Diccionario con estadísticas del índice actualizado
        """
        from .expedientes import normalizar_numero_expediente

        numero_normalizado = normalizar_numero_expediente(numero_expediente)
        identificador = self.gestor._obtener_o_registrar_identificador(numero_normalizado)
        ruta_expediente = self.gestor._obtener_ruta_expediente(numero_normalizado, identificador)

        dir_documentos_usuario = ruta_expediente / "documentos_usuario"

        if not dir_documentos_usuario.exists():
            return {"total_archivos": 0, "categorias": {}}

        categorias_indices = {}
        total_archivos = 0

        for categoria in CATEGORIAS_VALIDAS:
            if categoria == "externos":  # Skip externos (manejado por otro gestor)
                continue

            dir_categoria = dir_documentos_usuario / categoria

            if not dir_categoria.exists():
                continue

            archivos_categoria = []

            for archivo in dir_categoria.iterdir():
                if not archivo.is_file():
                    continue

                stat = archivo.stat()
                extension = archivo.suffix.lower()
                tipo_mime = mimetypes.guess_type(archivo)[0] or "application/octet-stream"

                info_archivo = {
                    "nombre": archivo.name,
                    "ruta_relativa": str(archivo.relative_to(ruta_expediente)),
                    "ruta_absoluta": str(archivo.resolve()),
                    "tamano_bytes": stat.st_size,
                    "tamano_mb": round(stat.st_size / 1024 / 1024, 2),
                    "extension": extension,
                    "tipo_mime": tipo_mime,
                    "categoria": categoria,
                    "fecha_creacion": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "fecha_modificacion": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    "hash_sha256": None,
                    "tags": [],
                    "descripcion": "",
                }

                archivos_categoria.append(info_archivo)
                total_archivos += 1

            categorias_indices[categoria] = {
                "directorio": f"documentos_usuario/{categoria}",
                "archivos": archivos_categoria,
            }

        # Actualizar manifest
        manifest_path = ruta_expediente / self.gestor.manifest_filename

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            manifest = {"directories": [], "metadata": {}}

        manifest["archivos_usuario"] = {
            "indice_ultima_actualizacion": datetime.now().isoformat(),
            "total_archivos": total_archivos,
            "total_archivos_propios": total_archivos,
            "total_archivos_externos": manifest.get("archivos_usuario", {}).get(
                "total_archivos_externos", 0
            ),
            "categorias": categorias_indices,
        }

        self._guardar_manifest_atomico(manifest_path, manifest)

        return {
            "total_archivos": total_archivos,
            "categorias": list(categorias_indices.keys()),
        }

    def _calcular_sha256(self, archivo: Path) -> str:
        """Calcula hash SHA-256 de un archivo."""
        sha256 = hashlib.sha256()
        with archivo.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def _actualizar_indice_archivo(
        self,
        numero_expediente: str,
        categoria: str,
        info_archivo: dict,
    ) -> None:
        """Actualiza índice en manifest con nuevo archivo."""
        from .expedientes import normalizar_numero_expediente

        numero_normalizado = normalizar_numero_expediente(numero_expediente)
        identificador = self.gestor._obtener_o_registrar_identificador(numero_normalizado)
        ruta_expediente = self.gestor._obtener_ruta_expediente(numero_normalizado, identificador)

        manifest_path = ruta_expediente / self.gestor.manifest_filename

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            manifest = {"directories": [], "metadata": {}}

        # Inicializar archivos_usuario si no existe
        if "archivos_usuario" not in manifest:
            manifest["archivos_usuario"] = {
                "indice_ultima_actualizacion": datetime.now().isoformat(),
                "total_archivos": 0,
                "total_archivos_propios": 0,
                "total_archivos_externos": 0,
                "categorias": {},
            }

        archivos_usuario = manifest["archivos_usuario"]

        # Inicializar categoría si no existe
        if "categorias" not in archivos_usuario:
            archivos_usuario["categorias"] = {}

        if categoria not in archivos_usuario["categorias"]:
            archivos_usuario["categorias"][categoria] = {
                "directorio": f"documentos_usuario/{categoria}",
                "archivos": [],
            }

        # Agregar archivo
        archivos_usuario["categorias"][categoria]["archivos"].append(info_archivo)

        # Actualizar totales
        archivos_usuario["total_archivos_propios"] = sum(
            len(cat["archivos"])
            for cat in archivos_usuario["categorias"].values()
        )
        archivos_usuario["total_archivos"] = (
            archivos_usuario["total_archivos_propios"] +
            archivos_usuario.get("total_archivos_externos", 0)
        )
        archivos_usuario["indice_ultima_actualizacion"] = datetime.now().isoformat()

        self._guardar_manifest_atomico(manifest_path, manifest)

    def _eliminar_de_indice(self, numero_expediente: str, ruta_relativa: str) -> None:
        """Elimina archivo del índice en manifest."""
        from .expedientes import normalizar_numero_expediente

        numero_normalizado = normalizar_numero_expediente(numero_expediente)
        identificador = self.gestor._obtener_o_registrar_identificador(numero_normalizado)
        ruta_expediente = self.gestor._obtener_ruta_expediente(numero_normalizado, identificador)

        manifest_path = ruta_expediente / self.gestor.manifest_filename

        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError):
            return

        archivos_usuario = manifest.get("archivos_usuario", {})
        categorias = archivos_usuario.get("categorias", {})

        # Buscar y eliminar archivo
        for cat_nombre, cat_data in categorias.items():
            archivos = cat_data.get("archivos", [])
            archivos_filtrados = [
                a for a in archivos
                if a.get("ruta_relativa") != ruta_relativa
            ]

            if len(archivos_filtrados) != len(archivos):
                cat_data["archivos"] = archivos_filtrados

                # Actualizar totales
                archivos_usuario["total_archivos_propios"] = sum(
                    len(cat["archivos"])
                    for cat in categorias.values()
                )
                archivos_usuario["total_archivos"] = (
                    archivos_usuario["total_archivos_propios"] +
                    archivos_usuario.get("total_archivos_externos", 0)
                )
                archivos_usuario["indice_ultima_actualizacion"] = datetime.now().isoformat()

                self._guardar_manifest_atomico(manifest_path, manifest)
                break

    def _guardar_manifest_atomico(self, path: Path, data: dict) -> None:
        """Guarda manifest usando escritura atómica."""
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            dir=path.parent,
            prefix=".tmp_",
        ) as tmp:
            json.dump(data, tmp, indent=2, ensure_ascii=False)
            tmp_path = Path(tmp.name)

        tmp_path.replace(path)


__all__ = ["GestorArchivosUsuario", "CATEGORIAS_VALIDAS"]
