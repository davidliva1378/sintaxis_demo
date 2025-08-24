import asyncio

async def extraer_datos_expediente(page):
    try:
        await page.wait_for_load_state("load")
        await page.wait_for_timeout(2000)

        numero = await page.query_selector("span[style='color:#000000;']")
        caratula = await page.query_selector(r"#expediente\:j_idt96\:detailCover")
        dependencia = await page.query_selector(r"#expediente\:j_idt96\:detailDependencia")
        jurisdiccion = await page.query_selector(r"#expediente\:j_idt96\:detailCamera")
        situacion = await page.query_selector(r"#expediente\:j_idt96\:detailSituation")

        expediente = {
            "numero": await numero.inner_text() if numero else "No encontrado",
            "caratula": await caratula.inner_text() if caratula else "No encontrada",
            "dependencia": await dependencia.inner_text() if dependencia else "No encontrada",
            "jurisdiccion": await jurisdiccion.inner_text() if jurisdiccion else "No encontrada",
            "situacion": await situacion.inner_text() if situacion else "No encontrada"
        }

        return expediente
    except Exception as e:
        print(f"⚠️ Error al extraer datos del expediente: {e}")
        return None