"""Gestor de estados de expedientes para extracción masiva."""

from __future__ import annotations

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from scripts.extraccion_masiva.models import EstadoExpediente

logger = logging.getLogger(__name__)


class EstadosManager:
    """Gestiona los estados de expedientes en el sistema de extracción masiva.

    Permite cargar, guardar y modificar estados de expedientes almacenados
    en un archivo JSON.
    """

    def __init__(self, archivo_estados: Path | str):
        """Inicializa el gestor de estados.

        Args:
            archivo_estados: Ruta al archivo JSON de estados
        """
        self.archivo_estados = Path(archivo_estados)
        self.estados: dict[str, dict[str, Any]] = {}

        # Crear directorio si no existe
        self.archivo_estados.parent.mkdir(parents=True, exist_ok=True)

    def cargar_estados(self) -> dict[str, dict[str, Any]]:
        """Carga los estados desde el archivo JSON.

        Returns:
            Diccionario con estados cargados

        Raises:
            Exception: Si hay error al cargar el archivo
        """
        if not self.archivo_estados.exists():
            logger.info(f"📝 Creando nuevo archivo de estados: {self.archivo_estados}")
            self.estados = {}
            self.guardar_estados()
            return self.estados

        try:
            with open(self.archivo_estados, 'r', encoding='utf-8') as f:
                self.estados = json.load(f)
            logger.info(f"✅ Cargados {len(self.estados)} estados desde {self.archivo_estados}")
            return self.estados

        except Exception as e:
            logger.error(f"❌ Error al cargar estados: {e}")
            raise

    def guardar_estados(self) -> None:
        """Guarda los estados en el archivo JSON.

        Raises:
            Exception: Si hay error al guardar el archivo
        """
        try:
            with open(self.archivo_estados, 'w', encoding='utf-8') as f:
                json.dump(self.estados, f, indent=2, ensure_ascii=False)
            logger.debug(f"💾 Estados guardados en {self.archivo_estados}")

        except Exception as e:
            logger.error(f"❌ Error al guardar estados: {e}")
            raise

    def inicializar_expedientes(
        self,
        numeros_expedientes: list[str],
        estado_inicial: EstadoExpediente = EstadoExpediente.PENDIENTE_REVISION,
        auto_guardar: bool = False
    ) -> int:
        """Inicializa expedientes nuevos con un estado inicial.

        No sobrescribe expedientes que ya tienen estado.

        Args:
            numeros_expedientes: Lista de números de expedientes
            estado_inicial: Estado inicial para expedientes nuevos
            auto_guardar: Si True, guarda automáticamente tras inicializar

        Returns:
            Cantidad de expedientes nuevos inicializados
        """
        inicializados = 0
        timestamp = datetime.now().isoformat()

        for numero in numeros_expedientes:
            if numero not in self.estados:
                self.estados[numero] = {
                    "estado": str(estado_inicial),
                    "fecha_registro": timestamp,
                    "fecha_actualizacion": timestamp,
                    "intentos": 0,
                    "notas": []
                }
                inicializados += 1

        if auto_guardar and inicializados > 0:
            self.guardar_estados()

        return inicializados

    def actualizar_estado(
        self,
        numero_expediente: str,
        nuevo_estado: EstadoExpediente,
        nota: str | None = None,
        auto_guardar: bool = False
    ) -> None:
        """Actualiza el estado de un expediente.

        Args:
            numero_expediente: Número del expediente
            nuevo_estado: Nuevo estado a asignar
            nota: Nota opcional para agregar al historial
            auto_guardar: Si True, guarda automáticamente tras actualizar
        """
        if numero_expediente not in self.estados:
            # Inicializar si no existe
            self.estados[numero_expediente] = {
                "estado": str(nuevo_estado),
                "fecha_registro": datetime.now().isoformat(),
                "fecha_actualizacion": datetime.now().isoformat(),
                "intentos": 0,
                "notas": []
            }
        else:
            self.estados[numero_expediente]["estado"] = str(nuevo_estado)
            self.estados[numero_expediente]["fecha_actualizacion"] = datetime.now().isoformat()

        if nota:
            if "notas" not in self.estados[numero_expediente]:
                self.estados[numero_expediente]["notas"] = []
            self.estados[numero_expediente]["notas"].append({
                "timestamp": datetime.now().isoformat(),
                "nota": nota
            })

        if auto_guardar:
            self.guardar_estados()

    def obtener_estado(self, numero_expediente: str) -> EstadoExpediente | None:
        """Obtiene el estado actual de un expediente.

        Args:
            numero_expediente: Número del expediente

        Returns:
            Estado del expediente o None si no existe
        """
        if numero_expediente not in self.estados:
            return None

        estado_str = self.estados[numero_expediente].get("estado")
        try:
            return EstadoExpediente(estado_str)
        except ValueError:
            logger.warning(f"⚠️  Estado inválido para expediente {numero_expediente}: {estado_str}")
            return None

    def obtener_expedientes_activos(self) -> list[str]:
        """Obtiene lista de expedientes con estados activos.

        Returns:
            Lista de números de expedientes activos
        """
        estados_activos = [str(e) for e in EstadoExpediente.estados_activos()]

        return [
            numero
            for numero, datos in self.estados.items()
            if datos.get("estado") in estados_activos
        ]

    def obtener_expedientes_por_estado(self, estado: EstadoExpediente) -> list[str]:
        """Obtiene expedientes con un estado específico.

        Args:
            estado: Estado a filtrar

        Returns:
            Lista de números de expedientes con ese estado
        """
        estado_str = str(estado)

        return [
            numero
            for numero, datos in self.estados.items()
            if datos.get("estado") == estado_str
        ]

    def obtener_resumen(self) -> dict[str, Any]:
        """Genera un resumen de estados.

        Returns:
            Diccionario con conteos por estado y totales
        """
        resumen: dict[str, Any] = {
            "total": len(self.estados),
            "por_estado": {},
            "activos": 0,
            "finales": 0
        }

        estados_activos = [str(e) for e in EstadoExpediente.estados_activos()]
        estados_finales = [str(e) for e in EstadoExpediente.estados_finales()]

        for datos in self.estados.values():
            estado = datos.get("estado", "desconocido")
            resumen["por_estado"][estado] = resumen["por_estado"].get(estado, 0) + 1

            if estado in estados_activos:
                resumen["activos"] += 1
            elif estado in estados_finales:
                resumen["finales"] += 1

        return resumen

    def incrementar_intentos(self, numero_expediente: str) -> int:
        """Incrementa el contador de intentos de un expediente.

        Args:
            numero_expediente: Número del expediente

        Returns:
            Nuevo contador de intentos
        """
        if numero_expediente in self.estados:
            self.estados[numero_expediente]["intentos"] = \
                self.estados[numero_expediente].get("intentos", 0) + 1
            return self.estados[numero_expediente]["intentos"]
        return 0
