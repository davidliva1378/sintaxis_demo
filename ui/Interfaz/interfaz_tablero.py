from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
                               QHBoxLayout, QInputDialog)
import sys


class TableroActuaciones(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Tablero de Actuaciones")
        self.setGeometry(100, 100, 800, 400)

        layout = QVBoxLayout()

        # Título
        self.titulo_label = QLabel("📅 Planificación Semanal de Actuaciones")
        layout.addWidget(self.titulo_label)

        # Tabla de planificación (Días en vertical)
        self.tabla = QTableWidget(7, 5)  # Siete filas (días de la semana) y cinco columnas para expedientes
        self.tabla.setVerticalHeaderLabels(["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
        self.tabla.setFixedHeight(300)
        layout.addWidget(self.tabla)

        # Botones de acción
        button_layout = QHBoxLayout()
        self.agregar_button = QPushButton("Agregar Expediente")
        self.agregar_button.clicked.connect(self.agregar_expediente)
        self.limpiar_button = QPushButton("Limpiar Tablero")
        self.limpiar_button.clicked.connect(self.limpiar_tablero)

        button_layout.addWidget(self.agregar_button)
        button_layout.addWidget(self.limpiar_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def agregar_expediente(self):
        # Pedir el número de expediente y el día de la semana
        expediente, ok = QInputDialog.getText(self, "Nuevo Expediente", "Ingrese el número de expediente:")
        if ok and expediente:
            dia, ok = QInputDialog.getItem(self, "Seleccionar Día", "Seleccione el día de la semana:",
                                           ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"],
                                           0, False)
            if ok and dia:
                fila = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"].index(dia)
                # Buscar la primera celda vacía en la fila
                for columna in range(self.tabla.columnCount()):
                    if self.tabla.item(fila, columna) is None:
                        self.tabla.setItem(fila, columna, QTableWidgetItem(expediente))
                        break

    def limpiar_tablero(self):
        # Limpiar todas las celdas
        self.tabla.clearContents()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TableroActuaciones()
    window.show()
    sys.exit(app.exec())
