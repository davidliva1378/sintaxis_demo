"""
Sistema de gestión de estados de expedientes.

Este módulo maneja los diferentes estados que puede tener un expediente
durante su ciclo de vida en el sistema.
"""

from enum import Enum
from typing import Dict, List, Optional
from pathlib import Path
import json
from datetime import datetime


class EstadoExpediente(str, Enum):
    """Estados posibles de un expediente."""

    NUEVO = "nuevo"                    # Recién descubierto
    MONITOREADO = "monitoreado"        # En seguimiento activo
    PRIORIZADO = "priorizado"          # Requiere atención urgente
    ARCHIVADO = "archivado"            # No requiere seguimiento
    IGNORADO = "ignorado"              # Excluido permanentemente
    ERROR = "error"                    # Error en procesamiento


class GestorEstados:
    """Gestor de estados de expedientes."""

    def __init__(self, archivo_estados: Optional[Path] = None):
        """
        Inicializar gestor de estados.

        Args:
            archivo_estados: Ruta al archivo JSON de estados
        """
        from Sistema_v6.configuracion.config import Config

        if archivo_estados is None:
            archivo_estados = Config.DATA_DIR / "estados_expedientes.json"

        self.archivo_estados = Path(archivo_estados)
        self.estados: Dict[str, Dict] = {}
        self.cargar_estados()

    def cargar_estados(self) -> None:
        """Cargar estados desde archivo JSON."""
        if self.archivo_estados.exists():
            try:
                with open(self.archivo_estados, "r", encoding="utf-8") as f:
                    self.estados = json.load(f)
            except Exception as e:
                print(f"⚠️ Error al cargar estados: {e}")
                self.estados = {}
        else:
            self.estados = {}

    def guardar_estados(self) -> None:
        """Guardar estados a archivo JSON."""
        self.archivo_estados.parent.mkdir(parents=True, exist_ok=True)

        with open(self.archivo_estados, "w", encoding="utf-8") as f:
            json.dump(self.estados, f, indent=2, ensure_ascii=False)

    def obtener_estado(self, numero_expediente: str) -> EstadoExpediente:
        """
        Obtener estado de un expediente.

        Args:
            numero_expediente: Número del expediente

        Returns:
            Estado del expediente (NUEVO si no existe)
        """
        if numero_expediente in self.estados:
            return EstadoExpediente(self.estados[numero_expediente]["estado"])
        return EstadoExpediente.NUEVO

    def actualizar_estado(
        self,
        numero_expediente: str,
        estado: EstadoExpediente,
        nota: Optional[str] = None,
        auto_guardar: bool = True
    ) -> None:
        """
        Actualizar estado de un expediente.

        Args:
            numero_expediente: Número del expediente
            estado: Nuevo estado
            nota: Nota adicional opcional
            auto_guardar: Si debe guardar automáticamente
        """
        self.estados[numero_expediente] = {
            "estado": estado.value,
            "fecha_actualizacion": datetime.now().isoformat(),
            "nota": nota
        }

        if auto_guardar:
            self.guardar_estados()

    def filtrar_por_estado(
        self,
        expedientes: List[Dict],
        estados_permitidos: List[EstadoExpediente]
    ) -> List[Dict]:
        """
        Filtrar expedientes por estado.

        Args:
            expedientes: Lista de expedientes
            estados_permitidos: Estados que se deben incluir

        Returns:
            Lista filtrada de expedientes
        """
        estados_str = [e.value for e in estados_permitidos]

        return [
            exp for exp in expedientes
            if self.obtener_estado(exp["numero"]).value in estados_str
        ]

    def inicializar_expedientes(
        self,
        numeros_expedientes: List[str],
        estado_inicial: EstadoExpediente = EstadoExpediente.MONITOREADO,
        auto_guardar: bool = True
    ) -> None:
        """
        Inicializar expedientes con un estado por defecto.

        Args:
            numeros_expedientes: Lista de números de expedientes
            estado_inicial: Estado inicial a asignar
            auto_guardar: Si debe guardar automáticamente
        """
        for numero in numeros_expedientes:
            if numero not in self.estados:
                self.estados[numero] = {
                    "estado": estado_inicial.value,
                    "fecha_creacion": datetime.now().isoformat(),
                    "fecha_actualizacion": datetime.now().isoformat(),
                    "nota": None
                }

        if auto_guardar:
            self.guardar_estados()

    def obtener_estadisticas(self) -> Dict[str, int]:
        """
        Obtener estadísticas de estados.

        Returns:
            Diccionario con conteo por estado
        """
        stats = {}
        for estado in EstadoExpediente:
            stats[estado.value] = 0

        for info in self.estados.values():
            estado = info["estado"]
            if estado in stats:
                stats[estado] += 1

        return stats
