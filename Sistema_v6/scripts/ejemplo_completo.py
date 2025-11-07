#!/usr/bin/env python3
"""Ejemplo completo del workflow del Sistema PJN v6.

Este script demuestra el flujo completo de 4 fases:
1. Extraer expedientes del PJN → JSON "base"
2. Filtrar expedientes por selección → JSON "sistema"
3. Crear workspaces organizados
4. Monitorear cambios periódicamente

NOTA: Requiere credenciales del PJN y scraping completamente implementado.
"""

import asyncio
import logging
from pathlib import Path

from application.dtos import (
    CrearWorkspacesCommand,
    ExtraerExpedientesCommand,
    FiltrarExpedientesCommand,
    MonitorearExpedientesCommand,
)
from infrastructure.config import get_settings
from infrastructure.di_container import get_container

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    """Flujo completo del sistema."""
    logger.info("=== Iniciando ejemplo completo Sistema PJN v6 ===")

    # Obtener configuración y contenedor
    settings = get_settings()
    container = get_container()

    # === FASE 1: Extraer expedientes ===
    logger.info("\n=== FASE 1: Extracción de expedientes ===")

    archivo_base = settings.storage.base_path / settings.storage.json_base_file

    command_extraer = ExtraerExpedientesCommand(
        usuario=None,  # Tomará de variables de entorno o .env
        contrasena=None,
        headless=True,
        guardar_en=archivo_base,
    )

    use_case_extraer = container.extraer_expedientes_use_case()

    try:
        result_extraer = await use_case_extraer.execute(command_extraer)

        if result_extraer.success:
            logger.info(f"✓ Extracción exitosa: {result_extraer.value.total} expedientes")
            logger.info(f"  Guardado en: {result_extraer.value.archivo_guardado}")
        else:
            logger.error(f"✗ Error en extracción: {result_extraer.error}")
            return

    except NotImplementedError:
        logger.warning("⚠ Scraping no implementado. Usando datos de ejemplo...")
        # Para demostración, crear archivo de ejemplo
        archivo_base.parent.mkdir(parents=True, exist_ok=True)
        import json

        datos_ejemplo = [
            {
                "numero": "CNM 0001/2024",
                "dependencia": "Juzgado Federal 1",
                "caratula": "CASO EJEMPLO A C/ B S/ MATERIA",
                "situacion": "En trámite",
                "ultima_actuacion": "2024-11-05",
            },
            {
                "numero": "CNM 0002/2024",
                "dependencia": "Juzgado Federal 2",
                "caratula": "OTRO CASO X C/ Y S/ OTRO",
                "situacion": "En trámite",
                "ultima_actuacion": "2024-11-04",
            },
        ]
        with archivo_base.open("w", encoding="utf-8") as f:
            json.dump(datos_ejemplo, f, indent=2, ensure_ascii=False)
        logger.info(f"✓ Archivo de ejemplo creado: {archivo_base}")

    # === FASE 2: Filtrar expedientes ===
    logger.info("\n=== FASE 2: Filtrado de expedientes ===")

    archivo_sistema = settings.storage.base_path / "expedientes_sistema.json"

    command_filtrar = FiltrarExpedientesCommand(
        numeros_seleccionados=["CNM 0001/2024"],  # Selección manual
        origen=archivo_base,
        destino=archivo_sistema,
        incluir_activos=True,  # Agregar activos automáticamente
        dias_actividad=30,
    )

    use_case_filtrar = container.filtrar_expedientes_use_case()
    result_filtrar = await use_case_filtrar.execute(command_filtrar)

    if result_filtrar.success:
        logger.info(
            f"✓ Filtrado exitoso: {result_filtrar.value.total_filtrados}/{result_filtrar.value.total_origen} expedientes"
        )
        logger.info(f"  Guardado en: {result_filtrar.value.archivo_guardado}")
    else:
        logger.error(f"✗ Error en filtrado: {result_filtrar.error}")
        return

    # === FASE 3: Crear workspaces ===
    logger.info("\n=== FASE 3: Creación de workspaces ===")

    workspaces_dir = settings.storage.base_path / settings.storage.workspaces_dir

    command_workspaces = CrearWorkspacesCommand(
        archivo_sistema=archivo_sistema,
        workspaces_dir=workspaces_dir,
        extraer_actuaciones=False,  # Requiere scraping implementado
        descargar_archivos=False,
    )

    use_case_workspaces = container.crear_workspaces_use_case()
    result_workspaces = await use_case_workspaces.execute(command_workspaces)

    if result_workspaces.success:
        logger.info(
            f"✓ Workspaces creados: {result_workspaces.value.workspaces_creados}/{result_workspaces.value.total_expedientes}"
        )
        if result_workspaces.value.errores > 0:
            logger.warning(f"  Errores: {result_workspaces.value.errores}")
    else:
        logger.error(f"✗ Error en creación de workspaces: {result_workspaces.error}")
        return

    # === FASE 4: Monitorear cambios (una verificación) ===
    logger.info("\n=== FASE 4: Monitoreo de cambios ===")

    command_monitoreo = MonitorearExpedientesCommand(
        archivo_sistema=archivo_sistema,
        workspaces_dir=workspaces_dir,
        intervalo_minutos=60,
        notificar=False,  # Desactivar notificaciones para demo
    )

    use_case_monitoreo = container.monitorear_expedientes_use_case()

    try:
        result_monitoreo = await use_case_monitoreo.execute(command_monitoreo)

        if result_monitoreo.success:
            logger.info(
                f"✓ Monitoreo completado: {result_monitoreo.value.cambios_detectados} cambios detectados"
            )
            if result_monitoreo.value.cambios:
                logger.info("  Cambios:")
                for cambio in result_monitoreo.value.cambios:
                    logger.info(f"    - {cambio}")
        else:
            logger.error(f"✗ Error en monitoreo: {result_monitoreo.error}")

    except NotImplementedError:
        logger.warning("⚠ Monitoreo no completamente implementado (scraping pendiente)")

    logger.info("\n=== Ejemplo completo finalizado ===")


if __name__ == "__main__":
    asyncio.run(main())
