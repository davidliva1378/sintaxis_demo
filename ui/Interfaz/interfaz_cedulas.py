from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
                               QPushButton, QHBoxLayout, QMessageBox)
from PySide6.QtGui import QColor
import sys


class CedulasApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cédulas Recibidas")
        self.setGeometry(100, 100, 1920, 1080)

        layout = QVBoxLayout()

        # Título
        self.titulo_label = QLabel("📩 Cédulas Recibidas")
        layout.addWidget(self.titulo_label)

        # Tabla de cédulas
        self.tabla_cedulas = QTableWidget()
        self.tabla_cedulas.setColumnCount(5)
        self.tabla_cedulas.setHorizontalHeaderLabels(["Expediente", "Detalle", "Fecha", "Acciones", ""])
        layout.addWidget(self.tabla_cedulas)

        # Botón para actualizar
        button_layout = QHBoxLayout()
        self.actualizar_button = QPushButton("🔄 Refrescar")
        self.actualizar_button.clicked.connect(self.cargar_cedulas)
        button_layout.addWidget(self.actualizar_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.cargar_cedulas()

    def cargar_cedulas(self):
        self.tabla_cedulas.setRowCount(0)

        # Datos simulados de cédulas recibidas
        cedulas = [
            {"expediente": "FPA 19049/2017", "detalle": "ROJAS, JUAN JOSE Y OTROS c/ ESTADO NACIONAL...",
             "fecha": "28/02/2025", "tipo": "N"},
            {"expediente": "FPA 299/2018", "detalle": "ZALAZAR, ROGELIO LIBORIO Y OTROS c/ ESTADO NACIONAL...",
             "fecha": "28/02/2025", "tipo": "N"},
            {"expediente": "CSS 171079/2018", "detalle": "ARAUJO WALTER RAMON c/ GENDARMERIA NACIONAL...",
             "fecha": "28/02/2025", "tipo": "D"},
        ]

        for row, cedula in enumerate(cedulas):
            self.tabla_cedulas.insertRow(row)

            self.tabla_cedulas.setItem(row, 0, QTableWidgetItem(cedula['expediente']))
            self.tabla_cedulas.setItem(row, 1, QTableWidgetItem(cedula['detalle']))
            self.tabla_cedulas.setItem(row, 2, QTableWidgetItem(cedula['fecha']))

            button_layout = QHBoxLayout()
            procesar_button = QPushButton("Procesar")
            procesar_button.clicked.connect(lambda _, r=row: self.procesar_cedula(r))

            archivar_button = QPushButton("Archivar")
            archivar_button.clicked.connect(lambda _, r=row: self.archivar_cedula(r))

            eliminar_button = QPushButton("Eliminar")
            eliminar_button.clicked.connect(lambda _, r=row: self.eliminar_cedula(r))

            descargar_button = QPushButton("Descargar PDF")
            descargar_button.clicked.connect(lambda _, r=row: self.descargar_pdf(r))

            self.tabla_cedulas.setCellWidget(row, 3, procesar_button)
            self.tabla_cedulas.setCellWidget(row, 4, archivar_button)
            self.tabla_cedulas.setCellWidget(row, 3, eliminar_button)
            self.tabla_cedulas.setCellWidget(row, 4, descargar_button)

    def procesar_cedula(self, row):
        QMessageBox.information(self, "Procesar Cédula", f"Cédula en fila {row + 1} ha sido procesada.")

    def archivar_cedula(self, row):
        QMessageBox.information(self, "Archivar Cédula", f"Cédula en fila {row + 1} ha sido archivada.")

    def eliminar_cedula(self, row):
        QMessageBox.warning(self, "Eliminar Cédula", f"Cédula en fila {row + 1} ha sido eliminada.")
        self.tabla_cedulas.removeRow(row)

    def descargar_pdf(self, row):
        QMessageBox.information(self, "Descargar PDF", f"Se descargará el PDF de la cédula en fila {row + 1}.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CedulasApp()
    window.show()
    sys.exit(app.exec())
