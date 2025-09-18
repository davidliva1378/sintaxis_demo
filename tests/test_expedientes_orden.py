from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from Sistema_v3.operaciones.expedientes import expedientes_v4 as expedientes_v3
from Sistema_v4.operaciones.expedientes import expedientes_v4


@pytest.mark.parametrize(
    "valor, esperado",
    [
        ("fecha", "FECHA"),
        ("caratula", "CARATULA"),
        ("oficina", "OFICINA"),
        ("situacion", "SITUACION"),
        ("FECHA", "FECHA"),
        ("Situacion", "SITUACION"),
    ],
)
@pytest.mark.parametrize("modulo", [expedientes_v4, expedientes_v3])
def test_resolver_valor_orden_valores_validos(valor, esperado, modulo):
    assert modulo._resolver_valor_orden(valor) == esperado


@pytest.mark.parametrize("modulo", [expedientes_v4, expedientes_v3])
def test_resolver_valor_orden_valores_invalidos(modulo):
    assert modulo._resolver_valor_orden("inexistente") is None
    assert modulo._resolver_valor_orden(None) is None
