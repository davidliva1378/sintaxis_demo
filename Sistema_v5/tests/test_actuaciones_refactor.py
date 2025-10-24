"""Tests para refactorización de módulo actuaciones.

Sprint 1, Tarea 1.1: Consolidar _calcular_metricas_descargas()
"""

import pytest
import sys
from pathlib import Path

# Agregar el directorio padre al path para importar pjn
sys.path.insert(0, str(Path(__file__).parent.parent))

from pjn.models import Actuacion
from pjn.parsers.actuaciones_parser import _calcular_metricas_descargas


class TestCalculoMetricas:
    """Tests para cálculo de métricas de descarga."""

    def test_metricas_lista_vacia(self):
        """Con lista vacía debe retornar ceros."""
        total, descargados, pendientes = _calcular_metricas_descargas([])
        assert (total, descargados, pendientes) == (0, 0, 0)

    def test_metricas_sin_archivos(self):
        """Actuaciones sin archivos no deben contarse."""
        actuaciones = [
            Actuacion(
                indice=1,
                oficina="Oficina 1",
                fecha="2025-01-01",
                tipo="RESOLUCION",
                detalle="Detalle de prueba",
                foja="1",
                tiene_archivo=False,
                descargado=False,
                hash="hash123",
                extraida_en="2025-01-01 10:00:00"
            )
        ]
        total, descargados, pendientes = _calcular_metricas_descargas(actuaciones)
        assert (total, descargados, pendientes) == (0, 0, 0)

    def test_metricas_archivos_mixtos(self):
        """Debe contar correctamente mezcla de estados."""
        actuaciones = [
            Actuacion(
                indice=1,
                oficina="Oficina 1",
                fecha="2025-01-01",
                tipo="RESOLUCION",
                detalle="Doc 1",
                foja="1",
                tiene_archivo=True,
                descargado=True,
                archivo="http://example.com/1.pdf",
                nombre_archivo="doc1.pdf",
                hash="hash1",
                extraida_en="2025-01-01 10:00:00"
            ),
            Actuacion(
                indice=2,
                oficina="Oficina 2",
                fecha="2025-01-02",
                tipo="RESOLUCION",
                detalle="Doc 2",
                foja="2",
                tiene_archivo=True,
                descargado=False,
                archivo="http://example.com/2.pdf",
                nombre_archivo="doc2.pdf",
                hash="hash2",
                extraida_en="2025-01-01 10:00:00"
            ),
            Actuacion(
                indice=3,
                oficina="Oficina 3",
                fecha="2025-01-03",
                tipo="RESOLUCION",
                detalle="Doc 3",
                foja="3",
                tiene_archivo=False,
                descargado=False,
                hash="hash3",
                extraida_en="2025-01-01 10:00:00"
            ),
            Actuacion(
                indice=4,
                oficina="Oficina 4",
                fecha="2025-01-04",
                tipo="RESOLUCION",
                detalle="Doc 4",
                foja="4",
                tiene_archivo=True,
                descargado=True,
                archivo="http://example.com/4.pdf",
                nombre_archivo="doc4.pdf",
                hash="hash4",
                extraida_en="2025-01-01 10:00:00"
            ),
        ]
        total, descargados, pendientes = _calcular_metricas_descargas(actuaciones)
        assert (total, descargados, pendientes) == (3, 2, 1)

    def test_metricas_todos_descargados(self):
        """Cuando todos están descargados, no debe haber pendientes."""
        actuaciones = [
            Actuacion(
                indice=i,
                oficina=f"Oficina {i}",
                fecha="2025-01-01",
                tipo="RESOLUCION",
                detalle=f"Doc {i}",
                foja=str(i),
                tiene_archivo=True,
                descargado=True,
                archivo=f"http://example.com/{i}.pdf",
                nombre_archivo=f"doc{i}.pdf",
                hash=f"hash{i}",
                extraida_en="2025-01-01 10:00:00"
            )
            for i in range(1, 6)
        ]
        total, descargados, pendientes = _calcular_metricas_descargas(actuaciones)
        assert (total, descargados, pendientes) == (5, 5, 0)

    def test_metricas_ninguno_descargado(self):
        """Cuando ninguno está descargado, todos son pendientes."""
        actuaciones = [
            Actuacion(
                indice=i,
                oficina=f"Oficina {i}",
                fecha="2025-01-01",
                tipo="RESOLUCION",
                detalle=f"Doc {i}",
                foja=str(i),
                tiene_archivo=True,
                descargado=False,
                archivo=f"http://example.com/{i}.pdf",
                nombre_archivo=f"doc{i}.pdf",
                hash=f"hash{i}",
                extraida_en="2025-01-01 10:00:00"
            )
            for i in range(1, 6)
        ]
        total, descargados, pendientes = _calcular_metricas_descargas(actuaciones)
        assert (total, descargados, pendientes) == (5, 0, 5)

    def test_metricas_con_dicts(self):
        """Debe funcionar con dicts además de objetos Actuacion."""
        actuaciones = [
            {
                "Indice": 1,
                "TieneArchivo": True,
                "Descargado": True
            },
            {
                "Indice": 2,
                "TieneArchivo": True,
                "Descargado": False
            },
            {
                "Indice": 3,
                "TieneArchivo": False,
                "Descargado": False
            }
        ]
        # Convertir a objetos Actuacion usando from_dict
        actuaciones_obj = [Actuacion.from_dict(act) for act in actuaciones]
        total, descargados, pendientes = _calcular_metricas_descargas(actuaciones_obj)
        assert (total, descargados, pendientes) == (2, 1, 1)

    def test_metricas_actuacion_sin_campo_descargado(self):
        """Debe manejar actuaciones donde descargado es None."""
        actuaciones = [
            Actuacion(
                indice=1,
                oficina="Oficina 1",
                fecha="2025-01-01",
                tipo="RESOLUCION",
                detalle="Doc 1",
                foja="1",
                tiene_archivo=True,
                descargado=None,  # None significa "no aplica" o "no descargado"
                archivo="http://example.com/1.pdf",
                hash="hash1",
                extraida_en="2025-01-01 10:00:00"
            )
        ]
        total, descargados, pendientes = _calcular_metricas_descargas(actuaciones)
        # descargado=None se trata como False
        assert (total, descargados, pendientes) == (1, 0, 1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
