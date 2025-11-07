"""Comandos para extracción masiva de expedientes."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class IniciarExtraccionMasivaCommand:
    """Comando para iniciar extracción masiva.

    Attributes:
        usuario: Usuario PJN
        contrasena: Contraseña PJN
        fecha_desde: Fecha desde (YYYY-MM-DD)
        fecha_hasta: Fecha hasta (YYYY-MM-DD)
        estados: Estados a filtrar
        dependencias: Dependencias a filtrar
        umbral_errores: Máximo de errores consecutivos permitidos
        headless: Ejecutar navegador en modo headless
        exportar_formatos: Formatos de exportación (json, excel, csv)
    """

    usuario: str
    contrasena: str
    fecha_desde: Optional[str] = None
    fecha_hasta: Optional[str] = None
    estados: Optional[List[str]] = None
    dependencias: Optional[List[str]] = None
    umbral_errores: int = 10
    headless: bool = True
    exportar_formatos: List[str] = field(default_factory=lambda: ["json"])


@dataclass
class ControlExtraccionCommand:
    """Comando para controlar extracción (pausar/reanudar/cancelar).

    Attributes:
        session_id: ID de la sesión de extracción
        accion: Acción a realizar (pausar, reanudar, cancelar)
    """

    session_id: str
    accion: str  # "pausar", "reanudar", "cancelar"

    def __post_init__(self):
        """Validar acción."""
        acciones_validas = ["pausar", "reanudar", "cancelar"]
        if self.accion not in acciones_validas:
            raise ValueError(
                f"Acción '{self.accion}' no válida. "
                f"Acciones válidas: {', '.join(acciones_validas)}"
            )
