"""
Sistema de métricas para servidor MCP.

Proporciona:
- Tracking de llamadas a tools
- Latencias promedio por tool
- Tasas de error
- Historial de uso
- Estadísticas exportables

Uso:
    from sintaxis_mcp.core.metrics import get_metrics, record_call

    # Registrar llamada
    record_call("buscar_expedientes", duration=0.5, error=False)

    # Obtener estadísticas
    stats = get_metrics().get_stats()
"""

import time
import threading
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import json
from pathlib import Path


@dataclass
class ToolCall:
    """Representa una llamada a un tool."""
    tool_name: str
    timestamp: datetime
    duration_ms: float
    success: bool
    error_type: Optional[str] = None


@dataclass
class ToolStats:
    """Estadísticas acumuladas de un tool."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    last_called: Optional[datetime] = None
    errors_by_type: Dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def avg_duration_ms(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.total_duration_ms / self.total_calls

    @property
    def error_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.failed_calls / self.total_calls

    @property
    def success_rate(self) -> float:
        return 1.0 - self.error_rate

    def to_dict(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "successful_calls": self.successful_calls,
            "failed_calls": self.failed_calls,
            "avg_duration_ms": round(self.avg_duration_ms, 2),
            "min_duration_ms": round(self.min_duration_ms, 2) if self.min_duration_ms != float('inf') else None,
            "max_duration_ms": round(self.max_duration_ms, 2),
            "success_rate": round(self.success_rate * 100, 1),
            "error_rate": round(self.error_rate * 100, 1),
            "last_called": self.last_called.isoformat() if self.last_called else None,
            "errors_by_type": dict(self.errors_by_type)
        }


class MetricsCollector:
    """
    Colector de métricas para el servidor MCP.

    Thread-safe para uso en entornos concurrentes.
    """

    # Singleton
    _instance = None
    _lock = threading.Lock()

    # Retención de historial
    HISTORY_RETENTION_HOURS = 24
    MAX_HISTORY_SIZE = 10000

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, persist_path: Optional[Path] = None):
        if self._initialized:
            return

        self._stats: Dict[str, ToolStats] = defaultdict(ToolStats)
        self._history: deque = deque(maxlen=self.MAX_HISTORY_SIZE)
        self._persist_path = persist_path or Path("var/metrics/mcp_metrics.json")
        self._start_time = datetime.now()
        self._lock = threading.RLock()

        # Cargar métricas persistidas si existen
        self._load_persisted()
        self._initialized = True

    def record_call(
        self,
        tool_name: str,
        duration_ms: float,
        success: bool = True,
        error_type: Optional[str] = None
    ) -> None:
        """
        Registra una llamada a un tool.

        Args:
            tool_name: Nombre del tool llamado
            duration_ms: Duración en milisegundos
            success: Si la llamada fue exitosa
            error_type: Tipo de error si hubo fallo
        """
        with self._lock:
            now = datetime.now()

            # Actualizar estadísticas del tool
            stats = self._stats[tool_name]
            stats.total_calls += 1
            stats.total_duration_ms += duration_ms
            stats.last_called = now

            if duration_ms < stats.min_duration_ms:
                stats.min_duration_ms = duration_ms
            if duration_ms > stats.max_duration_ms:
                stats.max_duration_ms = duration_ms

            if success:
                stats.successful_calls += 1
            else:
                stats.failed_calls += 1
                if error_type:
                    stats.errors_by_type[error_type] += 1

            # Agregar al historial
            call = ToolCall(
                tool_name=tool_name,
                timestamp=now,
                duration_ms=duration_ms,
                success=success,
                error_type=error_type
            )
            self._history.append(call)

    def get_tool_stats(self, tool_name: str) -> Optional[ToolStats]:
        """Obtiene estadísticas de un tool específico."""
        with self._lock:
            if tool_name in self._stats:
                return self._stats[tool_name]
            return None

    def get_all_stats(self) -> Dict[str, dict]:
        """Obtiene estadísticas de todos los tools."""
        with self._lock:
            return {
                name: stats.to_dict()
                for name, stats in self._stats.items()
            }

    def get_top_tools(self, limit: int = 10, by: str = "calls") -> List[dict]:
        """
        Obtiene los tools más utilizados.

        Args:
            limit: Número máximo de resultados
            by: Ordenar por 'calls', 'duration', 'errors'
        """
        with self._lock:
            tools_list = [
                {"name": name, **stats.to_dict()}
                for name, stats in self._stats.items()
            ]

            if by == "calls":
                key = lambda x: x["total_calls"]
            elif by == "duration":
                key = lambda x: x["avg_duration_ms"]
            elif by == "errors":
                key = lambda x: x["failed_calls"]
            else:
                key = lambda x: x["total_calls"]

            return sorted(tools_list, key=key, reverse=True)[:limit]

    def get_recent_calls(self, minutes: int = 60, tool_name: Optional[str] = None) -> List[dict]:
        """
        Obtiene llamadas recientes.

        Args:
            minutes: Ventana de tiempo en minutos
            tool_name: Filtrar por tool específico
        """
        with self._lock:
            cutoff = datetime.now() - timedelta(minutes=minutes)
            calls = []

            for call in self._history:
                if call.timestamp < cutoff:
                    continue
                if tool_name and call.tool_name != tool_name:
                    continue

                calls.append({
                    "tool_name": call.tool_name,
                    "timestamp": call.timestamp.isoformat(),
                    "duration_ms": round(call.duration_ms, 2),
                    "success": call.success,
                    "error_type": call.error_type
                })

            return calls

    def get_error_summary(self) -> dict:
        """Obtiene resumen de errores."""
        with self._lock:
            total_errors = sum(s.failed_calls for s in self._stats.values())
            total_calls = sum(s.total_calls for s in self._stats.values())

            # Tools con más errores
            error_tools = sorted(
                [
                    {"name": name, "errors": stats.failed_calls, "error_rate": stats.error_rate}
                    for name, stats in self._stats.items()
                    if stats.failed_calls > 0
                ],
                key=lambda x: x["errors"],
                reverse=True
            )[:5]

            # Errores por tipo
            errors_by_type: Dict[str, int] = defaultdict(int)
            for stats in self._stats.values():
                for error_type, count in stats.errors_by_type.items():
                    errors_by_type[error_type] += count

            return {
                "total_errors": total_errors,
                "total_calls": total_calls,
                "global_error_rate": round(total_errors / total_calls * 100, 2) if total_calls > 0 else 0,
                "tools_with_errors": error_tools,
                "errors_by_type": dict(errors_by_type)
            }

    def get_performance_summary(self) -> dict:
        """Obtiene resumen de rendimiento."""
        with self._lock:
            all_durations = [s.avg_duration_ms for s in self._stats.values() if s.total_calls > 0]

            # Tools más lentos
            slow_tools = sorted(
                [
                    {"name": name, "avg_ms": stats.avg_duration_ms, "max_ms": stats.max_duration_ms}
                    for name, stats in self._stats.items()
                    if stats.total_calls > 0
                ],
                key=lambda x: x["avg_ms"],
                reverse=True
            )[:5]

            # Tools más rápidos
            fast_tools = sorted(
                [
                    {"name": name, "avg_ms": stats.avg_duration_ms, "min_ms": stats.min_duration_ms}
                    for name, stats in self._stats.items()
                    if stats.total_calls > 0
                ],
                key=lambda x: x["avg_ms"]
            )[:5]

            return {
                "global_avg_ms": round(sum(all_durations) / len(all_durations), 2) if all_durations else 0,
                "slowest_tools": slow_tools,
                "fastest_tools": fast_tools
            }

    def get_stats(self) -> dict:
        """Obtiene estadísticas completas del sistema."""
        with self._lock:
            total_calls = sum(s.total_calls for s in self._stats.values())
            total_errors = sum(s.failed_calls for s in self._stats.values())
            uptime = datetime.now() - self._start_time

            return {
                "summary": {
                    "total_calls": total_calls,
                    "total_errors": total_errors,
                    "success_rate": round((1 - total_errors / total_calls) * 100, 2) if total_calls > 0 else 100,
                    "unique_tools_used": len([s for s in self._stats.values() if s.total_calls > 0]),
                    "uptime_seconds": int(uptime.total_seconds()),
                    "uptime_human": str(uptime).split('.')[0],
                    "history_size": len(self._history)
                },
                "by_tool": self.get_all_stats(),
                "top_10_by_calls": self.get_top_tools(10, "calls"),
                "errors": self.get_error_summary(),
                "performance": self.get_performance_summary()
            }

    def reset(self) -> None:
        """Resetea todas las métricas."""
        with self._lock:
            self._stats.clear()
            self._history.clear()
            self._start_time = datetime.now()

    def persist(self) -> None:
        """Persiste métricas a disco."""
        with self._lock:
            try:
                self._persist_path.parent.mkdir(parents=True, exist_ok=True)

                data = {
                    "start_time": self._start_time.isoformat(),
                    "saved_at": datetime.now().isoformat(),
                    "stats": {
                        name: {
                            "total_calls": s.total_calls,
                            "successful_calls": s.successful_calls,
                            "failed_calls": s.failed_calls,
                            "total_duration_ms": s.total_duration_ms,
                            "min_duration_ms": s.min_duration_ms if s.min_duration_ms != float('inf') else None,
                            "max_duration_ms": s.max_duration_ms,
                            "last_called": s.last_called.isoformat() if s.last_called else None,
                            "errors_by_type": dict(s.errors_by_type)
                        }
                        for name, s in self._stats.items()
                    }
                }

                with open(self._persist_path, 'w') as f:
                    json.dump(data, f, indent=2)

            except Exception as e:
                print(f"Error persisting metrics: {e}")

    def _load_persisted(self) -> None:
        """Carga métricas persistidas."""
        if not self._persist_path.exists():
            return

        try:
            with open(self._persist_path) as f:
                data = json.load(f)

            self._start_time = datetime.fromisoformat(data.get("start_time", datetime.now().isoformat()))

            for name, s in data.get("stats", {}).items():
                stats = ToolStats()
                stats.total_calls = s.get("total_calls", 0)
                stats.successful_calls = s.get("successful_calls", 0)
                stats.failed_calls = s.get("failed_calls", 0)
                stats.total_duration_ms = s.get("total_duration_ms", 0.0)
                stats.min_duration_ms = s.get("min_duration_ms") or float('inf')
                stats.max_duration_ms = s.get("max_duration_ms", 0.0)
                if s.get("last_called"):
                    stats.last_called = datetime.fromisoformat(s["last_called"])
                stats.errors_by_type = defaultdict(int, s.get("errors_by_type", {}))
                self._stats[name] = stats

        except Exception as e:
            print(f"Error loading persisted metrics: {e}")


# Singleton global
_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Obtiene instancia singleton del colector de métricas."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


def record_call(
    tool_name: str,
    duration_ms: float,
    success: bool = True,
    error_type: Optional[str] = None
) -> None:
    """Registra una llamada (atajo para get_metrics().record_call())."""
    get_metrics().record_call(tool_name, duration_ms, success, error_type)


class MetricsContext:
    """
    Context manager para medir duración de llamadas automáticamente.

    Uso:
        with MetricsContext("buscar_expedientes") as ctx:
            result = tools_service.execute_tool("buscar_expedientes", args)
        # Automáticamente registra duración y éxito/fallo
    """

    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.start_time: Optional[float] = None
        self.error: Optional[Exception] = None

    def __enter__(self) -> "MetricsContext":
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000

        success = exc_type is None
        error_type = None

        if exc_type:
            error_type = exc_type.__name__

        record_call(
            self.tool_name,
            duration_ms,
            success=success,
            error_type=error_type
        )

        # No suprimir la excepción
        return False
