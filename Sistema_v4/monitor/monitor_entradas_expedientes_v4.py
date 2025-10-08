"""Monitor de expedientes y entradas basado en la bandeja del sistema.

Originalmente esta versión se enfocaba exclusivamente en la verificación
periódica de expedientes del PJN. En esta iteración se reincorpora el
módulo de entradas (notificaciones y despachos) manteniendo pendiente el
resto de utilidades avanzadas (comparaciones, respaldos, etc.).
"""

from __future__ import annotations

import base64
import json
import os
import sys
import unicodedata
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from typing import TYPE_CHECKING, Callable, Optional

from PySide6.QtCore import QThread, QTimer, Signal, QTime
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSystemTrayIcon,
    QTabWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

ComparadorExpedientes = Callable[..., "ResultadoComparacion"]

_DIAS_EN_A_ESP = {
    "monday": "lunes",
    "tuesday": "martes",
    "wednesday": "miercoles",
    "thursday": "jueves",
    "friday": "viernes",
    "saturday": "sabado",
    "sunday": "domingo",
}


def _normalizar_dia_semana(valor: object) -> str:
    """Normaliza un nombre de día quitando tildes y homogeneizando idioma."""

    if not isinstance(valor, str):
        return ""

    texto = unicodedata.normalize("NFD", valor.strip().lower())
    texto_sin_tildes = "".join(
        caracter for caracter in texto if unicodedata.category(caracter) != "Mn"
    )
    return _DIAS_EN_A_ESP.get(texto_sin_tildes, texto_sin_tildes)

if TYPE_CHECKING:  # pragma: no cover - hints para herramientas de tipo
    try:
        from .comparacion_expedientes import ResultadoComparacion
    except ImportError:  # pragma: no cover - ejecución directa
        from comparacion_expedientes import ResultadoComparacion  # type: ignore[import-not-found]

try:
    from .comparacion_expedientes import (
        MODO_COMPARACION_TOTAL as _MODO_COMPARACION_TOTAL,
        comparar_expedientes as _comparar_expedientes,
    )
except ImportError:  # pragma: no cover - ejecución directa
    try:
        from comparacion_expedientes import (
            MODO_COMPARACION_TOTAL as _MODO_COMPARACION_TOTAL,
            comparar_expedientes as _comparar_expedientes,
        )
    except ImportError:  # pragma: no cover - entorno sin comparación disponible
        comparar_expedientes: Optional[ComparadorExpedientes] = None
        _MODO_COMPARACION_TOTAL = "total"
    else:
        comparar_expedientes = _comparar_expedientes
        MODO_COMPARACION_TOTAL = _MODO_COMPARACION_TOTAL
else:
    comparar_expedientes = _comparar_expedientes
    MODO_COMPARACION_TOTAL = _MODO_COMPARACION_TOTAL

if "MODO_COMPARACION_TOTAL" not in globals():  # pragma: no cover - fallback defensivo
    MODO_COMPARACION_TOTAL = "total"

try:
    from .respaldo_historico import (
        ARCHIVOS_PREDETERMINADOS,
        generar_respaldo_monitoreo,
    )
except ImportError:  # pragma: no cover - ejecución directa
    from respaldo_historico import (  # type: ignore[import-not-found]
        ARCHIVOS_PREDETERMINADOS,
        generar_respaldo_monitoreo,
    )

try:
    from .configuracion_modo import (
        DEFAULT_CONFIG,
        MODOS_VALIDOS,
        actualizar_modo_monitor,
        cargar_config_monitor,
        guardar_config_monitor,
        obtener_fecha_corte,
    )
except ImportError:  # pragma: no cover - ejecución directa
    from configuracion_modo import (
        DEFAULT_CONFIG,
        MODOS_VALIDOS,
        actualizar_modo_monitor,
        cargar_config_monitor,
        guardar_config_monitor,
        obtener_fecha_corte,
    )

try:
    from .icono_base64 import ICONO_BASE64
except ImportError:  # pragma: no cover - ejecución directa
    from icono_base64 import ICONO_BASE64

try:  # Importa primero desde la nueva arquitectura (Sistema_v4)
    from Sistema_v4.config.urls_pjn import URL_CONSULTAS  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - compatibilidad con Sistema_v3
    from Sistema_v3.config.urls_pjn import URL_CONSULTAS

try:
    from Sistema_v4.operaciones.expedientes.expedientes_v4 import (  # type: ignore[import-not-found]
        extraer_expedientes_completos,
    )
except ImportError:  # pragma: no cover - compatibilidad con Sistema_v3
    from Sistema_v3.operaciones.expedientes.expedientes_v4 import (
        extraer_expedientes_completos,
    )

try:
    from Sistema_v4.operaciones.entradas.extractor_entradas import (  # type: ignore[import-not-found]
        extraer_entradas_pjn,
    )
except ImportError:  # pragma: no cover - compatibilidad con Sistema_v3
    from Sistema_v3.operaciones.entradas.extractor_entradas import (
        extraer_entradas_pjn,
    )

try:
    from Sistema_v4.utils.logging import registrar_log  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover - compatibilidad con Sistema_v3
    from Sistema_v3.utils.logging import registrar_log

try:
    from Sistema_v4.web.auto_login import (  # type: ignore[import-not-found]
        SESSION_FILE,
        reutilizar_sesion_async,
    )
except ImportError:  # pragma: no cover - compatibilidad con Sistema_v3
    from Sistema_v3.web.auto_login import (  # type: ignore[import-not-found]
        SESSION_FILE,
        reutilizar_sesion_async,
    )


@dataclass
class ResultadoExpedientes:
    estado: str
    cantidad: int | None = None
    total_esperado: int | None = None
    ruta: str | None = None
    error: str | None = None
    motivo: str | None = None
    motivo_original: str | None = None
    duplicados_descartados: int | None = None
    filas_descartadas: int | None = None
    paginas_recorridas: int | None = None
    paginas_esperadas: int | None = None


@dataclass
class ResultadoEntradas:
    nuevas: int | None
    base_dir: Path | None = None
    historial_json: Path | None = None
    historial_csv: Path | None = None
    error: str | None = None


class ConfiguracionDialog(QDialog):
    """Diálogo para editar los parámetros del monitor desde la bandeja."""

    def __init__(self, config: dict, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Configuración del monitor")
        self._config = deepcopy(config) if isinstance(config, dict) else {}
        self._resultado: dict | None = None
        self._crear_ui()
        self._cargar_datos()

    def _crear_ui(self) -> None:
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget(self)
        layout.addWidget(self.tabs)

        self._crear_tab_general()
        self._crear_tab_intervalos()
        self._crear_tab_filtro()
        self._crear_tab_reintentos()
        self._crear_tab_respaldo()
        self._crear_tab_notificaciones()

        self.boton_restaurar = QPushButton("Restaurar valores predeterminados", self)
        self.boton_restaurar.clicked.connect(self._restaurar_defaults)
        layout.addWidget(self.boton_restaurar)

        self.estado_label = QLabel("", self)
        self.estado_label.setWordWrap(True)
        self.estado_label.setStyleSheet("color: #555;")
        layout.addWidget(self.estado_label)

        botones = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel, parent=self)
        botones.accepted.connect(self.accept)
        botones.rejected.connect(self.reject)
        layout.addWidget(botones)

        self.resize(560, 540)
        self._conectar_eventos()

    def _crear_tab_general(self) -> None:
        pagina = QWidget(self)
        formulario = QFormLayout(pagina)

        descripcion = self._crear_label_descriptivo(
            "Seleccioná el modo de trabajo y la carpeta base donde se guardan los "
            "resultados del monitoreo. También podés decidir si la comparación se "
            "ejecuta automáticamente tras cada verificación."
        )
        formulario.addRow(descripcion)

        self.modo_combo = QComboBox(pagina)
        for modo in MODOS_VALIDOS:
            texto = modo.replace("_", " ").capitalize()
            self.modo_combo.addItem(texto, modo)
        formulario.addRow("Modo de trabajo", self.modo_combo)

        self.monitoreo_edit = QLineEdit(pagina)
        self.monitoreo_boton = QPushButton("Seleccionar…", pagina)
        self.monitoreo_boton.clicked.connect(self._seleccionar_monitoreo)
        formulario.addRow(
            "Carpeta de monitoreo",
            self._crear_contenedor_ruta(self.monitoreo_edit, self.monitoreo_boton),
        )

        self.comparacion_modo_combo = QComboBox(pagina)
        self.comparacion_modo_combo.addItem(
            "Parcial (usa fecha de corte)", "parcial"
        )
        self.comparacion_modo_combo.addItem(
            "Total (base completa)", "total"
        )
        formulario.addRow("Modo de comparación", self.comparacion_modo_combo)

        self.comparacion_auto_check = QCheckBox(
            "Ejecutar comparación automática tras cada verificación exitosa",
            pagina,
        )
        formulario.addRow(self.comparacion_auto_check)

        self.tabs.addTab(pagina, "General")

    def _crear_tab_intervalos(self) -> None:
        pagina = QWidget(self)
        formulario = QFormLayout(pagina)

        descripcion = self._crear_label_descriptivo(
            "Elegí en qué días aplica el horario laboral y definí los intervalos "
            "tanto dentro como fuera de ese rango. Los días no seleccionados "
            "utilizarán automáticamente el intervalo fuera de horario."
        )
        formulario.addRow(descripcion)

        dias_widget = QWidget(pagina)
        dias_layout = QGridLayout(dias_widget)
        dias_layout.setContentsMargins(0, 0, 0, 0)
        dias_layout.setHorizontalSpacing(12)
        dias_layout.setVerticalSpacing(4)
        self.dias_laborales_checks: list[tuple[str, str, QCheckBox]] = []
        dias_formateados = [
            ("lunes", "Lunes"),
            ("martes", "Martes"),
            ("miércoles", "Miércoles"),
            ("jueves", "Jueves"),
            ("viernes", "Viernes"),
            ("sábado", "Sábado"),
            ("domingo", "Domingo"),
        ]
        for indice, (valor, etiqueta) in enumerate(dias_formateados):
            casilla = QCheckBox(etiqueta, pagina)
            fila, columna = divmod(indice, 4)
            dias_layout.addWidget(casilla, fila, columna)
            self.dias_laborales_checks.append((valor, _normalizar_dia_semana(valor), casilla))
        formulario.addRow("Días laborales", dias_widget)

        self.hora_inicio_edit = QTimeEdit(pagina)
        self.hora_inicio_edit.setDisplayFormat("HH:mm")
        formulario.addRow("Hora de inicio", self.hora_inicio_edit)

        self.hora_fin_edit = QTimeEdit(pagina)
        self.hora_fin_edit.setDisplayFormat("HH:mm")
        formulario.addRow("Hora de fin", self.hora_fin_edit)

        self.intervalo_laboral_expedientes_spin = QSpinBox(pagina)
        self.intervalo_laboral_expedientes_spin.setRange(1, 1440)
        formulario.addRow(
            "Intervalo laboral expedientes (min)",
            self.intervalo_laboral_expedientes_spin,
        )

        self.intervalo_laboral_entradas_spin = QSpinBox(pagina)
        self.intervalo_laboral_entradas_spin.setRange(1, 1440)
        formulario.addRow(
            "Intervalo laboral entradas (min)", self.intervalo_laboral_entradas_spin
        )

        self.intervalo_no_laboral_expedientes_spin = QSpinBox(pagina)
        self.intervalo_no_laboral_expedientes_spin.setRange(1, 1440)
        formulario.addRow(
            "Intervalo fuera de horario expedientes (min)",
            self.intervalo_no_laboral_expedientes_spin,
        )

        self.intervalo_no_laboral_entradas_spin = QSpinBox(pagina)
        self.intervalo_no_laboral_entradas_spin.setRange(1, 1440)
        formulario.addRow(
            "Intervalo fuera de horario entradas (min)",
            self.intervalo_no_laboral_entradas_spin,
        )

        self.tabs.addTab(pagina, "Intervalos")

    def _crear_tab_filtro(self) -> None:
        pagina = QWidget(self)
        formulario = QFormLayout(pagina)

        descripcion = self._crear_label_descriptivo(
            "Determiná cómo se calcula la fecha de corte para expedientes. La vista "
            "previa muestra el resultado estimado según los valores actuales."
        )
        formulario.addRow(descripcion)

        self.filtro_modo_combo = QComboBox(pagina)
        opciones = [
            ("Sin corte explícito", "sin_corte"),
            ("Hoy", "hoy"),
            ("Último día hábil", "ultimo_dia_habil"),
            ("Días hacia atrás", "dias_atras"),
            ("Hoy + Último día hábil", "hoy+ultimo_dia_habil"),
            ("Completo", "completo"),
        ]
        for etiqueta, valor in opciones:
            self.filtro_modo_combo.addItem(etiqueta, valor)
        formulario.addRow("Modo de filtro", self.filtro_modo_combo)

        self.filtro_dias_spin = QSpinBox(pagina)
        self.filtro_dias_spin.setRange(0, 365)
        formulario.addRow("Días hacia atrás", self.filtro_dias_spin)

        self.filtro_orden_edit = QLineEdit(pagina)
        formulario.addRow("Orden de extracción", self.filtro_orden_edit)

        self.filtro_preview_label = QLabel("", pagina)
        self.filtro_preview_label.setWordWrap(True)
        self.filtro_preview_label.setStyleSheet("color: #555;")
        formulario.addRow("Vista previa", self.filtro_preview_label)

        self.tabs.addTab(pagina, "Filtro")

    def _crear_tab_reintentos(self) -> None:
        pagina = QWidget(self)
        formulario = QFormLayout(pagina)

        descripcion = self._crear_label_descriptivo(
            "Definí cuántos reintentos realiza el monitor y cuánto espera entre "
            "cada intento para expedientes y entradas."
        )
        formulario.addRow(descripcion)

        self.reintentos_expedientes_spin = QSpinBox(pagina)
        self.reintentos_expedientes_spin.setRange(0, 20)
        formulario.addRow(
            "Reintentos expedientes",
            self.reintentos_expedientes_spin,
        )

        self.espera_expedientes_spin = QSpinBox(pagina)
        self.espera_expedientes_spin.setRange(0, 3600)
        formulario.addRow(
            "Espera entre reintentos de expedientes (seg)",
            self.espera_expedientes_spin,
        )

        self.reintentos_entradas_spin = QSpinBox(pagina)
        self.reintentos_entradas_spin.setRange(0, 20)
        formulario.addRow("Reintentos entradas", self.reintentos_entradas_spin)

        self.espera_entradas_spin = QSpinBox(pagina)
        self.espera_entradas_spin.setRange(0, 3600)
        formulario.addRow(
            "Espera entre reintentos de entradas (seg)",
            self.espera_entradas_spin,
        )

        self.tabs.addTab(pagina, "Reintentos")

    def _crear_tab_respaldo(self) -> None:
        pagina = QWidget(self)
        formulario = QFormLayout(pagina)

        descripcion = self._crear_label_descriptivo(
            "Elegí dónde se guardarán los respaldos históricos y qué archivos se "
            "copiarán en cada ejecución."
        )
        formulario.addRow(descripcion)

        self.respaldo_destino_edit = QLineEdit(pagina)
        self.respaldo_destino_boton = QPushButton("Seleccionar…", pagina)
        self.respaldo_destino_boton.clicked.connect(self._seleccionar_respaldo)
        formulario.addRow(
            "Destino de respaldos",
            self._crear_contenedor_ruta(
                self.respaldo_destino_edit, self.respaldo_destino_boton
            ),
        )

        self.respaldo_archivos_edit = QPlainTextEdit(pagina)
        self.respaldo_archivos_edit.setPlaceholderText(
            "Un archivo por línea (por ejemplo: expedientes_monitor.json)"
        )
        formulario.addRow(QLabel("Archivos a respaldar"), self.respaldo_archivos_edit)

        self.tabs.addTab(pagina, "Respaldo")

    def _crear_tab_notificaciones(self) -> None:
        pagina = QWidget(self)
        layout = QVBoxLayout(pagina)

        descripcion = self._crear_label_descriptivo(
            "Activá o desactivá los avisos en la bandeja según tus necesidades."
        )
        layout.addWidget(descripcion)

        self.notif_respaldo_check = QCheckBox(
            "Mostrar notificaciones al completar un respaldo",
            pagina,
        )
        self.notif_comparacion_sin_cambios_check = QCheckBox(
            "Notificar comparaciones sin cambios",
            pagina,
        )
        self.notif_comparacion_faltantes_check = QCheckBox(
            "Notificar faltantes en la comparación",
            pagina,
        )

        layout.addWidget(self.notif_respaldo_check)
        layout.addWidget(self.notif_comparacion_sin_cambios_check)
        layout.addWidget(self.notif_comparacion_faltantes_check)
        layout.addStretch(1)

        self.tabs.addTab(pagina, "Notificaciones")

    def _crear_contenedor_ruta(
        self, edit: QLineEdit, boton: QPushButton
    ) -> QWidget:
        contenedor = QWidget(self)
        layout = QHBoxLayout(contenedor)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(edit)
        layout.addWidget(boton)
        return contenedor

    def _crear_label_descriptivo(self, texto: str) -> QLabel:
        etiqueta = QLabel(texto, self)
        etiqueta.setWordWrap(True)
        etiqueta.setStyleSheet("color: #555;")
        return etiqueta

    def _conectar_eventos(self) -> None:
        self.filtro_modo_combo.currentIndexChanged.connect(self._actualizar_preview_fecha)
        self.filtro_dias_spin.valueChanged.connect(self._actualizar_preview_fecha)
        self.filtro_orden_edit.textChanged.connect(self._actualizar_preview_fecha)
        self.comparacion_modo_combo.currentIndexChanged.connect(self._actualizar_preview_fecha)
        self.monitoreo_edit.editingFinished.connect(
            lambda: self._validar_ruta(self.monitoreo_edit, "carpeta de monitoreo")
        )
        self.respaldo_destino_edit.editingFinished.connect(
            lambda: self._validar_ruta(self.respaldo_destino_edit, "destino de respaldos")
        )

    def _cargar_datos(self) -> None:
        config = deepcopy(self._config)

        modo_actual = config.get("modo", DEFAULT_CONFIG["modo"])
        indice = self.modo_combo.findData(modo_actual)
        if indice >= 0:
            self.modo_combo.setCurrentIndex(indice)

        rutas = config.get("rutas", {})
        if isinstance(rutas, dict):
            self.monitoreo_edit.setText(str(rutas.get("monitoreo", "")))

        comparacion = config.get("comparacion", {})
        if isinstance(comparacion, dict):
            modo_comparacion = comparacion.get(
                "modo", DEFAULT_CONFIG["comparacion"]["modo"]
            )
            indice = self.comparacion_modo_combo.findData(modo_comparacion)
            if indice >= 0:
                self.comparacion_modo_combo.setCurrentIndex(indice)
            self.comparacion_auto_check.setChecked(
                bool(comparacion.get("auto", DEFAULT_CONFIG["comparacion"]["auto"]))
            )

        horario = config.get("horario_laboral", {})
        if not isinstance(horario, dict):
            horario = {}
        dias = horario.get("dias", DEFAULT_CONFIG["horario_laboral"]["dias"])
        seleccionados = {
            _normalizar_dia_semana(dia)
            for dia in dias
            if isinstance(dia, str) and dia
        }
        for _, normalizado, casilla in self.dias_laborales_checks:
            casilla.setChecked(normalizado in seleccionados)
        inicio = horario.get(
            "hora_inicio", DEFAULT_CONFIG["horario_laboral"]["hora_inicio"]
        )
        fin = horario.get("hora_fin", DEFAULT_CONFIG["horario_laboral"]["hora_fin"])
        self._set_time_edit(self.hora_inicio_edit, inicio)
        self._set_time_edit(self.hora_fin_edit, fin)
        intervalo_laboral = horario.get(
            "intervalo_minutos", DEFAULT_CONFIG["horario_laboral"]["intervalo_minutos"]
        )
        intervalo_laboral_entradas = horario.get(
            "intervalo_minutos_entradas",
            DEFAULT_CONFIG["horario_laboral"]["intervalo_minutos_entradas"],
        )
        self.intervalo_laboral_expedientes_spin.setValue(int(intervalo_laboral))
        self.intervalo_laboral_entradas_spin.setValue(
            int(intervalo_laboral_entradas)
        )

        fuera_horario = config.get("fuera_horario", {})
        if not isinstance(fuera_horario, dict):
            fuera_horario = {}
        intervalo_no_laboral = fuera_horario.get(
            "intervalo_minutos", DEFAULT_CONFIG["fuera_horario"]["intervalo_minutos"]
        )
        intervalo_no_laboral_entradas = fuera_horario.get(
            "intervalo_minutos_entradas",
            DEFAULT_CONFIG["fuera_horario"]["intervalo_minutos_entradas"],
        )
        self.intervalo_no_laboral_expedientes_spin.setValue(
            int(intervalo_no_laboral)
        )
        self.intervalo_no_laboral_entradas_spin.setValue(
            int(intervalo_no_laboral_entradas)
        )

        filtro = config.get("filtro_expedientes", {})
        if isinstance(filtro, dict):
            modo_filtro = filtro.get(
                "modo", DEFAULT_CONFIG["filtro_expedientes"]["modo"]
            )
            indice = self.filtro_modo_combo.findData(modo_filtro)
            if indice >= 0:
                self.filtro_modo_combo.setCurrentIndex(indice)
            self.filtro_dias_spin.setValue(
                int(filtro.get(
                    "dias_atras", DEFAULT_CONFIG["filtro_expedientes"]["dias_atras"]
                ))
            )
            orden = filtro.get(
                "orden", DEFAULT_CONFIG["filtro_expedientes"]["orden"]
            )
            if isinstance(orden, str):
                self.filtro_orden_edit.setText(orden)

        self._actualizar_preview_fecha()

        reintentos = config.get("reintentos", {})
        exp_conf = reintentos.get("expedientes", {})
        ent_conf = reintentos.get("entradas", {})
        self.reintentos_expedientes_spin.setValue(
            int(exp_conf.get("maximos", DEFAULT_CONFIG["reintentos"]["expedientes"]["maximos"]))
        )
        self.espera_expedientes_spin.setValue(
            int(
                exp_conf.get(
                    "espera_segundos",
                    DEFAULT_CONFIG["reintentos"]["expedientes"]["espera_segundos"],
                )
            )
        )
        self.reintentos_entradas_spin.setValue(
            int(ent_conf.get("maximos", DEFAULT_CONFIG["reintentos"]["entradas"]["maximos"]))
        )
        self.espera_entradas_spin.setValue(
            int(
                ent_conf.get(
                    "espera_segundos",
                    DEFAULT_CONFIG["reintentos"]["entradas"]["espera_segundos"],
                )
            )
        )

        respaldo = config.get("respaldo", {})
        if isinstance(respaldo, dict):
            destino = respaldo.get(
                "destino", DEFAULT_CONFIG["respaldo"]["destino"]
            )
            if isinstance(destino, str):
                self.respaldo_destino_edit.setText(destino)
            archivos = respaldo.get("archivos", [])
            if isinstance(archivos, (list, tuple)):
                texto = "\n".join(str(archivo) for archivo in archivos if archivo)
                self.respaldo_archivos_edit.setPlainText(texto)

        notificaciones = config.get("notificaciones", {})
        self.notif_respaldo_check.setChecked(
            bool(
                notificaciones.get(
                    "respaldo", DEFAULT_CONFIG["notificaciones"]["respaldo"]
                )
            )
        )
        self.notif_comparacion_sin_cambios_check.setChecked(
            bool(
                notificaciones.get(
                    "comparacion_sin_cambios",
                    DEFAULT_CONFIG["notificaciones"]["comparacion_sin_cambios"],
                )
            )
        )
        self.notif_comparacion_faltantes_check.setChecked(
            bool(
                notificaciones.get(
                    "comparacion_faltantes",
                    DEFAULT_CONFIG["notificaciones"]["comparacion_faltantes"],
                )
            )
        )

    def _set_time_edit(self, widget: QTimeEdit, valor: object) -> None:
        texto = valor if isinstance(valor, str) else ""
        hora = QTime.fromString(texto, "HH:mm")
        if not hora.isValid():
            defecto = QTime.fromString("07:00", "HH:mm")
            hora = defecto if defecto.isValid() else QTime(7, 0)
        widget.setTime(hora)

    def _seleccionar_monitoreo(self) -> None:
        inicio = self.monitoreo_edit.text().strip() or str(
            Path.cwd() / DEFAULT_CONFIG["rutas"]["monitoreo"]
        )
        ruta = QFileDialog.getExistingDirectory(
            self, "Seleccionar carpeta de monitoreo", inicio
        )
        if ruta:
            self.monitoreo_edit.setText(ruta)

    def _seleccionar_respaldo(self) -> None:
        inicio = self.respaldo_destino_edit.text().strip() or str(
            Path.cwd() / DEFAULT_CONFIG["respaldo"]["destino"]
        )
        ruta = QFileDialog.getExistingDirectory(
            self, "Seleccionar destino de respaldos", inicio
        )
        if ruta:
            self.respaldo_destino_edit.setText(ruta)

    def accept(self) -> None:  # type: ignore[override]
        try:
            config = self._recopilar_configuracion(validar=True)
        except ValueError as error:
            QMessageBox.warning(self, "Configuración inválida", str(error))
            return

        self._resultado = config
        super().accept()

    def _asegurar_dict(self, destino: dict, clave: str, default: dict) -> dict:
        existente = destino.get(clave)
        if not isinstance(existente, dict):
            existente = deepcopy(default)
            destino[clave] = existente
        return existente

    def _recopilar_configuracion(self, validar: bool = False) -> dict:
        config = deepcopy(self._config) if isinstance(self._config, dict) else {}
        if not isinstance(config, dict):  # defensa ante valores no mapeables
            config = {}

        config["modo"] = self.modo_combo.currentData() or DEFAULT_CONFIG["modo"]

        rutas = self._asegurar_dict(config, "rutas", DEFAULT_CONFIG["rutas"])
        monitoreo = self.monitoreo_edit.text().strip()
        rutas["monitoreo"] = monitoreo or DEFAULT_CONFIG["rutas"]["monitoreo"]

        comparacion = self._asegurar_dict(
            config, "comparacion", DEFAULT_CONFIG["comparacion"]
        )
        comparacion["modo"] = (
            self.comparacion_modo_combo.currentData()
            or DEFAULT_CONFIG["comparacion"]["modo"]
        )
        comparacion["auto"] = self.comparacion_auto_check.isChecked()

        horario = self._asegurar_dict(
            config, "horario_laboral", DEFAULT_CONFIG["horario_laboral"]
        )
        dias = [
            valor
            for valor, _, casilla in self.dias_laborales_checks
            if casilla.isChecked()
        ]
        horario["dias"] = dias or DEFAULT_CONFIG["horario_laboral"]["dias"]
        horario["hora_inicio"] = self.hora_inicio_edit.time().toString("HH:mm")
        horario["hora_fin"] = self.hora_fin_edit.time().toString("HH:mm")
        horario["intervalo_minutos"] = self.intervalo_laboral_expedientes_spin.value()
        horario["intervalo_minutos_entradas"] = (
            self.intervalo_laboral_entradas_spin.value()
        )

        fuera_horario = self._asegurar_dict(
            config, "fuera_horario", DEFAULT_CONFIG["fuera_horario"]
        )
        fuera_horario["intervalo_minutos"] = (
            self.intervalo_no_laboral_expedientes_spin.value()
        )
        fuera_horario["intervalo_minutos_entradas"] = (
            self.intervalo_no_laboral_entradas_spin.value()
        )

        filtro = self._asegurar_dict(
            config, "filtro_expedientes", DEFAULT_CONFIG["filtro_expedientes"]
        )
        filtro_modo = self.filtro_modo_combo.currentData()
        if filtro_modo == "sin_corte":
            filtro_modo = ""
        filtro["modo"] = filtro_modo or DEFAULT_CONFIG["filtro_expedientes"]["modo"]
        filtro["dias_atras"] = self.filtro_dias_spin.value()
        filtro["orden"] = self.filtro_orden_edit.text().strip() or DEFAULT_CONFIG["filtro_expedientes"]["orden"]

        reintentos = self._asegurar_dict(
            config, "reintentos", DEFAULT_CONFIG["reintentos"]
        )
        exp_conf = self._asegurar_dict(
            reintentos, "expedientes", DEFAULT_CONFIG["reintentos"]["expedientes"]
        )
        exp_conf["maximos"] = self.reintentos_expedientes_spin.value()
        exp_conf["espera_segundos"] = self.espera_expedientes_spin.value()
        ent_conf = self._asegurar_dict(
            reintentos, "entradas", DEFAULT_CONFIG["reintentos"]["entradas"]
        )
        ent_conf["maximos"] = self.reintentos_entradas_spin.value()
        ent_conf["espera_segundos"] = self.espera_entradas_spin.value()

        respaldo = self._asegurar_dict(config, "respaldo", DEFAULT_CONFIG["respaldo"])
        destino_respaldo = self.respaldo_destino_edit.text().strip()
        respaldo["destino"] = (
            destino_respaldo or DEFAULT_CONFIG["respaldo"]["destino"]
        )
        archivos_texto = self.respaldo_archivos_edit.toPlainText().splitlines()
        respaldo["archivos"] = [
            archivo.strip() for archivo in archivos_texto if archivo.strip()
        ]

        notificaciones = self._asegurar_dict(
            config, "notificaciones", DEFAULT_CONFIG["notificaciones"]
        )
        notificaciones["respaldo"] = self.notif_respaldo_check.isChecked()
        notificaciones[
            "comparacion_sin_cambios"
        ] = self.notif_comparacion_sin_cambios_check.isChecked()
        notificaciones[
            "comparacion_faltantes"
        ] = self.notif_comparacion_faltantes_check.isChecked()

        if validar:
            self._validar_configuracion(config)

        return config

    def obtener_configuracion(self) -> dict | None:
        return deepcopy(self._resultado) if isinstance(self._resultado, dict) else None

    def _validar_configuracion(self, config: dict) -> None:
        rutas = config.get("rutas", {})
        respaldo = config.get("respaldo", {})

        if isinstance(rutas, dict):
            ruta_monitoreo = Path(rutas.get("monitoreo", ""))
            if not ruta_monitoreo:
                raise ValueError("Definí una carpeta de monitoreo válida.")
            ruta_monitoreo.mkdir(parents=True, exist_ok=True)

        if isinstance(respaldo, dict):
            destino = Path(respaldo.get("destino", ""))
            if not destino:
                raise ValueError("Definí un destino de respaldos válido.")
            destino.mkdir(parents=True, exist_ok=True)

        horario = config.get("horario_laboral", {})
        if isinstance(horario, dict):
            dias = horario.get("dias")
            if not dias:
                raise ValueError("Seleccioná al menos un día laboral.")

    def _validar_ruta(self, edit: QLineEdit, descripcion: str) -> None:
        texto = edit.text().strip()
        if not texto:
            self._mostrar_estado(
                f"Se usará la ruta predeterminada para la {descripcion}.", "info"
            )
            return

        ruta = Path(texto)
        try:
            ruta.mkdir(parents=True, exist_ok=True)
        except Exception as error:  # pragma: no cover - validación visual
            self._mostrar_estado(
                f"No se pudo preparar la {descripcion}: {error}.", "error"
            )
        else:
            self._mostrar_estado(
                f"La {descripcion} está configurada en {ruta.resolve()}", "ok"
            )

    def _actualizar_preview_fecha(self) -> None:
        modo_comparacion = self.comparacion_modo_combo.currentData()
        modo_filtro = self.filtro_modo_combo.currentData()
        if modo_comparacion == MODO_COMPARACION_TOTAL:
            self.filtro_preview_label.setText(
                "La comparación total omite el corte temporal; la extracción "
                "recorrerá la base completa."
            )
            return

        if modo_filtro in ("sin_corte", "", None):
            self.filtro_preview_label.setText(
                "No se aplicará un corte temporal; se recorrerán todas las páginas disponibles."
            )
            return

        try:
            configuracion = self._recopilar_configuracion(validar=False)
        except ValueError:
            self.filtro_preview_label.setText(
                "La configuración actual no es válida para calcular la vista previa."
            )
            return

        try:
            fecha_iso = obtener_fecha_corte(configuracion)
        except Exception as error:  # pragma: no cover - entornos sin helper
            self.filtro_preview_label.setText(
                f"No fue posible calcular la fecha de corte: {error}."
            )
            return

        if not fecha_iso:
            self.filtro_preview_label.setText(
                "No se obtuvo una fecha de corte con la configuración actual."
            )
            return

        try:
            fecha = datetime.fromisoformat(str(fecha_iso))
        except ValueError:
            self.filtro_preview_label.setText(f"Fecha obtenida: {fecha_iso}.")
            return

        self.filtro_preview_label.setText(
            "La extracción se detendrá al alcanzar el {:%d/%m/%Y}.".format(fecha)
        )

    def _restaurar_defaults(self) -> None:
        self._config = deepcopy(DEFAULT_CONFIG)
        self._cargar_datos()
        self._mostrar_estado(
            "Se restauraron los valores predeterminados del monitor.", "info"
        )

    def _mostrar_estado(self, mensaje: str, tipo: str = "info") -> None:
        colores = {"info": "#555", "ok": "#2e7d32", "error": "#b71c1c"}
        self.estado_label.setStyleSheet(f"color: {colores.get(tipo, '#555')};")
        self.estado_label.setText(mensaje)
class VerificadorExpedientesV4(QThread):
    """Hilo encargado de recuperar el listado completo de expedientes."""

    resultado = Signal(object)

    def __init__(
        self,
        carpeta_salida: str | Path = "datos_extraidos/monitoreo",
        nombre_archivo: str = "expedientes_monitor.json",
        guardar_json: bool = True,
        *,
        fecha_corte: str | None = None,
        orden: str | None = "fecha",
    ) -> None:
        super().__init__()
        self.carpeta_salida = Path(carpeta_salida)
        self.nombre_archivo = nombre_archivo
        self.guardar_json = guardar_json
        self.fecha_corte = fecha_corte
        self.orden = orden

    def run(self) -> None:  # type: ignore[override]
        import asyncio

        asyncio.run(self._verificar_async())

    async def _verificar_async(self) -> None:
        try:
            async with reutilizar_sesion_async() as (page, _context, _browser):
                if not page:
                    self.resultado.emit(ResultadoExpedientes(estado="fallo"))
                    return

                await page.goto(URL_CONSULTAS)
                (
                    expedientes,
                    motivo,
                    metadata,
                ) = await extraer_expedientes_completos(
                    page,
                    orden=self.orden,
                    detener_en_duplicado=False,
                    fecha_corte=self.fecha_corte,
                )

                total_esperado = None
                duplicados_descartados = 0
                filas_descartadas = 0
                paginas_recorridas = None
                paginas_esperadas = None
                if isinstance(metadata, dict):
                    total_meta = metadata.get("total_esperado")
                    if isinstance(total_meta, int):
                        total_esperado = total_meta
                    duplicados_meta = metadata.get("duplicados_descartados")
                    if isinstance(duplicados_meta, int):
                        duplicados_descartados = max(0, duplicados_meta)
                    filas_meta = metadata.get("filas_descartadas")
                    if isinstance(filas_meta, int):
                        filas_descartadas = max(0, filas_meta)
                    paginas_meta = metadata.get("paginas_recorridas")
                    if isinstance(paginas_meta, int):
                        paginas_recorridas = max(0, paginas_meta)
                    paginas_esp_meta = metadata.get("paginas_esperadas")
                    if isinstance(paginas_esp_meta, int):
                        paginas_esperadas = max(0, paginas_esp_meta)

                motivo_original = motivo
                motivos_corte_controlado = {
                    "limite_fecha",
                    "limite_tiempo",
                    "limite_paginas",
                    "duplicado_encontrado",
                    "bucle_detectado",
                    "sin_siguiente_habilitado",
                }
                extraccion_detencion_controlada = (
                    motivo_original in motivos_corte_controlado
                    or self.fecha_corte is not None
                )
                cantidad = len(expedientes)
                if total_esperado is not None:
                    registrar_log(
                        f"📈 Total anunciado por el portal: {total_esperado} expedientes"
                    )

                registrar_log(
                    "🧹 Filas descartadas durante la extracción: "
                    f"{duplicados_descartados} duplicadas / {filas_descartadas} inválidas."
                )

                if paginas_recorridas is not None:
                    esperado_log = (
                        str(paginas_esperadas)
                        if paginas_esperadas is not None
                        else "?"
                    )
                    registrar_log(
                        f"📄 Paginación: {paginas_recorridas} / {esperado_log}"
                    )

                if total_esperado is not None:
                    if total_esperado > cantidad:
                        total_descartado = duplicados_descartados + filas_descartadas
                        diferencia = total_esperado - cantidad
                        if total_esperado == cantidad + total_descartado:
                            detalle_descartes = []
                            if duplicados_descartados:
                                detalle_descartes.append(
                                    f"{duplicados_descartados} duplicadas"
                                )
                            if filas_descartadas:
                                detalle_descartes.append(
                                    f"{filas_descartadas} inválidas"
                                )
                            detalle = ", ".join(detalle_descartes) or "sin descartes registrados"
                            registrar_log(
                                "⚠️ El portal informó más expedientes de los que se "
                                "guardaron, pero la diferencia se explicó por "
                                f"{detalle} (total descartado: {total_descartado}; "
                                f"diferencia informada: {diferencia})."
                            )
                        elif extraccion_detencion_controlada:
                            if motivo_original == "limite_fecha" and self.fecha_corte:
                                registrar_log(
                                    "ℹ️ La extracción finalizó por la fecha de corte "
                                    f"{self.fecha_corte}; es esperable obtener menos "
                                    "expedientes que el total anunciado."
                                )
                            else:
                                registrar_log(
                                    "ℹ️ La extracción se detuvo de forma controlada "
                                    "antes de alcanzar el total anunciado; se omitirá "
                                    "el ajuste por diferencia."
                                )
                        else:
                            registrar_log(
                                "⚠️ La cantidad recopilada es menor al total anunciado "
                                f"por {diferencia} expedientes."
                            )
                            if total_descartado:
                                registrar_log(
                                    "🧮 Descartes registrados: "
                                    f"{duplicados_descartados} duplicadas / "
                                    f"{filas_descartadas} inválidas (total "
                                    f"{total_descartado})."
                                )
                            motivo = "total_incompleto"
                elif total_esperado < cantidad:
                    registrar_log(
                        "ℹ️ Se extrajeron más expedientes que los anunciados."
                    )

                if (
                    paginas_recorridas is not None
                    and paginas_esperadas is not None
                    and paginas_recorridas < paginas_esperadas
                ):
                    if extraccion_detencion_controlada:
                        registrar_log(
                            "ℹ️ La extracción se detuvo antes de recorrer todas las páginas "
                            "debido al límite configurado."
                        )
                    else:
                        registrar_log(
                            "⚠️ No se alcanzó la cantidad de páginas anunciadas por el portal."
                        )
                        motivo = "paginas_incompletas"

                ruta_archivo: Path | None = None
                if self.guardar_json:
                    ruta_archivo = self._guardar_resultados(expedientes)

                motivos_exitosos = {
                    "fin_listado": "completo",
                    "limite_fecha": "corte_controlado",
                    "limite_tiempo": "corte_controlado",
                    "limite_paginas": "corte_controlado",
                    "duplicado_encontrado": "corte_controlado",
                    "bucle_detectado": "corte_controlado",
                    "sin_siguiente": "completo",
                    "sin_siguiente_habilitado": "corte_controlado",
                    "paginas_incompletas": "total_incompleto",
                }
                estado_normalizado = motivos_exitosos.get(motivo, motivo)

                self.resultado.emit(
                    ResultadoExpedientes(
                        estado=estado_normalizado,
                        cantidad=len(expedientes),
                        total_esperado=total_esperado,
                        ruta=str(ruta_archivo) if ruta_archivo else None,
                        motivo=motivo,
                        motivo_original=(
                            motivo_original if motivo != motivo_original else None
                        ),
                        duplicados_descartados=duplicados_descartados,
                        filas_descartadas=filas_descartadas,
                        paginas_recorridas=paginas_recorridas,
                        paginas_esperadas=paginas_esperadas,
                    )
                )
        except Exception as exc:  # pragma: no cover - logging de errores
            registrar_log(f"❌ Error crítico en hilo de expedientes: {exc}")
            self.resultado.emit(
                ResultadoExpedientes(estado="fallo", error=str(exc))
            )

    def _guardar_resultados(self, expedientes: list[dict]) -> Path:
        self.carpeta_salida.mkdir(parents=True, exist_ok=True)
        ruta = self.carpeta_salida / self.nombre_archivo
        with ruta.open("w", encoding="utf-8") as archivo:
            json.dump(expedientes, archivo, ensure_ascii=False, indent=2)
        return ruta


class VerificadorEntradasV4(QThread):
    """Hilo encargado de recuperar las entradas del portal del PJN."""

    resultado = Signal(object)

    def __init__(self, destino: Path | str) -> None:
        super().__init__()
        self.destino = Path(destino)

    def run(self) -> None:  # type: ignore[override]
        import asyncio

        asyncio.run(self._verificar_async())

    async def _verificar_async(self) -> None:
        base_dir = self.destino
        base_dir.mkdir(parents=True, exist_ok=True)
        historial_json = base_dir / "historial_notificaciones.json"
        historial_csv = base_dir / "historial_notificaciones.csv"

        try:
            async with reutilizar_sesion_async() as (page, _context, _browser):
                if not page:
                    self.resultado.emit(
                        ResultadoEntradas(
                            nuevas=None,
                            base_dir=base_dir,
                            historial_json=historial_json,
                            historial_csv=historial_csv,
                            error="sesion_no_disponible",
                        )
                    )
                    return

                nuevas = await extraer_entradas_pjn(page, destino=str(base_dir))
                self.resultado.emit(
                    ResultadoEntradas(
                        nuevas=nuevas,
                        base_dir=base_dir,
                        historial_json=historial_json,
                        historial_csv=historial_csv,
                    )
                )
        except Exception as exc:  # pragma: no cover - logging de errores
            registrar_log(f"❌ Error en verificación de entradas: {exc}")
            self.resultado.emit(
                ResultadoEntradas(
                    nuevas=None,
                    base_dir=base_dir,
                    historial_json=historial_json,
                    historial_csv=historial_csv,
                    error=str(exc),
                )
            )


class MonitorExpedientesTray:
    """Crea un icono en la bandeja del sistema para monitorear expedientes."""

    def __init__(self) -> None:
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        if not QSystemTrayIcon.isSystemTrayAvailable():
            registrar_log("❌ La bandeja del sistema no está disponible. La aplicación se cerrará.")
            QMessageBox.critical(None, "Error", "La bandeja del sistema no está disponible.")
            sys.exit(1)

        self.tray = QSystemTrayIcon(self._crear_icono())
        self.tray.setToolTip("Monitor de Expedientes y Entradas PJN")
        self.tray.setVisible(True)

        self.menu = QMenu()
        self.menu.addAction("📥 Verificar expedientes").triggered.connect(
            self.verificar_expedientes
        )

        self.menu.addAction("📤 Verificar entradas").triggered.connect(
            self.verificar_entradas
        )

        self.accion_comparar = self.menu.addAction("🧪 Comparar expedientes")
        self.accion_comparar.triggered.connect(self.comparar_expedientes_manual)
        if comparar_expedientes is None:
            self.accion_comparar.setEnabled(False)
            self.accion_comparar.setToolTip(
                "Instala comparacion_expedientes.py para habilitar esta función."
            )

        self.submenu_modo = QMenu("🛠️ Modo de trabajo")
        self.acciones_modo: dict[str, QAction] = {}
        for modo in MODOS_VALIDOS:
            texto = modo.replace("_", " ").capitalize()
            accion = QAction(texto, checkable=True)
            accion.triggered.connect(
                lambda checked, valor=modo: self._manejar_cambio_modo(valor, checked)
            )
            self.submenu_modo.addAction(accion)
            self.acciones_modo[modo] = accion
        self.menu.addMenu(self.submenu_modo)

        self.submenu_utilidades = QMenu("🧰 Utilidades")
        accion_estado = self.submenu_utilidades.addAction("🔐 Estado de sesión")
        accion_estado.triggered.connect(self.mostrar_estado_sesion)
        accion_forzar = self.submenu_utilidades.addAction("⚠️ Forzar nuevo login")
        accion_forzar.triggered.connect(self.forzar_login)
        accion_respaldo = self.submenu_utilidades.addAction(
            "🗄️ Respaldar últimos resultados"
        )
        accion_respaldo.triggered.connect(self.respaldar_resultados)
        self.submenu_utilidades.addSeparator()
        placeholder = QAction("Más herramientas próximamente")
        placeholder.setEnabled(False)
        self.submenu_utilidades.addAction(placeholder)
        self.menu.addMenu(self.submenu_utilidades)

        accion_configuracion = self.menu.addAction("⚙️ Configuración…")
        accion_configuracion.triggered.connect(self.abrir_configuracion)

        self.menu.addSeparator()
        self.menu.addAction("🛑 Salir").triggered.connect(self.salir)
        self.tray.setContextMenu(self.menu)

        self.directorio_monitoreo = (
            Path(os.getcwd()) / DEFAULT_CONFIG["rutas"]["monitoreo"]
        ).resolve()
        self.reintentos_config: dict[str, dict[str, int]] = deepcopy(
            DEFAULT_CONFIG["reintentos"]
        )
        self.notificaciones_config: dict[str, bool] = deepcopy(
            DEFAULT_CONFIG["notificaciones"]
        )
        self.comparacion_auto: bool = DEFAULT_CONFIG["comparacion"]["auto"]

        self.config = self.cargar_config()
        self._aplicar_configuracion(self.config)
        self.actualizar_modo_seleccionado()
        self.actualizar_tooltip()
        self.hilo_expedientes: VerificadorExpedientesV4 | None = None
        self.hilo_entradas: VerificadorEntradasV4 | None = None
        self.ejecutando_expedientes = False
        self.ejecutando_entradas = False
        self.reintentos_expedientes = 0
        self.reintentos_entradas = 0

        self.timer_expedientes = QTimer()
        self.timer_expedientes.timeout.connect(self.verificar_expedientes)

        self.timer_entradas = QTimer()
        self.timer_entradas.timeout.connect(self.verificar_entradas)

        self.iniciar_temporizador()
        sys.exit(self.app.exec())

    @staticmethod
    def _crear_icono() -> QIcon:
        pixmap = QPixmap()
        if not pixmap.loadFromData(base64.b64decode(ICONO_BASE64)):
            registrar_log("⚠️ Icono incrustado inválido, usando icono por defecto")
            return QIcon()
        return QIcon(pixmap)

    def cargar_config(self) -> dict:
        return cargar_config_monitor()

    def _aplicar_configuracion(self, config: dict) -> None:
        self.directorio_monitoreo = self._resolver_directorio_monitoreo(config)
        self.reintentos_config = self._resolver_reintentos(config)
        self.notificaciones_config = self._resolver_notificaciones(config)

        comparacion = config.get("comparacion")
        if isinstance(comparacion, dict):
            self.comparacion_auto = bool(
                comparacion.get("auto", DEFAULT_CONFIG["comparacion"]["auto"])
            )
        else:
            self.comparacion_auto = DEFAULT_CONFIG["comparacion"]["auto"]

    def _resolver_directorio_monitoreo(self, config: dict) -> Path:
        rutas = config.get("rutas")
        if isinstance(rutas, dict):
            destino = rutas.get("monitoreo")
            if isinstance(destino, str) and destino.strip():
                ruta = Path(destino).expanduser()
                if not ruta.is_absolute():
                    return (Path(os.getcwd()) / destino).resolve()
                return ruta.resolve()

        por_defecto = DEFAULT_CONFIG["rutas"]["monitoreo"]
        ruta = Path(por_defecto).expanduser()
        if ruta.is_absolute():
            return ruta.resolve()
        return (Path(os.getcwd()) / ruta).resolve()

    def _resolver_reintentos(self, config: dict) -> dict[str, dict[str, int]]:
        resultado = deepcopy(DEFAULT_CONFIG["reintentos"])
        reintentos = config.get("reintentos")
        if not isinstance(reintentos, dict):
            return resultado

        for clave in ("expedientes", "entradas"):
            valores = reintentos.get(clave)
            if not isinstance(valores, dict):
                continue
            maximos = valores.get("maximos")
            espera = valores.get("espera_segundos")
            if isinstance(maximos, (int, float)):
                resultado[clave]["maximos"] = max(0, int(maximos))
            if isinstance(espera, (int, float)):
                resultado[clave]["espera_segundos"] = max(0, int(espera))
        return resultado

    def _resolver_notificaciones(self, config: dict) -> dict[str, bool]:
        resultado = deepcopy(DEFAULT_CONFIG["notificaciones"])
        notificaciones = config.get("notificaciones")
        if not isinstance(notificaciones, dict):
            return resultado

        for clave in resultado:
            valor = notificaciones.get(clave)
            if isinstance(valor, bool):
                resultado[clave] = valor
        return resultado

    def _obtener_config_reintentos(self, tipo: str) -> tuple[int, int]:
        configuracion = self.reintentos_config.get(tipo, {})
        maximos = int(configuracion.get("maximos", 0))
        espera = int(configuracion.get("espera_segundos", 0))
        return maximos, espera

    def _should_notify(self, clave: str, default: bool) -> bool:
        valor = self.notificaciones_config.get(clave)
        if isinstance(valor, bool):
            return valor
        return default

    def _resolver_intervalo_config(self, bloque: str, tipo: str) -> int:
        configuracion = self.config.get(bloque)
        if not isinstance(configuracion, dict):
            configuracion = {}

        base = DEFAULT_CONFIG.get(bloque, {})
        if not isinstance(base, dict):
            base = {}

        clave_especifica = (
            "intervalo_minutos_entradas" if tipo == "entradas" else "intervalo_minutos"
        )
        candidatos = [
            configuracion.get(clave_especifica),
            configuracion.get("intervalo_minutos"),
            base.get(clave_especifica),
            base.get("intervalo_minutos"),
        ]

        for candidato in candidatos:
            if isinstance(candidato, (int, float)):
                valor = int(candidato)
                return max(1, valor)

        return 60

    def esta_en_horario_laboral(self) -> bool:
        ahora = datetime.now()
        dia_actual = _normalizar_dia_semana(ahora.strftime("%A"))

        horario = self.config.get("horario_laboral")
        if not isinstance(horario, dict):
            horario = DEFAULT_CONFIG["horario_laboral"]

        dias_config = horario.get("dias", DEFAULT_CONFIG["horario_laboral"]["dias"])
        if not isinstance(dias_config, (list, tuple, set)):
            dias_config = DEFAULT_CONFIG["horario_laboral"]["dias"]
        dias_normalizados: set[str] = set()
        for dia in dias_config:
            normalizado = _normalizar_dia_semana(dia)
            if normalizado:
                dias_normalizados.add(normalizado)

        hora_inicio_texto = horario.get(
            "hora_inicio", DEFAULT_CONFIG["horario_laboral"]["hora_inicio"]
        )
        hora_fin_texto = horario.get(
            "hora_fin", DEFAULT_CONFIG["horario_laboral"]["hora_fin"]
        )

        hora_inicio = datetime.strptime(hora_inicio_texto, "%H:%M").time()
        hora_fin = datetime.strptime(hora_fin_texto, "%H:%M").time()
        return dia_actual in dias_normalizados and hora_inicio <= ahora.time() <= hora_fin

    def obtener_intervalo(self, tipo: str = "expedientes") -> int:
        modo = self.config.get("modo", "automatico")
        if modo == "laboral":
            return self._resolver_intervalo_config("horario_laboral", tipo)
        if modo == "no_laboral":
            return self._resolver_intervalo_config("fuera_horario", tipo)
        if modo == "automatico":
            bloque = "horario_laboral" if self.esta_en_horario_laboral() else "fuera_horario"
            return self._resolver_intervalo_config(bloque, tipo)
        return self._resolver_intervalo_config("fuera_horario", tipo)

    def iniciar_temporizador(self) -> None:
        intervalo_expedientes = self.obtener_intervalo("expedientes")
        intervalo_entradas = self.obtener_intervalo("entradas")
        self.timer_expedientes.start(intervalo_expedientes * 60 * 1000)
        self.timer_entradas.start(intervalo_entradas * 60 * 1000)
        self.verificar_expedientes()
        self.verificar_entradas()

    def reiniciar_temporizadores(self) -> None:
        self.timer_expedientes.stop()
        self.timer_entradas.stop()
        self.iniciar_temporizador()

    def actualizar_tooltip(self) -> None:
        modo = self.config.get("modo", "automatico").replace("_", " ").capitalize()
        intervalo_expedientes = self.obtener_intervalo("expedientes")
        intervalo_entradas = self.obtener_intervalo("entradas")
        tooltip = (
            "Monitor de Expedientes y Entradas PJN\n"
            f"Modo: {modo} · Intervalos: {intervalo_expedientes} min (expedientes) / "
            f"{intervalo_entradas} min (entradas)"
        )
        self.tray.setToolTip(tooltip)

    def actualizar_modo_seleccionado(self) -> None:
        modo_actual = self.config.get("modo", "automatico")
        for modo, accion in self.acciones_modo.items():
            accion.blockSignals(True)
            accion.setChecked(modo == modo_actual)
            accion.blockSignals(False)

    def _manejar_cambio_modo(self, modo: str, checked: bool) -> None:
        if not checked:
            return
        self.cambiar_modo(modo)

    def cambiar_modo(self, nuevo_modo: str) -> None:
        if nuevo_modo == self.config.get("modo"):
            registrar_log("ℹ️ El modo seleccionado ya está activo.")
            return
        try:
            self.config = actualizar_modo_monitor(nuevo_modo)
        except ValueError as error:
            registrar_log(f"❌ No se pudo actualizar el modo: {error}")
            self.actualizar_modo_seleccionado()
            return

        self._aplicar_configuracion(self.config)
        self.actualizar_modo_seleccionado()
        self.actualizar_tooltip()
        self.reiniciar_temporizadores()

        modo_legible = nuevo_modo.replace("_", " ").capitalize()
        intervalo_expedientes = self.obtener_intervalo("expedientes")
        intervalo_entradas = self.obtener_intervalo("entradas")
        registrar_log(
            "⚙️ Modo de trabajo actualizado a "
            f"{modo_legible} (expedientes {intervalo_expedientes} min, "
            f"entradas {intervalo_entradas} min)."
        )
        self.tray.showMessage(
            "Modo de trabajo actualizado",
            (
                f"{modo_legible} · Expedientes: {intervalo_expedientes} min · "
                f"Entradas: {intervalo_entradas} min"
            ),
        )

    def verificar_expedientes(self) -> None:
        if self.ejecutando_expedientes:
            registrar_log("⏳ Verificación de expedientes ya en curso.")
            return

        self.ejecutando_expedientes = True
        carpeta = self.directorio_monitoreo
        fecha_corte_resuelta: str | None = None

        comparacion_config = self.config.get("comparacion")
        modo_comparacion = None
        if isinstance(comparacion_config, dict):
            valor = comparacion_config.get("modo")
            if isinstance(valor, str):
                modo_comparacion = valor.strip().lower()

        omitir_fecha_corte = modo_comparacion == MODO_COMPARACION_TOTAL
        if omitir_fecha_corte:
            registrar_log(
                "📊 Comparación configurada en modo total: se omitirá la fecha de corte "
                "durante la extracción."
            )
        else:
            try:
                fecha_corte_iso = obtener_fecha_corte(self.config)
            except ImportError:
                registrar_log(
                    "⚠️ No se pudo resolver la fecha de corte: helper heredado no disponible."
                )
            except Exception as exc:  # pragma: no cover - logging defensivo
                registrar_log(f"⚠️ Error al resolver fecha de corte: {exc}")
            else:
                if fecha_corte_iso:
                    try:
                        fecha_corte_resuelta = datetime.strptime(
                            fecha_corte_iso, "%Y-%m-%d"
                        ).strftime("%d/%m/%Y")
                    except ValueError as exc:
                        registrar_log(
                            "⚠️ Fecha de corte inválida en configuración: "
                            f"{fecha_corte_iso} → {exc}"
                        )
                    else:
                        registrar_log(
                            "📆 Fecha de corte aplicada para la extracción: "
                            f"{fecha_corte_resuelta}"
                        )

        filtro_config = self.config.get("filtro_expedientes", {})
        orden_config = filtro_config.get("orden", "fecha") if filtro_config else "fecha"
        if isinstance(orden_config, str):
            orden_filtrado = orden_config.strip() or "fecha"
        else:
            orden_filtrado = "fecha"

        self.hilo_expedientes = VerificadorExpedientesV4(
            carpeta_salida=carpeta,
            fecha_corte=fecha_corte_resuelta,
            orden=orden_filtrado,
        )
        self.hilo_expedientes.resultado.connect(self.procesar_resultado_expedientes)
        self.hilo_expedientes.finished.connect(self._limpiar_hilo_expedientes)
        self.hilo_expedientes.start()

    def _limpiar_hilo_expedientes(self) -> None:
        if self.hilo_expedientes:
            self.hilo_expedientes.deleteLater()
            self.hilo_expedientes = None
        self.ejecutando_expedientes = False

    def verificar_entradas(self) -> None:
        if self.ejecutando_entradas:
            registrar_log("⏳ Verificación de entradas ya en curso.")
            return

        self.ejecutando_entradas = True
        carpeta = self.directorio_monitoreo
        self.hilo_entradas = VerificadorEntradasV4(destino=carpeta)
        self.hilo_entradas.resultado.connect(self.procesar_resultado_entradas)
        self.hilo_entradas.finished.connect(self._limpiar_hilo_entradas)
        self.hilo_entradas.start()

    def _limpiar_hilo_entradas(self) -> None:
        if self.hilo_entradas:
            self.hilo_entradas.deleteLater()
            self.hilo_entradas = None
        self.ejecutando_entradas = False

    def procesar_resultado_expedientes(self, datos: ResultadoExpedientes) -> None:
        mensajes = {
            "completo": "✅ Extracción finalizada exitosamente.",
            "corte_controlado": "✅ Extracción detenida de forma controlada.",
            "fallo": "❌ Fallo en la verificación.",
            "total_incompleto": "⚠️ Resultados incompletos respecto al total anunciado.",
        }

        mensajes_motivo = {
            "limite_fecha": "📅 Se alcanzó la fecha límite configurada.",
            "limite_tiempo": "⏱️ Se cumplió el tiempo máximo de extracción permitido.",
            "limite_paginas": "📄 Se alcanzó el tope de páginas configurado para la búsqueda.",
            "duplicado_encontrado": "📎 Se detuvo la extracción al detectar un expediente duplicado (solo si se fuerza detener_en_duplicado=True).",
            "bucle_detectado": "🌀 Se detectó un posible bucle de navegación y la extracción se detuvo de forma segura.",
            "sin_siguiente": "ℹ️ No se detectó un botón 'Siguiente'; se asumió el final del listado.",
            "sin_siguiente_habilitado": "ℹ️ El botón 'Siguiente' estaba deshabilitado, por lo que se consideró finalizado el listado.",
            "total_incompleto": "⚠️ Los registros obtenidos no alcanzaron el total informado por el portal.",
            "paginas_incompletas": "⚠️ No se recorrieron todas las páginas anunciadas por el portal; se reintentará la extracción.",
        }

        registrar_log(f"📦 Estado: {datos.estado}")
        mensaje_estado = mensajes.get(datos.estado, "❓ Estado no reconocido.")
        registrar_log(mensaje_estado)

        duplicados_descartados = datos.duplicados_descartados or 0
        filas_descartadas = datos.filas_descartadas or 0
        registrar_log(
            "🧾 Descartes reportados: "
            f"{duplicados_descartados} duplicadas / {filas_descartadas} inválidas."
        )

        if datos.motivo:
            mensaje_motivo = mensajes_motivo.get(datos.motivo)
            if mensaje_motivo:
                registrar_log(mensaje_motivo)
            else:
                registrar_log(f"ℹ️ Motivo recibido: {datos.motivo}")
        if datos.motivo_original:
            registrar_log(f"ℹ️ Motivo original reportado: {datos.motivo_original}")

        paginas_recorridas = datos.paginas_recorridas
        paginas_esperadas = datos.paginas_esperadas
        if paginas_recorridas is not None:
            esperado_log = (
                str(paginas_esperadas)
                if paginas_esperadas is not None
                else "?"
            )
            registrar_log(f"📄 Paginación reportada: {paginas_recorridas} / {esperado_log}")

        if datos.cantidad is not None:
            if datos.total_esperado is not None:
                registrar_log(
                    f"📊 Expedientes recopilados: {datos.cantidad} / {datos.total_esperado} esperados"
                )
            else:
                registrar_log(f"📊 Total extraídos: {datos.cantidad}")

            if datos.total_esperado is not None:
                mensaje_total = (
                    f"{datos.cantidad} de {datos.total_esperado} expedientes actualizados."
                )
            else:
                mensaje_total = f"{datos.cantidad} expedientes actualizados."

            mensaje_total += (
                " Descartados: "
                f"{duplicados_descartados} duplicadas / {filas_descartadas} inválidas."
            )

            if paginas_recorridas is not None:
                esperado_mensaje = (
                    str(paginas_esperadas)
                    if paginas_esperadas is not None
                    else "?"
                )
                mensaje_total += (
                    f" Paginación: {paginas_recorridas} / {esperado_mensaje}."
                )
                if (
                    paginas_esperadas is not None
                    and paginas_recorridas < paginas_esperadas
                ):
                    if datos.estado == "corte_controlado":
                        mensaje_total += (
                            " La extracción se detuvo por el límite configurado antes de "
                            "recorrer todas las páginas."
                        )
                    else:
                        mensaje_total += (
                            " Se detectaron páginas pendientes; se reintentará la extracción."
                        )

            icono = (
                QSystemTrayIcon.Warning
                if datos.estado == "total_incompleto"
                else QSystemTrayIcon.Information
            )
            self.tray.showMessage(
                "📥 Expedientes",
                mensaje_total,
                icono,
            )
        if datos.ruta:
            registrar_log(f"📁 Guardado en: {datos.ruta}")
        if datos.error:
            registrar_log(f"🛑 Error: {datos.error}")

        estados_exitosos = {"completo", "corte_controlado"}

        if datos.estado not in estados_exitosos:
            self.reintentos_expedientes += 1
            max_reintentos, espera_segundos = self._obtener_config_reintentos(
                "expedientes"
            )
            if max_reintentos <= 0:
                registrar_log(
                    "ℹ️ Reintentos de expedientes desactivados en la configuración."
                )
            elif self.reintentos_expedientes <= max_reintentos:
                registrar_log(
                    "🔁 Reintentando verificación (%s/%s) en %s segundo(s)..."
                    % (
                        self.reintentos_expedientes,
                        max_reintentos,
                        espera_segundos,
                    )
                )
                QTimer.singleShot(
                    max(0, espera_segundos) * 1000, self.verificar_expedientes
                )
            else:
                registrar_log(
                    "❌ Se alcanzó el límite de reintentos configurado para expedientes."
                )
        else:
            self.reintentos_expedientes = 0
            if self.comparacion_auto:
                self._comparar_expedientes(
                    origen="automática",
                    notificar=True,
                    notificar_sin_cambios=self._should_notify(
                        "comparacion_sin_cambios", False
                    ),
                    notificar_faltantes=self._should_notify(
                        "comparacion_faltantes", True
                    ),
                )
            else:
                registrar_log(
                    "ℹ️ Comparación automática desactivada; no se ejecutará tras la verificación."
                )

    def procesar_resultado_entradas(self, datos: ResultadoEntradas) -> None:
        if datos.nuevas is None:
            self.reintentos_entradas += 1
            registrar_log("❌ No se pudieron verificar las entradas.")
            if datos.error == "sesion_no_disponible":
                registrar_log("ℹ️ Sesión no disponible al intentar extraer entradas.")
            elif datos.error:
                registrar_log(f"🛑 Error reportado: {datos.error}")
            max_reintentos, espera_segundos = self._obtener_config_reintentos(
                "entradas"
            )
            if max_reintentos <= 0:
                registrar_log(
                    "ℹ️ Reintentos de entradas desactivados en la configuración."
                )
            elif self.reintentos_entradas <= max_reintentos:
                registrar_log(
                    "🔁 Reintentando entradas (%s/%s) en %s segundo(s)..."
                    % (
                        self.reintentos_entradas,
                        max_reintentos,
                        espera_segundos,
                    )
                )
                QTimer.singleShot(
                    max(0, espera_segundos) * 1000, self.verificar_entradas
                )
            else:
                registrar_log("❌ Se alcanzó el límite de reintentos de entradas configurado.")
            self.tray.showMessage(
                "📤 Entradas",
                "No fue posible completar la extracción de entradas.",
                QSystemTrayIcon.Critical,
            )
            return

        self.reintentos_entradas = 0
        nuevas = datos.nuevas

        if nuevas > 0:
            mensaje = f"{nuevas} nuevas entradas registradas."
            icono = QSystemTrayIcon.Information
        else:
            mensaje = "Sin nuevas entradas detectadas."
            icono = QSystemTrayIcon.Information

        registrar_log(f"📤 Resultado entradas: {mensaje}")
        if datos.base_dir:
            registrar_log(f"📁 Carpeta de monitoreo: {datos.base_dir}")
        if datos.historial_json:
            registrar_log(f"📄 Historial JSON: {datos.historial_json}")
        if datos.historial_csv:
            registrar_log(f"📄 Historial CSV: {datos.historial_csv}")

        self.tray.showMessage("📤 Entradas", mensaje, icono)

    def respaldar_resultados(self) -> None:
        base_monitoreo = self.directorio_monitoreo
        configuracion_respaldo = self.config.get("respaldo", {})
        destino_config = None
        archivos_config = None

        if isinstance(configuracion_respaldo, dict):
            destino_config = configuracion_respaldo.get("destino")
            archivos_config = configuracion_respaldo.get("archivos")

        destino_texto = (
            destino_config
            if isinstance(destino_config, str) and destino_config.strip()
            else DEFAULT_CONFIG["respaldo"]["destino"]
        )
        destino_base = Path(destino_texto).expanduser()
        if not destino_base.is_absolute():
            destino_base = (Path(os.getcwd()) / destino_texto).resolve()
        else:
            destino_base = destino_base.resolve()
        archivos = None
        if isinstance(archivos_config, (list, tuple)):
            archivos = [str(archivo) for archivo in archivos_config]

        try:
            resultado = generar_respaldo_monitoreo(
                origen=base_monitoreo,
                destino_base=destino_base,
                archivos=archivos,
            )
        except Exception as error:  # pragma: no cover - logging y notificaciones
            registrar_log(f"❌ Error al generar el respaldo histórico: {error}")
            self.tray.showMessage(
                "🗄️ Respaldo histórico",
                "No fue posible completar el respaldo. Revisa el log para más detalles.",
                QSystemTrayIcon.Critical,
            )
            return

        for archivo in resultado.copiados:
            registrar_log(f"✅ Respaldado: {archivo}")

        if resultado.omitidos:
            for origen, motivo in resultado.omitidos:
                if motivo == "no_encontrado":
                    registrar_log(f"⚠️ Archivo no encontrado para respaldo: {origen}")
                else:
                    registrar_log(
                        "⚠️ No se pudo respaldar {origen}: {motivo}".format(
                            origen=origen, motivo=motivo
                        )
                    )

        if resultado.copiados:
            mensaje = (
                "Se creó un respaldo con "
                f"{len(resultado.copiados)} archivo(s) en {resultado.destino}."
            )
            icono = QSystemTrayIcon.Information
        else:
            archivos_esperados = (
                archivos if archivos else [str(nombre) for nombre in ARCHIVOS_PREDETERMINADOS]
            )
            mensaje = (
                "No se copiaron archivos. Verifica que existan los resultados esperados: "
                + ", ".join(archivos_esperados)
            )
            icono = QSystemTrayIcon.Warning

        if self._should_notify("respaldo", True):
            self.tray.showMessage("🗄️ Respaldo histórico", mensaje, icono)

    def mostrar_estado_sesion(self) -> None:
        estado = "❌ Archivo de sesión no encontrado"
        detalles_archivo = ""
        try:
            with SESSION_FILE.open("r", encoding="utf-8") as archivo:
                datos = json.load(archivo)
            cookies = datos.get("cookies", []) if isinstance(datos, dict) else []
            if any("pjn.gov.ar" in str(cookie.get("domain", "")) for cookie in cookies):
                estado = "🟢 Sesión activa y válida"
            else:
                estado = "⚠️ Sesión incompleta o caducada"
            try:
                marca_tiempo = datetime.fromtimestamp(SESSION_FILE.stat().st_mtime)
                detalles_archivo = (
                    f"\n📅 Última actualización del archivo: {marca_tiempo:%Y-%m-%d %H:%M:%S}"
                )
            except OSError:
                detalles_archivo = ""
        except FileNotFoundError:
            estado = "❌ No se encontró una sesión guardada"
        except json.JSONDecodeError:
            estado = "❌ Archivo de sesión ilegible"
        except Exception as exc:  # pragma: no cover - diagnóstico en ejecución real
            estado = f"❌ Error inesperado al leer la sesión: {exc}"

        modo = self.config.get("modo", "automatico").replace("_", " ").capitalize()
        intervalo_expedientes = self.obtener_intervalo("expedientes")
        intervalo_entradas = self.obtener_intervalo("entradas")
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            ruta_sesion = SESSION_FILE.resolve()
        except Exception:  # pragma: no cover - rutas en entornos heterogéneos
            ruta_sesion = SESSION_FILE

        mensaje = (
            f"📅 Fecha y hora actual: {ahora}\n"
            f"🕒 Modo de trabajo: {modo}\n"
            "⏱ Intervalos configurados: "
            f"expedientes {intervalo_expedientes} min / "
            f"entradas {intervalo_entradas} min\n"
            f"{estado}"
            f"{detalles_archivo}"
            f"\n📁 Archivo: {ruta_sesion}"
        )

        registrar_log(f"🔐 Estado de sesión consultado: {estado}")
        QMessageBox.information(None, "Estado de sesión", mensaje)

    def forzar_login(self) -> None:
        try:
            if SESSION_FILE.exists():
                SESSION_FILE.unlink()
                registrar_log("⚠️ Se eliminó el archivo de sesión para forzar un nuevo login.")
                self.tray.showMessage(
                    "⚠️ Forzar login", "✅ Se eliminó la sesión guardada.", QSystemTrayIcon.Information
                )
            else:
                registrar_log("ℹ️ Se solicitó forzar login pero no había sesión guardada.")
                self.tray.showMessage(
                    "⚠️ Forzar login", "ℹ️ No se encontró una sesión previa.", QSystemTrayIcon.Information
                )
        except Exception as exc:  # pragma: no cover - manejo defensivo
            registrar_log(f"❌ Error al eliminar la sesión: {exc}")
            self.tray.showMessage(
                "⚠️ Forzar login",
                f"❌ No se pudo eliminar la sesión: {exc}",
                QSystemTrayIcon.Critical,
            )

    def comparar_expedientes_manual(self) -> None:
        self._comparar_expedientes(
            origen="manual",
            notificar=True,
            notificar_sin_cambios=self._should_notify(
                "comparacion_sin_cambios", False
            ),
            notificar_faltantes=self._should_notify(
                "comparacion_faltantes", True
            ),
        )

    def _comparar_expedientes(
        self,
        *,
        origen: str,
        notificar: bool,
        notificar_sin_cambios: bool,
        notificar_faltantes: bool,
    ) -> None:
        if comparar_expedientes is None:
            registrar_log(
                "ℹ️ Comparación de expedientes no disponible: faltan dependencias."
            )
            if notificar:
                self.tray.showMessage(
                    "📊 Comparación de expedientes",
                    "ℹ️ La comparación no está disponible en esta instalación.",
                    QSystemTrayIcon.Information,
                )
            return

        resultado: ResultadoComparacion = comparar_expedientes(
            base_dir=self.directorio_monitoreo,
            config=self.config,
        )

        for aviso in getattr(resultado, "avisos", []):
            registrar_log(f"ℹ️ Comparación {origen}: {aviso}")

        if resultado.faltantes:
            for mensaje in resultado.mensajes_faltantes():
                registrar_log(f"⚠️ Comparación {origen}: {mensaje}")
            if notificar and notificar_faltantes:
                self.tray.showMessage(
                    "📊 Comparación de expedientes",
                    "⚠️ No se encontraron los archivos necesarios para comparar.",
                    QSystemTrayIcon.Warning,
                )
            return

        if resultado.excepcion:
            registrar_log(
                f"❌ Comparación {origen}: error al comparar expedientes: {resultado.excepcion}"
            )
            if notificar:
                self.tray.showMessage(
                    "📊 Comparación de expedientes",
                    f"❌ Error al comparar: {resultado.excepcion}",
                    QSystemTrayIcon.Critical,
                )
            return

        total = resultado.total_cambios
        if total > 0:
            registrar_log(
                f"🧪 Comparación {origen}: {total} cambios detectados en expedientes."
            )
            if resultado.informe:
                registrar_log(f"📄 Informe de comparación: {resultado.informe}")
            if notificar:
                self.tray.showMessage(
                    "📊 Comparación de expedientes",
                    f"{total} cambios detectados.",
                    QSystemTrayIcon.Information,
                )
            return

        registrar_log("🧪 Comparación %s: sin cambios detectados." % origen)
        if notificar and notificar_sin_cambios:
            self.tray.showMessage(
                "📊 Comparación de expedientes",
                "Sin cambios detectados.",
                QSystemTrayIcon.Information,
            )

    def salir(self) -> None:
        self.tray.hide()
        self.app.quit()

    def abrir_configuracion(self) -> None:
        dialogo = ConfiguracionDialog(self.config, parent=self.menu)
        if dialogo.exec() != QDialog.Accepted:
            return

        nueva_config = dialogo.obtener_configuracion()
        if not isinstance(nueva_config, dict):
            return

        try:
            guardar_config_monitor(nueva_config)
        except Exception as error:  # pragma: no cover - persistencia en ejecución real
            registrar_log(f"❌ No se pudo guardar la configuración: {error}")
            QMessageBox.critical(
                None,
                "Error al guardar configuración",
                f"No fue posible guardar los cambios: {error}",
            )
            return

        self.config = cargar_config_monitor()
        self._aplicar_configuracion(self.config)
        self.actualizar_modo_seleccionado()
        self.actualizar_tooltip()
        self.reiniciar_temporizadores()
        registrar_log("⚙️ Configuración del monitor actualizada desde la bandeja.")
        self.tray.showMessage(
            "Configuración actualizada",
            "Los parámetros del monitor se guardaron correctamente.",
            QSystemTrayIcon.Information,
        )


if __name__ == "__main__":
    MonitorExpedientesTray()
