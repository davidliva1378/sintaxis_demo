# main_pyqt.py - Modelo PyQt para Sistema PJN Professional
import sys
import os
import json
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QTextEdit, QTabWidget, QSplitter, QGroupBox,
    QGridLayout, QMessageBox, QFileDialog, QHeaderView, QProgressBar,
    QStatusBar, QMenuBar, QToolBar, QFrame, QCheckBox, QSpinBox,
    QFormLayout, QScrollArea
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QPixmap, QIcon, QAction, QPalette, QColor

# Intentar importar tu código PJN
try:
    # Comentar/descomentar según tengas disponible tu código
    # from panel_pjn.acciones_pjn import extraer_expedientes, extraer_entradas
    PJN_DISPONIBLE = False  # Cambiar a True cuando tengas el código
except ImportError:
    PJN_DISPONIBLE = False


class ModernWidget(QWidget):
    """Widget base con estilo moderno"""

    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #f8fafc;
                color: #0f172a;
                font-family: 'Segoe UI', 'Inter', sans-serif;
            }
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: 500;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
            QPushButton:pressed {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #94a3b8;
            }
            QLineEdit, QComboBox, QSpinBox {
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 8px 12px;
                background-color: white;
                font-size: 14px;
            }
            QLineEdit:focus, QComboBox:focus, QSpinBox:focus {
                border-color: #3b82f6;
                outline: none;
            }
            QTableWidget {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
                alternate-background-color: #f8fafc;
                gridline-color: #e2e8f0;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                padding: 8px;
                border: none;
                font-weight: 600;
                color: #374151;
            }
            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
                margin-top: 2px;
            }
            QTabBar::tab {
                background-color: #f1f5f9;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                color: #64748b;
            }
            QTabBar::tab:selected {
                background-color: white;
                color: #3b82f6;
                border-bottom: 2px solid #3b82f6;
            }
            QGroupBox {
                font-weight: 600;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: #374151;
            }
            QTextEdit {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
                padding: 8px;
            }
            QProgressBar {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                background-color: #f1f5f9;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3b82f6;
                border-radius: 3px;
            }
        """)


class ExtraccionThread(QThread):
    """Hilo para extracciones sin bloquear la UI"""
    progreso = pyqtSignal(int)
    mensaje = pyqtSignal(str)
    terminado = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, tipo_extraccion, parametros):
        super().__init__()
        self.tipo = tipo_extraccion
        self.params = parametros

    def run(self):
        try:
            if self.tipo == "expedientes":
                self.simular_extraccion_expedientes()
            elif self.tipo == "notificaciones":
                self.simular_extraccion_notificaciones()
        except Exception as e:
            self.error.emit(str(e))

    def simular_extraccion_expedientes(self):
        """Simulación - reemplazar con tu código real"""
        expedientes = []
        total = 50  # Simulamos 50 expedientes

        for i in range(total):
            progreso = int((i + 1) / total * 100)
            self.progreso.emit(progreso)
            self.mensaje.emit(f"Extrayendo expediente {i + 1}/{total}...")

            expedientes.append({
                "numero": f"EXP-{1000 + i}/2024",
                "caratula": f"Expediente de prueba {i + 1} - Simulación para desarrollo",
                "dependencia": ["Juzgado Civil", "Juzgado Comercial", "Secretaría Municipal"][i % 3],
                "situacion": ["Activo", "Pendiente", "Cerrado"][i % 3],
                "ultima_actuacion": f"{15 + (i % 15):02d}/03/2024",
                "jurisdiccion": "CABA"
            })

            self.msleep(100)  # Simular trabajo

        self.terminado.emit(expedientes)

    def simular_extraccion_notificaciones(self):
        """Simulación de notificaciones"""
        notificaciones = []
        for i in range(10):
            self.progreso.emit(i * 10)
            self.mensaje.emit(f"Extrayendo notificación {i + 1}/10...")

            notificaciones.append({
                "numero": f"NOT-{2000 + i}",
                "caratula": f"Notificación {i + 1}",
                "fecha": "2024-03-15",
                "leida": i % 2 == 0
            })
            self.msleep(200)

        self.terminado.emit(notificaciones)


class DashboardWidget(ModernWidget):
    """Panel principal con estadísticas"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("Dashboard del Sistema")
        titulo.setStyleSheet("font-size: 24px; font-weight: 700; color: #1e293b; margin-bottom: 16px;")
        layout.addWidget(titulo)

        # Estadísticas
        stats_layout = QHBoxLayout()

        # Crear tarjetas de estadísticas
        self.crear_stat_card(stats_layout, "1,234", "Total Expedientes", "#3b82f6")
        self.crear_stat_card(stats_layout, "56", "Activos", "#10b981")
        self.crear_stat_card(stats_layout, "23", "Pendientes", "#f59e0b")
        self.crear_stat_card(stats_layout, "8", "Notificaciones", "#ef4444")

        layout.addLayout(stats_layout)

        # Tabla de expedientes recientes
        grupo_recientes = QGroupBox("Expedientes Recientes")
        tabla_layout = QVBoxLayout()

        self.tabla_recientes = QTableWidget(5, 4)
        self.tabla_recientes.setHorizontalHeaderLabels(["Número", "Carátula", "Estado", "Fecha"])

        # Datos de ejemplo
        datos_ejemplo = [
            ("EXP-1001/2024", "Solicitud Licencia Comercial", "Activo", "15/03/2024"),
            ("EXP-1002/2024", "Reclamo Servicios Públicos", "Pendiente", "12/03/2024"),
            ("EXP-1003/2024", "Permiso de Construcción", "Cerrado", "10/03/2024"),
            ("EXP-1004/2024", "Trámite Municipal", "Activo", "08/03/2024"),
            ("EXP-1005/2024", "Consulta Legal", "Pendiente", "05/03/2024")
        ]

        for row, (numero, caratula, estado, fecha) in enumerate(datos_ejemplo):
            self.tabla_recientes.setItem(row, 0, QTableWidgetItem(numero))
            self.tabla_recientes.setItem(row, 1, QTableWidgetItem(caratula))

            # Estado con color
            estado_item = QTableWidgetItem(estado)
            if estado == "Activo":
                estado_item.setBackground(QColor("#dcfce7"))
            elif estado == "Pendiente":
                estado_item.setBackground(QColor("#fef3c7"))
            else:
                estado_item.setBackground(QColor("#f3f4f6"))

            self.tabla_recientes.setItem(row, 2, estado_item)
            self.tabla_recientes.setItem(row, 3, QTableWidgetItem(fecha))

        # Ajustar columnas
        header = self.tabla_recientes.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        tabla_layout.addWidget(self.tabla_recientes)
        grupo_recientes.setLayout(tabla_layout)
        layout.addWidget(grupo_recientes)

        self.setLayout(layout)

    def crear_stat_card(self, layout, numero, label, color):
        """Crea una tarjeta de estadística"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 16px;
                margin: 4px;
            }}
        """)

        card_layout = QVBoxLayout()

        # Número
        num_label = QLabel(numero)
        num_label.setStyleSheet(f"font-size: 32px; font-weight: 700; color: {color}; margin-bottom: 8px;")
        num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Etiqueta
        text_label = QLabel(label)
        text_label.setStyleSheet("font-size: 14px; color: #64748b; font-weight: 500;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        card_layout.addWidget(num_label)
        card_layout.addWidget(text_label)
        card.setLayout(card_layout)

        layout.addWidget(card)


class ExpedientesWidget(ModernWidget):
    """Widget para gestión de expedientes"""

    def __init__(self):
        super().__init__()
        self.expedientes = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Título y controles
        header_layout = QHBoxLayout()

        titulo = QLabel("Gestión de Expedientes")
        titulo.setStyleSheet("font-size: 20px; font-weight: 600; color: #1e293b;")
        header_layout.addWidget(titulo)

        header_layout.addStretch()

        self.btn_extraer = QPushButton("Extraer Expedientes")
        self.btn_extraer.clicked.connect(self.extraer_expedientes)
        header_layout.addWidget(self.btn_extraer)

        layout.addLayout(header_layout)

        # Filtros
        filtros_group = QGroupBox("Filtros de Búsqueda")
        filtros_layout = QGridLayout()

        filtros_layout.addWidget(QLabel("Buscar:"), 0, 0)
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Número de expediente o carátula...")
        self.search_box.textChanged.connect(self.filtrar_tabla)
        filtros_layout.addWidget(self.search_box, 0, 1)

        filtros_layout.addWidget(QLabel("Estado:"), 0, 2)
        self.filtro_estado = QComboBox()
        self.filtro_estado.addItems(["Todos", "Activo", "Pendiente", "Cerrado"])
        self.filtro_estado.currentTextChanged.connect(self.filtrar_tabla)
        filtros_layout.addWidget(self.filtro_estado, 0, 3)

        self.btn_exportar = QPushButton("Exportar PDF")
        self.btn_exportar.clicked.connect(self.exportar_pdf)
        filtros_layout.addWidget(self.btn_exportar, 0, 4)

        filtros_group.setLayout(filtros_layout)
        layout.addWidget(filtros_group)

        # Tabla de expedientes
        self.tabla = QTableWidget()
        self.tabla.setColumnCount(6)
        self.tabla.setHorizontalHeaderLabels([
            "Sel", "Número", "Carátula", "Dependencia", "Estado", "Última Actuación"
        ])

        # Configurar tabla
        header = self.tabla.horizontalHeader()
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabla.setAlternatingRowColors(True)
        self.tabla.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.tabla)

        # Barra de progreso
        self.progress_widget = QWidget()
        progress_layout = QVBoxLayout()

        self.progress = QProgressBar()
        self.status_label = QLabel("Listo para extraer expedientes")

        progress_layout.addWidget(self.progress)
        progress_layout.addWidget(self.status_label)
        self.progress_widget.setLayout(progress_layout)
        self.progress_widget.hide()

        layout.addWidget(self.progress_widget)

        self.setLayout(layout)

    def extraer_expedientes(self):
        """Inicia la extracción de expedientes"""
        self.btn_extraer.setEnabled(False)
        self.progress_widget.show()
        self.progress.setValue(0)

        # Crear y ejecutar hilo de extracción
        self.extractor = ExtraccionThread("expedientes", {})
        self.extractor.progreso.connect(self.progress.setValue)
        self.extractor.mensaje.connect(self.status_label.setText)
        self.extractor.terminado.connect(self.on_extraccion_terminada)
        self.extractor.error.connect(self.on_extraccion_error)
        self.extractor.start()

    def on_extraccion_terminada(self, expedientes):
        """Callback cuando termina la extracción"""
        self.expedientes = expedientes
        self.actualizar_tabla()
        self.btn_extraer.setEnabled(True)
        self.progress_widget.hide()

        QMessageBox.information(self, "Extracción Completada",
                                f"Se extrajeron {len(expedientes)} expedientes correctamente.")

    def on_extraccion_error(self, error):
        """Callback para errores"""
        QMessageBox.critical(self, "Error", f"Error en extracción: {error}")
        self.btn_extraer.setEnabled(True)
        self.progress_widget.hide()

    def actualizar_tabla(self):
        """Actualiza la tabla con los expedientes filtrados"""
        expedientes_filtrados = self.get_expedientes_filtrados()

        self.tabla.setRowCount(len(expedientes_filtrados))

        for row, exp in enumerate(expedientes_filtrados):
            # Checkbox
            checkbox = QCheckBox()
            self.tabla.setCellWidget(row, 0, checkbox)

            # Datos
            self.tabla.setItem(row, 1, QTableWidgetItem(exp.get("numero", "")))
            self.tabla.setItem(row, 2, QTableWidgetItem(exp.get("caratula", "")))
            self.tabla.setItem(row, 3, QTableWidgetItem(exp.get("dependencia", "")))

            # Estado con color
            estado_item = QTableWidgetItem(exp.get("situacion", ""))
            if exp.get("situacion") == "Activo":
                estado_item.setBackground(QColor("#dcfce7"))
            elif exp.get("situacion") == "Pendiente":
                estado_item.setBackground(QColor("#fef3c7"))
            else:
                estado_item.setBackground(QColor("#f3f4f6"))

            self.tabla.setItem(row, 4, estado_item)
            self.tabla.setItem(row, 5, QTableWidgetItem(exp.get("ultima_actuacion", "")))

    def get_expedientes_filtrados(self):
        """Aplica filtros a los expedientes"""
        filtrados = self.expedientes

        # Filtro por texto
        texto = self.search_box.text().lower()
        if texto:
            filtrados = [exp for exp in filtrados
                         if texto in exp.get("numero", "").lower()
                         or texto in exp.get("caratula", "").lower()]

        # Filtro por estado
        estado = self.filtro_estado.currentText()
        if estado != "Todos":
            filtrados = [exp for exp in filtrados
                         if exp.get("situacion") == estado]

        return filtrados

    def filtrar_tabla(self):
        """Actualiza tabla cuando cambian filtros"""
        if self.expedientes:
            self.actualizar_tabla()

    def exportar_pdf(self):
        """Exporta expedientes seleccionados a PDF"""
        # Obtener expedientes seleccionados
        expedientes_seleccionados = []
        for row in range(self.tabla.rowCount()):
            checkbox = self.tabla.cellWidget(row, 0)
            if checkbox and checkbox.isChecked():
                expedientes_seleccionados.append(row)

        if not expedientes_seleccionados:
            QMessageBox.information(self, "Información",
                                    "Selecciona al menos un expediente para exportar")
            return

        archivo, _ = QFileDialog.getSaveFileName(
            self, "Guardar PDF",
            f"expedientes_{datetime.now().strftime('%Y%m%d')}.pdf",
            "PDF files (*.pdf)"
        )

        if archivo:
            # Aquí implementarías la generación real del PDF
            QMessageBox.information(self, "Éxito",
                                    f"PDF generado: {archivo}\n{len(expedientes_seleccionados)} expedientes incluidos")


class ConfiguracionWidget(ModernWidget):
    """Widget de configuración"""

    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("Configuración del Sistema")
        titulo.setStyleSheet("font-size: 20px; font-weight: 600; color: #1e293b; margin-bottom: 16px;")
        layout.addWidget(titulo)

        # Configuración PJN
        grupo_pjn = QGroupBox("Configuración de Acceso PJN")
        pjn_layout = QFormLayout()

        self.usuario_edit = QLineEdit()
        self.usuario_edit.setPlaceholderText("Tu usuario del PJN")
        pjn_layout.addRow("Usuario:", self.usuario_edit)

        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_edit.setPlaceholderText("Tu contraseña")
        pjn_layout.addRow("Contraseña:", self.password_edit)

        self.url_edit = QLineEdit()
        self.url_edit.setText("https://www.pjn.gov.ar")
        pjn_layout.addRow("URL Portal:", self.url_edit)

        self.btn_probar = QPushButton("Probar Conexión")
        self.btn_probar.clicked.connect(self.probar_conexion)
        pjn_layout.addRow("", self.btn_probar)

        grupo_pjn.setLayout(pjn_layout)
        layout.addWidget(grupo_pjn)

        # Configuración de archivos
        grupo_archivos = QGroupBox("Configuración de Archivos")
        archivos_layout = QFormLayout()

        carpeta_layout = QHBoxLayout()
        self.carpeta_edit = QLineEdit()
        self.carpeta_edit.setText(str(Path.home() / "Documentos" / "ExpedientesPJN"))
        carpeta_layout.addWidget(self.carpeta_edit)

        btn_carpeta = QPushButton("Seleccionar")
        btn_carpeta.clicked.connect(self.seleccionar_carpeta)
        carpeta_layout.addWidget(btn_carpeta)

        archivos_layout.addRow("Carpeta destino:", carpeta_layout)

        self.formato_combo = QComboBox()
        self.formato_combo.addItems(["PDF Profesional", "Excel Detallado", "Ambos Formatos"])
        archivos_layout.addRow("Formato exportación:", self.formato_combo)

        grupo_archivos.setLayout(archivos_layout)
        layout.addWidget(grupo_archivos)

        # Configuración avanzada
        grupo_avanzada = QGroupBox("Configuración Avanzada")
        avanzada_layout = QFormLayout()

        self.auto_extraccion = QComboBox()
        self.auto_extraccion.addItems(["Deshabilitada", "Cada 6 horas", "Diariamente", "Semanalmente"])
        avanzada_layout.addRow("Extracción automática:", self.auto_extraccion)

        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(10, 300)
        self.timeout_spin.setValue(30)
        self.timeout_spin.setSuffix(" segundos")
        avanzada_layout.addRow("Timeout conexión:", self.timeout_spin)

        grupo_avanzada.setLayout(avanzada_layout)
        layout.addWidget(grupo_avanzada)

        # Botones
        botones_layout = QHBoxLayout()

        btn_guardar = QPushButton("Guardar Configuración")
        btn_guardar.clicked.connect(self.guardar_configuracion)
        botones_layout.addWidget(btn_guardar)

        btn_resetear = QPushButton("Resetear")
        btn_resetear.setStyleSheet("background-color: #6b7280;")
        botones_layout.addWidget(btn_resetear)

        botones_layout.addStretch()

        layout.addLayout(botones_layout)
        layout.addStretch()

        self.setLayout(layout)

    def seleccionar_carpeta(self):
        """Selecciona carpeta de destino"""
        carpeta = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de destino")
        if carpeta:
            self.carpeta_edit.setText(carpeta)

    def probar_conexion(self):
        """Prueba la conexión con PJN"""
        if not self.usuario_edit.text() or not self.password_edit.text():
            QMessageBox.warning(self, "Advertencia", "Completa usuario y contraseña")
            return

        # Aquí implementarías la prueba real
        QMessageBox.information(self, "Conexión", "Conexión exitosa (simulada)")

    def guardar_configuracion(self):
        """Guarda la configuración"""
        config = {
            "usuario": self.usuario_edit.text(),
            "password": self.password_edit.text(),
            "url": self.url_edit.text(),
            "carpeta_destino": self.carpeta_edit.text(),
            "formato_exportacion": self.formato_combo.currentText(),
            "auto_extraccion": self.auto_extraccion.currentText(),
            "timeout": self.timeout_spin.value()
        }

        # Guardar en archivo JSON (o usar QSettings)
        config_file = Path("config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)

        QMessageBox.information(self, "Éxito", "Configuración guardada correctamente")


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación"""

    def __init__(self):
        super().__init__()
        self.init_ui()
        self.init_menu()
        self.init_statusbar()
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8fafc;
            }
        """)

    def init_ui(self):
        self.setWindowTitle("Sistema PJN Professional v1.0")
        self.setGeometry(100, 100, 1400, 900)

        # Widget central con pestañas
        self.tabs = QTabWidget()

        # Crear pestañas
        self.dashboard_widget = DashboardWidget()
        self.expedientes_widget = ExpedientesWidget()
        self.config_widget = ConfiguracionWidget()

        # Agregar pestañas
        self.tabs.addTab(self.dashboard_widget, "Dashboard")
        self.tabs.addTab(self.expedientes_widget, "Expedientes")
        self.tabs.addTab(self.config_widget, "Configuración")

        self.setCentralWidget(self.tabs)

    def init_menu(self):
        """Inicializa la barra de menú"""
        menubar = self.menuBar()

        # Menú Archivo
        archivo_menu = menubar.addMenu("Archivo")

        nueva_extraccion = QAction("Nueva Extracción", self)
        nueva_extraccion.triggered.connect(self.nueva_extraccion)
        archivo_menu.addAction(nueva_extraccion)

        archivo_menu.addSeparator()

        salir = QAction("Salir", self)
        salir.triggered.connect(self.close)
        archivo_menu.addAction(salir)

        # Menú Herramientas
        herramientas_menu = menubar.addMenu("Herramientas")

        config = QAction("Configuración", self)
        config.triggered.connect(lambda: self.tabs.setCurrentIndex(2))
        herramientas_menu.addAction(config)

        # Menú Ayuda
        ayuda_menu = menubar.addMenu("Ayuda")

        acerca = QAction("Acerca de", self)
        acerca.triggered.connect(self.mostrar_acerca)
        ayuda_menu.addAction(acerca)

    def init_statusbar(self):
        """Inicializa la barra de estado"""
        self.statusbar = QStatusBar()
        self.setStatusBar(self.statusbar)
        self.statusbar.showMessage("Sistema PJN Professional - Listo")

    def nueva_extraccion(self):
        """Inicia nueva extracción"""
        self.tabs.setCurrentIndex(1)  # Ir a pestaña expedientes
        self.expedientes_widget.extraer_expedientes()

    def mostrar_acerca(self):
        """Muestra información de la aplicación"""
        QMessageBox.about(self, "Acerca de Sistema PJN Professional",
                          "Sistema PJN Professional v1.0\n\n"
                          "Aplicación para extracción y gestión\n"
                          "de expedientes del Poder Judicial de la Nación\n\n"
                          "Desarrollado para abogados y estudios jurídicos\n\n"
                          "© 2024 - Todos los derechos reservados")


def main():
    """Función principal"""
    app = QApplication(sys.argv)

    # Configurar aplicación
    app.setApplicationName("Sistema PJN Professional")
    app.setApplicationVersion("1.0")
    app.setOrganizationName("Tu Empresa")

    # Configurar fuente por defecto
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    # Crear y mostrar ventana principal
    window = MainWindow()
    window.show()

    # Ejecutar aplicación
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())

# ==================== ARCHIVO ADICIONAL: requirements.txt ====================
"""
Crear un archivo requirements.txt con estas dependencias:

PyQt6==6.6.1
reportlab==4.0.4
pathlib
json5

Para instalar:
pip install -r requirements.txt

O individualmente:
pip install PyQt6 reportlab
"""

# ==================== ARCHIVO ADICIONAL: config_manager.py ====================
"""
Gestor de configuración más robusto (opcional)

import json
from pathlib import Path
from PyQt6.QtCore import QSettings

class ConfigManager:
    def __init__(self):
        self.config_file = Path("config.json")
        self.settings = QSettings("TuEmpresa", "SistemaPJN")

    def save_config(self, config_dict):
        # Guardar en JSON
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)

        # También en QSettings para persistencia del sistema
        for key, value in config_dict.items():
            self.settings.setValue(key, value)

    def load_config(self):
        if self.config_file.exists():
            with open(self.config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}
"""

# ==================== ARCHIVO ADICIONAL: pdf_generator.py ====================
"""
Generador de PDFs profesional con reportlab

from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime

class PDFGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()

    def generar_reporte_expedientes(self, expedientes, archivo_salida, datos_estudio=None):
        doc = SimpleDocTemplate(archivo_salida, pagesize=A4)
        story = []

        # Título
        titulo_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=1  # Centrado
        )

        titulo = Paragraph("Reporte de Expedientes", titulo_style)
        story.append(titulo)

        # Información del estudio (si se proporciona)
        if datos_estudio:
            info_estudio = f"<b>Estudio:</b> {datos_estudio.get('nombre', '')}<br/>"
            info_estudio += f"<b>Fecha:</b> {datetime.now().strftime('%d/%m/%Y')}<br/>"
            info_estudio += f"<b>Total expedientes:</b> {len(expedientes)}"

            info_para = Paragraph(info_estudio, self.styles['Normal'])
            story.append(info_para)
            story.append(Spacer(1, 20))

        # Tabla de expedientes
        datos_tabla = [['Número', 'Carátula', 'Dependencia', 'Estado', 'Última Actuación']]

        for exp in expedientes:
            datos_tabla.append([
                exp.get('numero', ''),
                exp.get('caratula', '')[:50] + '...' if len(exp.get('caratula', '')) > 50 else exp.get('caratula', ''),
                exp.get('dependencia', ''),
                exp.get('situacion', ''),
                exp.get('ultima_actuacion', '')
            ])

        tabla = Table(datos_tabla, colWidths=[1.5*inch, 3*inch, 2*inch, 1*inch, 1.5*inch])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))

        story.append(tabla)

        # Construir PDF
        doc.build(story)
        return archivo_salida
"""

# ==================== INSTRUCCIONES DE EJECUCIÓN ====================
"""
PASOS PARA EJECUTAR EN PYCHARM:

1. Crear nuevo proyecto Python
2. Instalar dependencias:
   pip install PyQt6

3. Copiar el código principal en main_pyqt.py

4. Ejecutar desde PyCharm:
   - Click derecho en main_pyqt.py
   - Run 'main_pyqt'

   O usar terminal:
   python main_pyqt.py

5. La aplicación debería abrir con:
   - Dashboard con estadísticas
   - Pestaña de expedientes con simulación de extracción
   - Configuración completa

ESTRUCTURA DE ARCHIVOS RECOMENDADA:
sistema_pjn/
├── main_pyqt.py           # Archivo principal (este código)
├── config.json            # Se crea automáticamente
├── requirements.txt       # Dependencias
├── panel_pjn/             # Tu código existente
│   └── acciones_pjn/
└── exports/               # PDFs generados

INTEGRACIÓN CON TU CÓDIGO:
1. Descomenta las líneas de import de panel_pjn
2. Cambia PJN_DISPONIBLE = True
3. Reemplaza las funciones simular_* por tu código real
4. Agrega tus parámetros específicos

PERSONALIZACIÓN:
- Colores: Modifica las variables CSS en ModernWidget
- Logo: Agrega setWindowIcon() con tu icono
- Funcionalidades: Extiende cada Widget según necesites
"""