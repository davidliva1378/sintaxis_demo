#!/usr/bin/env python3
"""Script para ejecutar el ejemplo completo del Sistema PJN v6.

Configura el PYTHONPATH automáticamente y ejecuta el ejemplo.
"""

import sys
from pathlib import Path

# Agregar Sistema_v6 al PYTHONPATH
sistema_v6_path = Path(__file__).parent
sys.path.insert(0, str(sistema_v6_path))

# Ahora importar y ejecutar
if __name__ == "__main__":
    # Importar después de configurar el path
    import asyncio
    import logging
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
        logger.info("\n=== FASE 1: Extraccion de expedientes ===")

        archivo_base = settings.storage.base_path / settings.storage.json_base_file

        try:
            # Crear datos de ejemplo para demostración
            logger.warning("Scraping no implementado. Creando datos de ejemplo...")
            archivo_base.parent.mkdir(parents=True, exist_ok=True)
            import json

            datos_ejemplo = [
                {
                    "numero": "CNM 0001/2024",
                    "dependencia": "Juzgado Federal 1",
                    "caratula": "CASO EJEMPLO A C/ B S/ MATERIA",
                    "situacion": "En tramite",
                    "ultima_actuacion": "2024-11-05",
                },
                {
                    "numero": "CNM 0002/2024",
                    "dependencia": "Juzgado Federal 2",
                    "caratula": "OTRO CASO X C/ Y S/ OTRO",
                    "situacion": "En tramite",
                    "ultima_actuacion": "2024-11-04",
                },
                {
                    "numero": "CNM 0003/2024",
                    "dependencia": "Juzgado Federal 1",
                    "caratula": "CASO ADICIONAL Z S/ TEMA",
                    "situacion": "En tramite",
                    "ultima_actuacion": "2024-11-03",
                },
            ]
            with archivo_base.open("w", encoding="utf-8") as f:
                json.dump(datos_ejemplo, f, indent=2, ensure_ascii=False)
            logger.info(f"Archivo de ejemplo creado: {archivo_base}")
            logger.info(f"Total expedientes: {len(datos_ejemplo)}")

        except Exception as e:
            logger.error(f"Error en creacion de datos: {e}")
            return

        # === FASE 2: Filtrar expedientes ===
        logger.info("\n=== FASE 2: Filtrado de expedientes ===")

        archivo_sistema = settings.storage.base_path / "expedientes_sistema.json"

        command_filtrar = FiltrarExpedientesCommand(
            numeros_seleccionados=["CNM 0001/2024", "CNM 0003/2024"],
            origen=archivo_base,
            destino=archivo_sistema,
            incluir_activos=True,
            dias_actividad=30,
        )

        use_case_filtrar = container.filtrar_expedientes_use_case()
        result_filtrar = await use_case_filtrar.execute(command_filtrar)

        if result_filtrar.success:
            logger.info(
                f"Filtrado exitoso: {result_filtrar.value.total} expedientes seleccionados"
            )
            logger.info(f"Guardado en: {result_filtrar.value.archivo_guardado}")
        else:
            logger.error(f"Error en filtrado: {result_filtrar.error}")
            return

        # === FASE 3: Crear workspaces ===
        logger.info("\n=== FASE 3: Creacion de workspaces ===")

        workspaces_dir = settings.storage.base_path / settings.storage.workspaces_dir

        command_workspaces = CrearWorkspacesCommand(
            json_sistema=archivo_sistema,
            base_path=workspaces_dir,
            extraer_actuaciones=False,
            descargar_archivos=False,
        )

        use_case_workspaces = container.crear_workspaces_use_case()
        result_workspaces = await use_case_workspaces.execute(command_workspaces)

        if result_workspaces.success:
            logger.info(
                f"Workspaces creados: {result_workspaces.value.total_creados}"
            )
            if result_workspaces.value.total_fallidos > 0:
                logger.warning(f"Fallidos: {result_workspaces.value.total_fallidos}")
        else:
            logger.error(f"Error en creacion de workspaces: {result_workspaces.error}")
            return

        # === FASE 4: Monitorear cambios ===
        logger.info("\n=== FASE 4: Monitoreo de cambios (desactivado) ===")
        logger.info("Monitoreo requiere scraping implementado. Saltando...")

        logger.info("\n=== Ejemplo completo finalizado ===")
        logger.info(f"\nArchivos creados:")
        logger.info(f"  - {archivo_base}")
        logger.info(f"  - {archivo_sistema}")
        logger.info(f"  - {workspaces_dir}/ (directorio con workspaces)")

    asyncio.run(main())
