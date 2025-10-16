#!/usr/bin/env python3
"""Test simple del monitor PJN - solo prueba componentes core sin navegador."""

import sys
from pathlib import Path

# Agregar directorio al path
sys.path.insert(0, str(Path(__file__).parent))

from pjn.monitor.config import MonitorConfig
from pjn.monitor.storage import StorageManager, EstadoMonitor
from pjn.monitor.detector import DetectorCambios
from pjn.monitor.notifier import NotificadorPlyer
from pjn.models import Entrada, ExpedienteResumen
from pjn.utils.logging import setup_logging, get_logger

setup_logging(level="INFO")
logger = get_logger(__name__)

def test_config():
    """Prueba que la configuración se puede crear y cargar."""
    logger.info("=== Test 1: Configuración ===")

    # Crear config
    config = MonitorConfig(modo="laboral", headless=True)
    assert config.modo == "laboral"
    assert config.headless == True

    # Guardar y cargar
    test_path = "test_config.json"
    config.to_file(test_path)
    config2 = MonitorConfig.from_file(test_path)
    assert config2.modo == config.modo

    # Limpiar
    Path(test_path).unlink()

    logger.info("? Config OK")


def test_storage():
    """Prueba que el storage guarda y carga correctamente."""
    logger.info("=== Test 2: Storage ===")

    storage = StorageManager("test_data")

    # Test estado
    estado = EstadoMonitor()
    estado.errores_consecutivos_entradas = 5
    storage.guardar_estado(estado)

    estado2 = storage.cargar_estado()
    assert estado2.errores_consecutivos_entradas == 5

    # Test entradas
    entradas = [
        Entrada(
            numero="EXP-001",
            caratula="Caso de prueba",
            fecha="2024-01-01",
            evento="Notificación de prueba",
            tipo_evento="N"
        )
    ]
    storage.guardar_entradas(entradas)
    entradas2 = storage.cargar_entradas_conocidas()
    assert len(entradas2) == 1
    assert entradas2[0].numero == "EXP-001"

    # Limpiar
    import shutil
    shutil.rmtree("test_data")

    logger.info("? Storage OK")


def test_detector():
    """Prueba que el detector identifica cambios correctamente."""
    logger.info("=== Test 3: Detector de cambios ===")

    detector = DetectorCambios()

    # Test entradas nuevas
    conocidas = [
        Entrada(numero="EXP-001", caratula="Caso 1", fecha="2024-01-01", evento="Evento 1", tipo_evento="N")
    ]
    actuales = [
        Entrada(numero="EXP-001", caratula="Caso 1", fecha="2024-01-01", evento="Evento 1", tipo_evento="N"),
        Entrada(numero="EXP-002", caratula="Caso 2", fecha="2024-01-02", evento="Evento 2", tipo_evento="N")
    ]

    nuevas = detector.detectar_nuevas_entradas(actuales, conocidas)
    assert len(nuevas) == 1
    assert nuevas[0].numero == "EXP-002"

    # Test expedientes con cambios
    anteriores = [
        ExpedienteResumen(
            numero="EXP-001",
            dependencia="Juzgado Civil 1",
            caratula="Caso 1",
            situacion="Activo",
            ultima_actuacion="Actuacion 1"
        )
    ]
    actuales_exp = [
        ExpedienteResumen(
            numero="EXP-001",
            dependencia="Juzgado Civil 1",
            caratula="Caso 1",
            situacion="Activo",
            ultima_actuacion="Actuacion 2"  # CAMBIO AQUI
        )
    ]

    cambios = detector.detectar_cambios_expedientes(actuales_exp, anteriores)
    assert len(cambios) == 1
    assert cambios[0].numero == "EXP-001"

    logger.info("? Detector OK")


def test_notifier():
    """Prueba que el notificador se inicializa correctamente."""
    logger.info("=== Test 4: Notificador ===")

    notificador = NotificadorPlyer()
    # Solo verificamos que se inicialice sin error
    # No enviamos notificación real para no molestar
    assert notificador is not None

    logger.info("? Notificador OK")


def main():
    """Ejecuta todos los tests."""
    logger.info("=" * 60)
    logger.info("PRUEBA SIMPLIFICADA DEL MONITOR PJN")
    logger.info("=" * 60)

    try:
        test_config()
        test_storage()
        test_detector()
        test_notifier()

        logger.info("\n" + "=" * 60)
        logger.info("? TODOS LOS TESTS PASARON!")
        logger.info("=" * 60)
        return 0

    except Exception as e:
        logger.error(f"\n? ERROR: {e}", exc_info=True)
        logger.info("\n" + "=" * 60)
        logger.info("? TESTS FALLARON")
        logger.info("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())
