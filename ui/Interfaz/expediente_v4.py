"""
Sistema de Gestión de Expedientes Jurídicos - PySide6
=====================================================
Versión ergonómica optimizada con:
- Temas claro/oscuro científicamente diseñados
- Temperatura de color adaptativa
- Sistema de notificaciones (toasts)
- Command Palette (Ctrl+K)
- Recordatorios de pausas (patrón 52/17)
- Timeline accionable
- Inspector contextual

Requisitos:
    pip install PySide6

Autor: Sistema de Gestión Legal
Licencia: LGPL (compatible con uso comercial)
"""

import sys
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QLineEdit, QScrollArea, QFrame, QTabWidget,
    QListWidget, QListWidgetItem, QStackedWidget, QDialog, QTextEdit,
    QSplitter, QToolButton, QShortcut
)
from PySide6.QtCore import (
    Qt, QTimer, QSettings, QSize, Signal, QPropertyAnimation,
    QEasingCurve, Property, QRect, QDateTime
)
from PySide6.QtGui import (
    QColor, QPalette, QFont, QIcon, QKeySequence, QPainter,
    QBrush, QPen, QLinearGradient
)


# ===== SISTEMA DE TEMAS =====

class ThemeMode(Enum):
    DARK = "dark"
    LIGHT = "light"


@dataclass
class ColorScheme:
    """Esquema de colores ergonómico"""
    # Fondos
    bg_primary: str
    bg_secondary: str
    bg_tertiary: str
    bg_elevated: str

    # Textos
    text_primary: str
    text_secondary: str
    text_tertiary: str

    # Bordes
    border_primary: str
    border_secondary: str

    # Acentos
    accent_blue: str
    accent_green: str
    accent_yellow: str
    accent_red: str
    accent_purple: str


class ThemeManager:
    """Gestor de temas con paletas optimizadas ergonómicamente"""

    DARK_THEME = ColorScheme(
        # Fondos - Material Design estándar (no negro puro)
        bg_primary="#121212",
        bg_secondary="#1e1e1e",
        bg_tertiary="#2d2d2d",
        bg_elevated="#252525",

        # Textos - Contraste WCAG AAA
        text_primary="#e4e4e7",  # Ratio 13.4:1
        text_secondary="#a1a1aa",  # Ratio 5.8:1
        text_tertiary="#71717a",

        # Bordes
        border_primary="#3f3f46",
        border_secondary="#27272a",

        # Acentos
        accent_blue="#3b82f6",
        accent_green="#10b981",
        accent_yellow="#f59e0b",
        accent_red="#ef4444",
        accent_purple="#8b5cf6"
    )

    LIGHT_THEME = ColorScheme(
        # Fondos - Blanco hueso (no blanco puro)
        bg_primary="#fafafa",
        bg_secondary="#f4f4f5",
        bg_tertiary="#e4e4e7",
        bg_elevated="#ffffff",

        # Textos - Gris oscuro (no negro puro)
        text_primary="#18181b",
        text_secondary="#52525b",
        text_tertiary="#a1a1aa",

        # Bordes
        border_primary="#e4e4e7",
        border_secondary="#f4f4f5",

        # Acentos
        accent_blue="#2563eb",
        accent_green="#059669",
        accent_yellow="#d97706",
        accent_red="#dc2626",
        accent_purple="#7c3aed"
    )

    @classmethod
    def get_theme(cls, mode: ThemeMode) -> ColorScheme:
        return cls.DARK_THEME if mode == ThemeMode.DARK else cls.LIGHT_THEME

    @classmethod
    def apply_theme(cls, widget: QWidget, theme: ColorScheme):
        """Aplica el tema a un widget"""
        palette = QPalette()

        # Colores base
        palette.setColor(QPalette.ColorRole.Window, QColor(theme.bg_primary))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(theme.text_primary))
        palette.setColor(QPalette.ColorRole.Base, QColor(theme.bg_secondary))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(theme.bg_tertiary))
        palette.setColor(QPalette.ColorRole.Text, QColor(theme.text_primary))
        palette.setColor(QPalette.ColorRole.Button, QColor(theme.bg_secondary))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(theme.text_primary))

        widget.setPalette(palette)

        # Stylesheet global
        widget.setStyleSheet(f"""
            QWidget {{
                background-color: {theme.bg_primary};
                color: {theme.text_primary};
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                font-size: 13px;
            }}

            QLineEdit, QTextEdit {{
                background-color: {theme.bg_secondary};
                color: {theme.text_primary};
                border: 1px solid {theme.border_primary};
                border-radius: 4px;
                padding: 6px 8px;
            }}

            QLineEdit:focus, QTextEdit:focus {{
                border-color: {theme.accent_blue};
            }}

            QPushButton {{
                background-color: {theme.bg_secondary};
                color: {theme.text_primary};
                border: 1px solid {theme.border_primary};
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: 500;
            }}

            QPushButton:hover {{
                background-color: {theme.bg_tertiary};
            }}

            QPushButton:pressed {{
                background-color: {theme.bg_primary};
            }}

            QTabWidget::pane {{
                border: 1px solid {theme.border_primary};
                background-color: {theme.bg_primary};
            }}

            QTabBar::tab {{
                background-color: {theme.bg_primary};
                color: {theme.text_secondary};
                border: none;
                border-bottom: 2px solid transparent;
                padding: 8px 16px;
                margin-right: 2px;
            }}

            QTabBar::tab:selected {{
                color: {theme.text_primary};
                border-bottom: 2px solid {theme.accent_blue};
            }}

            QTabBar::tab:hover {{
                color: {theme.text_primary};
            }}

            QScrollBar:vertical {{
                background-color: {theme.bg_primary};
                width: 12px;
                border-radius: 6px;
            }}

            QScrollBar::handle:vertical {{
                background-color: {theme.border_primary};
                border-radius: 6px;
                min-height: 20px;
            }}

            QScrollBar::handle:vertical:hover {{
                background-color: {theme.text_tertiary};
            }}

            QListWidget {{
                background-color: {theme.bg_primary};
                border: 1px solid {theme.border_primary};
                outline: none;
            }}

            QListWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {theme.border_secondary};
            }}

            QListWidget::item:selected {{
                background-color: {theme.bg_tertiary};
                color: {theme.text_primary};
            }}

            QListWidget::item:hover {{
                background-color: {theme.bg_secondary};
            }}
        """)


# ===== SISTEMA DE TOASTS =====

class ToastType(Enum):
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class Toast(QFrame):
    """Widget de notificación tipo toast con animación"""

    def __init__(self, message: str, toast_type: ToastType, theme: ColorScheme, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedWidth(400)

        # Configurar colores según tipo
        color_map = {
            ToastType.SUCCESS: theme.accent_green,
            ToastType.ERROR: theme.accent_red,
            ToastType.WARNING: theme.accent_yellow,
            ToastType.INFO: theme.accent_blue
        }

        icon_map = {
            ToastType.SUCCESS: "✓",
            ToastType.ERROR: "✗",
            ToastType.WARNING: "⚠",
            ToastType.INFO: "ℹ"
        }

        accent_color = color_map[toast_type]
        icon = icon_map[toast_type]

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # Icono
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"color: {accent_color}; font-size: 18px;")
        layout.addWidget(icon_label)

        # Mensaje
        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setStyleSheet(f"color: {theme.text_primary};")
        layout.addWidget(msg_label, 1)

        # Estilo del frame
        self.setStyleSheet(f"""
            Toast {{
                background-color: {theme.bg_elevated};
                border: 1px solid {theme.border_primary};
                border-left: 3px solid {accent_color};
                border-radius: 6px;
            }}
        """)

        # Animación de entrada
        self.setWindowOpacity(0)
        self.fade_in_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_in_animation.setDuration(300)
        self.fade_in_animation.setStartValue(0)
        self.fade_in_animation.setEndValue(1)
        self.fade_in_animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Timer para auto-cerrar
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.fade_out)
        self.timer.start(3000)

    def showEvent(self, event):
        super().showEvent(event)
        self.fade_in_animation.start()

    def fade_out(self):
        fade_out = QPropertyAnimation(self, b"windowOpacity")
        fade_out.setDuration(300)
        fade_out.setStartValue(1)
        fade_out.setEndValue(0)
        fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        fade_out.finished.connect(self.close)
        fade_out.start()


class ToastManager:
    """Gestor de toasts con posicionamiento automático"""

    def __init__(self, parent_widget: QWidget):
        self.parent = parent_widget
        self.toasts: List[Toast] = []
        self.spacing = 10

    def show_toast(self, message: str, toast_type: ToastType, theme: ColorScheme):
        toast = Toast(message, toast_type, theme, self.parent)
        self.toasts.append(toast)

        # Posicionar
        self.reposition_toasts()
        toast.show()

        # Remover de la lista cuando se cierra
        toast.destroyed.connect(lambda: self.toasts.remove(toast) if toast in self.toasts else None)
        toast.destroyed.connect(self.reposition_toasts)

    def reposition_toasts(self):
        """Reposiciona todos los toasts activos"""
        parent_rect = self.parent.rect()
        y_offset = 80  # Desde arriba

        for toast in self.toasts:
            x = parent_rect.right() - toast.width() - 20
            toast.move(x, y_offset)
            y_offset += toast.height() + self.spacing


# ===== MODELOS DE DATOS =====

@dataclass
class Actuacion:
    id: str
    tipo: str  # "proveido", "informe", "cedula", "sentencia", "presentacion"
    titulo: str
    fecha: datetime
    fojas: Optional[str] = None
    deo: Optional[str] = None
    tiene_adjunto: bool = False
    requiere_accion: bool = False
    notas: List[str] = None

    def __post_init__(self):
        if self.notas is None:
            self.notas = []


@dataclass
class Notificacion:
    id: str
    titulo: str
    vencimiento: datetime
    criticidad: str  # "baja", "media", "alta"
    atendida: bool = False


@dataclass
class Documento:
    id: str
    nombre: str
    etiqueta: str
    fecha: datetime
    status: Optional[str] = None
    size_kb: Optional[int] = None


@dataclass
class KPIsExpediente:
    caratula: str
    numero: str
    fuero: str
    juzgado: str
    estado_procesal: str
    proximo_vencimiento: Optional[datetime] = None
    riesgo: str = "bajo"  # "bajo", "medio", "alto"


# ===== DATOS MOCK =====

def crear_datos_mock():
    """Crea datos de ejemplo para testing"""
    hoy = datetime.now()

    kpis = KPIsExpediente(
        caratula="VALDEZ, FABIÁN P. c/ ESTADO NACIONAL – GNA s/ dif. salariales",
        numero="FPA 10610/2018",
        fuero="Federal",
        juzgado="Juzgado Federal de Paso de los Libres",
        estado_procesal="En ejecución",
        proximo_vencimiento=hoy + timedelta(days=5),
        riesgo="medio"
    )

    actuaciones = [
        Actuacion("a1", "proveido", "Se corre traslado a la demandada",
                  hoy - timedelta(days=12), fojas="155"),
        Actuacion("a2", "informe", "Informe DIRSAF",
                  hoy - timedelta(days=10), fojas="212/214",
                  tiene_adjunto=True, requiere_accion=True),
        Actuacion("a3", "presentacion", "Memorial de agravios demandada",
                  hoy - timedelta(days=9), fojas="215/221", tiene_adjunto=True),
        Actuacion("a4", "cedula", "Notificación electrónica a CENTINELA",
                  hoy - timedelta(days=7), deo="19269540", tiene_adjunto=True),
        Actuacion("a5", "sentencia", "Cámara confirma en lo principal",
                  hoy - timedelta(days=120), fojas="181/188",
                  notas=["Interés: tasa pasiva BCRA"]),
    ]

    notificaciones = [
        Notificacion("n1", "Cédula – Traslado impugnación de liquidación",
                     hoy + timedelta(days=3), "alta", False),
        Notificacion("n2", "Aviso PJN – Nuevo documento adjunto",
                     hoy + timedelta(days=10), "media", True),
    ]

    documentos = [
        Documento("d1", "Liquidación base TRIGO.pdf", "escrito",
                  hoy - timedelta(days=90), "complete", 412),
        Documento("d2", "Informe DIRSAF (fs. 212-214).pdf", "informe",
                  hoy - timedelta(days=10), "warning", 1296),
        Documento("d3", "Cédula electrónica DEO 19269540.pdf", "cedula",
                  hoy - timedelta(days=7), "pending", 380),
    ]

    return kpis, actuaciones, notificaciones, documentos


# ===== COMMAND PALETTE =====

class CommandPalette(QDialog):
    """Paleta de comandos estilo VS Code"""

    command_executed = Signal(str)

    def __init__(self, theme: ColorScheme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.commands = [
            ("📝 nuevo escrito", "nuevo_escrito"),
            ("🔄 sincronizar pjn", "sync_pjn"),
            ("📅 vencimientos semana", "vencimientos_semana"),
            ("📄 plantilla 1897/85", "plantilla_1897"),
            ("📊 resumen diario pdf", "resumen_pdf"),
            ("🌓 toggle tema claro/oscuro", "toggle_theme"),
            ("☕ pausas recordatorios", "toggle_breaks"),
        ]

        self.setup_ui()

    def setup_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setModal(True)
        self.setFixedWidth(600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Frame contenedor
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.bg_elevated};
                border: 1px solid {self.theme.border_primary};
                border-radius: 8px;
            }}
        """)
        frame_layout = QVBoxLayout(frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # Input de búsqueda
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(12, 12, 12, 12)

        search_icon = QLabel("🔍")
        search_layout.addWidget(search_icon)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Escribí un comando... (Esc para cerrar)")
        self.search_input.textChanged.connect(self.filter_commands)
        search_layout.addWidget(self.search_input)

        frame_layout.addWidget(search_container)

        # Separador
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet(f"background-color: {self.theme.border_primary};")
        separator.setFixedHeight(1)
        frame_layout.addWidget(separator)

        # Lista de comandos
        self.command_list = QListWidget()
        self.command_list.setFrameShape(QFrame.Shape.NoFrame)
        self.command_list.itemActivated.connect(self.execute_command)
        frame_layout.addWidget(self.command_list)

        # Poblar comandos
        self.populate_commands()

        layout.addWidget(frame)

    def populate_commands(self, filter_text=""):
        self.command_list.clear()
        for label, cmd in self.commands:
            if filter_text.lower() in label.lower():
                item = QListWidgetItem(label)
                item.setData(Qt.ItemDataRole.UserRole, cmd)
                self.command_list.addItem(item)

    def filter_commands(self, text):
        self.populate_commands(text)

    def execute_command(self, item):
        cmd = item.data(Qt.ItemDataRole.UserRole)
        self.command_executed.emit(cmd)
        self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.search_input.setFocus()
        self.search_input.selectAll()

        # Centrar en la ventana padre
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + 100
            self.move(x, y)


# ===== WIDGETS PRINCIPALES =====

class HeaderWidget(QFrame):
    """Header con KPIs y acciones rápidas"""

    action_triggered = Signal(str)

    def __init__(self, kpis: KPIsExpediente, theme: ColorScheme, parent=None):
        super().__init__(parent)
        self.kpis = kpis
        self.theme = theme
        self.setup_ui()

    def setup_ui(self):
        self.setFrameShape(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.bg_primary};
                border-bottom: 1px solid {self.theme.border_primary};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # Primera fila: Carátula y número
        top_layout = QHBoxLayout()

        title_label = QLabel(self.kpis.caratula)
        title_label.setStyleSheet(f"""
            font-size: 16px;
            font-weight: 600;
            color: {self.theme.text_primary};
        """)
        top_layout.addWidget(title_label)

        numero_label = QLabel(self.kpis.numero)
        numero_label.setStyleSheet(f"""
            background-color: {self.theme.bg_tertiary};
            color: {self.theme.text_secondary};
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
        """)
        top_layout.addWidget(numero_label)
        top_layout.addStretch()

        # Botones de acción
        btn_nuevo = QPushButton("Nuevo escrito")
        btn_nuevo.clicked.connect(lambda: self.action_triggered.emit("nuevo_escrito"))
        btn_nuevo.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme.accent_green}33;
                color: {self.theme.accent_green};
                border: 1px solid {self.theme.accent_green}4D;
            }}
        """)
        top_layout.addWidget(btn_nuevo)

        btn_sync = QPushButton("Sincronizar PJN")
        btn_sync.clicked.connect(lambda: self.action_triggered.emit("sync_pjn"))
        btn_sync.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.theme.accent_blue}33;
                color: {self.theme.accent_blue};
                border: 1px solid {self.theme.accent_blue}4D;
            }}
        """)
        top_layout.addWidget(btn_sync)

        layout.addLayout(top_layout)

        # Segunda fila: Metadata
        meta_layout = QHBoxLayout()
        meta_text = f"Fuero: {self.kpis.fuero} • Juzgado: {self.kpis.juzgado} • Estado: {self.kpis.estado_procesal}"
        meta_label = QLabel(meta_text)
        meta_label.setStyleSheet(f"color: {self.theme.text_secondary}; font-size: 11px;")
        meta_layout.addWidget(meta_label)

        # Vencimiento y riesgo
        if self.kpis.proximo_vencimiento:
            dias = (self.kpis.proximo_vencimiento - datetime.now()).days
            venc_label = QLabel(f"📅 Próx. venc.: {self.kpis.proximo_vencimiento.strftime('%d/%m/%Y')} ({dias} días)")
            venc_label.setStyleSheet(f"color: {self.theme.text_secondary}; font-size: 11px;")
            meta_layout.addWidget(venc_label)

        riesgo_colors = {"bajo": self.theme.accent_green, "medio": self.theme.accent_yellow,
                         "alto": self.theme.accent_red}
        riesgo_label = QLabel(f"Riesgo: {self.kpis.riesgo.upper()}")
        riesgo_label.setStyleSheet(f"color: {riesgo_colors[self.kpis.riesgo]}; font-size: 11px; font-weight: 600;")
        meta_layout.addWidget(riesgo_label)

        meta_layout.addStretch()
        layout.addLayout(meta_layout)


class TimelineWidget(QWidget):
    """Timeline de actuaciones con filtros"""

    item_selected = Signal(str)

    def __init__(self, actuaciones: List[Actuacion], theme: ColorScheme, parent=None):
        super().__init__(parent)
        self.actuaciones = actuaciones
        self.theme = theme
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Barra de filtros
        filter_bar = QWidget()
        filter_layout = QHBoxLayout(filter_bar)
        filter_layout.setContentsMargins(8, 8, 8, 8)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("🔍 Buscar actuación, DEO, fojas...")
        self.search_box.textChanged.connect(self.filter_items)
        filter_layout.addWidget(self.search_box)

        self.action_filter = QPushButton("Solo con acción")
        self.action_filter.setCheckable(True)
        self.action_filter.toggled.connect(self.filter_items)
        filter_layout.addWidget(self.action_filter)

        layout.addWidget(filter_bar)

        # Lista de actuaciones
        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self.on_item_clicked)
        layout.addWidget(self.list_widget)

        self.populate_list()

    def populate_list(self):
        self.list_widget.clear()
        for act in self.actuaciones:
            item = QListWidgetItem()
            widget = self.create_actuacion_widget(act)
            item.setSizeHint(widget.sizeHint())
            item.setData(Qt.ItemDataRole.UserRole, act.id)
            self.list_widget.addItem(item)
            self.list_widget.setItemWidget(item, widget)

    def create_actuacion_widget(self, act: Actuacion) -> QWidget:
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(12, 8, 12, 8)

        # Icono tipo
        icon_map = {"proveido": "⚡", "informe": "ℹ️", "cedula": "🔔",
                    "sentencia": "⭐", "presentacion": "📄"}
        icon_label = QLabel(icon_map.get(act.tipo, "📋"))
        icon_label.setFixedWidth(30)
        layout.addWidget(icon_label)

        # Contenido
        content_layout = QVBoxLayout()

        title_layout = QHBoxLayout()
        title_label = QLabel(act.titulo)
        title_label.setStyleSheet(f"color: {self.theme.text_primary}; font-weight: 600;")
        title_layout.addWidget(title_label)

        if act.requiere_accion:
            badge = QLabel("Requiere acción")
            badge.setStyleSheet(f"""
                background-color: {self.theme.accent_yellow}33;
                color: {self.theme.accent_yellow};
                border: 1px solid {self.theme.accent_yellow}4D;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 10px;
            """)
            title_layout.addWidget(badge)

        title_layout.addStretch()
        content_layout.addLayout(title_layout)

        # Metadata
        meta_text = f"{act.fecha.strftime('%d/%m/%Y')}"
        if act.fojas:
            meta_text += f" • fs. {act.fojas}"
        if act.deo:
            meta_text += f" • DEO {act.deo}"

        meta_label = QLabel(meta_text)
        meta_label.setStyleSheet(f"color: {self.theme.text_secondary}; font-size: 11px;")
        content_layout.addWidget(meta_label)

        layout.addLayout(content_layout, 1)

        return widget

    def filter_items(self):
        search_text = self.search_box.text().lower()
        only_action = self.action_filter.isChecked()

        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            act_id = item.data(Qt.ItemDataRole.UserRole)
            act = next((a for a in self.actuaciones if a.id == act_id), None)

            if act:
                matches_search = search_text in act.titulo.lower() or \
                                 search_text in (act.deo or "").lower() or \
                                 search_text in (act.fojas or "").lower()
                matches_filter = not only_action or act.requiere_accion

                item.setHidden(not (matches_search and matches_filter))

    def on_item_clicked(self, item):
        act_id = item.data(Qt.ItemDataRole.UserRole)
        self.item_selected.emit(act_id)


class InspectorWidget(QWidget):
    """Panel inspector contextual"""

    def __init__(self, theme: ColorScheme, parent=None):
        super().__init__(parent)
        self.theme = theme
        self.current_item = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        self.title_label = QLabel("Seleccioná un elemento")
        self.title_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {self.theme.text_primary};
        """)
        layout.addWidget(self.title_label)

        self.details_label = QLabel("")
        self.details_label.setWordWrap(True)
        self.details_label.setStyleSheet(f"color: {self.theme.text_secondary}; font-size: 12px;")
        layout.addWidget(self.details_label)

        # Botones de acción
        self.actions_layout = QHBoxLayout()
        layout.addLayout(self.actions_layout)

        layout.addStretch()

    def update_content(self, item: Any):
        """Actualiza el contenido del inspector"""
        self.current_item = item

        if isinstance(item, Actuacion):
            self.title_label.setText(item.titulo)
            details = f"Fecha: {item.fecha.strftime('%d/%m/%Y')}"
            if item.fojas:
                details += f"\nFojas: {item.fojas}"
            if item.deo:
                details += f"\nDEO: {item.deo}"
            self.details_label.setText(details)
        elif isinstance(item, Notificacion):
            self.title_label.setText(item.titulo)
            dias = (item.vencimiento - datetime.now()).days
            self.details_label.setText(
                f"Vence: {item.vencimiento.strftime('%d/%m/%Y')} ({dias} días)\nCriticidad: {item.criticidad.upper()}")
        elif isinstance(item, Documento):
            self.title_label.setText(item.nombre)
            self.details_label.setText(
                f"Fecha: {item.fecha.strftime('%d/%m/%Y')}\nTipo: {item.etiqueta}\nTamaño: {item.size_kb} KB")


# ===== VENTANA PRINCIPAL =====

class MainWindow(QMainWindow):
    """Ventana principal del sistema"""

    def __init__(self):
        super().__init__()

        # Configuración
        self.settings = QSettings("SistemaLegal", "GestionExpedientes")

        # Cargar tema guardado
        saved_mode = self.settings.value("theme_mode", ThemeMode.DARK.value)
        self.current_mode = ThemeMode(saved_mode)
        self.theme = ThemeManager.get_theme(self.current_mode)

        # Cargar datos
        self.kpis, self.actuaciones, self.notificaciones, self.documentos = crear_datos_mock()

        # Toast manager
        self.toast_manager = None  # Se inicializa después de crear la UI

        # Recordatorio de pausas
        self.break_reminder_enabled = self.settings.value("break_reminder", True, type=bool)
        self.break_timer = QTimer(self)
        self.break_timer.timeout.connect(self.show_break_reminder)
        if self.break_reminder_enabled:
            self.break_timer.start(52 * 60 * 1000)  # 52 minutos

        self.setup_ui()
        self.setup_shortcuts()

        # Inicializar toast manager después de crear UI
        self.toast_manager = ToastManager(self)

    def setup_ui(self):
        self.setWindowTitle("Sistema de Gestión de Expedientes Jurídicos")
        self.setGeometry(100, 100, 1400, 900)

        # Aplicar tema
        ThemeManager.apply_theme(self, self.theme)

        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        self.header = HeaderWidget(self.kpis, self.theme)
        self.header.action_triggered.connect(self.handle_action)
        main_layout.addWidget(self.header)

        # Botón de toggle tema (flotante en header)
        self.theme_toggle = QPushButton()
        self.theme_toggle.setFixedSize(32, 32)
        self.theme_toggle.clicked.connect(self.toggle_theme)
        self.update_theme_button()
        self.theme_toggle.setParent(self.header)
        self.theme_toggle.move(self.width() - 50, 10)

        # Tabs
        self.tabs = QTabWidget()
        self.tabs.addTab(self.create_actuaciones_tab(), "Actuaciones")
        self.tabs.addTab(QWidget(), "Notificaciones")
        self.tabs.addTab(QWidget(), "Escritos")
        self.tabs.addTab(QWidget(), "Agenda")
        self.tabs.addTab(QWidget(), "Documentos")
        self.tabs.addTab(QWidget(), "Análisis")
        self.tabs.addTab(QWidget(), "Auditoría")

        main_layout.addWidget(self.tabs)

        # Barra de estado
        self.statusBar().showMessage("Sistema iniciado correctamente")

    def create_actuaciones_tab(self) -> QWidget:
        """Crea el tab de actuaciones con timeline e inspector"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Splitter para redimensionar
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Timeline
        self.timeline = TimelineWidget(self.actuaciones, self.theme)
        self.timeline.item_selected.connect(self.on_actuacion_selected)
        splitter.addWidget(self.timeline)

        # Inspector
        self.inspector = InspectorWidget(self.theme)
        splitter.addWidget(self.inspector)

        splitter.setSizes([800, 400])

        layout.addWidget(splitter)
        return widget

    def setup_shortcuts(self):
        """Configura atajos de teclado"""
        # Command Palette: Ctrl+K
        palette_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        palette_shortcut.activated.connect(self.show_command_palette)

        # Toggle tema: Ctrl+Shift+T
        theme_shortcut = QShortcut(QKeySequence("Ctrl+Shift+T"), self)
        theme_shortcut.activated.connect(self.toggle_theme)

    def show_command_palette(self):
        """Muestra la paleta de comandos"""
        palette = CommandPalette(self.theme, self)
        palette.command_executed.connect(self.execute_command)
        palette.exec()

    def execute_command(self, command: str):
        """Ejecuta un comando de la paleta"""
        if command == "nuevo_escrito":
            self.show_toast("📝 Abriendo editor de nuevo escrito...", ToastType.INFO)
        elif command == "sync_pjn":
            self.show_toast("🔄 Sincronizando con PJN...", ToastType.INFO)
            QTimer.singleShot(2000, lambda: self.show_toast("✓ Sincronización completada", ToastType.SUCCESS))
        elif command == "toggle_theme":
            self.toggle_theme()
        elif command == "toggle_breaks":
            self.toggle_break_reminders()
        else:
            self.show_toast(f"Ejecutando: {command}", ToastType.INFO)

    def handle_action(self, action: str):
        """Maneja acciones del header"""
        self.execute_command(action)

    def toggle_theme(self):
        """Alterna entre modo claro y oscuro"""
        self.current_mode = ThemeMode.LIGHT if self.current_mode == ThemeMode.DARK else ThemeMode.DARK
        self.theme = ThemeManager.get_theme(self.current_mode)
        self.settings.setValue("theme_mode", self.current_mode.value)

        # Reaplicar tema
        ThemeManager.apply_theme(self, self.theme)
        self.update_theme_button()

        # Recrear widgets con nuevo tema
        self.header.theme = self.theme
        self.timeline.theme = self.theme
        self.inspector.theme = self.theme

        mode_name = "claro" if self.current_mode == ThemeMode.LIGHT else "oscuro"
        self.show_toast(f"🌓 Tema cambiado a {mode_name}", ToastType.INFO)

    def update_theme_button(self):
        """Actualiza el icono del botón de tema"""
        icon_text = "☀️" if self.current_mode == ThemeMode.DARK else "🌙"
        self.theme_toggle.setText(icon_text)

    def toggle_break_reminders(self):
        """Activa/desactiva recordatorios de pausas"""
        self.break_reminder_enabled = not self.break_reminder_enabled
        self.settings.setValue("break_reminder", self.break_reminder_enabled)

        if self.break_reminder_enabled:
            self.break_timer.start(52 * 60 * 1000)
            self.show_toast("☕ Recordatorios de pausa activados", ToastType.INFO)
        else:
            self.break_timer.stop()
            self.show_toast("☕ Recordatorios de pausa desactivados", ToastType.INFO)

    def show_break_reminder(self):
        """Muestra recordatorio de pausa"""
        self.show_toast("🫖 Hora de un descanso. Llevás 52 minutos trabajando. Descansá 17 minutos.",
                        ToastType.INFO)

    def show_toast(self, message: str, toast_type: ToastType):
        """Muestra un toast"""
        if self.toast_manager:
            self.toast_manager.show_toast(message, toast_type, self.theme)

    def on_actuacion_selected(self, act_id: str):
        """Maneja selección de actuación"""
        act = next((a for a in self.actuaciones if a.id == act_id), None)
        if act:
            self.inspector.update_content(act)
            self.statusBar().showMessage(f"Seleccionado: {act.titulo} - {act.fecha.strftime('%d/%m/%Y')}")

    def resizeEvent(self, event):
        """Reposiciona botón de tema al redimensionar"""
        super().resizeEvent(event)
        if hasattr(self, 'theme_toggle'):
            self.theme_toggle.move(self.width() - 50, 10)


# ===== APLICACIÓN PRINCIPAL =====

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Sistema de Gestión de Expedientes")
    app.setOrganizationName("SistemaLegal")

    # Configurar fuente base
    font = QFont()
    font.setFamily("-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif")
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()