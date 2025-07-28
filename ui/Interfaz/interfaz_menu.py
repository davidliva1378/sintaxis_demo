from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QMessageBox
import sys


class MenuPrincipal(QMainWindow):
    """Ventana principal con opciones de navegación."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Menú Principal")
        self.setGeometry(100, 100, 400, 300)

        layout = QVBoxLayout()

        self.btn_expedientes = QPushButton("Expedientes")
        self.btn_expedientes.clicked.connect(lambda: self._mostrar_mensaje("Expedientes"))
        layout.addWidget(self.btn_expedientes)

        self.btn_actuaciones = QPushButton("Actuaciones")
        self.btn_actuaciones.clicked.connect(lambda: self._mostrar_mensaje("Actuaciones"))
        layout.addWidget(self.btn_actuaciones)

        self.btn_notificaciones = QPushButton("Notificaciones")
        self.btn_notificaciones.clicked.connect(lambda: self._mostrar_mensaje("Notificaciones"))
        layout.addWidget(self.btn_notificaciones)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def _mostrar_mensaje(self, opcion: str) -> None:
        """Muestra un mensaje de información al usuario."""
        QMessageBox.information(self, opcion, f"Se seleccionó la opción '{opcion}'.")


def main() -> None:
    """Ejecuta la aplicación de ejemplo."""
    app = QApplication(sys.argv)
    window = MenuPrincipal()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
