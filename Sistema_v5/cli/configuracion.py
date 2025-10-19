# -*- coding: utf-8 -*-
"""CLI integral para gestionar ``SystemConfig`` en Sistema_v5.

Este módulo reemplaza al antiguo ``scripts/configurar_sistema.py`` (interfaz
Tk) con un asistente de línea de comandos que permite:

* Visualizar la configuración actual agrupada por dominios.
* Ejecutar un asistente interactivo (wizard) que recorre *todas* las opciones y
  permite modificarlas en caliente.
* Actualizar campos específicos mediante ``campo=valor`` desde la consola.
* Generar plantillas de variables de entorno y backups puntuales.

Ejemplos de uso::

    # Ejecutar asistente interactivo con todas las categorías
    python -m Sistema_v5.cli.configuracion --config config/sistema.json

    # Mostrar configuración actual en formato tabla
    python -m Sistema_v5.cli.configuracion show

    # Editar campos directamente
    python -m Sistema_v5.cli.configuracion set modo_monitor=laboral nivel_log=DEBUG

    # Crear backup manual
    python -m Sistema_v5.cli.configuracion backup --destino backups/manual.json

El módulo puede invocarse mediante ``python -m`` o ``python Sistema_v5/cli/configuracion.py``.
"""

from __future__ import annotations

import argparse
import json
import sys
import unicodedata
from dataclasses import asdict
from pathlib import Path
from textwrap import indent
from typing import Any, Iterable

if __name__ == "__main__" and __package__ is None:  # pragma: no cover - compatibilidad script directo
    sys.path.append(str(Path(__file__).resolve().parents[2]))
    __package__ = "Sistema_v5.cli"

from ..pjn.system_config import (
    ENV_FIELD_MAP,
    BOOL_FIELDS,
    INT_FIELDS,
    LIST_FIELDS,
    LOWER_FIELDS,
    UPPER_FIELDS,
    OPTIONAL_STR_FIELDS,
    SystemConfig,
)

# ---------------------------------------------------------------------------
# Definiciones de campos y metadatos
# ---------------------------------------------------------------------------

FIELD_GROUPS: dict[str, list[str]] = {
    "directorios": [
        "directorio_extraccion_inicial",
        "directorio_extracciones_temporales",
        "directorio_expedientes_base",
        "directorio_comparaciones",
        "directorio_reportes",
        "directorio_logs",
        "directorio_backups",
        "directorio_cache",
        "directorio_descargas",
        "directorio_monitor_datos",
    ],
    "monitoreo": [
        "modo_monitor",
        "headless",
        "intervalos_laboral_expedientes",
        "intervalos_laboral_entradas",
        "intervalos_no_laboral_expedientes",
        "intervalos_no_laboral_entradas",
        "dias_laborales",
        "hora_inicio",
        "hora_fin",
        "verificar_entradas",
        "verificar_expedientes",
        "notificar_nuevas_entradas",
        "notificar_cambios_expedientes",
        "notificar_errores",
        "comparacion_automatica",
        "fecha_corte_expedientes",
        "fecha_desde_entradas",
        "fecha_hasta_entradas",
        "fecha_desde_expedientes",
        "fecha_hasta_expedientes",
    ],
    "extraccion": [
        "max_paginas_expedientes",
        "timeout_default",
        "timeout_login",
        "timeout_descarga",
        "max_reintentos_expedientes",
        "espera_reintentos_expedientes",
        "max_reintentos_entradas",
        "espera_reintentos_entradas",
        "max_reintentos_descarga",
    ],
    "comparacion": [
        "modo_comparacion",
        "generar_reportes_automaticos",
        "formato_reportes",
    ],
    "sistema": [
        "fecha_inicio_sistema",
        "fecha_ultimo_backup",
        "intervalo_backup_automatico",
        "retener_historico_dias",
        "nivel_log",
        "max_tamaño_log_mb",
        "rotacion_logs",
        "guardar_sesion",
        "duracion_sesion_horas",
        "limite_memoria_mb",
        "max_archivos_cache",
    ],
}

FIELD_METADATA: dict[str, dict[str, Any]] = {
    "directorio_extraccion_inicial": {
        "label": "Extracción inicial",
        "help": "Fuente base para comparaciones",
    },
    "directorio_extracciones_temporales": {
        "label": "Extracciones temporales",
        "help": "Trabajos en progreso",
    },
    "directorio_expedientes_base": {
        "label": "Expedientes base",
        "help": "Carpetas por expediente",
    },
    "directorio_comparaciones": {
        "label": "Comparaciones",
        "help": "Resultados de difs",
    },
    "directorio_reportes": {
        "label": "Reportes",
        "help": "Salidas automáticas",
    },
    "directorio_logs": {
        "label": "Logs",
        "help": "Archivos de logging",
    },
    "directorio_backups": {
        "label": "Backups",
        "help": "Respaldos de config",
    },
    "directorio_cache": {
        "label": "Cache",
        "help": "Datos temporales",
    },
    "directorio_descargas": {
        "label": "Descargas",
        "help": "PDFs bajados",
    },
    "directorio_monitor_datos": {
        "label": "Datos monitor",
        "help": "Estado y registros",
    },
    "modo_monitor": {
        "label": "Modo monitor",
        "choices": ["automatico", "laboral", "no_laboral"],
    },
    "headless": {
        "label": "Browser headless",
        "help": "Ejecutar sin UI",
    },
    "intervalos_laboral_expedientes": {
        "label": "Intervalo laboral expedientes (min)",
    },
    "intervalos_laboral_entradas": {
        "label": "Intervalo laboral entradas (min)",
    },
    "intervalos_no_laboral_expedientes": {
        "label": "Intervalo no laboral expedientes (min)",
    },
    "intervalos_no_laboral_entradas": {
        "label": "Intervalo no laboral entradas (min)",
    },
    "dias_laborales": {
        "label": "Días laborales",
        "help": "Separar por coma",
    },
    "hora_inicio": {
        "label": "Hora inicio laboral",
    },
    "hora_fin": {
        "label": "Hora fin laboral",
    },
    "verificar_entradas": {
        "label": "Verificar entradas",
    },
    "verificar_expedientes": {
        "label": "Verificar expedientes",
    },
    "notificar_nuevas_entradas": {
        "label": "Notificar nuevas entradas",
    },
    "notificar_cambios_expedientes": {
        "label": "Notificar cambios",
    },
    "notificar_errores": {
        "label": "Notificar errores",
    },
    "comparacion_automatica": {
        "label": "Comparación automática",
    },
    "fecha_corte_expedientes": {
        "label": "Fecha corte expedientes",
        "help": "YYYY-MM-DD o vacío",
    },
    "fecha_desde_entradas": {
        "label": "Fecha desde entradas",
    },
    "fecha_hasta_entradas": {
        "label": "Fecha hasta entradas",
    },
    "fecha_desde_expedientes": {
        "label": "Fecha desde expedientes",
    },
    "fecha_hasta_expedientes": {
        "label": "Fecha hasta expedientes",
    },
    "max_paginas_expedientes": {
        "label": "Máx. páginas expedientes",
    },
    "timeout_default": {
        "label": "Timeout default (ms)",
    },
    "timeout_login": {
        "label": "Timeout login (ms)",
    },
    "timeout_descarga": {
        "label": "Timeout descarga (ms)",
    },
    "max_reintentos_expedientes": {
        "label": "Reintentos expedientes",
    },
    "espera_reintentos_expedientes": {
        "label": "Espera reintentos expedientes (s)",
    },
    "max_reintentos_entradas": {
        "label": "Reintentos entradas",
    },
    "espera_reintentos_entradas": {
        "label": "Espera reintentos entradas (s)",
    },
    "max_reintentos_descarga": {
        "label": "Reintentos descarga",
    },
    "modo_comparacion": {
        "label": "Modo comparación",
        "choices": ["automatico", "manual", "deshabilitado"],
    },
    "generar_reportes_automaticos": {
        "label": "Reportes automáticos",
    },
    "formato_reportes": {
        "label": "Formato reportes",
        "choices": ["json", "excel", "pdf"],
    },
    "fecha_inicio_sistema": {
        "label": "Fecha inicio sistema",
        "help": "Autogenerada, se puede resetear",
    },
    "fecha_ultimo_backup": {
        "label": "Fecha último backup",
    },
    "intervalo_backup_automatico": {
        "label": "Intervalo backup (días)",
    },
    "retener_historico_dias": {
        "label": "Retención histórico (días)",
    },
    "nivel_log": {
        "label": "Nivel log",
        "choices": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    },
    "max_tamaño_log_mb": {
        "label": "Tamaño log (MB)",
    },
    "rotacion_logs": {
        "label": "Rotación logs",
    },
    "guardar_sesion": {
        "label": "Guardar sesión",
    },
    "duracion_sesion_horas": {
        "label": "Duración sesión (h)",
    },
    "limite_memoria_mb": {
        "label": "Límite memoria (MB)",
    },
    "max_archivos_cache": {
        "label": "Máx. archivos cache",
    },
}

CHOICE_FIELDS: dict[str, set[str]] = {
    field: set(meta["choices"])
    for field, meta in FIELD_METADATA.items()
    if "choices" in meta
}

TRUE_VALUES = {"1", "true", "t", "yes", "y", "si", "sí", "on", "s"}
FALSE_VALUES = {"0", "false", "f", "no", "n", "off"}

# ---------------------------------------------------------------------------
# Utilidades de parsing y formateo
# ---------------------------------------------------------------------------


def parse_field_value(field: str, raw_value: str) -> Any:
    """Convierte la entrada de texto a un valor tipado."""

    value = raw_value.strip()

    if field in OPTIONAL_STR_FIELDS and value.lower() in {"", "none", "null", "-"}:
        return None

    if field in BOOL_FIELDS:
        lowered = value.lower()
        if lowered in TRUE_VALUES:
            return True
        if lowered in FALSE_VALUES:
            return False
        raise ValueError(
            f"Valor inválido para {field!r}. Usa sí/no, true/false, 1/0"
        )

    if field in INT_FIELDS:
        try:
            return int(value)
        except ValueError as exc:  # pragma: no cover - validación simple
            raise ValueError(f"{field} debe ser un número entero") from exc

    if field in LIST_FIELDS:
        if not value:
            return []
        return [item.strip() for item in value.split(",") if item.strip()]

    if field in LOWER_FIELDS:
        lowered = value.lower()
        _validate_choice(field, lowered)
        return lowered

    if field in UPPER_FIELDS:
        uppered = value.upper()
        _validate_choice(field, uppered)
        return uppered

    _validate_choice(field, value)
    return value


def _validate_choice(field: str, value: str) -> None:
    choices = CHOICE_FIELDS.get(field)
    if choices and value not in choices:
        raise ValueError(
            f"Valor inválido para {field!r}. Opciones: {', '.join(sorted(choices))}"
        )


def format_value(value: Any) -> str:
    """Formatea valores para representación en tabla."""

    if isinstance(value, bool):
        return "sí" if value else "no"
    if isinstance(value, list):
        return ", ".join(map(str, value)) or "(vacío)"
    if value is None:
        return "(sin definir)"
    return str(value)


# ---------------------------------------------------------------------------
# Operaciones principales
# ---------------------------------------------------------------------------


def load_config(path: Path) -> SystemConfig:
    try:
        return SystemConfig.from_file(path)
    except FileNotFoundError:
        return SystemConfig()


def run_wizard(config: SystemConfig, *, categories: Iterable[str] | None = None) -> dict[str, Any]:
    """Ejecuta el asistente interactivo para todas las categorías."""

    print("=" * 72)
    print("ASISTENTE DE CONFIGURACIÓN DEL SISTEMA PJN")
    print("=" * 72)
    print("Pulsa Enter para conservar el valor actual. Escribe '-' para limpiar campos opcionales.")
    print()

    updates: dict[str, Any] = {}
    selected = set(categories) if categories else None

    for group, fields in FIELD_GROUPS.items():
        if selected and group not in selected:
            continue

        print(f"[{group.upper()}]")
        for field in fields:
            current = getattr(config, field)
            descriptor = FIELD_METADATA.get(field, {})
            label = descriptor.get("label", field)
            help_text = descriptor.get("help")

            print(f"- {label}")
            if help_text:
                print(indent(help_text, "    "))
            print(indent(f"Actual: {format_value(current)}", "    "))

            while True:
                try:
                    raw = input(f"    Nuevo valor para {field} (Enter para mantener): ")
                except KeyboardInterrupt:
                    print("\nInterrupción detectada. Guardando cambios parciales...")
                    return updates

                if not raw.strip():
                    print("    (sin cambios)")
                    break

                try:
                    parsed = parse_field_value(field, raw)
                except ValueError as exc:
                    print(indent(f"⚠️  {exc}", "    "))
                    continue

                updates[field] = parsed
                print(indent(f"✔️  Nuevo valor: {format_value(parsed)}", "    "))
                break

            print()

    return updates


def apply_updates(config: SystemConfig, updates: dict[str, Any]) -> SystemConfig:
    if not updates:
        return config

    data = config.to_dict()
    data.update(updates)
    return SystemConfig(**data)


def save_config(config: SystemConfig, path: Path, *, create_backup: bool = True) -> None:
    if create_backup and path.exists():
        backup_path = path.with_suffix(path.suffix + ".bak")
        config_actual = SystemConfig.from_file(path)
        config_actual.to_file(backup_path)
        print(f"Backup creado en {backup_path}")

    config.to_file(path)
    print(f"Configuración guardada en {path}")


# ---------------------------------------------------------------------------
# Comandos CLI
# ---------------------------------------------------------------------------


def cmd_show(config: SystemConfig, args: argparse.Namespace) -> None:
    if args.format == "json":
        print(json.dumps(asdict(config), indent=2, ensure_ascii=False))
        return

    if args.format == "env":
        for field, env_suffix in ENV_FIELD_MAP.items():
            valor = getattr(config, field)
            print(f"{env_suffix}={format_value(valor)}")
        return

    # Formato tabla
    for group, fields in FIELD_GROUPS.items():
        print("=" * 72)
        print(group.upper())
        print("=" * 72)
        for field in fields:
            descriptor = FIELD_METADATA.get(field, {})
            label = descriptor.get("label", field)
            print(f"{label:<40} {format_value(getattr(config, field))}")
        print()


def cmd_set(config: SystemConfig, args: argparse.Namespace, path: Path) -> None:
    updates: dict[str, Any] = {}
    available_fields = set(config.to_dict())

    for pair in args.pairs:
        if "=" not in pair:
            raise SystemExit(f"Entrada inválida '{pair}'. Usa campo=valor")
        field, raw_value = pair.split("=", 1)
        field = field.strip()
        raw_value = raw_value.strip()
        field = resolve_field_name(field, available_fields)

        try:
            updates[field] = parse_field_value(field, raw_value)
        except ValueError as exc:
            raise SystemExit(str(exc))

    new_config = apply_updates(config, updates)
    save_config(new_config, path, create_backup=not args.no_backup)


def cmd_wizard(config: SystemConfig, args: argparse.Namespace, path: Path) -> None:
    categories = args.categorias
    updates = run_wizard(config, categories=categories)
    if not updates:
        print("No se realizaron cambios. Nada que guardar.")
        return

    new_config = apply_updates(config, updates)

    if not args.auto_confirm:
        print()
        print("Resumen de cambios:")
        for field, value in updates.items():
            label = FIELD_METADATA.get(field, {}).get("label", field)
            print(f"- {label}: {format_value(getattr(config, field))} -> {format_value(value)}")
        confirm = input("¿Guardar cambios? [s/N]: ").strip().lower()
        if confirm not in TRUE_VALUES:
            print("Cambios descartados.")
            return

    save_config(new_config, path, create_backup=not args.no_backup)


def cmd_env_template() -> None:
    print("Variables de entorno disponibles (prefijo SISTEMA_ por defecto):")
    for field, env_suffix in ENV_FIELD_MAP.items():
        print(f"  SISTEMA_{env_suffix} -> {field}")


def resolve_field_name(name: str, available: Iterable[str]) -> str:
    if name in available:
        return name

    normalized = _strip_accents(name)
    for candidate in available:
        if _strip_accents(candidate) == normalized:
            return candidate

    raise SystemExit(f"Campo desconocido: {name}")


def _strip_accents(value: str) -> str:
    return "".join(
        char for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )


def cmd_backup(config: SystemConfig, args: argparse.Namespace) -> None:
    destino = Path(args.destino) if args.destino else None
    backup_path = config.hacer_backup(destino)
    print(f"Backup generado en {backup_path}")


# ---------------------------------------------------------------------------
# Punto de entrada principal
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Asistente CLI para gestionar config/sistema.json",
    )
    parser.add_argument(
        "--config",
        default="config/sistema.json",
        type=Path,
        help="Ruta al archivo de configuración",
    )
    subparsers = parser.add_subparsers(dest="command")

    show_parser = subparsers.add_parser("show", help="Mostrar configuración actual")
    show_parser.add_argument(
        "--format",
        choices={"table", "json", "env"},
        default="table",
        help="Formato de salida",
    )

    set_parser = subparsers.add_parser("set", help="Actualizar campos puntuales")
    set_parser.add_argument("pairs", nargs="+", help="Parámetros como campo=valor")
    set_parser.add_argument(
        "--no-backup",
        action="store_true",
        help="No crear backups automáticos",
    )

    wizard_parser = subparsers.add_parser(
        "wizard", help="Asistente interactivo para todas las opciones"
    )
    wizard_parser.add_argument(
        "--categorias",
        nargs="*",
        choices=sorted(FIELD_GROUPS.keys()),
        help="Limitar el asistente a categorías específicas",
    )
    wizard_parser.add_argument(
        "--auto-confirm",
        action="store_true",
        help="Guardar sin pedir confirmación final",
    )
    wizard_parser.add_argument(
        "--no-backup",
        action="store_true",
        help="No crear backups automáticos",
    )

    subparsers.add_parser("env", help="Listar variables de entorno disponibles")

    backup_parser = subparsers.add_parser("backup", help="Crear backup manual")
    backup_parser.add_argument(
        "--destino",
        help="Ruta del archivo de backup (opcional)",
    )

    parser.add_argument(
        "--version",
        action="version",
        version="Sistema_v5 configurador CLI 1.0",
    )

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    config_path: Path = args.config
    config = load_config(config_path)

    command = args.command or "wizard"

    if command == "show":
        cmd_show(config, args)
    elif command == "set":
        cmd_set(config, args, config_path)
    elif command == "wizard":
        cmd_wizard(config, args, config_path)
    elif command == "env":
        cmd_env_template()
    elif command == "backup":
        cmd_backup(config, args)
    else:
        parser.print_help()


if __name__ == "__main__":  # pragma: no cover - CLI directo
    main(sys.argv[1:])
