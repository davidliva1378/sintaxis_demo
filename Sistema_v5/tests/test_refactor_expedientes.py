"""Tests para la refactorización de extraer_expedientes_completos() - Sprint 2, Tarea 2.2.

Este módulo verifica que las funciones refactorizadas funcionan correctamente:
- _procesar_filas_pagina()
"""

import pytest
from datetime import datetime
from unittest.mock import MagicMock

from pjn.scraping.expedientes import _procesar_filas_pagina
from pjn.models.expediente import ExpedienteResumen


class TestProcesarFilasPagina:
    """Tests para _procesar_filas_pagina()."""

    def test_procesar_filas_validas(self):
        """Debe procesar correctamente filas válidas."""
        # Filas de ejemplo
        filas = [
            ["EXP-001", "Dependencia 1", "Caratula 1", "Activo", "01/01/2025"],
            ["EXP-002", "Dependencia 2", "Caratula 2", "Activo", "02/01/2025"],
        ]

        huellas = set()
        mapper = lambda resumen: resumen.to_dict()

        resultados, descartadas, duplicados, motivo = _procesar_filas_pagina(
            filas,
            fecha_corte_dt=None,
            huellas=huellas,
            omitir_duplicados=True,
            detener_en_duplicado=False,
            resumen_mapper=mapper,
        )

        assert len(resultados) == 2
        assert descartadas == 0
        assert duplicados == 0
        assert motivo is None

    def test_procesar_filas_con_invalidas(self):
        """Debe descartar filas inválidas y continuar."""
        filas = [
            ["EXP-001", "Dep 1", "Car 1", "Activo", "01/01/2025"],
            [],  # Fila inválida (vacía)
            ["EXP-002", "Dep 2", "Car 2", "Activo", "02/01/2025"],
        ]

        huellas = set()
        mapper = lambda resumen: resumen.to_dict()

        resultados, descartadas, duplicados, motivo = _procesar_filas_pagina(
            filas,
            fecha_corte_dt=None,
            huellas=huellas,
            omitir_duplicados=True,
            detener_en_duplicado=False,
            resumen_mapper=mapper,
        )

        assert len(resultados) == 2
        assert descartadas == 1  # Una fila descartada
        assert duplicados == 0
        assert motivo is None

    def test_detectar_duplicados_sin_detener(self):
        """Debe omitir duplicados cuando omitir_duplicados=True."""
        filas = [
            ["EXP-001", "Dep 1", "Car 1", "Activo", "01/01/2025"],
            ["EXP-001", "Dep 1", "Car 1", "Activo", "01/01/2025"],  # Duplicado
        ]

        huellas = set()
        mapper = lambda resumen: resumen.to_dict()

        resultados, descartadas, duplicados, motivo = _procesar_filas_pagina(
            filas,
            fecha_corte_dt=None,
            huellas=huellas,
            omitir_duplicados=True,
            detener_en_duplicado=False,  # No detener
            resumen_mapper=mapper,
        )

        assert len(resultados) == 1  # Solo el primero
        assert descartadas == 0
        assert duplicados == 1  # Un duplicado encontrado
        assert motivo is None  # No se detiene

    def test_detener_en_duplicado(self):
        """Debe detenerse al encontrar duplicado si detener_en_duplicado=True."""
        filas = [
            ["EXP-001", "Dep 1", "Car 1", "Activo", "01/01/2025"],
            ["EXP-001", "Dep 1", "Car 1", "Activo", "01/01/2025"],  # Duplicado
            ["EXP-002", "Dep 2", "Car 2", "Activo", "02/01/2025"],  # No se procesa
        ]

        huellas = set()
        mapper = lambda resumen: resumen.to_dict()

        resultados, descartadas, duplicados, motivo = _procesar_filas_pagina(
            filas,
            fecha_corte_dt=None,
            huellas=huellas,
            omitir_duplicados=True,
            detener_en_duplicado=True,  # Detener
            resumen_mapper=mapper,
        )

        assert len(resultados) == 1  # Solo el primero
        assert descartadas == 0
        assert duplicados == 0  # No se cuenta porque se detuvo
        assert motivo == "duplicado_encontrado"

    def test_detener_por_fecha_corte(self):
        """Debe detenerse al alcanzar fecha de corte."""
        from datetime import datetime

        filas = [
            ["EXP-001", "Dep 1", "Car 1", "Activo", "15/01/2025"],  # Después
            ["EXP-002", "Dep 2", "Car 2", "Activo", "05/01/2025"],  # Antes de corte
        ]

        fecha_corte = datetime(2025, 1, 10)  # Corte: 10/01/2025
        huellas = set()
        mapper = lambda resumen: resumen.to_dict()

        resultados, descartadas, duplicados, motivo = _procesar_filas_pagina(
            filas,
            fecha_corte_dt=fecha_corte,
            huellas=huellas,
            omitir_duplicados=True,
            detener_en_duplicado=False,
            resumen_mapper=mapper,
        )

        assert len(resultados) == 1  # Solo EXP-001 (15/01)
        assert descartadas == 0
        assert duplicados == 0
        assert motivo == "limite_fecha"

    def test_mapper_personalizado(self):
        """Debe aplicar mapper personalizado correctamente."""
        filas = [
            ["EXP-001", "Dep 1", "Car 1", "Activo", "01/01/2025"],
        ]

        huellas = set()
        # Mapper personalizado que solo retorna el número
        mapper = lambda resumen: {"numero": resumen.numero}

        resultados, _, _, motivo = _procesar_filas_pagina(
            filas,
            fecha_corte_dt=None,
            huellas=huellas,
            omitir_duplicados=True,
            detener_en_duplicado=False,
            resumen_mapper=mapper,
        )

        assert len(resultados) == 1
        assert resultados[0] == {"numero": "EXP-001"}
        assert motivo is None

    def test_procesar_lista_vacia(self):
        """Debe manejar correctamente lista vacía."""
        filas = []

        huellas = set()
        mapper = lambda resumen: resumen.to_dict()

        resultados, descartadas, duplicados, motivo = _procesar_filas_pagina(
            filas,
            fecha_corte_dt=None,
            huellas=huellas,
            omitir_duplicados=True,
            detener_en_duplicado=False,
            resumen_mapper=mapper,
        )

        assert len(resultados) == 0
        assert descartadas == 0
        assert duplicados == 0
        assert motivo is None

    def test_mantener_duplicados_si_configurado(self):
        """Debe mantener duplicados si omitir_duplicados=False."""
        filas = [
            ["EXP-001", "Dep 1", "Car 1", "Activo", "01/01/2025"],
            ["EXP-001", "Dep 1", "Car 1", "Activo", "01/01/2025"],  # Duplicado
        ]

        huellas = set()
        mapper = lambda resumen: resumen.to_dict()

        resultados, descartadas, duplicados, motivo = _procesar_filas_pagina(
            filas,
            fecha_corte_dt=None,
            huellas=huellas,
            omitir_duplicados=False,  # No omitir duplicados
            detener_en_duplicado=False,
            resumen_mapper=mapper,
        )

        assert len(resultados) == 2  # Ambos se incluyen
        assert descartadas == 0
        assert duplicados == 1  # Se cuenta como duplicado pero se incluye
        assert motivo is None


# Marcar todo el módulo para ejecutar con pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
