"""
Modulo reutilizable de verificación de expedientes.
Puede ser llamado desde monitor_general.py u otros sistemas.
"""

import asyncio
import os
from datetime import datetime
from PySide6.QtCore import QThread, Signal

from panel_pjn.acciones_pjn.urls_pjn import URL_CONSULTAS
from core.modulos_monitor.expedientes_modular.extraer_expedientes import extraer_expedientes
from web.auto_login import reutilizar_sesion_async

def registrar_log(mensaje):
    try:
        os.makedirs("impresion_logs", exist_ok=True)
        with open("impresion_logs/log_monitoreo.txt", "a", encoding="utf-8") as f:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            f.write(f"[{timestamp}] {mensaje}\n")
    except Exception as e:
        print(f"Error al registrar log: {e}")
    print(mensaje)

class VerificadorExpedientes(QThread):
    resultado = Signal(object)

    def run(self):
        asyncio.run(self.verificar_async())

    async def verificar_async(self):
        registrar_log("🔍 Iniciando verificación de expedientes...")
        try:
            page, _, browser, playwright = await reutilizar_sesion_async()
            await page.goto(URL_CONSULTAS)
            registrar_log("🌐 Navegación a consultas realizada.")
            expedientes, ruta, estado = await extraer_expedientes(
                page,
                carpeta_salida="datos_iniciales/",
                nombre_archivo="expedientes_monitor.json",
                detener_en_duplicado=True,
                guardar_json=True,
                tiempo_maximo_segundos=None
            )
            resultado = {
                "estado": estado,
                "ruta": ruta,
                "cantidad": len(expedientes)
            }
            await browser.close()
            await playwright.stop()
            self.resultado.emit(resultado)
        except Exception as e:
            registrar_log(f"❌ Error en verificación: {e}")
            self.resultado.emit({"estado": "fallo", "error": str(e)})
