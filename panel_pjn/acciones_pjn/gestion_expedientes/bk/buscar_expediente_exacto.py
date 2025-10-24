import asyncio

async def buscar_expediente_exacto(page, texto_buscado):
    pagina = 1
    encontrado = None
    texto = texto_buscado.strip().lower()

    async def buscar_en_pagina():
        tabla = await page.query_selector("table.table-striped")
        if not tabla:
            return None
        filas = await tabla.query_selector_all("tbody tr")
        for fila in filas:
            columnas = await fila.query_selector_all("td")
            if len(columnas) >= 3:
                numero = (await columnas[0].inner_text()).strip().lower()
                caratula = (await columnas[2].inner_text()).strip().lower()
                if texto == numero or texto == caratula:
                    return fila
        return None

    async def avanzar_pagina():
        boton_siguiente = await page.query_selector("a[id*='j_idt285']")
        if boton_siguiente:
            await boton_siguiente.click()
            await page.wait_for_timeout(3000)
            return True
        return False

    print(f"🔎 Buscando coincidencia exacta para: '{texto_buscado}'...")
    while True:
        print(f"📄 Página {pagina}...")
        fila = await buscar_en_pagina()
        if fila:
            print(f"✅ Expediente encontrado en página {pagina}.")
            encontrado = fila
            break
        if not await avanzar_pagina():
            break
        pagina += 1

    if not encontrado:
        print(f"❌ No se encontró coincidencia exacta para: '{texto_buscado}'")
    return encontrado