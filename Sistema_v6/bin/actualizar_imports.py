#!/usr/bin/env python3
"""
Script para actualizar imports de módulos migrados a Sistema_v6.

Este script actualiza automáticamente los imports en todos los archivos .py
del directorio Sistema_v6 para reflejar la nueva estructura de directorios.
"""

import re
from pathlib import Path
from typing import List, Tuple


# Mapeo de imports antiguos a nuevos
IMPORT_MAPPINGS = [
    # core.* -> Sistema_v6.*
    (r"from core\.flujo_inicial", "from Sistema_v6.extractor_inicial"),
    (r"from core\.gestion_expedientes", "from Sistema_v6.gestion_expedientes"),
    (r"from core\.utils", "from Sistema_v6.utils"),
    (r"from core\.modulos_monitor\.expedientes_modular", "from Sistema_v6.pjn.monitor"),

    # web.* -> Sistema_v6.pjn.*
    (r"from web\.auto_login", "from Sistema_v6.pjn.auto_login"),
    (r"from web\.navegador", "from Sistema_v6.pjn.navegador"),
    (r"from web\.funciones_navegador_async", "from Sistema_v6.pjn.funciones_navegador_async"),

    # panel_pjn.* -> Sistema_v6.configuracion.*
    (r"from panel_pjn\.acciones_pjn\.urls_pjn", "from Sistema_v6.configuracion.urls"),

    # Imports de extraccion_inicial que ahora son extractor_inicial
    (r"from Sistema_v6.extractor_inicial.extraccion_inicial import", "from Sistema_v6.extractor_inicial.extraccion_inicial import"),
]


def actualizar_imports_en_archivo(archivo: Path) -> Tuple[bool, int]:
    """
    Actualiza los imports en un archivo Python.

    Args:
        archivo: Ruta al archivo Python

    Returns:
        Tupla (modificado, num_cambios) donde:
        - modificado: Si el archivo fue modificado
        - num_cambios: Número de cambios realizados
    """
    try:
        with open(archivo, "r", encoding="utf-8") as f:
            contenido = f.read()
    except Exception as e:
        print(f"❌ Error leyendo {archivo}: {e}")
        return False, 0

    contenido_original = contenido
    num_cambios = 0

    # Aplicar cada mapeo
    for patron, reemplazo in IMPORT_MAPPINGS:
        nuevo_contenido, n = re.subn(patron, reemplazo, contenido)
        if n > 0:
            contenido = nuevo_contenido
            num_cambios += n

    # Si hubo cambios, guardar archivo
    if contenido != contenido_original:
        try:
            with open(archivo, "w", encoding="utf-8") as f:
                f.write(contenido)
            return True, num_cambios
        except Exception as e:
            print(f"❌ Error escribiendo {archivo}: {e}")
            return False, 0

    return False, 0


def actualizar_todos_los_imports(directorio_base: Path) -> None:
    """
    Actualiza imports en todos los archivos .py del directorio.

    Args:
        directorio_base: Directorio raíz donde buscar archivos
    """
    archivos_python = list(directorio_base.rglob("*.py"))

    print(f"🔍 Encontrados {len(archivos_python)} archivos Python")
    print(f"📁 Directorio base: {directorio_base}")
    print()

    archivos_modificados = 0
    total_cambios = 0

    for archivo in archivos_python:
        # Saltar __pycache__ y archivos de backup
        if "__pycache__" in str(archivo) or archivo.name.endswith(".bak"):
            continue

        modificado, num_cambios = actualizar_imports_en_archivo(archivo)

        if modificado:
            archivos_modificados += 1
            total_cambios += num_cambios
            print(f"✅ {archivo.relative_to(directorio_base)} ({num_cambios} cambios)")

    print()
    print("=" * 60)
    print(f"✅ Actualización completada")
    print(f"   Archivos modificados: {archivos_modificados}/{len(archivos_python)}")
    print(f"   Total de cambios: {total_cambios}")
    print("=" * 60)


def main():
    """Función principal."""
    # Obtener directorio de Sistema_v6
    script_dir = Path(__file__).resolve().parent
    sistema_v6_dir = script_dir.parent

    print("=" * 60)
    print("ACTUALIZACIÓN DE IMPORTS - Sistema v6")
    print("=" * 60)
    print()

    actualizar_todos_los_imports(sistema_v6_dir)


if __name__ == "__main__":
    main()
