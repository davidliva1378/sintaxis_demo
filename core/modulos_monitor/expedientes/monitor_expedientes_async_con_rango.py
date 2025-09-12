import asyncio
import json
import sys
from PySide6.QtCore import QThread, Signal, QTimer, Qt
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QWidget
from PySide6.QtGui import QIcon
from panel_pjn.acciones_pjn.urls_pjn import URL_CONSULTAS
from core.modulos_monitor.expedientes_modular.extraer_expedientes import extraer_expedientes
from web.auto_login import reutilizar_sesion_async
from monitoreo_automatico_habilitado import monitoreo_automatico_habilitado
from core.utils.logging import registrar_log

class VerificadorAsync(QThread):
    resultado = Signal(object)

    def run(self):
        asyncio.run(self.verificar_async())

    async def verificar_async(self):
        registrar_log("🔍 Iniciando verificación de expedientes...")
        try:
            async with reutilizar_sesion_async() as (page, context, browser):
                await page.goto(URL_CONSULTAS)
                registrar_log("🌐 Navegación a consultas realizada.")
                expedientes, ruta, estado = await extraer_expedientes(
                    page,
                    carpeta_salida="datos_iniciales/",
                    nombre_archivo="expedientes_monitor.json",
                    detener_en_duplicado=True,
                    guardar_json=True,
                    tiempo_maximo_segundos=None
                )
                resultado = {
                    "estado": estado,
                    "ruta": ruta,
                    "cantidad": len(expedientes)
                }
                self.resultado.emit(resultado)

        except Exception as e:
            registrar_log(f"❌ Error en verificación: {e}")
            self.resultado.emit({"error": str(e)})

class MonitorExpedientes(QSystemTrayIcon):
    def __init__(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            registrar_log("❌ La bandeja del sistema no está disponible. La aplicación se cerrará.")
            QMessageBox.critical(None, "Error", "La bandeja del sistema no está disponible.")
            sys.exit(1)
        super().__init__()
        self.setIcon(QIcon("icono.ico"))
        self.setToolTip("Monitor de Expedientes")
        self.menu = QMenu()
        self.menu.addAction("🔄 Verificar ahora", self.verificar)
        self.menu.addAction("🔐 Estado de sesión", self.ver_estado_sesion)
        self.menu.addSeparator()
        self.menu.addAction("⏹️ Salir", QApplication.quit)
        self.setContextMenu(self.menu)
        self.show()
        registrar_log("🟢 Monitor de expedientes iniciado correctamente.")
        intervalo = 30 * 60 * 1000  # 30 minutos en milisegundos
        self.timer = QTimer()
        self.timer.timeout.connect(self.verificar_automaticamente)
        self.timer.start(intervalo)


    
    def verificar_automaticamente(self):
        if monitoreo_automatico_habilitado():
            registrar_log("⏰ Ejecutando verificación automática dentro del horario habilitado.")
            self.verificar()
        else:
            registrar_log("⏳ Horario o día no habilitado. No se ejecuta verificación automática.")

    def verificar(self):
        registrar_log("🕵️‍♂️ Acción: Verificar ahora")
        self.reintentos = 0
        self.iniciar_verificacion()

    def iniciar_verificacion(self):
        self.verificador = VerificadorAsync()
        self.verificador.resultado.connect(self.procesar_resultado)
        self.verificador.start()

    def procesar_resultado(self, datos):
        estado = datos.get("estado", "desconocido")
        mensajes = {
            "completo": "✅ Extracción finalizada exitosamente.",
            "repetido_detectado": "⚠️ Se detectó repetición de expedientes. La extracción se interrumpió.",
            "tiempo_maximo": "⏱ Se alcanzó el tiempo máximo permitido.",
            "tabla_no_disponible": "❌ No se encontró la tabla de expedientes en la página.",
            "desconocido": "❓ Estado de extracción no reconocido."
        }

        registrar_log(f"📦 Estado: {estado}")
        registrar_log(f"{mensajes.get(estado, mensajes['desconocido'])}")

        if "cantidad" in datos:
            registrar_log(f"📊 Total extraídos: {datos['cantidad']}")

        if datos.get("ruta"):
            registrar_log(f"📁 Guardado en: {datos['ruta']}")

        if estado != "completo":
            self.reintentos += 1
            if self.reintentos < 5:
                registrar_log(f"🔁 Reintentando verificación ({self.reintentos}/5) en 5 segundos...")
                QTimer.singleShot(5000, self.iniciar_verificacion)
            else:
                registrar_log("❌ Se alcanzó el límite de reintentos. No se pudo completar la verificación.")
        else:
            self.reintentos = 0

    def ver_estado_sesion(self):
        estado = "❌ No verificado"
        try:
            with open("estado_sesion.json", "r", encoding="utf-8") as f:
                datos = json.load(f)
                if "cookies" in datos and any("pjn.gov.ar" in c.get("domain", "") for c in datos["cookies"]):
                    estado = "🟢 Sesión activa y válida"
                else:
                    estado = "⚠️ Sesión incompleta"
        except Exception:
            estado = "❌ Archivo de sesión no encontrado o ilegible"

        ventana = QWidget()
        ventana.setWindowFlag(Qt.WindowType.Tool)
        ventana.hide()

        QMessageBox.information(
            ventana,
            "Estado de Sesión",
            estado,
            QMessageBox.StandardButton.Ok
        )

if __name__ == "__main__":
    app = QApplication([])
    tray = MonitorExpedientes()
    QMessageBox.information(None, "Monitor de Expedientes", "🟢 Monitor activo con verificación habilitada.")
    app.exec()