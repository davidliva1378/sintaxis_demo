import sys
import os
import json
from datetime import datetime
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu, QMessageBox, QWidget
from PySide6.QtGui import QIcon, QAction
from PySide6.QtCore import QTimer, QThread, Signal, Qt
import asyncio
from playwright.async_api import async_playwright

from Sistema_v3.operaciones.expedientes.expedientes import extraer_expedientes
from Sistema_v3.operaciones.actuaciones.actuaciones import descargar_archivos_actuaciones
from web.auto_login import reutilizar_sesion_async, SESSION_FILE

CONFIG_PATH = "config/config_monitor_v3.json"


class VerificadorSistemaV3(QThread):
    resultado = Signal(dict)

    def __init__(self, carpeta_salida="datos_extraidos/sistema_v3"):
        super().__init__()
        self.carpeta_salida = carpeta_salida

    def run(self):
        asyncio.run(self.verificar_async())

    async def verificar_async(self):
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                login_exitoso = await reutilizar_sesion_async(page)
                if not login_exitoso:
                    self.resultado.emit({"estado": "fallo", "mensaje": "No se pudo iniciar sesión"})
                    await browser.close()
                    return

                print("🔍 Extrayendo expedientes...")
                expedientes, ruta_archivo, estado = await extraer_expedientes(
                    page=page,
                    carpeta_salida=self.carpeta_salida,
                    delay=3000,
                    detener_en_duplicado=True,
                    tiempo_maximo_segundos=1800
                )

                resultado = {
                    "estado": estado,
                    "cantidad": len(expedientes) if expedientes else 0,
                    "ruta": ruta_archivo
                }

                self.resultado.emit(resultado)
                await browser.close()

        except Exception as e:
            print(f"❌ Error en verificación: {e}")
            self.resultado.emit({"estado": "fallo", "mensaje": str(e)})


class MonitorGeneralV3:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.tray = QSystemTrayIcon(QIcon("icono.ico"))
        self.tray.setToolTip("Monitor General Sistema V3")
        self.tray.setVisible(True)

        self.menu = QMenu()
        self.menu.addAction("📥 Verificar Expedientes").triggered.connect(self.verificar_expedientes)
        self.menu.addAction("⚙️ Verificar Actuaciones").triggered.connect(self.verificar_actuaciones)
        self.menu.addAction("🔐 Estado de Sesión").triggered.connect(self.estado_sesion)
        
        self.submenu_modo = QMenu("🛠️ Modo de Trabajo")
        for modo in ["automatico", "laboral", "no_laboral"]:
            nombre_visible = modo.replace("_", " ").capitalize()
            accion = QAction(nombre_visible, checkable=True)
            accion.setData(modo)
            accion.triggered.connect(lambda checked, a=accion: self.cambiar_modo(a.data()))
            self.submenu_modo.addAction(accion)
        self.menu.addMenu(self.submenu_modo)

        self.menu.addAction("⚠️ Forzar nuevo login").triggered.connect(self.forzar_login)
        self.menu.addSeparator()
        self.menu.addAction("🛑 Salir").triggered.connect(self.salir)
        self.tray.setContextMenu(self.menu)

        self.config = self.cargar_config()
        self.actualizar_modo_seleccionado()

        self.timer_verificacion = QTimer()
        self.timer_verificacion.timeout.connect(self.verificar_expedientes)

        self.ejecutando_verificacion = False
        self.reintentos = 0

        self.iniciar_temporizador()
        sys.exit(self.app.exec())

    def cargar_config(self):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            config_default = {
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
            os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(config_default, f, indent=2, ensure_ascii=False)
            return config_default

    def esta_en_horario_laboral(self):
        ahora = datetime.now()
        dia_actual = ahora.strftime("%A").lower()
        dias_map = {
            "monday": "lunes", "tuesday": "martes", "wednesday": "miércoles",
            "thursday": "jueves", "friday": "viernes", "saturday": "sábado", "sunday": "domingo"
        }
        dia_actual = dias_map.get(dia_actual, dia_actual)
        
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

    def iniciar_temporizador(self):
        intervalo = self.obtener_intervalo()
        self.timer_verificacion.start(intervalo * 60 * 1000)
        print(f"🕒 Monitor iniciado con intervalo de {intervalo} minutos")
        self.verificar_expedientes()

    def verificar_expedientes(self):
        if self.ejecutando_verificacion:
            print("⏳ Verificación ya en curso.")
            return
            
        self.ejecutando_verificacion = True
        print("🔍 Iniciando verificación de expedientes Sistema V3...")
        
        self.verificador = VerificadorSistemaV3(
            carpeta_salida=os.path.abspath(os.path.join(os.getcwd(), "datos_extraidos", "sistema_v3"))
        )
        self.verificador.resultado.connect(self.procesar_resultado)
        self.verificador.start()

    def verificar_actuaciones(self):
        print("⚙️ Función de verificación de actuaciones en desarrollo...")
        self.tray.showMessage("⚙️ Actuaciones", "Funcionalidad en desarrollo")

    def procesar_resultado(self, datos):
        estado = datos.get("estado", "desconocido")
        mensajes = {
            "completo": "✅ Extracción finalizada exitosamente.",
            "repetido_detectado": "⚠️ Se detectó repetición de expedientes. La extracción se interrumpió.",
            "tiempo_maximo": "⏱ Se alcanzó el tiempo máximo permitido.",
            "tabla_no_disponible": "❌ No se encontró la tabla de expedientes en la página.",
            "fallo": "❌ Fallo en la verificación.",
            "corte_fecha": "📆 Se aplicó la fecha de corte. Extracción finalizada.",
            "desconocido": "❓ Estado no reconocido."
        }

        print(f"📦 Estado: {estado}")
        mensaje = mensajes.get(estado, mensajes["desconocido"])
        print(mensaje)

        if "cantidad" in datos:
            print(f"📊 Total extraídos: {datos['cantidad']}")

        if datos.get("ruta"):
            print(f"📁 Guardado en: {datos['ruta']}")

        self.tray.showMessage("📥 Sistema V3", mensaje)

        if estado not in ("completo", "corte_fecha"):
            self.reintentos += 1
            if self.reintentos < 5:
                print(f"🔁 Reintentando verificación ({self.reintentos}/5) en 5 segundos...")
                QTimer.singleShot(5000, self.verificar_expedientes)
            else:
                print("❌ Se alcanzó el límite de reintentos.")
        else:
            self.reintentos = 0

        self.ejecutando_verificacion = False

    def cambiar_modo(self, nuevo_modo):
        self.config["modo"] = nuevo_modo
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
        self.actualizar_modo_seleccionado()
        self.timer_verificacion.stop()
        self.iniciar_temporizador()
        print(f"🔄 Modo cambiado a: {nuevo_modo}")

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
        QMessageBox.information(ventana, "Estado del Monitor V3", mensaje)

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


if __name__ == "__main__":
    MonitorGeneralV3()