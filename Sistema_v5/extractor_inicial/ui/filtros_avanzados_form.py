"""Formulario avanzado de filtrado de expedientes con previsualización.

Este módulo provee una GUI Tkinter mejorada que permite aplicar múltiples
filtros combinables sobre un listado de expedientes, con actualización en
tiempo real y exportación de resultados.
"""

from __future__ import annotations

import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
from typing import Sequence

from ...pjn.models.expediente import ExpedienteResumen
from ..filtrador import FiltradorExpedientes
from ..exporters import exportar_json, exportar_csv, exportar_excel


class FiltrosAvanzadosForm(tk.Toplevel):
    """GUI avanzada para filtrado interactivo de expedientes.

    Permite aplicar múltiples filtros combinables con previsualización
    en tiempo real y exportación de resultados seleccionados.

    Attributes:
        expedientes_originales: Listado completo sin filtrar
        filtrador: Instancia de FiltradorExpedientes
        seleccion_actual: Expedientes tras aplicar filtros
    """

    def __init__(
        self,
        master: tk.Misc | None,
        expedientes: Sequence[ExpedienteResumen],
        *,
        titulo: str = "Filtrado Avanzado de Expedientes",
    ):
        """Inicializa el formulario de filtros avanzados.

        Args:
            master: Widget padre de Tkinter
            expedientes: Listado de expedientes a filtrar
            titulo: Título de la ventana
        """
        super().__init__(master=master)
        self.title(titulo)
        self.geometry("1100x750")
        self.minsize(1000, 650)

        if master is not None:
            self.transient(master)

        self.expedientes_originales = list(expedientes)
        self.filtrador = FiltradorExpedientes(self.expedientes_originales)
        self.seleccion_actual: list[ExpedienteResumen] = list(expedientes)
        self.result: list[ExpedienteResumen] | None = None

        # Variables de filtros
        self._dias_atras_var = tk.IntVar(value=0)
        self._dias_atras_activo = tk.BooleanVar(value=False)

        self._situaciones_vars: dict[str, tk.BooleanVar] = {}
        self._situaciones_activo = tk.BooleanVar(value=False)

        self._dependencia_var = tk.StringVar()
        self._dependencia_regex = tk.BooleanVar(value=False)
        self._dependencia_activo = tk.BooleanVar(value=False)

        self._fecha_desde_var = tk.StringVar()
        self._fecha_hasta_var = tk.StringVar()
        self._rango_fechas_activo = tk.BooleanVar(value=False)

        self._build_ui()
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Aplicar filtros iniciales (sin filtrar nada)
        self._aplicar_filtros()

    def _build_ui(self) -> None:
        """Construye la interfaz gráfica completa."""
        # Frame principal con panel izquierdo (filtros) y derecho (resultados)
        main_container = ttk.Frame(self, padding=10)
        main_container.pack(fill=tk.BOTH, expand=True)

        # Panel izquierdo: Filtros
        filtros_frame = ttk.LabelFrame(main_container, text="Filtros", padding=15)
        filtros_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10))

        self._build_filtros_panel(filtros_frame)

        # Panel derecho: Resultados
        resultados_frame = ttk.Frame(main_container)
        resultados_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_resultados_panel(resultados_frame)

        # Panel inferior: Botones de acción
        self._build_botones_panel(self)

    def _build_filtros_panel(self, parent: ttk.LabelFrame) -> None:
        """Construye el panel de filtros."""
        # Filtro 1: Días atrás (última actuación)
        filtro1_frame = ttk.LabelFrame(parent, text="Actividad Reciente", padding=10)
        filtro1_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            filtro1_frame,
            text="Activar",
            variable=self._dias_atras_activo,
            command=self._aplicar_filtros,
        ).pack(anchor=tk.W)

        dias_container = ttk.Frame(filtro1_frame)
        dias_container.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(dias_container, text="Últimos").pack(side=tk.LEFT)

        dias_spinbox = ttk.Spinbox(
            dias_container,
            from_=1,
            to=365,
            textvariable=self._dias_atras_var,
            width=10,
            command=self._aplicar_filtros,
        )
        dias_spinbox.pack(side=tk.LEFT, padx=5)
        self._dias_atras_var.trace_add("write", lambda *_: self._aplicar_filtros())

        ttk.Label(dias_container, text="días").pack(side=tk.LEFT)

        # Filtro 2: Situación procesal
        filtro2_frame = ttk.LabelFrame(parent, text="Situación Procesal", padding=10)
        filtro2_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            filtro2_frame,
            text="Activar",
            variable=self._situaciones_activo,
            command=self._aplicar_filtros,
        ).pack(anchor=tk.W)

        situaciones_container = ttk.Frame(filtro2_frame)
        situaciones_container.pack(fill=tk.X, pady=(5, 0))

        # Obtener situaciones únicas del listado
        situaciones_unicas = sorted(
            {exp.situacion for exp in self.expedientes_originales if exp.situacion}
        )

        for situacion in situaciones_unicas[:8]:  # Máximo 8 para no saturar UI
            var = tk.BooleanVar(value=False)
            self._situaciones_vars[situacion] = var
            ttk.Checkbutton(
                situaciones_container,
                text=situacion,
                variable=var,
                command=self._aplicar_filtros,
            ).pack(anchor=tk.W, pady=2)

        # Filtro 3: Dependencia
        filtro3_frame = ttk.LabelFrame(parent, text="Dependencia/Juzgado", padding=10)
        filtro3_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            filtro3_frame,
            text="Activar",
            variable=self._dependencia_activo,
            command=self._aplicar_filtros,
        ).pack(anchor=tk.W)

        dep_entry = ttk.Entry(
            filtro3_frame,
            textvariable=self._dependencia_var,
            width=25,
        )
        dep_entry.pack(fill=tk.X, pady=(5, 5))
        self._dependencia_var.trace_add("write", lambda *_: self._aplicar_filtros())

        ttk.Checkbutton(
            filtro3_frame,
            text="Usar expresión regular",
            variable=self._dependencia_regex,
            command=self._aplicar_filtros,
        ).pack(anchor=tk.W)

        ttk.Label(
            filtro3_frame,
            text="Ej: JUZ. CIV. o JUZ\\.\\s*CIV\\.\\s*\\d+ (regex)",
            font=("TkDefaultFont", 8),
            foreground="gray",
        ).pack(anchor=tk.W)

        # Filtro 4: Rango de fechas
        filtro4_frame = ttk.LabelFrame(parent, text="Rango de Fechas", padding=10)
        filtro4_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Checkbutton(
            filtro4_frame,
            text="Activar",
            variable=self._rango_fechas_activo,
            command=self._aplicar_filtros,
        ).pack(anchor=tk.W)

        fechas_container = ttk.Frame(filtro4_frame)
        fechas_container.pack(fill=tk.X, pady=(5, 0))

        ttk.Label(fechas_container, text="Desde:").grid(row=0, column=0, sticky=tk.W, pady=2)
        desde_entry = ttk.Entry(fechas_container, textvariable=self._fecha_desde_var, width=15)
        desde_entry.grid(row=0, column=1, padx=(5, 0), pady=2)
        self._fecha_desde_var.trace_add("write", lambda *_: self._aplicar_filtros())

        ttk.Label(fechas_container, text="Hasta:").grid(row=1, column=0, sticky=tk.W, pady=2)
        hasta_entry = ttk.Entry(fechas_container, textvariable=self._fecha_hasta_var, width=15)
        hasta_entry.grid(row=1, column=1, padx=(5, 0), pady=2)
        self._fecha_hasta_var.trace_add("write", lambda *_: self._aplicar_filtros())

        ttk.Label(
            filtro4_frame,
            text="Formato: YYYY-MM-DD o DD/MM/YYYY",
            font=("TkDefaultFont", 8),
            foreground="gray",
        ).pack(anchor=tk.W, pady=(5, 0))

        # Botón limpiar filtros
        ttk.Button(
            parent,
            text="Limpiar Todos los Filtros",
            command=self._limpiar_filtros,
        ).pack(fill=tk.X, pady=(10, 0))

    def _build_resultados_panel(self, parent: ttk.Frame) -> None:
        """Construye el panel de resultados."""
        # Estadísticas
        stats_frame = ttk.LabelFrame(parent, text="Estadísticas", padding=10)
        stats_frame.pack(fill=tk.X, pady=(0, 10))

        self._stats_label = ttk.Label(
            stats_frame,
            text="Sin filtros aplicados",
            font=("TkDefaultFont", 10, "bold"),
        )
        self._stats_label.pack()

        # Lista de resultados
        lista_frame = ttk.LabelFrame(parent, text="Expedientes Filtrados", padding=10)
        lista_frame.pack(fill=tk.BOTH, expand=True)

        # Scrollbars
        scrollbar_y = ttk.Scrollbar(lista_frame, orient=tk.VERTICAL)
        scrollbar_x = ttk.Scrollbar(lista_frame, orient=tk.HORIZONTAL)

        self._tree = ttk.Treeview(
            lista_frame,
            columns=("numero", "dependencia", "caratula", "situacion", "ultima_act"),
            show="headings",
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
            selectmode=tk.EXTENDED,
        )

        scrollbar_y.config(command=self._tree.yview)
        scrollbar_x.config(command=self._tree.xview)

        # Configurar columnas
        self._tree.heading("numero", text="Número")
        self._tree.heading("dependencia", text="Dependencia")
        self._tree.heading("caratula", text="Carátula")
        self._tree.heading("situacion", text="Situación")
        self._tree.heading("ultima_act", text="Última Actuación")

        self._tree.column("numero", width=150, minwidth=100)
        self._tree.column("dependencia", width=200, minwidth=150)
        self._tree.column("caratula", width=300, minwidth=200)
        self._tree.column("situacion", width=120, minwidth=80)
        self._tree.column("ultima_act", width=120, minwidth=80)

        # Pack
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

    def _build_botones_panel(self, parent: tk.Toplevel) -> None:
        """Construye el panel de botones de acción."""
        botones_frame = ttk.Frame(parent, padding=10)
        botones_frame.pack(fill=tk.X, side=tk.BOTTOM)

        # Botones de exportación
        export_frame = ttk.LabelFrame(botones_frame, text="Exportar", padding=5)
        export_frame.pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            export_frame,
            text="JSON",
            command=self._exportar_json,
            width=8,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            export_frame,
            text="CSV",
            command=self._exportar_csv,
            width=8,
        ).pack(side=tk.LEFT, padx=2)

        ttk.Button(
            export_frame,
            text="Excel",
            command=self._exportar_excel,
            width=8,
        ).pack(side=tk.LEFT, padx=2)

        # Botones principales (MÁS GRANDES Y VISIBLES)
        ttk.Button(
            botones_frame,
            text="❌ Cancelar",
            command=self._on_cancel,
            width=20,
        ).pack(side=tk.RIGHT, padx=(5, 0))

        # Botón de confirmación en VERDE/destacado
        btn_confirmar = ttk.Button(
            botones_frame,
            text="✅ Confirmar y Continuar",
            command=self._on_confirmar,
            width=25,
        )
        btn_confirmar.pack(side=tk.RIGHT, padx=5)

        # Hacer el botón más visible (estilo)
        try:
            # Intentar resaltar el botón
            style = ttk.Style()
            style.configure('Accent.TButton', font=('TkDefaultFont', 12, 'bold'))
            btn_confirmar.configure(style='Accent.TButton')
        except Exception:
            pass  # Si falla, usar estilo por defecto

    def _aplicar_filtros(self) -> None:
        """Aplica todos los filtros activos y actualiza la UI."""
        # Resetear filtrador
        self.filtrador.resetear()

        # Aplicar filtros según checkboxes activos
        try:
            # Filtro 1: Días atrás
            if self._dias_atras_activo.get():
                dias = self._dias_atras_var.get()
                if dias > 0:
                    self.filtrador.filtrar_por_dias_atras(dias)

            # Filtro 2: Situaciones
            if self._situaciones_activo.get():
                situaciones_seleccionadas = [
                    situacion
                    for situacion, var in self._situaciones_vars.items()
                    if var.get()
                ]
                if situaciones_seleccionadas:
                    self.filtrador.filtrar_por_situacion(situaciones_seleccionadas)

            # Filtro 3: Dependencia
            if self._dependencia_activo.get():
                pattern = self._dependencia_var.get().strip()
                if pattern:
                    self.filtrador.filtrar_por_dependencia(
                        pattern,
                        regex=self._dependencia_regex.get(),
                    )

            # Filtro 4: Rango de fechas
            if self._rango_fechas_activo.get():
                desde = self._fecha_desde_var.get().strip() or None
                hasta = self._fecha_hasta_var.get().strip() or None
                if desde or hasta:
                    self.filtrador.filtrar_por_rango_fechas(desde, hasta)

        except ValueError as e:
            messagebox.showerror("Error de Filtro", str(e), parent=self)
            self.filtrador.resetear()

        # Obtener resultados
        self.seleccion_actual = self.filtrador.obtener_resultados()

        # Actualizar UI
        self._actualizar_resultados()
        self._actualizar_estadisticas()

    def _actualizar_resultados(self) -> None:
        """Actualiza el Treeview con los expedientes filtrados."""
        # Limpiar
        for item in self._tree.get_children():
            self._tree.delete(item)

        # Poblar
        for exp in self.seleccion_actual:
            self._tree.insert(
                "",
                tk.END,
                values=(
                    exp.numero,
                    exp.dependencia,
                    exp.caratula,
                    exp.situacion or "",
                    exp.ultima_actuacion or "",
                ),
            )

    def _actualizar_estadisticas(self) -> None:
        """Actualiza el label de estadísticas."""
        stats = self.filtrador.obtener_estadisticas()
        texto = (
            f"Total: {stats['total_filtrado']} de {stats['total_original']} "
            f"({stats['porcentaje_retenido']:.1f}% retenido)\n"
            f"Filtros aplicados: {stats['filtros_aplicados']}"
        )
        self._stats_label.config(text=texto)

    def _limpiar_filtros(self) -> None:
        """Limpia todos los filtros y restaura el listado original."""
        # Desactivar checkboxes
        self._dias_atras_activo.set(False)
        self._situaciones_activo.set(False)
        self._dependencia_activo.set(False)
        self._rango_fechas_activo.set(False)

        # Limpiar valores
        self._dias_atras_var.set(0)
        for var in self._situaciones_vars.values():
            var.set(False)
        self._dependencia_var.set("")
        self._dependencia_regex.set(False)
        self._fecha_desde_var.set("")
        self._fecha_hasta_var.set("")

        # Reaplicar (sin filtros)
        self._aplicar_filtros()

    def _exportar_json(self) -> None:
        """Exporta la selección actual a JSON."""
        if not self.seleccion_actual:
            messagebox.showwarning("Sin datos", "No hay expedientes para exportar", parent=self)
            return

        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".json",
            filetypes=[("JSON", "*.json"), ("Todos", "*.*")],
            initialfile="expedientes_filtrados.json",
        )

        if path:
            try:
                exportar_json(self.seleccion_actual, Path(path))
                messagebox.showinfo(
                    "Exportación Exitosa",
                    f"Exportados {len(self.seleccion_actual)} expedientes a:\n{path}",
                    parent=self,
                )
            except Exception as e:
                messagebox.showerror("Error de Exportación", str(e), parent=self)

    def _exportar_csv(self) -> None:
        """Exporta la selección actual a CSV."""
        if not self.seleccion_actual:
            messagebox.showwarning("Sin datos", "No hay expedientes para exportar", parent=self)
            return

        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos", "*.*")],
            initialfile="expedientes_filtrados.csv",
        )

        if path:
            try:
                exportar_csv(self.seleccion_actual, Path(path))
                messagebox.showinfo(
                    "Exportación Exitosa",
                    f"Exportados {len(self.seleccion_actual)} expedientes a:\n{path}",
                    parent=self,
                )
            except Exception as e:
                messagebox.showerror("Error de Exportación", str(e), parent=self)

    def _exportar_excel(self) -> None:
        """Exporta la selección actual a Excel."""
        if not self.seleccion_actual:
            messagebox.showwarning("Sin datos", "No hay expedientes para exportar", parent=self)
            return

        path = filedialog.asksaveasfilename(
            parent=self,
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx"), ("Todos", "*.*")],
            initialfile="expedientes_filtrados.xlsx",
        )

        if path:
            try:
                exportar_excel(self.seleccion_actual, Path(path))
                messagebox.showinfo(
                    "Exportación Exitosa",
                    f"Exportados {len(self.seleccion_actual)} expedientes a:\n{path}",
                    parent=self,
                )
            except ImportError:
                messagebox.showerror(
                    "Dependencia Faltante",
                    "La exportación a Excel requiere 'openpyxl'.\n"
                    "Instálalo con: pip install openpyxl",
                    parent=self,
                )
            except Exception as e:
                messagebox.showerror("Error de Exportación", str(e), parent=self)

    def _on_confirmar(self) -> None:
        """Confirma la selección y cierra el formulario."""
        if not self.seleccion_actual:
            respuesta = messagebox.askyesno(
                "Selección Vacía",
                "No hay expedientes seleccionados. ¿Desea continuar de todos modos?",
                parent=self,
            )
            if not respuesta:
                return

        self.result = self.seleccion_actual
        self.grab_release()
        self.destroy()

    def _on_cancel(self) -> None:
        """Cancela y cierra el formulario sin guardar."""
        self.result = None
        self.grab_release()
        self.destroy()


def mostrar_filtros_avanzados(
    expedientes: Sequence[ExpedienteResumen],
    *,
    titulo: str = "Filtrado Avanzado de Expedientes",
) -> list[ExpedienteResumen] | None:
    """Muestra el formulario de filtros avanzados y retorna la selección.

    Args:
        expedientes: Listado de expedientes a filtrar
        titulo: Título de la ventana

    Returns:
        Lista de expedientes seleccionados, o None si se canceló

    Example:
        >>> expedientes = [...]  # Lista de ExpedienteResumen
        >>> seleccion = mostrar_filtros_avanzados(expedientes)
        >>> if seleccion:
        ...     print(f"Usuario seleccionó {len(seleccion)} expedientes")
    """
    root = tk.Tk()

    # NO ocultar la ventana root en macOS
    # root.withdraw()  # Comentado para macOS

    # Configurar para macOS: forzar ventana al frente
    try:
        root.lift()
        root.attributes('-topmost', True)
        # Aplicar también a todas las ventanas toplevel
        root.after(100, lambda: root.attributes('-topmost', False))
    except Exception:
        pass  # Ignorar errores en otras plataformas

    form = FiltrosAvanzadosForm(root, expedientes, titulo=titulo)

    # En macOS, asegurar que la ventana se muestre
    try:
        form.lift()
        form.focus_force()
        form.attributes('-topmost', True)
        form.after(100, lambda: form.attributes('-topmost', False))
        # Forzar actualización
        form.update()
        form.deiconify()
    except Exception:
        pass

    root.wait_window(form)
    root.destroy()

    return form.result


__all__ = ["FiltrosAvanzadosForm", "mostrar_filtros_avanzados"]
