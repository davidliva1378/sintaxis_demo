#!/usr/bin/env python3
"""Script para encontrar constantes mágicas (magic numbers y magic strings)."""

import ast
import re
from pathlib import Path
from collections import defaultdict

class MagicConstantFinder(ast.NodeVisitor):
    """Visitor que encuentra constantes mágicas en el código."""

    def __init__(self, filename):
        self.filename = filename
        self.magic_numbers = []
        self.magic_strings = []

    def visit_Num(self, node):
        """Visita nodos numéricos (Python <3.8)."""
        self._check_number(node.n, node.lineno)
        self.generic_visit(node)

    def visit_Constant(self, node):
        """Visita nodos constantes (Python ≥3.8)."""
        if isinstance(node.value, (int, float)):
            self._check_number(node.value, node.lineno)
        elif isinstance(node.value, str):
            self._check_string(node.value, node.lineno)
        self.generic_visit(node)

    def _check_number(self, value, lineno):
        """Verifica si un número es 'mágico'."""
        # Ignorar números obvios
        if value in (0, 1, -1, 2):
            return

        # Ignorar números muy grandes (probablemente timestamps o IDs)
        if abs(value) > 1_000_000_000:
            return

        self.magic_numbers.append((lineno, value))

    def _check_string(self, value, lineno):
        """Verifica si un string es 'mágico'."""
        # Ignorar strings vacíos, muy cortos o muy largos
        if not value or len(value) < 3 or len(value) > 200:
            return

        # Ignorar mensajes de log simples
        if value.strip() in ('', ' ', '\n', '\t'):
            return

        # Buscar strings que parecen importantes:
        # - Selectores CSS
        # - Timeouts/delays
        # - Rutas de archivo
        # - Códigos de estado

        patterns = [
            r'^[a-z0-9\-_\.#\[\]:\(\)\s]+$',  # Selectores CSS
            r'\.(?:pdf|json|csv|txt|xml)$',    # Extensiones
            r'^[A-Z_]+$',                       # CONSTANTES_ESTILO
            r'limite_|error_|timeout_',         # Códigos de estado
        ]

        for pattern in patterns:
            if re.search(pattern, value, re.IGNORECASE):
                self.magic_strings.append((lineno, value))
                break

def analyze_file(filepath):
    """Analiza un archivo en busca de constantes mágicas."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            tree = ast.parse(content, filename=str(filepath))
    except Exception as e:
        return None, None

    finder = MagicConstantFinder(str(filepath))
    finder.visit(tree)

    return finder.magic_numbers, finder.magic_strings

def main():
    pjn_dir = Path(__file__).parent.parent / "pjn"

    print("🔍 Buscando constantes mágicas...\n")
    print("="*80)

    all_numbers = defaultdict(list)
    all_strings = defaultdict(list)

    for py_file in pjn_dir.rglob("*.py"):
        if "__pycache__" in str(py_file) or "test" in str(py_file):
            continue

        numbers, strings = analyze_file(py_file)
        if numbers:
            for lineno, value in numbers:
                all_numbers[value].append((str(py_file), lineno))
        if strings:
            for lineno, value in strings:
                all_strings[value].append((str(py_file), lineno))

    # Mostrar números mágicos más comunes
    print(f"\n📊 Números mágicos encontrados: {len(all_numbers)}\n")
    print("Top 20 números más repetidos:")
    print("-" * 80)

    sorted_numbers = sorted(all_numbers.items(), key=lambda x: len(x[1]), reverse=True)
    for value, locations in sorted_numbers[:20]:
        print(f"\n{value} - Usado {len(locations)} vez/veces")
        for filepath, lineno in locations[:3]:  # Top 3 ubicaciones
            short_path = filepath.replace(str(pjn_dir.parent), "")
            print(f"  {short_path}:{lineno}")
        if len(locations) > 3:
            print(f"  ... y {len(locations) - 3} más")

    # Mostrar strings mágicos más comunes
    print(f"\n\n📝 Strings mágicos encontrados: {len(all_strings)}\n")
    print("Top 20 strings más repetidos:")
    print("-" * 80)

    sorted_strings = sorted(all_strings.items(), key=lambda x: len(x[1]), reverse=True)
    for value, locations in sorted_strings[:20]:
        if len(value) > 60:
            display_value = value[:60] + "..."
        else:
            display_value = value
        print(f"\n'{display_value}' - Usado {len(locations)} vez/veces")
        for filepath, lineno in locations[:3]:
            short_path = filepath.replace(str(pjn_dir.parent), "")
            print(f"  {short_path}:{lineno}")
        if len(locations) > 3:
            print(f"  ... y {len(locations) - 3} más")

if __name__ == "__main__":
    main()
