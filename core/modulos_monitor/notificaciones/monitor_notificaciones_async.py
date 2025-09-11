
import sys
import os
import json
import asyncio
from datetime import datetime
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer, QThread, Signal
from web.auto_login import reutilizar_sesion_async, SESSION_FILE

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config_monitor.json")

def cargar_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️ Error al cargar configuración: {e}")
        return {
            "modo": "automatico",
            "horario_laboral": {
                "dias": ["lunes", "martes", "miércoles", "jueves", "viernes"],
                "hora_inicio": "07:00",
                "hora_fin": "20:00",
                "intervalo_minutos": 30
            },
            "fuera_horario": {
                "intervalo_minutos": 240
            }
        }

def esta_en_horario_laboral(config):
    ahora = datetime.now()
    dia_actual = ahora.strftime("%A").lower()
    dias = [d.lower() for d in config["horario_laboral"]["dias"]]
    hora_inicio = datetime.strptime(config["horario_laboral"]["hora_inicio"], "%H:%M").time()
    hora_fin = datetime.strptime(config["horario_laboral"]["hora_fin"], "%H:%M").time()
    return dia_actual in dias and hora_inicio <= ahora.time() <= hora_fin

def obtener_intervalo(config):
    modo = config.get("modo", "automatico").lower()
    if modo == "laboral":
        return config["horario_laboral"]["intervalo_minutos"]
    elif modo == "nolaboral":
        return config["fuera_horario"]["intervalo_minutos"]
    elif modo == "automatico":
        if esta_en_horario_laboral(config):
            return config["horario_laboral"]["intervalo_minutos"]
        else:
            return config["fuera_horario"]["intervalo_minutos"]
    return 60

class VerificadorAsync(QThread):
    resultado = Signal(object)

    def run(self):
        asyncio.run(self.verificar_async())

    async def verificar_async(self):
        async with reutilizar_sesion_async() as (page, _, _):
            if page:
                from notificaciones_v2.notificaciones_control_v4_async import actualizar_notificaciones_nuevas
                nuevas = await actualizar_notificaciones_nuevas(page)
                self.resultado.emit(nuevas)
            else:
                self.resultado.emit(None)

class MonitorNotificaciones:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.tray = QSystemTrayIcon()

        icon_path = os.path.join(os.path.dirname(__file__), "icono.png")
        if os.path.exists(icon_path):
            self.tray.setIcon(QIcon(icon_path))
        else:
            self.tray.setIcon(QIcon.fromTheme("applications-system"))

        self.tray.setVisible(True)
        self.menu = QMenu()

        self.config = cargar_config()
        self.temporizador = QTimer()
        self.temporizador.timeout.connect(self.verificar)

        accion_verificar = QAction("✅ Verificar Ahora")
        accion_verificar.triggered.connect(self.verificar)
        self.menu.addAction(accion_verificar)

        accion_estado = QAction("ℹ️ Estado Actual")
        accion_estado.triggered.connect(self.mostrar_estado)
        self.menu.addAction(accion_estado)

        self.menu.addSeparator()

        self.submenu_modo = QMenu("🛠️ Modo de Trabajo")
        self.accion_modo_automatico = QAction("Automático", checkable=True)
        self.accion_modo_laboral = QAction("Laboral", checkable=True)
        self.accion_modo_nolaboral = QAction("No Laboral", checkable=True)

        self.accion_modo_automatico.triggered.connect(lambda: self.cambiar_modo("automatico"))
        self.accion_modo_laboral.triggered.connect(lambda: self.cambiar_modo("laboral"))
        self.accion_modo_nolaboral.triggered.connect(lambda: self.cambiar_modo("nolaboral"))

        self.submenu_modo.addAction(self.accion_modo_automatico)
        self.submenu_modo.addAction(self.accion_modo_laboral)
        self.submenu_modo.addAction(self.accion_modo_nolaboral)
        self.menu.addMenu(self.submenu_modo)

        self.menu.addSeparator()

        accion_forzar_login = QAction("⚠️ Forzar nuevo login")
        accion_forzar_login.triggered.connect(self.forzar_nuevo_login)
        self.menu.addAction(accion_forzar_login)

        accion_salir = QAction("🛑 Salir")
        accion_salir.triggered.connect(self.salir)
        self.menu.addAction(accion_salir)

        self.tray.setContextMenu(self.menu)

        self.actualizar_modo_seleccionado()
        self.iniciar_temporizador()

        sys.exit(self.app.exec())

    def actualizar_modo_seleccionado(self):
        modo = self.config.get("modo", "automatico")
        self.accion_modo_automatico.setChecked(modo == "automatico")
        self.accion_modo_laboral.setChecked(modo == "laboral")
        self.accion_modo_nolaboral.setChecked(modo == "nolaboral")

    def cambiar_modo(self, nuevo_modo):
        self.config["modo"] = nuevo_modo
        self.actualizar_modo_seleccionado()
        print(f"🔄 Modo cambiado a: {nuevo_modo}")
        self.temporizador.stop()
        self.iniciar_temporizador()

    def iniciar_temporizador(self):
        intervalo = obtener_intervalo(self.config)
        print(f"⏱️ Intervalo configurado: {intervalo} minutos")
        self.temporizador.start(intervalo * 60 * 1000)
        self.verificar()

    def verificar(self):
        print(f"🔍 Verificando notificaciones... {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.hilo_verificacion = VerificadorAsync()
        self.hilo_verificacion.resultado.connect(self.procesar_resultado_verificacion)
        self.hilo_verificacion.start()

    def procesar_resultado_verificacion(self, nuevas):
        if nuevas is not None:
            if nuevas > 0:
                self.tray.showMessage("🔔 Notificaciones", f"{nuevas} nuevos expedientes detectados.")
            else:
                print("✅ No hay nuevas notificaciones.")
        else:
            print("❌ No se pudo verificar notificaciones.")

    def mostrar_estado(self):
        intervalo = obtener_intervalo(self.config)
        modo = self.config.get("modo", "desconocido").capitalize()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        mensaje = f"🕒 Modo: {modo}\nIntervalo: {intervalo} minutos\nAhora: {ahora}"
        self.tray.showMessage("ℹ️ Estado del Monitor", mensaje)

    def salir(self):
        print("🛑 Saliendo del monitor...")
        self.tray.hide()
        self.app.quit()

    def forzar_nuevo_login(self):
        try:
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
                print("🗑️ Archivo de sesión eliminado correctamente.")
                self.tray.showMessage("Login forzado", "✅ Se eliminó el archivo de sesión. El próximo login será completo.")
            else:
                print("ℹ️ No hay archivo de sesión guardado.")
                self.tray.showMessage("Login forzado", "ℹ️ No se encontró una sesión guardada.")
        except Exception as e:
            print(f"❌ Error al eliminar la sesión: {e}")
            self.tray.showMessage("Login forzado", f"❌ Error al eliminar la sesión: {e}")

if __name__ == "__main__":
    MonitorNotificaciones()
