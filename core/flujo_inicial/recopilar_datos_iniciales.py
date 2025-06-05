import os
import json
import asyncio
from datetime import datetime

from web.auto_login import reutilizar_sesion_async
from core.modulos_monitor.expedientes_modular.extraer_expedientes import extraer_expedientes
from notificaciones_v2.notificaciones_control_v4_async import actualizar_notificaciones_nuevas
from panel_pjn.acciones_pjn.gestion_actuaciones.extraccion_completa import extraer_actuaciones_completas
from panel_pjn.acciones_pjn.urls_pjn import URL_CONSULTAS


async def recopilar_datos_iniciales():
    """
    Realiza la extracción inicial completa:
    - Expedientes
    - Notificaciones
    - Actuaciones por expediente (sin descargar archivos)
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
    expedientes, _, _ = await extraer_expedientes(
        page,
        carpeta_salida=None,
        nombre_archivo=None,
        detener_en_duplicado=True,
        guardar_json=False,
        tiempo_maximo_segundos=None
    )
    archivo_expedientes = os.path.join(carpeta_destino, f"expedientes_completo_{fecha}.json")
    with open(archivo_expedientes, "w", encoding="utf-8") as f:
        json.dump(expedientes, f, indent=2, ensure_ascii=False)
    print(f"✅ Expedientes extraídos: {len(expedientes)}")

    print("\n🔔 Extrayendo notificaciones...")
    notificaciones = await actualizar_notificaciones_nuevas(page)
    archivo_notificaciones = os.path.join(carpeta_destino, f"notificaciones_completo_{fecha}.json")
    with open(archivo_notificaciones, "w", encoding="utf-8") as f:
        json.dump(notificaciones, f, indent=2, ensure_ascii=False)
    print(f"✅ Notificaciones extraídas: {len(notificaciones)}")

    print("\n📑 Extrayendo actuaciones (solo metadatos)...")
    actuaciones_por_expediente = {}
    for exp in expedientes:
        numero = exp.get("numero") or exp.get("expediente")
        print(f"  - {numero}...", end=" ")
        try:
            actuaciones, _, error = await extraer_actuaciones_completas(
                page_expediente=page,
                expediente_datos=exp,
                incluir_historicas=False,
                directorio_base="base_datos_simulada/"
            )
            actuaciones_por_expediente[numero] = actuaciones
            print(f"{len(actuaciones)} actuaciones")
        except Exception as e:
            print(f"❌ Error: {e}")

    archivo_actuaciones = os.path.join(carpeta_destino, f"actuaciones_completo_{fecha}.json")
    with open(archivo_actuaciones, "w", encoding="utf-8") as f:
        json.dump(actuaciones_por_expediente, f, indent=2, ensure_ascii=False)

    print("\n🎉 Recopilación de datos inicial completada.")

    await browser.close()
    await playwright.stop()


if __name__ == "__main__":
    asyncio.run(recopilar_datos_iniciales())
