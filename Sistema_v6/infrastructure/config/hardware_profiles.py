"""Configuración de perfiles de hardware para IA.

Este módulo permite configurar el sistema de IA según el hardware disponible:
- development: Mac/CPU-only (recursos limitados)
- production: Intel i7 + RTX 3060 (GPU CUDA)
- production_max: Para equipos de alta gama

La configuración se detecta automáticamente o se puede forzar via HARDWARE_PROFILE env var.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Literal, Optional

logger = logging.getLogger(__name__)

# Tipo de perfil
HardwareProfileType = Literal["development", "production", "production_max", "auto"]


@dataclass
class HardwareProfile:
    """Configuración de hardware para servicios de IA.

    Attributes:
        name: Nombre del perfil
        description: Descripción del perfil

        # LLM (Ollama)
        llm_model: Modelo LLM a usar
        llm_num_ctx: Tamaño del contexto (tokens)
        llm_num_predict: Tokens máximos a generar
        llm_temperature: Temperatura por defecto

        # Embeddings
        embedding_model: Modelo de embeddings
        embedding_device: Dispositivo (cpu/cuda)
        embedding_batch_size: Tamaño de batch para embeddings

        # Reranking
        rerank_model: Modelo de reranking
        rerank_device: Dispositivo (cpu/cuda)
        rerank_top_k: Top K para reranking

        # NER
        ner_model: Modelo NER (GLiNER)
        ner_device: Dispositivo (cpu/cuda)
        ner_threshold: Umbral de confianza

        # General
        batch_size: Tamaño de batch general
        max_concurrent_requests: Requests concurrentes máximos
        use_gpu: Si usar GPU cuando esté disponible
    """
    name: str
    description: str

    # LLM (Ollama)
    llm_model: str = "llama3.1:8b"
    llm_num_ctx: int = 4096
    llm_num_predict: int = 2000
    llm_temperature: float = 0.7

    # Embeddings
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    embedding_device: str = "cpu"
    embedding_batch_size: int = 8

    # Reranking (Cross-Encoder)
    rerank_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    rerank_device: str = "cpu"
    rerank_top_k: int = 5

    # NER (GLiNER)
    ner_model: str = "urchade/gliner_multi-v2.1"
    ner_device: str = "cpu"
    ner_threshold: float = 0.5
    ner_llm_threshold: float = 0.6  # Umbral para usar LLM fallback
    ner_llm_enabled: bool = True  # Habilitar fallback LLM

    # General
    batch_size: int = 4
    max_concurrent_requests: int = 2
    use_gpu: bool = False

    # Query Expansion
    query_expansion_enabled: bool = True
    query_expansion_max_variations: int = 3


# Perfiles predefinidos
HARDWARE_PROFILES: dict[str, HardwareProfile] = {
    "development": HardwareProfile(
        name="development",
        description="Mac/CPU-only - Recursos limitados para desarrollo",
        llm_model="llama3.2:1b",
        llm_num_ctx=4096,
        llm_num_predict=1000,
        embedding_device="cpu",
        embedding_batch_size=4,
        rerank_device="cpu",
        rerank_top_k=3,
        ner_device="cpu",
        batch_size=4,
        max_concurrent_requests=2,
        use_gpu=False,
        query_expansion_enabled=True,
        query_expansion_max_variations=2,
    ),
    "production": HardwareProfile(
        name="production",
        description="Intel i7 + RTX 3060 12GB - GPU CUDA habilitada",
        llm_model="mistral-nemo:12b",
        llm_num_ctx=8192,
        llm_num_predict=2000,
        embedding_device="cuda",
        embedding_batch_size=32,
        rerank_device="cuda",
        rerank_top_k=5,
        ner_device="cuda",
        batch_size=16,
        max_concurrent_requests=8,
        use_gpu=True,
        query_expansion_enabled=True,
        query_expansion_max_variations=3,
    ),
    "production_max": HardwareProfile(
        name="production_max",
        description="Hardware de alta gama - Máxima calidad",
        llm_model="llama3.1:70b-q4_K_M",
        llm_num_ctx=16384,
        llm_num_predict=4000,
        embedding_device="cuda",
        embedding_batch_size=64,
        rerank_device="cuda",
        rerank_top_k=10,
        ner_device="cuda",
        batch_size=32,
        max_concurrent_requests=16,
        use_gpu=True,
        query_expansion_enabled=True,
        query_expansion_max_variations=5,
    ),
}


def _detect_cuda_available() -> bool:
    """Detecta si CUDA está disponible."""
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False


def _detect_hardware_profile() -> str:
    """Detecta automáticamente el perfil de hardware.

    Returns:
        Nombre del perfil detectado
    """
    if _detect_cuda_available():
        try:
            import torch
            gpu_mem = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            if gpu_mem >= 20:  # 20GB+ VRAM
                return "production_max"
            elif gpu_mem >= 8:  # 8GB+ VRAM (RTX 3060 tiene 12GB)
                return "production"
        except Exception:
            pass
        return "production"

    return "development"


def get_hardware_profile(profile_name: Optional[str] = None) -> HardwareProfile:
    """Obtiene el perfil de hardware configurado.

    Args:
        profile_name: Nombre del perfil. Si es None o "auto", detecta automáticamente.

    Returns:
        HardwareProfile configurado

    Example:
        >>> profile = get_hardware_profile()
        >>> print(f"Usando perfil: {profile.name}")
        >>> print(f"Modelo LLM: {profile.llm_model}")
    """
    # Prioridad: parámetro > env var > auto-detect
    if profile_name is None or profile_name == "auto":
        profile_name = os.environ.get("HARDWARE_PROFILE", "auto")

    if profile_name == "auto":
        profile_name = _detect_hardware_profile()
        logger.info(f"Hardware detectado automáticamente: {profile_name}")

    if profile_name not in HARDWARE_PROFILES:
        logger.warning(
            f"Perfil '{profile_name}' no encontrado. "
            f"Usando 'development'. Disponibles: {list(HARDWARE_PROFILES.keys())}"
        )
        profile_name = "development"

    profile = HARDWARE_PROFILES[profile_name]
    logger.info(f"Usando perfil de hardware: {profile.name} - {profile.description}")

    return profile


def get_device(profile: Optional[HardwareProfile] = None) -> str:
    """Obtiene el dispositivo a usar (cpu/cuda).

    Args:
        profile: Perfil de hardware. Si es None, obtiene el actual.

    Returns:
        "cuda" si GPU disponible y habilitada, "cpu" en caso contrario
    """
    if profile is None:
        profile = get_hardware_profile()

    if profile.use_gpu and _detect_cuda_available():
        return "cuda"
    return "cpu"


# Singleton del perfil activo
_active_profile: Optional[HardwareProfile] = None


def get_active_profile() -> HardwareProfile:
    """Obtiene el perfil activo (singleton).

    Returns:
        HardwareProfile activo
    """
    global _active_profile
    if _active_profile is None:
        _active_profile = get_hardware_profile()
    return _active_profile


def set_active_profile(profile_name: str) -> HardwareProfile:
    """Establece el perfil activo.

    Args:
        profile_name: Nombre del perfil

    Returns:
        HardwareProfile configurado
    """
    global _active_profile
    _active_profile = get_hardware_profile(profile_name)
    return _active_profile


def get_profile_info() -> dict:
    """Obtiene información del perfil activo.

    Returns:
        Dict con información del perfil
    """
    profile = get_active_profile()
    cuda_available = _detect_cuda_available()

    return {
        "profile_name": profile.name,
        "description": profile.description,
        "cuda_available": cuda_available,
        "cuda_enabled": profile.use_gpu and cuda_available,
        "llm_model": profile.llm_model,
        "llm_num_ctx": profile.llm_num_ctx,
        "embedding_device": profile.embedding_device if cuda_available else "cpu",
        "rerank_device": profile.rerank_device if cuda_available else "cpu",
        "ner_device": profile.ner_device if cuda_available else "cpu",
        "batch_size": profile.batch_size,
        "max_concurrent_requests": profile.max_concurrent_requests,
        "available_profiles": list(HARDWARE_PROFILES.keys()),
    }
