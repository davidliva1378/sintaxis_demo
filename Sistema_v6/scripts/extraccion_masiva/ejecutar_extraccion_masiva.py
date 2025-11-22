#!/usr/bin/env python3
"""Script principal para extracción masiva de expedientes.

Este script orquesta el flujo completo de 5 fases para extracción masiva:

1. Extracción del listado completo de expedientes
2. Filtrado y gestión de estados
3. Generación de estructura de directorios
4. Extracción completa batch con actuaciones
5. Procesamiento con procesador_pdf (opcional)

Adaptado de: Sistema_v5/bin/ejecutar_extraccion.py
Versión: 6.1.0

Uso:
    # Modo interactivo (con GUI para filtros)
    python scripts/extraccion_masiva/ejecutar_extraccion_masiva.py

    # Modo CLI
    python scripts/extraccion_masiva/ejecutar_extraccion_masiva.py --no-gui

    # Con todas las opciones
    python scripts/extraccion_masiva/ejecutar_extraccion_masiva.py \\
        --headless \\
        --no-filtros \\
        --procesar \\
        --dias-urgentes 5 \\
        --umbral-errores 3

    # Usar configuración desde archivo
    python scripts/extraccion_masiva/ejecutar_extraccion_masiva.py \\
        --config config/extraccion_masiva.json

Autor: sintaXis v6.1
Fecha: 2025-11-07
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

# Agregar raíz del proyecto (Sistema_v6) al path
SCRIPT_DIR = Path(__file__).parent
SISTEMA_V6_ROOT = SCRIPT_DIR.parent.parent
if str(SISTEMA_V6_ROOT) not in sys.path:
    sys.path.insert(0, str(SISTEMA_V6_ROOT))

# Componentes de extracción masiva
from scripts.extraccion_masiva import (
    EstadosManager,
    EstadoExpediente,
    GestorDirectoriosExpedientes,
    ExtractorCompletoBatch,
    ExpedienteInfo,
)

# Componentes migrados a v6 (ahora internos)
from infrastructure.adapters.session.playwright_session_manager import reutilizar_sesion_async
from infrastructure.adapters.scraping.expedientes_batch_extractor import extraer_expedientes
from core.domain.constants import URL_CONSULTAS

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constantes
DEFAULT_CONFIG = {
    "headless": True,
    "descargar_adjuntos": False,
    "umbral_errores": 5,
    "procesar_con_pdf": False,
    "dias_urgentes": 7,
    "omitir_filtros": False,
    "no_gui": False,
    "directorios": {
        "expedientes": "data/expedientes",
        "estados": "data/estados",
        "reportes": "data/reportes"
    }
}


def cargar_configuracion(config_path: Path | None) -> dict[str, Any]:
    """Carga configuración desde archivo o usa valores por defecto.

    Args:
        config_path: Ruta al archivo de configuración JSON

    Returns:
        Diccionario con configuración completa
    """
    config = DEFAULT_CONFIG.copy()

    if config_path and config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_archivo = json.load(f)
            config.update(config_archivo)
            logger.info(f"✅ Configuración cargada desde {config_path}")
        except Exception as e:
            logger.warning(f"⚠️  Error al cargar configuración: {e}")
            logger.info("📌 Usando configuración por defecto")

    return config


async def fase_1_extraer_listado(
    page,
    config: dict[str, Any]
) -> tuple[list[dict], Path | None, str]:
    """Fase 1: Extracción del listado completo de expedientes.

    Args:
        page: Página de Playwright
        config: Configuración del sistema

    Returns:
        Tupla (expedientes, ruta_json, motivo)
    """
    logger.info("=" * 70)
    logger.info("FASE 1: EXTRACCIÓN DEL LISTADO COMPLETO")
    logger.info("=" * 70)

    try:
        # Navegar al portal
        await page.goto(URL_CONSULTAS)
        await page.wait_for_load_state("domcontentloaded")

        # Extraer expedientes
        expedientes, ruta_json, motivo = await extraer_expedientes(
            page=page,
            guardar_json=True,
            detener_en_duplicado=False,  # Queremos TODOS los expedientes
            fecha_corte=None,
        )

        logger.info(f"✅ Extraídos {len(expedientes)} expedientes")
        logger.info(f"📄 Guardado en: {ruta_json}")
        logger.info(f"⛔ Motivo de finalización: {motivo}")

        return expedientes, ruta_json, motivo

    except Exception as e:
        logger.error(f"❌ Error en Fase 1: {e}")
        raise


def fase_2_gestionar_estados(
    expedientes: list[dict],
    config: dict[str, Any]
) -> list[str]:
    """Fase 2: Filtrado y gestión de estados.

    Args:
        expedientes: Lista de expedientes extraídos
        config: Configuración del sistema

    Returns:
        Lista de números de expedientes activos para procesar
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("FASE 2: FILTRADO Y GESTIÓN DE ESTADOS")
    logger.info("=" * 70)

    try:
        # Inicializar gestor de estados
        estados_dir = Path(config["directorios"]["estados"])
        estados_file = estados_dir / "estados_expedientes.json"

        manager = EstadosManager(archivo_estados=estados_file)
        manager.cargar_estados()

        # Obtener números de expedientes
        numeros_expedientes = [exp["numero"] for exp in expedientes]

        if config["omitir_filtros"]:
            logger.info("⏭️  Omitiendo filtros (--no-filtros activado)")

            # Inicializar todos como MONITOREADO
            inicializados = manager.inicializar_expedientes(
                numeros_expedientes,
                estado_inicial=EstadoExpediente.MONITOREADO,
                auto_guardar=True
            )

            logger.info(f"📝 Inicializados {inicializados} expedientes como MONITOREADO")

            # Retornar todos
            return numeros_expedientes

        else:
            # Inicializar nuevos como PENDIENTE_REVISION
            inicializados = manager.inicializar_expedientes(
                numeros_expedientes,
                estado_inicial=EstadoExpediente.PENDIENTE_REVISION,
                auto_guardar=False
            )

            logger.info(f"📝 Inicializados {inicializados} expedientes nuevos")

            if config["no_gui"]:
                # Modo CLI: Usar estados existentes
                logger.info("🖥️  Modo CLI: Usando estados existentes")
            else:
                # Modo GUI: Mostrar interfaz de filtros
                logger.info("🖼️  Modo GUI: Abriendo interfaz de filtros...")
                logger.info("⚠️  GUI no implementada aún, usando estados existentes")
                # TODO: Implementar interfaz de filtros (Fase D)

            # Guardar estados
            manager.guardar_estados()

            # Obtener expedientes activos
            expedientes_activos = manager.obtener_expedientes_activos()

            logger.info(f"✅ {len(expedientes_activos)} expedientes activos para procesamiento")

            # Mostrar resumen
            resumen = manager.obtener_resumen()
            logger.info("📊 Resumen de estados:")
            for estado, count in resumen["por_estado"].items():
                logger.info(f"   - {estado}: {count}")

            return expedientes_activos

    except Exception as e:
        logger.error(f"❌ Error en Fase 2: {e}")
        raise


def fase_3_crear_directorios(
    expedientes: list[dict],
    expedientes_activos: list[str],
    config: dict[str, Any]
) -> list[tuple[Path, dict]]:
    """Fase 3: Generación de estructura de directorios.

    Args:
        expedientes: Lista completa de expedientes
        expedientes_activos: Números de expedientes activos
        config: Configuración del sistema

    Returns:
        Lista de tuplas (ruta, manifest) para cada expediente creado
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("FASE 3: GENERACIÓN DE ESTRUCTURA DE DIRECTORIOS")
    logger.info("=" * 70)

    try:
        # Inicializar gestor de directorios
        expedientes_dir = Path(config["directorios"]["expedientes"])
        gestor = GestorDirectoriosExpedientes(raiz=expedientes_dir)

        # Filtrar expedientes activos
        expedientes_para_crear = [
            exp for exp in expedientes
            if exp["numero"] in expedientes_activos
        ]

        if not expedientes_para_crear:
            logger.warning("⚠️  No hay expedientes activos para crear directorios")
            return []

        logger.info(f"📁 Creando estructura para {len(expedientes_para_crear)} expedientes...")

        # Crear directorios
        resultados = gestor.crear_desde_json(expedientes_para_crear)

        logger.info(f"✅ Creados directorios para {len(resultados)} expedientes")

        # Mostrar primeros 5
        for i, (ruta, manifest) in enumerate(resultados[:5], 1):
            logger.info(f"   {i}. {ruta.name}")
            logger.info(f"      Directorios: {len(manifest['directories'])}")

        if len(resultados) > 5:
            logger.info(f"   ... y {len(resultados) - 5} más")

        return resultados

    except Exception as e:
        logger.error(f"❌ Error en Fase 3: {e}")
        raise


async def fase_4_extraccion_batch(
    page,
    expedientes: list[dict],
    expedientes_activos: list[str],
    config: dict[str, Any]
) -> tuple[Any, Path]:
    """Fase 4: Extracción completa batch con actuaciones.

    Args:
        page: Página de Playwright
        expedientes: Lista completa de expedientes
        expedientes_activos: Números de expedientes activos
        config: Configuración del sistema

    Returns:
        Tupla (resumen_batch, reporte_path)
    """
    logger.info("")
    logger.info("=" * 70)
    logger.info("FASE 4: EXTRACCIÓN COMPLETA BATCH")
    logger.info("=" * 70)

    try:
        # Filtrar expedientes activos
        expedientes_batch = [
            exp for exp in expedientes
            if exp["numero"] in expedientes_activos
        ]

        if not expedientes_batch:
            logger.warning("⚠️  No hay expedientes para procesar en batch")
            return None, None

        # Crear procesador batch
        expedientes_dir = Path(config["directorios"]["expedientes"])
        batch = ExtractorCompletoBatch(
            umbral_errores_consecutivos=config["umbral_errores"],
            headless=config["headless"],
            descargar_adjuntos=config["descargar_adjuntos"],
            directorio_base=expedientes_dir
        )

        # Configurar callbacks
        def on_progreso(indice: int, total: int, expediente):
            logger.info(f"   [{indice}/{total}] Procesando: {expediente}")

        def on_expediente_inicio(expediente, indice: int, total: int):
            logger.info(f"   🔄 Iniciando extracción de {expediente.numero}...")

        def on_expediente_fin(resultado, tiempo_segundos: float):
            if resultado.estado == "success":
                logger.info(f"   ✅ {resultado.mensaje} ({tiempo_segundos:.1f}s)")
            elif resultado.estado == "error":
                logger.error(f"   ❌ {resultado.mensaje} ({tiempo_segundos:.1f}s)")
            else:
                logger.warning(f"   ⊘ {resultado.mensaje}")

        def on_umbral_errores(num_errores: int, mensajes: list[str]) -> str:
            logger.warning("")
            logger.warning(f"⚠️  UMBRAL DE ERRORES ALCANZADO: {num_errores} errores consecutivos")
            logger.warning("Últimos errores:")
            for msg in mensajes[-3:]:
                logger.warning(f"   - {msg}")

            if config["no_gui"]:
                logger.info("   Modo CLI: Continuando automáticamente...")
                return "continuar"
            else:
                # TODO: Mostrar diálogo en GUI (Fase D)
                logger.info("   Sin GUI disponible, continuando automáticamente...")
                return "continuar"

        batch.set_callback_progreso(on_progreso)
        batch.set_callback_expediente_inicio(on_expediente_inicio)
        batch.set_callback_expediente_fin(on_expediente_fin)
        batch.set_callback_error_umbral(on_umbral_errores)

        logger.info(f"🚀 Procesando {len(expedientes_batch)} expedientes...")

        # Extractor personalizado (placeholder - debe implementarse según necesidades)
        async def extraer_actuaciones_expediente(expediente, page):
            """Extractor personalizado para actuaciones.

            TODO: Implementar lógica real de extracción de actuaciones.
            Por ahora retorna datos de ejemplo.
            """
            await asyncio.sleep(0.1)  # Simular trabajo

            return {
                "numero_expediente": expediente.numero,
                "caratula": expediente.caratula,
                "actuaciones": [],
                "metadata": {
                    "fecha_extraccion": datetime.now().isoformat(),
                    "total_actuaciones": 0
                }
            }

        # Procesar lote
        resumen = await batch.procesar_lote(
            expedientes_batch,
            page=page,
            extractor_personalizado=extraer_actuaciones_expediente
        )

        logger.info("")
        logger.info("📊 RESUMEN DEL BATCH:")
        logger.info(f"   Total:    {resumen.total}")
        logger.info(f"   Exitosos: {resumen.exitosos}")
        logger.info(f"   Errores:  {resumen.errores}")
        logger.info(f"   Omitidos: {resumen.omitidos}")
        logger.info(f"   Duración: {resumen.duracion_segundos:.1f}s")
        if resumen.total > 0:
            logger.info(f"   Promedio: {resumen.duracion_segundos/resumen.total:.2f}s por expediente")

        # Generar reporte
        reportes_dir = Path(config["directorios"]["reportes"])
        reportes_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        reporte_path = reportes_dir / f"reporte_batch_{timestamp}.json"

        reporte_path_final = batch.generar_reporte(reporte_path)
        logger.info(f"💾 Reporte guardado en: {reporte_path_final}")

        return resumen, reporte_path_final

    except Exception as e:
        logger.error(f"❌ Error en Fase 4: {e}")
        raise


def fase_5_procesar_con_pdf(
    resumen_batch: Any,
    config: dict[str, Any]
) -> dict[str, Any] | None:
    """Fase 5: Procesamiento con procesador_pdf (opcional).

    Args:
        resumen_batch: Resumen del batch de Fase 4
        config: Configuración del sistema

    Returns:
        Diccionario con resultados del procesamiento o None si no se ejecuta
    """
    if not config["procesar_con_pdf"]:
        logger.info("")
        logger.info("=" * 70)
        logger.info("FASE 5: PROCESAMIENTO CON PROCESADOR_PDF")
        logger.info("=" * 70)
        logger.info("⏭️  Omitida (--procesar no activado)")
        return None

    logger.info("")
    logger.info("=" * 70)
    logger.info("FASE 5: PROCESAMIENTO CON PROCESADOR_PDF")
    logger.info("=" * 70)

    try:
        # Verificar si procesador_pdf está disponible
        try:
            from core.procesador_pdf import ClasificadorActuaciones
            from extractor_inicial.procesamiento_expedientes import ProcesadorExpedientesInicial
        except ImportError:
            logger.warning("⚠️  procesador_pdf no está disponible")
            logger.info("   Instale las dependencias: pip install -r Sistema_v5/procesador_pdf/requirements.txt")
            return None

        # TODO: Implementar procesamiento con procesador_pdf
        # Por ahora solo logeamos
        logger.info("🔄 Procesamiento con procesador_pdf...")
        logger.info("⚠️  Implementación pendiente - requiere integración específica")
        logger.info(f"   Días urgentes configurados: {config['dias_urgentes']}")

        return {
            "status": "skipped",
            "message": "Implementación pendiente"
        }

    except Exception as e:
        logger.error(f"❌ Error en Fase 5: {e}")
        return None


async def main_async(args: argparse.Namespace) -> int:
    """Función principal asíncrona.

    Args:
        args: Argumentos parseados de la línea de comandos

    Returns:
        Código de salida (0 = éxito, 1 = error)
    """
    try:
        # Cargar configuración
        config_path = Path(args.config) if args.config else None
        config = cargar_configuracion(config_path)

        # Sobrescribir con argumentos CLI (tienen prioridad)
        if args.headless is not None:
            config["headless"] = args.headless
        if args.no_adjuntos:
            config["descargar_adjuntos"] = False
        if args.umbral_errores is not None:
            config["umbral_errores"] = args.umbral_errores
        if args.procesar:
            config["procesar_con_pdf"] = True
        if args.dias_urgentes is not None:
            config["dias_urgentes"] = args.dias_urgentes
        if args.no_filtros:
            config["omitir_filtros"] = True
        if args.no_gui:
            config["no_gui"] = True

        # Mostrar configuración
        logger.info("=" * 70)
        logger.info("CONFIGURACIÓN DE EXTRACCIÓN MASIVA")
        logger.info("=" * 70)
        logger.info(f"Headless:           {config['headless']}")
        logger.info(f"Descargar adjuntos: {config['descargar_adjuntos']}")
        logger.info(f"Umbral errores:     {config['umbral_errores']}")
        logger.info(f"Procesar con PDF:   {config['procesar_con_pdf']}")
        logger.info(f"Días urgentes:      {config['dias_urgentes']}")
        logger.info(f"Omitir filtros:     {config['omitir_filtros']}")
        logger.info(f"Modo:               {'CLI' if config['no_gui'] else 'GUI'}")
        logger.info("")

        # Iniciar sesión de Playwright
        logger.info("🔐 Iniciando sesión de Playwright...")
        async with reutilizar_sesion_async() as (page, context, browser):
            logger.info("✅ Sesión iniciada")

            # FASE 1: Extracción del listado
            expedientes, ruta_json, motivo = await fase_1_extraer_listado(page, config)

            if not expedientes:
                logger.error("❌ No se extrajeron expedientes. Finalizando.")
                return 1

            # FASE 2: Gestión de estados
            expedientes_activos = fase_2_gestionar_estados(expedientes, config)

            if not expedientes_activos:
                logger.error("❌ No hay expedientes activos para procesar. Finalizando.")
                return 1

            # FASE 3: Creación de directorios
            resultados_dirs = fase_3_crear_directorios(expedientes, expedientes_activos, config)

            # FASE 4: Extracción batch
            resumen_batch, reporte_path = await fase_4_extraccion_batch(
                page, expedientes, expedientes_activos, config
            )

            # FASE 5: Procesamiento con procesador_pdf (opcional)
            resultado_procesamiento = fase_5_procesar_con_pdf(resumen_batch, config)

        # Resumen final
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ EXTRACCIÓN MASIVA COMPLETADA")
        logger.info("=" * 70)
        logger.info(f"Total expedientes extraídos:  {len(expedientes)}")
        logger.info(f"Expedientes activos:          {len(expedientes_activos)}")
        logger.info(f"Directorios creados:          {len(resultados_dirs) if resultados_dirs else 0}")
        if resumen_batch:
            logger.info(f"Procesados en batch:          {resumen_batch.exitosos}/{resumen_batch.total}")
            logger.info(f"Reporte batch:                {reporte_path}")

        return 0

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Operación cancelada por el usuario")
        return 130
    except Exception as e:
        logger.error(f"\n❌ Error fatal: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main() -> int:
    """Función principal con parseo de argumentos.

    Returns:
        Código de salida
    """
    parser = argparse.ArgumentParser(
        description="Extracción masiva de expedientes del PJN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos:
  %(prog)s                                    # Modo interactivo con GUI
  %(prog)s --no-gui                           # Modo CLI sin interfaz
  %(prog)s --no-filtros                       # Procesar todos los expedientes
  %(prog)s --procesar --dias-urgentes 5       # Con procesamiento PDF
  %(prog)s --config config/extraccion.json    # Usar configuración personalizada

Para más información consulte: scripts/extraccion_masiva/README.md
        """
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Ruta al archivo de configuración JSON"
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        default=None,
        help="Ejecutar Playwright en modo headless (sin navegador visible)"
    )

    parser.add_argument(
        "--no-adjuntos",
        action="store_true",
        help="No descargar archivos adjuntos de actuaciones"
    )

    parser.add_argument(
        "--umbral-errores",
        type=int,
        metavar="N",
        help="Número de errores consecutivos antes de pausar (default: 5)"
    )

    parser.add_argument(
        "--procesar",
        action="store_true",
        help="Activar procesamiento con procesador_pdf (clasificación y vencimientos)"
    )

    parser.add_argument(
        "--dias-urgentes",
        type=int,
        metavar="N",
        help="Días para considerar un vencimiento como urgente (default: 7)"
    )

    parser.add_argument(
        "--no-filtros",
        action="store_true",
        help="Omitir paso de filtrado (procesar todos los expedientes como MONITOREADO)"
    )

    parser.add_argument(
        "--no-gui",
        action="store_true",
        help="Ejecutar en modo CLI sin interfaz gráfica"
    )

    args = parser.parse_args()

    # Ejecutar main async
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
