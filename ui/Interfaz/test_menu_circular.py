import sys
import math
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *


class MenuCircularItem:
    """Representa un item del menú circular"""

    def __init__(self, texto, icono, accion, color=None, atajo=None):
        self.texto = texto
        self.icono = icono
        self.accion = accion
        self.color = color or QColor(59, 130, 246)
        self.atajo = atajo
        self.angulo = 0
        self.posicion = QPoint()
        self.hover = False
        self.rect = QRect()
        self.animacion_escala = 1.0


class MenuCircular(QWidget):
    """Menú circular genérico reutilizable para todo el proyecto"""

    accion_ejecutada = pyqtSignal(str, object)  # accion, contexto
    menu_cerrado = pyqtSignal()

    def __init__(self, parent=None, radio=80, tamaño_item=40):
        super().__init__(parent if parent else QApplication.activeWindow())

        # Configuración de ventana
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        # Configuración del menú
        self.radio_items = radio
        self.tamaño_item = tamaño_item
        self.radio_centro = tamaño_item // 2
        self.tamaño_total = (radio + tamaño_item) * 2 + 20

        self.setFixedSize(self.tamaño_total, self.tamaño_total)
        self.centro = QPoint(self.tamaño_total // 2, self.tamaño_total // 2)

        # Estado del menú
        self.items = []
        self.contexto = None
        self.item_hover = None
        self.progreso_animacion = 0.0
        self.animando = False
        self.posicion_mouse = QPoint()

        # Animaciones
        self.timer_animacion = QTimer()
        self.timer_animacion.timeout.connect(self.actualizar_animacion)

        # Auto-cierre
        self.timer_auto_cierre = QTimer()
        self.timer_auto_cierre.setSingleShot(True)
        self.timer_auto_cierre.timeout.connect(self.cerrar_menu)

        self.setMouseTracking(True)
        self.installEventFilter(self)

        # Configuración inicial
        self.hide()

    def mostrar_en(self, posicion, items, contexto=None):
        """Muestra el menú en una posición específica con items dados"""
        self.contexto = contexto
        self.items = items
        self.calcular_posiciones()

        # Posicionar el menú centrado en el punto
        menu_pos = posicion - QPoint(self.tamaño_total // 2, self.tamaño_total // 2)

        # Ajustar para que no se salga de la pantalla
        screen = QApplication.primaryScreen().geometry()
        menu_pos.setX(max(0, min(menu_pos.x(), screen.width() - self.tamaño_total)))
        menu_pos.setY(max(0, min(menu_pos.y(), screen.height() - self.tamaño_total)))

        self.move(menu_pos)
        self.show()
        self.raise_()
        self.activateWindow()

        # Iniciar animación de entrada
        self.iniciar_animacion_entrada()

        # Auto-cierre después de 5 segundos
        self.timer_auto_cierre.start(5000)

    def calcular_posiciones(self):
        """Calcula las posiciones de los items en el círculo"""
        num_items = len(self.items)
        if num_items == 0:
            return

        # Calcular ángulo entre items
        angulo_step = 2 * math.pi / num_items
        angulo_inicial = -math.pi / 2  # Empezar desde arriba

        for i, item in enumerate(self.items):
            angulo = angulo_inicial + i * angulo_step
            item.angulo = angulo

            # Calcular posición
            x = self.centro.x() + self.radio_items * math.cos(angulo)
            y = self.centro.y() + self.radio_items * math.sin(angulo)
            item.posicion = QPoint(int(x), int(y))

            # Crear rectángulo para detección de hover
            item.rect = QRect(
                item.posicion.x() - self.tamaño_item // 2,
                item.posicion.y() - self.tamaño_item // 2,
                self.tamaño_item,
                self.tamaño_item
            )

    def iniciar_animacion_entrada(self):
        """Inicia la animación de entrada del menú"""
        self.progreso_animacion = 0.0
        self.animando = True
        self.timer_animacion.start(16)  # ~60 FPS

    def actualizar_animacion(self):
        """Actualiza la animación del menú"""
        if not self.animando:
            return

        self.progreso_animacion += 0.1

        if self.progreso_animacion >= 1.0:
            self.progreso_animacion = 1.0
            self.animando = False
            self.timer_animacion.stop()

        self.update()

    def paintEvent(self, event):
        """Dibuja el menú circular"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fondo semi-transparente
        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.rect())

        # Círculo central
        factor_animacion = self.ease_out_back(self.progreso_animacion)
        radio_centro_animado = int(self.radio_centro * factor_animacion)

        painter.setBrush(QBrush(QColor(30, 30, 30, 200)))
        painter.setPen(QPen(QColor(60, 60, 60), 2))
        painter.drawEllipse(
            self.centro.x() - radio_centro_animado,
            self.centro.y() - radio_centro_animado,
            radio_centro_animado * 2,
            radio_centro_animado * 2
        )

        # Dibujar items
        for i, item in enumerate(self.items):
            self.dibujar_item(painter, item, i)

        # Texto del item hover
        if self.item_hover:
            self.dibujar_tooltip(painter, self.item_hover)

    def dibujar_item(self, painter, item, index):
        """Dibuja un item individual del menú"""
        # Animación de entrada escalonada
        delay = index * 0.1
        progreso_item = max(0, min(1, (self.progreso_animacion - delay) / 0.3))

        if progreso_item <= 0:
            return

        # Factor de escala para animación
        escala = self.ease_out_back(progreso_item)
        if item.hover:
            escala *= 1.2

        tamaño_animado = int(self.tamaño_item * escala)

        # Posición animada
        pos_x = int(self.centro.x() + (item.posicion.x() - self.centro.x()) * progreso_item)
        pos_y = int(self.centro.y() + (item.posicion.y() - self.centro.y()) * progreso_item)

        # Círculo del item
        color_fondo = item.color.lighter(120) if item.hover else item.color
        painter.setBrush(QBrush(color_fondo))
        painter.setPen(QPen(QColor(255, 255, 255, 100), 2))

        rect_item = QRect(
            pos_x - tamaño_animado // 2,
            pos_y - tamaño_animado // 2,
            tamaño_animado,
            tamaño_animado
        )

        painter.drawEllipse(rect_item)

        # Icono
        painter.setPen(QPen(QColor(255, 255, 255)))
        font = QFont()
        font.setPointSize(int(12 * escala))
        painter.setFont(font)

        painter.drawText(rect_item, Qt.AlignmentFlag.AlignCenter, item.icono)

        # Actualizar rect para hover detection
        item.rect = rect_item

    def dibujar_tooltip(self, painter, item):
        """Dibuja el tooltip del item hover"""
        if not item.hover:
            return

        # Configurar texto
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        painter.setFont(font)

        metrics = QFontMetrics(font)
        texto_completo = item.texto
        if item.atajo:
            texto_completo += f" ({item.atajo})"

        rect_texto = metrics.boundingRect(texto_completo)
        padding = 8

        # Posición del tooltip
        tooltip_x = item.posicion.x() - rect_texto.width() // 2 - padding
        tooltip_y = item.posicion.y() - self.tamaño_item - rect_texto.height() - padding * 2

        # Fondo del tooltip
        rect_tooltip = QRect(
            tooltip_x, tooltip_y,
            rect_texto.width() + padding * 2,
            rect_texto.height() + padding * 2
        )

        painter.setBrush(QBrush(QColor(40, 40, 40, 220)))
        painter.setPen(QPen(QColor(80, 80, 80), 1))
        painter.drawRoundedRect(rect_tooltip, 4, 4)

        # Texto del tooltip
        painter.setPen(QPen(QColor(255, 255, 255)))
        painter.drawText(
            rect_tooltip,
            Qt.AlignmentFlag.AlignCenter,
            texto_completo
        )

    def ease_out_back(self, t):
        """Función de easing para animación suave con rebote"""
        c1 = 1.70158
        c3 = c1 + 1
        return 1 + c3 * pow(t - 1, 3) + c1 * pow(t - 1, 2)

    def mouseMoveEvent(self, event):
        """Maneja el movimiento del mouse para hover"""
        self.posicion_mouse = event.pos()

        # Detectar hover en items
        item_anterior = self.item_hover
        self.item_hover = None

        for item in self.items:
            if item.rect.contains(event.pos()):
                self.item_hover = item
                item.hover = True
            else:
                item.hover = False

        # Actualizar si cambió el hover
        if self.item_hover != item_anterior:
            self.update()

            # Reiniciar timer de auto-cierre si hay hover
            if self.item_hover:
                self.timer_auto_cierre.start(5000)

    def mousePressEvent(self, event):
        """Maneja clicks en el menú"""
        if event.button() == Qt.MouseButton.LeftButton:
            for item in self.items:
                if item.rect.contains(event.pos()):
                    self.accion_ejecutada.emit(item.accion, self.contexto)
                    self.cerrar_menu()
                    return

            # Click fuera del menú - cerrar
            self.cerrar_menu()

    def keyPressEvent(self, event):
        """Maneja teclas de atajo"""
        if event.key() == Qt.Key.Key_Escape:
            self.cerrar_menu()
            return

        # Buscar atajo en items
        tecla = event.text().upper()
        for item in self.items:
            if item.atajo and item.atajo.upper() == tecla:
                self.accion_ejecutada.emit(item.accion, self.contexto)
                self.cerrar_menu()
                return

        super().keyPressEvent(event)

    def eventFilter(self, obj, event):
        """Filtro de eventos para auto-cierre"""
        if event.type() == QEvent.Type.WindowDeactivate:
            QTimer.singleShot(100, self.cerrar_menu)
        return super().eventFilter(obj, event)

    def cerrar_menu(self):
        """Cierra el menú con animación"""
        self.timer_auto_cierre.stop()
        self.timer_animacion.stop()
        self.menu_cerrado.emit()
        self.close()


# Factory para crear menús predefinidos
class MenuCircularFactory:
    """Factory para crear menús circulares predefinidos"""

    @staticmethod
    def crear_menu_expediente(parent=None):
        """Crea menú para acciones de expediente"""
        items = [
            MenuCircularItem("Ver Detalle", "👁️", "ver_detalle", QColor(59, 130, 246), "V"),
            MenuCircularItem("Editar", "✏️", "editar", QColor(245, 158, 11), "E"),
            MenuCircularItem("Imprimir", "🖨️", "imprimir", QColor(139, 92, 246), "P"),
            MenuCircularItem("Exportar PDF", "📄", "exportar_pdf", QColor(239, 68, 68), "D"),
            MenuCircularItem("Compartir", "📤", "compartir", QColor(34, 197, 94), "S"),
            MenuCircularItem("Archivar", "📁", "archivar", QColor(107, 114, 128), "A")
        ]

        menu = MenuCircular(parent)
        return menu, items

    @staticmethod
    def crear_menu_documento(parent=None):
        """Crea menú para acciones de documento"""
        items = [
            MenuCircularItem("Abrir", "📂", "abrir", QColor(59, 130, 246), "O"),
            MenuCircularItem("Descargar", "⬇️", "descargar", QColor(34, 197, 94), "D"),
            MenuCircularItem("Vista Previa", "👁️", "preview", QColor(245, 158, 11), "P"),
            MenuCircularItem("Compartir", "📤", "compartir", QColor(139, 92, 246), "S"),
            MenuCircularItem("Propiedades", "ℹ️", "propiedades", QColor(107, 114, 128), "I"),
            MenuCircularItem("Eliminar", "🗑️", "eliminar", QColor(239, 68, 68), "X")
        ]

        menu = MenuCircular(parent)
        return menu, items

    @staticmethod
    def crear_menu_actuacion(parent=None):
        """Crea menú para acciones de actuación"""
        items = [
            MenuCircularItem("Ver Detalle", "👁️", "ver_detalle", QColor(59, 130, 246), "V"),
            MenuCircularItem("Editar", "✏️", "editar", QColor(245, 158, 11), "E"),
            MenuCircularItem("Duplicar", "📋", "duplicar", QColor(16, 185, 129), "C"),
            MenuCircularItem("Agregar Nota", "📝", "agregar_nota", QColor(139, 92, 246), "N"),
            MenuCircularItem("Marcar Importante", "⭐", "importante", QColor(245, 158, 11), "M"),
            MenuCircularItem("Eliminar", "🗑️", "eliminar", QColor(239, 68, 68), "X")
        ]

        menu = MenuCircular(parent)
        return menu, items

    @staticmethod
    def crear_menu_timeline(parent=None):
        """Crea menú para timeline"""
        items = [
            MenuCircularItem("Agregar Evento", "➕", "agregar", QColor(34, 197, 94), "A"),
            MenuCircularItem("Filtrar", "🔍", "filtrar", QColor(59, 130, 246), "F"),
            MenuCircularItem("Zoom Ajustar", "🔍", "zoom_fit", QColor(245, 158, 11), "Z"),
            MenuCircularItem("Exportar", "📤", "exportar", QColor(139, 92, 246), "E"),
            MenuCircularItem("Configurar", "⚙️", "configurar", QColor(107, 114, 128), "C")
        ]

        menu = MenuCircular(parent, radio=60, tamaño_item=35)
        return menu, items


# Ejemplo de uso
class EjemploMenuCircular(QMainWindow):
    """Ejemplo de uso del menú circular"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ejemplo Menú Circular")
        self.setGeometry(100, 100, 800, 600)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)

        # Instrucciones
        instrucciones = QLabel("""
        <h2>Menú Circular - Demo</h2>
        <p><b>Click derecho</b> en cualquier parte para abrir el menú circular</p>
        <p><b>Características:</b></p>
        <ul>
        <li>Animación suave de entrada</li>
        <li>Hover con tooltips</li>
        <li>Atajos de teclado</li>
        <li>Auto-cierre inteligente</li>
        <li>Completamente personalizable</li>
        </ul>
        """)
        layout.addWidget(instrucciones)

        # Botones de ejemplo
        botones_layout = QHBoxLayout()

        btn_expediente = QPushButton("🗂️ Menú Expediente")
        btn_expediente.clicked.connect(self.mostrar_menu_expediente)
        botones_layout.addWidget(btn_expediente)

        btn_documento = QPushButton("📄 Menú Documento")
        btn_documento.clicked.connect(self.mostrar_menu_documento)
        botones_layout.addWidget(btn_documento)

        btn_timeline = QPushButton("📅 Menú Timeline")
        btn_timeline.clicked.connect(self.mostrar_menu_timeline)
        botones_layout.addWidget(btn_timeline)

        layout.addLayout(botones_layout)
        layout.addStretch()

        # Configurar menú contextual
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.mostrar_menu_contextual)

    def mostrar_menu_expediente(self):
        """Muestra menú de expediente"""
        menu, items = MenuCircularFactory.crear_menu_expediente(self)
        menu.accion_ejecutada.connect(self.manejar_accion)
        posicion = self.mapToGlobal(self.rect().center())
        menu.mostrar_en(posicion, items, {"tipo": "expediente", "id": "EXP-001"})

    def mostrar_menu_documento(self):
        """Muestra menú de documento"""
        menu, items = MenuCircularFactory.crear_menu_documento(self)
        menu.accion_ejecutada.connect(self.manejar_accion)
        posicion = self.mapToGlobal(self.rect().center())
        menu.mostrar_en(posicion, items, {"tipo": "documento", "id": "DOC-001"})

    def mostrar_menu_timeline(self):
        """Muestra menú de timeline"""
        menu, items = MenuCircularFactory.crear_menu_timeline(self)
        menu.accion_ejecutada.connect(self.manejar_accion)
        posicion = self.mapToGlobal(self.rect().center())
        menu.mostrar_en(posicion, items, {"tipo": "timeline"})

    def mostrar_menu_contextual(self, posicion):
        """Muestra menú contextual con click derecho"""
        menu, items = MenuCircularFactory.crear_menu_expediente(self)
        menu.accion_ejecutada.connect(self.manejar_accion)
        posicion_global = self.mapToGlobal(posicion)
        menu.mostrar_en(posicion_global, items, {"tipo": "contextual"})

    def manejar_accion(self, accion, contexto):
        """Maneja las acciones del menú"""
        QMessageBox.information(
            self,
            "Acción Ejecutada",
            f"Acción: {accion}\nContexto: {contexto}"
        )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    ventana = EjemploMenuCircular()
    ventana.show()

    sys.exit(app.exec())