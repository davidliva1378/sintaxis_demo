from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
                               QPushButton, QHBoxLayout, QLineEdit, QMessageBox, QComboBox)
import sys


class ExpedientesApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Listado de Expedientes")
        self.setGeometry(100, 100, 1920, 1080)

        layout = QVBoxLayout()

        # Título
        self.titulo_label = QLabel("📂 Listado de Expedientes")
        layout.addWidget(self.titulo_label)

        # Barra de búsqueda
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar por número o carátula...")
        self.search_button = QPushButton("🔍 Buscar")
        self.search_button.clicked.connect(self.filtrar_expedientes)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        layout.addLayout(search_layout)

        # Tabla de expedientes
        self.tabla_expedientes = QTableWidget()
        self.tabla_expedientes.setColumnCount(8)
        self.tabla_expedientes.setHorizontalHeaderLabels([
            "Número", "Carátula", "Tipo de Proceso", "Instancia", "Situación",
            "Fecha de Inicio", "Última Actuación", "Acciones"
        ])
        layout.addWidget(self.tabla_expedientes)

        # Botón para actualizar
        button_layout = QHBoxLayout()
        self.actualizar_button = QPushButton("🔄 Refrescar")
        self.actualizar_button.clicked.connect(self.cargar_expedientes)
        button_layout.addWidget(self.actualizar_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)
        self.cargar_expedientes()

    def cargar_expedientes(self):
        self.tabla_expedientes.setRowCount(0)

        # Datos simulados de expedientes
        expedientes = [
            {"numero": "FPA 19049/2017", "caratula": "ROJAS, JUAN JOSE Y OTROS c/ ESTADO NACIONAL...",
             "tipo_proceso": "Amparo", "instancia": "Primera", "situacion": "En trámite",
             "fecha_inicio": "10/01/2024", "ultima_actuacion": "28/02/2025"},
            {"numero": "CSS 171079/2018", "caratula": "ARAUJO WALTER RAMON c/ GENDARMERIA NACIONAL...",
             "tipo_proceso": "Ordinario", "instancia": "Segunda", "situacion": "Archivado",
             "fecha_inicio": "05/06/2018", "ultima_actuacion": "15/01/2025"}
        ]

        for row, exp in enumerate(expedientes):
            self.tabla_expedientes.insertRow(row)
            self.tabla_expedientes.setItem(row, 0, QTableWidgetItem(exp['numero']))
            self.tabla_expedientes.setItem(row, 1, QTableWidgetItem(exp['caratula']))
            self.tabla_expedientes.setItem(row, 2, QTableWidgetItem(exp['tipo_proceso']))
            self.tabla_expedientes.setItem(row, 3, QTableWidgetItem(exp['instancia']))
            self.tabla_expedientes.setItem(row, 4, QTableWidgetItem(exp['situacion']))
            self.tabla_expedientes.setItem(row, 5, QTableWidgetItem(exp['fecha_inicio']))
            self.tabla_expedientes.setItem(row, 6, QTableWidgetItem(exp['ultima_actuacion']))

            button_layout = QHBoxLayout()
            ver_button = QPushButton("Ver Detalle")
            ver_button.clicked.connect(lambda _, r=row: self.ver_detalle(r))

            editar_button = QPushButton("Editar")
            editar_button.clicked.connect(lambda _, r=row: self.editar_expediente(r))

            eliminar_button = QPushButton("Eliminar")
            eliminar_button.clicked.connect(lambda _, r=row: self.eliminar_expediente(r))

            exportar_button = QPushButton("Exportar PDF")
            exportar_button.clicked.connect(lambda _, r=row: self.exportar_pdf(r))

            button_layout.addWidget(ver_button)
            button_layout.addWidget(editar_button)
            button_layout.addWidget(eliminar_button)
            button_layout.addWidget(exportar_button)

            self.tabla_expedientes.setCellWidget(row, 7, ver_button)
            self.tabla_expedientes.setCellWidget(row, 7, editar_button)
            self.tabla_expedientes.setCellWidget(row, 7, eliminar_button)
            self.tabla_expedientes.setCellWidget(row, 7, exportar_button)

    def filtrar_expedientes(self):
        QMessageBox.information(self, "Buscar", "Función de búsqueda aún no implementada.")

    def ver_detalle(self, row):
        QMessageBox.information(self, "Ver Detalle", f"Mostrando detalles del expediente en fila {row + 1}.")

    def editar_expediente(self, row):
        QMessageBox.information(self, "Editar Expediente", f"Editando expediente en fila {row + 1}.")

    def eliminar_expediente(self, row):
        QMessageBox.warning(self, "Eliminar Expediente", f"Expediente en fila {row + 1} ha sido eliminado.")
        self.tabla_expedientes.removeRow(row)

    def exportar_pdf(self, row):
        QMessageBox.information(self, "Exportar PDF", f"Se exportará el expediente en fila {row + 1} a PDF.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ExpedientesApp()
    window.show()
    sys.exit(app.exec())