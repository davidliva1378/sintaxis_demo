#!/usr/bin/env python3
"""Analiza imports no utilizados en el código."""

import ast
from pathlib import Path
from collections import defaultdict

def analyze_file(filepath):
    """Analiza un archivo Python para encontrar imports no utilizados."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content, filename=str(filepath))
    except Exception as e:
        return None

    # Recopilar imports
    imports = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                name = alias.asname if alias.asname else alias.name
                imports[name] = alias.name
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == '*':
                    continue
                name = alias.asname if alias.asname else alias.name
                imports[name] = f"{node.module}.{alias.name}" if node.module else alias.name

    # Buscar uso de cada import en el contenido
    unused = []
    for name, full_name in imports.items():
        # Contar usos (excluyendo la línea de import)
        uses = content.count(name)
        import_uses = content.count(f"import {name}") + content.count(f"import {full_name}")
        actual_uses = uses - import_uses

        # Si solo aparece en TYPE_CHECKING, se considera "usado" de forma especial
        if "TYPE_CHECKING" in content and f"if TYPE_CHECKING:" in content:
            # Es normal que algunos imports solo estén en TYPE_CHECKING
            pass
        elif actual_uses <= 1:  # <= 1 porque puede aparecer 1 vez en __all__
            unused.append((name, full_name, actual_uses))

    return unused

def main():
    pjn_dir = Path(__file__).parent.parent / "pjn"

    print("🔍 Analizando imports no utilizados...\n")
    print("="*80)

    all_unused = []

    for py_file in pjn_dir.rglob("*.py"):
        if "__pycache__" in str(py_file) or "test" in str(py_file):
            continue

        unused = analyze_file(py_file)
        if unused:
            for name, full_name, uses in unused:
                all_unused.append((str(py_file), name, full_name, uses))

    # Agrupar por archivo
    by_file = defaultdict(list)
    for filepath, name, full_name, uses in all_unused:
        by_file[filepath].append((name, full_name, uses))

    print(f"\n📊 Archivos con posibles imports no utilizados: {len(by_file)}\n")

    for filepath in sorted(by_file.keys())[:20]:  # Top 20
        short_path = filepath.replace(str(pjn_dir.parent), "")
        unused_list = by_file[filepath]
        if len(unused_list) > 0:
            print(f"\n📄 {short_path}")
            for name, full_name, uses in unused_list[:10]:  # Top 10 per file
                print(f"   - {name} (from {full_name}) - {uses} uso(s) real(es)")

if __name__ == "__main__":
    main()
