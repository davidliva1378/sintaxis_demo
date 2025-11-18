"""
Módulo reutilizable de verificación de expedientes.
Versión con manejo robusto de errores en QThread, carpeta destino parametrizable
y soporte de modo "completo" (sin fecha de corte).
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from PySide6.QtCore import QThread, Signal

from configuracion.urls import URL_CONSULTAS
from pjn.monitor.extraer_expedientes import extraer_expedientes
from pjn.auto_login import reutilizar_sesion_async
from utils.logging import registrar_log


def obtener_fecha_corte(config: dict) -> str | None:
    """
    Devuelve una fecha de corte en formato YYYY-MM-DD, o None si no corresponde aplicar corte.
    Modos soportados en config["filtro_expedientes"]["modo"]:
      - "hoy"
      - "ultimo_dia_habil"
      - "dias_atras" (usa 'dias_atras' del config)
      - "hoy+ultimo_dia_habil"
      - "completo" / "sin_corte" / "none" / ""  -> sin corte
    Si el valor es desconocido, no se aplica corte (None).
    Si "dias_atras" no es un entero válido, se registra un aviso y tampoco se aplica corte.
    """
    modo = (config.get("filtro_expedientes", {}).get("modo", "ultimo_dia_habil") or "").lower()

    # Sin corte explícito
    if modo in {"completo", "sin_corte", "none", ""}:
        return None

    if modo == "hoy":
        return datetime.now().strftime("%Y-%m-%d")

    if modo == "ultimo_dia_habil":
        hoy = datetime.now()
        if hoy.weekday() == 5:      # sábado
            delta = 1
        elif hoy.weekday() == 6:    # domingo
            delta = 2
        else:
            delta = 0
        dia_habil = hoy - timedelta(days=delta)
        return dia_habil.strftime("%Y-%m-%d")

    if modo == "dias_atras":
        dias_raw = config.get("filtro_expedientes", {}).get("dias_atras", 1)
        try:
            dias = int(dias_raw)
        except ValueError:
            registrar_log(f"Valor de dias_atras inválido: {dias_raw!r}. Se omite corte.")
            return None
        fecha = datetime.now() - timedelta(days=max(dias, 0))
        return fecha.strftime("%Y-%m-%d")

    if modo == "hoy+ultimo_dia_habil":
        hoy = datetime.now()
        if hoy.weekday() >= 5:  # fin de semana
            delta = 1 if hoy.weekday() == 5 else 2
            dia_habil = hoy - timedelta(days=delta)
            return dia_habil.strftime("%Y-%m-%d")
        return hoy.strftime("%Y-%m-%d")

    # Valor no reconocido -> sin corte
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
            async with reutilizar_sesion_async() as (page, context, browser):
                if page:
                    await page.goto(URL_CONSULTAS)
                    registrar_log("🌐 Navegación a consultas realizada.")

                    # Resolver ruta del archivo de configuración (proyecto/config/config_monitor.json)
                    base_dir = os.path.dirname(os.path.abspath(__file__))
                    ruta_config = os.path.normpath(
                        os.path.join(base_dir, "../../../config/config_monitor.json")
                    )

                    if not os.path.exists(ruta_config):
                        # fallback: intentar en raíz del proyecto
                        ruta_config_alt = os.path.normpath(
                            os.path.join(base_dir, "../../../config_monitor.json")
                        )
                        if os.path.exists(ruta_config_alt):
                            ruta_config = ruta_config_alt

                    with open(ruta_config, "r", encoding="utf-8") as f:
                        config = json.load(f)

                    fecha_corte_iso = obtener_fecha_corte(config)

                    # Convertir a formato dd/mm/yyyy solo si existe
                    if fecha_corte_iso:
                        try:
                            fecha_corte = datetime.strptime(
                                fecha_corte_iso, "%Y-%m-%d"
                            ).strftime("%d/%m/%Y")
                        except Exception as e:
                            registrar_log(
                                f"⚠️ Error al convertir fecha de corte: {fecha_corte_iso} → {e}"
                            )
                            fecha_corte = None
                    else:
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
                        orden=orden,
                    )

                    self.resultado.emit(
                        {
                            "estado": estado
                            if (
                                estado
                                in {
                                    "completo",
                                    "repetido_detectado",
                                    "tiempo_maximo",
                                    "tabla_no_disponible",
                                    "fallo",
                                    "corte_fecha",
                                }
                            )
                            else ("corte_fecha" if fecha_corte else "completo"),
                            "ruta": ruta,
                            "cantidad": len(expedientes),
                        }
                    )
                else:
                    self.resultado.emit({"estado": "fallo"})
        except Exception as e:
            registrar_log(f"❌ Error en verificación: {e}")
            self.resultado.emit({"estado": "fallo", "error": str(e)})
