
import asyncio
import os
from datetime import datetime
from web.auto_login import reutilizar_sesion_async
from panel_pjn.acciones_pjn.urls_pjn import URL_CONSULTAS
from core.modulos_monitor.expedientes_modular.extraer_expedientes import extraer_expedientes
import json

async def ir_a_consultas_tras_login(fecha_corte=None):
    page, browser, context, _ = await reutilizar_sesion_async()

    if not page:
        print("❌ No se pudo iniciar sesión.")
        return

    print("🌐 Redirigiendo a la página de CONSULTAS de expedientes...")
    await page.goto(URL_CONSULTAS)
    await page.wait_for_load_state("networkidle")
    print("✅ Página de CONSULTAS cargada correctamente.")

    input("⏸️ Pausa: inspeccioná la página antes del ordenamiento. Presioná ENTER para continuar...")

    print("📊 Seleccionando ordenamiento por FECHA...")
    await page.select_option(r"#j_idt150\:order_by_form\:camara", value="FECHA")
    await page.click("a:has-text('Ordenar')")
    await page.wait_for_selector("table.table-striped tbody tr", timeout=10000)
    print("✅ Expedientes ordenados por fecha.")

    input("⏸️ Pausa: inspeccioná la tabla ordenada. Presioná ENTER para continuar...")

    print(f"📥 Extrayendo expedientes con corte en {fecha_corte}...")
    expedientes, _, _ = await extraer_expedientes(page, guardar_json=False, fecha_corte=fecha_corte)
    print(f"📦 {len(expedientes)} expedientes extraídos con fecha {fecha_corte}.")

    nombre_archivo = f"expedientes_hoy_{datetime.today().strftime('%Y-%m-%d')}.json"
    os.makedirs("datos_extraidos/monitoreo/", exist_ok=True)
    path = os.path.join("datos_extraidos/monitoreo/", nombre_archivo)

    with open(path, "w", encoding="utf-8") as f:
        json.dump(expedientes, f, ensure_ascii=False, indent=2)

    print(f"✅ Guardado en {path}")

    try:
        await page.close()
        await context.close()
        await browser.close()
    except Exception as e:
        print(f"⚠️ Advertencia al cerrar recursos: {e}")
    finally:
        await asyncio.sleep(0.1)
