import sys
import os
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer
from datetime import datetime
from web.auto_login import reutilizar_sesion
from notificaciones_v2.notificaciones_control_v4_async import actualizar_notificaciones_nuevas

class MonitorNotificaciones:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.tray = QSystemTrayIcon()

        icon_path = os.path.join(os.path.dirname(__file__), "icono.png")
        if os.path.exists(icon_path):
            self.tray.setIcon(QIcon(icon_path))
            print("🖼️ Icono personalizado cargado correctamente.")
        else:
            self.tray.setIcon(QIcon.fromTheme("applications-system"))
            print("⚠️ Icono personalizado no encontrado. Se usará el ícono por defecto.")

        self.tray.setVisible(True)
        print("✅ Icono de bandeja creado correctamente")

        self.menu = QMenu()
        accion_verificar = QAction("✅ Verificar Ahora")
        accion_verificar.triggered.connect(self.verificar)
        self.menu.addAction(accion_verificar)

        self.menu.addSeparator()

        accion_salir = QAction("🛑 Salir")
        accion_salir.triggered.connect(self.salir)
        self.menu.addAction(accion_salir)

        self.tray.setContextMenu(self.menu)

        self.temporizador = QTimer()
        self.temporizador.timeout.connect(self.verificar)
        self.temporizador.start(10 * 60 * 1000)
        print("🔁 Temporizador iniciado: verificación cada 10 minutos")

        print("🚀 Ejecutando aplicación de monitoreo")
        sys.exit(self.app.exec())

    def verificar(self):
        print(f"🔍 Verificando notificaciones... ({datetime.now().strftime('%H:%M:%S')})")
        page = reutilizar_sesion()
        if page:
            nuevas = actualizar_notificaciones_nuevas(page)
            if nuevas > 0:
                self.tray.showMessage("🔔 Notificaciones", f"{nuevas} nuevas notificaciones detectadas.")

    def salir(self):
        print("🛑 Saliendo del monitor_borrar...")
        self.tray.hide()
        self.app.quit()

if __name__ == "__main__":
    MonitorNotificaciones()