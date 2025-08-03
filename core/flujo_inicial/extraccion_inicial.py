import asyncio
from datetime import datetime
import os
import json

from playwright.async_api import async_playwright
from web.auto_login import reutilizar_sesion_async
from core.modulos_monitor.expedientes_modular.extraer_expedientes import extraer_expedientes
from panel_pjn.acciones_pjn.urls_pjn import URL_CONSULTAS

MAX_INTENTOS = 5

async def extraccion_incremental_async():
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    carpeta_destino = os.path.join("datos_extraidos", "monitoreo", "historico")
    os.makedirs(carpeta_destino, exist_ok=True)
    ruta_final = os.path.join(carpeta_destino, f"expedientes_completo_incremental_{fecha_hoy}.json")

    expedientes_totales = []
    intentos = 0

    async with async_playwright() as p:
        page, context, browser, _ = await reutilizar_sesion_async()

        while intentos < MAX_INTENTOS:
            intentos += 1
            print(f"🔁 Intento {intentos} de extracción...")

            # Reiniciar navegación completamente para evitar sesión mal cargada
            await page.close()
            page = await context.new_page()
            await page.goto(URL_CONSULTAS)
            await page.wait_for_load_state("domcontentloaded")

            try:
                nuevos, _, motivo = await extraer_expedientes(
                    page=page,
                    guardar_json=False,
                    detener_en_duplicado=True,
                    fecha_corte=None
                )
            except Exception as e:
                print(f"❌ Error inesperado: {e}")
                continue

            numeros_existentes = {e['numero'] for e in expedientes_totales}
            nuevos_filtrados = [e for e in nuevos if e['numero'] not in numeros_existentes]

            if nuevos_filtrados:
                expedientes_totales.extend(nuevos_filtrados)
                print(f"✅ Nuevos expedientes incorporados: {len(nuevos_filtrados)}")
            else:
                print("⚠️ No se encontraron expedientes nuevos.")

            print(f"⛔ Motivo de interrupción: {motivo}")
            if motivo in ("fin_tabla", "completo"):
                break

        if intentos >= MAX_INTENTOS:
            print("⚠️ Se alcanzó el límite de intentos.")
            print("[1] Reintentar ahora")
            print("[2] Guardar lista parcial")
            print("[3] Cancelar")
            opcion = input("Seleccione una opción: ").strip()
            if opcion == "1":
                await extraccion_incremental_async()
                return
            elif opcion == "2":
                print("💾 Guardando parcial...")
            else:
                print("🛑 Operación cancelada.")
                return

        with open(ruta_final, "w", encoding="utf-8") as f:
            json.dump(expedientes_totales, f, indent=2, ensure_ascii=False)
        print(f"📁 Expedientes guardados en {ruta_final}")

        await context.close()
        await browser.close()
        print("🏁 Extracción finalizada.")


if __name__ == "__main__":
    asyncio.run(extraccion_incremental_async())
