"""Comandos de aplicación (Command pattern).

Los comandos encapsulan las intenciones del usuario y los datos necesarios
para ejecutar acciones en el sistema.

Siguiendo el patrón CQRS (Command Query Responsibility Segregation), los comandos
representan operaciones que modifican el estado del sistema.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ExtraerExpedientesCommand:
    """Comando para extraer la lista completa de expedientes del PJN.

    Este comando inicia el proceso de scraping para obtener todos los expedientes
    del usuario autenticado.

    Attributes:
        usuario: Usuario del PJN (None para usar variable de entorno)
        contrasena: Contraseña del PJN (None para usar variable de entorno)
        headless: Si True, ejecuta el navegador sin interfaz gráfica
        guardar_en: Path donde guardar el JSON resultante
    """

    usuario: str | None = None
    contrasena: str | None = None
    headless: bool = True
    guardar_en: Path | None = None


@dataclass(frozen=True)
class ExtraerEntradasCommand:
    """Comando para extraer entradas (notificaciones/despachos) del PJN.

    Attributes:
        usuario: Usuario del PJN (None para usar variable de entorno)
        contrasena: Contraseña del PJN (None para usar variable de entorno)
        headless: Si True, ejecuta el navegador sin interfaz gráfica
        guardar_en: Path donde guardar el JSON resultante
    """

    usuario: str | None = None
    contrasena: str | None = None
    headless: bool = True
    guardar_en: Path | None = None


@dataclass(frozen=True)
class ExtraerActuacionesCommand:
    """Comando para extraer actuaciones de un expediente específico.

    Attributes:
        numero_expediente: Número del expediente (ej: "FPA-000632-2017")
        anio: Año del expediente
        usuario: Usuario del PJN (None para usar variable de entorno)
        contrasena: Contraseña del PJN (None para usar variable de entorno)
        headless: Si True, ejecuta el navegador sin interfaz gráfica
        guardar_en: Path donde guardar el JSON resultante
    """

    numero_expediente: str
    anio: str
    usuario: str | None = None
    contrasena: str | None = None
    headless: bool = True
    guardar_en: Path | None = None


@dataclass(frozen=True)
class FiltrarExpedientesCommand:
    """Comando para filtrar expedientes según criterios del usuario.

    Este comando permite al usuario seleccionar qué expedientes pasarán del
    JSON "base" al JSON "sistema" que será monitoreado.

    Attributes:
        numeros_seleccionados: Lista de números de expediente seleccionados
        origen: Path del JSON "base" (fuente de datos)
        destino: Path del JSON "sistema" (resultado del filtrado)
        incluir_activos: Si True, incluye automáticamente expedientes activos
        dias_actividad: Días hacia atrás para considerar "activo"
    """

    numeros_seleccionados: list[str]
    origen: Path
    destino: Path
    incluir_activos: bool = False
    dias_actividad: int = 30


@dataclass(frozen=True)
class CrearWorkspaceCommand:
    """Comando para crear el workspace (estructura de directorios) de un expediente.

    Attributes:
        numero_expediente: Número del expediente
        base_path: Directorio base donde crear el workspace
        extraer_actuaciones: Si True, extrae actuaciones automáticamente
        descargar_archivos: Si True, descarga archivos adjuntos automáticamente
    """

    numero_expediente: str
    base_path: Path
    extraer_actuaciones: bool = True
    descargar_archivos: bool = False


@dataclass(frozen=True)
class CrearWorkspacesCommand:
    """Comando para crear workspaces para múltiples expedientes.

    Attributes:
        json_sistema: Path del JSON "sistema" con expedientes seleccionados
        base_path: Directorio base donde crear los workspaces
        extraer_actuaciones: Si True, extrae actuaciones automáticamente
        descargar_archivos: Si True, descarga archivos adjuntos automáticamente
    """

    json_sistema: Path
    base_path: Path
    extraer_actuaciones: bool = True
    descargar_archivos: bool = False


@dataclass(frozen=True)
class MonitorearExpedientesCommand:
    """Comando para monitorear expedientes y mantener actualizado el sistema.

    Este comando ejecuta el monitoreo periódico de expedientes seleccionados,
    detectando cambios y actualizando el workspace.

    Attributes:
        json_sistema: Path del JSON "sistema" con expedientes a monitorear
        base_path: Directorio base de los workspaces
        intervalo_segundos: Intervalo entre verificaciones (0 = ejecutar una vez)
        notificar_cambios: Si True, envía notificaciones cuando hay cambios
        descargar_nuevos_archivos: Si True, descarga archivos nuevos automáticamente
    """

    json_sistema: Path
    base_path: Path
    intervalo_segundos: int = 0
    notificar_cambios: bool = True
    descargar_nuevos_archivos: bool = True


@dataclass(frozen=True)
class DescargarArchivoCommand:
    """Comando para descargar un archivo adjunto de una actuación.

    Attributes:
        numero_expediente: Número del expediente
        indice_actuacion: Índice de la actuación que contiene el archivo
        destino: Directorio donde guardar el archivo
        usuario: Usuario del PJN (None para usar variable de entorno)
        contrasena: Contraseña del PJN (None para usar variable de entorno)
        headless: Si True, ejecuta el navegador sin interfaz gráfica
    """

    numero_expediente: str
    indice_actuacion: int
    destino: Path
    usuario: str | None = None
    contrasena: str | None = None
    headless: bool = True


@dataclass(frozen=True)
class MarcarEntradaLeidaCommand:
    """Comando para marcar una entrada como leída.

    Attributes:
        numero_expediente: Número del expediente de la entrada
        fecha: Fecha de la entrada
        evento: Evento de la entrada (para identificación única)
    """

    numero_expediente: str
    fecha: str
    evento: str | None = None
