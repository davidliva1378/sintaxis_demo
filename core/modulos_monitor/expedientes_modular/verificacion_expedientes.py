"""
Modulo reutilizable de verificación de expedientes.
Versión con manejo robusto de errores en QThread y carpeta destino parametrizable.
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
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


def obtener_fecha_corte(config) -> str:
    modo = config.get("filtro_expedientes", {}).get("modo", "ultimo_dia_habil")

    if modo == "hoy":
        return datetime.now().strftime("%Y-%m-%d")

    elif modo == "ultimo_dia_habil":
        hoy = datetime.now()
        if hoy.weekday() == 5:
            delta = 1
        elif hoy.weekday() == 6:
            delta = 2
        else:
            delta = 0
        dia_habil = hoy - timedelta(days=delta)
        return dia_habil.strftime("%Y-%m-%d")

    elif modo == "dias_atras":
        dias = config.get("filtro_expedientes", {}).get("dias_atras", 1)
        fecha = datetime.now() - timedelta(days=dias)
        return fecha.strftime("%Y-%m-%d")

    elif modo == "hoy+ultimo_dia_habil":
        hoy = datetime.now()
        if hoy.weekday() >= 5:
            delta = 1 if hoy.weekday() == 5 else 2
            dia_habil = hoy - timedelta(days=delta)
            return dia_habil.strftime("%Y-%m-%d")
        else:
            return hoy.strftime("%Y-%m-%d")

    return None


class VerificadorExpedientes(QThread):
    resultado = Signal(object)

    def __init__(self, carpeta_salida: str = "datos_extraidos/monitoreo/"):
        super().__init__()
        self.carpeta_salida = carpeta_salida

    def run(self):
        print("✅ Cargando verificacion_expedientes con manejo de errores y filtro de fecha")
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

                base_dir = os.path.dirname(os.path.abspath(__file__))
                ruta_config = os.path.join(base_dir, "../../../config/config_monitor.json")

                with open(ruta_config, "r", encoding="utf-8") as f:

                    config = json.load(f)

                fecha_corte = obtener_fecha_corte(config)
                # Convertir fecha_corte al formato que espera extraer_expedientes.py: dd/mm/yyyy
                try:
                    fecha_corte = datetime.strptime(fecha_corte, "%Y-%m-%d").strftime("%d/%m/%Y")
                except Exception as e:
                    registrar_log(f"⚠️ Error al convertir fecha de corte: {fecha_corte} → {e}")
                    fecha_corte = None
                orden = config.get("filtro_expedientes", {}).get("orden", "fecha")

                expedientes, ruta, estado = await extraer_expedientes(
                    page,
                    carpeta_salida=self.carpeta_salida,
                    nombre_archivo="expedientes_monitor.json",
                    detener_en_duplicado=True,
                    guardar_json=True,
                    fecha_corte=fecha_corte,
                    tiempo_maximo_segundos=None,
                    orden=orden
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
