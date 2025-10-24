# workflow_optimizado_completo.py - Sistema PJN con UX optimizado
import sys
import json
from datetime import datetime, timedelta
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QTextEdit, QSplitter, QGroupBox, QGridLayout,
    QMessageBox, QFileDialog, QHeaderView, QProgressBar, QFrame,
    QCheckBox, QListWidget, QListWidgetItem, QStackedWidget,
    QScrollArea, QToolButton, QMenu, QTreeWidget, QTreeWidgetItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QIcon, QAction, QPalette, QColor


class ExpedienteCard(QFrame):
    """Card individual de expediente con acciones rápidas"""
    clicked = pyqtSignal(dict)
    action_triggered = pyqtSignal(str, dict)

    def __init__(self, expediente_data):
        super().__init__()
        self.data = expediente_data
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)

        # Header con número y estado
        header_layout = QHBoxLayout()

        numero_label = QLabel(self.data.get('numero', 'N/A'))
        numero_label.setStyleSheet("font-weight: 600; font-size: 14px; color: #1e293b;")
        header_layout.addWidget(numero_label)

        header_layout.addStretch()

        estado = self.data.get('situacion', 'Desconocido')
        estado_label = QLabel(estado)
        estado_colors = {
            'Activo': '#10b981', 'Pendiente': '#f59e0b',
            'Cerrado': '#6b7280', 'Urgente': '#ef4444'
        }
        color = estado_colors.get(estado, '#6b7280')
        estado_label.setStyleSheet(f"""
            background-color: {color}; color: white; 
            padding: 2px 8px; border-radius: 10px; 
            font-size: 11px; font-weight: 600;
        """)
        header_layout.addWidget(estado_label)

        layout.addLayout(header_layout)

        # Carátula
        caratula_label = QLabel(self.data.get('caratula', 'Sin carátula'))
        caratula_label.setWordWrap(True)
        caratula_label.setStyleSheet("color: #374151; font-size: 13px; line-height: 1.4;")
        layout.addWidget(caratula_label)

        # Información adicional
        info_layout = QGridLayout()
        info_layout.setSpacing(4)

        dependencia = QLabel(f"Dependencia: {self.data.get('dependencia', 'N/A')}")
        dependencia.setStyleSheet("color: #6b7280; font-size: 11px;")
        info_layout.addWidget(dependencia, 0, 0, 1, 2)

        fecha = QLabel(f"Última: {self.data.get('ultima_actuacion', 'N/A')}")
        fecha.setStyleSheet("color: #6b7280; font-size: 11px;")
        info_layout.addWidget(fecha, 1, 0)

        # Indicador de urgencia si corresponde
        if self.data.get('urgente', False):
            urgente_label = QLabel("URGENTE")
            urgente_label.setStyleSheet("color: #ef4444; font-weight: 600; font-size: 11px;")
            info_layout.addWidget(urgente_label, 1, 1)

        layout.addLayout(info_layout)

        # Acciones rápidas
        acciones_layout = QHBoxLayout()
        acciones_layout.setSpacing(4)

        btn_ver = QPushButton("Ver")
        btn_ver.setStyleSheet(self.get_button_style("#3b82f6"))
        btn_ver.clicked.connect(lambda: self.action_triggered.emit("ver", self.data))
        acciones_layout.addWidget(btn_ver)

        btn_pdf = QPushButton("PDF")
        btn_pdf.setStyleSheet(self.get_button_style("#10b981"))
        btn_pdf.clicked.connect(lambda: self.action_triggered.emit("pdf", self.data))
        acciones_layout.addWidget(btn_pdf)

        btn_actualizar = QPushButton("Actualizar")
        btn_actualizar.setStyleSheet(self.get_button_style("#f59e0b"))
        btn_actualizar.clicked.connect(lambda: self.action_triggered.emit("actualizar", self.data))
        acciones_layout.addWidget(btn_actualizar)

        layout.addLayout(acciones_layout)
        self.setLayout(layout)

    def setup_style(self):
        prioridad = self.data.get('prioridad', 'normal')
        border_colors = {
            'alta': '#ef4444', 'media': '#f59e0b', 'normal': '#e2e8f0'
        }
        border_color = border_colors.get(prioridad, '#e2e8f0')

        self.setStyleSheet(f"""
            QFrame {{
                background-color: white;
                border: 2px solid {border_color};
                border-radius: 8px;
                padding: 12px;
                margin: 4px;
            }}
            QFrame:hover {{
                border-color: #3b82f6;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
        """)

        self.setFixedHeight(160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def get_button_style(self, color):
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 4px 8px;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 500;
            }}
            QPushButton:hover {{
                opacity: 0.8;
            }}
        """

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.data)


class PanelTareasDiarias(QFrame):
    """Panel lateral con tareas y expedientes del día"""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Título
        titulo = QLabel("Trabajo de Hoy")
        titulo.setStyleSheet("font-size: 16px; font-weight: 600; color: #1e293b; margin-bottom: 12px;")
        layout.addWidget(titulo)

        # Resumen rápido
        resumen_frame = QFrame()
        resumen_frame.setStyleSheet("""
            QFrame { 
                background-color: #f8fafc; 
                border-radius: 6px; 
                padding: 8px; 
                margin-bottom: 12px; 
            }
        """)
        resumen_layout = QVBoxLayout(resumen_frame)

        stats_layout = QGridLayout()
        self.crear_stat_mini(stats_layout, "8", "Pendientes", 0, 0)
        self.crear_stat_mini(stats_layout, "3", "Urgentes", 0, 1)
        self.crear_stat_mini(stats_layout, "12", "Vencen Hoy", 1, 0)
        self.crear_stat_mini(stats_layout, "5", "Actualizados", 1, 1)

        resumen_layout.addLayout(stats_layout)
        layout.addWidget(resumen_frame)

        # Lista de tareas
        tareas_group = QGroupBox("Tareas Pendientes")
        tareas_layout = QVBoxLayout()

        tareas = [
            {"texto": "Revisar expediente EXP-1001/2024", "urgente": True},
            {"texto": "Preparar informe para cliente García", "urgente": False},
            {"texto": "Audiencia 14:00 - Caso Pérez", "urgente": True},
            {"texto": "Responder notificación PJN", "urgente": False},
        ]

        for tarea in tareas:
            tarea_item = self.crear_tarea_item(tarea)
            tareas_layout.addWidget(tarea_item)

        tareas_group.setLayout(tareas_layout)
        layout.addWidget(tareas_group)

        # Expedientes favoritos
        favoritos_group = QGroupBox("Expedientes Frecuentes")
        favoritos_layout = QVBoxLayout()

        expedientes_fav = [
            "EXP-1001/2024 - García",
            "EXP-0895/2024 - Constructora ABC",
            "EXP-1156/2024 - Pérez vs Estado"
        ]

        for exp in expedientes_fav:
            btn_fav = QPushButton(exp)
            btn_fav.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 6px;
                    border: 1px solid #e2e8f0;
                    border-radius: 4px;
                    background-color: white;
                    font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #f1f5f9;
                    border-color: #3b82f6;
                }
            """)
            favoritos_layout.addWidget(btn_fav)

        favoritos_group.setLayout(favoritos_layout)
        layout.addWidget(favoritos_group)

        layout.addStretch()
        self.setLayout(layout)

    def crear_stat_mini(self, layout, numero, label, row, col):
        frame = QFrame()
        frame.setStyleSheet("border: 1px solid #e2e8f0; border-radius: 4px; padding: 4px;")

        mini_layout = QVBoxLayout(frame)
        mini_layout.setSpacing(2)

        num_label = QLabel(numero)
        num_label.setStyleSheet("font-size: 18px; font-weight: 700; color: #3b82f6;")
        num_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel(label)
        text_label.setStyleSheet("font-size: 10px; color: #6b7280;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        mini_layout.addWidget(num_label)
        mini_layout.addWidget(text_label)

        layout.addWidget(frame, row, col)

    def crear_tarea_item(self, tarea):
        item_frame = QFrame()
        layout = QHBoxLayout(item_frame)
        layout.setContentsMargins(8, 6, 8, 6)

        checkbox = QCheckBox()
        layout.addWidget(checkbox)

        texto = QLabel(tarea["texto"])
        texto.setStyleSheet(f"""
            color: {'#ef4444' if tarea['urgente'] else '#374151'};
            font-weight: {'600' if tarea['urgente'] else '400'};
            font-size: 12px;
        """)
        layout.addWidget(texto)

        if tarea["urgente"]:
            urgente_icon = QLabel("!")
            urgente_icon.setStyleSheet("color: #ef4444; font-weight: bold;")
            layout.addWidget(urgente_icon)

        item_frame.setStyleSheet("""
            QFrame {
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                margin-bottom: 2px;
                background-color: white;
            }
            QFrame:hover {
                background-color: #f8fafc;
            }
        """)

        return item_frame

    def setup_style(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border-right: 1px solid #e2e8f0;
            }
            QGroupBox {
                font-weight: 600;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                margin-top: 8px;
                padding-top: 8px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 6px;
                color: #374151;
                font-size: 12px;
            }
        """)
        self.setFixedWidth(280)


class AreaTrabajoPrincipal(QWidget):
    """Área principal de trabajo adaptable"""

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Barra de herramientas contextual
        self.toolbar = self.crear_toolbar()
        layout.addWidget(self.toolbar)

        # Área de contenido adaptable
        self.stack = QStackedWidget()

        # Vista Dashboard
        self.vista_dashboard = self.crear_vista_dashboard()
        self.stack.addWidget(self.vista_dashboard)

        # Vista Detalle
        self.vista_detalle = self.crear_vista_detalle()
        self.stack.addWidget(self.vista_detalle)

        layout.addWidget(self.stack)
        self.setLayout(layout)

    def crear_toolbar(self):
        toolbar_frame = QFrame()
        toolbar_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border-bottom: 1px solid #e2e8f0;
                padding: 8px;
            }
        """)

        toolbar_layout = QHBoxLayout(toolbar_frame)

        # Búsqueda global
        search_frame = QFrame()
        search_frame.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
                padding: 4px;
            }
        """)
        search_layout = QHBoxLayout(search_frame)

        search_icon = QLabel("Buscar:")
        search_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar expedientes, números, carátulas...")
        self.search_input.setStyleSheet("border: none; background: transparent; font-size: 14px;")
        search_layout.addWidget(self.search_input)

        toolbar_layout.addWidget(search_frame)

        # Filtros rápidos
        filtros_frame = QFrame()
        filtros_layout = QHBoxLayout(filtros_frame)

        self.btn_todos = QPushButton("Todos")
        self.btn_hoy = QPushButton("Hoy")
        self.btn_urgentes = QPushButton("Urgentes")
        self.btn_pendientes = QPushButton("Pendientes")

        for btn in [self.btn_todos, self.btn_hoy, self.btn_urgentes, self.btn_pendientes]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #f1f5f9;
                    border: 1px solid #e2e8f0;
                    border-radius: 4px;
                    padding: 6px 12px;
                    font-size: 12px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #e2e8f0;
                }
                QPushButton:checked {
                    background-color: #3b82f6;
                    color: white;
                }
            """)
            btn.setCheckable(True)
            filtros_layout.addWidget(btn)

        self.btn_todos.setChecked(True)
        toolbar_layout.addWidget(filtros_frame)

        toolbar_layout.addStretch()

        # Acciones principales
        self.btn_actualizar_todo = QPushButton("Actualizar Todo")
        self.btn_actualizar_todo.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_actualizar_todo.clicked.connect(self.actualizar_expedientes)
        toolbar_layout.addWidget(self.btn_actualizar_todo)

        return toolbar_frame

    def crear_vista_dashboard(self):
        dashboard = QWidget()
        layout = QVBoxLayout(dashboard)

        # Grid de expedientes en cards
        scroll_area = QScrollArea()
        scroll_content = QWidget()
        grid_layout = QGridLayout(scroll_content)

        # Datos de ejemplo
        expedientes_ejemplo = [
            {
                "numero": "EXP-1001/2024",
                "caratula": "Solicitud de Licencia Comercial - García, María Elena",
                "dependencia": "Juzgado Civil y Comercial N°1",
                "situacion": "Urgente",
                "ultima_actuacion": "15/03/2024",
                "prioridad": "alta",
                "urgente": True
            },
            {
                "numero": "EXP-1002/2024",
                "caratula": "Reclamo por Servicios Públicos - Pérez, Juan Carlos",
                "dependencia": "Secretaría de Servicios Públicos",
                "situacion": "Pendiente",
                "ultima_actuacion": "12/03/2024",
                "prioridad": "media"
            },
            {
                "numero": "EXP-1003/2024",
                "caratula": "Permiso de Construcción - Constructora ABC S.A.",
                "dependencia": "Dirección de Obras Públicas",
                "situacion": "Activo",
                "ultima_actuacion": "10/03/2024",
                "prioridad": "normal"
            },
            {
                "numero": "EXP-1004/2024",
                "caratula": "Trámite de Habilitación Comercial - Local Gastronómico",
                "dependencia": "Municipalidad CABA",
                "situacion": "Pendiente",
                "ultima_actuacion": "08/03/2024",
                "prioridad": "media"
            },
            {
                "numero": "EXP-1005/2024",
                "caratula": "Consulta sobre Normativa Urbana - Edificio Residencial",
                "dependencia": "Dirección de Planeamiento",
                "situacion": "Activo",
                "ultima_actuacion": "05/03/2024",
                "prioridad": "normal"
            }
        ]

        # Crear cards
        for i, exp in enumerate(expedientes_ejemplo):
            card = ExpedienteCard(exp)
            card.clicked.connect(self.mostrar_detalle)
            card.action_triggered.connect(self.manejar_accion)

            row = i // 3
            col = i % 3
            grid_layout.addWidget(card, row, col)

        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        return dashboard

    def crear_vista_detalle(self):
        detalle = QWidget()
        layout = QVBoxLayout(detalle)

        # Panel de detalle expandido
        detalle_frame = QFrame()
        detalle_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 20px;
            }
        """)

        detalle_layout = QVBoxLayout(detalle_frame)

        # Botón volver
        btn_volver = QPushButton("← Volver al Dashboard")
        btn_volver.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_volver.setStyleSheet("""
            QPushButton {
                background-color: #6b7280;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                text-align: left;
            }
            QPushButton:hover {
                background-color: #4b5563;
            }
        """)
        detalle_layout.addWidget(btn_volver)

        # Información principal
        self.detalle_titulo = QLabel("Expediente Seleccionado")
        self.detalle_titulo.setStyleSheet("font-size: 18px; font-weight: 600; color: #1e293b; margin: 16px 0;")
        detalle_layout.addWidget(self.detalle_titulo)

        self.detalle_contenido = QTextEdit()
        self.detalle_contenido.setPlaceholderText("Selecciona un expediente para ver los detalles...")
        detalle_layout.addWidget(self.detalle_contenido)

        # Acciones del detalle
        acciones_layout = QHBoxLayout()

        btn_imprimir = QPushButton("Imprimir")
        btn_pdf = QPushButton("Generar PDF")
        btn_email = QPushButton("Enviar por Email")
        btn_agendar = QPushButton("Agendar Seguimiento")

        for btn in [btn_imprimir, btn_pdf, btn_email, btn_agendar]:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 8px 16px;
                    font-weight: 500;
                }
                QPushButton:hover {
                    background-color: #2563eb;
                }
            """)
            acciones_layout.addWidget(btn)

        detalle_layout.addLayout(acciones_layout)
        layout.addWidget(detalle_frame)

        return detalle

    def mostrar_detalle(self, expediente_data):
        """Muestra el detalle de un expediente"""
        self.stack.setCurrentIndex(1)  # Vista detalle

        titulo = f"Expediente {expediente_data.get('numero', 'N/A')}"
        self.detalle_titulo.setText(titulo)

        contenido = f"""
        <h3>{expediente_data.get('caratula', 'Sin carátula')}</h3>

        <p><strong>Número:</strong> {expediente_data.get('numero', 'N/A')}</p>
        <p><strong>Dependencia:</strong> {expediente_data.get('dependencia', 'N/A')}</p>
        <p><strong>Estado:</strong> {expediente_data.get('situacion', 'N/A')}</p>
        <p><strong>Última Actuación:</strong> {expediente_data.get('ultima_actuacion', 'N/A')}</p>

        <hr>

        <h4>Últimas Actuaciones:</h4>
        <ul>
            <li>15/03/2024 - Notificación enviada</li>
            <li>12/03/2024 - Documentación presentada</li>
            <li>10/03/2024 - Expediente iniciado</li>
        </ul>

        <h4>Documentos Adjuntos:</h4>
        <ul>
            <li>📄 Formulario_solicitud.pdf</li>
            <li>📄 Documentacion_respaldatoria.pdf</li>
            <li>📄 Comprobante_pago.jpg</li>
        </ul>
        """

        self.detalle_contenido.setHtml(contenido)

    def manejar_accion(self, accion, expediente_data):
        """Maneja las acciones rápidas de las cards"""
        numero = expediente_data.get('numero', 'N/A')

        if accion == "ver":
            self.mostrar_detalle(expediente_data)
        elif accion == "pdf":
            QMessageBox.information(None, "Exportar PDF", f"Generando PDF para {numero}")
        elif accion == "actualizar":
            QMessageBox.information(None, "Actualizar", f"Actualizando expediente {numero}")

    def actualizar_expedientes(self):
        """Simula actualización de expedientes"""
        QMessageBox.information(None, "Actualización", "Iniciando actualización de todos los expedientes...")


class WorkflowMainWindow(QMainWindow):
    """Ventana principal con workflow optimizado"""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        self.setWindowTitle("Sistema PJN Professional - Workflow Optimizado")
        self.setGeometry(100, 100, 1600, 1000)

        # Widget central con splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Splitter principal
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Panel lateral izquierdo
        self.panel_tareas = PanelTareasDiarias()
        splitter.addWidget(self.panel_tareas)

        # Área principal de trabajo
        self.area_principal = AreaTrabajoPrincipal()
        splitter.addWidget(self.area_principal)

        # Configurar proporciones
        splitter.setSizes([280, 1320])
        splitter.setCollapsible(0, True)
        splitter.setCollapsible(1, False)

        main_layout.addWidget(splitter)

        # Barra de estado mejorada
        self.setup_statusbar()

        # Menú
        self.setup_menu()

    def setup_menu(self):
        """Configura el menú principal"""
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

        # Menú Ver
        ver_menu = menubar.addMenu("Ver")

        toggle_panel = QAction("Mostrar/Ocultar Panel Lateral", self)
        toggle_panel.triggered.connect(self.toggle_panel_lateral)
        ver_menu.addAction(toggle_panel)

        # Menú Ayuda
        ayuda_menu = menubar.addMenu("Ayuda")

        acerca = QAction("Acerca de", self)
        acerca.triggered.connect(self.mostrar_acerca)
        ayuda_menu.addAction(acerca)

    def setup_statusbar(self):
        statusbar = self.statusBar()

        # Estado de conexión
        self.conexion_label = QLabel("🟢 Conectado al PJN")
        self.conexion_label.setStyleSheet("color: #10b981; font-weight: 500;")
        statusbar.addWidget(self.conexion_label)

        statusbar.addPermanentWidget(QLabel("|"))

        # Última actualización
        self.actualizacion_label = QLabel("Última actualización: 15/03/2024 14:30")
        self.actualizacion_label.setStyleSheet("color: #6b7280;")
        statusbar.addPermanentWidget(self.actualizacion_label)

        statusbar.addPermanentWidget(QLabel("|"))

        # Estadísticas rápidas
        self.stats_label = QLabel("156 expedientes | 8 pendientes | 3 urgentes")
        self.stats_label.setStyleSheet("color: #374151; font-weight: 500;")
        statusbar.addPermanentWidget(self.stats_label)

    def setup_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8fafc;
            }
            QSplitter::handle {
                background-color: #e2e8f0;
                width: 1px;
            }
            QSplitter::handle:hover {
                background-color: #3b82f6;
            }
            QStatusBar {
                background-color: white;
                border-top: 1px solid #e2e8f0;
                color: #374151;
                font-size: 12px;
            }
        """)

    def nueva_extraccion(self):
        """Inicia nueva extracción"""
        QMessageBox.information(self, "Nueva Extracción", "Iniciando extracción de expedientes...")

    def toggle_panel_lateral(self):
        """Muestra/oculta el panel lateral"""
        panel = self.findChild(PanelTareasDiarias)
        if panel:
            panel.setVisible(not panel.isVisible())

    def mostrar_acerca(self):
        """Muestra información de la aplicación"""
        QMessageBox.about(self, "Acerca de Sistema PJN Professional",
                          "Sistema PJN Professional v2.0\n"
                          "Workflow Optimizado\n\n"
                          "Aplicación para extracción y gestión\n"
                          "de expedientes del Poder Judicial de la Nación\n\n"
                          "Diseñado específicamente para abogados\n"
                          "y estudios jurídicos\n\n"
                          "© 2024 - Todos los derechos reservados")


def main():
    """Función principal"""
    app = QApplication(sys.argv)

    # Configurar aplicación
    app.setApplicationName("Sistema PJN Professional - Workflow Optimizado")
    app.setApplicationVersion("2.0")
    app.setOrganizationName("Tu Empresa")

    # Fuente optimizada para lectura profesional
    font = QFont("Segoe UI", 9)
    app.setFont(font)

    # Crear y mostrar ventana principal
    window = WorkflowMainWindow()
    window.show()

    # Ejecutar aplicación
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())