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
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QThread, QTimer, Signal
from PySide6.QtGui import QAction, QIcon, QPixmap
from PySide6.QtWidgets import QApplication, QMenu, QMessageBox, QSystemTrayIcon

try:
    from .configuracion_modo import (
        MODOS_VALIDOS,
        actualizar_modo_monitor,
        cargar_config_monitor,
    )
except ImportError:  # pragma: no cover - ejecución directa
    from configuracion_modo import (
        MODOS_VALIDOS,
        actualizar_modo_monitor,
        cargar_config_monitor,
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
        reutilizar_sesion_async,
    )
except ImportError:  # pragma: no cover - compatibilidad con Sistema_v3
    from Sistema_v3.web.auto_login import reutilizar_sesion_async


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


class VerificadorExpedientesV4(QThread):
    """Hilo encargado de recuperar el listado completo de expedientes."""

    resultado = Signal(object)

    def __init__(
        self,
        carpeta_salida: str | Path = "datos_extraidos/monitoreo",
        nombre_archivo: str = "expedientes_monitor.json",
        guardar_json: bool = True,
    ) -> None:
        super().__init__()
        self.carpeta_salida = Path(carpeta_salida)
        self.nombre_archivo = nombre_archivo
        self.guardar_json = guardar_json

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
                    orden="fecha",
                    detener_en_duplicado=False,
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

        # Espacio reservado para herramientas adicionales. Se reintroducirán
        # en futuras versiones una vez finalizada la migración a v4.
        placeholder = QAction("🛠️ Utilidades adicionales (próximamente)")
        placeholder.setEnabled(False)
        self.menu.addAction(placeholder)

        self.menu.addSeparator()
        self.menu.addAction("🛑 Salir").triggered.connect(self.salir)
        self.tray.setContextMenu(self.menu)

        self.config = self.cargar_config()
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

    def esta_en_horario_laboral(self) -> bool:
        ahora = datetime.now()
        dia_actual = ahora.strftime("%A").lower()
        dias = [d.lower() for d in self.config["horario_laboral"]["dias"]]
        hora_inicio = datetime.strptime(
            self.config["horario_laboral"]["hora_inicio"], "%H:%M"
        ).time()
        hora_fin = datetime.strptime(
            self.config["horario_laboral"]["hora_fin"], "%H:%M"
        ).time()
        return dia_actual in dias and hora_inicio <= ahora.time() <= hora_fin

    def obtener_intervalo(self) -> int:
        modo = self.config.get("modo", "automatico")
        if modo == "laboral":
            return self.config["horario_laboral"]["intervalo_minutos"]
        if modo == "no_laboral":
            return self.config["fuera_horario"]["intervalo_minutos"]
        if modo == "automatico":
            return (
                self.config["horario_laboral"]["intervalo_minutos"]
                if self.esta_en_horario_laboral()
                else self.config["fuera_horario"]["intervalo_minutos"]
            )
        return 60

    def iniciar_temporizador(self) -> None:
        intervalo = self.obtener_intervalo()
        self.timer_expedientes.start(intervalo * 60 * 1000)
        self.timer_entradas.start(intervalo * 60 * 1000)
        self.verificar_expedientes()
        self.verificar_entradas()

    def reiniciar_temporizadores(self) -> None:
        self.timer_expedientes.stop()
        self.timer_entradas.stop()
        self.iniciar_temporizador()

    def actualizar_tooltip(self) -> None:
        modo = self.config.get("modo", "automatico").replace("_", " ").capitalize()
        intervalo = self.obtener_intervalo()
        tooltip = (
            "Monitor de Expedientes y Entradas PJN\n"
            f"Modo: {modo} · Intervalo: {intervalo} minutos"
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

        self.actualizar_modo_seleccionado()
        self.actualizar_tooltip()
        self.reiniciar_temporizadores()

        modo_legible = nuevo_modo.replace("_", " ").capitalize()
        intervalo = self.obtener_intervalo()
        registrar_log(
            "⚙️ Modo de trabajo actualizado a "
            f"{modo_legible} ({intervalo} minutos)."
        )
        self.tray.showMessage(
            "Modo de trabajo actualizado",
            f"{modo_legible} · Intervalo: {intervalo} minutos",
        )

    def verificar_expedientes(self) -> None:
        if self.ejecutando_expedientes:
            registrar_log("⏳ Verificación de expedientes ya en curso.")
            return

        self.ejecutando_expedientes = True
        carpeta = Path(os.getcwd()) / "datos_extraidos" / "monitoreo"
        self.hilo_expedientes = VerificadorExpedientesV4(carpeta_salida=carpeta)
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
        carpeta = Path(os.getcwd()) / "datos_extraidos" / "monitoreo"
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
            if self.reintentos_expedientes < 5:
                registrar_log(
                    f"🔁 Reintentando verificación ({self.reintentos_expedientes}/5) en 5 segundos..."
                )
                QTimer.singleShot(5000, self.verificar_expedientes)
            else:
                registrar_log(
                    "❌ Se alcanzó el límite de reintentos. No se pudo completar la verificación."
                )
        else:
            self.reintentos_expedientes = 0

    def procesar_resultado_entradas(self, datos: ResultadoEntradas) -> None:
        if datos.nuevas is None:
            self.reintentos_entradas += 1
            registrar_log("❌ No se pudieron verificar las entradas.")
            if datos.error == "sesion_no_disponible":
                registrar_log("ℹ️ Sesión no disponible al intentar extraer entradas.")
            elif datos.error:
                registrar_log(f"🛑 Error reportado: {datos.error}")
            if self.reintentos_entradas < 5:
                registrar_log(
                    f"🔁 Reintentando entradas ({self.reintentos_entradas}/5) en 5 segundos..."
                )
                QTimer.singleShot(5000, self.verificar_entradas)
            else:
                registrar_log("❌ Se alcanzó el límite de reintentos de entradas.")
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

    def salir(self) -> None:
        self.tray.hide()
        self.app.quit()


if __name__ == "__main__":
    MonitorExpedientesTray()
