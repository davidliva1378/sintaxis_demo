from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QTextEdit, QComboBox,
                               QPushButton, QFileDialog, QDateEdit, QHBoxLayout, QMessageBox)
from PySide6.QtCore import QDate
import sys


class ActuacionesApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Gestión de Actuaciones")
        self.setGeometry(100, 100, 500, 400)

        layout = QVBoxLayout()

        # Expediente
        self.expediente_label = QLabel("Expediente:")
        self.expediente_input = QLineEdit()
        layout.addWidget(self.expediente_label)
        layout.addWidget(self.expediente_input)

        # Oficina
        self.oficina_label = QLabel("Oficina:")
        self.oficina_input = QLineEdit()
        layout.addWidget(self.oficina_label)
        layout.addWidget(self.oficina_input)

        # Fecha
        self.fecha_label = QLabel("Fecha:")
        self.fecha_input = QDateEdit()
        self.fecha_input.setCalendarPopup(True)
        self.fecha_input.setDate(QDate.currentDate())
        layout.addWidget(self.fecha_label)
        layout.addWidget(self.fecha_input)

        # Tipo de Actuación
        self.tipo_label = QLabel("Tipo de Actuación:")
        self.tipo_input = QComboBox()
        self.tipo_input.addItems(["Demanda", "Notificación", "Oficio", "Presentación", "Otros"])
        layout.addWidget(self.tipo_label)
        layout.addWidget(self.tipo_input)

        # Detalle
        self.detalle_label = QLabel("Detalle:")
        self.detalle_input = QTextEdit()
        layout.addWidget(self.detalle_label)
        layout.addWidget(self.detalle_input)

        # Foja
        self.foja_label = QLabel("Foja:")
        self.foja_input = QLineEdit()
        layout.addWidget(self.foja_label)
        layout.addWidget(self.foja_input)

        # Archivo adjunto
        self.archivo_label = QLabel("Archivo:")
        self.archivo_button = QPushButton("Adjuntar Archivo")
        self.archivo_button.clicked.connect(self.seleccionar_archivo)
        layout.addWidget(self.archivo_label)
        layout.addWidget(self.archivo_button)

        # Botones de acción
        button_layout = QHBoxLayout()
        self.guardar_button = QPushButton("Guardar")
        self.cancelar_button = QPushButton("Cancelar")
        button_layout.addWidget(self.guardar_button)
        button_layout.addWidget(self.cancelar_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Conectar botones
        self.guardar_button.clicked.connect(self.guardar_actuacion)
        self.cancelar_button.clicked.connect(self.close)

    def seleccionar_archivo(self):
        archivo, _ = QFileDialog.getOpenFileName(self, "Seleccionar Archivo", "", "Todos los archivos (*)")
        if archivo:
            self.archivo_label.setText(f"Archivo: {archivo}")

    def guardar_actuacion(self):
        expediente = self.expediente_input.text()
        oficina = self.oficina_input.text()
        fecha = self.fecha_input.date().toString("yyyy-MM-dd")
        tipo = self.tipo_input.currentText()
        detalle = self.detalle_input.toPlainText()
        foja = self.foja_input.text()
        archivo = self.archivo_label.text().replace("Archivo: ", "")

        if not expediente or not detalle:
            QMessageBox.warning(self, "Error", "El expediente y el detalle son obligatorios.")
            return

        # Aquí puedes agregar la inserción en la base de datos
        QMessageBox.information(self, "Éxito", "Actuación guardada correctamente.")
        self.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ActuacionesApp()
    window.show()
    sys.exit(app.exec())
