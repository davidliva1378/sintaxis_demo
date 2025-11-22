import os
from playwright.async_api import Page

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

        try:
            ruta_archivo = os.path.join(carpeta_destino, nombre_archivo)

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
            await download.save_as(ruta_archivo)
            print(f"✅ Archivo descargado: {nombre_archivo}")

        except Exception as e:
            print(f"❌ Error al descargar archivo de la actuación {idx}: {e}")