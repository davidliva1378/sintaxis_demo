
import asyncio
from datetime import datetime
import os
import json
import logging

from web.auto_login import reutilizar_sesion_async
from core.modulos_monitor.expedientes_modular.extraer_expedientes import extraer_expedientes
from panel_pjn.acciones_pjn.urls_pjn import URL_CONSULTAS

# Importar procesamiento de expedientes (opcional)
try:
    from core.flujo_inicial.procesamiento_expedientes import (
        ProcesadorExpedientesInicial,
        clasificar_actuaciones_desde_json,
        PROCESADOR_DISPONIBLE
    )
except ImportError:
    PROCESADOR_DISPONIBLE = False
    logging.warning("Módulo de procesamiento no disponible")

MAX_INTENTOS = 5

async def extraccion_incremental_async(procesar_expedientes: bool = False):
    """
    Extrae expedientes de forma incremental del PJN.

    Args:
        procesar_expedientes: Si True, procesa expedientes con procesador_pdf
                             (requiere módulo de procesamiento disponible)

    Returns:
        Tuple[list, dict | None]: Lista de expedientes extraídos y resultado
                                   del procesamiento (si se habilitó)
    """
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    carpeta_destino = os.path.join("datos_extraidos", "monitoreo", "historico")
    os.makedirs(carpeta_destino, exist_ok=True)
    ruta_final = os.path.join(carpeta_destino, f"expedientes_completo_incremental_{fecha_hoy}.json")

    expedientes_totales = []
    intentos = 0

    async with reutilizar_sesion_async() as (page, context, browser):
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

        # NUEVO: Procesamiento de expedientes con procesador_pdf
        resultado_procesamiento = None
        if procesar_expedientes and PROCESADOR_DISPONIBLE and expedientes_totales:
            print("\n" + "=" * 70)
            print("🔄 INICIANDO PROCESAMIENTO DE EXPEDIENTES")
            print("=" * 70)

            try:
                procesador = ProcesadorExpedientesInicial(config={
                    "clasificar": True,
                    "analizar_vencimientos": True,
                    "detectar_duplicados": False,
                    "dias_urgentes": 7,
                    "extraer_actuaciones": False,  # No extraer actuaciones por ahora
                    "guardar_reportes": True,
                })

                resultado_procesamiento = await procesador.procesar_expedientes_extraidos(
                    expedientes_totales,
                    page=None,  # Sin página porque no extraemos actuaciones
                    carpeta_base=carpeta_destino
                )

                # Mostrar resumen
                print("\n📊 RESUMEN DE PROCESAMIENTO:")
                print(f"  Total expedientes: {resultado_procesamiento['total_expedientes']}")
                print(f"  Procesados: {resultado_procesamiento['expedientes_procesados']}")

                if resultado_procesamiento.get("vencimientos_urgentes"):
                    venc_urgentes = len(resultado_procesamiento["vencimientos_urgentes"])
                    print(f"\n⚠️  VENCIMIENTOS URGENTES DETECTADOS: {venc_urgentes}")

                if resultado_procesamiento.get("errores"):
                    errores = len(resultado_procesamiento["errores"])
                    print(f"\n❌ Errores durante procesamiento: {errores}")

                print("\n" + "=" * 70)

            except Exception as e:
                print(f"\n❌ Error durante el procesamiento: {e}")
                logging.error(f"Error procesando expedientes: {e}", exc_info=True)

        elif procesar_expedientes and not PROCESADOR_DISPONIBLE:
            print("\n⚠️ Procesamiento solicitado pero procesador_pdf no está disponible")

    print("🏁 Extracción finalizada.")
    return expedientes_totales, resultado_procesamiento


if __name__ == "__main__":
    asyncio.run(extraccion_incremental_async())
