#!/usr/bin/env python3
"""Script de prueba para verificar el filtro de entradas."""

import asyncio
import logging
import sys
from datetime import datetime, timedelta

# Configurar logging para ver todo
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)

from pjn.monitor.config import MonitorConfig
from pjn.scraping.entradas import extraer_entradas_datos
from pjn.scraping.base import obtener_pagina_autenticada

async def test_filtro():
    """Prueba el filtro de entradas con días hacia atrás."""

    print("=" * 60)
    print("TEST: Filtro de Entradas con días_atras_entradas = 7")
    print("=" * 60)

    # Cargar configuración
    config = MonitorConfig.from_file("config/monitor.json")

    print(f"\n📋 Configuración cargada:")
    print(f"   dias_atras_entradas: {config.dias_atras_entradas}")
    print(f"   fecha_desde_entradas: {config.fecha_desde_entradas}")
    print(f"   headless: {config.headless}")

    # Calcular fecha_desde
    if config.dias_atras_entradas is not None:
        hoy = datetime.now().date()
        fecha_desde_calculada = hoy - timedelta(days=config.dias_atras_entradas)
        fecha_desde = fecha_desde_calculada.strftime("%Y-%m-%d")
        print(f"\n📅 Fecha calculada:")
        print(f"   Hoy: {hoy.strftime('%d/%m/%Y')}")
        print(f"   Fecha desde: {fecha_desde_calculada.strftime('%d/%m/%Y')} ({fecha_desde})")
    else:
        fecha_desde = config.fecha_desde_entradas
        print(f"\n⚠️  No se configuró dias_atras_entradas")
        print(f"   Usando fecha_desde_entradas: {fecha_desde}")

    print(f"\n🔍 Iniciando extracción...")
    print(f"   Esto puede tomar unos segundos...")

    try:
        # Extraer entradas
        async with obtener_pagina_autenticada(headless=config.headless) as (page, _, _):
            print(f"\n✅ Sesión autenticada")
            await page.goto("https://portalpjn.pjn.gov.ar/inicio")

            print(f"🌐 Navegando a bandeja de entradas...")

            entradas = await extraer_entradas_datos(
                page,
                duplicados=False,
                incluir_tipos=("N",),
                fecha_desde=fecha_desde,
                fecha_hasta=None
            )

            print(f"\n" + "=" * 60)
            print(f"✅ EXTRACCIÓN COMPLETADA")
            print(f"=" * 60)
            print(f"\n📊 Resultados:")
            print(f"   Total entradas extraídas: {len(entradas)}")

            if entradas:
                # Mostrar rango de fechas
                fechas = [e.fecha for e in entradas if e.fecha]
                if fechas:
                    print(f"\n📅 Rango de fechas en las entradas:")
                    print(f"   Más antigua: {min(fechas)}")
                    print(f"   Más reciente: {max(fechas)}")

                # Mostrar primeras 5 entradas
                print(f"\n📝 Primeras 5 entradas:")
                for i, entrada in enumerate(entradas[:5], 1):
                    print(f"   {i}. {entrada.fecha} - {entrada.caratula[:50]}...")

                # Verificar si hay entradas fuera del rango
                if config.dias_atras_entradas and fecha_desde:
                    fecha_limite = datetime.strptime(fecha_desde, "%Y-%m-%d").date()
                    entradas_antiguas = [e for e in entradas if e.fecha and datetime.strptime(e.fecha, "%Y-%m-%d").date() < fecha_limite]

                    if entradas_antiguas:
                        print(f"\n⚠️  ADVERTENCIA: {len(entradas_antiguas)} entradas más antiguas que {fecha_desde}")
                        print(f"   Esto NO debería ocurrir con el filtro activo!")
                    else:
                        print(f"\n✅ CORRECTO: Todas las entradas son >= {fecha_desde}")

            print(f"\n" + "=" * 60)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0

if __name__ == "__main__":
    sys.exit(asyncio.run(test_filtro()))
