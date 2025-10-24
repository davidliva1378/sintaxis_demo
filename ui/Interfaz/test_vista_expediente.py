import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from datetime import datetime, timedelta


class VistaDetalleExpediente(QWidget):
    """Vista detallada y completa de un expediente individual"""

    def __init__(self, expediente_data=None):
        super().__init__()
        self.expediente_data = expediente_data or self.get_datos_ejemplo()
        self.setup_ui()
        self.setup_style()
        self.cargar_datos()

    def get_datos_ejemplo(self):
        """Datos de ejemplo para testing"""
        return {
            'numero': 'EXP-2024-001234-PJN',
            'caratula': 'GARCÍA, JUAN CARLOS C/ EMPRESA XYZ S.A. S/ DAÑOS Y PERJUICIOS',
            'dependencia': 'Juzgado Civil y Comercial N° 12',
            'situacion': 'EN TRÁMITE',
            'ultima_actuacion': 'Vista al actor para alegar',
            'fecha_inicio': '2024-01-15',
            'fecha_actualizacion': '2024-08-30',
            'tipo_proceso': 'Ordinario',
            'materia': 'Civil y Comercial',
            'monto': '$2.500.000',
            'prioridad': 'Alta',
            'abogado_responsable': 'Dr. María Rodriguez',
            'estado_procesal': 'Período de Prueba'
        }

    def setup_ui(self):
        self.setWindowTitle("Detalle del Expediente")
        self.setGeometry(100, 100, 1400, 900)

        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header con información principal
        self.crear_header()
        main_layout.addWidget(self.header_widget)

        # Área principal con tabs
        self.crear_tabs()
        main_layout.addWidget(self.tabs_widget)

        # Footer con acciones
        self.crear_footer()
        main_layout.addWidget(self.footer_widget)

    def crear_header(self):
        """Crea el header con información principal del expediente"""
        self.header_widget = QFrame()
        self.header_widget.setFixedHeight(180)

        layout = QHBoxLayout(self.header_widget)
        layout.setContentsMargins(25, 20, 25, 20)

        # Columna izquierda - Info principal
        left_column = QVBoxLayout()

        # Número y carátula
        self.numero_label = QLabel()
        self.numero_label.setWordWrap(True)
        left_column.addWidget(self.numero_label)

        self.caratula_label = QLabel()
        self.caratula_label.setWordWrap(True)
        left_column.addWidget(self.caratula_label)

        # Dependencia
        self.dependencia_label = QLabel()
        left_column.addWidget(self.dependencia_label)

        layout.addLayout(left_column, 2)

        # Columna derecha - Estados y fechas
        right_column = QVBoxLayout()

        # Estado actual
        self.estado_widget = self.crear_badge_estado()
        right_column.addWidget(self.estado_widget)

        # Información adicional
        self.info_adicional = QLabel()
        right_column.addWidget(self.info_adicional)

        layout.addLayout(right_column, 1)

    def crear_badge_estado(self):
        """Crea el badge de estado visual"""
        widget = QFrame()
        widget.setFixedSize(180, 80)

        layout = QVBoxLayout(widget)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.estado_label = QLabel("EN TRÁMITE")
        self.estado_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.prioridad_label = QLabel("PRIORIDAD ALTA")
        self.prioridad_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.estado_label)
        layout.addWidget(self.prioridad_label)

        return widget

    def crear_tabs(self):
        """Crea las pestañas con diferentes vistas del expediente"""
        self.tabs_widget = QTabWidget()

        # Tab 1: Actuaciones
        self.tab_actuaciones = self.crear_tab_actuaciones()
        self.tabs_widget.addTab(self.tab_actuaciones, "📋 Actuaciones")

        # Tab 2: Documentos
        self.tab_documentos = self.crear_tab_documentos()
        self.tabs_widget.addTab(self.tab_documentos, "📎 Documentos")

        # Tab 3: Partes
        self.tab_partes = self.crear_tab_partes()
        self.tabs_widget.addTab(self.tab_partes, "👥 Partes")

        # Tab 4: Cronología
        self.tab_cronologia = self.crear_tab_cronologia()
        self.tabs_widget.addTab(self.tab_cronologia, "📅 Cronología")

        # Tab 5: Notas y Observaciones
        self.tab_notas = self.crear_tab_notas()
        self.tabs_widget.addTab(self.tab_notas, "📝 Notas")

    def crear_tab_actuaciones(self):
        """Tab con las actuaciones del expediente"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Herramientas de filtro
        filtros_layout = QHBoxLayout()

        # Filtro por fecha
        filtros_layout.addWidget(QLabel("Desde:"))
        self.fecha_desde = QDateEdit(calendarPopup=True)
        self.fecha_desde.setDate(QDate.currentDate().addMonths(-6))
        filtros_layout.addWidget(self.fecha_desde)

        filtros_layout.addWidget(QLabel("Hasta:"))
        self.fecha_hasta = QDateEdit(calendarPopup=True)
        self.fecha_hasta.setDate(QDate.currentDate())
        filtros_layout.addWidget(self.fecha_hasta)

        # Filtro por tipo
        filtros_layout.addWidget(QLabel("Tipo:"))
        self.filtro_tipo = QComboBox()
        self.filtro_tipo.addItems(["Todas", "Providencias", "Resoluciones", "Sentencias", "Notificaciones"])
        filtros_layout.addWidget(self.filtro_tipo)

        filtros_layout.addStretch()

        btn_filtrar = QPushButton("🔍 Filtrar")
        filtros_layout.addWidget(btn_filtrar)

        layout.addLayout(filtros_layout)

        # Tabla de actuaciones
        self.tabla_actuaciones = QTableWidget()
        self.tabla_actuaciones.setColumnCount(4)
        self.tabla_actuaciones.setHorizontalHeaderLabels([
            "Fecha", "Tipo", "Descripción", "Funcionario"
        ])

        # Configurar tabla
        header = self.tabla_actuaciones.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        self.tabla_actuaciones.setAlternatingRowColors(True)
        self.tabla_actuaciones.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)

        # Llenar con datos de ejemplo
        self.cargar_actuaciones()

        layout.addWidget(self.tabla_actuaciones)

        return widget

    def crear_tab_documentos(self):
        """Tab con los documentos del expediente"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Toolbar para documentos
        toolbar_layout = QHBoxLayout()

        btn_agregar_doc = QPushButton("➕ Agregar Documento")
        btn_agregar_doc.clicked.connect(self.agregar_documento)
        toolbar_layout.addWidget(btn_agregar_doc)

        btn_escanear = QPushButton("📱 Escanear")
        toolbar_layout.addWidget(btn_escanear)

        toolbar_layout.addStretch()

        # Filtros de documento
        filtro_tipo_doc = QComboBox()
        filtro_tipo_doc.addItems(["Todos", "PDF", "Word", "Excel", "Imágenes"])
        toolbar_layout.addWidget(filtro_tipo_doc)

        layout.addLayout(toolbar_layout)

        # Lista de documentos con vista de iconos
        self.lista_documentos = QListWidget()
        self.lista_documentos.setViewMode(QListWidget.ViewMode.IconMode)
        self.lista_documentos.setIconSize(QSize(64, 64))
        self.lista_documentos.setGridSize(QSize(120, 100))
        self.lista_documentos.setResizeMode(QListWidget.ResizeMode.Adjust)

        # Context menu para documentos
        self.lista_documentos.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.lista_documentos.customContextMenuRequested.connect(self.mostrar_menu_documento)

        # Llenar con documentos de ejemplo
        self.cargar_documentos()

        layout.addWidget(self.lista_documentos)

        return widget

    def crear_tab_partes(self):
        """Tab con las partes del proceso"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # División en dos columnas
        partes_layout = QHBoxLayout()

        # Columna Actores
        actores_group = QGroupBox("ACTORES")
        actores_layout = QVBoxLayout(actores_group)

        self.lista_actores = QListWidget()
        actores_layout.addWidget(self.lista_actores)

        btn_agregar_actor = QPushButton("➕ Agregar Actor")
        actores_layout.addWidget(btn_agregar_actor)

        partes_layout.addWidget(actores_group)

        # Columna Demandados
        demandados_group = QGroupBox("DEMANDADOS")
        demandados_layout = QVBoxLayout(demandados_group)

        self.lista_demandados = QListWidget()
        demandados_layout.addWidget(self.lista_demandados)

        btn_agregar_demandado = QPushButton("➕ Agregar Demandado")
        demandados_layout.addWidget(btn_agregar_demandado)

        partes_layout.addWidget(demandados_group)

        layout.addLayout(partes_layout)

        # Área de detalle de parte seleccionada
        detalle_group = QGroupBox("Detalle de la Parte")
        detalle_layout = QFormLayout(detalle_group)

        self.detalle_nombre = QLineEdit()
        self.detalle_tipo_doc = QComboBox()
        self.detalle_tipo_doc.addItems(["DNI", "CUIL", "CUIT", "Pasaporte"])
        self.detalle_numero_doc = QLineEdit()
        self.detalle_telefono = QLineEdit()
        self.detalle_email = QLineEdit()
        self.detalle_domicilio = QTextEdit()
        self.detalle_domicilio.setMaximumHeight(60)

        detalle_layout.addRow("Nombre/Razón Social:", self.detalle_nombre)
        detalle_layout.addRow("Tipo Documento:", self.detalle_tipo_doc)
        detalle_layout.addRow("Número Documento:", self.detalle_numero_doc)
        detalle_layout.addRow("Teléfono:", self.detalle_telefono)
        detalle_layout.addRow("Email:", self.detalle_email)
        detalle_layout.addRow("Domicilio:", self.detalle_domicilio)

        layout.addWidget(detalle_group)

        # Cargar datos de ejemplo
        self.cargar_partes()

        return widget

    def crear_tab_cronologia(self):
        """Tab con línea de tiempo del expediente"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Timeline visual
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Crear eventos de timeline
        eventos = [
            ("2024-01-15", "Inicio del Expediente", "Se presenta la demanda inicial", "inicio"),
            ("2024-02-20", "Notificación a Demandado", "Se notifica al demandado de la demanda", "notificacion"),
            ("2024-03-10", "Contestación de Demanda", "El demandado presenta su contestación", "contestacion"),
            ("2024-04-15", "Apertura a Prueba", "Se abre el período probatorio", "prueba"),
            ("2024-06-30", "Ofrecimiento de Pruebas", "Las partes ofrecen sus pruebas", "prueba"),
            ("2024-07-20", "Producción de Pruebas", "Se producen las pruebas testimoniales", "prueba"),
            ("2024-08-30", "Vista para Alegar", "Última actuación registrada", "actual")
        ]

        for fecha, titulo, descripcion, tipo in eventos:
            evento_widget = self.crear_evento_timeline(fecha, titulo, descripcion, tipo)
            scroll_layout.addWidget(evento_widget)

        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)

        layout.addWidget(scroll_area)

        return widget

    def crear_evento_timeline(self, fecha, titulo, descripcion, tipo):
        """Crea un widget para un evento del timeline"""
        evento_frame = QFrame()
        evento_frame.setFixedHeight(80)

        layout = QHBoxLayout(evento_frame)
        layout.setContentsMargins(15, 10, 15, 10)

        # Icono según tipo
        icono_label = QLabel()
        iconos = {
            "inicio": "🚀",
            "notificacion": "📧",
            "contestacion": "📝",
            "prueba": "🔍",
            "actual": "📌"
        }
        icono_label.setText(iconos.get(tipo, "📄"))
        icono_label.setFixedSize(30, 30)
        icono_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icono_label)

        # Línea vertical (simulada)
        linea = QFrame()
        linea.setFixedWidth(2)
        layout.addWidget(linea)

        # Contenido del evento
        contenido_layout = QVBoxLayout()

        fecha_label = QLabel(fecha)
        fecha_label.setStyleSheet("font-size: 12px; color: #666;")
        contenido_layout.addWidget(fecha_label)

        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        contenido_layout.addWidget(titulo_label)

        desc_label = QLabel(descripcion)
        desc_label.setStyleSheet("font-size: 12px; color: #888;")
        contenido_layout.addWidget(desc_label)

        layout.addLayout(contenido_layout)
        layout.addStretch()

        return evento_frame

    def crear_tab_notas(self):
        """Tab para notas y observaciones personales"""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Toolbar para notas
        toolbar_layout = QHBoxLayout()

        btn_nueva_nota = QPushButton("➕ Nueva Nota")
        btn_nueva_nota.clicked.connect(self.nueva_nota)
        toolbar_layout.addWidget(btn_nueva_nota)

        btn_buscar_nota = QPushButton("🔍 Buscar")
        toolbar_layout.addWidget(btn_buscar_nota)

        toolbar_layout.addStretch()

        # Filtro por categoría
        filtro_categoria = QComboBox()
        filtro_categoria.addItems(["Todas", "Estrategia", "Recordatorios", "Observaciones", "Contactos"])
        toolbar_layout.addWidget(filtro_categoria)

        layout.addLayout(toolbar_layout)

        # Lista de notas
        self.lista_notas = QListWidget()

        # Agregar notas de ejemplo
        self.cargar_notas()

        layout.addWidget(self.lista_notas)

        # Editor de nota
        editor_group = QGroupBox("Editor de Nota")
        editor_layout = QVBoxLayout(editor_group)

        # Campos de la nota
        campos_layout = QHBoxLayout()

        campos_layout.addWidget(QLabel("Categoría:"))
        self.nota_categoria = QComboBox()
        self.nota_categoria.addItems(["Estrategia", "Recordatorios", "Observaciones", "Contactos"])
        campos_layout.addWidget(self.nota_categoria)

        campos_layout.addWidget(QLabel("Fecha:"))
        self.nota_fecha = QDateEdit(calendarPopup=True)
        self.nota_fecha.setDate(QDate.currentDate())
        campos_layout.addWidget(self.nota_fecha)

        campos_layout.addStretch()

        editor_layout.addLayout(campos_layout)

        # Título de la nota
        titulo_layout = QHBoxLayout()
        titulo_layout.addWidget(QLabel("Título:"))
        self.nota_titulo = QLineEdit()
        titulo_layout.addWidget(self.nota_titulo)
        editor_layout.addLayout(titulo_layout)

        # Contenido de la nota
        editor_layout.addWidget(QLabel("Contenido:"))
        self.nota_contenido = QTextEdit()
        self.nota_contenido.setMaximumHeight(120)
        editor_layout.addWidget(self.nota_contenido)

        # Botones del editor
        botones_layout = QHBoxLayout()
        btn_guardar_nota = QPushButton("💾 Guardar")
        btn_cancelar_nota = QPushButton("❌ Cancelar")

        botones_layout.addStretch()
        botones_layout.addWidget(btn_guardar_nota)
        botones_layout.addWidget(btn_cancelar_nota)

        editor_layout.addLayout(botones_layout)
        layout.addWidget(editor_group)

        return widget

    def crear_footer(self):
        """Crea el footer con acciones principales"""
        self.footer_widget = QFrame()
        self.footer_widget.setFixedHeight(80)

        layout = QHBoxLayout(self.footer_widget)
        layout.setContentsMargins(20, 15, 20, 15)

        # Botones de acción
        btn_volver = QPushButton("⬅️ Volver al Listado")
        btn_volver.setFixedHeight(40)
        btn_volver.clicked.connect(self.volver_listado)
        layout.addWidget(btn_volver)

        layout.addStretch()

        # Acciones del expediente
        btn_imprimir = QPushButton("🖨️ Imprimir Carátula")
        btn_imprimir.setFixedHeight(40)
        layout.addWidget(btn_imprimir)

        btn_pdf = QPushButton("📄 Generar Reporte PDF")
        btn_pdf.setFixedHeight(40)
        btn_pdf.clicked.connect(self.generar_pdf)
        layout.addWidget(btn_pdf)

        btn_email = QPushButton("📧 Enviar por Email")
        btn_email.setFixedHeight(40)
        layout.addWidget(btn_email)

        btn_agendar = QPushButton("📅 Agendar Seguimiento")
        btn_agendar.setFixedHeight(40)
        btn_agendar.clicked.connect(self.agendar_seguimiento)
        layout.addWidget(btn_agendar)

    def cargar_datos(self):
        """Carga los datos del expediente en la vista"""
        # Header
        self.numero_label.setText(f"<h2>{self.expediente_data['numero']}</h2>")
        self.caratula_label.setText(f"<h3 style='color: #374151;'>{self.expediente_data['caratula']}</h3>")
        self.dependencia_label.setText(f"<b>Dependencia:</b> {self.expediente_data['dependencia']}")

        # Estado
        self.estado_label.setText(self.expediente_data['situacion'])
        self.prioridad_label.setText(f"PRIORIDAD {self.expediente_data['prioridad'].upper()}")

        # Info adicional
        info_texto = f"""
        <b>Tipo:</b> {self.expediente_data['tipo_proceso']}<br>
        <b>Materia:</b> {self.expediente_data['materia']}<br>
        <b>Monto:</b> {self.expediente_data['monto']}<br>
        <b>Responsable:</b> {self.expediente_data['abogado_responsable']}
        """
        self.info_adicional.setText(info_texto)

    def cargar_actuaciones(self):
        """Carga las actuaciones en la tabla"""
        actuaciones = [
            ("30/08/2024", "Providencia", "Vista al actor para alegar sobre el mérito de la prueba", "Dr. Martínez"),
            ("15/08/2024", "Resolución", "Se tiene por producida la prueba testimonial", "Dr. Martínez"),
            ("10/08/2024", "Providencia", "Se señala audiencia para testimonial", "Secretario"),
            ("25/07/2024", "Notificación", "Se notifica ofrecimiento de pruebas", "Mesa de Entradas"),
            ("20/07/2024", "Providencia", "Se tienen por ofrecidas las pruebas", "Dr. Martínez"),
        ]

        self.tabla_actuaciones.setRowCount(len(actuaciones))

        for row, (fecha, tipo, descripcion, funcionario) in enumerate(actuaciones):
            self.tabla_actuaciones.setItem(row, 0, QTableWidgetItem(fecha))
            self.tabla_actuaciones.setItem(row, 1, QTableWidgetItem(tipo))
            self.tabla_actuaciones.setItem(row, 2, QTableWidgetItem(descripcion))
            self.tabla_actuaciones.setItem(row, 3, QTableWidgetItem(funcionario))

    def cargar_documentos(self):
        """Carga los documentos en la lista"""
        documentos = [
            ("📄", "Demanda_inicial.pdf"),
            ("📄", "Contestacion_demanda.pdf"),
            ("📊", "Prueba_pericial.xlsx"),
            ("🖼️", "Fotos_evidencia.jpg"),
            ("📄", "Escrito_alegatos.docx"),
        ]

        for icono, nombre in documentos:
            item = QListWidgetItem(f"{icono}\n{nombre}")
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.lista_documentos.addItem(item)

    def cargar_partes(self):
        """Carga las partes del proceso"""
        # Actores
        actores = ["GARCÍA, JUAN CARLOS - DNI 12.345.678"]
        for actor in actores:
            self.lista_actores.addItem(actor)

        # Demandados
        demandados = ["EMPRESA XYZ S.A. - CUIT 30-12345678-9"]
        for demandado in demandados:
            self.lista_demandados.addItem(demandado)

    def cargar_notas(self):
        """Carga las notas existentes"""
        notas = [
            "💡 Estrategia - Enfocar en negligencia del demandado",
            "⏰ Recordatorio - Vencimiento alegatos: 15/09/2024",
            "👁️ Observación - Cliente muy ansioso por resultados",
            "📞 Contacto - Hablar con perito el viernes"
        ]

        for nota in notas:
            self.lista_notas.addItem(nota)

    def setup_style(self):
        """Configura los estilos de la aplicación"""
        self.setStyleSheet("""
            QWidget {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 9pt;
            }

            QFrame {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }

            QTabWidget::pane {
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background-color: white;
            }

            QTabBar::tab {
                background-color: #f8fafc;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
            }

            QTabBar::tab:selected {
                background-color: white;
                border-bottom: 2px solid #3b82f6;
            }

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

            QPushButton:pressed {
                background-color: #1d4ed8;
            }

            QTableWidget {
                gridline-color: #e2e8f0;
                background-color: white;
                alternate-background-color: #f8fafc;
            }

            QTableWidget::item {
                padding: 8px;
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)

    # Métodos de eventos
    def volver_listado(self):
        """Vuelve al listado de expedientes"""
        self.close()

    def generar_pdf(self):
        """Genera un reporte PDF del expediente"""
        QMessageBox.information(self, "Generar PDF",
                                f"Generando reporte PDF para {self.expediente_data['numero']}")

    def agendar_seguimiento(self):
        """Abre diálogo para agendar seguimiento"""
        QMessageBox.information(self, "Agendar Seguimiento",
                                "Función de agenda en desarrollo")

    def agregar_documento(self):
        """Agrega un nuevo documento"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar Documento", "",
            "Todos los archivos (*);;PDF (*.pdf);;Word (*.docx);;Excel (*.xlsx)"
        )
        if file_path:
            # Aquí iría la lógica para agregar el documento
            QMessageBox.information(self, "Documento Agregado",
                                    f"Documento agregado: {file_path}")

    def mostrar_menu_documento(self, position):
        """Muestra menú contextual para documentos"""
        menu = QMenu(self)

        abrir_action = QAction("Abrir", self)
        descargar_action = QAction("Descargar", self)
        eliminar_action = QAction("Eliminar", self)

        menu.addAction(abrir_action)
        menu.addAction(descargar_action)
        menu.addSeparator()
        menu.addAction(eliminar_action)

        menu.exec(self.lista_documentos.mapToGlobal(position))

    def nueva_nota(self):
        """Crea una nueva nota"""
        self.nota_titulo.clear()
        self.nota_contenido.clear()
        self.nota_fecha.setDate(QDate.currentDate())
        self.nota_titulo.setFocus()


# Aplicación de ejemplo
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Configurar el estilo de la aplicación
    app.setStyle('Fusion')

    # Crear y mostrar la ventana
    ventana = VistaDetalleExpediente()
    ventana.show()

    sys.exit(app.exec())


class DialogoAgregarParte(QDialog):
    """Diálogo para agregar nuevas partes al expediente"""

    def __init__(self, tipo_parte="actor", parent=None):
        super().__init__(parent)
        self.tipo_parte = tipo_parte
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        self.setWindowTitle(f"Agregar {self.tipo_parte.title()}")
        self.setFixedSize(500, 400)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Título
        titulo = QLabel(f"Agregar Nuevo {self.tipo_parte.title()}")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b;")
        layout.addWidget(titulo)

        # Formulario
        form_layout = QFormLayout()

        # Tipo de persona
        self.tipo_persona = QComboBox()
        self.tipo_persona.addItems(["Persona Física", "Persona Jurídica"])
        self.tipo_persona.currentTextChanged.connect(self.cambiar_tipo_persona)
        form_layout.addRow("Tipo de Persona:", self.tipo_persona)

        # Nombre/Razón Social
        self.nombre = QLineEdit()
        self.nombre.setPlaceholderText("Ingrese nombre completo o razón social")
        form_layout.addRow("Nombre/Razón Social:", self.nombre)

        # Tipo y número de documento
        doc_layout = QHBoxLayout()
        self.tipo_documento = QComboBox()
        self.actualizar_tipos_documento()
        doc_layout.addWidget(self.tipo_documento)

        self.numero_documento = QLineEdit()
        self.numero_documento.setPlaceholderText("Número sin puntos ni guiones")
        doc_layout.addWidget(self.numero_documento)

        form_layout.addRow("Documento:", doc_layout)

        # Información de contacto
        self.telefono = QLineEdit()
        self.telefono.setPlaceholderText("Ej: +54 11 1234-5678")
        form_layout.addRow("Teléfono:", self.telefono)

        self.email = QLineEdit()
        self.email.setPlaceholderText("correo@ejemplo.com")
        form_layout.addRow("Email:", self.email)

        # Domicilio
        self.domicilio = QTextEdit()
        self.domicilio.setMaximumHeight(80)
        self.domicilio.setPlaceholderText("Domicilio completo (calle, número, ciudad, provincia)")
        form_layout.addRow("Domicilio:", self.domicilio)

        # Campos específicos para persona jurídica
        self.campos_juridica = QWidget()
        juridica_layout = QFormLayout(self.campos_juridica)

        self.representante = QLineEdit()
        self.representante.setPlaceholderText("Nombre del representante legal")
        juridica_layout.addRow("Representante Legal:", self.representante)

        self.cargo_representante = QLineEdit()
        self.cargo_representante.setPlaceholderText("Ej: Presidente, Gerente General")
        juridica_layout.addRow("Cargo:", self.cargo_representante)

        self.campos_juridica.setVisible(False)

        layout.addLayout(form_layout)
        layout.addWidget(self.campos_juridica)

        # Botones
        botones_layout = QHBoxLayout()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        botones_layout.addWidget(btn_cancelar)

        botones_layout.addStretch()

        btn_guardar = QPushButton("Guardar")
        btn_guardar.clicked.connect(self.guardar_parte)
        btn_guardar.setDefault(True)
        botones_layout.addWidget(btn_guardar)

        layout.addLayout(botones_layout)

    def cambiar_tipo_persona(self, tipo):
        """Cambia los campos según el tipo de persona"""
        es_juridica = tipo == "Persona Jurídica"
        self.campos_juridica.setVisible(es_juridica)
        self.actualizar_tipos_documento()

        if es_juridica:
            self.nombre.setPlaceholderText("Razón social completa")
        else:
            self.nombre.setPlaceholderText("Apellido, Nombre")

    def actualizar_tipos_documento(self):
        """Actualiza los tipos de documento según el tipo de persona"""
        self.tipo_documento.clear()

        if self.tipo_persona.currentText() == "Persona Física":
            self.tipo_documento.addItems(["DNI", "LC", "LE", "Pasaporte", "CI"])
        else:
            self.tipo_documento.addItems(["CUIT", "CDI"])

    def guardar_parte(self):
        """Valida y guarda la nueva parte"""
        if not self.nombre.text().strip():
            QMessageBox.warning(self, "Error", "Debe ingresar un nombre o razón social")
            return

        if not self.numero_documento.text().strip():
            QMessageBox.warning(self, "Error", "Debe ingresar un número de documento")
            return

        # Aquí iría la lógica para guardar en la base de datos
        QMessageBox.information(self, "Éxito", f"{self.tipo_parte.title()} agregado correctamente")
        self.accept()

    def setup_style(self):
        """Configura los estilos del diálogo"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }

            QLineEdit, QTextEdit, QComboBox {
                padding: 8px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background-color: white;
            }

            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #3b82f6;
                outline: none;
            }

            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 500;
            }

            QPushButton:hover {
                background-color: #2563eb;
            }

            QPushButton:pressed {
                background-color: #1d4ed8;
            }
        """)


class DialogoNuevaNota(QDialog):
    """Diálogo para crear una nueva nota"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        self.setWindowTitle("Nueva Nota")
        self.setFixedSize(600, 500)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        # Título
        titulo = QLabel("Crear Nueva Nota")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold; color: #1e293b;")
        layout.addWidget(titulo)

        # Formulario
        form_layout = QFormLayout()

        # Categoría
        self.categoria = QComboBox()
        self.categoria.addItems([
            "💡 Estrategia",
            "⏰ Recordatorio",
            "👁️ Observación",
            "📞 Contacto",
            "📋 Tarea",
            "⚠️ Importante"
        ])
        form_layout.addRow("Categoría:", self.categoria)

        # Fecha y hora
        fecha_layout = QHBoxLayout()

        self.fecha = QDateEdit(calendarPopup=True)
        self.fecha.setDate(QDate.currentDate())
        fecha_layout.addWidget(self.fecha)

        self.hora = QTimeEdit()
        self.hora.setTime(QTime.currentTime())
        fecha_layout.addWidget(self.hora)

        form_layout.addRow("Fecha y Hora:", fecha_layout)

        # Título de la nota
        self.titulo_nota = QLineEdit()
        self.titulo_nota.setPlaceholderText("Título descriptivo de la nota")
        form_layout.addRow("Título:", self.titulo_nota)

        # Prioridad
        self.prioridad = QComboBox()
        self.prioridad.addItems(["Baja", "Media", "Alta", "Urgente"])
        self.prioridad.setCurrentText("Media")
        form_layout.addRow("Prioridad:", self.prioridad)

        layout.addLayout(form_layout)

        # Contenido
        layout.addWidget(QLabel("Contenido:"))
        self.contenido = QTextEdit()
        self.contenido.setPlaceholderText("Escriba aquí el contenido de la nota...")
        layout.addWidget(self.contenido)

        # Recordatorio
        recordatorio_group = QGroupBox("Recordatorio")
        recordatorio_layout = QVBoxLayout(recordatorio_group)

        self.activar_recordatorio = QCheckBox("Activar recordatorio")
        recordatorio_layout.addWidget(self.activar_recordatorio)

        recordatorio_fecha_layout = QHBoxLayout()
        self.fecha_recordatorio = QDateTimeEdit(calendarPopup=True)
        self.fecha_recordatorio.setDateTime(QDateTime.currentDateTime().addDays(1))
        self.fecha_recordatorio.setEnabled(False)

        self.activar_recordatorio.toggled.connect(self.fecha_recordatorio.setEnabled)

        recordatorio_fecha_layout.addWidget(QLabel("Fecha:"))
        recordatorio_fecha_layout.addWidget(self.fecha_recordatorio)
        recordatorio_fecha_layout.addStretch()

        recordatorio_layout.addLayout(recordatorio_fecha_layout)
        layout.addWidget(recordatorio_group)

        # Botones
        botones_layout = QHBoxLayout()

        btn_cancelar = QPushButton("Cancelar")
        btn_cancelar.clicked.connect(self.reject)
        botones_layout.addWidget(btn_cancelar)

        botones_layout.addStretch()

        btn_guardar = QPushButton("Guardar Nota")
        btn_guardar.clicked.connect(self.guardar_nota)
        btn_guardar.setDefault(True)
        botones_layout.addWidget(btn_guardar)

        layout.addLayout(botones_layout)

    def guardar_nota(self):
        """Valida y guarda la nueva nota"""
        if not self.titulo_nota.text().strip():
            QMessageBox.warning(self, "Error", "Debe ingresar un título para la nota")
            return

        if not self.contenido.toPlainText().strip():
            QMessageBox.warning(self, "Error", "Debe ingresar contenido para la nota")
            return

        # Aquí iría la lógica para guardar la nota
        nota_data = {
            'categoria': self.categoria.currentText(),
            'fecha': self.fecha.date().toString('dd/MM/yyyy'),
            'hora': self.hora.time().toString('hh:mm'),
            'titulo': self.titulo_nota.text(),
            'contenido': self.contenido.toPlainText(),
            'prioridad': self.prioridad.currentText(),
            'recordatorio': self.activar_recordatorio.isChecked(),
            'fecha_recordatorio': self.fecha_recordatorio.dateTime().toString(
                'dd/MM/yyyy hh:mm') if self.activar_recordatorio.isChecked() else None
        }

        QMessageBox.information(self, "Éxito", "Nota guardada correctamente")
        self.accept()

    def setup_style(self):
        """Configura los estilos del diálogo"""
        self.setStyleSheet("""
            QDialog {
                background-color: #f8fafc;
            }

            QLineEdit, QTextEdit, QComboBox, QDateEdit, QTimeEdit, QDateTimeEdit {
                padding: 8px;
                border: 1px solid #d1d5db;
                border-radius: 4px;
                background-color: white;
            }

            QLineEdit:focus, QTextEdit:focus, QComboBox:focus {
                border-color: #3b82f6;
                outline: none;
            }

            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-weight: 500;
            }

            QPushButton:hover {
                background-color: #2563eb;
            }

            QGroupBox {
                font-weight: bold;
                border: 2px solid #e2e8f0;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
            }

            QCheckBox {
                font-weight: normal;
            }
        """)


class WidgetEstadisticasExpediente(QWidget):
    """Widget que muestra estadísticas del expediente"""

    def __init__(self, expediente_data=None):
        super().__init__()
        self.expediente_data = expediente_data
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        layout = QGridLayout(self)
        layout.setSpacing(10)

        # Crear tarjetas de estadísticas
        self.crear_tarjeta_tiempo("⏱️", "Tiempo Transcurrido", "227 días", layout, 0, 0)
        self.crear_tarjeta_tiempo("📋", "Total Actuaciones", "15", layout, 0, 1)
        self.crear_tarjeta_tiempo("📎", "Documentos", "8", layout, 0, 2)
        self.crear_tarjeta_tiempo("💰", "Monto en Disputa", "$2.500.000", layout, 0, 3)

        self.crear_tarjeta_tiempo("🎯", "Estado Procesal", "Período de Prueba", layout, 1, 0)
        self.crear_tarjeta_tiempo("👥", "Partes", "2", layout, 1, 1)
        self.crear_tarjeta_tiempo("📝", "Notas Personales", "4", layout, 1, 2)
        self.crear_tarjeta_tiempo("📅", "Próximo Vto.", "15/09/2024", layout, 1, 3)

    def crear_tarjeta_tiempo(self, icono, titulo, valor, layout, row, col):
        """Crea una tarjeta de estadística"""
        tarjeta = QFrame()
        tarjeta.setFixedSize(160, 80)

        tarjeta_layout = QVBoxLayout(tarjeta)
        tarjeta_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tarjeta_layout.setSpacing(5)

        # Fila superior: icono y título
        header_layout = QHBoxLayout()

        icono_label = QLabel(icono)
        icono_label.setStyleSheet("font-size: 20px;")
        header_layout.addWidget(icono_label)

        titulo_label = QLabel(titulo)
        titulo_label.setStyleSheet("font-size: 10px; color: #6b7280; font-weight: 500;")
        header_layout.addWidget(titulo_label)
        header_layout.addStretch()

        tarjeta_layout.addLayout(header_layout)

        # Valor principal
        valor_label = QLabel(valor)
        valor_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #1f2937;")
        valor_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tarjeta_layout.addWidget(valor_label)

        layout.addWidget(tarjeta, row, col)

    def setup_style(self):
        """Configura los estilos del widget"""
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 8px;
            }

            QFrame:hover {
                border-color: #3b82f6;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }
        """)


# Función para agregar el widget de estadísticas a la vista principal
def agregar_estadisticas_a_vista(vista_expediente):
    """Agrega el widget de estadísticas a la vista principal"""
    # Insertar el widget de estadísticas después del header
    estadisticas = WidgetEstadisticasExpediente(vista_expediente.expediente_data)
    vista_expediente.layout().insertWidget(1, estadisticas)