"""Configuración centralizada de Rate Limiting.

Este módulo proporciona un limiter compartido para usar en todos los routers
de la API, evitando problemas de instancias desconectadas.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Limiter centralizado - usar este en todos los routers
limiter = Limiter(key_func=get_remote_address)
