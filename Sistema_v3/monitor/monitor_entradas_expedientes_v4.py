"""Monitor de expedientes basado en bandeja del sistema.

Este módulo es una versión simplificada enfocada exclusivamente en la
verificación periódica de expedientes del PJN. Las utilidades
adicionales disponibles en versiones previas (entradas, comparación,
respaldos, etc.) se reincorporarán en iteraciones futuras.
"""

from __future__ import annotations

import base64
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

try:
    from .icono_base64 import ICONO_BASE64
except ImportError:  # pragma: no cover - ejecución directa
    from icono_base64 import ICONO_BASE64

try:  # Importa primero desde la nueva arquitectura (Sistema_v4)
    from Sistema_v4.config.urls_pjn import URL_CONSULTAS  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - compatibilidad con Sistema_v3
    from Sistema_v3.config.urls_pjn import URL_CONSULTAS

try:
    from Sistema_v4.operaciones.expedientes.expedientes_v4 import (  # type: ignore[import-not-found]
        extraer_expedientes_completos,
    )
except ImportError:  # pragma: no cover - compatibilidad con Sistema_v3
    from Sistema_v3.operaciones.expedientes.expedientes_v4 import (
        extraer_expedientes_completos,
    )

try:
    from Sistema_v4.utils.logging import registrar_log  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - compatibilidad con Sistema_v3
    from Sistema_v3.utils.logging import registrar_log

try:
    from Sistema_v4.web.auto_login import (  # type: ignore[import-not-found]
        reutilizar_sesion_async,
    )
except ImportError:  # pragma: no cover - compatibilidad con Sistema_v3
    from Sistema_v3.web.auto_login import reutilizar_sesion_async


@dataclass
class ResultadoExpedientes:
    estado: str
    cantidad: int | None = None
    ruta: str | None = None
    error: str | None = None


CONFIG_PATH = Path("config/config_monitor.json")
DEFAULT_CONFIG = {
    "modo": "automatico",
    "horario_laboral": {
        "dias": ["lunes", "martes", "miércoles", "jueves", "viernes"],
        "hora_inicio": "07:00",
        "hora_fin": "20:00",
        "intervalo_minutos": 30,
    },
    "fuera_horario": {"intervalo_minutos": 240},
}


class VerificadorExpedientesV4(QThread):
    """Hilo encargado de recuperar el listado completo de expedientes."""

    resultado = Signal(object)

    def __init__(
        self,
        carpeta_salida: str | Path = "datos_extraidos/monitoreo",
        nombre_archivo: str = "expedientes_monitor.json",
        guardar_json: bool = True,
    ) -> None:
        super().__init__()
        self.carpeta_salida = Path(carpeta_salida)
        self.nombre_archivo = nombre_archivo
        self.guardar_json = guardar_json

    def run(self) -> None:  # type: ignore[override]
        import asyncio

        asyncio.run(self._verificar_async())

    async def _verificar_async(self) -> None:
        try:
            async with reutilizar_sesion_async() as (page, _context, _browser):
                if not page:
                    self.resultado.emit(ResultadoExpedientes(estado="fallo"))
                    return

                await page.goto(URL_CONSULTAS)
                expedientes, motivo = await extraer_expedientes_completos(
                    page, orden="fecha"
                )

                ruta_archivo: Path | None = None
                if self.guardar_json:
                    ruta_archivo = self._guardar_resultados(expedientes)

                motivos_exitosos = {"fin_listado", "sin_siguiente", "sin_siguiente_habilitado"}
                estado_resultado = "completo" if motivo in motivos_exitosos else motivo

                self.resultado.emit(
                    ResultadoExpedientes(
                        estado=estado_resultado,
                        cantidad=len(expedientes),
                        ruta=str(ruta_archivo) if ruta_archivo else None,
                    )
                )
        except Exception as exc:  # pragma: no cover - logging de errores
            registrar_log(f"❌ Error crítico en hilo de expedientes: {exc}")
            self.resultado.emit(
                ResultadoExpedientes(estado="fallo", error=str(exc))
            )

    def _guardar_resultados(self, expedientes: list[dict]) -> Path:
        self.carpeta_salida.mkdir(parents=True, exist_ok=True)
        ruta = self.carpeta_salida / self.nombre_archivo
        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(expedientes, archivo, ensure_ascii=False, indent=2)
        return ruta


class MonitorExpedientesTray:
    """Crea un icono en la bandeja del sistema para monitorear expedientes."""

    def __init__(self) -> None:
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        if not QSystemTrayIcon.isSystemTrayAvailable():
            registrar_log("❌ La bandeja del sistema no está disponible. La aplicación se cerrará.")
            QMessageBox.critical(None, "Error", "La bandeja del sistema no está disponible.")
            sys.exit(1)

        self.tray = QSystemTrayIcon(self._crear_icono())
        self.tray.setToolTip("Monitor de Expedientes PJN")
        self.tray.setVisible(True)

        self.menu = QMenu()
        self.menu.addAction("📥 Verificar Expedientes").triggered.connect(
            self.verificar_expedientes
        )

        # Espacio reservado para herramientas adicionales. Se reintroducirán
        # en futuras versiones una vez finalizada la migración a v4.
        placeholder = QAction("🛠️ Utilidades adicionales (próximamente)")
        placeholder.setEnabled(False)
        self.menu.addAction(placeholder)

        self.menu.addSeparator()
        self.menu.addAction("🛑 Salir").triggered.connect(self.salir)
        self.tray.setContextMenu(self.menu)

        self.config = self.cargar_config()
        self.hilo_expedientes: VerificadorExpedientesV4 | None = None
        self.ejecutando_expedientes = False
        self.reintentos_expedientes = 0

        self.timer_expedientes = QTimer()
        self.timer_expedientes.timeout.connect(self.verificar_expedientes)

        self.iniciar_temporizador()
        sys.exit(self.app.exec())

    @staticmethod
    def _crear_icono() -> QIcon:
        pixmap = QPixmap()
        if not pixmap.loadFromData(base64.b64decode(ICONO_BASE64)):
            registrar_log("⚠️ Icono incrustado inválido, usando icono por defecto")
            return QIcon()
        return QIcon(pixmap)

    def cargar_config(self) -> dict:
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except Exception:
            datos = json.loads(json.dumps(DEFAULT_CONFIG))

        datos.setdefault("modo", DEFAULT_CONFIG["modo"])
        datos.setdefault("horario_laboral", DEFAULT_CONFIG["horario_laboral"])
        datos.setdefault("fuera_horario", DEFAULT_CONFIG["fuera_horario"])
        return datos

    def esta_en_horario_laboral(self) -> bool:
        ahora = datetime.now()
        dia_actual = ahora.strftime("%A").lower()
        dias = [d.lower() for d in self.config["horario_laboral"]["dias"]]
        hora_inicio = datetime.strptime(
            self.config["horario_laboral"]["hora_inicio"], "%H:%M"
        ).time()
        hora_fin = datetime.strptime(
            self.config["horario_laboral"]["hora_fin"], "%H:%M"
        ).time()
        return dia_actual in dias and hora_inicio <= ahora.time() <= hora_fin

    def obtener_intervalo(self) -> int:
        modo = self.config.get("modo", "automatico")
        if modo == "laboral":
            return self.config["horario_laboral"]["intervalo_minutos"]
        if modo == "no_laboral":
            return self.config["fuera_horario"]["intervalo_minutos"]
        if modo == "automatico":
            return (
                self.config["horario_laboral"]["intervalo_minutos"]
                if self.esta_en_horario_laboral()
                else self.config["fuera_horario"]["intervalo_minutos"]
            )
        return 60

    def iniciar_temporizador(self) -> None:
        intervalo = self.obtener_intervalo()
        self.timer_expedientes.start(intervalo * 60 * 1000)
        self.verificar_expedientes()

    def verificar_expedientes(self) -> None:
        if self.ejecutando_expedientes:
            registrar_log("⏳ Verificación de expedientes ya en curso.")
            return

        self.ejecutando_expedientes = True
        carpeta = Path(os.getcwd()) / "datos_extraidos" / "monitoreo"
        self.hilo_expedientes = VerificadorExpedientesV4(carpeta_salida=carpeta)
        self.hilo_expedientes.resultado.connect(self.procesar_resultado_expedientes)
        self.hilo_expedientes.finished.connect(self._limpiar_hilo_expedientes)
        self.hilo_expedientes.start()

    def _limpiar_hilo_expedientes(self) -> None:
        if self.hilo_expedientes:
            self.hilo_expedientes.deleteLater()
            self.hilo_expedientes = None
        self.ejecutando_expedientes = False

    def procesar_resultado_expedientes(self, datos: ResultadoExpedientes) -> None:
        mensajes = {
            "completo": "✅ Extracción finalizada exitosamente.",
            "fallo": "❌ Fallo en la verificación.",
        }

        registrar_log(f"📦 Estado: {datos.estado}")
        registrar_log(mensajes.get(datos.estado, "❓ Estado no reconocido."))

        if datos.cantidad is not None:
            registrar_log(f"📊 Total extraídos: {datos.cantidad}")
            self.tray.showMessage(
                "📥 Expedientes",
                f"{datos.cantidad} expedientes actualizados.",
            )
        if datos.ruta:
            registrar_log(f"📁 Guardado en: {datos.ruta}")
        if datos.error:
            registrar_log(f"🛑 Error: {datos.error}")

        if datos.estado != "completo":
            self.reintentos_expedientes += 1
            if self.reintentos_expedientes < 5:
                registrar_log(
                    f"🔁 Reintentando verificación ({self.reintentos_expedientes}/5) en 5 segundos..."
                )
                QTimer.singleShot(5000, self.verificar_expedientes)
            else:
                registrar_log(
                    "❌ Se alcanzó el límite de reintentos. No se pudo completar la verificación."
                )
        else:
            self.reintentos_expedientes = 0

    def salir(self) -> None:
        self.tray.hide()
        self.app.quit()


if __name__ == "__main__":
    MonitorExpedientesTray()
