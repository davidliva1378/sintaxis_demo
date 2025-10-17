#!/usr/bin/env python3
"""Herramienta de benchmarking para el módulo pjn.

Este script realiza mediciones de performance de las funciones críticas
del sistema, identificando cuellos de botella y oportunidades de optimización.

Usage:
    python scripts/performance_benchmark.py
    python scripts/performance_benchmark.py --profile
    python scripts/performance_benchmark.py --memory
"""

import asyncio
import cProfile
import io
import json
import pstats
import time
import tracemalloc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from pjn.models import Actuacion, ExpedienteResumen, Entrada
from pjn.parsers.expedientes_parser import parse_expediente_resumen
from pjn.models._utils import coerce_str, coerce_int, coerce_bool, get_first


# ============================================================================
# MÉTRICAS Y RESULTADOS
# ============================================================================

@dataclass
class BenchmarkResult:
    """Resultado de un benchmark individual."""

    name: str
    iterations: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    ops_per_second: float
    memory_usage: int = 0  # bytes

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "iterations": self.iterations,
            "total_time_seconds": round(self.total_time, 6),
            "avg_time_ms": round(self.avg_time * 1000, 3),
            "min_time_ms": round(self.min_time * 1000, 3),
            "max_time_ms": round(self.max_time * 1000, 3),
            "ops_per_second": round(self.ops_per_second, 2),
            "memory_usage_kb": round(self.memory_usage / 1024, 2),
        }


@dataclass
class BenchmarkSuite:
    """Suite completa de benchmarks."""

    results: list[BenchmarkResult] = field(default_factory=list)
    total_time: float = 0.0
    timestamp: str = ""

    def add_result(self, result: BenchmarkResult) -> None:
        self.results.append(result)
        self.total_time += result.total_time

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "total_time_seconds": round(self.total_time, 6),
            "total_benchmarks": len(self.results),
            "results": [r.to_dict() for r in self.results],
        }


# ============================================================================
# FUNCIONES DE BENCHMARKING
# ============================================================================

def benchmark_function(func: Callable, iterations: int = 1000, **kwargs) -> BenchmarkResult:
    """Ejecuta un benchmark de una función sincrónica.

    Args:
        func: Función a benchmarkear
        iterations: Número de iteraciones
        **kwargs: Argumentos para la función

    Returns:
        Resultado del benchmark
    """
    times = []

    # Warmup
    for _ in range(min(10, iterations // 10)):
        func(**kwargs)

    # Benchmark real
    tracemalloc.start()
    start_memory = tracemalloc.get_traced_memory()[0]

    for _ in range(iterations):
        start = time.perf_counter()
        func(**kwargs)
        end = time.perf_counter()
        times.append(end - start)

    end_memory = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()

    total_time = sum(times)
    avg_time = total_time / iterations
    min_time = min(times)
    max_time = max(times)
    ops_per_second = iterations / total_time if total_time > 0 else 0
    memory_usage = end_memory - start_memory

    return BenchmarkResult(
        name=func.__name__,
        iterations=iterations,
        total_time=total_time,
        avg_time=avg_time,
        min_time=min_time,
        max_time=max_time,
        ops_per_second=ops_per_second,
        memory_usage=memory_usage,
    )


async def benchmark_async_function(
    func: Callable,
    iterations: int = 1000,
    **kwargs
) -> BenchmarkResult:
    """Ejecuta un benchmark de una función asíncrona.

    Args:
        func: Función async a benchmarkear
        iterations: Número de iteraciones
        **kwargs: Argumentos para la función

    Returns:
        Resultado del benchmark
    """
    times = []

    # Warmup
    for _ in range(min(10, iterations // 10)):
        await func(**kwargs)

    # Benchmark real
    tracemalloc.start()
    start_memory = tracemalloc.get_traced_memory()[0]

    for _ in range(iterations):
        start = time.perf_counter()
        await func(**kwargs)
        end = time.perf_counter()
        times.append(end - start)

    end_memory = tracemalloc.get_traced_memory()[0]
    tracemalloc.stop()

    total_time = sum(times)
    avg_time = total_time / iterations
    min_time = min(times)
    max_time = max(times)
    ops_per_second = iterations / total_time if total_time > 0 else 0
    memory_usage = end_memory - start_memory

    return BenchmarkResult(
        name=func.__name__,
        iterations=iterations,
        total_time=total_time,
        avg_time=avg_time,
        min_time=min_time,
        max_time=max_time,
        ops_per_second=ops_per_second,
        memory_usage=memory_usage,
    )


# ============================================================================
# BENCHMARKS ESPECÍFICOS
# ============================================================================

def benchmark_parse_expediente_resumen(iterations: int = 10000) -> BenchmarkResult:
    """Benchmark de parse_expediente_resumen()."""
    valores = ["EXP001/2025", "Juzgado Federal 1", "CASO DE PRUEBA S/ EXPEDIENTE", "Activo", "15/10/2025"]

    return benchmark_function(
        parse_expediente_resumen,
        iterations=iterations,
        valores=valores
    )


def benchmark_actuacion_to_dict(iterations: int = 10000) -> BenchmarkResult:
    """Benchmark de Actuacion.to_dict()."""
    actuacion = Actuacion(
        indice=1,
        oficina="Secretaría Federal",
        oficina_completa="Secretaría Federal del Juzgado",
        fecha="2025-10-15",
        tipo="RESOLUCION",
        detalle="Se resuelve hacer lugar a la petición formulada",
        foja="Foja 123",
        tiene_archivo=True,
        nombre_archivo="documento.pdf",
        tipo_archivo="pdf"
    )

    result = benchmark_function(
        actuacion.to_dict,
        iterations=iterations
    )
    result.name = "Actuacion.to_dict"
    return result


def benchmark_coerce_functions(iterations: int = 50000) -> list[BenchmarkResult]:
    """Benchmark de funciones coerce_* en _utils."""
    results = []

    # coerce_str
    result = benchmark_function(
        coerce_str,
        iterations=iterations,
        value="  Test String  "
    )
    result.name = "coerce_str"
    results.append(result)

    # coerce_int
    result = benchmark_function(
        coerce_int,
        iterations=iterations,
        value="12345",
        default=0
    )
    result.name = "coerce_int"
    results.append(result)

    # coerce_bool
    result = benchmark_function(
        coerce_bool,
        iterations=iterations,
        value="true",
        default=False
    )
    result.name = "coerce_bool"
    results.append(result)

    # get_first (no tiene kwargs, usa *args)
    data = {"key1": None, "key2": "value2", "key3": "value3"}

    def wrapper_get_first():
        return get_first(data, "missing", "key2", "key3", default=None)

    result = benchmark_function(
        wrapper_get_first,
        iterations=iterations
    )
    result.name = "get_first"
    results.append(result)

    return results


def benchmark_model_creation(iterations: int = 10000) -> list[BenchmarkResult]:
    """Benchmark de creación de modelos de dominio."""
    results = []

    # ExpedienteResumen.from_dict
    data = {
        "numero": "EXP001/2025",
        "dependencia": "Juzgado Federal 1",
        "caratula": "CASO DE PRUEBA S/ EXPEDIENTE",
        "situacion": "Activo",
        "ultima_actuacion": "2025-10-15"
    }

    result = benchmark_function(
        ExpedienteResumen.from_dict,
        iterations=iterations,
        data=data
    )
    result.name = "ExpedienteResumen.from_dict"
    results.append(result)

    # Actuacion.from_dict
    data_act = {
        "Indice": 1,
        "Oficina": "Secretaría",
        "Fecha": "15/10/2025",
        "Tipo": "Resolución",
        "Detalle": "Se resuelve...",
        "TieneArchivo": True
    }

    result = benchmark_function(
        Actuacion.from_dict,
        iterations=iterations,
        data=data_act
    )
    result.name = "Actuacion.from_dict"
    results.append(result)

    # Entrada.from_dict
    data_ent = {
        "numero": "EXP001/2025",
        "caratula": "CASO DE PRUEBA",
        "fecha": "2025-10-15",
        "evento": "Notificación",
        "leida": False
    }

    result = benchmark_function(
        Entrada.from_dict,
        iterations=iterations,
        data=data_ent
    )
    result.name = "Entrada.from_dict"
    results.append(result)

    return results


def benchmark_json_operations(iterations: int = 1000) -> list[BenchmarkResult]:
    """Benchmark de operaciones con JSON."""
    results = []

    # Crear datos de prueba
    expediente = ExpedienteResumen(
        numero="EXP001/2025",
        dependencia="Juzgado Federal 1",
        caratula="CASO DE PRUEBA S/ EXPEDIENTE",
        situacion="Activo",
        ultima_actuacion="2025-10-15"
    )

    actuaciones = [
        Actuacion(
            indice=i,
            oficina=f"Secretaría {i}",
            fecha="2025-10-15",
            tipo="Resolución",
            detalle=f"Detalle {i}",
            tiene_archivo=True
        )
        for i in range(50)
    ]

    # to_dict()
    result = benchmark_function(
        expediente.to_dict,
        iterations=iterations
    )
    result.name = "ExpedienteResumen.to_dict"
    results.append(result)

    # Serialización JSON de lista de actuaciones
    def serialize_actuaciones():
        return json.dumps([act.to_dict() for act in actuaciones])

    result = benchmark_function(
        serialize_actuaciones,
        iterations=iterations
    )
    result.name = "serialize_50_actuaciones"
    results.append(result)

    # Deserialización JSON
    json_str = json.dumps([act.to_dict() for act in actuaciones])

    def deserialize_actuaciones():
        data = json.loads(json_str)
        return [Actuacion.from_dict(d) for d in data]

    result = benchmark_function(
        deserialize_actuaciones,
        iterations=iterations
    )
    result.name = "deserialize_50_actuaciones"
    results.append(result)

    return results


# ============================================================================
# PROFILING CON CPROFILE
# ============================================================================

def profile_function(func: Callable, *args, **kwargs) -> str:
    """Ejecuta profiling de una función con cProfile.

    Args:
        func: Función a perfilar
        *args: Argumentos posicionales
        **kwargs: Argumentos nombrados

    Returns:
        Reporte de profiling como string
    """
    profiler = cProfile.Profile()
    profiler.enable()

    func(*args, **kwargs)

    profiler.disable()

    # Generar reporte
    stream = io.StringIO()
    stats = pstats.Stats(profiler, stream=stream)
    stats.strip_dirs()
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # Top 20 funciones

    return stream.getvalue()


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Ejecuta la suite completa de benchmarks."""
    print("=" * 80)
    print("PERFORMANCE BENCHMARK - PJN Sistema v5")
    print("=" * 80)
    print()

    suite = BenchmarkSuite(timestamp=time.strftime("%Y-%m-%d %H:%M:%S"))

    # 1. Parsers
    print("📊 Benchmarking Parsers...")
    result = benchmark_parse_expediente_resumen()
    suite.add_result(result)
    print(f"  ✓ {result.name}: {result.avg_time*1000:.3f} ms/op ({result.ops_per_second:.0f} ops/s)")

    result = benchmark_actuacion_to_dict()
    suite.add_result(result)
    print(f"  ✓ {result.name}: {result.avg_time*1000:.3f} ms/op ({result.ops_per_second:.0f} ops/s)")

    # 2. Coerce functions
    print("\n📊 Benchmarking Coerce Functions...")
    results = benchmark_coerce_functions()
    for result in results:
        suite.add_result(result)
        print(f"  ✓ {result.name}: {result.avg_time*1000:.3f} ms/op ({result.ops_per_second:.0f} ops/s)")

    # 3. Model creation
    print("\n📊 Benchmarking Model Creation...")
    results = benchmark_model_creation()
    for result in results:
        suite.add_result(result)
        print(f"  ✓ {result.name}: {result.avg_time*1000:.3f} ms/op ({result.ops_per_second:.0f} ops/s)")

    # 4. JSON operations
    print("\n📊 Benchmarking JSON Operations...")
    results = benchmark_json_operations()
    for result in results:
        suite.add_result(result)
        print(f"  ✓ {result.name}: {result.avg_time*1000:.3f} ms/op ({result.ops_per_second:.0f} ops/s)")

    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"Total de benchmarks: {len(suite.results)}")
    print(f"Tiempo total: {suite.total_time:.3f} segundos")
    print()

    # Top 5 más rápidos
    sorted_results = sorted(suite.results, key=lambda r: r.avg_time)
    print("🚀 Top 5 Operaciones Más Rápidas:")
    for i, result in enumerate(sorted_results[:5], 1):
        print(f"  {i}. {result.name}: {result.avg_time*1000:.3f} ms/op")

    print()

    # Top 5 más lentos
    print("🐌 Top 5 Operaciones Más Lentas:")
    for i, result in enumerate(reversed(sorted_results[-5:]), 1):
        print(f"  {i}. {result.name}: {result.avg_time*1000:.3f} ms/op")

    # Guardar resultados
    output_dir = Path(__file__).parent.parent / "documentacion" / "performance"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / f"benchmark_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(suite.to_dict(), f, indent=2, ensure_ascii=False)

    print(f"\n✅ Resultados guardados en: {output_file}")


if __name__ == "__main__":
    main()
