from __future__ import annotations
from typing import Dict, List, Optional, Tuple, Literal
from pathlib import Path
from ._impl_expedientes import extraer_expedientes as _impl_extraer_expedientes

EstadoExtraccion = Literal["completo", "parcial", "error"]

async def extraer_expedientes(
    *args, **kwargs
) -> Tuple[List[Dict], Optional[Path], EstadoExtraccion]:
    """Adaptador: expone la implementación real con un contrato estable."""
    return await _impl_extraer_expedientes(*args, **kwargs)
