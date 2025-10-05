import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from datetime import datetime, timedelta


class SolapaButton(QPushButton):
    """Botón personalizado para las solapas laterales"""

    def __init__(self, icon_name, solapa_id, color="#3b82f6", parent=None):
        super().__init__(parent)
        self.solapa_id = solapa_id
        self.color = color
        self.is_active = False

        # Configuración del botón
        self.setFixedSize(40, 40)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Ícono (usando texto unicode como iconos)
        icons = {
            'info': '📊',
            'timeline': '📅',
            'docs': '📎',
            'partes': '👥',
            'actuaciones': '⚖️',
            'notas': '📝'
        }
        self.setText(icons.get(icon_name, '•'))

        self.update_style()

    def set_active(self, active):
        self.is_active = active
        self.update_style()

    def update_style(self):
        if self.is_active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {self.color};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 18px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {self.color};
                    transform: scale(1.05);
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: #f3f4f6;
                    color: #6b7280;
                    border: none;
                    border-radius: 8px;
                    font-size: 18px;
                }}
                QPushButton:hover {{
                    background-color: #e5e7eb;
                }}
            """)


class PanelInformacion(QWidget):
    """Panel de información del expediente"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Datos del expediente
        grupo_datos = QGroupBox("Datos del Expediente")
        grupo_datos.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)

        datos_layout = QFormLayout()
        datos_layout.setSpacing(8)

        datos_layout.addRow("Número:", self.create_label("EXP-2024-001234-PJN"))
        datos_layout.addRow("Estado:", self.create_badge("En Trámite", "#10b981"))
        datos_layout.addRow("Inicio:", self.create_label("15/01/2024"))
        datos_layout.addRow("Última act.:", self.create_label("02/10/2024"))

        grupo_datos.setLayout(datos_layout)
        layout.addWidget(grupo_datos)

        # Estadísticas
        grupo_stats = QGroupBox("Estadísticas")
        grupo_stats.setStyleSheet(grupo_datos.styleSheet())

        stats_layout = QGridLayout()
        stats_layout.setSpacing(8)

        stats_layout.addWidget(self.create_stat_card("24", "Actuaciones", "#3b82f6"), 0, 0)
        stats_layout.addWidget(self.create_stat_card("15", "Documentos", "#ef4444"), 0, 1)
        stats_layout.addWidget(self.create_stat_card("3", "Audiencias", "#8b5cf6"), 1, 0)
        stats_layout.addWidget(self.create_stat_card("268", "Días", "#10b981"), 1, 1)

        grupo_stats.setLayout(stats_layout)
        layout.addWidget(grupo_stats)

        # Vencimientos
        grupo_venc = QGroupBox("Próximos Vencimientos")
        grupo_venc.setStyleSheet(grupo_datos.styleSheet())

        venc_layout = QVBoxLayout()
        venc_layout.addWidget(self.create_alert("⚠️", "Alegatos pendientes", "Vence: 10/10/2024", "#f59e0b"))
        venc_layout.addWidget(self.create_alert("📅", "Audiencia programada", "15/10/2024 - 10:00 hs", "#3b82f6"))

        grupo_venc.setLayout(venc_layout)
        layout.addWidget(grupo_venc)

        layout.addStretch()

    def create_label(self, text):
        label = QLabel(text)
        label.setStyleSheet("font-size: 12px; color: #1f2937;")
        return label

    def create_badge(self, text, color):
        badge = QLabel(text)
        badge.setStyleSheet(f"""
            background-color: {color}20;
            color: {color};
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        """)
        badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        return badge

    def create_stat_card(self, value, label, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color}20;
                border-radius: 6px;
                padding: 8px;
            }}
        """)

        layout = QVBoxLayout(card)
        layout.setSpacing(2)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 20px; font-weight: bold; color: {color};")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        text_label = QLabel(label)
        text_label.setStyleSheet(f"font-size: 10px; color: {color};")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(value_label)
        layout.addWidget(text_label)

        return card

    def create_alert(self, icon, title, subtitle, color):
        alert = QFrame()
        alert.setStyleSheet(f"""
            QFrame {{
                background-color: {color}20;
                border: 1px solid {color}40;
                border-radius: 6px;
                padding: 8px;
            }}
        """)

        layout = QHBoxLayout(alert)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 16px; color: {color};")

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)

        title_label = QLabel(title)
        title_label.setStyleSheet(f"font-size: 12px; font-weight: bold; color: {color};")

        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(f"font-size: 10px; color: {color}aa;")

        text_layout.addWidget(title_label)
        text_layout.addWidget(subtitle_label)

        layout.addWidget(icon_label)
        layout.addLayout(text_layout)

        return alert


class PanelTimeline(QWidget):
    """Panel de timeline resumido"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Eventos Cronológicos")
        title.setStyleSheet("font-weight: bold; font-size: 13px;")

        expandir_btn = QPushButton("Expandir →")
        expandir_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #3b82f6;
                font-size: 11px;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(expandir_btn)
        layout.addLayout(header)

        # Lista de eventos
        eventos = [
            {"tipo": "Inicio", "fecha": "15/01/2024", "desc": "Presentación de demanda"},
            {"tipo": "Providencia", "fecha": "25/01/2024", "desc": "Traslado al demandado"},
            {"tipo": "Contestación", "fecha": "10/02/2024", "desc": "Demandado contesta"},
            {"tipo": "Audiencia", "fecha": "20/03/2024", "desc": "Audiencia preliminar"},
        ]

        for evento in eventos:
            layout.addWidget(self.create_evento_item(evento))

        layout.addStretch()

        # Botón ver todos
        ver_todos = QPushButton("Ver Timeline Completo")
        ver_todos.setStyleSheet("""
            QPushButton {
                background-color: #eff6ff;
                color: #3b82f6;
                border: none;
                border-radius: 6px;
                padding: 8px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #dbeafe;
            }
        """)
        layout.addWidget(ver_todos)

    def create_evento_item(self, evento):
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 8px;
            }
            QFrame:hover {
                background-color: #f3f4f6;
            }
        """)

        layout = QHBoxLayout(item)
        layout.setSpacing(8)

        # Punto timeline
        punto = QLabel("●")
        punto.setStyleSheet("color: #3b82f6; font-size: 8px;")
        punto.setFixedWidth(10)

        # Contenido
        content_layout = QVBoxLayout()
        content_layout.setSpacing(2)

        header_layout = QHBoxLayout()
        tipo_label = QLabel(evento["tipo"])
        tipo_label.setStyleSheet("font-weight: bold; font-size: 11px;")

        fecha_label = QLabel(evento["fecha"])
        fecha_label.setStyleSheet("font-size: 10px; color: #6b7280;")

        header_layout.addWidget(tipo_label)
        header_layout.addWidget(fecha_label)
        header_layout.addStretch()

        desc_label = QLabel(evento["desc"])
        desc_label.setStyleSheet("font-size: 10px; color: #9ca3af;")

        content_layout.addLayout(header_layout)
        content_layout.addWidget(desc_label)

        layout.addWidget(punto)
        layout.addLayout(content_layout)

        return item


class PanelDocumentos(QWidget):
    """Panel de documentos"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QHBoxLayout()
        title = QLabel("Archivos del Expediente")
        title.setStyleSheet("font-weight: bold; font-size: 13px;")

        upload_btn = QPushButton("📤")
        upload_btn.setFixedSize(30, 30)
        upload_btn.setStyleSheet("""
            QPushButton {
                background-color: #eff6ff;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #dbeafe;
            }
        """)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(upload_btn)
        layout.addLayout(header)

        # Lista de documentos
        documentos = [
            {"nombre": "Demanda Inicial.pdf", "tipo": "Demanda", "tamaño": "2.3 MB", "fecha": "15/01/2024"},
            {"nombre": "Contestación.pdf", "tipo": "Contestación", "tamaño": "1.8 MB", "fecha": "10/02/2024"},
            {"nombre": "Pruebas Actor.pdf", "tipo": "Prueba", "tamaño": "4.5 MB", "fecha": "05/03/2024"},
            {"nombre": "Pericia Contable.pdf", "tipo": "Pericia", "tamaño": "3.2 MB", "fecha": "15/04/2024"},
        ]

        for doc in documentos:
            layout.addWidget(self.create_doc_item(doc))

        layout.addStretch()

    def create_doc_item(self, doc):
        item = QFrame()
        item.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                padding: 8px;
            }
            QFrame:hover {
                background-color: #f3f4f6;
            }
        """)

        layout = QHBoxLayout(item)
        layout.setSpacing(10)

        # Ícono
        icon_frame = QFrame()
        icon_frame.setFixedSize(32, 32)
        icon_frame.setStyleSheet("""
            QFrame {
                background-color: #fee2e2;
                border-radius: 6px;
            }
        """)
        icon_layout = QVBoxLayout(icon_frame)
        icon_layout.setContentsMargins(0, 0, 0, 0)
        icon = QLabel("📄")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_layout.addWidget(icon)

        # Info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        nombre = QLabel(doc["nombre"])
        nombre.setStyleSheet("font-size: 11px; font-weight: bold;")

        detalles = QLabel(f"{doc['tipo']} • {doc['tamaño']} • {doc['fecha']}")
        detalles.setStyleSheet("font-size: 9px; color: #6b7280;")

        info_layout.addWidget(nombre)
        info_layout.addWidget(detalles)

        # Acciones
        acciones = QHBoxLayout()

        ver_btn = QPushButton("👁️")
        ver_btn.setFixedSize(24, 24)
        ver_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
                border-radius: 4px;
            }
        """)

        download_btn = QPushButton("⬇️")
        download_btn.setFixedSize(24, 24)
        download_btn.setStyleSheet(ver_btn.styleSheet())

        acciones.addWidget(ver_btn)
        acciones.addWidget(download_btn)

        layout.addWidget(icon_frame)
        layout.addLayout(info_layout, 1)
        layout.addLayout(acciones)

        return item


class PanelLateral(QFrame):
    """Panel lateral expandible para las solapas (ahora a la derecha)"""

    solapa_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.expanded = True
        self.current_solapa = "info"
        self.setup_ui()

    def setup_ui(self):
        self.setFixedWidth(320)
        self.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border-left: 1px solid #e5e7eb;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setFixedHeight(50)
        header.setStyleSheet("border-bottom: 1px solid #e5e7eb; padding: 12px;")
        header_layout = QHBoxLayout(header)

        self.title_label = QLabel("Información")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 13px;")

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                font-size: 14px;
                color: #6b7280;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
                border-radius: 4px;
            }
        """)
        close_btn.clicked.connect(self.toggle_panel)

        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(close_btn)

        layout.addWidget(header)

        # Contenido con QStackedWidget
        self.stack = QStackedWidget()
        self.stack.addWidget(PanelInformacion())  # 0
        self.stack.addWidget(PanelTimeline())  # 1
        self.stack.addWidget(PanelDocumentos())  # 2
        self.stack.addWidget(QLabel("Partes"))  # 3
        self.stack.addWidget(QLabel("Actuaciones"))  # 4
        self.stack.addWidget(QLabel("Notas"))  # 5

        layout.addWidget(self.stack)

    def cambiar_solapa(self, solapa_id):
        self.current_solapa = solapa_id

        # Mapeo de IDs a índices del stack
        solapas_map = {
            'info': (0, "Información"),
            'timeline': (1, "Timeline"),
            'docs': (2, "Documentos"),
            'partes': (3, "Partes"),
            'actuaciones': (4, "Actuaciones"),
            'notas': (5, "Notas")
        }

        if solapa_id in solapas_map:
            index, titulo = solapas_map[solapa_id]
            self.stack.setCurrentIndex(index)
            self.title_label.setText(titulo)

            if not self.expanded:
                self.toggle_panel()

    def toggle_panel(self):
        self.expanded = not self.expanded

        # Animación suave
        self.animation = QPropertyAnimation(self, b"minimumWidth")
        self.animation.setDuration(200)
        self.animation.setStartValue(self.width())
        self.animation.setEndValue(320 if self.expanded else 0)
        self.animation.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.animation_max = QPropertyAnimation(self, b"maximumWidth")
        self.animation_max.setDuration(200)
        self.animation_max.setStartValue(self.width())
        self.animation_max.setEndValue(320 if self.expanded else 0)
        self.animation_max.setEasingCurve(QEasingCurve.Type.InOutQuad)

        self.animation.start()
        self.animation_max.start()


class VentanaExpedienteSolapas(QMainWindow):
    """Ventana principal con interfaz de solapas laterales a la DERECHA"""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        self.setWindowTitle("Sistema de Gestión de Expedientes - EXP-2024-001234-PJN")
        self.setGeometry(100, 100, 1400, 800)

        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar de navegación (IZQUIERDA)
        sidebar = self.crear_sidebar()
        main_layout.addWidget(sidebar)

        # Área principal (CENTRO)
        area_principal = self.crear_area_principal()
        main_layout.addLayout(area_principal, 1)

        # Barra de solapas (DERECHA)
        solapas_bar = self.crear_barra_solapas()
        main_layout.addWidget(solapas_bar)

        # Panel lateral expandible (DERECHA)
        self.panel_lateral = PanelLateral()
        main_layout.addWidget(self.panel_lateral)

    def crear_sidebar(self):
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #1f2937;
                border-right: 1px solid #374151;
            }
        """)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Logo/Header
        header = QHBoxLayout()
        logo = QLabel("⚖️")
        logo.setStyleSheet("font-size: 24px;")
        title = QLabel("LexSystem")
        title.setStyleSheet("color: white; font-weight: bold; font-size: 14px;")
        header.addWidget(logo)
        header.addWidget(title)
        header.addStretch()
        layout.addLayout(header)

        layout.addSpacing(20)

        # Menú de navegación
        nav_items = [
            ("🏠", "Inicio", False),
            ("📁", "Expedientes", True),
            ("📅", "Agenda", False),
            ("👥", "Clientes", False),
            ("📊", "Reportes", False),
            ("🔔", "Notificaciones", False),
        ]

        for icon, label, active in nav_items:
            btn = self.crear_nav_button(icon, label, active)
            layout.addWidget(btn)

        layout.addStretch()

        # Settings al final
        settings = self.crear_nav_button("⚙️", "Configuración", False)
        layout.addWidget(settings)

        return sidebar

    def crear_nav_button(self, icon, label, active):
        btn = QPushButton(f"{icon}  {label}")
        if active:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #3b82f6;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    padding: 10px;
                    text-align: left;
                    font-size: 13px;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    color: #9ca3af;
                    border: none;
                    border-radius: 6px;
                    padding: 10px;
                    text-align: left;
                    font-size: 13px;
                }
                QPushButton:hover {
                    background-color: #374151;
                    color: white;
                }
            """)
        return btn

    def crear_barra_solapas(self):
        """Barra de solapas ahora a la DERECHA"""
        solapas_frame = QFrame()
        solapas_frame.setFixedWidth(54)
        solapas_frame.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border-left: 1px solid #e5e7eb;
            }
        """)

        layout = QVBoxLayout(solapas_frame)
        layout.setContentsMargins(7, 16, 7, 16)
        layout.setSpacing(8)

        # Configuración de solapas
        solapas_config = [
            ('info', 'info', '#3b82f6'),
            ('timeline', 'timeline', '#8b5cf6'),
            ('docs', 'docs', '#ef4444'),
            ('partes', 'partes', '#10b981'),
            ('actuaciones', 'actuaciones', '#f59e0b'),
            ('notas', 'notas', '#eab308'),
        ]

        self.solapa_buttons = []
        for icon, solapa_id, color in solapas_config:
            btn = SolapaButton(icon, solapa_id, color)
            btn.clicked.connect(lambda checked, sid=solapa_id: self.cambiar_solapa(sid))
            layout.addWidget(btn)
            self.solapa_buttons.append(btn)

        # Marcar primera como activa
        self.solapa_buttons[0].set_active(True)

        layout.addStretch()

        return solapas_frame

    def cambiar_solapa(self, solapa_id):
        # Actualizar botones
        for btn in self.solapa_buttons:
            btn.set_active(btn.solapa_id == solapa_id)

        # Cambiar panel
        self.panel_lateral.cambiar_solapa(solapa_id)

    def crear_area_principal(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header superior
        header = self.crear_header()
        layout.addWidget(header)

        # Información del expediente
        info_expediente = self.crear_info_expediente()
        layout.addWidget(info_expediente)

        # Área de contenido/documento
        contenido = self.crear_area_contenido()
        layout.addWidget(contenido, 1)

        return layout

    def crear_header(self):
        header = QFrame()
        header.setFixedHeight(60)
        header.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border-bottom: 1px solid #e5e7eb;
            }
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(20, 12, 20, 12)

        # Breadcrumb
        breadcrumb = QLabel("Expedientes  >  EXP-2024-001234-PJN")
        breadcrumb.setStyleSheet("font-size: 12px; color: #6b7280;")
        layout.addWidget(breadcrumb)

        # Buscador
        search = QLineEdit()
        search.setPlaceholderText("🔍 Buscar en el expediente...")
        search.setFixedWidth(300)
        search.setStyleSheet("""
            QLineEdit {
                padding: 8px 12px;
                border: 1px solid #e5e7eb;
                border-radius: 6px;
                background-color: white;
                font-size: 12px;
            }
            QLineEdit:focus {
                border-color: #3b82f6;
            }
        """)
        layout.addWidget(search)

        layout.addStretch()

        # Acciones rápidas
        dark_mode = QPushButton("🌙")
        dark_mode.setFixedSize(36, 36)
        dark_mode.setStyleSheet("""
            QPushButton {
                background-color: #f3f4f6;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: #e5e7eb;
            }
        """)

        notif = QPushButton("🔔")
        notif.setFixedSize(36, 36)
        notif.setStyleSheet(dark_mode.styleSheet())

        avatar = QPushButton("JG")
        avatar.setFixedSize(36, 36)
        avatar.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 18px;
                font-weight: bold;
                font-size: 12px;
            }
        """)

        layout.addWidget(dark_mode)
        layout.addWidget(notif)
        layout.addWidget(avatar)

        return header

    def crear_info_expediente(self):
        info = QFrame()
        info.setFixedHeight(90)
        info.setStyleSheet("""
            QFrame {
                background-color: #f9fafb;
                border-bottom: 1px solid #e5e7eb;
            }
        """)

        layout = QVBoxLayout(info)
        layout.setContentsMargins(20, 12, 20, 12)

        # Título y estado
        header_layout = QHBoxLayout()

        titulo = QLabel("GARCÍA, JUAN C/ PÉREZ, MARÍA S/ CUMPLIMIENTO DE CONTRATO")
        titulo.setStyleSheet("font-size: 16px; font-weight: bold;")

        estado = QLabel("En Trámite")
        estado.setStyleSheet("""
            background-color: #d1fae5;
            color: #065f46;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        """)

        header_layout.addWidget(titulo)
        header_layout.addWidget(estado)
        header_layout.addStretch()

        # Botones
        btn_actuacion = QPushButton("➕ Nueva Actuación")
        btn_actuacion.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)

        btn_documento = QPushButton("📤 Subir Documento")
        btn_documento.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #374151;
                border: 1px solid #d1d5db;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #f9fafb;
            }
        """)

        header_layout.addWidget(btn_actuacion)
        header_layout.addWidget(btn_documento)

        layout.addLayout(header_layout)

        # Detalles
        detalles = QLabel("📋 EXP-2024-001234-PJN  •  ⚖️ Juzgado Nacional Civil N° 45  •  📅 Inicio: 15/01/2024")
        detalles.setStyleSheet("font-size: 11px; color: #6b7280;")
        layout.addWidget(detalles)

        return info

    def crear_area_contenido(self):
        contenido = QFrame()
        contenido.setStyleSheet("""
            QFrame {
                background-color: white;
                margin: 16px;
                border-radius: 8px;
                border: 1px solid #e5e7eb;
            }
        """)

        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar del documento
        toolbar = QFrame()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet("border-bottom: 1px solid #e5e7eb;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(16, 8, 16, 8)

        doc_title = QLabel("📄 Demanda Inicial.pdf")
        doc_title.setStyleSheet("font-weight: 600; font-size: 13px;")
        toolbar_layout.addWidget(doc_title)
        toolbar_layout.addStretch()

        # Botones del toolbar
        for icon in ["🔍", "⛶", "⬇️"]:
            btn = QPushButton(icon)
            btn.setFixedSize(32, 32)
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #f3f4f6;
                }
            """)
            toolbar_layout.addWidget(btn)

        layout.addWidget(toolbar)

        # Área de visualización del documento
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")

        documento = QWidget()
        doc_layout = QVBoxLayout(documento)
        doc_layout.setContentsMargins(60, 40, 60, 40)

        # Contenido simulado del documento
        doc_text = QTextEdit()
        doc_text.setReadOnly(True)
        doc_text.setStyleSheet("""
            QTextEdit {
                border: none;
                font-size: 13px;
                line-height: 1.6;
                color: #1f2937;
            }
        """)
        doc_text.setHtml("""
            <h2>DEMANDA POR CUMPLIMIENTO DE CONTRATO</h2>
            <p><strong>Señor Juez:</strong></p>
            <p><strong>JUAN CARLOS GARCÍA</strong>, por derecho propio, con domicilio real en Av. Corrientes 1234, 
            Ciudad Autónoma de Buenos Aires, constituyendo domicilio legal en Av. de Mayo 567, piso 3°, 
            oficina "B" de esta ciudad, a V.S. respetuosamente digo:</p>

            <h3>I. OBJETO</h3>
            <p>Que en legal tiempo y forma, vengo a promover demanda por cumplimiento de contrato en contra 
            de la Sra. <strong>MARÍA SOLEDAD PÉREZ</strong>, domiciliada en Av. Rivadavia 5678 de esta ciudad, 
            por la suma de PESOS QUINIENTOS MIL ($500.000), con más sus intereses y costas...</p>

            <h3>II. HECHOS</h3>
            <p>Con fecha 15 de marzo de 2023, mi representado celebró con la demandada un contrato de 
            compraventa de inmueble...</p>

            <h3>III. DERECHO</h3>
            <p>La presente acción se funda en las disposiciones del Código Civil y Comercial de la Nación, 
            particularmente en los artículos 957 y siguientes relativos al cumplimiento de las obligaciones...</p>

            <p style="margin-top: 40px;"><strong>Por todo lo expuesto, solicito a V.S.:</strong></p>
            <ol>
                <li>Tenga por presentada la demanda en legal tiempo y forma.</li>
                <li>Se corra traslado a la parte demandada.</li>
                <li>Oportunamente, se haga lugar a la demanda con costas.</li>
            </ol>

            <p style="margin-top: 60px; text-align: right;">Proveer de conformidad,<br/>
            <strong>Dr. Alberto Rodríguez</strong><br/>
            Letrado del Actor</p>
        """)

        doc_layout.addWidget(doc_text)

        scroll.setWidget(documento)
        layout.addWidget(scroll)

        return contenido

    def setup_style(self):
        """Estilos globales de la aplicación"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #f3f4f6;
                width: 10px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical {
                background: #9ca3af;
                border-radius: 5px;
                min-height: 20px;
            }
            QScrollBar::handle:vertical:hover {
                background: #6b7280;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Configurar fuente
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    ventana = VentanaExpedienteSolapas()
    ventana.show()

    sys.exit(app.exec())