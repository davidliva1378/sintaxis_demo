"""Script para probar y actualizar selectores del PJN.

Este script:
1. Se conecta al PJN con credenciales
2. Abre un expediente conocido
3. Prueba todos los selectores importantes
4. Reporta cuáles funcionan y cuáles no
5. Opcionalmente abre el navegador para inspección manual

Uso:
    # Configurar credenciales
    export PJN_USER="tu_usuario"
    export PJN_PASSWORD="tu_password"

    # Ejecutar
    python scripts/test_selectores_pjn.py

    # Para inspección manual, descomentar await page.pause() al final
"""

import asyncio
import os
import sys
from pathlib import Path

# Agregar directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from pjn.auto_login import reutilizar_sesion_async
from pjn.selectores import SEL_EXPEDIENTES, SEL_ACTUACIONES

# Expediente de prueba conocido
EXPEDIENTE_TEST = {
    "numero": "024925",
    "anio": "2018",
    "prefijo": "FPA"
}


async def test_selector(page, nombre, selector, contexto="página actual"):
    """Prueba un selector y reporta si funciona."""
    try:
        elemento = await page.query_selector(selector)
        if elemento:
            texto = await elemento.inner_text()
            print(f"  ✓ {nombre}: OK")
            print(f"    Selector: {selector}")
            print(f"    Texto encontrado: {texto[:80]}...")
            return True
        else:
            print(f"  ✗ {nombre}: NO ENCONTRADO")
            print(f"    Selector: {selector}")
            print(f"    Contexto: {contexto}")
            return False
    except Exception as e:
        print(f"  ✗ {nombre}: ERROR - {e}")
        print(f"    Selector: {selector}")
        return False


async def probar_selectores_alternativos(page, nombre_campo):
    """Intenta encontrar selectores alternativos usando diferentes estrategias."""
    print(f"\n  🔍 Buscando selectores alternativos para {nombre_campo}...")

    # Estrategia 1: Buscar todos los elementos con IDs que contengan "expediente"
    ids_expediente = await page.evaluate("""
        () => {
            const elementos = document.querySelectorAll('[id*="expediente"]');
            return Array.from(elementos).map(el => ({
                id: el.id,
                texto: el.innerText.substring(0, 50),
                tag: el.tagName
            }));
        }
    """)

    if ids_expediente:
        print(f"\n    Elementos con 'expediente' en el ID:")
        for elem in ids_expediente[:10]:  # Mostrar solo primeros 10
            if elem['texto'].strip():
                print(f"      #{elem['id']} ({elem['tag']}): {elem['texto']}...")

    # Estrategia 2: Buscar por texto visible si conocemos el patrón
    patrones_busqueda = {
        "Carátula": ["detail.*cover", "caratula", "cover"],
        "Dependencia": ["detail.*depend", "dependencia", "depend"],
        "Jurisdicción": ["detail.*jurisd", "detail.*camera", "jurisdiccion"],
        "Situación": ["detail.*situa", "situacion", "situation"]
    }

    if nombre_campo in patrones_busqueda:
        for patron in patrones_busqueda[nombre_campo]:
            elementos = await page.evaluate(f"""
                (patron) => {{
                    const regex = new RegExp(patron, 'i');
                    const elementos = document.querySelectorAll('[id]');
                    return Array.from(elementos)
                        .filter(el => regex.test(el.id))
                        .map(el => ({{
                            id: el.id,
                            texto: el.innerText.substring(0, 50)
                        }}));
                }}
            """, patron)

            if elementos:
                print(f"\n    Elementos con patrón '{patron}':")
                for elem in elementos[:5]:
                    if elem['texto'].strip():
                        print(f"      #{elem['id']}: {elem['texto']}...")


async def main():
    print("=" * 80)
    print("TEST DE SELECTORES DEL PORTAL JUDICIAL NACIONAL")
    print("=" * 80)

    # --- OPCIÓN 1: Hardcodear credenciales (NO RECOMENDADO - solo para testing rápido) ---
    # Descomentar estas líneas y agregar tus credenciales:
    os.environ["PJN_USER"] = "20213071662"
    os.environ["PJN_PASSWORD"] = "Surrey_1970"
    # IMPORTANTE: NO HAGAS COMMIT de este archivo con credenciales hardcodeadas!

    # --- OPCIÓN 2: Pedir credenciales interactivamente ---
    usuario = os.getenv("PJN_USER")
    password = os.getenv("PJN_PASSWORD")

    if not usuario or not password:
        print("\n🔐 Credenciales del Portal Judicial Nacional")
        print("-" * 80)

        if not usuario:
            usuario = input("Usuario (CUIL): ").strip()
            if usuario:
                os.environ["PJN_USER"] = usuario

        if not password:
            from getpass import getpass
            password = getpass("Contraseña: ").strip()
            if password:
                os.environ["PJN_PASSWORD"] = password

    # Verificar que tenemos credenciales
    if not os.getenv("PJN_USER") or not os.getenv("PJN_PASSWORD"):
        print("\n❌ No se proporcionaron credenciales válidas")
        return

    print(f"\n📋 Usuario: {os.getenv('PJN_USER')}")
    print(f"📋 Expediente de prueba: {EXPEDIENTE_TEST['prefijo']} {EXPEDIENTE_TEST['numero']}/{EXPEDIENTE_TEST['anio']}")

    async with reutilizar_sesion_async() as (page, context, browser):
        if not page:
            print("\n❌ No se pudo iniciar sesión en el PJN")
            return

        print("\n1. ✅ Login exitoso al PJN\n")

        # Esperar un momento para que la página termine de cargar completamente
        await page.wait_for_timeout(2000)

        print("=" * 80)
        print("INSTRUCCIONES PARA INSPECCIÓN MANUAL")
        print("=" * 80)
        print("\n📋 PASOS A SEGUIR:")
        print("\n1. Se abrirá el Playwright Inspector y el navegador")
        print("2. En el navegador, presiona F12 para abrir DevTools")
        print("3. Usa el selector de elementos (Ctrl+Shift+C o el ícono de flecha)")
        print("4. Navega manualmente al expediente que quieras inspeccionar:")
        print(f"   - Busca el expediente: {EXPEDIENTE_TEST['prefijo']} {EXPEDIENTE_TEST['numero']}/{EXPEDIENTE_TEST['anio']}")
        print("   - O cualquier otro expediente que tengas")
        print("\n5. SELECTORES A BUSCAR:")
        print("   ├─ Carátula del expediente")
        print("   ├─ Dependencia/Juzgado")
        print("   ├─ Jurisdicción")
        print("   ├─ Situación del expediente")
        print("   └─ Número del expediente")
        print("\n6. Para cada elemento:")
        print("   a) Click en el elemento con el inspector")
        print("   b) En DevTools, click derecho → Copy → Copy selector")
        print("   c) Anota el selector copiado")
        print("\n7. Cuando termines, presiona 'Resume' en el Playwright Inspector")
        print("\n" + "=" * 80)

        # ACTIVADO: Inspección manual con Playwright Inspector
        print("\n⏸️  Pausando para inspección manual...")
        print("   Usa el Playwright Inspector para probar selectores")
        print("   Presiona F12 en el navegador para abrir DevTools")
        print("   Presiona el botón 'Resume' en el Inspector cuando termines")
        await page.pause()


if __name__ == "__main__":
    asyncio.run(main())
