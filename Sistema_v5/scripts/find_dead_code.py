#!/usr/bin/env python3
"""Script para encontrar código potencialmente muerto."""

import ast
import os
from pathlib import Path
from collections import defaultdict

def find_all_definitions(directory):
    """Encuentra todas las definiciones de funciones y clases."""
    definitions = defaultdict(list)

    for py_file in Path(directory).rglob("*.py"):
        if "test" in str(py_file) or "__pycache__" in str(py_file):
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(py_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    name = node.name
                    if not name.startswith('_'):  # Solo funciones públicas
                        definitions[name].append(str(py_file))
                elif isinstance(node, ast.ClassDef):
                    name = node.name
                    definitions[name].append(str(py_file))
        except Exception as e:
            print(f"Error parsing {py_file}: {e}")

    return definitions

def find_all_usages(directory, name):
    """Encuentra todos los usos de un nombre."""
    usages = []

    for py_file in Path(directory).rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue

        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Contar ocurrencias (excluyendo la definición)
            if f"def {name}(" in content or f"class {name}" in content:
                # Archivo de definición
                count = content.count(name) - 1  # -1 por la definición
            else:
                count = content.count(name)

            if count > 0:
                usages.append((str(py_file), count))
        except Exception:
            pass

    return usages

def main():
    pjn_dir = Path(__file__).parent.parent / "pjn"

    print("🔍 Buscando definiciones...\n")
    definitions = find_all_definitions(pjn_dir)

    print(f"📊 Encontradas {len(definitions)} definiciones públicas\n")
    print("="*80)

    potentially_dead = []

    for name, files in sorted(definitions.items()):
        usages = find_all_usages(pjn_dir, name)
        usage_count = sum(count for _, count in usages)

        # Consideramos "potencialmente muerto" si solo tiene 1-2 usos
        # (que podrían ser solo la definición y __all__)
        if usage_count <= 2:
            potentially_dead.append((name, files, usages, usage_count))

    print(f"\n⚠️  Elementos con pocos usos (potencialmente no utilizados): {len(potentially_dead)}\n")
    print("="*80)

    for name, def_files, usages, count in potentially_dead[:30]:  # Top 30
        print(f"\n📦 {name}")
        print(f"   Definido en: {', '.join(def_files)}")
        print(f"   Usos totales: {count}")
        if usages:
            for file, uses in usages[:3]:  # Top 3 archivos
                file_short = str(file).replace(str(pjn_dir), "pjn")
                print(f"     - {file_short}: {uses} uso(s)")

if __name__ == "__main__":
    main()
