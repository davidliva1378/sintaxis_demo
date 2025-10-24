"""Ventana de progreso para extracción batch de expedientes.

Muestra en tiempo real el progreso de la extracción completa con:
- Barra de progreso principal
- Expediente actual siendo procesado
- Log de operaciones recientes
- Estadísticas: exitosos, errores, omitidos
- Estimación de tiempo restante
- Botones para pausar/cancelar
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk, scrolledtext
from datetime import datetime, timedelta
from typing import Callable


class ProgressWindow(tk.Toplevel):
    """Ventana de progreso para procesamiento batch de expedientes."""

    def __init__(
        self,
        parent: tk.Tk,
        total_expedientes: int,
        on_pause: Callable[[], None] | None = None,
        on_cancel: Callable[[], None] | None = None,
    ):
        """Inicializa la ventana de progreso.

        Args:
            parent: Ventana padre (root)
            total_expedientes: Número total de expedientes a procesar
            on_pause: Callback cuando se presiona pausar
            on_cancel: Callback cuando se presiona cancelar
        """
        super().__init__(parent)

        self.title("Extracción de Expedientes - Progreso")
        self.geometry("800x600")
        self.resizable(True, True)

        # Estado
        self.total = total_expedientes
        self.procesados = 0
        self.exitosos = 0
        self.errores = 0
        self.omitidos = 0
        self.expediente_actual = ""
        self.estado_actual = "Iniciando..."
        self.tiempo_inicio = datetime.now()
        self.tiempos_procesamiento = []  # Para calcular ETA

        # Callbacks
        self._on_pause = on_pause
        self._on_cancel = on_cancel
        self._pausado = False

        # Crear interfaz
        self._crear_ui()

        # Configurar cierre de ventana
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # En macOS, forzar al frente
        try:
            self.lift()
            self.focus_force()
            self.attributes('-topmost', True)
            self.after(100, lambda: self.attributes('-topmost', False))
        except Exception:
            pass

    def _crear_ui(self) -> None:
        """Crea todos los elementos de la interfaz."""
        # Padding general
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # === SECCIÓN SUPERIOR: Progreso Principal ===
        progress_frame = ttk.LabelFrame(main_frame, text="Progreso General", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        # Barra de progreso
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            mode="determinate",
            maximum=self.total,
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 5))

        # Label de progreso
        self.lbl_progreso = ttk.Label(
            progress_frame,
            text=f"0 / {self.total} expedientes procesados (0%)",
            font=("TkDefaultFont", 11, "bold"),
        )
        self.lbl_progreso.pack()

        # === SECCIÓN MEDIA: Estado Actual ===
        estado_frame = ttk.LabelFrame(main_frame, text="Estado Actual", padding="10")
        estado_frame.pack(fill=tk.X, pady=(0, 10))

        # Expediente actual
        ttk.Label(estado_frame, text="Expediente:").grid(row=0, column=0, sticky=tk.W)
        self.lbl_expediente = ttk.Label(
            estado_frame,
            text="-",
            font=("TkDefaultFont", 10, "bold"),
            foreground="blue",
        )
        self.lbl_expediente.grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        # Estado/Operación actual
        ttk.Label(estado_frame, text="Operación:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.lbl_estado = ttk.Label(estado_frame, text="-")
        self.lbl_estado.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=(5, 0))

        # === SECCIÓN ESTADÍSTICAS ===
        stats_frame = ttk.LabelFrame(main_frame, text="Estadísticas", padding="10")
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        # Grid de estadísticas
        stats_grid = ttk.Frame(stats_frame)
        stats_grid.pack(fill=tk.X)

        # Exitosos
        ttk.Label(stats_grid, text="✅ Exitosos:").grid(row=0, column=0, sticky=tk.W)
        self.lbl_exitosos = ttk.Label(stats_grid, text="0", foreground="green")
        self.lbl_exitosos.grid(row=0, column=1, sticky=tk.W, padx=(5, 20))

        # Errores
        ttk.Label(stats_grid, text="❌ Errores:").grid(row=0, column=2, sticky=tk.W)
        self.lbl_errores = ttk.Label(stats_grid, text="0", foreground="red")
        self.lbl_errores.grid(row=0, column=3, sticky=tk.W, padx=(5, 20))

        # Omitidos
        ttk.Label(stats_grid, text="⊘ Omitidos:").grid(row=0, column=4, sticky=tk.W)
        self.lbl_omitidos = ttk.Label(stats_grid, text="0", foreground="orange")
        self.lbl_omitidos.grid(row=0, column=5, sticky=tk.W, padx=(5, 0))

        # Tiempo y ETA
        ttk.Label(stats_grid, text="⏱️ Tiempo:").grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        self.lbl_tiempo = ttk.Label(stats_grid, text="00:00:00")
        self.lbl_tiempo.grid(row=1, column=1, sticky=tk.W, padx=(5, 20), pady=(5, 0))

        ttk.Label(stats_grid, text="⏳ ETA:").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        self.lbl_eta = ttk.Label(stats_grid, text="Calculando...")
        self.lbl_eta.grid(row=1, column=3, sticky=tk.W, padx=(5, 0), pady=(5, 0), columnspan=3)

        # === SECCIÓN LOG ===
        log_frame = ttk.LabelFrame(main_frame, text="Log de Actividad", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            height=10,
            wrap=tk.WORD,
            font=("Monaco", 9) if self._is_macos() else ("Courier", 9),
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        self.log_text.config(state=tk.DISABLED)  # Solo lectura

        # === BOTONES DE CONTROL ===
        botones_frame = ttk.Frame(main_frame)
        botones_frame.pack(fill=tk.X)

        # Botón Pausar (deshabilitado por ahora)
        self.btn_pausar = ttk.Button(
            botones_frame,
            text="⏸️ Pausar",
            command=self._on_pausar_click,
            state=tk.DISABLED,  # Por ahora deshabilitado
        )
        self.btn_pausar.pack(side=tk.LEFT, padx=(0, 5))

        # Botón Cancelar
        self.btn_cancelar = ttk.Button(
            botones_frame,
            text="❌ Cancelar",
            command=self._on_cancelar_click,
        )
        self.btn_cancelar.pack(side=tk.LEFT)

        # Botón Cerrar (inicialmente oculto)
        self.btn_cerrar = ttk.Button(
            botones_frame,
            text="✅ Cerrar",
            command=self._on_close,
        )
        # No se muestra hasta que termine el proceso

        # Iniciar actualización de tiempo
        self._actualizar_tiempo()

    def _is_macos(self) -> bool:
        """Detecta si estamos en macOS."""
        import platform
        return platform.system() == "Darwin"

    def actualizar_progreso(
        self,
        procesados: int,
        expediente_actual: str,
        estado: str = "",
    ) -> None:
        """Actualiza el progreso principal.

        Args:
            procesados: Número de expedientes procesados hasta ahora
            expediente_actual: Número del expediente siendo procesado
            estado: Descripción del estado/operación actual
        """
        self.procesados = procesados
        self.expediente_actual = expediente_actual
        if estado:
            self.estado_actual = estado

        # Actualizar barra de progreso
        self.progress_bar["value"] = procesados

        # Actualizar labels
        porcentaje = (procesados / self.total * 100) if self.total > 0 else 0
        self.lbl_progreso.config(
            text=f"{procesados} / {self.total} expedientes procesados ({porcentaje:.1f}%)"
        )
        self.lbl_expediente.config(text=expediente_actual)
        self.lbl_estado.config(text=self.estado_actual)

        # Forzar actualización
        self.update_idletasks()

    def actualizar_estadisticas(
        self,
        exitosos: int,
        errores: int,
        omitidos: int,
    ) -> None:
        """Actualiza contadores de estadísticas.

        Args:
            exitosos: Número de expedientes exitosos
            errores: Número de expedientes con error
            omitidos: Número de expedientes omitidos
        """
        self.exitosos = exitosos
        self.errores = errores
        self.omitidos = omitidos

        self.lbl_exitosos.config(text=str(exitosos))
        self.lbl_errores.config(text=str(errores))
        self.lbl_omitidos.config(text=str(omitidos))

        self.update_idletasks()

    def agregar_log(self, mensaje: str, nivel: str = "info") -> None:
        """Agrega una línea al log de actividad.

        Args:
            mensaje: Mensaje a agregar
            nivel: Nivel del mensaje (info, success, error, warning)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")

        # Símbolos por nivel
        simbolos = {
            "info": "ℹ️",
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
        }
        simbolo = simbolos.get(nivel, "•")

        linea = f"[{timestamp}] {simbolo} {mensaje}\n"

        # Agregar al log
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, linea)
        self.log_text.see(tk.END)  # Scroll al final
        self.log_text.config(state=tk.DISABLED)

        self.update_idletasks()

    def registrar_tiempo_procesamiento(self, segundos: float) -> None:
        """Registra el tiempo de procesamiento de un expediente para calcular ETA.

        Args:
            segundos: Tiempo en segundos que tomó procesar el expediente
        """
        self.tiempos_procesamiento.append(segundos)

        # Mantener solo los últimos 10 para promedio móvil
        if len(self.tiempos_procesamiento) > 10:
            self.tiempos_procesamiento.pop(0)

        # Calcular ETA
        self._calcular_eta()

    def _calcular_eta(self) -> None:
        """Calcula y actualiza la estimación de tiempo restante."""
        if not self.tiempos_procesamiento or self.procesados == 0:
            return

        # Promedio de tiempo por expediente
        promedio_segundos = sum(self.tiempos_procesamiento) / len(self.tiempos_procesamiento)

        # Expedientes restantes
        restantes = self.total - self.procesados

        # ETA en segundos
        eta_segundos = promedio_segundos * restantes

        # Convertir a timedelta
        eta_delta = timedelta(seconds=int(eta_segundos))

        # Formatear
        horas = eta_delta.seconds // 3600
        minutos = (eta_delta.seconds % 3600) // 60
        segundos = eta_delta.seconds % 60

        if horas > 0:
            eta_str = f"{horas}h {minutos}m {segundos}s"
        elif minutos > 0:
            eta_str = f"{minutos}m {segundos}s"
        else:
            eta_str = f"{segundos}s"

        self.lbl_eta.config(text=eta_str)
        self.update_idletasks()

    def _actualizar_tiempo(self) -> None:
        """Actualiza el label de tiempo transcurrido cada segundo."""
        if not hasattr(self, "tiempo_inicio"):
            return

        transcurrido = datetime.now() - self.tiempo_inicio

        horas = transcurrido.seconds // 3600
        minutos = (transcurrido.seconds % 3600) // 60
        segundos = transcurrido.seconds % 60

        tiempo_str = f"{horas:02d}:{minutos:02d}:{segundos:02d}"
        self.lbl_tiempo.config(text=tiempo_str)

        # Programar siguiente actualización
        self.after(1000, self._actualizar_tiempo)

    def marcar_completado(self) -> None:
        """Marca el proceso como completado."""
        self.lbl_estado.config(text="✅ Proceso completado")

        # Mostrar botón cerrar, ocultar cancelar
        self.btn_cancelar.pack_forget()
        self.btn_pausar.pack_forget()
        self.btn_cerrar.pack(side=tk.LEFT)

        # Deshabilitar cierre con X hasta que se presione cerrar
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self.agregar_log("Proceso de extracción completado", "success")
        self.update_idletasks()

    def marcar_error_fatal(self, mensaje: str) -> None:
        """Marca el proceso como terminado por error fatal.

        Args:
            mensaje: Mensaje de error a mostrar
        """
        self.lbl_estado.config(text=f"❌ Error: {mensaje}")

        # Mostrar botón cerrar
        self.btn_cancelar.pack_forget()
        self.btn_pausar.pack_forget()
        self.btn_cerrar.pack(side=tk.LEFT)

        self.agregar_log(f"Error fatal: {mensaje}", "error")
        self.update_idletasks()

    def _on_pausar_click(self) -> None:
        """Handler del botón pausar."""
        if self._on_pause:
            self._pausado = not self._pausado
            if self._pausado:
                self.btn_pausar.config(text="▶️ Reanudar")
                self.agregar_log("Proceso pausado por el usuario", "warning")
            else:
                self.btn_pausar.config(text="⏸️ Pausar")
                self.agregar_log("Proceso reanudado", "info")

            self._on_pause()

    def _on_cancelar_click(self) -> None:
        """Handler del botón cancelar."""
        # Confirmar cancelación
        from tkinter import messagebox

        respuesta = messagebox.askyesno(
            "Confirmar Cancelación",
            "¿Está seguro que desea cancelar la extracción?\n\n"
            "Los expedientes ya procesados se mantendrán, pero los restantes no se descargarán.",
            icon=messagebox.WARNING,
        )

        if respuesta:
            if self._on_cancel:
                self._on_cancel()

            self.agregar_log("Proceso cancelado por el usuario", "warning")
            self.lbl_estado.config(text="❌ Cancelado por el usuario")

            # Mostrar botón cerrar
            self.btn_cancelar.pack_forget()
            self.btn_pausar.pack_forget()
            self.btn_cerrar.pack(side=tk.LEFT)

    def _on_close(self) -> None:
        """Handler del cierre de ventana."""
        # Solo permitir cerrar si el proceso terminó
        if self.btn_cerrar.winfo_ismapped():
            self.destroy()
        else:
            # Si el proceso está corriendo, preguntar si cancelar
            self._on_cancelar_click()


def test_progress_window():
    """Función de prueba para la ventana de progreso."""
    import time
    import random

    root = tk.Tk()
    root.withdraw()

    # Crear ventana de progreso
    progress = ProgressWindow(root, total_expedientes=10)

    # Simular procesamiento
    def simular_procesamiento():
        expedientes_prueba = [
            f"EXP-{i:03d}/2024" for i in range(1, 11)
        ]

        for i, exp in enumerate(expedientes_prueba, 1):
            # Actualizar progreso
            progress.actualizar_progreso(
                i,
                exp,
                f"Descargando actuaciones ({random.randint(5, 20)} encontradas)..."
            )
            progress.agregar_log(f"Procesando expediente {exp}")

            # Simular trabajo
            time_ms = random.randint(500, 1500)
            root.after(time_ms)
            root.update()

            # Actualizar estadísticas (simular éxito o error)
            if random.random() < 0.9:  # 90% éxito
                progress.actualizar_estadisticas(i, 0, 0)
                progress.agregar_log(f"Expediente {exp} descargado correctamente", "success")
            else:
                progress.actualizar_estadisticas(i - 1, 1, 0)
                progress.agregar_log(f"Error al descargar {exp}", "error")

            # Registrar tiempo
            progress.registrar_tiempo_procesamiento(time_ms / 1000)

        # Marcar completado
        progress.marcar_completado()

    # Iniciar simulación
    root.after(500, simular_procesamiento)

    root.mainloop()


if __name__ == "__main__":
    test_progress_window()
