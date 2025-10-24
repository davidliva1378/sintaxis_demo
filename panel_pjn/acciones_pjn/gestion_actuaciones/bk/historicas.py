#refactorizada
import os
import re
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from panel_pjn.acciones_pjn.gestion_actuaciones.utilidades import limpiar_texto, normalizar_fecha, generar_hash_archivo #refactorizados a utils.py


async def extraer_actuaciones_historicas(page_expediente, expediente_datos, indice_inicial=1):
    actuaciones = []
    indice_actual = indice_inicial
    try:
        await page_expediente.click("a:has-text('Ver históricas')")

        # Esperamos que aparezca la tabla o el mensaje de "no posee actuaciones"
        try:
            await page_expediente.wait_for_selector(
                "#expediente\\:action-historic-table tbody tr, div.alert.white-panel",
                timeout=8000
            )
        except Exception:
            return [], "Timeout esperando tabla o mensaje de actuaciones históricas"

        mensaje = await page_expediente.query_selector("div.alert.white-panel")
        if mensaje:
            texto = await mensaje.inner_text()
            if "no posee actuaciones históricas" in texto.lower():
                print("El expediente no posee actuaciones históricas.")
                return [], None

        expediente_numero = expediente_datos.get("numero", "desconocido")
        expediente_numero = re.sub(r'[^a-zA-Z0-9_-]', '_', expediente_numero)
        timestamp_extraccion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        pagina = 1
        while True:
            print(f"Página {pagina} (históricas): extrayendo...")

            filas = await page_expediente.query_selector_all("#expediente\\:action-historic-table tbody tr")
            if not filas:
                print("No se encontraron filas en actuaciones históricas.")
                break

            for fila in filas:
                celdas = await fila.query_selector_all("td")
                if len(celdas) < 6:
                    continue

                oficina = limpiar_texto(await celdas[1].inner_text())
                oficina_completa = await celdas[1].get_attribute("title") or oficina
                fecha_cruda = limpiar_texto(await celdas[2].inner_text())
                fecha = normalizar_fecha(fecha_cruda)
                tipo = limpiar_texto(await celdas[3].inner_text()).replace(" ", "_").upper()
                detalle = limpiar_texto(await celdas[4].inner_text())
                foja = limpiar_texto(await celdas[5].inner_text())

                archivo_url = None
                nombre_archivo = None
                tipo_archivo = None

                icono = await fila.query_selector("i.fa-download")
                tiene_archivo = bool(icono)

                if icono:
                    link = await page_expediente.evaluate_handle("(el) => el.closest('a')", icono)
                    if link:
                        archivo_url = await link.get_attribute("href")
                        nombre_archivo = await link.get_attribute("download")
                        if not nombre_archivo and archivo_url:
                            parsed = urlparse(archivo_url)
                            nombre_archivo = parse_qs(parsed.query).get("tipoDoc", ["documento.pdf"])[0]
                        tipo_archivo = os.path.splitext(nombre_archivo)[1][1:].lower() if nombre_archivo else None
                        hash_val = generar_hash_archivo(fecha, tipo, detalle)
                        nombre_archivo = f"{fecha}_{tipo}_{hash_val}.pdf"
                else:
                    hash_val = generar_hash_archivo(fecha, tipo, detalle)

                actuaciones.append({
                    "Indice": indice_actual,
                    "Oficina": oficina,
                    "OficinaCompleta": oficina_completa,
                    "Fecha": fecha,
                    "Tipo": tipo,
                    "Detalle": detalle,
                    "Foja": foja,
                    "Archivo": archivo_url if archivo_url else "N/A",
                    "NombreArchivo": nombre_archivo if archivo_url else "N/A",
                    "TieneArchivo": tiene_archivo,
                    "TipoArchivo": tipo_archivo if tipo_archivo else "N/A",
                    "Hash": hash_val,
                    "ExtraidaEn": timestamp_extraccion,
                    "EsHistorica": True
                })

                indice_actual += 1

            boton_siguiente = await page_expediente.query_selector("a[id^='expediente:j_idt']:not(.ui-state-disabled):has-text('Siguiente')")
            if boton_siguiente:
                try:
                    fila_primera = await page_expediente.query_selector("#expediente\\:action-historic-table tbody tr td:nth-child(3)")
                    fecha_antes = await fila_primera.inner_text() if fila_primera else ""

                    await boton_siguiente.click()
                    pagina += 1

                    await page_expediente.wait_for_selector("#expediente\\:action-historic-table tbody tr", timeout=8000)
                    await page_expediente.wait_for_function(
                        """
                        (fechaAntes) => {
                            const celda = document.querySelector('#expediente\\\\:action-historic-table tbody tr td:nth-child(3)');
                            return celda && celda.innerText.trim() !== fechaAntes;
                        }
                        """,
                        arg=fecha_antes.strip(),
                        timeout=8000
                    )

                except Exception as e:
                    print(f"No se pudo avanzar de página histórica: {e}")
                    break
            else:
                print("No hay más páginas históricas.")
                break

        return actuaciones, None

    except Exception as e:
        return [], f"Error al extraer históricas: {type(e).__name__}: {str(e)}"
