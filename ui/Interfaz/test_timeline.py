import sys
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *
from datetime import datetime, timedelta
import math


class EventoTimeline:
    """Representa un evento en el timeline"""

    def __init__(self, fecha, titulo, descripcion, categoria, duracion_dias=1, color=None):
        self.fecha = fecha
        self.titulo = titulo
        self.descripcion = descripcion
        self.categoria = categoria
        self.duracion_dias = duracion_dias
        self.color = color or self.get_color_por_categoria()
        self.seleccionado = False

    def get_color_por_categoria(self):
        """Asigna colores según la categoría"""
        colores = {
            'juzgado': QColor(59, 130, 246),  # Azul - Actuaciones del juzgado
            'partes': QColor(16, 185, 129),  # Verde - Escritos de partes
            'documentos': QColor(245, 158, 11),  # Amarillo - Documentos
            'audiencias': QColor(239, 68, 68),  # Rojo - Audiencias
            'notificaciones': QColor(139, 92, 246),  # Púrpura - Notificaciones
            'hitos': QColor(75, 85, 99)  # Gris - Hitos importantes
        }
        return colores.get(self.categoria, QColor(156, 163, 175))


class TimelineWidget(QWidget):
    """Widget principal del timeline estilo editor de video"""

    evento_seleccionado = pyqtSignal(EventoTimeline)

    def __init__(self):
        super().__init__()

        # INICIALIZAR TODAS LAS VARIABLES PRIMERO - ANTES DE CUALQUIER MÉTODO
        self.eventos = []
        self.zoom_level = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 5.0
        self.pixels_por_dia = 3  # ESTA VARIABLE DEBE EXISTIR ANTES DE setup_datos_ejemplo
        self.altura_track = 60
        self.margen_lateral = 80
        self.scroll_offset = 0

        # Estado de interacción
        self.evento_arrastrado = None
        self.posicion_arrastre = None
        self.evento_seleccionado_actual = None

        # Fechas por defecto
        self.fecha_inicio = datetime.now() - timedelta(days=30)
        self.fecha_fin = datetime.now() + timedelta(days=30)

        # Configuraciones de UI
        self.setMinimumHeight(400)
        self.setMouseTracking(True)

        # Configurar tracks
        self.tracks = [
            {'nombre': '🏛️ Actuaciones Juzgado', 'categoria': 'juzgado', 'y': 0},
            {'nombre': '📝 Escritos Partes', 'categoria': 'partes', 'y': 1},
            {'nombre': '📎 Documentos', 'categoria': 'documentos', 'y': 2},
            {'nombre': '⚖️ Audiencias', 'categoria': 'audiencias', 'y': 3},
            {'nombre': '🔔 Notificaciones', 'categoria': 'notificaciones', 'y': 4}
        ]

        # Scrollbar horizontal - CREAR DESPUÉS DE LAS VARIABLES
        self.h_scrollbar = QScrollBar(Qt.Orientation.Horizontal)
        self.h_scrollbar.valueChanged.connect(self.on_scroll_horizontal)

        # AHORA SÍ llamar a los métodos que usan las variables
        self.cargar_datos_ejemplo()
        self.setup_ui()

    def cargar_datos_ejemplo(self):
        """Crea datos de ejemplo para el timeline"""
        base_date = datetime(2024, 1, 15)

        eventos_data = [
            # Juzgado
            (0, "Inicio Expediente", "Se presenta la demanda inicial", "juzgado"),
            (10, "Providencia", "Se ordena traslado al demandado", "juzgado"),
            (45, "Resolución", "Se tiene por contestada la demanda", "juzgado"),
            (60, "Providencia", "Se abre a prueba", "juzgado"),
            (120, "Resolución", "Se clausura período probatorio", "juzgado"),
            (140, "Vista para Alegar", "Se concede vista para alegar", "juzgado"),

            # Partes
            (5, "Demanda Inicial", "Presentación de la demanda", "partes"),
            (40, "Contestación", "Demandado contesta demanda", "partes"),
            (65, "Ofrecimiento Pruebas Actor", "Actor ofrece pruebas", "partes"),
            (70, "Ofrecimiento Pruebas Demandado", "Demandado ofrece pruebas", "partes"),
            (145, "Alegatos Actor", "Presentación alegatos del actor", "partes"),

            # Documentos
            (8, "Poder Especial", "Se agrega poder del abogado", "documentos"),
            (12, "Documentación Respaldatoria", "Contratos y facturas", "documentos"),
            (75, "Pericia Contable", "Informe pericial contable", "documentos"),
            (95, "Prueba Testimonial", "Declaraciones testimoniales", "documentos"),

            # Audiencias
            (85, "Audiencia Testimonial", "Declaración de testigos", "audiencias", 1),
            (100, "Audiencia Pericial", "Explicaciones del perito", "audiencias", 1),

            # Notificaciones
            (15, "Notif. Demandado", "Cédula de notificación", "notificaciones"),
            (50, "Notif. Apertura Prueba", "Notificación apertura a prueba", "notificaciones"),
            (125, "Notif. Clausura", "Notificación clausura prueba", "notificaciones"),
        ]

        # Limpiar eventos anteriores
        self.eventos.clear()

        for dias, titulo, desc, categoria, *extra in eventos_data:
            duracion = extra[0] if extra else 1
            fecha = base_date + timedelta(days=dias)
            evento = EventoTimeline(fecha, titulo, desc, categoria, duracion)
            self.eventos.append(evento)

        # Calcular rango de fechas
        if self.eventos:
            fechas = [e.fecha for e in self.eventos]
            self.fecha_inicio = min(fechas) - timedelta(days=10)
            self.fecha_fin = max(fechas) + timedelta(days=30)

    def setup_ui(self):
        """Configura la interfaz del timeline"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Toolbar superior
        toolbar = self.crear_toolbar()
        layout.addWidget(toolbar)

        # Área del timeline (self como widget de dibujo)
        timeline_frame = QFrame()
        timeline_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        timeline_layout = QVBoxLayout(timeline_frame)
        timeline_layout.setContentsMargins(0, 0, 0, 0)
        timeline_layout.setSpacing(0)

        # Widget de dibujo del timeline
        self.canvas_widget = QWidget()
        self.canvas_widget.paintEvent = self.paintEvent
        self.canvas_widget.mousePressEvent = self.mousePressEvent
        self.canvas_widget.mouseMoveEvent = self.mouseMoveEvent
        self.canvas_widget.wheelEvent = self.wheelEvent
        self.canvas_widget.setMinimumHeight(350)
        timeline_layout.addWidget(self.canvas_widget, 1)

        # Scrollbar horizontal
        timeline_layout.addWidget(self.h_scrollbar)

        layout.addWidget(timeline_frame)

        # Panel de información del evento seleccionado
        self.info_panel = self.crear_panel_info()
        layout.addWidget(self.info_panel)

        # Actualizar scrollbar después de que todo esté creado
        self.actualizar_scrollbar()

    def crear_toolbar(self):
        """Crea la barra de herramientas"""
        toolbar = QFrame()
        toolbar.setFixedHeight(50)
        toolbar.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
            }
        """)

        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(15, 10, 15, 10)

        # Controles de zoom
        layout.addWidget(QLabel("🔍"))

        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 500)  # 0.1x a 5.0x
        self.zoom_slider.setValue(100)  # 1.0x
        self.zoom_slider.setFixedWidth(150)
        self.zoom_slider.valueChanged.connect(self.cambiar_zoom)
        layout.addWidget(self.zoom_slider)

        self.zoom_label = QLabel("100%")
        self.zoom_label.setFixedWidth(50)
        layout.addWidget(self.zoom_label)

        layout.addWidget(QFrame())  # Separador

        # Controles de vista
        btn_fit_all = QPushButton("📏 Ajustar Todo")
        btn_fit_all.clicked.connect(self.ajustar_todo)
        layout.addWidget(btn_fit_all)

        btn_today = QPushButton("📅 Hoy")
        btn_today.clicked.connect(self.ir_a_hoy)
        layout.addWidget(btn_today)

        # Botón agregar evento
        btn_agregar = QPushButton("➕ Agregar Evento")
        btn_agregar.clicked.connect(self.agregar_evento)
        layout.addWidget(btn_agregar)

        layout.addStretch()

        # Leyenda de colores
        self.crear_leyenda(layout)

        return toolbar

    def crear_leyenda(self, layout):
        """Crea la leyenda de colores"""
        leyenda_frame = QFrame()
        leyenda_layout = QHBoxLayout(leyenda_frame)
        leyenda_layout.setSpacing(15)

        categorias = [
            ('juzgado', '🏛️ Juzgado'),
            ('partes', '📝 Partes'),
            ('documentos', '📎 Docs'),
            ('audiencias', '⚖️ Audiencias'),
            ('notificaciones', '🔔 Notif.')
        ]

        for categoria, texto in categorias:
            item_layout = QHBoxLayout()

            # Cuadrado de color
            color_square = QLabel()
            color_square.setFixedSize(12, 12)
            color = EventoTimeline(None, None, None, categoria).color
            color_square.setStyleSheet(f"""
                background-color: {color.name()};
                border-radius: 2px;
            """)
            item_layout.addWidget(color_square)

            # Texto
            texto_label = QLabel(texto)
            texto_label.setStyleSheet("font-size: 10px; color: #6b7280;")
            item_layout.addWidget(texto_label)

            item_widget = QWidget()
            item_widget.setLayout(item_layout)
            leyenda_layout.addWidget(item_widget)

        layout.addWidget(leyenda_frame)

    def crear_panel_info(self):
        """Crea el panel de información del evento seleccionado"""
        panel = QFrame()
        panel.setFixedHeight(100)
        panel.setStyleSheet("""
            QFrame {
                background-color: #f8fafc;
                border-top: 1px solid #e2e8f0;
            }
        """)

        layout = QHBoxLayout(panel)
        layout.setContentsMargins(20, 15, 20, 15)

        # Información del evento
        info_layout = QVBoxLayout()

        self.info_titulo = QLabel("Selecciona un evento para ver detalles")
        self.info_titulo.setStyleSheet("font-weight: bold; font-size: 14px; color: #1f2937;")
        info_layout.addWidget(self.info_titulo)

        self.info_descripcion = QLabel("")
        self.info_descripcion.setStyleSheet("color: #6b7280; font-size: 12px;")
        self.info_descripcion.setWordWrap(True)
        info_layout.addWidget(self.info_descripcion)

        self.info_fecha = QLabel("")
        self.info_fecha.setStyleSheet("color: #9ca3af; font-size: 11px;")
        info_layout.addWidget(self.info_fecha)

        layout.addLayout(info_layout, 1)

        # Botones de acción
        botones_layout = QVBoxLayout()

        btn_ver_detalle = QPushButton("👁️ Ver Detalle")
        btn_ver_detalle.clicked.connect(self.ver_detalle_evento)
        botones_layout.addWidget(btn_ver_detalle)

        btn_editar = QPushButton("✏️ Editar")
        btn_editar.clicked.connect(self.editar_evento)
        botones_layout.addWidget(btn_editar)

        layout.addLayout(botones_layout)

        return panel

    def paintEvent(self, event):
        """Dibuja el timeline"""
        painter = QPainter(self.canvas_widget if hasattr(self, 'canvas_widget') else self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        if hasattr(self, 'canvas_widget'):
            rect = self.canvas_widget.rect()
        else:
            rect = self.rect()

        # Fondo
        painter.fillRect(rect, QColor(255, 255, 255))

        # Dibujar grid y labels de tracks
        self.dibujar_tracks(painter, rect)

        # Dibujar línea de tiempo
        self.dibujar_linea_tiempo(painter, rect)

        # Dibujar eventos
        self.dibujar_eventos(painter, rect)

        # Dibujar línea de tiempo actual
        self.dibujar_linea_actual(painter, rect)

    def dibujar_tracks(self, painter, rect):
        """Dibuja los tracks y sus etiquetas"""
        font = QFont()
        font.setPointSize(9)
        painter.setFont(font)

        for i, track in enumerate(self.tracks):
            y = i * self.altura_track + 30  # 30px para la regla de tiempo

            # Línea separadora
            painter.setPen(QPen(QColor(229, 231, 235), 1))
            painter.drawLine(0, y, rect.width(), y)

            # Etiqueta del track
            label_rect = QRect(5, y + 5, self.margen_lateral - 10, self.altura_track - 10)
            painter.setPen(QPen(QColor(107, 114, 128)))
            painter.drawText(label_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, track['nombre'])

    def dibujar_linea_tiempo(self, painter, rect):
        """Dibuja la regla de tiempo superior"""
        painter.fillRect(0, 0, rect.width(), 30, QColor(248, 250, 252))
        painter.setPen(QPen(QColor(156, 163, 175), 1))
        painter.drawLine(0, 30, rect.width(), 30)

        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)

        # Calcular paso de tiempo basado en zoom
        dias_totales = (self.fecha_fin - self.fecha_inicio).days
        ancho_disponible = rect.width() - self.margen_lateral
        paso_dias = max(1, int(dias_totales / (ancho_disponible / 60)))  # Una marca cada ~60px

        fecha_actual = self.fecha_inicio
        while fecha_actual <= self.fecha_fin:
            x = self.fecha_a_x(fecha_actual, rect)
            if x >= self.margen_lateral and x <= rect.width():
                # Línea vertical
                painter.setPen(QPen(QColor(209, 213, 219), 1))
                painter.drawLine(x, 0, x, rect.height())

                # Texto de fecha
                painter.setPen(QPen(QColor(107, 114, 128)))
                fecha_texto = fecha_actual.strftime("%d/%m")
                painter.drawText(x - 20, 15, 40, 15, Qt.AlignmentFlag.AlignCenter, fecha_texto)

            fecha_actual += timedelta(days=paso_dias)

    def dibujar_eventos(self, painter, rect):
        """Dibuja los eventos en el timeline"""
        for evento in self.eventos:
            track_y = None
            for track in self.tracks:
                if track['categoria'] == evento.categoria:
                    track_y = track['y']
                    break

            if track_y is None:
                continue

            x = self.fecha_a_x(evento.fecha, rect)
            y = track_y * self.altura_track + 35  # 30px regla + 5px margen

            # Ancho del evento basado en duración
            ancho = max(20, evento.duracion_dias * self.pixels_por_dia * self.zoom_level)
            alto = self.altura_track - 15

            # Solo dibujar si está visible
            if x + ancho >= self.margen_lateral and x <= rect.width():
                # Fondo del evento
                color = evento.color
                if evento.seleccionado or evento == self.evento_seleccionado_actual:
                    color = color.lighter(120)
                    painter.setPen(QPen(QColor(59, 130, 246), 2))
                else:
                    painter.setPen(QPen(color.darker(110), 1))

                painter.setBrush(QBrush(color))
                evento_rect = QRect(x, y, ancho, alto)
                painter.drawRoundedRect(evento_rect, 4, 4)

                # Texto del evento
                painter.setPen(QPen(QColor(255, 255, 255) if color.lightness() < 128 else QColor(0, 0, 0)))
                font = QFont()
                font.setPointSize(8)
                font.setBold(True)
                painter.setFont(font)

                texto_rect = evento_rect.adjusted(4, 2, -4, -2)
                painter.drawText(texto_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, evento.titulo)

    def dibujar_linea_actual(self, painter, rect):
        """Dibuja una línea vertical para la fecha actual"""
        x = self.fecha_a_x(datetime.now(), rect)
        if x >= self.margen_lateral and x <= rect.width():
            painter.setPen(QPen(QColor(239, 68, 68), 2))
            painter.drawLine(x, 30, x, rect.height())

            # Triángulo en la parte superior
            triangle = [
                QPoint(x, 30),
                QPoint(x - 5, 20),
                QPoint(x + 5, 20)
            ]
            painter.setBrush(QBrush(QColor(239, 68, 68)))
            painter.drawPolygon(triangle)

    def fecha_a_x(self, fecha, rect):
        """Convierte una fecha a coordenada X"""
        if not fecha:
            return 0

        dias_desde_inicio = (fecha - self.fecha_inicio).days
        x = self.margen_lateral + (dias_desde_inicio * self.pixels_por_dia * self.zoom_level) - self.scroll_offset
        return int(x)

    def x_a_fecha(self, x, rect):
        """Convierte coordenada X a fecha"""
        dias = (x - self.margen_lateral + self.scroll_offset) / (self.pixels_por_dia * self.zoom_level)
        return self.fecha_inicio + timedelta(days=dias)

    def evento_en_posicion(self, pos):
        """Encuentra el evento en una posición dada"""
        for evento in self.eventos:
            track_y = None
            for track in self.tracks:
                if track['categoria'] == evento.categoria:
                    track_y = track['y']
                    break

            if track_y is None:
                continue

            rect = self.canvas_widget.rect() if hasattr(self, 'canvas_widget') else self.rect()
            x = self.fecha_a_x(evento.fecha, rect)
            y = track_y * self.altura_track + 35
            ancho = max(20, evento.duracion_dias * self.pixels_por_dia * self.zoom_level)
            alto = self.altura_track - 15

            evento_rect = QRect(x, y, ancho, alto)
            if evento_rect.contains(pos):
                return evento

        return None

    def mousePressEvent(self, event):
        """Maneja clicks del mouse"""
        if event.button() == Qt.MouseButton.LeftButton:
            evento = self.evento_en_posicion(event.pos())
            if evento:
                self.seleccionar_evento(evento)
                self.evento_arrastrado = evento
                self.posicion_arrastre = event.pos()

    def mouseMoveEvent(self, event):
        """Maneja movimiento del mouse"""
        evento = self.evento_en_posicion(event.pos())
        if evento:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            QToolTip.showText(event.globalPosition().toPoint(),
                              f"{evento.titulo}\n{evento.descripcion}\n{evento.fecha.strftime('%d/%m/%Y')}")
        else:
            self.setCursor(Qt.CursorShape.ArrowCursor)

    def wheelEvent(self, event):
        """Maneja zoom con rueda del mouse"""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_level = min(self.max_zoom, self.zoom_level * 1.1)
            else:
                self.zoom_level = max(self.min_zoom, self.zoom_level / 1.1)

            # Actualizar slider
            self.zoom_slider.setValue(int(self.zoom_level * 100))
            self.actualizar_scrollbar()
            self.update()
        else:
            # Scroll horizontal
            delta = event.angleDelta().y()
            self.scroll_offset += delta
            self.scroll_offset = max(0, self.scroll_offset)
            self.h_scrollbar.setValue(self.scroll_offset)
            self.update()

    def seleccionar_evento(self, evento):
        """Selecciona un evento y actualiza el panel de información"""
        # Deseleccionar evento anterior
        if self.evento_seleccionado_actual:
            self.evento_seleccionado_actual.seleccionado = False

        # Seleccionar nuevo evento
        self.evento_seleccionado_actual = evento
        evento.seleccionado = True

        # Actualizar panel de información
        self.info_titulo.setText(evento.titulo)
        self.info_descripcion.setText(evento.descripcion)
        self.info_fecha.setText(f"📅 {evento.fecha.strftime('%d/%m/%Y')} • Categoría: {evento.categoria.title()}")

        # Emitir señal
        self.evento_seleccionado.emit(evento)

        self.update()

    def cambiar_zoom(self, valor):
        """Cambia el nivel de zoom"""
        self.zoom_level = valor / 100.0
        self.zoom_label.setText(f"{valor}%")
        self.actualizar_scrollbar()
        self.update()

    def actualizar_scrollbar(self):
        """Actualiza el scrollbar horizontal"""
        dias_totales = (self.fecha_fin - self.fecha_inicio).days
        ancho_total = dias_totales * self.pixels_por_dia * self.zoom_level
        ancho_visible = (self.canvas_widget.width() if hasattr(self,
                                                               'canvas_widget') else self.width()) - self.margen_lateral
        ancho_visible = max(400, ancho_visible)  # Valor mínimo de seguridad

        if ancho_total > ancho_visible:
            self.h_scrollbar.setRange(0, int(ancho_total - ancho_visible))
            self.h_scrollbar.setPageStep(int(ancho_visible))
            self.h_scrollbar.setVisible(True)
        else:
            self.h_scrollbar.setVisible(False)

    def on_scroll_horizontal(self, valor):
        """Maneja el scroll horizontal"""
        self.scroll_offset = valor
        self.update()

    def ajustar_todo(self):
        """Ajusta el zoom para mostrar todo el timeline"""
        if not self.eventos:
            return

        dias_totales = (self.fecha_fin - self.fecha_inicio).days
        ancho_disponible = max(400, (
            self.canvas_widget.width() if hasattr(self, 'canvas_widget') else self.width()) - self.margen_lateral - 20)
        zoom_necesario = ancho_disponible / (dias_totales * self.pixels_por_dia)

        self.zoom_level = max(self.min_zoom, min(self.max_zoom, zoom_necesario))
        self.zoom_slider.setValue(int(self.zoom_level * 100))
        self.scroll_offset = 0
        self.h_scrollbar.setValue(0)
        self.update()

    def ir_a_hoy(self):
        """Centra la vista en la fecha actual"""
        rect = self.canvas_widget.rect() if hasattr(self, 'canvas_widget') else self.rect()
        x_hoy = self.fecha_a_x(datetime.now(), rect)
        centro_pantalla = max(400, rect.width()) // 2
        self.scroll_offset = max(0, x_hoy - centro_pantalla)
        self.h_scrollbar.setValue(self.scroll_offset)
        self.update()

    def agregar_evento(self):
        """Abre diálogo para agregar evento"""
        QMessageBox.information(self, "Agregar Evento", "Función de agregar evento en desarrollo")

    def ver_detalle_evento(self):
        """Abre el detalle del evento seleccionado"""
        if self.evento_seleccionado_actual:
            QMessageBox.information(self, "Detalle del Evento",
                                    f"Evento: {self.evento_seleccionado_actual.titulo}\n"
                                    f"Fecha: {self.evento_seleccionado_actual.fecha.strftime('%d/%m/%Y')}\n"
                                    f"Descripción: {self.evento_seleccionado_actual.descripcion}")

    def editar_evento(self):
        """Abre el editor del evento seleccionado"""
        if self.evento_seleccionado_actual:
            QMessageBox.information(self, "Editar Evento",
                                    "Función de edición en desarrollo")

    def resizeEvent(self, event):
        """Maneja el redimensionamiento de la ventana"""
        super().resizeEvent(event)
        self.actualizar_scrollbar()


class VentanaTimelineExpediente(QMainWindow):
    """Ventana principal para el timeline del expediente"""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setup_style()

    def setup_ui(self):
        self.setWindowTitle("Timeline del Expediente - EXP-2024-001234-PJN")
        self.setGeometry(100, 100, 1400, 800)

        # Widget central
        self.timeline = TimelineWidget()
        self.setCentralWidget(self.timeline)

        # Conectar señales
        self.timeline.evento_seleccionado.connect(self.on_evento_seleccionado)

        # Barra de menú
        self.crear_menu()

        # Barra de estado
        self.statusBar().showMessage("Timeline cargado - Use Ctrl+Rueda para zoom, rueda para scroll")

    def crear_menu(self):
        """Crea la barra de menú"""
        menubar = self.menuBar()

        # Menú Archivo
        archivo_menu = menubar.addMenu('Archivo')

        exportar_action = QAction('Exportar Timeline', self)
        exportar_action.triggered.connect(self.exportar_timeline)
        archivo_menu.addAction(exportar_action)

        # Menú Vista
        vista_menu = menubar.addMenu('Vista')

        zoom_in_action = QAction('Zoom In', self)
        zoom_in_action.setShortcut('Ctrl+=')
        zoom_in_action.triggered.connect(
            lambda: self.timeline.cambiar_zoom(min(500, self.timeline.zoom_slider.value() + 20)))
        vista_menu.addAction(zoom_in_action)

        zoom_out_action = QAction('Zoom Out', self)
        zoom_out_action.setShortcut('Ctrl+-')
        zoom_out_action.triggered.connect(
            lambda: self.timeline.cambiar_zoom(max(10, self.timeline.zoom_slider.value() - 20)))
        vista_menu.addAction(zoom_out_action)

        vista_menu.addSeparator()

        ajustar_action = QAction('Ajustar Todo', self)
        ajustar_action.setShortcut('Ctrl+0')
        ajustar_action.triggered.connect(self.timeline.ajustar_todo)
        vista_menu.addAction(ajustar_action)

    def on_evento_seleccionado(self, evento):
        """Maneja la selección de eventos"""
        self.statusBar().showMessage(f"Seleccionado: {evento.titulo} - {evento.fecha.strftime('%d/%m/%Y')}")

    def exportar_timeline(self):
        """Exporta el timeline a imagen"""
        QMessageBox.information(self, "Exportar", "Función de exportación en desarrollo")

    def setup_style(self):
        """Configura el estilo de la aplicación"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #ffffff;
            }

            QMenuBar {
                background-color: #f8fafc;
                border-bottom: 1px solid #e2e8f0;
                padding: 4px;
            }

            QMenuBar::item {
                background-color: transparent;
                padding: 6px 12px;
                border-radius: 4px;
            }

            QMenuBar::item:selected {
                background-color: #e2e8f0;
            }

            QStatusBar {
                background-color: #f8fafc;
                border-top: 1px solid #e2e8f0;
                color: #6b7280;
            }

            QPushButton {
                background-color: #3b82f6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
                font-size: 12px;
            }

            QPushButton:hover {
                background-color: #2563eb;
            }

            QPushButton:pressed {
                background-color: #1d4ed8;
            }

            QSlider::groove:horizontal {
                border: 1px solid #d1d5db;
                height: 6px;
                background: #f3f4f6;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #3b82f6;
                border: 1px solid #2563eb;
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }

            QSlider::handle:horizontal:hover {
                background: #2563eb;
            }

            QScrollBar:horizontal {
                border: none;
                background: #f3f4f6;
                height: 12px;
                border-radius: 6px;
            }

            QScrollBar::handle:horizontal {
                background: #9ca3af;
                border-radius: 6px;
                min-width: 20px;
            }

            QScrollBar::handle:horizontal:hover {
                background: #6b7280;
            }
        """)


# Aplicación principal
if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Configurar estilo de la aplicación
    app.setStyle('Fusion')

    # Crear y mostrar la ventana principal
    ventana = VentanaTimelineExpediente()
    ventana.show()

    sys.exit(app.exec())