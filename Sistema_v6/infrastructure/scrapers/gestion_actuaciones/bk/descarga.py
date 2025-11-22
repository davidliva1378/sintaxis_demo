#refact
import os
import asyncio
from playwright.async_api import Page

async def aviso_si_tarda(idx, segundos):
    await asyncio.sleep(segundos)
    print(f"⏳ Descarga en curso para actuación {idx}... lleva más de {segundos} segundos.")

async def descargar_archivos_actuaciones(page: Page, actuaciones: list, carpeta_destino: str):
    if not actuaciones:
        print("⚠️ No se proporcionaron actuaciones para descargar.")
        return

    print(f"📥 Iniciando descarga de archivos ({len(actuaciones)} actuaciones)...")
    os.makedirs(carpeta_destino, exist_ok=True)

    for idx, act in enumerate(actuaciones, start=1):
        archivo_url = act.get("Archivo", "N/A")
        nombre_archivo = act.get("NombreArchivo", f"documento_{idx}.pdf")

        if archivo_url == "N/A":
            print(f"🚫 Actuación {idx}: sin archivo para descargar.")
            continue

        ruta_archivo = os.path.join(carpeta_destino, nombre_archivo)

        if os.path.exists(ruta_archivo):
            print(f"⏭️ Archivo ya existe: {nombre_archivo}")
            continue

        for intento in range(3):
            try:
                async with page.expect_download() as download_info:
                    await page.evaluate("""
                        (url) => {
                            const a = document.createElement('a');
                            a.href = url;
                            a.target = '_blank';
                            a.rel = 'noopener';
                            a.click();
                        }
                    """, archivo_url)

                download = await download_info.value

                # Aviso si tarda
                advertencia = asyncio.create_task(aviso_si_tarda(idx, 30))
                await download.save_as(ruta_archivo)
                advertencia.cancel()

                print(f"✅ Archivo descargado: {nombre_archivo}")
                break  # éxito
            except Exception as e:
                if intento == 2:
                    print(f"❌ Falló la descarga tras 3 intentos para actuación {idx}: {e}")
                else:
                    print(f"⚠️ Reintentando actuación {idx} ({intento + 1}/3)...")
                    await asyncio.sleep(4)
