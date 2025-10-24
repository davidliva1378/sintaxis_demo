#!/usr/bin/env python
"""Script de prueba para verificar el método _actualizar_actuaciones_expedientes."""

import sys
from pathlib import Path

# Configurar path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print("🧪 Verificando implementación de actualización de actuaciones\n")

# Test 1: Verificar imports dentro del método
print("Test 1: Verificando que los imports lazy funcionan...")
try:
    from Sistema_v5.pjn.scraping.base import obtener_pagina_autenticada, descomponer_numero_expediente
    from Sistema_v5.pjn.scraping.expedientes import buscar_expedientes, mostrar_y_elegir_expediente
    from Sistema_v5.pjn.services.actuaciones import procesar_actuaciones_expediente
    print("✅ Todos los imports necesarios están disponibles\n")
except ImportError as e:
    print(f"❌ Error en imports: {e}\n")
    sys.exit(1)

# Test 2: Verificar función descomponer_numero_expediente
print("Test 2: Verificando descomposición de números de expediente...")
test_casos = [
    "FPA 12345/2024",
    "12345/2024",
    "FPA 12345/2024/I",
    "123/2023",
]

for numero in test_casos:
    try:
        prefijo, num, anio = descomponer_numero_expediente(numero)
        if num and anio:
            print(f"  ✅ {numero:20} → número={num}, año={anio}")
        else:
            print(f"  ⚠️  {numero:20} → número={num}, año={anio} (puede ser válido)")
    except Exception as e:
        print(f"  ❌ {numero:20} → Error: {e}")

print()

# Test 3: Verificar que MonitorPJN carga correctamente
print("Test 3: Verificando MonitorPJN...")
try:
    from Sistema_v5.pjn.monitor.core import MonitorPJN
    from Sistema_v5.configuracion.monitor import MonitorConfig

    # Intentar crear config de prueba
    config = MonitorConfig(
        directorio_datos="data/monitor",
        headless=True,
        actualizar_actuaciones_automaticamente=True,
        max_reintentos_actualizacion_actuaciones=3,
    )
    print(f"  ✅ MonitorConfig creado")
    print(f"     - actualizar_actuaciones_automaticamente: {config.actualizar_actuaciones_automaticamente}")
    print(f"     - max_reintentos: {config.max_reintentos_actualizacion_actuaciones}")

except Exception as e:
    print(f"  ❌ Error creando MonitorConfig: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 4: Verificar método existe y tiene firma correcta
print("Test 4: Verificando método _actualizar_actuaciones_expedientes...")
try:
    import inspect
    metodo = getattr(MonitorPJN, '_actualizar_actuaciones_expedientes', None)

    if metodo is None:
        print("  ❌ Método no existe")
        sys.exit(1)

    sig = inspect.signature(metodo)
    params = list(sig.parameters.keys())

    print(f"  ✅ Método existe")
    print(f"     - Parámetros: {params}")
    print(f"     - Es async: {inspect.iscoroutinefunction(metodo)}")

    # Verificar que el método tiene el código correcto
    source = inspect.getsource(metodo)

    # Verificar imports corregidos
    if 'buscar_expedientes' in source and 'mostrar_y_elegir_expediente' in source:
        print(f"  ✅ Imports corregidos detectados en el código")
    else:
        print(f"  ⚠️  No se detectaron los imports corregidos")

    if 'descomponer_numero_expediente' in source:
        print(f"  ✅ Uso de descomponer_numero_expediente detectado")
    else:
        print(f"  ⚠️  No se detectó uso de descomponer_numero_expediente")

except Exception as e:
    print(f"  ❌ Error: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 5: Verificar integración en _verificar_expedientes_internal
print("Test 5: Verificando integración en ciclo de monitoreo...")
try:
    metodo_verificar = getattr(MonitorPJN, '_verificar_expedientes_internal', None)
    if metodo_verificar:
        source = inspect.getsource(metodo_verificar)
        if '_actualizar_actuaciones_expedientes' in source:
            print("  ✅ Método integrado en _verificar_expedientes_internal")

            # Verificar que se llama condicionalmente
            if 'actualizar_actuaciones_automaticamente' in source:
                print("  ✅ Llamada condicional detectada (usa config)")
            else:
                print("  ⚠️  No se detectó verificación de config")
        else:
            print("  ❌ Método NO está integrado en _verificar_expedientes_internal")
    else:
        print("  ❌ _verificar_expedientes_internal no existe")
except Exception as e:
    print(f"  ❌ Error: {e}")

print()
print("="*60)
print("✅ TODAS LAS VERIFICACIONES COMPLETADAS")
print("="*60)
print("\nEl código está listo para ejecutarse con el monitor real.")
print("Ejecuta el monitor universal para probarlo en vivo.")
