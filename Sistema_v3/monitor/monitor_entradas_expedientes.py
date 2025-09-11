import sys
import os
import json
import base64
from datetime import datetime
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QWidget
from PySide6.QtGui import QIcon, QAction, QPixmap
from PySide6.QtCore import QTimer, QThread, Signal, Qt

from .icono_base64 import ICONO_BASE64
from Sistema_v3.web.auto_login import reutilizar_sesion_async, SESSION_FILE
from urls_pjn import URL_CONSULTAS
from Sistema_v3.operaciones.expedientes.ref_expedientes import (
    extraer_expedientes,
)
from Sistema_v3.operaciones.entradas.extractor_entradas import (
    extraer_entradas_pjn,
)
from core.utils.logging import registrar_log
from core.gestion_expedientes.comparar_expedientes_monitor import (
    comparar_expedientes_monitor,
)

CONFIG_PATH = "config/config_monitor.json"


class VerificadorExpedientesV3(QThread):
    resultado = Signal(object)

    def __init__(self, carpeta_salida: str = "datos_extraidos/monitoreo"):
        super().__init__()
        self.carpeta_salida = carpeta_salida

    def run(self) -> None:  # type: ignore[override]
        import asyncio

        asyncio.run(self.verificar_async())

    async def verificar_async(self) -> None:
        try:
            async with reutilizar_sesion_async() as (page, context, browser):
                if page:
                    await page.goto(URL_CONSULTAS)
                    expedientes, ruta, estado = await extraer_expedientes(
                        page,
                        carpeta_salida=self.carpeta_salida,
                        nombre_archivo="expedientes_monitor.json",
                        detener_en_duplicado=True,
                        guardar_json=True,
                    )
                    self.resultado.emit(
                        {"estado": estado, "cantidad": len(expedientes), "ruta": ruta}
                    )
                else:
                    self.resultado.emit({"estado": "fallo"})
        except Exception as e:  # pragma: no cover - logging de errores
            registrar_log(f"❌ Error crítico en hilo de expedientes: {e}")
            self.resultado.emit({"estado": "fallo", "error": str(e)})


class VerificadorEntradasV3(QThread):
    resultado = Signal(object)

    def run(self) -> None:  # type: ignore[override]
        import asyncio

        asyncio.run(self.verificar_async())

    async def verificar_async(self) -> None:
        try:
            async with reutilizar_sesion_async() as (page, context, browser):
                if page:
                    destino = os.path.abspath(
                        os.path.join(os.getcwd(), "datos_extraidos", "monitoreo")
                    )
                    nuevas = await extraer_entradas_pjn(page, destino=destino)
                    self.resultado.emit(nuevas)
                else:
                    self.resultado.emit(None)
        except Exception as e:  # pragma: no cover - logging de errores
            registrar_log(f"❌ Error en verificación de entradas: {e}")
            self.resultado.emit(None)


class MonitorEntradasExpedientes:
    def __init__(self) -> None:
        self.app = QApplication(sys.argv)
        pixmap = QPixmap()
        if not pixmap.loadFromData(base64.b64decode(ICONO_BASE64)):
            registrar_log("⚠️ icono incrustado inválido, usando icono por defecto")
            icono = QIcon()
        else:
            icono = QIcon(pixmap)
        self.tray = QSystemTrayIcon(icono)
        self.tray.setToolTip("Monitor Expedientes/Entradas PJN")
        self.tray.setVisible(True)

        self.menu = QMenu()
        self.menu.addAction("📥 Verificar Expedientes").triggered.connect(
            self.verificar_expedientes
        )
        self.menu.addAction("📤 Verificar Entradas").triggered.connect(
            self.verificar_entradas
        )
        self.menu.addAction("🔐 Estado de Sesión").triggered.connect(self.estado_sesion)
        self.menu.addAction("🧪 Comparar Expedientes").triggered.connect(
            self.comparar_expedientes
        )
        self.menu.addAction(
            "🗂 Copiar últimos resultados a histórico"
        ).triggered.connect(self.respaldar_resultados)
        self.submenu_modo = QMenu("🛠️ Modo de Trabajo")
        for modo in ["automatico", "laboral", "no_laboral"]:
            nombre_visible = modo.replace("_", " ").capitalize()
            accion = QAction(nombre_visible, checkable=True)
            accion.setData(modo)
            accion.triggered.connect(
                lambda checked, a=accion: self.cambiar_modo(a.data())
            )
            self.submenu_modo.addAction(accion)
        self.menu.addMenu(self.submenu_modo)
        self.menu.addSeparator()
        self.menu.addAction("🛑 Salir").triggered.connect(self.salir)
        self.tray.setContextMenu(self.menu)

        self.config = self.cargar_config()
        self.actualizar_modo_seleccionado()

        self.timer_expedientes = QTimer()
        self.timer_expedientes.timeout.connect(self.verificar_expedientes)

        self.timer_entradas = QTimer()
        self.timer_entradas.timeout.connect(self.verificar_entradas)

        self.reintentos_expedientes = 0
        self.reintentos_entradas = 0
        self.ejecutando_expedientes = False
        self.ejecutando_entradas = False

        self.iniciar_temporizadores()
        sys.exit(self.app.exec())

    def cargar_config(self) -> dict:
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                datos = json.load(f)
                datos.setdefault("modo", "automatico")
                return datos
        except Exception:
            return {
                "modo": "automatico",
                "horario_laboral": {
                    "dias": ["lunes", "martes", "miércoles", "jueves", "viernes"],
                    "hora_inicio": "07:00",
                    "hora_fin": "20:00",
                    "intervalo_minutos": 30,
                },
                "fuera_horario": {"intervalo_minutos": 240},
            }

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
        elif modo == "no_laboral":
            return self.config["fuera_horario"]["intervalo_minutos"]
        elif modo == "automatico":
            return (
                self.config["horario_laboral"]["intervalo_minutos"]
                if self.esta_en_horario_laboral()
                else self.config["fuera_horario"]["intervalo_minutos"]
            )
        return 60

    def iniciar_temporizadores(self) -> None:
        intervalo = self.obtener_intervalo()
        self.timer_expedientes.start(intervalo * 60 * 1000)
        self.timer_entradas.start(intervalo * 60 * 1000)
        self.verificar_expedientes()
        self.verificar_entradas()

    def cambiar_modo(self, nuevo_modo: str) -> None:
        self.config["modo"] = nuevo_modo
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)
        self.actualizar_modo_seleccionado()
        self.timer_expedientes.stop()
        self.timer_entradas.stop()
        self.iniciar_temporizadores()

    def actualizar_modo_seleccionado(self) -> None:
        modo = self.config.get("modo", "automatico")
        for accion in self.submenu_modo.actions():
            accion.setChecked(accion.data() == modo)

    def verificar_expedientes(self) -> None:
        if self.ejecutando_expedientes:
            registrar_log("⏳ Verificación de expedientes ya en curso.")
            return
        self.ejecutando_expedientes = True
        self.hilo_expedientes = VerificadorExpedientesV3(
            carpeta_salida=os.path.abspath(
                os.path.join(os.getcwd(), "datos_extraidos", "monitoreo")
            )
        )
        self.hilo_expedientes.finished.connect(self.hilo_expedientes.deleteLater)
        self.hilo_expedientes.resultado.connect(self.procesar_resultado_expedientes)
        self.hilo_expedientes.start()

    def verificar_entradas(self) -> None:
        if self.ejecutando_entradas:
            registrar_log("⏳ Verificación de entradas ya en curso.")
            return
        self.ejecutando_entradas = True
        self.hilo_entradas = VerificadorEntradasV3()
        self.hilo_entradas.finished.connect(self.hilo_entradas.deleteLater)
        self.hilo_entradas.resultado.connect(self.procesar_resultado_entradas)
        self.hilo_entradas.start()

    def procesar_resultado_expedientes(self, datos: dict) -> None:
        estado = datos.get("estado", "desconocido")
        mensajes = {
            "completo": "✅ Extracción finalizada exitosamente.",
            "repetido_detectado": "⚠️ Se detectó repetición de expedientes.",
            "tiempo_maximo": "⏱ Se alcanzó el tiempo máximo permitido.",
            "tabla_no_disponible": "❌ No se encontró la tabla de expedientes.",
            "corte_fecha": "📆 Se aplicó la fecha de corte.",
            "fallo": "❌ Fallo en la verificación.",
            "desconocido": "❓ Estado no reconocido.",
        }

        registrar_log(f"📦 Estado: {estado}")
        registrar_log(mensajes.get(estado, mensajes["desconocido"]))

        if datos.get("cantidad") is not None:
            registrar_log(f"📊 Total extraídos: {datos['cantidad']}")
        if datos.get("ruta"):
            registrar_log(f"📁 Guardado en: {datos['ruta']}")

        if estado not in ("completo", "corte_fecha"):
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

        self.ejecutando_expedientes = False

    def procesar_resultado_entradas(self, nuevas: int | None) -> None:
        if nuevas is not None:
            self.reintentos_entradas = 0
            if nuevas > 0:
                self.tray.showMessage("📤 Entradas", f"{nuevas} nuevas registradas.")
            else:
                self.tray.showMessage("📤 Entradas", "Sin nuevas entradas.")
        else:
            self.reintentos_entradas += 1
            if self.reintentos_entradas < 5:
                registrar_log(
                    f"🔁 Reintentando entradas ({self.reintentos_entradas}/5) en 5 segundos..."
                )
                QTimer.singleShot(5000, self.verificar_entradas)
            else:
                registrar_log("❌ Se alcanzó el límite de reintentos de entradas.")

        self.ejecutando_entradas = False

    def comparar_expedientes(self) -> None:
        """Compara el último archivo de expedientes con la base histórica."""
        try:
            base_dir = os.path.abspath(
                os.path.join(os.getcwd(), "datos_extraidos", "monitoreo")
            )
            ruta_actual = os.path.join(base_dir, "expedientes_monitor.json")
            ruta_base = os.path.join(base_dir, "expedientes_monitor - base.json")
            carpeta_salida = os.path.join(base_dir, "reportes")

            nuevos, modificados, eliminados = comparar_expedientes_monitor(
                ruta_actual, ruta_base, carpeta_salida
            )

            total = len(nuevos) + len(modificados) + len(eliminados)
            if total > 0:
                self.tray.showMessage(
                    "📊 Comparación de Expedientes",
                    f"{total} cambios detectados.",
                )
            else:
                self.tray.showMessage(
                    "📊 Comparación de Expedientes",
                    "Sin cambios detectados.",
                )
        except Exception as e:
            self.tray.showMessage(
                "❌ Error", f"No se pudo completar la comparación: {e}"
            )

    def respaldar_resultados(self) -> None:
        """Copia los últimos resultados de verificación a un histórico."""
        from datetime import datetime
        import shutil

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        destino = os.path.join("datos_extraidos", "monitoreo", "historico", timestamp)
        os.makedirs(destino, exist_ok=True)

        base_dir = os.path.join("datos_extraidos", "monitoreo")
        archivos = {
            os.path.join(
                base_dir, "expedientes_monitor.json"
            ): "expedientes_completo.json",
            os.path.join(
                base_dir, "historial_notificaciones.json"
            ): "notificaciones_completo.json",
        }

        for origen, nombre_destino in archivos.items():
            if os.path.exists(origen):
                shutil.copy(origen, os.path.join(destino, nombre_destino))
                print(f"✅ Copiado: {origen} → {nombre_destino}")
            else:
                print(f"⚠️ Archivo no encontrado: {origen}")

    def estado_sesion(self) -> None:
        estado = "❌ No verificado"
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                datos = json.load(f)
                if any(
                    "pjn.gov.ar" in c.get("domain", "")
                    for c in datos.get("cookies", [])
                ):
                    estado = "🟢 Sesión activa y válida"
                else:
                    estado = "⚠️ Sesión incompleta"
        except FileNotFoundError:
            estado = "❌ Archivo de sesión no encontrado"
        except json.JSONDecodeError:
            estado = "❌ Archivo de sesión ilegible"
        except Exception as e:
            estado = f"❌ Error inesperado: {e}"

        modo = self.config.get("modo", "automatico").replace("_", " ").capitalize()
        intervalo = self.obtener_intervalo()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        mensaje = (
            f"📅 Fecha y hora: {ahora}\n"
            f"🕒 Modo de trabajo actual: {modo}\n"
            f"⏱ Intervalo de verificación: {intervalo} minutos\n"
            f"{estado}"
        )

        ventana = QWidget()
        ventana.setWindowFlag(Qt.Tool)
        QMessageBox.information(ventana, "Estado del Monitor", mensaje)

    def salir(self) -> None:
        self.tray.hide()
        self.app.quit()


if __name__ == "__main__":
    MonitorEntradasExpedientes()
