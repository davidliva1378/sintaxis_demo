"""Formulario de configuración del sistema PJN.

Este módulo proporciona una interfaz gráfica completa con pestañas
para configurar todos los aspectos del sistema.
"""

from __future__ import annotations

import sys
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Callable, Sequence

if __package__ in (None, ""):
    _PACKAGE_ROOT = Path(__file__).resolve().parents[2]
    _PROJECT_ROOT = _PACKAGE_ROOT.parent
    _project_root_str = str(_PROJECT_ROOT)
    if _project_root_str not in sys.path:
        sys.path.append(_project_root_str)

    from Sistema_v5.configuracion.core.system_config import (  # type: ignore[import-not-found]
        SystemConfig,
        ModoMonitor,
        ModoComparacion,
        FormatoReporte,
        NivelLog,
    )

    from Sistema_v5.configuracion.gui.config_widgets import (  # type: ignore[import-not-found]
        DirectorySelector,
        DatePicker,
        TimePicker,
        IntervalInput,
        DaysSelector,
    )
else:
    from ..core.system_config import (
        SystemConfig,
        ModoMonitor,
        ModoComparacion,
        FormatoReporte,
        NivelLog,
    )

    from .config_widgets import (
        DirectorySelector,
        DatePicker,
        TimePicker,
        IntervalInput,
        DaysSelector,
    )


class ConfigForm(tk.Tk):
    """Formulario principal de configuración del sistema PJN.

    Proporciona una interfaz gráfica con pestañas para configurar:
    - Directorios del sistema
    - Opciones de monitoreo
    - Configuración de extracción
    - Configuración general del sistema
    """

    def __init__(self, config_path: str = "config/sistema.json"):
        """Inicializa el formulario de configuración.

        Args:
            config_path: Ruta al archivo de configuración
        """
        super().__init__()

        self.config_path = Path(config_path)
        self.config: SystemConfig | None = None

        # Configurar ventana
        self.title("Configuración del Sistema PJN")
        self.geometry("800x600")
        self.resizable(True, True)

        # Crear UI
        self._create_widgets()
        self._load_config()

    def _create_widgets(self) -> None:
        """Crea todos los widgets de la interfaz."""
        # Frame principal
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Crear notebook (pestañas)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Crear pestañas
        self._create_directories_tab()
        self._create_monitoring_tab()
        self._create_extraction_tab()
        self._create_system_tab()

        # Frame de botones
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(
            button_frame,
            text="💾 Guardar",
            command=self._save_config
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="🔄 Recargar",
            command=self._load_config
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="🔧 Restaurar Defaults",
            command=self._restore_defaults
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="📂 Exportar...",
            command=self._export_config
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="📁 Importar...",
            command=self._import_config
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            button_frame,
            text="❌ Cerrar",
            command=self.quit
        ).pack(side=tk.RIGHT, padx=5)

    # =========================================================================
    # PESTAÑA DE DIRECTORIOS
    # =========================================================================

    def _create_directories_tab(self) -> None:
        """Crea la pestaña de configuración de directorios."""
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="📁 Directorios")

        # Frame con scroll
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Empaquetar canvas y scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Crear campos
        self.dir_widgets = {}

        directories = [
            ("extraccion_inicial", "Extracción Inicial", "Archivos fuente para comparaciones"),
            ("extracciones_temporales", "Extracciones Temporales", "Extracciones en progreso"),
            ("expedientes_base", "Expedientes", "Carpetas de expedientes individuales"),
            ("comparaciones", "Comparaciones", "Resultados de comparaciones"),
            ("reportes", "Reportes", "Reportes generados"),
            ("logs", "Logs", "Archivos de log del sistema"),
            ("backups", "Backups", "Backups de configuración"),
            ("cache", "Cache", "Cache de sesiones y datos temporales"),
            ("descargas", "Descargas", "PDFs y archivos descargados"),
            ("monitor_datos", "Monitor (Datos)", "Datos del monitor"),
        ]

        for i, (key, label, tooltip) in enumerate(directories):
            frame = ttk.LabelFrame(scrollable_frame, text=label, padding=10)
            frame.pack(fill=tk.X, padx=5, pady=5)

            # Tooltip
            ttk.Label(
                frame,
                text=tooltip,
                font=("TkDefaultFont", 9, "italic"),
                foreground="gray"
            ).pack(anchor=tk.W, pady=(0, 5))

            # Selector de directorio
            selector = DirectorySelector(frame)
            selector.pack(fill=tk.X)

            self.dir_widgets[f"directorio_{key}"] = selector

    # =========================================================================
    # PESTAÑA DE MONITOREO
    # =========================================================================

    def _create_monitoring_tab(self) -> None:
        """Crea la pestaña de configuración de monitoreo."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="🔍 Monitoreo")

        # Frame con scroll
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.mon_widgets = {}

        # Modo de monitor
        frame = ttk.LabelFrame(scrollable_frame, text="Modo de Operación", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        self.mon_widgets["modo_monitor"] = tk.StringVar(value="automatico")
        ttk.Radiobutton(
            frame,
            text="Automático (alterna según horario)",
            variable=self.mon_widgets["modo_monitor"],
            value="automatico"
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            frame,
            text="Siempre horario laboral",
            variable=self.mon_widgets["modo_monitor"],
            value="laboral"
        ).pack(anchor=tk.W)
        ttk.Radiobutton(
            frame,
            text="Siempre horario no laboral",
            variable=self.mon_widgets["modo_monitor"],
            value="no_laboral"
        ).pack(anchor=tk.W)

        # Intervalos
        frame = ttk.LabelFrame(scrollable_frame, text="Intervalos de Verificación", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        # Intervalos laborales
        ttk.Label(frame, text="Horario laboral:").pack(anchor=tk.W, pady=(0, 5))

        subframe = ttk.Frame(frame)
        subframe.pack(fill=tk.X, padx=20, pady=(0, 10))

        ttk.Label(subframe, text="Expedientes:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.mon_widgets["intervalos_laboral_expedientes"] = IntervalInput(
            subframe,
            initial_value=15,
            unit="minutos"
        )
        self.mon_widgets["intervalos_laboral_expedientes"].grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(subframe, text="Entradas:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.mon_widgets["intervalos_laboral_entradas"] = IntervalInput(
            subframe,
            initial_value=10,
            unit="minutos"
        )
        self.mon_widgets["intervalos_laboral_entradas"].grid(row=1, column=1, sticky=tk.W, padx=(10, 0))

        # Intervalos no laborales
        ttk.Label(frame, text="Horario no laboral:").pack(anchor=tk.W, pady=(10, 5))

        subframe = ttk.Frame(frame)
        subframe.pack(fill=tk.X, padx=20, pady=(0, 10))

        ttk.Label(subframe, text="Expedientes:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.mon_widgets["intervalos_no_laboral_expedientes"] = IntervalInput(
            subframe,
            initial_value=60,
            unit="minutos"
        )
        self.mon_widgets["intervalos_no_laboral_expedientes"].grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(subframe, text="Entradas:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.mon_widgets["intervalos_no_laboral_entradas"] = IntervalInput(
            subframe,
            initial_value=30,
            unit="minutos"
        )
        self.mon_widgets["intervalos_no_laboral_entradas"].grid(row=1, column=1, sticky=tk.W, padx=(10, 0))

        # Horario laboral
        frame = ttk.LabelFrame(scrollable_frame, text="Horario Laboral", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        subframe = ttk.Frame(frame)
        subframe.pack(fill=tk.X)

        ttk.Label(subframe, text="Hora inicio:").pack(side=tk.LEFT, padx=(0, 5))
        self.mon_widgets["hora_inicio"] = TimePicker(subframe, initial_value="08:00")
        self.mon_widgets["hora_inicio"].pack(side=tk.LEFT, padx=(0, 20))

        ttk.Label(subframe, text="Hora fin:").pack(side=tk.LEFT, padx=(0, 5))
        self.mon_widgets["hora_fin"] = TimePicker(subframe, initial_value="18:00")
        self.mon_widgets["hora_fin"].pack(side=tk.LEFT)

        # Días laborales
        ttk.Label(frame, text="Días laborales:").pack(anchor=tk.W, pady=(10, 5))
        self.mon_widgets["dias_laborales"] = DaysSelector(
            frame,
            initial_days=["lunes", "martes", "miercoles", "jueves", "viernes"]
        )
        self.mon_widgets["dias_laborales"].pack(fill=tk.X, pady=(0, 5))

        # Verificaciones
        frame = ttk.LabelFrame(scrollable_frame, text="Verificaciones", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        self.mon_widgets["verificar_entradas"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="Verificar entradas",
            variable=self.mon_widgets["verificar_entradas"]
        ).pack(anchor=tk.W)

        self.mon_widgets["verificar_expedientes"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="Verificar expedientes",
            variable=self.mon_widgets["verificar_expedientes"]
        ).pack(anchor=tk.W)

        # Notificaciones
        frame = ttk.LabelFrame(scrollable_frame, text="Notificaciones", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        self.mon_widgets["notificar_nuevas_entradas"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="Notificar nuevas entradas",
            variable=self.mon_widgets["notificar_nuevas_entradas"]
        ).pack(anchor=tk.W)

        self.mon_widgets["notificar_cambios_expedientes"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="Notificar cambios en expedientes",
            variable=self.mon_widgets["notificar_cambios_expedientes"]
        ).pack(anchor=tk.W)

        self.mon_widgets["notificar_errores"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="Notificar errores",
            variable=self.mon_widgets["notificar_errores"]
        ).pack(anchor=tk.W)

        # Comparación y filtros
        frame = ttk.LabelFrame(scrollable_frame, text="Comparación y filtros", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        self.mon_widgets["comparacion_automatica"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame,
            text="Ejecutar comparación automática tras cada verificación",
            variable=self.mon_widgets["comparacion_automatica"]
        ).pack(anchor=tk.W)

        ttk.Label(frame, text="Modo de comparación:").pack(anchor=tk.W, pady=(10, 5))
        self.mon_widgets["modo_comparacion"] = ttk.Combobox(
            frame,
            values=["automatico", "manual", "deshabilitado"],
            state="readonly",
            width=20
        )
        self.mon_widgets["modo_comparacion"].set("manual")
        self.mon_widgets["modo_comparacion"].pack(anchor=tk.W, padx=20, pady=(0, 10))

        ttk.Label(frame, text="Filtros de fecha para entradas:").pack(anchor=tk.W)
        entradas_frame = ttk.Frame(frame)
        entradas_frame.pack(fill=tk.X, padx=20, pady=(5, 10))

        ttk.Label(entradas_frame, text="Desde:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.mon_widgets["fecha_desde_entradas"] = DatePicker(entradas_frame)
        self.mon_widgets["fecha_desde_entradas"].grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(entradas_frame, text="Hasta:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.mon_widgets["fecha_hasta_entradas"] = DatePicker(entradas_frame)
        self.mon_widgets["fecha_hasta_entradas"].grid(row=1, column=1, sticky=tk.W, padx=(10, 0))

        # Días hacia atrás (alternativa a fechas específicas)
        ttk.Label(entradas_frame, text="O días atrás:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.mon_widgets["dias_atras_entradas"] = IntervalInput(
            entradas_frame,
            initial_value=None,
            unit="días",
            min_value=1,
            max_value=365
        )
        self.mon_widgets["dias_atras_entradas"].grid(row=2, column=1, sticky=tk.W, padx=(10, 0))

        # Nota explicativa
        nota_label = ttk.Label(
            entradas_frame,
            text="(Si especifica 'días atrás', anula 'Desde')",
            font=("TkDefaultFont", 8, "italic"),
            foreground="gray"
        )
        nota_label.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=(2, 0))

        ttk.Label(frame, text="Filtros de fecha para expedientes:").pack(anchor=tk.W, pady=(10, 0))
        expedientes_frame = ttk.Frame(frame)
        expedientes_frame.pack(fill=tk.X, padx=20, pady=(5, 10))

        ttk.Label(expedientes_frame, text="Desde:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.mon_widgets["fecha_desde_expedientes"] = DatePicker(expedientes_frame)
        self.mon_widgets["fecha_desde_expedientes"].grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(expedientes_frame, text="Hasta:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.mon_widgets["fecha_hasta_expedientes"] = DatePicker(expedientes_frame)
        self.mon_widgets["fecha_hasta_expedientes"].grid(row=1, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(frame, text="Fecha de corte para expedientes:").pack(anchor=tk.W)
        corte_frame = ttk.Frame(frame)
        corte_frame.pack(fill=tk.X, padx=20, pady=(5, 0))
        self.mon_widgets["fecha_corte_expedientes"] = DatePicker(corte_frame)
        self.mon_widgets["fecha_corte_expedientes"].pack(anchor=tk.W)

        # Días hacia atrás para expedientes
        ttk.Label(frame, text="O días atrás para expedientes:").pack(anchor=tk.W, pady=(10, 5))
        dias_atras_exp_frame = ttk.Frame(frame)
        dias_atras_exp_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        self.mon_widgets["dias_atras_expedientes"] = IntervalInput(
            dias_atras_exp_frame,
            initial_value=None,
            unit="días",
            min_value=1,
            max_value=365
        )
        self.mon_widgets["dias_atras_expedientes"].pack(anchor=tk.W)

        # Configuración avanzada de extracción de expedientes
        frame_exp_avanzado = ttk.LabelFrame(scrollable_frame, text="Extracción de Expedientes - Avanzado", padding=10)
        frame_exp_avanzado.pack(fill=tk.X, padx=5, pady=5)

        # Extracción completa
        self.mon_widgets["extraccion_expedientes_completa"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame_exp_avanzado,
            text="Extracción completa (sin límite de páginas)",
            variable=self.mon_widgets["extraccion_expedientes_completa"]
        ).pack(anchor=tk.W, pady=(0, 10))

        # Ordenamiento
        orden_subframe = ttk.Frame(frame_exp_avanzado)
        orden_subframe.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(orden_subframe, text="Ordenar por:").pack(side=tk.LEFT, padx=(0, 10))
        self.mon_widgets["expedientes_orden"] = ttk.Combobox(
            orden_subframe,
            values=["Sin orden", "Fecha", "Carátula", "Oficina", "Situación"],
            state="readonly",
            width=20
        )
        self.mon_widgets["expedientes_orden"].set("Fecha")
        self.mon_widgets["expedientes_orden"].pack(side=tk.LEFT)

        # Detener en duplicados
        self.mon_widgets["expedientes_detener_duplicados"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame_exp_avanzado,
            text="Detener al encontrar expedientes duplicados",
            variable=self.mon_widgets["expedientes_detener_duplicados"]
        ).pack(anchor=tk.W, pady=(0, 10))

        # Máximo de páginas (solo si no es extracción completa)
        max_pag_subframe = ttk.Frame(frame_exp_avanzado)
        max_pag_subframe.pack(fill=tk.X)

        ttk.Label(max_pag_subframe, text="Máximo de páginas:").pack(side=tk.LEFT, padx=(0, 10))
        self.mon_widgets["expedientes_max_paginas"] = IntervalInput(
            max_pag_subframe,
            initial_value=50,
            unit="páginas",
            min_value=1,
            max_value=1000
        )
        self.mon_widgets["expedientes_max_paginas"].pack(side=tk.LEFT)

        # Nota explicativa
        nota_max_pag = ttk.Label(
            frame_exp_avanzado,
            text="(Se ignora si 'Extracción completa' está activado)",
            font=("TkDefaultFont", 8, "italic"),
            foreground="gray"
        )
        nota_max_pag.pack(anchor=tk.W, pady=(2, 0))

    # =========================================================================
    # PESTAÑA DE EXTRACCIÓN
    # =========================================================================

    def _create_extraction_tab(self) -> None:
        """Crea la pestaña de configuración de extracción."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="⚙️ Extracción")

        # Frame con scroll
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.ext_widgets = {}

        # Browser
        frame = ttk.LabelFrame(scrollable_frame, text="Browser", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        self.ext_widgets["headless"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="Modo headless (sin interfaz gráfica)",
            variable=self.ext_widgets["headless"]
        ).pack(anchor=tk.W)

        # Límites
        frame = ttk.LabelFrame(scrollable_frame, text="Límites", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(frame, text="Máximo de páginas a extraer:").pack(anchor=tk.W, pady=(0, 5))
        self.ext_widgets["max_paginas_expedientes"] = IntervalInput(
            frame,
            initial_value=200,
            unit="páginas",
            min_value=1,
            max_value=1000
        )
        self.ext_widgets["max_paginas_expedientes"].pack(anchor=tk.W, padx=20)

        # Timeouts
        frame = ttk.LabelFrame(scrollable_frame, text="Timeouts (milisegundos)", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        subframe = ttk.Frame(frame)
        subframe.pack(fill=tk.X)

        ttk.Label(subframe, text="Por defecto:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ext_widgets["timeout_default"] = IntervalInput(
            subframe,
            initial_value=8000,
            unit="ms",
            min_value=1000,
            max_value=60000
        )
        self.ext_widgets["timeout_default"].grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(subframe, text="Login:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.ext_widgets["timeout_login"] = IntervalInput(
            subframe,
            initial_value=60000,
            unit="ms",
            min_value=10000,
            max_value=120000
        )
        self.ext_widgets["timeout_login"].grid(row=1, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(subframe, text="Descarga:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.ext_widgets["timeout_descarga"] = IntervalInput(
            subframe,
            initial_value=30000,
            unit="ms",
            min_value=5000,
            max_value=120000
        )
        self.ext_widgets["timeout_descarga"].grid(row=2, column=1, sticky=tk.W, padx=(10, 0))

        # Reintentos
        frame = ttk.LabelFrame(scrollable_frame, text="Reintentos", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        subframe = ttk.Frame(frame)
        subframe.pack(fill=tk.X)

        ttk.Label(subframe, text="Expedientes:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.ext_widgets["max_reintentos_expedientes"] = IntervalInput(
            subframe,
            initial_value=3,
            unit="reintentos",
            min_value=1,
            max_value=20
        )
        self.ext_widgets["max_reintentos_expedientes"].grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Label(subframe, text="Espera:").grid(row=0, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        self.ext_widgets["espera_reintentos_expedientes"] = IntervalInput(
            subframe,
            initial_value=30,
            unit="segundos",
            min_value=1,
            max_value=300
        )
        self.ext_widgets["espera_reintentos_expedientes"].grid(row=0, column=3, sticky=tk.W, padx=(10, 0))

        ttk.Label(subframe, text="Entradas:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.ext_widgets["max_reintentos_entradas"] = IntervalInput(
            subframe,
            initial_value=3,
            unit="reintentos",
            min_value=1,
            max_value=20
        )
        self.ext_widgets["max_reintentos_entradas"].grid(row=1, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Label(subframe, text="Espera:").grid(row=1, column=2, sticky=tk.W, padx=(20, 0), pady=2)
        self.ext_widgets["espera_reintentos_entradas"] = IntervalInput(
            subframe,
            initial_value=30,
            unit="segundos",
            min_value=1,
            max_value=300
        )
        self.ext_widgets["espera_reintentos_entradas"].grid(row=1, column=3, sticky=tk.W, padx=(10, 0))

        ttk.Label(subframe, text="Descargas:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.ext_widgets["max_reintentos_descarga"] = IntervalInput(
            subframe,
            initial_value=3,
            unit="reintentos",
            min_value=1,
            max_value=20
        )
        self.ext_widgets["max_reintentos_descarga"].grid(row=2, column=1, sticky=tk.W, padx=(10, 0))
        subframe.columnconfigure(3, weight=1)

    # =========================================================================
    # PESTAÑA DE SISTEMA
    # =========================================================================

    def _create_system_tab(self) -> None:
        """Crea la pestaña de configuración del sistema."""
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="🔧 Sistema")

        # Frame con scroll
        canvas = tk.Canvas(tab)
        scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.sys_widgets = {}

        # Logging
        frame = ttk.LabelFrame(scrollable_frame, text="Logging", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(frame, text="Nivel de log:").pack(anchor=tk.W, pady=(0, 5))
        self.sys_widgets["nivel_log"] = ttk.Combobox(
            frame,
            values=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
            state="readonly",
            width=15
        )
        self.sys_widgets["nivel_log"].set("INFO")
        self.sys_widgets["nivel_log"].pack(anchor=tk.W, padx=20, pady=(0, 10))

        self.sys_widgets["rotacion_logs"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="Habilitar rotación de logs",
            variable=self.sys_widgets["rotacion_logs"]
        ).pack(anchor=tk.W)

        ttk.Label(frame, text="Tamaño máximo de log:").pack(anchor=tk.W, pady=(10, 5))
        self.sys_widgets["max_tamaño_log_mb"] = IntervalInput(
            frame,
            initial_value=50,
            unit="MB",
            min_value=1,
            max_value=500
        )
        self.sys_widgets["max_tamaño_log_mb"].pack(anchor=tk.W, padx=20)

        # Backups
        frame = ttk.LabelFrame(scrollable_frame, text="Backups", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(frame, text="Intervalo de backup automático:").pack(anchor=tk.W, pady=(0, 5))
        self.sys_widgets["intervalo_backup_automatico"] = IntervalInput(
            frame,
            initial_value=7,
            unit="días",
            min_value=1,
            max_value=365
        )
        self.sys_widgets["intervalo_backup_automatico"].pack(anchor=tk.W, padx=20, pady=(0, 10))

        ttk.Label(frame, text="Retener históricos:").pack(anchor=tk.W, pady=(0, 5))
        self.sys_widgets["retener_historico_dias"] = IntervalInput(
            frame,
            initial_value=90,
            unit="días",
            min_value=7,
            max_value=3650
        )
        self.sys_widgets["retener_historico_dias"].pack(anchor=tk.W, padx=20)

        # Sesión
        frame = ttk.LabelFrame(scrollable_frame, text="Sesión del Portal", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        self.sys_widgets["guardar_sesion"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            frame,
            text="Guardar sesión entre ejecuciones",
            variable=self.sys_widgets["guardar_sesion"]
        ).pack(anchor=tk.W)

        ttk.Label(frame, text="Duración de sesión:").pack(anchor=tk.W, pady=(10, 5))
        self.sys_widgets["duracion_sesion_horas"] = IntervalInput(
            frame,
            initial_value=24,
            unit="horas",
            min_value=1,
            max_value=168
        )
        self.sys_widgets["duracion_sesion_horas"].pack(anchor=tk.W, padx=20)

        # Límites de recursos
        frame = ttk.LabelFrame(scrollable_frame, text="Límites de Recursos", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(frame, text="Límite de memoria (0 = sin límite):").pack(anchor=tk.W, pady=(0, 5))
        self.sys_widgets["limite_memoria_mb"] = IntervalInput(
            frame,
            initial_value=2048,
            unit="MB",
            min_value=0,
            max_value=16384
        )
        self.sys_widgets["limite_memoria_mb"].pack(anchor=tk.W, padx=20, pady=(0, 10))

        ttk.Label(frame, text="Máximo de archivos en cache (0 = sin límite):").pack(anchor=tk.W, pady=(0, 5))
        self.sys_widgets["max_archivos_cache"] = IntervalInput(
            frame,
            initial_value=1000,
            unit="archivos",
            min_value=0,
            max_value=10000
        )
        self.sys_widgets["max_archivos_cache"].pack(anchor=tk.W, padx=20)

        # Reportes
        frame = ttk.LabelFrame(scrollable_frame, text="Reportes", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        self.sys_widgets["generar_reportes_automaticos"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            frame,
            text="Generar reportes automáticamente",
            variable=self.sys_widgets["generar_reportes_automaticos"]
        ).pack(anchor=tk.W)

        ttk.Label(frame, text="Formato de reportes:").pack(anchor=tk.W, pady=(10, 5))
        self.sys_widgets["formato_reportes"] = ttk.Combobox(
            frame,
            values=["json", "excel", "pdf"],
            state="readonly",
            width=15
        )
        self.sys_widgets["formato_reportes"].set("json")
        self.sys_widgets["formato_reportes"].pack(anchor=tk.W, padx=20)

        # Información del sistema
        frame = ttk.LabelFrame(scrollable_frame, text="Información del sistema", padding=10)
        frame.pack(fill=tk.X, padx=5, pady=5)

        self.sys_widgets["fecha_inicio_sistema"] = tk.StringVar(value="-")
        self.sys_widgets["fecha_ultimo_backup"] = tk.StringVar(value="-")

        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.X, padx=10, pady=(0, 5))

        ttk.Label(info_frame, text="Fecha de inicio:").grid(row=0, column=0, sticky=tk.W, pady=2)
        ttk.Entry(
            info_frame,
            textvariable=self.sys_widgets["fecha_inicio_sistema"],
            state="readonly",
            width=25
        ).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))

        ttk.Label(info_frame, text="Último backup:").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(
            info_frame,
            textvariable=self.sys_widgets["fecha_ultimo_backup"],
            state="readonly",
            width=25
        ).grid(row=1, column=1, sticky=tk.W, padx=(10, 0))

    # =========================================================================
    # MÉTODOS DE CARGA/GUARDADO
    # =========================================================================

    def _load_config(self) -> None:
        """Carga la configuración desde archivo."""
        try:
            # Cargar configuración
            if self.config_path.exists():
                self.config = SystemConfig.from_file(self.config_path)
            else:
                self.config = SystemConfig()

            # Actualizar widgets de directorios
            for key, widget in self.dir_widgets.items():
                value = getattr(self.config, key, "")
                widget.set(value)

            # Actualizar widgets de monitoreo
            self.mon_widgets["modo_monitor"].set(self.config.modo_monitor)
            self.mon_widgets["intervalos_laboral_expedientes"].set(self.config.intervalos_laboral_expedientes)
            self.mon_widgets["intervalos_laboral_entradas"].set(self.config.intervalos_laboral_entradas)
            self.mon_widgets["intervalos_no_laboral_expedientes"].set(self.config.intervalos_no_laboral_expedientes)
            self.mon_widgets["intervalos_no_laboral_entradas"].set(self.config.intervalos_no_laboral_entradas)
            self.mon_widgets["hora_inicio"].set(self.config.hora_inicio)
            self.mon_widgets["hora_fin"].set(self.config.hora_fin)
            self.mon_widgets["dias_laborales"].set(self.config.dias_laborales)
            self.mon_widgets["verificar_entradas"].set(self.config.verificar_entradas)
            self.mon_widgets["verificar_expedientes"].set(self.config.verificar_expedientes)
            self.mon_widgets["notificar_nuevas_entradas"].set(self.config.notificar_nuevas_entradas)
            self.mon_widgets["notificar_cambios_expedientes"].set(self.config.notificar_cambios_expedientes)
            self.mon_widgets["notificar_errores"].set(self.config.notificar_errores)
            self.mon_widgets["comparacion_automatica"].set(self.config.comparacion_automatica)
            self.mon_widgets["modo_comparacion"].set(self.config.modo_comparacion)
            self.mon_widgets["fecha_desde_entradas"].set(self.config.fecha_desde_entradas)
            self.mon_widgets["fecha_hasta_entradas"].set(self.config.fecha_hasta_entradas)
            self.mon_widgets["fecha_desde_expedientes"].set(self.config.fecha_desde_expedientes)
            self.mon_widgets["fecha_hasta_expedientes"].set(self.config.fecha_hasta_expedientes)
            self.mon_widgets["fecha_corte_expedientes"].set(self.config.fecha_corte_expedientes)

            # Nuevos campos - días atrás y configuración avanzada expedientes
            self.mon_widgets["dias_atras_entradas"].set(self.config.dias_atras_entradas)
            self.mon_widgets["dias_atras_expedientes"].set(self.config.dias_atras_expedientes)
            self.mon_widgets["extraccion_expedientes_completa"].set(self.config.extraccion_expedientes_completa)

            # Mapear valor de orden a texto del combobox
            orden_map = {None: "Sin orden", "fecha": "Fecha", "caratula": "Carátula",
                        "oficina": "Oficina", "situacion": "Situación"}
            orden_texto = orden_map.get(self.config.expedientes_orden, "Fecha")
            self.mon_widgets["expedientes_orden"].set(orden_texto)

            self.mon_widgets["expedientes_detener_duplicados"].set(self.config.expedientes_detener_duplicados)
            if self.config.expedientes_max_paginas is not None:
                self.mon_widgets["expedientes_max_paginas"].set(self.config.expedientes_max_paginas)

            # Actualizar widgets de extracción
            self.ext_widgets["headless"].set(self.config.headless)
            self.ext_widgets["max_paginas_expedientes"].set(self.config.max_paginas_expedientes)
            self.ext_widgets["timeout_default"].set(self.config.timeout_default)
            self.ext_widgets["timeout_login"].set(self.config.timeout_login)
            self.ext_widgets["timeout_descarga"].set(self.config.timeout_descarga)
            self.ext_widgets["max_reintentos_expedientes"].set(self.config.max_reintentos_expedientes)
            self.ext_widgets["max_reintentos_entradas"].set(self.config.max_reintentos_entradas)
            self.ext_widgets["max_reintentos_descarga"].set(self.config.max_reintentos_descarga)
            self.ext_widgets["espera_reintentos_expedientes"].set(self.config.espera_reintentos_expedientes)
            self.ext_widgets["espera_reintentos_entradas"].set(self.config.espera_reintentos_entradas)

            # Actualizar widgets de sistema
            self.sys_widgets["nivel_log"].set(self.config.nivel_log)
            self.sys_widgets["rotacion_logs"].set(self.config.rotacion_logs)
            self.sys_widgets["max_tamaño_log_mb"].set(self.config.max_tamaño_log_mb)
            self.sys_widgets["intervalo_backup_automatico"].set(self.config.intervalo_backup_automatico)
            self.sys_widgets["retener_historico_dias"].set(self.config.retener_historico_dias)
            self.sys_widgets["guardar_sesion"].set(self.config.guardar_sesion)
            self.sys_widgets["duracion_sesion_horas"].set(self.config.duracion_sesion_horas)
            self.sys_widgets["limite_memoria_mb"].set(self.config.limite_memoria_mb)
            self.sys_widgets["max_archivos_cache"].set(self.config.max_archivos_cache)
            self.sys_widgets["generar_reportes_automaticos"].set(self.config.generar_reportes_automaticos)
            self.sys_widgets["formato_reportes"].set(self.config.formato_reportes)
            self.sys_widgets["fecha_inicio_sistema"].set(self.config.fecha_inicio_sistema or "-")
            self.sys_widgets["fecha_ultimo_backup"].set(self.config.fecha_ultimo_backup or "-")

            messagebox.showinfo("Éxito", "Configuración cargada correctamente")

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar configuración:\n{e}")

    def _save_config(self) -> None:
        """Guarda la configuración actual."""
        try:
            # Crear nueva configuración con valores de los widgets
            config_data = {}

            # Directorios
            for key, widget in self.dir_widgets.items():
                config_data[key] = widget.get()

            # Monitoreo
            config_data["modo_monitor"] = self.mon_widgets["modo_monitor"].get()
            config_data["intervalos_laboral_expedientes"] = self.mon_widgets["intervalos_laboral_expedientes"].get()
            config_data["intervalos_laboral_entradas"] = self.mon_widgets["intervalos_laboral_entradas"].get()
            config_data["intervalos_no_laboral_expedientes"] = self.mon_widgets["intervalos_no_laboral_expedientes"].get()
            config_data["intervalos_no_laboral_entradas"] = self.mon_widgets["intervalos_no_laboral_entradas"].get()
            config_data["hora_inicio"] = self.mon_widgets["hora_inicio"].get()
            config_data["hora_fin"] = self.mon_widgets["hora_fin"].get()
            config_data["dias_laborales"] = self.mon_widgets["dias_laborales"].get()
            config_data["verificar_entradas"] = self.mon_widgets["verificar_entradas"].get()
            config_data["verificar_expedientes"] = self.mon_widgets["verificar_expedientes"].get()
            config_data["notificar_nuevas_entradas"] = self.mon_widgets["notificar_nuevas_entradas"].get()
            config_data["notificar_cambios_expedientes"] = self.mon_widgets["notificar_cambios_expedientes"].get()
            config_data["notificar_errores"] = self.mon_widgets["notificar_errores"].get()
            config_data["comparacion_automatica"] = self.mon_widgets["comparacion_automatica"].get()
            config_data["modo_comparacion"] = self.mon_widgets["modo_comparacion"].get()
            config_data["fecha_desde_entradas"] = self.mon_widgets["fecha_desde_entradas"].get()
            config_data["fecha_hasta_entradas"] = self.mon_widgets["fecha_hasta_entradas"].get()
            config_data["fecha_desde_expedientes"] = self.mon_widgets["fecha_desde_expedientes"].get()
            config_data["fecha_hasta_expedientes"] = self.mon_widgets["fecha_hasta_expedientes"].get()
            config_data["fecha_corte_expedientes"] = self.mon_widgets["fecha_corte_expedientes"].get()

            # Nuevos campos - días atrás y configuración avanzada expedientes
            config_data["dias_atras_entradas"] = self.mon_widgets["dias_atras_entradas"].get()
            config_data["dias_atras_expedientes"] = self.mon_widgets["dias_atras_expedientes"].get()
            config_data["extraccion_expedientes_completa"] = self.mon_widgets["extraccion_expedientes_completa"].get()

            # Mapear texto del combobox a valor de orden
            orden_text = self.mon_widgets["expedientes_orden"].get()
            orden_inverso_map = {"Sin orden": None, "Fecha": "fecha", "Carátula": "caratula",
                                "Oficina": "oficina", "Situación": "situacion"}
            config_data["expedientes_orden"] = orden_inverso_map.get(orden_text, None)

            config_data["expedientes_detener_duplicados"] = self.mon_widgets["expedientes_detener_duplicados"].get()
            config_data["expedientes_max_paginas"] = self.mon_widgets["expedientes_max_paginas"].get()

            # Extracción
            config_data["headless"] = self.ext_widgets["headless"].get()
            config_data["max_paginas_expedientes"] = self.ext_widgets["max_paginas_expedientes"].get()
            config_data["timeout_default"] = self.ext_widgets["timeout_default"].get()
            config_data["timeout_login"] = self.ext_widgets["timeout_login"].get()
            config_data["timeout_descarga"] = self.ext_widgets["timeout_descarga"].get()
            config_data["max_reintentos_expedientes"] = self.ext_widgets["max_reintentos_expedientes"].get()
            config_data["max_reintentos_entradas"] = self.ext_widgets["max_reintentos_entradas"].get()
            config_data["max_reintentos_descarga"] = self.ext_widgets["max_reintentos_descarga"].get()
            config_data["espera_reintentos_expedientes"] = self.ext_widgets["espera_reintentos_expedientes"].get()
            config_data["espera_reintentos_entradas"] = self.ext_widgets["espera_reintentos_entradas"].get()

            # Sistema
            config_data["nivel_log"] = self.sys_widgets["nivel_log"].get()
            config_data["rotacion_logs"] = self.sys_widgets["rotacion_logs"].get()
            config_data["max_tamaño_log_mb"] = self.sys_widgets["max_tamaño_log_mb"].get()
            config_data["intervalo_backup_automatico"] = self.sys_widgets["intervalo_backup_automatico"].get()
            config_data["retener_historico_dias"] = self.sys_widgets["retener_historico_dias"].get()
            config_data["guardar_sesion"] = self.sys_widgets["guardar_sesion"].get()
            config_data["duracion_sesion_horas"] = self.sys_widgets["duracion_sesion_horas"].get()
            config_data["limite_memoria_mb"] = self.sys_widgets["limite_memoria_mb"].get()
            config_data["max_archivos_cache"] = self.sys_widgets["max_archivos_cache"].get()
            config_data["generar_reportes_automaticos"] = self.sys_widgets["generar_reportes_automaticos"].get()
            config_data["formato_reportes"] = self.sys_widgets["formato_reportes"].get()

            # Preservar fecha_inicio_sistema si existe
            if self.config and self.config.fecha_inicio_sistema:
                config_data["fecha_inicio_sistema"] = self.config.fecha_inicio_sistema
            if self.config and self.config.fecha_ultimo_backup:
                config_data["fecha_ultimo_backup"] = self.config.fecha_ultimo_backup

            # Crear y guardar configuración
            new_config = SystemConfig(**config_data)
            new_config.to_file(self.config_path)

            # Crear directorios si no existen
            new_config.crear_directorios()

            self.config = new_config

            messagebox.showinfo("Éxito", f"Configuración guardada en:\n{self.config_path}")

        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar configuración:\n{e}")

    def _restore_defaults(self) -> None:
        """Restaura la configuración por defecto."""
        if messagebox.askyesno(
            "Confirmar",
            "¿Restaurar todos los valores a sus defaults?\n\nEsto no afectará el archivo guardado hasta que presione 'Guardar'."
        ):
            self.config = SystemConfig()
            self._load_config()

    def _export_config(self) -> None:
        """Exporta la configuración a un archivo."""
        if not self.config:
            messagebox.showwarning("Advertencia", "No hay configuración cargada")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Exportar Configuración"
        )

        if file_path:
            try:
                self.config.to_file(file_path)
                messagebox.showinfo("Éxito", f"Configuración exportada a:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al exportar:\n{e}")

    def _import_config(self) -> None:
        """Importa la configuración desde un archivo."""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Importar Configuración"
        )

        if file_path:
            try:
                self.config = SystemConfig.from_file(file_path)
                self._load_config()
                messagebox.showinfo("Éxito", "Configuración importada correctamente")
            except Exception as e:
                messagebox.showerror("Error", f"Error al importar:\n{e}")


def main(argv: Sequence[str] | None = None) -> None:
    """Punto de entrada de línea de comandos para el formulario.

    Parameters
    ----------
    argv:
        Argumentos recibidos desde la CLI. Se admite ``None`` para utilizar
        ``sys.argv[1:]`` por defecto.
    """

    import argparse

    parser = argparse.ArgumentParser(
        description="Configurador del Sistema PJN"
    )
    parser.add_argument(
        "--config",
        "-c",
        default="config/sistema.json",
        help="Ruta al archivo de configuración (default: config/sistema.json)",
    )

    args = parser.parse_args(list(argv) if argv is not None else None)

    print("=" * 70)
    print("CONFIGURADOR DEL SISTEMA PJN")
    print("=" * 70)
    print()
    print(f"Archivo de configuración: {args.config}")
    print()
    print("Abriendo interfaz gráfica...")
    print()

    app = ConfigForm(config_path=args.config)
    app.mainloop()


if __name__ == "__main__":
    main()


__all__ = ["ConfigForm"]
