import sys
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from datetime import datetime, timedelta

class ActuacionWidget(QFrame):
    """Widget individual de actuación con vista expandible"""
    
    documento_solicitado = Signal(str)
    
    def __init__(self, actuacion, parent=None):
        super().__init__(parent)
        self.actuacion = actuacion
        self.expandido = False
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                margin: 2px 0px;
            }
            QFrame:hover {
                border-color: #1976D2;
                background-color: #f8f9fa;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)
        
        # Header compacto
        header = QHBoxLayout()
        
        # Fecha con ícono según antigüedad
        dias = (datetime.now() - datetime.strptime(self.actuacion['fecha'], '%d/%m/%Y')).days
        if dias <= 7:
            icono_fecha = "🆕"
            color_fecha = "#4CAF50"
        elif dias <= 30:
            icono_fecha = "📅"
            color_fecha = "#FF9800"
        else:
            icono_fecha = "📆"
            color_fecha = "#757575"
        
        fecha_label = QLabel(f"{icono_fecha} {self.actuacion['fecha']}")
        fecha_label.setStyleSheet(f"color: {color_fecha}; font-weight: bold; font-size: 12px;")
        fecha_label.setFixedWidth(120)
        
        # Tipo de actuación destacado
        tipo_label = QLabel(self.actuacion['tipo'])
        tipo_label.setStyleSheet("""
            background-color: #E3F2FD;
            color: #1565C0;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 11px;
            font-weight: bold;
        """)
        tipo_label.setFixedWidth(180)
        
        # Descripción truncada
        desc_label = QLabel(self.actuacion['descripcion'][:80] + "..." if len(self.actuacion['descripcion']) > 80 else self.actuacion['descripcion'])
        desc_label.setStyleSheet("color: #424242; font-size: 12px;")
        
        # Botones de acción
        acciones = QHBoxLayout()
        
        if self.actuacion.get('tiene_documento'):
            btn_ver = QPushButton("👁️")
            btn_ver.setFixedSize(28, 28)
            btn_ver.setToolTip("Vista rápida")
            btn_ver.clicked.connect(lambda: self.documento_solicitado.emit(self.actuacion['id']))
            btn_ver.setStyleSheet("""
                QPushButton {
                    background-color: #1976D2;
                    color: white;
                    border: none;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #1565C0;
                }
            """)
            
            btn_descargar = QPushButton("⬇️")
            btn_descargar.setFixedSize(28, 28)
            btn_descargar.setToolTip("Descargar")
            btn_descargar.setStyleSheet(btn_ver.styleSheet())
            
            acciones.addWidget(btn_ver)
            acciones.addWidget(btn_descargar)
        
        btn_expandir = QPushButton("⋯")
        btn_expandir.setFixedSize(28, 28)
        btn_expandir.setToolTip("Ver detalles")
        btn_expandir.clicked.connect(self.toggle_expandir)
        btn_expandir.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #757575;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-color: #1976D2;
            }
        """)
        acciones.addWidget(btn_expandir)
        
        header.addWidget(fecha_label)
        header.addWidget(tipo_label)
        header.addWidget(desc_label, 1)
        header.addLayout(acciones)
        
        layout.addLayout(header)
        
        # Detalles expandibles (inicialmente oculto)
        self.detalles_widget = QWidget()
        self.detalles_widget.setVisible(False)
        detalles_layout = QVBoxLayout(self.detalles_widget)
        detalles_layout.setContentsMargins(0, 8, 0, 0)
        
        # Descripción completa
        desc_completa = QLabel(self.actuacion['descripcion'])
        desc_completa.setWordWrap(True)
        desc_completa.setStyleSheet("color: #616161; font-size: 11px; padding: 8px; background-color: #f5f5f5; border-radius: 4px;")
        detalles_layout.addWidget(desc_completa)
        
        # Metadata adicional
        if self.actuacion.get('folio'):
            meta = QLabel(f"📄 Folios: {self.actuacion['folio']} | 🏛️ Oficina: {self.actuacion['oficina']}")
            meta.setStyleSheet("color: #9e9e9e; font-size: 10px;")
            detalles_layout.addWidget(meta)
        
        layout.addWidget(self.detalles_widget)
    
    def toggle_expandir(self):
        self.expandido = not self.expandido
        self.detalles_widget.setVisible(self.expandido)


class VisorDocumentoRapido(QFrame):
    """Visor rápido de documentos en panel lateral"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-left: 3px solid #1976D2;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header = QHBoxLayout()
        
        titulo = QLabel("Vista Rápida del Documento")
        titulo.setStyleSheet("font-weight: bold; font-size: 14px; color: #1565C0;")
        
        btn_cerrar = QPushButton("✕")
        btn_cerrar.setFixedSize(24, 24)
        btn_cerrar.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                color: #757575;
            }
            QPushButton:hover {
                background-color: #f5f5f5;
                border-radius: 4px;
            }
        """)
        
        header.addWidget(titulo)
        header.addStretch()
        header.addWidget(btn_cerrar)
        
        layout.addLayout(header)
        
        # Información del documento
        info = QLabel("📄 CÉDULA ELECTRÓNICA PARTE\nCÉDULA N° 2500009772063\nNotificado: 12/09/2025 21:13")
        info.setStyleSheet("color: #424242; font-size: 11px; padding: 12px; background-color: #E3F2FD; border-radius: 6px;")
        layout.addWidget(info)
        
        # Área de contenido
        contenido = QTextEdit()
        contenido.setReadOnly(True)
        contenido.setStyleSheet("""
            QTextEdit {
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                padding: 8px;
                font-size: 12px;
                background-color: #fafafa;
            }
        """)
        contenido.setPlainText(
            "PARANÁ, 12 de Septiembre de 2025\n\n"
            "AUTOS Y VISTOS:\n"
            "Por devueltos los presentes autos. Por practicada la liquidación "
            "presentada, córrase traslado a la contraria por el plazo de cinco días...\n\n"
            "[Contenido simulado del documento]"
        )
        layout.addWidget(contenido, 1)
        
        # Acciones
        acciones = QHBoxLayout()
        
        btn_descargar = QPushButton("⬇️ Descargar PDF")
        btn_descargar.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        
        btn_imprimir = QPushButton("🖨️ Imprimir")
        btn_imprimir.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #1976D2;
                border: 1px solid #1976D2;
                border-radius: 6px;
                padding: 8px 16px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #E3F2FD;
            }
        """)
        
        acciones.addWidget(btn_descargar)
        acciones.addWidget(btn_imprimir)
        
        layout.addLayout(acciones)


class FiltrosInteligentes(QFrame):
    """Panel de filtros inteligentes y búsqueda"""
    
    filtro_aplicado = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        self.setFixedHeight(120)
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border-bottom: 2px solid #e0e0e0;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        
        # Búsqueda rápida
        busqueda_layout = QHBoxLayout()
        
        busqueda = QLineEdit()
        busqueda.setPlaceholderText("🔍 Buscar actuación, documento, fecha... (Ctrl+F)")
        busqueda.setStyleSheet("""
            QLineEdit {
                padding: 10px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 13px;
                background-color: white;
            }
            QLineEdit:focus {
                border-color: #1976D2;
            }
        """)
        busqueda_layout.addWidget(busqueda, 1)
        
        # Filtros rápidos
        btn_nuevas = QPushButton("🆕 Nuevas (7 días)")
        btn_nuevas.setCheckable(True)
        btn_nuevas.setStyleSheet(self.estilo_filtro())
        
        btn_documentos = QPushButton("📎 Con documentos")
        btn_documentos.setCheckable(True)
        btn_documentos.setStyleSheet(self.estilo_filtro())
        
        btn_cedulas = QPushButton("📬 Cédulas")
        btn_cedulas.setCheckable(True)
        btn_cedulas.setStyleSheet(self.estilo_filtro())
        
        busqueda_layout.addWidget(btn_nuevas)
        busqueda_layout.addWidget(btn_documentos)
        busqueda_layout.addWidget(btn_cedulas)
        
        layout.addLayout(busqueda_layout)
        
        # Filtros avanzados
        avanzados_layout = QHBoxLayout()
        
        # Rango de fechas
        fecha_desde = QDateEdit()
        fecha_desde.setCalendarPopup(True)
        fecha_desde.setDate(QDate.currentDate().addMonths(-1))
        fecha_desde.setStyleSheet(self.estilo_input())
        
        fecha_hasta = QDateEdit()
        fecha_hasta.setCalendarPopup(True)
        fecha_hasta.setDate(QDate.currentDate())
        fecha_hasta.setStyleSheet(self.estilo_input())
        
        # Tipo de actuación
        tipo_combo = QComboBox()
        tipo_combo.addItems(["Todos los tipos", "Cédulas", "Movimientos", "Escritos", "Sentencias", "Providencias"])
        tipo_combo.setStyleSheet(self.estilo_input())
        
        # Oficina
        oficina_combo = QComboBox()
        oficina_combo.addItems(["Todas las oficinas", "CIV", "C/2"])
        oficina_combo.setStyleSheet(self.estilo_input())
        
        avanzados_layout.addWidget(QLabel("Desde:"))
        avanzados_layout.addWidget(fecha_desde)
        avanzados_layout.addWidget(QLabel("Hasta:"))
        avanzados_layout.addWidget(fecha_hasta)
        avanzados_layout.addWidget(QLabel("Tipo:"))
        avanzados_layout.addWidget(tipo_combo)
        avanzados_layout.addWidget(QLabel("Oficina:"))
        avanzados_layout.addWidget(oficina_combo)
        avanzados_layout.addStretch()
        
        # Botón aplicar
        btn_aplicar = QPushButton("Aplicar Filtros")
        btn_aplicar.setStyleSheet("""
            QPushButton {
                background-color: #1976D2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1565C0;
            }
        """)
        avanzados_layout.addWidget(btn_aplicar)
        
        layout.addLayout(avanzados_layout)
    
    def estilo_filtro(self):
        return """
            QPushButton {
                background-color: white;
                color: #424242;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                border-color: #1976D2;
                color: #1976D2;
            }
            QPushButton:checked {
                background-color: #1976D2;
                color: white;
                border-color: #1976D2;
            }
        """
    
    def estilo_input(self):
        return """
            QDateEdit, QComboBox {
                padding: 6px 10px;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
            }
            QDateEdit:focus, QComboBox:focus {
                border-color: #1976D2;
            }
        """


class ResumenExpediente(QFrame):
    """Panel resumen siempre visible"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        self.setFixedHeight(80)
        self.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565C0, stop:1 #1976D2);
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        
        # Info principal
        info_layout = QVBoxLayout()
        
        caratula = QLabel("ABALLAY, ABRAHAM ARTUS Y OTROS C/ ESTADO NACIONAL ARG.")
        caratula.setStyleSheet("color: white; font-size: 15px; font-weight: bold;")
        
        detalles = QLabel("📋 FPA 024925/2018 • ⚖️ Juzgado Federal Paraná 2 • 📅 Última act: 12/09/2025")
        detalles.setStyleSheet("color: #E3F2FD; font-size: 11px;")
        
        info_layout.addWidget(caratula)
        info_layout.addWidget(detalles)
        
        layout.addLayout(info_layout, 1)
        
        # Estado y acciones
        estado = QLabel("EN LETRA")
        estado.setStyleSheet("""
            background-color: #4CAF50;
            color: white;
            padding: 6px 16px;
            border-radius: 16px;
            font-size: 12px;
            font-weight: bold;
        """)
        estado.setFixedHeight(32)
        
        # Estadísticas rápidas
        stats = QHBoxLayout()
        stats.setSpacing(20)
        
        for valor, label in [("156", "Actuaciones"), ("48", "Documentos"), ("12", "Escritos")]:
            stat_widget = QWidget()
            stat_layout = QVBoxLayout(stat_widget)
            stat_layout.setContentsMargins(0, 0, 0, 0)
            stat_layout.setSpacing(2)
            
            valor_label = QLabel(valor)
            valor_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
            valor_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            texto_label = QLabel(label)
            texto_label.setStyleSheet("color: #E3F2FD; font-size: 9px;")
            texto_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            stat_layout.addWidget(valor_label)
            stat_layout.addWidget(texto_label)
            
            stats.addWidget(stat_widget)
        
        layout.addWidget(estado)
        layout.addLayout(stats)


class SistemaJudicialOptimizado(QMainWindow):
    """Sistema optimizado para trabajo diario con expedientes"""
    
    def __init__(self):
        super().__init__()
        self.actuaciones_data = self.cargar_datos_ejemplo()
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Sistema de Expedientes - Optimizado para Trabajo Diario")
        self.setGeometry(100, 100, 1600, 900)
        
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Resumen siempre visible
        resumen = ResumenExpediente()
        layout.addWidget(resumen)
        
        # Filtros inteligentes
        filtros = FiltrosInteligentes()
        layout.addWidget(filtros)
        
        # Contenido principal con splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Lista de actuaciones (izquierda)
        scroll_actuaciones = QScrollArea()
        scroll_actuaciones.setWidgetResizable(True)
        scroll_actuaciones.setStyleSheet("border: none; background-color: #fafafa;")
        
        actuaciones_widget = QWidget()
        actuaciones_layout = QVBoxLayout(actuaciones_widget)
        actuaciones_layout.setContentsMargins(12, 12, 12, 12)
        actuaciones_layout.setSpacing(4)
        
        # Agregar actuaciones agrupadas por fecha
        self.agregar_actuaciones_agrupadas(actuaciones_layout)
        
        actuaciones_layout.addStretch()
        scroll_actuaciones.setWidget(actuaciones_widget)
        
        # Visor rápido (derecha)
        visor = VisorDocumentoRapido()
        
        splitter.addWidget(scroll_actuaciones)
        splitter.addWidget(visor)
        splitter.setSizes([1000, 600])
        
        layout.addWidget(splitter, 1)
        
        # Barra de estado con info útil
        self.crear_barra_estado()
    
    def agregar_actuaciones_agrupadas(self, layout):
        """Agrupa actuaciones por fecha para mejor organización"""
        
        # Agrupar por fecha
        por_fecha = {}
        for act in self.actuaciones_data:
            fecha = act['fecha']
            if fecha not in por_fecha:
                por_fecha[fecha] = []
            por_fecha[fecha].append(act)
        
        # Mostrar agrupadas
        for fecha in sorted(por_fecha.keys(), key=lambda x: datetime.strptime(x, '%d/%m/%Y'), reverse=True):
            # Header de fecha
            header = QLabel(f"📅 {fecha}")
            header.setStyleSheet("""
                color: #1565C0;
                font-weight: bold;
                font-size: 13px;
                padding: 8px 4px;
                background-color: #E3F2FD;
                border-radius: 4px;
            """)
            layout.addWidget(header)
            
            # Actuaciones de ese día
            for act in por_fecha[fecha]:
                widget = ActuacionWidget(act)
                layout.addWidget(widget)
            
            # Separador
            layout.addSpacing(8)
    
    def crear_barra_estado(self):
        status = self.statusBar()
        status.setStyleSheet("""
            QStatusBar {
                background-color: #f5f5f5;
                color: #616161;
                border-top: 1px solid #e0e0e0;
                font-size: 11px;
            }
        """)
        
        # Info útil
        status.addWidget(QLabel("⌨️ Ctrl+F: Buscar"))
        status.addWidget(QLabel(" | "))
        status.addWidget(QLabel("⌨️ Ctrl+D: Descargar selección"))
        status.addWidget(QLabel(" | "))
        status.addWidget(QLabel("⌨️ Ctrl+T: Vista timeline"))
        status.addPermanentWidget(QLabel("📊 Mostrando 23 de 156 actuaciones"))
    
    def cargar_datos_ejemplo(self):
        """Datos realistas del portal"""
        return [
            {
                'id': '1',
                'fecha': '12/09/2025',
                'oficina': 'C/2',
                'tipo': 'CÉDULA ELECTRÓNICA',
                'descripcion': 'CÉDULA ELECTRÓNICA PARTE - CÉDULA N° 2500009772063 - NOTIFICADO EL 12/09/2025 21:13',
                'folio': '',
                'tiene_documento': True
            },
            {
                'id': '2',
                'fecha': '12/09/2025',
                'oficina': 'C/2',
                'tipo': 'MOVIMIENTO',
                'descripcion': 'EN LETRA - POR DEVUELTOS. POR PRACTICADA LIQUIDACION. DE LA MISMA TRASLADO',
                'folio': '213/213',
                'tiene_documento': True
            },
            {
                'id': '3',
                'fecha': '12/09/2025',
                'oficina': 'C/2',
                'tipo': 'ESCRITO AGREGADO',
                'descripcion': 'ACTOR ACOMPAÑA LIQUIDACIÓN [Presentado 07/09/2025 13:37]',
                'folio': '111/212',
                'tiene_documento': True
            },
            {
                'id': '4',
                'fecha': '04/09/2025',
                'oficina': 'CIV',
                'tipo': 'MOVIMIENTO',
                'descripcion': 'EN LETRA',
                'folio': '',
                'tiene_documento': False
            },
            {
                'id': '5',
                'fecha': '04/09/2025',
                'oficina': 'CIV',
                'tipo': 'RECEPCION PASE',
                'descripcion': 'JUZGADO FEDERAL DE PARANÁ 2 - SECRETARIA CIVIL Y COMERCIAL 2',
                'folio': '',
                'tiene_documento': False
            },
            {
                'id': '6',
                'fecha': '20/08/2025',
                'oficina': 'CIV',
                'tipo': 'PUBLICACION SENTENCIA',
                'descripcion': 'SENTENCIA - 20/08/2025',
                'folio': '',
                'tiene_documento': True
            },
            {
                'id': '7',
                'fecha': '20/08/2025',
                'oficina': 'CIV',
                'tipo': 'MOVIMIENTO',
                'descripcion': 'EN LETRA',
                'folio': '',
                'tiene_documento': False
            },
            {
                'id': '8',
                'fecha': '20/08/2025',
                'oficina': 'CIV',
                'tipo': 'CÉDULA ELECTRÓNICA TRIBUNAL',
                'descripcion': 'CÉDULA N° 25000096559010 - NOTIFICADO EL DIA: 20/08/2025 11:49',
                'folio': '',
                'tiene_documento': True
            }
        ]


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    ventana = SistemaJudicialOptimizado()
    ventana.show()
    
    sys.exit(app.exec())