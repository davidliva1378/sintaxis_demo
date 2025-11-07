"""Interfaces de servicios externos.

Este módulo define los contratos (interfaces) para servicios externos que la capa
de aplicación necesita: scraping, almacenamiento de archivos, notificaciones, etc.

Siguiendo el principio de Inversión de Dependencias, la aplicación define estas
interfaces y la infraestructura las implementa.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Mapping, Sequence

from core.domain.entities import (
    Actuacion,
    ActuacionesArchivo,
    Entrada,
    ExpedienteIdentificacion,
    ExpedienteResumen,
)


class IScraperPort(ABC):
    """Interfaz para scraping del Portal Judicial Nacional.

    Define las operaciones de extracción de datos del PJN usando web scraping.
    """

    @abstractmethod
    async def extraer_expedientes(
        self,
        *,
        credenciales: tuple[str, str] | None = None,
        headless: bool = True,
    ) -> list[ExpedienteResumen]:
        """Extrae la lista completa de expedientes del usuario.

        Args:
            credenciales: Tupla (usuario, contraseña) o None para usar env vars
            headless: Si True, ejecuta el navegador sin interfaz gráfica

        Returns:
            Lista de expedientes extraídos

        Raises:
            CredencialesFaltantes: Si las credenciales no están disponibles
            SesionInvalida: Si la sesión no es válida
            ScrapingError: Si ocurre un error durante el scraping
        """
        pass

    @abstractmethod
    async def extraer_entradas(
        self,
        *,
        credenciales: tuple[str, str] | None = None,
        headless: bool = True,
    ) -> list[Entrada]:
        """Extrae las entradas (notificaciones/despachos) del usuario.

        Args:
            credenciales: Tupla (usuario, contraseña) o None para usar env vars
            headless: Si True, ejecuta el navegador sin interfaz gráfica

        Returns:
            Lista de entradas extraídas

        Raises:
            CredencialesFaltantes: Si las credenciales no están disponibles
            SesionInvalida: Si la sesión no es válida
            ScrapingError: Si ocurre un error durante el scraping
        """
        pass

    @abstractmethod
    async def extraer_actuaciones(
        self,
        identificacion: ExpedienteIdentificacion,
        *,
        credenciales: tuple[str, str] | None = None,
        headless: bool = True,
    ) -> ActuacionesArchivo:
        """Extrae las actuaciones de un expediente específico.

        Args:
            identificacion: Identificación del expediente (numero y año)
            credenciales: Tupla (usuario, contraseña) o None para usar env vars
            headless: Si True, ejecuta el navegador sin interfaz gráfica

        Returns:
            Archivo con encabezado y actuaciones del expediente

        Raises:
            ExpedienteNoEncontrado: Si el expediente no existe
            CredencialesFaltantes: Si las credenciales no están disponibles
            SesionInvalida: Si la sesión no es válida
            ScrapingError: Si ocurre un error durante el scraping
        """
        pass

    @abstractmethod
    async def descargar_archivo_actuacion(
        self,
        actuacion: Actuacion,
        destino: Path,
        *,
        credenciales: tuple[str, str] | None = None,
        headless: bool = True,
    ) -> Path:
        """Descarga el archivo adjunto de una actuación.

        Args:
            actuacion: Actuación que contiene el archivo
            destino: Ruta donde guardar el archivo
            credenciales: Tupla (usuario, contraseña) o None para usar env vars
            headless: Si True, ejecuta el navegador sin interfaz gráfica

        Returns:
            Path del archivo descargado

        Raises:
            ArchivoNoDisponible: Si la actuación no tiene archivo
            CredencialesFaltantes: Si las credenciales no están disponibles
            DescargaError: Si ocurre un error durante la descarga
        """
        pass


class IStoragePort(ABC):
    """Interfaz para almacenamiento de archivos y datos.

    Define las operaciones de lectura/escritura de archivos JSON, PDFs, etc.
    """

    @abstractmethod
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
            StorageError: Si ocurre un error al guardar
        """
        pass

    @abstractmethod
    async def leer_json(self, archivo: Path) -> Mapping[str, Any] | list[Any]:
        """Lee datos desde un archivo JSON.

        Args:
            archivo: Ruta del archivo JSON

        Returns:
            Datos leídos (dict o lista)

        Raises:
            ArchivoNoEncontrado: Si el archivo no existe
            StorageError: Si ocurre un error al leer
        """
        pass

    @abstractmethod
    async def existe_archivo(self, archivo: Path) -> bool:
        """Verifica si existe un archivo.

        Args:
            archivo: Ruta del archivo

        Returns:
            True si existe, False en caso contrario
        """
        pass

    @abstractmethod
    async def crear_directorio(self, directorio: Path) -> None:
        """Crea un directorio (y sus padres si no existen).

        Args:
            directorio: Ruta del directorio a crear

        Raises:
            StorageError: Si ocurre un error al crear
        """
        pass

    @abstractmethod
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
            StorageError: Si ocurre un error al listar
        """
        pass

    @abstractmethod
    async def copiar_archivo(self, origen: Path, destino: Path) -> None:
        """Copia un archivo de origen a destino.

        Args:
            origen: Ruta del archivo origen
            destino: Ruta del archivo destino

        Raises:
            ArchivoNoEncontrado: Si el archivo origen no existe
            StorageError: Si ocurre un error al copiar
        """
        pass

    @abstractmethod
    async def mover_archivo(self, origen: Path, destino: Path) -> None:
        """Mueve un archivo de origen a destino.

        Args:
            origen: Ruta del archivo origen
            destino: Ruta del archivo destino

        Raises:
            ArchivoNoEncontrado: Si el archivo origen no existe
            StorageError: Si ocurre un error al mover
        """
        pass


class INotificacionPort(ABC):
    """Interfaz para envío de notificaciones.

    Define las operaciones para notificar al usuario por diferentes canales.
    """

    @abstractmethod
    async def notificar_escritorio(
        self,
        titulo: str,
        mensaje: str,
        *,
        urgencia: str = "normal",
    ) -> None:
        """Envía una notificación del sistema operativo.

        Args:
            titulo: Título de la notificación
            mensaje: Cuerpo del mensaje
            urgencia: Nivel de urgencia ("normal", "alta", "critica")

        Raises:
            NotificacionError: Si ocurre un error al enviar
        """
        pass

    @abstractmethod
    async def notificar_email(
        self,
        destinatario: str,
        asunto: str,
        cuerpo: str,
        *,
        html: bool = False,
    ) -> None:
        """Envía una notificación por email.

        Args:
            destinatario: Dirección de email del destinatario
            asunto: Asunto del email
            cuerpo: Cuerpo del mensaje
            html: Si True, el cuerpo es HTML

        Raises:
            NotificacionError: Si ocurre un error al enviar
        """
        pass

    @abstractmethod
    async def notificar_telegram(
        self,
        mensaje: str,
        *,
        chat_id: str | None = None,
    ) -> None:
        """Envía una notificación por Telegram.

        Args:
            mensaje: Mensaje a enviar (soporta Markdown)
            chat_id: ID del chat (None para usar default de config)

        Raises:
            NotificacionError: Si ocurre un error al enviar
        """
        pass


class IWorkspacePort(ABC):
    """Interfaz para gestión de workspaces de expedientes.

    Define las operaciones para crear y mantener la estructura de directorios
    de cada expediente.
    """

    @abstractmethod
    async def crear_workspace(
        self,
        numero_expediente: str,
        base_path: Path,
    ) -> Path:
        """Crea la estructura de directorios para un expediente.

        Estructura típica:
        base_path/
        └── FPA-000632-2017/
            ├── actuaciones.json
            ├── archivos/
            │   ├── actuacion_001.pdf
            │   └── actuacion_002.pdf
            └── metadata.json

        Args:
            numero_expediente: Número del expediente
            base_path: Directorio base donde crear el workspace

        Returns:
            Path del workspace creado

        Raises:
            StorageError: Si ocurre un error al crear
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
    async def listar_workspaces(self, base_path: Path) -> list[str]:
        """Lista todos los workspaces existentes.

        Args:
            base_path: Directorio base donde buscar

        Returns:
            Lista de números de expediente con workspace
        """
        pass
