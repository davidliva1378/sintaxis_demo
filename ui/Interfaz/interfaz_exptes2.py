from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QFrame)
from PySide6.QtGui import QFont
import sys


class ExpedienteTouchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Expediente - Vista Touch")
        self.setGeometry(100, 100, 1920, 1080)

        layout = QVBoxLayout()

        # Título
        self.titulo_label = QLabel("📂 Expediente: FPA 19049/2017")
        self.titulo_label.setFont(QFont("Arial", 24, QFont.Bold))
        layout.addWidget(self.titulo_label)

        # Información del expediente
        info_layout = QVBoxLayout()
        detalles = [
            "Carátula: ROJAS, JUAN JOSE Y OTROS c/ ESTADO NACIONAL...",
            "Tipo de Proceso: Amparo",
            "Instancia: Primera",
            "Situación: En trámite",
            "Fecha de Inicio: 10/01/2024",
            "Última Actuación: 28/02/2025",
            "Jurisdicción: Justicia Federal",
            "Dependencia: Juzgado Federal Nº 1"
        ]

        for detalle in detalles:
            label = QLabel(detalle)
            label.setFont(QFont("Arial", 18))
            label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
            label.setStyleSheet("padding: 10px; background-color: #F4F4F4; border-radius: 10px;")
            info_layout.addWidget(label)

        layout.addLayout(info_layout)

        # Botones de acción grandes para pantallas touch
        button_layout = QHBoxLayout()

        editar_button = QPushButton("✏️ Editar")
        exportar_button = QPushButton("📄 Exportar PDF")
        cerrar_button = QPushButton("❌ Cerrar")

        for button in [editar_button, exportar_button, cerrar_button]:
            button.setFont(QFont("Arial", 18, QFont.Bold))
            button.setStyleSheet("padding: 20px; background-color: #007BFF; color: white; border-radius: 10px;")
            button_layout.addWidget(button)

        layout.addLayout(button_layout)
        self.setLayout(layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExpedienteTouchApp()
    window.show()
    sys.exit(app.exec())
