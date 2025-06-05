import sys
import os
import json
from datetime import datetime
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QWidget
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer, QThread, Signal, Qt
from web.auto_login import reutilizar_sesion_async, SESSION_FILE
from core.modulos_monitor.expedientes_modular.verificacion_expedientes import VerificadorExpedientes, registrar_log
from core.gestion_expedientes.comparar_expedientes_monitor import comparar_expedientes_monitor


CONFIG_PATH = "config_monitor.json"

class VerificadorNotificaciones(QThread):
    resultado = Signal(object)

    def run(self):
        import asyncio
        asyncio.run(self.verificar_async())

    async def verificar_async(self):
        from notificaciones_v2.notificaciones_control_v4_async import actualizar_notificaciones_nuevas
        page, _, _, _ = await reutilizar_sesion_async()
        if page:
            destino = os.path.abspath(os.path.join(os.getcwd(), "datos_extraidos", "monitoreo"))
            nuevas = await actualizar_notificaciones_nuevas(page, destino=destino)

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
        self.menu.addAction("🧪 Comparar Expedientes").triggered.connect(self.comparar_expedientes)
        self.menu.addAction("🗂 Copiar últimos resultados a histórico").triggered.connect(self.respaldar_resultados_verificacion)

        self.submenu_modo = QMenu("🛠️ Modo de Trabajo")
        for modo in ["automatico", "laboral", "no_laboral"]:
            nombre_visible = modo.replace("_", " ").capitalize()
            accion = QAction(nombre_visible, checkable=True)
            accion.setData(modo)  # Asocia el valor real del modo
            accion.triggered.connect(lambda checked, a=accion: self.cambiar_modo(a.data()))
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
        self.reintentos_notif = 0
        self.ejecutando_verificacion = False
        self.ejecutando_notificaciones = False

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
        if self.ejecutando_verificacion:
            registrar_log("⏳ Verificación de expedientes ya en curso.")
            return
        self.ejecutando_verificacion = True
        self.verificador = VerificadorExpedientes(carpeta_salida=os.path.abspath(os.path.join(os.getcwd(), "datos_extraidos", "monitoreo")))
        self.verificador.resultado.connect(self.procesar_resultado_expedientes)
        self.verificador.start()

    def verificar_notificaciones(self):
        if self.ejecutando_notificaciones:
            registrar_log("⏳ Verificación de notificaciones ya en curso.")
            return
        self.ejecutando_notificaciones = True
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

        self.tray.showMessage("📥 Expedientes", mensajes.get(estado, "❓ Estado no reconocido"))

        if estado != "completo":
            self.reintentos += 1
            if self.reintentos < 5:
                registrar_log(f"🔁 Reintentando verificación ({self.reintentos}/5) en 5 segundos...")
                QTimer.singleShot(5000, self.verificar_expedientes)
            else:
                registrar_log("❌ Se alcanzó el límite de reintentos. No se pudo completar la verificación.")
        else:
            self.reintentos = 0
            # 🔄 Comparar automáticamente al finalizar verificación exitosa
            try:
                ruta_actual = "C:/Users/aleja/Documents/Sistema/modulos_monitor/general/descargas_monitoreo/expedientes/expedientes_monitor.json"
                ruta_base = "C:/Users/aleja/Documents/Sistema/modulos_monitor/general/descargas_monitoreo/expedientes/expedientes_monitor - base.json"
                carpeta_salida = "C:/Users/aleja/Documents/Sistema/modulos_monitor/general/reportes"

                nuevos, modificados, eliminados = comparar_expedientes_monitor(
                    ruta_actual, ruta_base, carpeta_salida
                )

                total = len(nuevos) + len(modificados) + len(eliminados)
                if total > 0:
                    registrar_log(f"🧪 Comparación automática detectó {total} cambios.")
                    self.tray.showMessage("📊 Comparación automática", f"{total} cambios detectados.")
                else:
                    registrar_log("📊 Comparación automática: sin cambios detectados.")
            except Exception as e:
                registrar_log(f"❌ Error al comparar expedientes: {e}")



        self.ejecutando_verificacion = False

    def procesar_resultado_notificaciones(self, nuevas):
        if nuevas is not None:
            self.reintentos_notif = 0
            if nuevas > 0:
                self.tray.showMessage("🔔 Notificaciones", f"{nuevas} nuevos expedientes detectados.")
            else:
                self.tray.showMessage("🔔 Notificaciones", "Sin nuevas notificaciones.")
        else:
            self.reintentos_notif += 1
            if self.reintentos_notif < 5:
                registrar_log(f"🔁 Reintentando notificaciones ({self.reintentos_notif}/5) en 5 segundos...")
                QTimer.singleShot(5000, self.verificar_notificaciones)
            else:
                registrar_log("❌ Se alcanzó el límite de reintentos de notificaciones.")

        self.ejecutando_notificaciones = False

    def respaldar_resultados_verificacion(self):
        from datetime import datetime
        import os
        import shutil

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        destino = os.path.join("datos_extraidos", "monitoreo", "historico", timestamp)
        os.makedirs(destino, exist_ok=True)

        archivos = {
            "datos_iniciales/expedientes_monitor.json": "expedientes_completo.json",
            "descargas_monitoreo/notificaciones/historial_notificaciones.json": "notificaciones_completo.json"
        }

        for origen, nombre_destino in archivos.items():
            if os.path.exists(origen):
                shutil.copy(origen, os.path.join(destino, nombre_destino))
                print(f"✅ Copiado: {origen} → {nombre_destino}")
            else:
                print(f"⚠️ Archivo no encontrado: {origen}")

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
            accion.setChecked(accion.text().replace(" ", "_").lower() == modo)

    def estado_sesion(self):
        estado = "❌ No verificado"
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                datos = json.load(f)
                if any("pjn.gov.ar" in c.get("domain", "") for c in datos.get("cookies", [])):
                    estado = "🟢 Sesión activa y válida"
                else:
                    estado = "⚠️ Sesión incompleta"
        except FileNotFoundError:
            estado = "❌ Archivo de sesión no encontrado"
        except json.JSONDecodeError:
            estado = "❌ Archivo de sesión ilegible"
        except Exception as e:
            estado = f"❌ Error inesperado: {e}"

        modo = self.config.get("modo", "automatico").replace("_", " ").capitalize()
        intervalo = self.obtener_intervalo()
        ahora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        mensaje = (
            f"📅 Fecha y hora: {ahora}\n"
            f"🕒 Modo de trabajo actual: {modo}\n"
            f"⏱ Intervalo de verificación: {intervalo} minutos\n"
            f"{estado}"
        )

        ventana = QWidget()
        ventana.setWindowFlag(Qt.Tool)
        QMessageBox.information(ventana, "Estado del Monitor", mensaje)

    def forzar_login(self):
        try:
            if os.path.exists(SESSION_FILE):
                os.remove(SESSION_FILE)
                self.tray.showMessage("Login forzado", "✅ Se eliminó el archivo de sesión.")
            else:
                self.tray.showMessage("Login forzado", "ℹ️ No se encontró una sesión guardada.")
        except Exception as e:
            self.tray.showMessage("Error", f"❌ No se pudo eliminar la sesión: {e}")

    def salir(self):
        self.tray.hide()
        self.app.quit()

    def comparar_expedientes(self):
        try:
            ruta_actual = "C:/Users/aleja/Documents/Sistema/modulos_monitor/general/descargas_monitoreo/expedientes/expedientes_monitor.json"
            ruta_base = "C:/Users/aleja/Documents/Sistema/modulos_monitor/general/descargas_monitoreo/expedientes/expedientes_monitor - base.json"
            carpeta_salida = "C:/Users/aleja/Documents/Sistema/modulos_monitor/general/reportes"

            nuevos, modificados, eliminados = comparar_expedientes_monitor(ruta_actual, ruta_base, carpeta_salida)

            total = len(nuevos) + len(modificados) + len(eliminados)
            if total > 0:
                self.tray.showMessage("📊 Comparación de Expedientes", f"{total} cambios detectados.")
            else:
                self.tray.showMessage("📊 Comparación de Expedientes", "Sin cambios detectados.")

        except Exception as e:
            self.tray.showMessage("❌ Error", f"No se pudo completar la comparación: {e}")


if __name__ == "__main__":
    MonitorGeneral()
