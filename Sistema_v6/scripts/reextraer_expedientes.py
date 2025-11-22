"""Script para re-extraer expedientes con selectores actualizados.

Este script re-procesa los 4 expedientes existentes para actualizar
sus datos con los nuevos selectores corregidos.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pjn.auto_login import reutilizar_sesion_async
from pjn.scraping.expedientes import (
    buscar_expediente_por_numero,
    extraer_datos_expediente,
)
from pjn.selectores import SEL_EXPEDIENTES

# Credenciales
os.environ["PJN_USER"] = "20213071662"
os.environ["PJN_PASSWORD"] = "Surrey_1970"

# Expedientes a re-extraer (en formato normalizado)
EXPEDIENTES = [
    "FRE-004413-2021",
    "FPA-002139-2023",
    "FRE-004321-2021",
    "FRE-005084-2021-1"
]


async def procesar_expediente(numero: str, page):
    """Procesa un expediente completo."""
    print(f"\n{'='*80}")
    print(f"Procesando expediente: {numero}")
    print(f"{'='*80}")

    try:
        # Convertir número normalizado a formato PJN (con espacios y slash)
        # FRE-004413-2021 → FRE 004413/2021
        partes = numero.split('-')
        if len(partes) >= 3:
            prefijo = partes[0]
            num = partes[1]
            anio = partes[2]
            # Si hay sufijo (como en FRE-005084-2021-1)
            sufijo = f"/{partes[3]}" if len(partes) > 3 else ""
            numero_pjn = f"{prefijo} {num}/{anio}{sufijo}"
        else:
            numero_pjn = numero.replace('-', ' ')

        print(f"Formato PJN: {numero_pjn}")

        # Buscar expediente
        print(f"🔍 Buscando expediente {num}/{anio}...")
        exito, motivo = await buscar_expediente_por_numero(page, num, anio)

        if not exito:
            print(f"❌ Error al buscar: {motivo}")
            return {"exito": False, "error": f"Búsqueda falló: {motivo}"}

        # Obtener la primera fila de resultados
        print(f"📋 Obteniendo resultados...")
        filas = await page.query_selector_all(SEL_EXPEDIENTES.FILAS_RESULTADOS)

        if not filas:
            print(f"❌ No se encontraron resultados")
            return {"exito": False, "error": "Sin resultados"}

        # Abrir el primer expediente (click en el enlace)
        print(f"🔓 Abriendo expediente...")
        fila = filas[0]
        enlace = await fila.query_selector(SEL_EXPEDIENTES.ENLACE_EXPEDIENTE)

        if not enlace:
            print(f"❌ No se encontró enlace para abrir")
            return {"exito": False, "error": "Sin enlace"}

        await enlace.click()
        await page.wait_for_load_state("load", timeout=30000)
        await page.wait_for_timeout(2000)

        # Extraer datos del expediente abierto
        print(f"📝 Extrayendo datos...")
        datos = await extraer_datos_expediente(page)

        if not datos:
            print(f"❌ No se pudieron extraer datos")
            return {"exito": False, "error": "Extracción falló"}

        print(f"✅ Expediente procesado exitosamente")
        print(f"   Número: {datos.get('numero', 'N/A')}")
        print(f"   Carátula: {datos.get('caratula', 'N/A')[:80]}...")
        print(f"   Dependencia: {datos.get('dependencia', 'N/A')}")
        print(f"   Situación: {datos.get('situacion', 'N/A')}")

        # Actualizar el archivo JSON del expediente
        actualizar_expediente_json(numero, datos)

        return {"exito": True, "datos": datos}

    except Exception as e:
        print(f"❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        return {"exito": False, "error": str(e)}


def actualizar_expediente_json(numero_normalizado: str, datos: dict):
    """Actualiza el JSON de expedientes_sistema.json con los datos extraídos."""
    archivo_sistema = Path("data/expedientes_sistema.json")

    if not archivo_sistema.exists():
        print(f"⚠️ Archivo {archivo_sistema} no encontrado")
        return

    # Leer archivo actual
    with open(archivo_sistema, "r", encoding="utf-8") as f:
        expedientes = json.load(f)

    # Buscar y actualizar el expediente
    for exp in expedientes:
        if exp["numero"] == numero_normalizado:
            exp["caratula"] = datos.get("caratula", "No encontrada")
            exp["dependencia"] = datos.get("dependencia", "No encontrada")
            exp["situacion"] = datos.get("situacion", "No encontrada")
            print(f"📝 Actualizado {numero_normalizado} en {archivo_sistema}")
            break

    # Guardar archivo actualizado
    with open(archivo_sistema, "w", encoding="utf-8") as f:
        json.dump(expedientes, f, indent=2, ensure_ascii=False)

    print(f"💾 Archivo guardado: {archivo_sistema}")


async def main():
    print("="*80)
    print("RE-EXTRACCIÓN DE EXPEDIENTES CON SELECTORES ACTUALIZADOS")
    print("="*80)
    print(f"\nExpedientes a procesar: {len(EXPEDIENTES)}")
    for exp in EXPEDIENTES:
        print(f"  - {exp}")

    # Obtener sesión autenticada del PJN
    print("\n🔐 Iniciando sesión en el PJN...")
    async with reutilizar_sesion_async() as (page, context, browser):
        if not page:
            print("❌ No se pudo iniciar sesión en el PJN")
            return

        print("✅ Sesión iniciada correctamente\n")

        resultados = []
        exitosos = 0
        fallidos = 0

        for numero in EXPEDIENTES:
            resultado = await procesar_expediente(numero, page)
            resultados.append({
                "numero": numero,
                "resultado": resultado
            })

            if resultado.get("exito"):
                exitosos += 1
            else:
                fallidos += 1

            # Pequeña pausa entre expedientes
            await asyncio.sleep(2)

        # Resumen final
        print("\n" + "="*80)
        print("RESUMEN FINAL")
        print("="*80)
        print(f"\n✅ Exitosos: {exitosos}/{len(EXPEDIENTES)}")
        print(f"❌ Fallidos: {fallidos}/{len(EXPEDIENTES)}")

        if fallidos > 0:
            print("\nExpedientes fallidos:")
            for r in resultados:
                if not r["resultado"].get("exito"):
                    print(f"  - {r['numero']}: {r['resultado'].get('error', 'Error desconocido')}")

        print("\n" + "="*80)
        print("Los datos actualizados se han guardado en:")
        print("  - data/expedientes_sistema.json")
        print("\nREINICIA EL BACKEND para ver los cambios en el frontend:")
        print("  1. Detén el backend actual")
        print("  2. Ejecuta: python scripts/iniciar_servidores.py")
        print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
