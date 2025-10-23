#!/usr/bin/env python3
"""Script de extracción inicial v2.0 con filtrado avanzado.

Este script implementa el nuevo flujo de extracción inicial:
1. Extraer listado completo con MonitorPJN
2. Filtrado avanzado mediante GUI
3. Generación de directorios por expediente
4. Extracción completa con manejo inteligente de errores

Uso (desde directorio Sistema_v5):
    python ejecutar_extraccion_inicial_v2.py
    python ejecutar_extraccion_inicial_v2.py --headless
    python ejecutar_extraccion_inicial_v2.py --config ../config/sistema.json
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox
import logging

# Configurar paths relativos a Sistema_v5
SISTEMA_V5_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SISTEMA_V5_DIR.parent

# Agregar raíz del proyecto al path para que Sistema_v5 sea un paquete
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Sistema_v5.configuracion.core import SystemConfig
from Sistema_v5.pjn.monitor import MonitorPJN, MonitorConfig
from Sistema_v5.pjn.utils.logging import setup_logging, get_logger
from Sistema_v5.extractor_inicial import mostrar_filtros_avanzados
from Sistema_v5.extractor_inicial.batch_processor import ExtractorCompletoBatch
from Sistema_v5.extractor_inicial.ui.progress_window import ProgressWindow
from Sistema_v5.gestor_directorios import GestorDirectoriosExpedientes


logger = get_logger(__name__)


def parse_args() -> dict[str, object]:
    """Parsea argumentos de línea de comandos."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extracción inicial de expedientes PJN v2.0"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="../config/sistema.json",
        help="Ruta al archivo de configuración del sistema (relativa a Sistema_v5)",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Ejecutar Playwright en modo headless (sin navegador visible)",
    )
    parser.add_argument(
        "--no-filtros",
        action="store_true",
        help="Omitir paso de filtrado (procesar todos los expedientes)",
    )
    parser.add_argument(
        "--no-adjuntos",
        action="store_true",
        help="No descargar archivos adjuntos de actuaciones",
    )
    parser.add_argument(
        "--umbral-errores",
        type=int,
        default=5,
        help="Número de errores consecutivos antes de pausar (default: 5)",
    )
    parser.add_argument(
        "--desde-json",
        type=str,
        default=None,
        help="Usar un JSON ya extraído (salta Fase 1). Ruta relativa a Sistema_v5",
    )

    args = parser.parse_args()
    return vars(args)


async def fase_1_extraer_listado(
    config: SystemConfig,
    headless: bool,
) -> tuple[list, Path]:
    """Fase 1: Extraer listado completo usando MonitorPJN."""
    logger.info("=" * 60)
    logger.info("FASE 1: EXTRACCIÓN DEL LISTADO COMPLETO")
    logger.info("=" * 60)

    monitor_config = MonitorConfig.from_system_config(config)
    monitor_config.headless = headless
    monitor = MonitorPJN(monitor_config)

    logger.info("🚀 Iniciando extracción del listado con MonitorPJN...")
    expedientes, json_path = await monitor.extraer_listado_inicial(exportar_csv=True)

    logger.info(f"✅ Extraídos {len(expedientes)} expedientes")
    logger.info(f"📄 Guardado en: {json_path}")

    return expedientes, json_path


def fase_2_filtrar_expedientes(
    expedientes: list,
    omitir_filtros: bool,
) -> list | None:
    """Fase 2: Filtrado avanzado mediante GUI."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("FASE 2: FILTRADO Y SELECCIÓN")
    logger.info("=" * 60)

    if omitir_filtros:
        logger.info("⏭️  Omitiendo filtros (--no-filtros activado)")
        return expedientes

    logger.info("🔍 Abriendo GUI de filtros avanzados...")
    seleccion = mostrar_filtros_avanzados(
        expedientes,
        titulo="Selección de Expedientes para Extracción Completa",
    )

    if seleccion is None:
        logger.warning("❌ Usuario canceló la selección")
        return None

    logger.info(f"✅ Usuario seleccionó {len(seleccion)} expedientes")
    return seleccion


def fase_3_crear_directorios(
    seleccion: list,
    config: SystemConfig,
) -> None:
    """Fase 3: Generación de directorios por expediente."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("FASE 3: GENERACIÓN DE DIRECTORIOS")
    logger.info("=" * 60)

    gestor = GestorDirectoriosExpedientes.desde_config(
        config,
        base_dir=SISTEMA_V5_DIR,
    )

    logger.info(f"📁 Creando estructura para {len(seleccion)} expedientes...")

    expedientes_json = [
        {
            "numero_expediente": exp.numero,
            "metadata": {
                "dependencia": exp.dependencia,
                "caratula": exp.caratula,
                "situacion": exp.situacion,
                "ultima_actuacion": exp.ultima_actuacion,
            },
        }
        for exp in seleccion
    ]

    try:
        resultados = gestor.crear_desde_json(expedientes_json)
        logger.info(f"✅ Creados {len(resultados)} directorios de expedientes")
    except ValueError as exc:
        logger.error(f"❌ Error al crear directorios: {exc}")
        raise


async def fase_4_extraer_completo(
    seleccion: list,
    headless: bool,
    descargar_adjuntos: bool,
    umbral_errores: int,
) -> None:
    """Fase 4: Extracción completa con manejo de errores."""
    logger.info("")
    logger.info("=" * 60)
    logger.info("FASE 4: EXTRACCIÓN COMPLETA BATCH")
    logger.info("=" * 60)

    batch = ExtractorCompletoBatch(
        umbral_errores_consecutivos=umbral_errores,
        headless=headless,
        descargar_adjuntos=descargar_adjuntos,
    )

    # Callback de progreso
    def on_progreso(indice: int, total: int, expediente) -> None:
        logger.info(f"[{indice}/{total}] Procesando: {expediente.numero}")

    # Callback de umbral de errores
    def on_umbral_errores(num_errores: int, mensajes: list[str]) -> str:
        logger.warning(f"⚠️  Alcanzado umbral: {num_errores} errores consecutivos")
        logger.warning("Últimos errores:")
        for msg in mensajes[-5:]:  # Mostrar últimos 5
            logger.warning(f"  - {msg}")

        # Preguntar al usuario
        respuesta = messagebox.askyesnocancel(
            "Umbral de Errores Alcanzado",
            f"Se han producido {num_errores} errores consecutivos.\n\n"
            f"¿Qué desea hacer?\n\n"
            f"• SÍ: Continuar procesando\n"
            f"• NO: Saltar expedientes restantes\n"
            f"• CANCELAR: Detener completamente",
            icon=messagebox.WARNING,
        )

        if respuesta is True:
            return "continuar"
        elif respuesta is False:
            return "saltar"
        else:
            return "cancelar"

    batch.set_callback_progreso(on_progreso)
    batch.set_callback_error_umbral(on_umbral_errores)

    logger.info(f"🤖 Procesando {len(seleccion)} expedientes...")
    logger.info(f"   Headless: {headless}")
    logger.info(f"   Descargar adjuntos: {descargar_adjuntos}")
    logger.info(f"   Umbral errores: {umbral_errores}")

    try:
        resumen = await batch.procesar_lote(seleccion)

        logger.info("")
        logger.info("=" * 60)
        logger.info("RESUMEN FINAL")
        logger.info("=" * 60)
        logger.info(f"✅ Exitosos:  {resumen.exitosos}/{resumen.total}")
        logger.info(f"❌ Errores:    {resumen.errores}/{resumen.total}")
        logger.info(f"⊘  Omitidos:   {resumen.omitidos}/{resumen.total}")
        logger.info(f"⏱️  Duración:   {resumen.duracion_segundos:.1f} segundos")

        # Guardar reporte
        from Sistema_v5.extractor_inicial.exporters import exportar_json

        reporte_path = SISTEMA_V5_DIR / "data" / "reportes" / f"extraccion_{resumen.tiempo_inicio.replace(':', '-').split('.')[0]}.json"
        reporte_path.parent.mkdir(parents=True, exist_ok=True)

        reporte_data = {
            "resumen": {
                "total": resumen.total,
                "exitosos": resumen.exitosos,
                "errores": resumen.errores,
                "omitidos": resumen.omitidos,
                "tiempo_inicio": resumen.tiempo_inicio,
                "tiempo_fin": resumen.tiempo_fin,
                "duracion_segundos": resumen.duracion_segundos,
            },
            "resultados": [
                {
                    "numero": r.expediente.numero,
                    "estado": r.estado,
                    "mensaje": r.mensaje,
                    "error": r.error,
                    "timestamp": r.timestamp,
                }
                for r in resumen.resultados
            ],
        }

        import json
        reporte_path.write_text(
            json.dumps(reporte_data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        logger.info(f"📊 Reporte guardado en: {reporte_path}")

    except Exception as exc:
        logger.exception(f"❌ Error durante procesamiento batch: {exc}")
        raise


async def main() -> int:
    """Función principal que orquesta todo el flujo."""
    args = parse_args()

    # Configurar logging
    log_dir = SISTEMA_V5_DIR / "logs"
    log_dir.mkdir(exist_ok=True)
    setup_logging(
        level="INFO",
        log_file=log_dir / "extraccion_inicial_v2.log",
    )

    logger.info("🚀 Iniciando Extracción Inicial v2.0")
    logger.info(f"Configuración: {args['config']}")

    try:
        # Cargar configuración
        config_path = SISTEMA_V5_DIR / args["config"]
        if not config_path.exists():
            logger.error(f"❌ No se encontró el archivo de configuración: {config_path}")
            return 1

        config = SystemConfig.from_file(config_path)
        headless = args["headless"] or config.headless

        # Fase 1: Extraer listado (o cargar desde JSON existente)
        if args["desde_json"]:
            logger.info(f"📄 Cargando expedientes desde JSON: {args['desde_json']}")
            from Sistema_v5.extractor_inicial import cargar_json
            json_path = SISTEMA_V5_DIR / args["desde_json"]
            if not json_path.exists():
                logger.error(f"❌ Archivo JSON no encontrado: {json_path}")
                return 1
            expedientes, metadata = cargar_json(json_path)
            logger.info(f"✅ Cargados {len(expedientes)} expedientes desde {json_path.name}")
        else:
            expedientes, json_path = await fase_1_extraer_listado(config, headless)

        if not expedientes:
            logger.warning("⚠️  No se extrajeron expedientes. Finalizando.")
            return 0

        # Fase 2: Filtrar
        seleccion = fase_2_filtrar_expedientes(expedientes, args["no_filtros"])

        if seleccion is None:
            logger.info("❌ Proceso cancelado por el usuario")
            return 0

        if not seleccion:
            logger.warning("⚠️  No hay expedientes seleccionados. Finalizando.")
            return 0

        # Fase 3: Crear directorios
        fase_3_crear_directorios(seleccion, config)

        # Fase 4: Extraer completo
        await fase_4_extraer_completo(
            seleccion,
            headless,
            not args["no_adjuntos"],
            args["umbral_errores"],
        )

        logger.info("")
        logger.info("=" * 60)
        logger.info("✅ EXTRACCIÓN INICIAL COMPLETADA CON ÉXITO")
        logger.info("=" * 60)
        return 0

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Proceso interrumpido por el usuario (Ctrl+C)")
        return 130

    except Exception as exc:
        logger.exception(f"❌ Error fatal: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
