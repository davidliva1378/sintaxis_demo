#!/usr/bin/env python3
"""Script de demostración del sistema de logging de Sistema_v5.

Este script muestra cómo funciona el sistema de logging con diferentes niveles
y configuraciones.

Uso:
    # Modo normal (INFO)
    python test_logging_demo.py

    # Modo debug (ver todo)
    LOG_LEVEL=DEBUG python test_logging_demo.py

    # Modo silencioso (solo errores)
    LOG_LEVEL=ERROR python test_logging_demo.py

    # Guardar logs en archivo
    LOG_FILE=logs/demo.log python test_logging_demo.py

    # Sin colores
    LOG_COLORS=false python test_logging_demo.py
"""
import asyncio
import sys
from pathlib import Path

# Agregar el proyecto al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Sistema_v5.pjn.utils.logging import get_logger, setup_logging

# Obtener logger para este módulo
logger = get_logger(__name__)


def demo_niveles_logging():
    """Demuestra los diferentes niveles de logging."""
    print("\n" + "="*60)
    print("DEMOSTRACIÓN DE NIVELES DE LOGGING")
    print("="*60 + "\n")

    logger.debug("🔍 DEBUG: Variable x = 42, y = 'test'")
    logger.info("ℹ️ INFO: Proceso iniciado correctamente")
    logger.warning("⚠️ WARNING: Timeout detectado, reintentando...")
    logger.error("❌ ERROR: No se pudo descargar el archivo")
    logger.critical("💥 CRITICAL: Sistema en estado crítico")


def demo_con_parametros():
    """Demuestra logging con parámetros (más eficiente)."""
    print("\n" + "="*60)
    print("LOGGING CON PARÁMETROS")
    print("="*60 + "\n")

    expediente = "FPA 12345/2021"
    pagina = 3
    archivos = 15

    logger.info("📄 Procesando expediente: %s", expediente)
    logger.info("📄 Página %d de %d", pagina, 10)
    logger.info("📥 Descargando %d archivos...", archivos)


def demo_emojis_visual():
    """Demuestra el estilo visual con emojis (igual que print actual)."""
    print("\n" + "="*60)
    print("ESTILO VISUAL CON EMOJIS")
    print("="*60 + "\n")

    logger.info("📄 Página 1: extrayendo...")
    logger.info("✅ Archivo descargado: documento.pdf")
    logger.info("⏭️ Archivo ya existe: informe.docx")
    logger.warning("⚠️ Timeout, reintentando...")
    logger.error("❌ Error de I/O al guardar archivo")
    logger.info("📁 JSONs guardados en: /path/to/folder")


def demo_debug_detallado():
    """Demuestra información de debug (solo visible con LOG_LEVEL=DEBUG)."""
    print("\n" + "="*60)
    print("INFORMACIÓN DE DEBUG")
    print("="*60 + "\n")

    logger.debug("🔍 Iniciando procesamiento...")
    logger.debug("🔍 fecha_limpia: '12/09/2025'")
    logger.debug("🔍 Hash calculado: abc123")
    logger.debug("🔍 Nombre de archivo: 12-09-2025_deo_abc123.pdf")


async def demo_async_operations():
    """Demuestra logging en operaciones asíncronas."""
    print("\n" + "="*60)
    print("OPERACIONES ASÍNCRONAS")
    print("="*60 + "\n")

    logger.info("🚀 Iniciando operaciones async...")

    for i in range(3):
        await asyncio.sleep(0.5)
        logger.info("⏳ Paso %d completado", i + 1)

    logger.info("✅ Todas las operaciones completadas")


def mostrar_configuracion_actual():
    """Muestra la configuración actual de logging."""
    import logging
    import os

    print("\n" + "="*60)
    print("CONFIGURACIÓN ACTUAL")
    print("="*60)
    print(f"Nivel LOG_LEVEL: {os.getenv('LOG_LEVEL', 'INFO (default)')}")
    print(f"Archivo LOG_FILE: {os.getenv('LOG_FILE', 'No (solo consola)')}")
    print(f"Colores LOG_COLORS: {os.getenv('LOG_COLORS', 'true (default)')}")
    print(f"Nivel efectivo: {logging.getLevelName(logging.getLogger().level)}")
    print("="*60 + "\n")


def main():
    """Ejecuta todas las demostraciones."""
    mostrar_configuracion_actual()

    demo_niveles_logging()
    demo_con_parametros()
    demo_emojis_visual()
    demo_debug_detallado()

    # Demo async
    asyncio.run(demo_async_operations())

    print("\n" + "="*60)
    print("EJEMPLO DE USO EN CÓDIGO")
    print("="*60)
    print("""
from Sistema_v5.pjn.utils.logging import get_logger

logger = get_logger(__name__)

# En lugar de:
print(f"📄 Página {pagina}: extrayendo...")

# Usar:
logger.info("📄 Página %d: extrayendo...", pagina)
    """)

    print("\n" + "="*60)
    print("VARIABLES DE ENTORNO DISPONIBLES")
    print("="*60)
    print("""
export LOG_LEVEL=DEBUG     # Ver todo incluso debug
export LOG_LEVEL=INFO      # Solo INFO y superiores (default)
export LOG_LEVEL=ERROR     # Solo errores

export LOG_FILE=logs/sistema_v5.log  # Guardar en archivo
export LOG_COLORS=false    # Desactivar colores
    """)


if __name__ == "__main__":
    main()
