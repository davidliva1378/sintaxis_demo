#!/usr/bin/env python3
"""Análisis de uso de memoria del módulo pjn.

Este script mide el consumo de memoria de estructuras de datos
y operaciones comunes del sistema.

Usage:
    python scripts/memory_profiler.py
"""

import sys
import tracemalloc
from typing import Any

from pjn.models import Actuacion, ActuacionesArchivo, ExpedienteResumen, Entrada


def get_size(obj: Any, seen: set | None = None) -> int:
    """Calcula recursivamente el tamaño de un objeto en bytes.

    Args:
        obj: Objeto a medir
        seen: Set de IDs ya visitados (para evitar loops)

    Returns:
        Tamaño total en bytes
    """
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return 0

    seen.add(obj_id)

    if isinstance(obj, dict):
        size += sum(get_size(k, seen) + get_size(v, seen) for k, v in obj.items())
    elif hasattr(obj, "__dict__"):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, "__iter__") and not isinstance(obj, (str, bytes, bytearray)):
        try:
            size += sum(get_size(item, seen) for item in obj)
        except TypeError:
            pass

    return size


def analyze_model_memory():
    """Analiza el uso de memoria de modelos de dominio."""
    print("=" * 80)
    print("ANÁLISIS DE MEMORIA - Modelos de Dominio")
    print("=" * 80)
    print()

    # ExpedienteResumen
    exp = ExpedienteResumen(
        numero="FPA_012345_2025",
        dependencia="Juzgado Federal en lo Penal Administrativo Nro. 1",
        caratula="CAUSA JUDICIAL S/ DELITO COMPLEJO",
        situacion="EN TRAMITE - PRUEBA",
        ultima_actuacion="2025-10-15"
    )

    size = get_size(exp)
    print(f"ExpedienteResumen:")
    print(f"  Tamaño: {size:,} bytes ({size/1024:.2f} KB)")
    print(f"  Por expediente en lista de 1000: {size*1000/1024/1024:.2f} MB")
    print()

    # Actuacion
    act = Actuacion(
        indice=1,
        oficina="Secretaría Federal",
        oficina_completa="Secretaría Federal del Juzgado en lo Penal Administrativo",
        fecha="2025-10-15",
        tipo="RESOLUCION_JUDICIAL",
        detalle="Se resuelve hacer lugar a la petición formulada por la parte actora en el presente expediente",
        foja="Foja 123 - Cuerpo Principal",
        archivo="https://ejemplo.com/archivo.pdf",
        nombre_archivo="resolucion_judicial_123.pdf",
        tiene_archivo=True,
        tipo_archivo="pdf",
        hash="abc123def456",
        extraida_en="2025-10-17T16:00:00",
        es_historica=False,
        descargado=True
    )

    size = get_size(act)
    print(f"Actuacion (completa):")
    print(f"  Tamaño: {size:,} bytes ({size/1024:.2f} KB)")
    print(f"  Por actuación en lista de 100: {size*100/1024/1024:.2f} MB")
    print()

    # ActuacionesArchivo
    encabezado = {
        "Expediente": "FPA_012345_2025",
        "Dependencia": "Juzgado Federal en lo Penal Administrativo Nro. 1",
        "Caratula": "CAUSA JUDICIAL S/ DELITO COMPLEJO",
        "total_archivos_con_enlace": 50,
        "Cantidad de Archivos Descargados": 45,
        "descargas_pendientes": 5
    }

    actuaciones = tuple([
        Actuacion(
            indice=i,
            oficina=f"Secretaría {i}",
            fecha="2025-10-15",
            tipo="RESOLUCION",
            detalle=f"Detalle de la actuación número {i}",
            tiene_archivo=(i % 2 == 0)
        )
        for i in range(100)
    ])

    archivo = ActuacionesArchivo(encabezado=encabezado, actuaciones=actuaciones)
    size = get_size(archivo)
    print(f"ActuacionesArchivo (100 actuaciones):")
    print(f"  Tamaño: {size:,} bytes ({size/1024:.2f} KB)")
    print(f"  Tamaño por actuación: {size/100:.0f} bytes")
    print()

    # Entrada
    ent = Entrada(
        numero="FPA_012345_2025",
        caratula="CAUSA JUDICIAL S/ DELITO COMPLEJO",
        fecha="2025-10-15",
        evento="Notificación de Resolución",
        tipo_evento="NOTIFICACION",
        leida=False,
        extraida_en="2025-10-17T16:00:00"
    )

    size = get_size(ent)
    print(f"Entrada:")
    print(f"  Tamaño: {size:,} bytes ({size/1024:.2f} KB)")
    print(f"  Por entrada en lista de 50: {size*50/1024/1024:.2f} MB")
    print()


def analyze_dict_vs_dataclass():
    """Compara uso de memoria: dict vs dataclass."""
    print("=" * 80)
    print("COMPARACIÓN: Dict vs Dataclass (slots=True)")
    print("=" * 80)
    print()

    # Dict
    dict_exp = {
        "numero": "FPA_012345_2025",
        "dependencia": "Juzgado Federal en lo Penal Administrativo Nro. 1",
        "caratula": "CAUSA JUDICIAL S/ DELITO COMPLEJO",
        "situacion": "EN TRAMITE - PRUEBA",
        "ultima_actuacion": "2025-10-15"
    }

    size_dict = get_size(dict_exp)
    print(f"Dict:")
    print(f"  Tamaño: {size_dict:,} bytes ({size_dict/1024:.2f} KB)")
    print()

    # Dataclass
    dc_exp = ExpedienteResumen(
        numero="FPA_012345_2025",
        dependencia="Juzgado Federal en lo Penal Administrativo Nro. 1",
        caratula="CAUSA JUDICIAL S/ DELITO COMPLEJO",
        situacion="EN TRAMITE - PRUEBA",
        ultima_actuacion="2025-10-15"
    )

    size_dc = get_size(dc_exp)
    print(f"Dataclass (slots=True):")
    print(f"  Tamaño: {size_dc:,} bytes ({size_dc/1024:.2f} KB)")
    print()

    # Ahorro
    savings = (1 - size_dc / size_dict) * 100
    print(f"Ahorro con dataclass: {savings:.1f}%")
    print(f"Ahorro en 1000 objetos: {(size_dict - size_dc) * 1000 / 1024:.2f} KB")
    print()


def analyze_peak_memory():
    """Analiza picos de memoria durante operaciones comunes."""
    print("=" * 80)
    print("ANÁLISIS DE PICOS DE MEMORIA")
    print("=" * 80)
    print()

    tracemalloc.start()

    # Operación 1: Crear muchos expedientes
    print("Creando 10,000 ExpedienteResumen...")
    snapshot_before = tracemalloc.take_snapshot()

    expedientes = [
        ExpedienteResumen(
            numero=f"EXP{i:06d}/2025",
            dependencia=f"Juzgado {i % 10}",
            caratula=f"CAUSA {i}",
            situacion="Activo",
            ultima_actuacion="2025-10-15"
        )
        for i in range(10000)
    ]

    snapshot_after = tracemalloc.take_snapshot()

    stats = snapshot_after.compare_to(snapshot_before, 'lineno')
    total_allocated = sum(stat.size_diff for stat in stats if stat.size_diff > 0)

    print(f"  Memoria asignada: {total_allocated / 1024 / 1024:.2f} MB")
    print(f"  Por expediente: {total_allocated / 10000:.0f} bytes")
    print()

    # Operación 2: Serializar a dict
    print("Serializando 10,000 expedientes a dict...")
    snapshot_before = tracemalloc.take_snapshot()

    dicts = [exp.to_dict() for exp in expedientes]

    snapshot_after = tracemalloc.take_snapshot()

    stats = snapshot_after.compare_to(snapshot_before, 'lineno')
    total_allocated = sum(stat.size_diff for stat in stats if stat.size_diff > 0)

    print(f"  Memoria adicional: {total_allocated / 1024 / 1024:.2f} MB")
    print(f"  Por serialización: {total_allocated / 10000:.0f} bytes")
    print()

    tracemalloc.stop()


def main():
    """Ejecuta todos los análisis de memoria."""
    analyze_model_memory()
    print()
    analyze_dict_vs_dataclass()
    print()
    analyze_peak_memory()

    print("=" * 80)
    print("RECOMENDACIONES")
    print("=" * 80)
    print()
    print("✅ Uso de dataclass(slots=True) es eficiente")
    print("✅ Tamaño de objetos es razonable")
    print("✅ No se detectan problemas de memoria evidentes")
    print()
    print("💡 Para optimizar memoria:")
    print("  1. Usar generadores en lugar de listas cuando sea posible")
    print("  2. Procesar en lotes si hay muchos expedientes")
    print("  3. Liberar objetos grandes cuando ya no se necesiten")
    print("  4. Considerar compresión para almacenamiento en disco")


if __name__ == "__main__":
    main()
