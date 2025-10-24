#!/usr/bin/env python3
"""
Script para generar inventario completo de funciones y clases del proyecto.
"""
import ast
import os
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass


@dataclass
class FunctionInfo:
    name: str
    type: str  # 'function', 'async_function', 'method', 'async_method', 'class'
    module: str
    signature: str
    docstring: str | None
    is_private: bool
    decorators: List[str]
    lineno: int


class InventoryGenerator:
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.inventory: Dict[str, List[FunctionInfo]] = {}

    def extract_signature(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        """Extrae la signatura de una función."""
        args = []

        # Argumentos posicionales
        for arg in node.args.args:
            arg_str = arg.arg
            if arg.annotation:
                arg_str += f": {ast.unparse(arg.annotation)}"
            args.append(arg_str)

        # Valores por defecto
        defaults = node.args.defaults
        if defaults:
            # Los defaults se aplican de derecha a izquierda
            for i, default in enumerate(defaults):
                idx = len(args) - len(defaults) + i
                if idx >= 0 and idx < len(args):
                    args[idx] += f" = {ast.unparse(default)}"

        # *args
        if node.args.vararg:
            vararg = f"*{node.args.vararg.arg}"
            if node.args.vararg.annotation:
                vararg += f": {ast.unparse(node.args.vararg.annotation)}"
            args.append(vararg)

        # **kwargs
        if node.args.kwarg:
            kwarg = f"**{node.args.kwarg.arg}"
            if node.args.kwarg.annotation:
                kwarg += f": {ast.unparse(node.args.kwarg.annotation)}"
            args.append(kwarg)

        signature = f"({', '.join(args)})"

        # Return type
        if node.returns:
            signature += f" -> {ast.unparse(node.returns)}"

        return signature

    def extract_decorators(self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef) -> List[str]:
        """Extrae los decoradores de un nodo."""
        decorators = []
        for decorator in node.decorator_list:
            decorators.append(ast.unparse(decorator))
        return decorators

    def extract_docstring(self, node) -> str | None:
        """Extrae el docstring de un nodo."""
        return ast.get_docstring(node)

    def analyze_file(self, file_path: Path) -> List[FunctionInfo]:
        """Analiza un archivo Python y extrae funciones y clases."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read(), filename=str(file_path))
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []

        module_path = str(file_path.relative_to(self.base_path)).replace('/', '.').replace('.py', '')
        items = []

        for node in ast.walk(tree):
            # Clases
            if isinstance(node, ast.ClassDef):
                info = FunctionInfo(
                    name=node.name,
                    type='class',
                    module=module_path,
                    signature='',
                    docstring=self.extract_docstring(node),
                    is_private=node.name.startswith('_'),
                    decorators=self.extract_decorators(node),
                    lineno=node.lineno
                )
                items.append(info)

            # Funciones (tanto top-level como métodos)
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                is_async = isinstance(node, ast.AsyncFunctionDef)

                # Determinar si es método o función
                is_method = False
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.ClassDef):
                        if node in ast.walk(parent):
                            is_method = True
                            break

                func_type = 'async_method' if is_async and is_method else \
                           'async_function' if is_async else \
                           'method' if is_method else \
                           'function'

                info = FunctionInfo(
                    name=node.name,
                    type=func_type,
                    module=module_path,
                    signature=self.extract_signature(node),
                    docstring=self.extract_docstring(node),
                    is_private=node.name.startswith('_'),
                    decorators=self.extract_decorators(node),
                    lineno=node.lineno
                )
                items.append(info)

        return items

    def generate_inventory(self, target_dir: str = "pjn"):
        """Genera el inventario completo."""
        target_path = self.base_path / target_dir

        for py_file in sorted(target_path.rglob("*.py")):
            if "__pycache__" in str(py_file):
                continue

            items = self.analyze_file(py_file)
            if items:
                module_path = str(py_file.relative_to(self.base_path)).replace('/', '.').replace('.py', '')
                self.inventory[module_path] = items

    def generate_markdown(self) -> str:
        """Genera el inventario en formato Markdown."""
        lines = []
        lines.append("# 📋 Inventario Completo de Funciones - Sistema_v5")
        lines.append("")
        lines.append("**Generado automáticamente**")
        lines.append(f"**Versión:** 5.6")
        lines.append("**Última actualización:** 17 de octubre, 2025")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("## 📖 Índice de Módulos")
        lines.append("")

        # Generar índice
        for module_path in sorted(self.inventory.keys()):
            module_name = module_path.split('.')[-1]
            anchor = module_path.replace('.', '').replace('_', '-')
            lines.append(f"- [{module_path}](#{anchor})")

        lines.append("")
        lines.append("---")
        lines.append("")

        # Generar contenido por módulo
        for module_path in sorted(self.inventory.keys()):
            items = self.inventory[module_path]

            lines.append(f"## `{module_path}`")
            lines.append("")

            # Agrupar por tipo
            classes = [i for i in items if i.type == 'class' and not i.is_private]
            public_funcs = [i for i in items if i.type in ('function', 'async_function') and not i.is_private]
            private_funcs = [i for i in items if i.type in ('function', 'async_function') and i.is_private]

            # Clases
            if classes:
                lines.append("### Clases")
                lines.append("")
                for cls in sorted(classes, key=lambda x: x.name):
                    lines.append(f"#### `{cls.name}`")
                    lines.append("")
                    if cls.decorators:
                        lines.append(f"**Decoradores:** `{', '.join(cls.decorators)}`")
                        lines.append("")
                    if cls.docstring:
                        # Primera línea del docstring
                        first_line = cls.docstring.split('\n')[0].strip()
                        lines.append(f"**Descripción:** {first_line}")
                        lines.append("")
                    lines.append(f"**Ubicación:** `{module_path}:{cls.lineno}`")
                    lines.append("")

                    # Métodos de la clase
                    methods = [i for i in items if i.type in ('method', 'async_method') and not i.is_private]
                    if methods:
                        lines.append("**Métodos públicos:**")
                        lines.append("")
                        for method in sorted(methods, key=lambda x: x.name):
                            async_marker = "async " if method.type == 'async_method' else ""
                            lines.append(f"##### `{async_marker}{method.name}{method.signature}`")
                            lines.append("")
                            if method.decorators:
                                lines.append(f"**Decoradores:** `{', '.join(method.decorators)}`")
                                lines.append("")
                            if method.docstring:
                                lines.append("**Documentación:**")
                                lines.append("")
                                lines.append("```")
                                lines.append(method.docstring)
                                lines.append("```")
                                lines.append("")
                            else:
                                lines.append("*Sin documentación*")
                                lines.append("")
                            lines.append(f"**Ubicación:** `{module_path}:{method.lineno}`")
                            lines.append("")
                        lines.append("")

            # Funciones públicas
            if public_funcs:
                lines.append("### Funciones Públicas")
                lines.append("")
                for func in sorted(public_funcs, key=lambda x: x.name):
                    async_marker = "async " if func.type == 'async_function' else ""
                    lines.append(f"#### `{async_marker}{func.name}{func.signature}`")
                    lines.append("")
                    if func.decorators:
                        lines.append(f"**Decoradores:** `{', '.join(func.decorators)}`")
                        lines.append("")
                    if func.docstring:
                        # Documentación completa (sin límite de líneas)
                        lines.append("**Documentación:**")
                        lines.append("")
                        lines.append("```")
                        lines.append(func.docstring)
                        lines.append("```")
                        lines.append("")
                    else:
                        lines.append("*Sin documentación*")
                        lines.append("")
                    lines.append(f"**Ubicación:** `{module_path}:{func.lineno}`")
                    lines.append("")

            # Funciones privadas (solo lista)
            if private_funcs:
                lines.append("### Funciones Privadas")
                lines.append("")
                for func in sorted(private_funcs, key=lambda x: x.name):
                    async_marker = "async " if func.type == 'async_function' else ""
                    lines.append(f"- `{async_marker}{func.name}{func.signature}` (línea {func.lineno})")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Estadísticas
        lines.append("## 📊 Estadísticas")
        lines.append("")

        total_modules = len(self.inventory)
        total_classes = sum(1 for items in self.inventory.values() for i in items if i.type == 'class')
        total_public_funcs = sum(1 for items in self.inventory.values() for i in items
                                 if i.type in ('function', 'async_function') and not i.is_private)
        total_private_funcs = sum(1 for items in self.inventory.values() for i in items
                                  if i.type in ('function', 'async_function') and i.is_private)
        total_async = sum(1 for items in self.inventory.values() for i in items
                         if 'async' in i.type)

        lines.append(f"- **Módulos totales:** {total_modules}")
        lines.append(f"- **Clases:** {total_classes}")
        lines.append(f"- **Funciones públicas:** {total_public_funcs}")
        lines.append(f"- **Funciones privadas:** {total_private_funcs}")
        lines.append(f"- **Funciones async:** {total_async}")
        lines.append(f"- **Total items:** {total_classes + total_public_funcs + total_private_funcs}")
        lines.append("")

        return '\n'.join(lines)


def main():
    """Función principal."""
    base_path = Path(__file__).parent.parent
    generator = InventoryGenerator(base_path)

    print("Generando inventario...")
    generator.generate_inventory(target_dir="pjn")

    print("Generando Markdown...")
    markdown = generator.generate_markdown()

    output_file = base_path / "docs" / "INVENTARIO_FUNCIONES.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"✅ Inventario generado en: {output_file}")

    # Mostrar estadísticas
    print("\n📊 Estadísticas:")
    total_modules = len(generator.inventory)
    total_items = sum(len(items) for items in generator.inventory.values())
    print(f"  - Módulos: {total_modules}")
    print(f"  - Items totales: {total_items}")


if __name__ == "__main__":
    main()
