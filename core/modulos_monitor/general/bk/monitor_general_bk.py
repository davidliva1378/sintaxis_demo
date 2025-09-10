import sys
import os
import json
from datetime import datetime
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer, QThread, Signal
from web.auto_login import reutilizar_sesion_async, SESSION_FILE
from modulos_monitor.expedientes.obtener_intervalo_monitor import obtener_intervalo_monitor
from modulos_monitor.expedientes.monitoreo_automatico_habilitado import monitoreo_automatico_habilitado
from core.modulos_monitor.expedientes_modular.extraer_expedientes import extraer_expedientes
from modulos_monitor.expedientes_modular.verificacion_expedientes import VerificadorExpedientes, registrar_log

CONFIG_PATH = "config_monitor.json"


class VerificadorExpedientes(QThread):
    resultado = Signal(object)

    def run(self):
        import asyncio
        asyncio.run(self.verificar_async())

    async def verificar_async(self):
        from panel_pjn.acciones_pjn.urls_pjn import URL_CONSULTAS
        async with reutilizar_sesion_async() as (page, context, browser):
            if page:
                await page.goto(URL_CONSULTAS)
                carpeta = os.path.join(os.getcwd(), "descargas_monitoreo", "expedientes")
                expedientes, ruta, estado = await extraer_expedientes(
                    page,
                    carpeta_salida=carpeta,
                    nombre_archivo="expedientes_monitor.json",
                    detener_en_duplicado=True,
                    guardar_json=True,
                    tiempo_maximo_segundos=None
                )
                self.resultado.emit({
                    "estado": estado,
                    "ruta": ruta,
                    "cantidad": len(expedientes)
                })
            else:
                self.resultado.emit({"estado": "fallo"})


class VerificadorNotificaciones(QThread):
    resultado = Signal(object)

    def run(self):
        import asyncio
        asyncio.run(self.verificar_async())

    async def verificar_async(self):
        from notificaciones_v2.notificaciones_control_v4_async import actualizar_notificaciones_nuevas
        async with reutilizar_sesion_async() as (page, context, browser):
            if page:
                nuevas = await actualizar_notificaciones_nuevas(page)
                self.resultado.emit(nuevas)
            else:
                self.resultado.emit(None)


class MonitorGeneral:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.tray = QSystemTrayIcon(QIcon("icono.ico"))
        self.tray.setToolTip("Monitor General PJN")
        self.tray.setVisible(True)

        self.menu = QMenu()
        self.menu.addAction("📥 Verificar Expedientes").triggered.connect(self.verificar_expedientes)
        self.menu.addAction("🔔 Verificar Notificaciones").triggered.connect(self.verificar_notificaciones)
        self.menu.addAction("🔐 Estado de Sesión").triggered.connect(self.estado_sesion)

        self.submenu_modo = QMenu("🛠️ Modo de Trabajo")
        for modo in ["automatico", "laboral", "no_laboral"]:
            accion = QAction(modo.capitalize(), checkable=True)
            accion.triggered.connect(lambda checked, m=modo: self.cambiar_modo(m))
            self.submenu_modo.addAction(accion)
        self.menu.addMenu(self.submenu_modo)

        self.menu.addAction("⚠️ Forzar nuevo login").triggered.connect(self.forzar_login)
        self.menu.addSeparator()
        self.menu.addAction("🛑 Salir").triggered.connect(self.salir)
        self.tray.setContextMenu(self.menu)

        self.config = self.cargar_config()
        self.actualizar_modo_seleccionado()

        self.timer_expedientes = QTimer()
        self.timer_expedientes.timeout.connect(self.verificar_expedientes)

        self.timer_notificaciones = QTimer()
        self.timer_notificaciones.timeout.connect(self.verificar_notificaciones)

        self.reintentos = 0

        self.iniciar_temporizadores()
        sys.exit(self.app.exec())

    def cargar_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {
                "modo": "automatico",
                "horario_laboral": {
                    "dias": ["lunes", "martes", "miércoles", "jueves", "viernes"],
                    "hora_inicio": "07:00",
                    "hora_fin": "20:00",
                    "intervalo_minutos": 30
                },
                "fuera_horario": {
                    "intervalo_minutos": 240
                }
            }

    def esta_en_horario_laboral(self):
        ahora = datetime.now()
        dia_actual = ahora.strftime("%A").lower()
        dias = [d.lower() for d in self.config["horario_laboral"]["dias"]]
        hora_inicio = datetime.strptime(self.config["horario_laboral"]["hora_inicio"], "%H:%M").time()
        hora_fin = datetime.strptime(self.config["horario_laboral"]["hora_fin"], "%H:%M").time()
        return dia_actual in dias and hora_inicio <= ahora.time() <= hora_fin

    def obtener_intervalo(self):
        modo = self.config.get("modo", "automatico")
        if modo == "laboral":
            return self.config["horario_laboral"]["intervalo_minutos"]
        elif modo == "no_laboral":
            return self.config["fuera_horario"]["intervalo_minutos"]
        elif modo == "automatico":
            return self.config["horario_laboral"]["intervalo_minutos"] if self.esta_en_horario_laboral() else \
            self.config["fuera_horario"]["intervalo_minutos"]
        return 60

    def iniciar_temporizadores(self):
        intervalo = self.obtener_intervalo()
        self.timer_expedientes.start(intervalo * 60 * 1000)
        self.timer_notificaciones.start(intervalo * 60 * 1000)
        self.verificar_expedientes()
        self.verificar_notificaciones()

    def verificar_expedientes(self):
        self.verificador = VerificadorExpedientes()
        self.verificador.resultado.connect(self.procesar_resultado_expedientes)
        self.verificador.start()

    def verificar_notificaciones(self):
        self.hilo_notificaciones = VerificadorNotificaciones()
        self.hilo_notificaciones.resultado.connect(self.procesar_resultado_notificaciones)
        self.hilo_notificaciones.start()

    def procesar_resultado_expedientes(self, datos):
        estado = datos.get("estado", "desconocido")
        mensajes = {
            "completo": "✅ Extracción finalizada exitosamente.",
            "repetido_detectado": "⚠️ Se detectó repetición de expedientes. La extracción se interrumpió.",
            "tiempo_maximo": "⏱ Se alcanzó el tiempo máximo permitido.",
            "tabla_no_disponible": "❌ No se encontró la tabla de expedientes en la página.",
            "fallo": "❌ Fallo en la verificación.",
            "desconocido": "❓ Estado no reconocido."
        }

        registrar_log(f"📦 Estado: {estado}")
        registrar_log(mensajes.get(estado, mensajes["desconocido"]))

        if "cantidad" in datos:
            registrar_log(f"📊 Total extraídos: {datos['cantidad']}")

        if datos.get("ruta"):
            registrar_log(f"📁 Guardado en: {datos['ruta']}")

        # Notificación en bandeja
        self.tray.showMessage("📥 Expedientes", mensajes.get(estado, "❓ Estado no reconocido"))

        # Reintentos automáticos
        if estado != "completo":
            self.reintentos += 1
            if self.reintentos < 5:
                registrar_log(f"🔁 Reintentando verificación ({self.reintentos}/5) en 5 segundos...")
                QTimer.singleShot(5000, self.verificar_expedientes)
            else:
                registrar_log("❌ Se alcanzó el límite de reintentos. No se pudo completar la verificación.")
        else:
            self.reintentos = 0

    def procesar_resultado_notificaciones(self, nuevas):
        if nuevas is not None:
            if nuevas > 0:
                self.tray.showMessage("🔔 Notificaciones", f"{nuevas} nuevos expedientes detectados.")

    def cambiar_modo(self, nuevo_modo):
        self.config["modo"] = nuevo_modo
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2)
        self.actualizar_modo_seleccionado()
        self.timer_expedientes.stop()
        self.timer_notificaciones.stop()
        self.iniciar_temporizadores()

    def actualizar_modo_seleccionado(self):
        modo = self.config.get("modo", "automatico")
        for accion in self.submenu_modo.actions():
            accion.setChecked(accion.text().lower() == modo)

    def estado_sesion(self):
        estado = "❌ No verificado"
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                datos = json.load(f)
                if any("pjn.gov.ar" in c.get("domain", "") for c in datos.get("cookies", [])):
                    estado = "🟢 Sesión activa y válida"
                else:
                    estado = "⚠️ Sesión incompleta"
        except:
            estado = "❌ Archivo de sesión no encontrado o ilegible"
        QMessageBox.information(None, "Estado de Sesión", estado)

    def forzar_login(self):
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
            self.tray.showMessage("Login forzado", "✅ Se eliminó el archivo de sesión.")
        else:
            self.tray.showMessage("Login forzado", "ℹ️ No se encontró una sesión guardada.")

    def salir(self):
        self.tray.hide()
        self.app.quit()


if __name__ == "__main__":
    MonitorGeneral()
