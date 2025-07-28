import os
import json
import asyncio
import shutil
from datetime import datetime

from web.auto_login import reutilizar_sesion_async
from core.modulos_monitor.expedientes_modular.extraer_expedientes import extraer_expedientes
from notificaciones_v2.notificaciones_control_v4_async import actualizar_notificaciones_nuevas
from panel_pjn.acciones_pjn.urls_pjn import URL_CONSULTAS


async def recopilar_datos_iniciales():
    """Extrae la lista completa de expedientes y las notificaciones nuevas.

    El resultado se guarda dentro de ``datos_extraidos/monitoreo/historico``.
    No se realiza descarga de actuaciones.
    """
    fecha = datetime.now().strftime("%Y-%m-%d")
    carpeta_destino = "datos_extraidos/monitoreo/historico"
    os.makedirs(carpeta_destino, exist_ok=True)

    print("\n🔐 Iniciando sesión automática...")
    page, context, browser, playwright = await reutilizar_sesion_async()
    if not page:
        print("❌ No se pudo iniciar sesión. Abortando.")
        return

    print("\n🌐 Navegando a la página de expedientes...")
    await page.goto(URL_CONSULTAS)

    print("\n📂 Extrayendo expedientes...")
    expedientes, archivo_expedientes, _ = await extraer_expedientes(
        page,
        carpeta_salida=carpeta_destino,
        nombre_archivo=f"expedientes_completo_{fecha}.json",
        detener_en_duplicado=True,
        guardar_json=True,
        tiempo_maximo_segundos=None
    )
    print(f"✅ Expedientes extraídos: {len(expedientes)}")
    if archivo_expedientes:
        print(f"📁 Guardados en: {archivo_expedientes}")

    print("\n🔔 Extrayendo notificaciones...")
    await actualizar_notificaciones_nuevas(page, destino=carpeta_destino)
    historial = os.path.join(carpeta_destino, "historial_notificaciones.json")
    if os.path.exists(historial):
        with open(historial, "r", encoding="utf-8") as f:
            notificaciones = json.load(f)
        print(f"✅ Notificaciones extraídas: {len(notificaciones)}")
    else:
        print("⚠️ No se encontró el historial de notificaciones.")

    print("\n🎉 Recopilación de datos inicial completada.")

    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(recopilar_datos_iniciales())
