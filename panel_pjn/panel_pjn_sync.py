import sys
import subprocess
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
import os

class PanelPJN(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Panel de Acceso - PJN")
        self.setGeometry(100, 100, 360, 400)

        layout = QVBoxLayout()

        scripts = {
            "🔍 Consultas": "acciones_pjn/abrir_consultas.py",
            "🔔 Notificaciones": "acciones_pjn/abrir_notificaciones.py",
            "📝 Escritos": "acciones_pjn/abrir_escritos.py",
            "📤 DEOX": "acciones_pjn/abrir_deox.py",
            "⚖️ IWECS": "acciones_pjn/abrir_iwecs.py",
            "👥 Autorizados": "acciones_pjn/abrir_autorizados.py"
        }

        for nombre, ruta in scripts.items():
            btn = QPushButton(nombre)
            btn.clicked.connect(lambda checked, ruta=ruta: self.abrir_script_externo(ruta))
            layout.addWidget(btn)

        contenedor = QWidget()
        contenedor.setLayout(layout)
        self.setCentralWidget(contenedor)

    def abrir_script_externo(self, ruta):
        if sys.platform.startswith("win"):
            subprocess.Popen(["start", "cmd", "/k", f"python {ruta}"], shell=True)
        else:
            subprocess.Popen(["x-terminal-emulator", "-e", f"python3 {ruta}"])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ventana = PanelPJN()
    ventana.show()
    sys.exit(app.exec())