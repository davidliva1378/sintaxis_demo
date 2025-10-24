# splash_solo_animacion_15s.py
import sys
import random
import string
from math import ceil

from PySide6.QtCore import Qt, QTimer, Signal, QRect
from PySide6.QtGui import QPixmap, QPainter, QFont, QColor, QFontMetrics, QGuiApplication
from PySide6.QtWidgets import QApplication, QSplashScreen


class AnimatedSplashScreen(QSplashScreen):
    animation_complete = Signal()

    def __init__(self,
                 width=1200, height=800, cols=50, rows=30,
                 target_total_ms=15000,           # 🎯 objetivo total ~15 s
                 noise_ms=3000,                   # “ruido” inicial antes de desaparecer
                 pre_form_ms=500,                 # pausa antes de formar sintaXis
                 letter_ms=150,                   # cadencia entre letras
                 post_pause_ms=2000,              # pausa final antes de cerrar
                 tick_ms=16):                     # ~60 FPS para desaparecer
        # --- Ventana (no fullscreen) ---
        self.window_w = int(width)
        self.window_h = int(height)
        pixmap = QPixmap(self.window_w, self.window_h)
        pixmap.fill(QColor(15, 15, 35))
        super().__init__(pixmap, Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)

        # Centrar en pantalla
        screen = QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        x = geo.x() + (geo.width() - self.window_w) // 2
        y = geo.y() + (geo.height() - self.window_h) // 2
        self.setGeometry(QRect(x, y, self.window_w, self.window_h))

        # --- Grilla fija ---
        self.cols = int(cols)
        self.rows = int(rows)
        self.cell_w = self.window_w // self.cols
        self.cell_h = self.window_h // self.rows
        self.grid_x0 = 0
        self.grid_y0 = 0

        # --- Fuente y métricas ---
        self.font = QFont("Courier New", 16, QFont.Weight.Medium)
        self.font_bold = QFont("Courier New", 16, QFont.Weight.Bold)
        fm = QFontMetrics(self.font)
        self.baseline_offset = (self.cell_h - fm.height()) // 2 + fm.ascent()

        # --- Pool de caracteres ---
        self.characters = string.ascii_letters + string.digits + "!@#$%^&*()_+-=[]{}|;:,.<>?"

        # --- Grilla de celdas ---
        self.char_grid = [{
            "char": random.choice(self.characters),
            "visible": True,
            "is_sintaxis": False,
            "final_char": None
        } for _ in range(self.rows * self.cols)]

        # --- “sintaXis” en última fila, a la derecha ---
        self.sintaxis_word = "sintaXis"
        self.sintaxis_positions = []
        last_row_start = (self.rows - 1) * self.cols
        word_start_col = max(0, self.cols - len(self.sintaxis_word))
        for i, letter in enumerate(self.sintaxis_word):
            pos = last_row_start + word_start_col + i
            self.sintaxis_positions.append(pos)
            self.char_grid[pos]["is_sintaxis"] = True
            self.char_grid[pos]["final_char"] = letter

        # --- Estados/tiempos ---
        self.animation_phase = "changing"  # changing -> disappearing -> forming -> complete
        self.NOISE_MS = int(noise_ms)
        self.PRE_FORM_MS = int(pre_form_ms)
        self.LETTER_MS = int(letter_ms)
        self.POST_MS = int(post_pause_ms)
        self.TICK_MS = int(tick_ms)
        self.TARGET_TOTAL_MS = int(target_total_ms)

        # calcular cuántas celdas hay que borrar y ritmo requerido
        total_cells = self.rows * self.cols
        total_to_disappear = total_cells - len(self.sintaxis_positions)

        # tiempo “fijo” (sin contar desaparición)
        fixed_ms = self.NOISE_MS + self.PRE_FORM_MS + self.POST_MS + (len(self.sintaxis_positions) - 1) * self.LETTER_MS
        available_ms = max(500, self.TARGET_TOTAL_MS - fixed_ms)  # al menos 0,5 s para no ser instantáneo

        # cuántos ticks habrá para desaparecer
        ticks_for_disappear = max(1, int(available_ms // self.TICK_MS))
        # cuántas celdas borrar por tick para llegar al objetivo
        self.cells_per_tick = max(1, ceil(total_to_disappear / ticks_for_disappear))

        # --- Timers ---
        self.change_timer = QTimer(self)
        self.change_timer.timeout.connect(self.update_characters)
        self.change_timer.start(60)  # ruido suave

        self.repaint_timer = QTimer(self)
        self.repaint_timer.timeout.connect(self.update)
        self.repaint_timer.start(16)  # ~60 FPS

        # cola y timer de desaparición
        self.indices_to_disappear = []
        self.disappear_timer = QTimer(self)
        self.disappear_timer.timeout.connect(self.on_disappear_tick)

        # arrancar
        QTimer.singleShot(self.NOISE_MS, self.start_disappearing)

    # ------------------ FASE 1: RUIDO ------------------ #
    def update_characters(self):
        if self.animation_phase == "changing":
            for cell in self.char_grid:
                if random.random() > 0.85:
                    cell["char"] = random.choice(self.characters)
        elif self.animation_phase == "disappearing":
            for cell in self.char_grid:
                if cell["visible"] and random.random() > 0.90:
                    cell["char"] = random.choice(self.characters)

    # --------------- FASE 2: DESAPARICIÓN --------------- #
    def start_disappearing(self):
        if self.animation_phase != "changing":
            return
        self.animation_phase = "disappearing"

        # llenar cola EXCLUYENDO sintaXis
        self.indices_to_disappear.clear()
        for r in range(self.rows):
            for c in range(self.cols):
                idx = r * self.cols + c
                if not self.char_grid[idx]["is_sintaxis"]:
                    self.indices_to_disappear.append(idx)

        # iniciar timer fluido
        self.disappear_timer.start(self.TICK_MS)

    def on_disappear_tick(self):
        if not self.indices_to_disappear:
            self.disappear_timer.stop()
            QTimer.singleShot(self.PRE_FORM_MS, self.start_forming_sintaxis)
            return

        # borrar “cells_per_tick” celdas por tick
        for _ in range(self.cells_per_tick):
            if not self.indices_to_disappear:
                break
            idx = self.indices_to_disappear.pop(0)
            self.char_grid[idx]["visible"] = False

        self.update()

    # --------------- FASE 3: FORMAR “sintaXis” ---------- #
    def start_forming_sintaxis(self):
        if self.animation_phase not in ("disappearing", "forming"):
            return
        self.animation_phase = "forming"
        self.change_timer.stop()

        # formar letra por letra
        for i, pos in enumerate(self.sintaxis_positions):
            QTimer.singleShot(i * self.LETTER_MS, lambda p=pos: self.form_letter(p))

        total_form_ms = (len(self.sintaxis_positions) - 1) * self.LETTER_MS
        QTimer.singleShot(total_form_ms + self.POST_MS, self.finish_animation)

    def form_letter(self, pos):
        self.char_grid[pos]["char"] = self.char_grid[pos]["final_char"]
        self.char_grid[pos]["visible"] = True
        self.update()

    # -------------------- FIN --------------------------- #
    def finish_animation(self):
        self.animation_phase = "complete"
        self.repaint_timer.stop()
        self.update()
        QTimer.singleShot(300, self.close_and_quit)

    def close_and_quit(self):
        self.close()
        app = QApplication.instance()
        if app:
            app.quit()

    # -------------------- DIBUJO ------------------------ #
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        painter.fillRect(self.rect(), QColor(15, 15, 35))

        painter.setFont(self.font)
        fm = QFontMetrics(self.font)

        for i, cell in enumerate(self.char_grid):
            if not cell["visible"]:
                continue
            row = i // self.cols
            col = i % self.cols
            x = self.grid_x0 + col * self.cell_w
            y = self.grid_y0 + row * self.cell_h

            if cell["is_sintaxis"] and self.animation_phase in ("forming", "complete"):
                painter.setFont(self.font_bold)
                painter.setPen(QColor(255, 255, 255))
                fm_b = QFontMetrics(self.font_bold)
                text_w = fm_b.horizontalAdvance(cell["char"])
                tx = x + (self.cell_w - text_w) // 2
                ty = y + self.baseline_offset
                painter.drawText(tx, ty, cell["char"])
                painter.setFont(self.font)
            else:
                painter.setPen(QColor(255, 255, 255))
                text_w = fm.horizontalAdvance(cell["char"])
                tx = x + (self.cell_w - text_w) // 2
                ty = y + self.baseline_offset
                painter.drawText(tx, ty, cell["char"])


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("sintaXis - Splash (~15s)")
    app.setApplicationVersion("1.0")

    splash = AnimatedSplashScreen(
        width=1200, height=800, cols=50, rows=30,
        target_total_ms=15000,   # cambia acá si querés 12s/18s/etc.
        noise_ms=3000, pre_form_ms=500, letter_ms=150, post_pause_ms=2000,
        tick_ms=16
    )
    splash.show()
    app.processEvents()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
