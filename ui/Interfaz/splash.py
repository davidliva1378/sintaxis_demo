# splash_solo_animacion_mejorado_no_fullscreen.py
import sys
import random
import string
from collections import deque

from PySide6.QtCore import Qt, QTimer, Signal, QRect
from PySide6.QtGui import (
    QPixmap, QPainter, QFont, QColor, QFontMetrics, QGuiApplication
)
from PySide6.QtWidgets import QApplication, QSplashScreen


class AnimatedSplashScreen(QSplashScreen):
    animation_complete = Signal()

    def __init__(self, width=1200, height=800, cols=50, rows=30):
        # --- Pixmap al tamaño de la ventana (no fullscreen) ---
        self.window_w = int(width)
        self.window_h = int(height)
        pixmap = QPixmap(self.window_w, self.window_h)
        pixmap.fill(QColor(15, 15, 35))
        super().__init__(pixmap, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        # Centrar la ventana en el monitor principal
        screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = geo.x() + (geo.width() - self.window_w) // 2
        y = geo.y() + (geo.height() - self.window_h) // 2
        self.setGeometry(QRect(x, y, self.window_w, self.window_h))

        # --- Config de fuente y métricas para celdas ---
        self.font = QFont("Courier New", 16, QFont.Weight.Medium)
        self.font_bold = QFont("Courier New", 16, QFont.Weight.Bold)
        fm = QFontMetrics(self.font)
        char_w = fm.horizontalAdvance("M")
        char_h = fm.height()
        self.cell_pad_w = max(6, char_w // 4)
        self.cell_pad_h = max(6, char_h // 5)
        self.cell_w = char_w + self.cell_pad_w
        self.cell_h = char_h + self.cell_pad_h

        # Grilla fija (como tu original)
        self.cols = int(cols)
        self.rows = int(rows)

        # Ajuste de grilla: ocupar homogéneo todo el pixmap
        # Manteniendo filas/columnas fijas, recalculamos cell_w/h para encajar exacto
        self.cell_w = self.window_w // self.cols
        self.cell_h = self.window_h // self.rows
        self.grid_x0 = 0
        self.grid_y0 = 0

        # --- Pool de caracteres ---
        self.characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"

        # --- Grilla de celdas ---
        self.char_grid = []
        for _ in range(self.rows * self.cols):
            self.char_grid.append({
                "char": random.choice(self.characters),
                "visible": True,
                "is_sintaxis": False,
                "final_char": None,
            })

        # --- Palabra final: sintaXis (última fila, a la derecha) ---
        self.sintaxis_word = "sintaXis"
        self.sintaxis_positions = []
        last_row_start = (self.rows - 1) * self.cols
        word_start_col = max(0, self.cols - len(self.sintaxis_word))
        for i, letter in enumerate(self.sintaxis_word):
            pos = last_row_start + word_start_col + i
            self.sintaxis_positions.append(pos)
            self.char_grid[pos]["is_sintaxis"] = True
            self.char_grid[pos]["final_char"] = letter

        # --- Estado ---
        self.animation_phase = "changing"   # changing -> disappearing -> forming -> complete
        self.disappeared_count = 0
        self.formed_count = 0

        # --- Timers ---
        self.change_timer = QTimer(self)
        self.change_timer.timeout.connect(self.update_characters)
        self.change_timer.start(60)  # ruido suave

        # Repintado estable
        self.repaint_timer = QTimer(self)
        self.repaint_timer.timeout.connect(self.update)
        self.repaint_timer.start(16)  # ~60fps

        # Desaparición fluida (un solo timer + cola)
        self.indices_to_disappear = deque()
        self.disappear_timer = QTimer(self)
        self.disappear_timer.timeout.connect(self.on_disappear_tick)
        self.disappear_interval_ms = 14  # ajustable 10–20ms

        # Start
        QTimer.singleShot(3000, self.start_disappearing)

    # ------------------ FASE 1: CAMBIO (RUIDO) ------------------ #
    def update_characters(self):
        if self.animation_phase == "changing":
            for cell in self.char_grid:
                if random.random() > 0.85:
                    cell["char"] = random.choice(self.characters)
        elif self.animation_phase == "disappearing":
            for cell in self.char_grid:
                if cell["visible"] and random.random() > 0.90:
                    cell["char"] = random.choice(self.characters)

    # ---------------- FASE 2: DESAPARICIÓN SUAVE ---------------- #
    def start_disappearing(self):
        if self.animation_phase != "changing":
            return
        self.animation_phase = "disappearing"
        self.disappeared_count = 0
        self.indices_to_disappear.clear()

        # Secuencia fila/columna EXCLUYENDO sintaXis
        for row in range(self.rows):
            for col in range(self.cols):
                idx = row * self.cols + col
                if not self.char_grid[idx]["is_sintaxis"]:
                    self.indices_to_disappear.append(idx)

        self.disappear_timer.start(self.disappear_interval_ms)

    def on_disappear_tick(self):
        if not self.indices_to_disappear:
            self.disappear_timer.stop()
            QTimer.singleShot(500, self.start_forming_sintaxis)
            return

        idx = self.indices_to_disappear.popleft()
        self.char_grid[idx]["visible"] = False
        self.disappeared_count += 1
        self.update()

    # --------------- FASE 3: FORMAR “sintaXis” ------------------ #
    def start_forming_sintaxis(self):
        if self.animation_phase not in ("disappearing", "forming"):
            return
        self.animation_phase = "forming"
        self.change_timer.stop()

        # Cadencia agradable: 150 ms por letra
        for i, pos in enumerate(self.sintaxis_positions):
            QTimer.singleShot(i * 150, lambda p=pos: self.form_letter(p))

        total_form_ms = (len(self.sintaxis_positions) - 1) * 150 + 1
        QTimer.singleShot(total_form_ms + 2000, self.finish_animation)

    def form_letter(self, pos):
        self.char_grid[pos]["char"] = self.char_grid[pos]["final_char"]
        self.char_grid[pos]["visible"] = True
        self.formed_count += 1
        self.update()

    # -------------------- FIN DE ANIMACIÓN ---------------------- #
    def finish_animation(self):
        self.animation_phase = "complete"
        self.repaint_timer.stop()
        self.update()
        self.close_and_quit()

    def close_and_quit(self):
        self.hide()
        self.animation_complete.emit()

    # ---------------------- RENDERIZADO ------------------------- #
    def paintEvent(self, event):
        super().paintEvent(event)

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        painter.fillRect(self.rect(), QColor(15, 15, 35))

        # Métricas para centrado vertical/horizontal
        painter.setFont(self.font)
        fm_regular = QFontMetrics(self.font)
        regular_baseline_offset = (
            (self.cell_h - fm_regular.height()) // 2 + fm_regular.ascent()
        )
        fm_bold = None
        bold_baseline_offset = None

        for i, cell in enumerate(self.char_grid):
            if not cell["visible"]:
                continue

            row = i // self.cols
            col = i % self.cols
            x = self.grid_x0 + col * self.cell_w
            y = self.grid_y0 + row * self.cell_h

            if cell["is_sintaxis"] and self.animation_phase in ("forming", "complete"):
                if fm_bold is None:
                    fm_bold = QFontMetrics(self.font_bold)
                    bold_baseline_offset = (
                        (self.cell_h - fm_bold.height()) // 2 + fm_bold.ascent()
                    )
                painter.setFont(self.font_bold)
                painter.setPen(QColor(255, 255, 255))
                text_w = fm_bold.horizontalAdvance(cell["char"])
                tx = x + (self.cell_w - text_w) // 2
                ty = y + bold_baseline_offset
                painter.drawText(tx, ty, cell["char"])
                painter.setFont(self.font)
            else:
                painter.setPen(QColor(255, 255, 255))
                text_w = fm_regular.horizontalAdvance(cell["char"])
                tx = x + (self.cell_w - text_w) // 2
                ty = y + regular_baseline_offset
                painter.drawText(tx, ty, cell["char"])


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("sintaXis - Solo Animación (ventana fija)")
    app.setApplicationVersion("1.2")

    # Tamaño y grilla (como el original)
    splash = AnimatedSplashScreen(width=1200, height=800, cols=50, rows=30)
    splash.show()
    app.processEvents()
    splash.animation_complete.connect(app.quit)

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
