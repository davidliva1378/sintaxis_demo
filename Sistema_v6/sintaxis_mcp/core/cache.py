"""
Sistema de cache para resultados de tools MCP.

Proporciona:
- Cache LRU en memoria con TTL configurable
- Políticas de cache por tool
- Invalidación selectiva
- Estadísticas de uso

Uso:
    from sintaxis_mcp.core.cache import get_cache, cached_call

    # Usar decorador
    @cached_call(ttl=300)
    def my_expensive_function():
        ...

    # O usar directamente
    cache = get_cache()
    result = cache.get("key")
    if result is None:
        result = compute_expensive()
        cache.set("key", result, ttl=300)
"""

import hashlib
import json
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, Optional, TypeVar, Generic
from functools import wraps


T = TypeVar('T')


@dataclass
class CacheEntry:
    """Entrada de cache con TTL."""
    value: Any
    created_at: float
    expires_at: float
    hits: int = 0
    tool_name: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at

    @property
    def ttl_remaining(self) -> float:
        return max(0, self.expires_at - time.time())


@dataclass
class CacheStats:
    """Estadísticas del cache."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    expirations: int = 0
    total_sets: int = 0
    total_invalidations: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> dict:
        return {
            "hits": self.hits,
            "misses": self.misses,
            "evictions": self.evictions,
            "expirations": self.expirations,
            "total_sets": self.total_sets,
            "total_invalidations": self.total_invalidations,
            "hit_rate": round(self.hit_rate * 100, 2)
        }


# Configuración de TTL por defecto para cada tipo de tool
DEFAULT_TTL_BY_TOOL = {
    # Estadísticas - se pueden cachear más tiempo
    "estadisticas_sistema": 300,      # 5 minutos
    "estadisticas_expediente": 300,
    "estadisticas_procesamiento": 300,
    "estadisticas_entidades": 300,
    "estadisticas_monitoreo": 60,     # 1 minuto (puede cambiar más)
    "resumen_vencimientos": 180,      # 3 minutos

    # Conteos y agregados - cache medio
    "contar_expedientes": 120,        # 2 minutos
    "expedientes_por_dependencia": 120,
    "actuaciones_por_tipo": 120,
    "entidades_por_tipo": 120,

    # Búsquedas frecuentes - cache corto
    "listar_expedientes": 60,
    "expedientes_recientes": 60,
    "vencimientos_pendientes": 60,
    "vencimientos_urgentes": 60,
    "proximos_vencimientos": 60,

    # Detalle de expediente - cache corto
    "obtener_expediente": 60,
    "resumen_expediente": 120,

    # Sin cache (datos que cambian frecuentemente o escrituras)
    "buscar_expedientes": 30,         # Búsquedas pueden variar
    "buscar_actuaciones": 30,
    "buscar_entidades": 30,
    "estado_monitoreo": 30,
    "listar_cambios_monitoreo": 0,    # Sin cache - datos en tiempo real
    "sincronizar_expedientes_monitoreo": 0,  # Operación de escritura
    "agregar_expediente_monitoreo": 0,
    "pausar_expediente_monitoreo": 0,
    "reanudar_expediente_monitoreo": 0,
}

# TTL por defecto si no está especificado
DEFAULT_TTL = 60  # 1 minuto


class ResultCache:
    """
    Cache LRU en memoria con TTL configurable por tool.

    Thread-safe para uso en entornos concurrentes.
    """

    # Singleton
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, max_size: int = 1000, default_ttl: int = DEFAULT_TTL):
        if self._initialized:
            return

        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._stats = CacheStats()
        self._lock = threading.RLock()
        self._ttl_config = dict(DEFAULT_TTL_BY_TOOL)
        self._enabled = True
        self._initialized = True

    def get_ttl_for_tool(self, tool_name: str) -> int:
        """Obtiene TTL configurado para un tool."""
        return self._ttl_config.get(tool_name, self._default_ttl)

    def configure_ttl(self, tool_name: str, ttl: int) -> None:
        """Configura TTL para un tool específico."""
        with self._lock:
            self._ttl_config[tool_name] = ttl

    def is_cacheable(self, tool_name: str) -> bool:
        """Verifica si un tool debe ser cacheado."""
        return self.get_ttl_for_tool(tool_name) > 0

    def _make_key(self, tool_name: str, args: Dict[str, Any]) -> str:
        """Genera una clave única para tool + argumentos."""
        # Normalizar argumentos para la clave
        normalized = json.dumps(args, sort_keys=True, default=str)
        args_hash = hashlib.md5(normalized.encode()).hexdigest()[:12]
        return f"{tool_name}:{args_hash}"

    def get(self, tool_name: str, args: Dict[str, Any]) -> Optional[Any]:
        """
        Obtiene un valor del cache.

        Args:
            tool_name: Nombre del tool
            args: Argumentos del tool

        Returns:
            Valor cacheado o None si no existe/expiró
        """
        if not self._enabled:
            return None

        key = self._make_key(tool_name, args)

        with self._lock:
            entry = self._cache.get(key)

            if entry is None:
                self._stats.misses += 1
                return None

            if entry.is_expired:
                self._cache.pop(key, None)
                self._stats.misses += 1
                self._stats.expirations += 1
                return None

            # Hit - mover al final (más reciente)
            self._cache.move_to_end(key)
            entry.hits += 1
            self._stats.hits += 1

            return entry.value

    def set(
        self,
        tool_name: str,
        args: Dict[str, Any],
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Guarda un valor en cache.

        Args:
            tool_name: Nombre del tool
            args: Argumentos del tool
            value: Valor a cachear
            ttl: TTL en segundos (usa default si no se especifica)
        """
        if not self._enabled:
            return

        if ttl is None:
            ttl = self.get_ttl_for_tool(tool_name)

        # No cachear si TTL es 0
        if ttl <= 0:
            return

        key = self._make_key(tool_name, args)
        now = time.time()

        with self._lock:
            # Evictar si estamos al límite
            while len(self._cache) >= self._max_size:
                # Remover el más antiguo (primero en OrderedDict)
                self._cache.popitem(last=False)
                self._stats.evictions += 1

            # Guardar entrada
            self._cache[key] = CacheEntry(
                value=value,
                created_at=now,
                expires_at=now + ttl,
                tool_name=tool_name
            )
            self._stats.total_sets += 1

    def invalidate(self, tool_name: Optional[str] = None) -> int:
        """
        Invalida entradas del cache.

        Args:
            tool_name: Si se especifica, solo invalida ese tool.
                      Si es None, invalida todo el cache.

        Returns:
            Número de entradas invalidadas
        """
        with self._lock:
            if tool_name is None:
                count = len(self._cache)
                self._cache.clear()
                self._stats.total_invalidations += count
                return count

            # Invalidar solo entradas de un tool específico
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if entry.tool_name == tool_name
            ]
            for key in keys_to_remove:
                del self._cache[key]

            self._stats.total_invalidations += len(keys_to_remove)
            return len(keys_to_remove)

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalida entradas cuya clave coincida con un patrón.

        Args:
            pattern: Substring que debe estar en la clave

        Returns:
            Número de entradas invalidadas
        """
        with self._lock:
            keys_to_remove = [
                key for key in self._cache.keys()
                if pattern in key
            ]
            for key in keys_to_remove:
                del self._cache[key]

            self._stats.total_invalidations += len(keys_to_remove)
            return len(keys_to_remove)

    def cleanup_expired(self) -> int:
        """
        Limpia entradas expiradas.

        Returns:
            Número de entradas limpiadas
        """
        with self._lock:
            now = time.time()
            keys_to_remove = [
                key for key, entry in self._cache.items()
                if entry.expires_at < now
            ]
            for key in keys_to_remove:
                del self._cache[key]

            self._stats.expirations += len(keys_to_remove)
            return len(keys_to_remove)

    def get_stats(self) -> dict:
        """Obtiene estadísticas del cache."""
        with self._lock:
            # Estadísticas por tool
            by_tool: Dict[str, dict] = {}
            for key, entry in self._cache.items():
                tool = entry.tool_name or "unknown"
                if tool not in by_tool:
                    by_tool[tool] = {"count": 0, "hits": 0, "avg_age": 0}
                by_tool[tool]["count"] += 1
                by_tool[tool]["hits"] += entry.hits
                by_tool[tool]["avg_age"] += entry.age_seconds

            for tool, stats in by_tool.items():
                if stats["count"] > 0:
                    stats["avg_age"] = round(stats["avg_age"] / stats["count"], 1)

            return {
                "enabled": self._enabled,
                "size": len(self._cache),
                "max_size": self._max_size,
                "default_ttl": self._default_ttl,
                "stats": self._stats.to_dict(),
                "by_tool": by_tool
            }

    def enable(self) -> None:
        """Habilita el cache."""
        self._enabled = True

    def disable(self) -> None:
        """Deshabilita el cache."""
        self._enabled = False

    def reset_stats(self) -> None:
        """Resetea estadísticas."""
        with self._lock:
            self._stats = CacheStats()


# Singleton global
_cache: Optional[ResultCache] = None


def get_cache() -> ResultCache:
    """Obtiene instancia singleton del cache."""
    global _cache
    if _cache is None:
        _cache = ResultCache()
    return _cache


def cached_call(
    tool_name: str,
    ttl: Optional[int] = None
) -> Callable:
    """
    Decorador para cachear resultados de llamadas a tools.

    Args:
        tool_name: Nombre del tool
        ttl: TTL en segundos (usa default si no se especifica)

    Uso:
        @cached_call("estadisticas_sistema")
        def get_system_stats():
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            cache = get_cache()

            # Construir args como dict para la clave
            call_args = kwargs.copy()

            # Intentar obtener del cache
            cached_value = cache.get(tool_name, call_args)
            if cached_value is not None:
                return cached_value

            # Ejecutar y cachear
            result = func(*args, **kwargs)
            cache.set(tool_name, call_args, result, ttl)
            return result

        return wrapper
    return decorator


class CacheContext:
    """
    Context manager para operaciones con cache.

    Uso:
        with CacheContext("buscar_expedientes", {"texto": "perez"}) as ctx:
            if ctx.hit:
                return ctx.value
            result = expensive_operation()
            ctx.store(result)
            return result
    """

    def __init__(self, tool_name: str, args: Dict[str, Any], ttl: Optional[int] = None):
        self.tool_name = tool_name
        self.args = args
        self.ttl = ttl
        self.cache = get_cache()
        self.hit = False
        self.value: Any = None

    def __enter__(self) -> "CacheContext":
        self.value = self.cache.get(self.tool_name, self.args)
        self.hit = self.value is not None
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def store(self, value: Any) -> None:
        """Guarda un valor en cache."""
        self.cache.set(self.tool_name, self.args, value, self.ttl)
