"""
Modulo reutilizable de verificación de expedientes.
Versión con manejo robusto de errores en QThread y carpeta destino parametrizable.
"""

import asyncio
import json
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

    def __init__(self, carpeta_salida: str = "datos_extraidos/monitoreo/"):
        super().__init__()
        self.carpeta_salida = carpeta_salida

    def run(self):
        print("✅ Cargando verificacion_expedientes con manejo de errores")
        try:
            asyncio.run(self.verificar_async())
        except Exception as e:
            registrar_log(f"❌ Error crítico en hilo de expedientes: {e}")
            self.resultado.emit({"estado": "fallo", "error": str(e)})

    async def verificar_async(self):
        try:
            registrar_log("🔍 Iniciando verificación de expedientes...")
            page, _, browser, playwright = await reutilizar_sesion_async()
            if page:
                await page.goto(URL_CONSULTAS)
                registrar_log("🌐 Navegación a consultas realizada.")
                expedientes, ruta, estado = await extraer_expedientes(
                    page,
                    carpeta_salida=self.carpeta_salida,
                    nombre_archivo="expedientes_monitor.json",
                    detener_en_duplicado=True,
                    guardar_json=True,
                    tiempo_maximo_segundos=None
                )
                await browser.close()
                await playwright.stop()
                self.resultado.emit({
                    "estado": estado,
                    "ruta": ruta,
                    "cantidad": len(expedientes)
                })
            else:
                self.resultado.emit({"estado": "fallo"})
        except Exception as e:
            registrar_log(f"❌ Error en verificación: {e}")
            self.resultado.emit({"estado": "fallo", "error": str(e)})
