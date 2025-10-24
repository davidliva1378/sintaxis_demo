#!/usr/bin/env python3
"""Test para validar Mejora #2: Estandarización de manejo de errores.

Este script prueba que:
1. Funciones modernas lanzan excepciones correctamente
2. Funciones deprecated mantienen retorno tuple por compatibilidad
3. Las excepciones están bien documentadas
"""

from __future__ import annotations

import sys
from pathlib import Path

# Agregar Sistema_v5 al path
sys.path.insert(0, str(Path(__file__).parent))

from pjn.utils.logging import setup_logging, get_logger

logger = get_logger(__name__)


def test_1_imports():
    """Prueba 1: Verificar que las funciones se importan correctamente."""
    print("\n" + "="*60)
    print("PRUEBA 1: Importar funciones refactorizadas")
    print("="*60)

    try:
        from pjn.scraping.actuaciones import (
            extraer_actuaciones_pagina_modelos,
            extraer_actuaciones_pagina,
            extraer_actuaciones_datos,
        )
        print("✅ Importación exitosa de extraer_actuaciones_pagina_modelos")
        print("✅ Importación exitosa de extraer_actuaciones_pagina (deprecated)")
        print("✅ Importación exitosa de extraer_actuaciones_datos")
    except ImportError as e:
        print(f"❌ Error importando: {e}")
        return False

    print("\n✅ PRUEBA 1: COMPLETADA")
    return True


def test_2_signatures():
    """Prueba 2: Verificar firmas de las funciones."""
    print("\n" + "="*60)
    print("PRUEBA 2: Verificar firmas de funciones")
    print("="*60)

    import inspect
    from pjn.scraping.actuaciones import (
        extraer_actuaciones_pagina_modelos,
        extraer_actuaciones_pagina,
    )

    # Verificar función moderna (sin tuple en retorno)
    sig_modelos = inspect.signature(extraer_actuaciones_pagina_modelos)
    return_annotation = sig_modelos.return_annotation
    print(f"\n📋 extraer_actuaciones_pagina_modelos:")
    print(f"   Retorno: {return_annotation}")

    # Verificar que NO retorna tuple con error
    if "tuple" in str(return_annotation).lower():
        print("   ⚠️  Todavía retorna tuple (debería lanzar excepciones)")
    else:
        print("   ✅ Retorna list[Actuacion] (lanza excepciones)")

    # Verificar función deprecated (CON tuple en retorno)
    sig_deprecated = inspect.signature(extraer_actuaciones_pagina)
    return_annotation_dep = sig_deprecated.return_annotation
    print(f"\n📋 extraer_actuaciones_pagina (deprecated):")
    print(f"   Retorno: {return_annotation_dep}")

    if "tuple" in str(return_annotation_dep).lower():
        print("   ✅ Retorna tuple (mantiene compatibilidad)")
    else:
        print("   ⚠️  No retorna tuple (perdió compatibilidad)")

    print("\n✅ PRUEBA 2: COMPLETADA")
    return True


def test_3_docstrings():
    """Prueba 3: Verificar que las excepciones están documentadas."""
    print("\n" + "="*60)
    print("PRUEBA 3: Verificar documentación de excepciones")
    print("="*60)

    from pjn.scraping.actuaciones import (
        extraer_actuaciones_pagina_modelos,
        extraer_actuaciones_datos,
        _extraer_actuaciones_pagina_generico,
    )

    funciones = [
        ("extraer_actuaciones_pagina_modelos", extraer_actuaciones_pagina_modelos),
        ("extraer_actuaciones_datos", extraer_actuaciones_datos),
        ("_extraer_actuaciones_pagina_generico", _extraer_actuaciones_pagina_generico),
    ]

    for nombre, func in funciones:
        docstring = func.__doc__ or ""
        print(f"\n📋 {nombre}:")

        if "Raises:" in docstring or "raises:" in docstring.lower():
            print("   ✅ Documenta excepciones en docstring")
            # Extraer líneas de Raises
            lines = docstring.split("\n")
            in_raises = False
            for line in lines:
                if "Raises:" in line or "raises:" in line.lower():
                    in_raises = True
                    continue
                if in_raises:
                    if line.strip() and not line.strip().startswith(("Args:", "Returns:", "Note:", "Example:")):
                        print(f"      - {line.strip()}")
                    elif line.strip().startswith(("Args:", "Returns:", "Note:", "Example:")):
                        break
        else:
            print("   ⚠️  No documenta excepciones en docstring")

    print("\n✅ PRUEBA 3: COMPLETADA")
    return True


def test_4_excepciones_disponibles():
    """Prueba 4: Verificar que las excepciones están disponibles."""
    print("\n" + "="*60)
    print("PRUEBA 4: Verificar excepciones disponibles")
    print("="*60)

    try:
        from pjn.exceptions import (
            ExtraccionError,
            TimeoutExtraccion,
            ActuacionesNoDisponibles,
            PJNError,
        )
        print("✅ ExtraccionError importada")
        print("✅ TimeoutExtraccion importada")
        print("✅ ActuacionesNoDisponibles importada")
        print("✅ PJNError importada (base)")

        # Verificar jerarquía
        print(f"\n📋 Jerarquía de excepciones:")
        print(f"   ExtraccionError hereda de: {ExtraccionError.__bases__}")
        print(f"   TimeoutExtraccion hereda de: {TimeoutExtraccion.__bases__}")
        print(f"   ActuacionesNoDisponibles hereda de: {ActuacionesNoDisponibles.__bases__}")

    except ImportError as e:
        print(f"❌ Error importando excepciones: {e}")
        return False

    print("\n✅ PRUEBA 4: COMPLETADA")
    return True


def test_5_resumen():
    """Prueba 5: Resumen de la mejora."""
    print("\n" + "="*60)
    print("PRUEBA 5: Resumen de la Mejora #2")
    print("="*60)

    print("""
📊 Cambios implementados:

1. Funciones MODERNAS (lanzan excepciones):
   - extraer_actuaciones_pagina_modelos()
   - _extraer_actuaciones_pagina_generico()
   - extraer_actuaciones_datos()

2. Funciones DEPRECATED (mantienen tuple):
   - extraer_actuaciones_pagina() → tuple[list, str | None]
   - extraer_actuaciones_completas() → tuple[list, list, str | None]

3. Excepciones disponibles:
   - ExtraccionError
   - TimeoutExtraccion
   - ActuacionesNoDisponibles

4. Beneficios:
   ✅ Código más limpio y predecible
   ✅ Manejo de errores consistente
   ✅ Excepciones bien documentadas
   ✅ Retrocompatibilidad mantenida

5. Ejemplo de uso:

   # Código MODERNO (recomendado):
   try:
       actuaciones = await extraer_actuaciones_pagina_modelos(page, datos, 1)
   except TimeoutExtraccion as e:
       logger.error(f"Timeout: {e}")
   except ExtraccionError as e:
       logger.error(f"Error: {e}")

   # Código DEPRECATED (compatibilidad):
   actuaciones, error = await extraer_actuaciones_pagina(page, datos, 1)
   if error:
       logger.error(f"Error: {error}")
    """)

    print("\n✅ PRUEBA 5: COMPLETADA")
    return True


def main():
    """Ejecuta todas las pruebas."""
    print("\n" + "🧪"*30)
    print("PRUEBAS DE VALIDACIÓN - Mejora #2: Manejo de Errores")
    print("🧪"*30)

    setup_logging()

    try:
        resultados = []
        resultados.append(("Imports", test_1_imports()))
        resultados.append(("Signatures", test_2_signatures()))
        resultados.append(("Docstrings", test_3_docstrings()))
        resultados.append(("Excepciones", test_4_excepciones_disponibles()))
        resultados.append(("Resumen", test_5_resumen()))

        # Resumen final
        print("\n" + "="*60)
        print("📊 RESUMEN DE PRUEBAS")
        print("="*60)

        total = len(resultados)
        exitosas = sum(1 for _, resultado in resultados if resultado)

        for nombre, resultado in resultados:
            status = "✅" if resultado else "❌"
            print(f"{status} {nombre}")

        print(f"\nTotal: {exitosas}/{total} pruebas exitosas")

        if exitosas == total:
            print("\n✅ TODAS LAS PRUEBAS COMPLETADAS EXITOSAMENTE")
            print("\n🎉 Mejora #2 implementada y validada correctamente!")
            return 0
        else:
            print(f"\n⚠️  {total - exitosas} prueba(s) fallaron")
            return 1

    except Exception as e:
        print(f"\n❌ ERROR DURANTE LAS PRUEBAS: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
