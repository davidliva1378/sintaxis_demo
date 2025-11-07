"""Gestor de directorios para expedientes."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class GestorDirectoriosExpedientes:
    """Gestiona la creación de estructura de directorios para expedientes.

    Crea una jerarquía de directorios organizada para almacenar:
    - Datos del expediente
    - Actuaciones
    - Documentos descargados
    - Metadata y manifiestos
    """

    def __init__(self, raiz: Path | str):
        """Inicializa el gestor de directorios.

        Args:
            raiz: Directorio raíz donde se crearán los expedientes
        """
        self.raiz = Path(raiz)
        self.raiz.mkdir(parents=True, exist_ok=True)

    def crear_desde_json(
        self,
        expedientes: list[dict[str, Any]]
    ) -> list[tuple[Path, dict[str, Any]]]:
        """Crea estructura de directorios para una lista de expedientes.

        Args:
            expedientes: Lista de diccionarios con datos de expedientes
                        Cada diccionario debe tener al menos: numero, caratula

        Returns:
            Lista de tuplas (ruta_expediente, manifest) con información de
            directorios creados
        """
        resultados: list[tuple[Path, dict[str, Any]]] = []

        for expediente in expedientes:
            try:
                ruta, manifest = self.crear_expediente(expediente)
                resultados.append((ruta, manifest))

            except Exception as e:
                logger.error(
                    f"❌ Error al crear directorio para expediente "
                    f"{expediente.get('numero', 'DESCONOCIDO')}: {e}"
                )
                continue

        return resultados

    def crear_expediente(
        self,
        expediente: dict[str, Any]
    ) -> tuple[Path, dict[str, Any]]:
        """Crea la estructura de directorios para un expediente.

        Args:
            expediente: Diccionario con datos del expediente

        Returns:
            Tupla (ruta_expediente, manifest) con:
            - ruta_expediente: Path al directorio principal
            - manifest: Dict con metadata de directorios creados

        Raises:
            ValueError: Si faltan campos obligatorios
            Exception: Si hay error al crear directorios
        """
        numero = expediente.get("numero")
        caratula = expediente.get("caratula")

        if not numero or not caratula:
            raise ValueError("El expediente debe tener 'numero' y 'caratula'")

        # Sanitizar nombre del expediente
        nombre_sanitizado = self._sanitizar_nombre(numero)

        # Crear directorio principal del expediente
        directorio_expediente = self.raiz / nombre_sanitizado
        directorio_expediente.mkdir(parents=True, exist_ok=True)

        # Crear subdirectorios
        subdirectorios = self._crear_subdirectorios(directorio_expediente)

        # Crear manifest.json con metadata
        manifest = {
            "numero_expediente": numero,
            "caratula": caratula,
            "juzgado": expediente.get("juzgado"),
            "fecha": expediente.get("fecha"),
            "tipo": expediente.get("tipo"),
            "fecha_creacion": datetime.now().isoformat(),
            "directories": subdirectorios,
            "metadata": expediente.get("metadata", {})
        }

        # Guardar manifest.json
        manifest_path = directorio_expediente / "manifest.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.debug(f"✅ Creado directorio para expediente {numero}")

        return directorio_expediente, manifest

    def _crear_subdirectorios(self, directorio_base: Path) -> list[str]:
        """Crea los subdirectorios estándar dentro de un expediente.

        Args:
            directorio_base: Path al directorio del expediente

        Returns:
            Lista de nombres de subdirectorios creados
        """
        subdirectorios = [
            "actuaciones",       # Datos de actuaciones
            "documentos",        # PDFs y archivos descargados
            "adjuntos",          # Adjuntos descargados
            "procesados",        # Datos procesados
            "reportes",          # Reportes generados
            "temporal"           # Archivos temporales
        ]

        for subdir in subdirectorios:
            (directorio_base / subdir).mkdir(parents=True, exist_ok=True)

        return subdirectorios

    def _sanitizar_nombre(self, nombre: str) -> str:
        """Sanitiza un nombre para usarlo como nombre de directorio.

        Args:
            nombre: Nombre a sanitizar

        Returns:
            Nombre sanitizado seguro para filesystem
        """
        # Reemplazar caracteres problemáticos
        reemplazos = {
            '/': '-',
            '\\': '-',
            ':': '-',
            '*': '-',
            '?': '-',
            '"': '',
            '<': '',
            '>': '',
            '|': '-',
            ' ': '_'
        }

        nombre_sanitizado = nombre
        for char, reemplazo in reemplazos.items():
            nombre_sanitizado = nombre_sanitizado.replace(char, reemplazo)

        # Limitar longitud (algunos sistemas tienen límite de 255 caracteres)
        if len(nombre_sanitizado) > 200:
            nombre_sanitizado = nombre_sanitizado[:200]

        return nombre_sanitizado

    def obtener_directorio_expediente(self, numero_expediente: str) -> Path | None:
        """Obtiene el path al directorio de un expediente.

        Args:
            numero_expediente: Número del expediente

        Returns:
            Path al directorio o None si no existe
        """
        nombre_sanitizado = self._sanitizar_nombre(numero_expediente)
        directorio = self.raiz / nombre_sanitizado

        if directorio.exists():
            return directorio

        return None

    def listar_expedientes(self) -> list[dict[str, Any]]:
        """Lista todos los expedientes en el directorio raíz.

        Returns:
            Lista de diccionarios con info de expedientes (desde manifest.json)
        """
        expedientes = []

        for directorio in self.raiz.iterdir():
            if not directorio.is_dir():
                continue

            manifest_path = directorio / "manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    expedientes.append(manifest)
                except Exception as e:
                    logger.warning(
                        f"⚠️  Error al leer manifest de {directorio.name}: {e}"
                    )

        return expedientes
