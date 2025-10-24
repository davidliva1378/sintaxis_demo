import json
import os
import sys
from tempfile import TemporaryDirectory
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from notificaciones_v2.notificaciones_control_v4_async import (
    notificaciones_proximas_a_vencer,
)


def test_notificaciones_proximas_a_vencer():
    with TemporaryDirectory() as tmpdir:
        historial = [
            {
                "numero": "123/2024",
                "caratula": "Test 1",
                "fecha": (datetime.now() + timedelta(hours=24)).strftime("%Y-%m-%d"),
                "leida": False,
            },
            {
                "numero": "456/2024",
                "caratula": "Test 2",
                "fecha": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
                "leida": False,
            },
        ]

        path = os.path.join(tmpdir, "historial_notificaciones.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(historial, f)

        resultado = notificaciones_proximas_a_vencer(destino=tmpdir, horas=48)
        assert len(resultado) == 1
        assert resultado[0]["numero"] == "123/2024"

