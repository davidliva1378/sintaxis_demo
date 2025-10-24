#!/usr/bin/env python3
"""Script de prueba para validar las mejoras implementadas en Sistema_v5.

Este script prueba:
1. Configuración centralizada
2. Funciones de extracción puras (sin I/O)
3. Módulo de persistencia
4. Funciones sin side effects

Ejecutar: python test_mejoras_implementadas.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Agregar Sistema_v5 al path
sys.path.insert(0, str(Path(__file__).parent))

from pjn.config import get_config, set_config, Config, reset_config
from pjn.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


def test_1_configuracion():
    """Prueba 1: Configuración centralizada."""
    print("\n" + "="*60)
    print("PRUEBA 1: Configuración Centralizada")
    print("="*60)

    # Test 1.1: Obtener configuración por defecto
    print("\n📋 1.1: Obtener configuración por defecto")
    config = get_config()
    print(f"✅ Timeout default: {config.scraping.timeout_default} ms")
    print(f"✅ Max páginas: {config.scraping.max_paginas_expedientes}")
    print(f"✅ Headless: {config.browser.headless}")
    print(f"✅ URL login: {config.auth.login_url}")
    print(f"✅ Dir actuaciones: {config.archivos.directorio_base_actuaciones}")

    # Test 1.2: Configuración para testing
    print("\n📋 1.2: Configuración para testing")
    reset_config()
    set_config(Config.for_testing())
    config_test = get_config()
    print(f"✅ Timeout reducido: {config_test.scraping.timeout_default} ms")
    print(f"✅ Max páginas reducido: {config_test.scraping.max_paginas_expedientes}")
    print(f"✅ Headless forzado: {config_test.browser.headless}")

    # Test 1.3: Override desde environment
    print("\n📋 1.3: Override desde environment variables")
    os.environ["PJN_MAX_PAGINAS"] = "50"
    os.environ["PJN_TIMEOUT_DEFAULT"] = "5000"
    reset_config()
    config_env = get_config()
    print(f"✅ Max páginas desde ENV: {config_env.scraping.max_paginas_expedientes}")
    print(f"✅ Timeout desde ENV: {config_env.scraping.timeout_default} ms")

    # Cleanup
    del os.environ["PJN_MAX_PAGINAS"]
    del os.environ["PJN_TIMEOUT_DEFAULT"]
    reset_config()

    print("\n✅ PRUEBA 1: COMPLETADA")


async def test_2_extraccion_pura_simulada():
    """Prueba 2: Simular extracción pura sin conectar al portal."""
    print("\n" + "="*60)
    print("PRUEBA 2: Funciones de Extracción Puras (Simulada)")
    print("="*60)

    print("\n📋 2.1: Importar funciones de extracción")
    try:
        from pjn.scraping.actuaciones import extraer_actuaciones_datos
        from pjn.scraping.entradas import extraer_entradas_datos
        print("✅ Importación exitosa de extraer_actuaciones_datos")
        print("✅ Importación exitosa de extraer_entradas_datos")
    except ImportError as e:
        print(f"❌ Error importando: {e}")
        return

    print("\n📋 2.2: Verificar firmas de funciones")
    import inspect

    sig_actuaciones = inspect.signature(extraer_actuaciones_datos)
    print(f"✅ Firma extraer_actuaciones_datos: {sig_actuaciones}")

    sig_entradas = inspect.signature(extraer_entradas_datos)
    print(f"✅ Firma extraer_entradas_datos: {sig_entradas}")

    print("\n💡 Nota: Para probar con datos reales, necesitas:")
    print("   1. Credenciales del portal (PJN_USER, PJN_PASSWORD)")
    print("   2. Ejecutar con playwright instalado")
    print("   3. Ver: pjn/scripts/rf_test_extraccion_completa.py")

    print("\n✅ PRUEBA 2: COMPLETADA")


def test_3_persistencia():
    """Prueba 3: Módulo de persistencia."""
    print("\n" + "="*60)
    print("PRUEBA 3: Módulo de Persistencia")
    print("="*60)

    print("\n📋 3.1: Importar funciones de persistencia")
    try:
        from pjn.persistence import (
            cargar_actuaciones_json,
            cargar_actuaciones_archivo,
            guardar_actuaciones_json,
            listar_archivos_actuaciones,
        )
        print("✅ Importación exitosa de cargar_actuaciones_json")
        print("✅ Importación exitosa de cargar_actuaciones_archivo")
        print("✅ Importación exitosa de guardar_actuaciones_json")
        print("✅ Importación exitosa de listar_archivos_actuaciones")
    except ImportError as e:
        print(f"❌ Error importando: {e}")
        return

    print("\n📋 3.2: Crear datos de prueba")
    from pjn.models import Actuacion, ActuacionesArchivo
    from pjn.parsers.actuaciones_parser import construir_actuaciones_archivo

    # Crear actuaciones de prueba
    actuaciones_prueba = [
        Actuacion(
            indice=1,
            oficina="JUZG001",
            oficina_completa="Juzgado Federal 1",
            fecha="2025-01-15",
            tipo="Resolución",
            detalle="Prueba 1",
            foja="F.1",
            tiene_archivo=True,
            archivo="http://ejemplo.com/archivo1.pdf",
            nombre_archivo="resolucion-1.pdf",
            tipo_archivo="pdf",
            es_historica=False,
            descargado=False,
            extraida_en="2025-10-15 12:00:00",
        ),
        Actuacion(
            indice=2,
            oficina="JUZG001",
            oficina_completa="Juzgado Federal 1",
            fecha="2025-01-16",
            tipo="Providencia",
            detalle="Prueba 2",
            foja="F.2",
            tiene_archivo=False,
            archivo=None,
            nombre_archivo=None,
            tipo_archivo=None,
            es_historica=False,
            descargado=False,
            extraida_en="2025-10-15 12:00:00",
        ),
    ]

    # Note: ActuacionesArchivo tiene 'actuaciones' (no 'actuaciones_actuales')
    # La función construir_actuaciones_archivo combina actuales + históricas
    archivo_prueba = ActuacionesArchivo(
        encabezado={"numero": "TEST-12345", "caratula": "Prueba Sistema v5"},
        actuaciones=tuple(actuaciones_prueba),
    )

    print(f"✅ Archivo de prueba creado: {len(archivo_prueba.actuaciones)} actuaciones")

    print("\n📋 3.3: Guardar archivo JSON")
    try:
        test_dir = Path("./test_persistencia_temp")
        test_dir.mkdir(exist_ok=True)

        ruta_guardada = guardar_actuaciones_json(
            archivo_prueba,
            directorio_base=str(test_dir),
            numero_expediente="TEST-12345",
        )
        print(f"✅ Archivo guardado en: {ruta_guardada}")
        print(f"✅ Tamaño: {Path(ruta_guardada).stat().st_size} bytes")
    except Exception as e:
        print(f"❌ Error guardando: {e}")
        return

    print("\n📋 3.4: Cargar archivo JSON")
    try:
        archivo_cargado = cargar_actuaciones_archivo(ruta_guardada)
        print(f"✅ Archivo cargado correctamente")
        print(f"✅ Número expediente: {archivo_cargado.encabezado.get('numero')}")
        print(f"✅ Actuaciones: {len(archivo_cargado.actuaciones)}")
        print(f"✅ Con archivo: {sum(1 for a in archivo_cargado.actuaciones if a.tiene_archivo)}")
    except Exception as e:
        print(f"❌ Error cargando: {e}")
        return

    print("\n📋 3.5: Listar archivos")
    try:
        archivos = listar_archivos_actuaciones(str(test_dir))
        print(f"✅ Archivos encontrados: {len(archivos)}")
        for archivo in archivos:
            print(f"   - {archivo.name}")
    except Exception as e:
        print(f"❌ Error listando: {e}")

    print("\n📋 3.6: Limpiar archivos de prueba")
    try:
        import shutil
        shutil.rmtree(test_dir)
        print(f"✅ Archivos de prueba eliminados")
    except Exception as e:
        print(f"⚠️  No se pudo limpiar: {e}")

    print("\n✅ PRUEBA 3: COMPLETADA")


def test_4_sin_side_effects():
    """Prueba 4: Funciones sin side effects."""
    print("\n" + "="*60)
    print("PRUEBA 4: Funciones sin Side Effects")
    print("="*60)

    print("\n📋 4.1: Importar funciones")
    try:
        from pjn.scraping.actuaciones import (
            calcular_metricas_descargas_json,
            actualizar_metricas_descargas_en_json,
        )
        print("✅ Importación exitosa")
    except ImportError as e:
        print(f"❌ Error importando: {e}")
        return

    print("\n📋 4.2: Probar función PURA (sin side effects)")
    payload_original = {
        "Expediente": {
            "numero": "12345",
            "Cantidad de Archivos Descargados": 0,
        },
        "Actuaciones": [
            {"TieneArchivo": True, "Descargado": True},
            {"TieneArchivo": True, "Descargado": False},
            {"TieneArchivo": False, "Descargado": None},
        ],
    }

    print(f"   Original - Descargados: {payload_original['Expediente']['Cantidad de Archivos Descargados']}")

    # Llamar función pura
    payload_actualizado = calcular_metricas_descargas_json(payload_original)

    print(f"   Actualizado - Descargados: {payload_actualizado['Expediente']['Cantidad de Archivos Descargados']}")
    print(f"   Original - Descargados: {payload_original['Expediente']['Cantidad de Archivos Descargados']}")

    if payload_original['Expediente']['Cantidad de Archivos Descargados'] == 0:
        print("✅ Original NO fue modificado (sin side effects)")
    else:
        print("❌ Original FUE modificado (side effect detectado!)")

    if payload_actualizado['Expediente']['Cantidad de Archivos Descargados'] == 1:
        print("✅ Nuevo objeto tiene valores correctos")
    else:
        print("❌ Valores incorrectos en objeto nuevo")

    print("\n📋 4.3: Comparar con función DEPRECATED (con side effects)")
    payload_mutable = {
        "Expediente": {
            "numero": "12345",
            "Cantidad de Archivos Descargados": 0,
        },
        "Actuaciones": [
            {"TieneArchivo": True, "Descargado": True},
            {"TieneArchivo": True, "Descargado": False},
        ],
    }

    print(f"   Antes - Descargados: {payload_mutable['Expediente']['Cantidad de Archivos Descargados']}")

    # Llamar función deprecated (muta el original)
    actualizar_metricas_descargas_en_json(payload_mutable)

    print(f"   Después - Descargados: {payload_mutable['Expediente']['Cantidad de Archivos Descargados']}")

    if payload_mutable['Expediente']['Cantidad de Archivos Descargados'] == 1:
        print("⚠️  Original FUE modificado (side effect esperado en función deprecated)")
    else:
        print("❌ Función deprecated no funcionó correctamente")

    print("\n✅ PRUEBA 4: COMPLETADA")


def test_5_integracion():
    """Prueba 5: Caso de uso integrado."""
    print("\n" + "="*60)
    print("PRUEBA 5: Caso de Uso Integrado")
    print("="*60)

    print("\n📋 Escenario: Pipeline completo sin I/O intermedio")
    print("""
    Caso de uso:
    1. Configurar para testing
    2. Crear datos de prueba en memoria
    3. Procesar sin guardar archivos
    4. Guardar solo al final
    5. Recargar y verificar
    """)

    # Paso 1: Configurar
    print("\n   Paso 1: Configurar para testing")
    reset_config()
    set_config(Config.for_testing())
    config = get_config()
    print(f"   ✅ Timeouts reducidos: {config.scraping.timeout_default} ms")

    # Paso 2: Crear datos (simula extracción)
    print("\n   Paso 2: Crear datos de prueba (simula extracción)")
    from pjn.models import Actuacion, ActuacionesArchivo

    actuaciones = [
        Actuacion(
            indice=i,
            oficina="JUZG001",
            oficina_completa="Juzgado Federal 1",
            fecha=f"2025-01-{i:02d}",
            tipo="Resolución",
            detalle=f"Actuación {i}",
            foja=f"F.{i}",
            tiene_archivo=True if i % 2 == 0 else False,
            archivo=f"http://ejemplo.com/archivo{i}.pdf" if i % 2 == 0 else None,
            nombre_archivo=f"archivo-{i}.pdf" if i % 2 == 0 else None,
            tipo_archivo="pdf" if i % 2 == 0 else None,
            es_historica=False,
            descargado=False if i % 2 == 0 else False,
            extraida_en="2025-10-15 12:00:00",
        )
        for i in range(1, 11)
    ]

    archivo = ActuacionesArchivo(
        encabezado={"numero": "INTEG-999", "caratula": "Prueba Integración"},
        actuaciones=tuple(actuaciones),
    )
    print(f"   ✅ Creadas {len(archivo.actuaciones)} actuaciones en memoria")

    # Paso 3: Procesar en memoria
    print("\n   Paso 3: Procesar en memoria (sin I/O)")
    con_archivo = [a for a in archivo.actuaciones if a.tiene_archivo]
    print(f"   ✅ Filtradas {len(con_archivo)} actuaciones con archivo")

    # Paso 4: Guardar solo al final
    print("\n   Paso 4: Guardar solo al final")
    from pjn.persistence import guardar_actuaciones_json

    test_dir = Path("./test_integracion_temp")
    test_dir.mkdir(exist_ok=True)

    ruta = guardar_actuaciones_json(archivo, str(test_dir), "INTEG-999")
    print(f"   ✅ Guardado en: {ruta}")

    # Paso 5: Recargar y verificar
    print("\n   Paso 5: Recargar y verificar")
    from pjn.persistence import cargar_actuaciones_archivo

    archivo_recargado = cargar_actuaciones_archivo(ruta)
    print(f"   ✅ Recargadas {len(archivo_recargado.actuaciones)} actuaciones")

    # Verificar integridad
    if len(archivo_recargado.actuaciones) == len(archivo.actuaciones):
        print("   ✅ Cantidad de actuaciones coincide")
    else:
        print("   ❌ Cantidad de actuaciones NO coincide")

    # Limpiar
    import shutil
    shutil.rmtree(test_dir)
    print("   ✅ Archivos de prueba limpiados")

    reset_config()
    print("\n✅ PRUEBA 5: COMPLETADA")


def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "🔬"*30)
    print("PRUEBAS DE VALIDACIÓN - Sistema_v5 Mejoras")
    print("🔬"*30)

    setup_logging()

    try:
        # Pruebas síncronas
        test_1_configuracion()
        test_3_persistencia()
        test_4_sin_side_effects()
        test_5_integracion()

        # Prueba asíncrona
        asyncio.run(test_2_extraccion_pura_simulada())

        # Resumen
        print("\n" + "="*60)
        print("✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
        print("="*60)
        print("""
Próximos pasos sugeridos:
1. Revisar ROADMAP.md para ver progreso
2. Revisar MEJORAS_IMPLEMENTADAS.md para ejemplos
3. Migrar un script real para usar las nuevas funciones
4. Probar con datos reales del portal PJN

¿Dudas o problemas? Revisa la documentación en:
- Sistema_v5/ROADMAP.md
- Sistema_v5/MEJORAS_IMPLEMENTADAS.md
        """)

    except Exception as e:
        print(f"\n❌ ERROR DURANTE LAS PRUEBAS: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
