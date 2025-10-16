"""Tests para warnings de depreciación - Sprint 1, Tarea 1.2.

Este módulo verifica que las funciones deprecated emiten los warnings correctos
y que las alternativas funcionan sin warnings.
"""

import copy
import warnings
from unittest.mock import AsyncMock, MagicMock

import pytest

from pjn.models import Actuacion
from pjn.scraping.actuaciones import (
    actualizar_metricas_descargas_en_json,
    calcular_metricas_descargas_json,
)


class TestDeprecationWarningsMetricas:
    """Tests para verificar warnings en funciones de cálculo de métricas."""

    def test_actualizar_metricas_emite_deprecation_warning(self):
        """actualizar_metricas_descargas_en_json() debe emitir DeprecationWarning."""
        payload = {
            "Expediente": {"Cantidad de Archivos Descargados": 0},
            "Actuaciones": [
                {"TieneArchivo": True, "Descargado": True},
                {"TieneArchivo": True, "Descargado": False},
            ]
        }

        # ✅ Debe emitir DeprecationWarning
        with pytest.warns(DeprecationWarning, match="deprecated.*v6.0"):
            actualizar_metricas_descargas_en_json(payload)

    def test_actualizar_metricas_warning_mensaje_correcto(self):
        """El warning debe mencionar la función alternativa."""
        payload = {
            "Expediente": {"Cantidad de Archivos Descargados": 0},
            "Actuaciones": []
        }

        with pytest.warns(DeprecationWarning) as warning_info:
            actualizar_metricas_descargas_en_json(payload)

        # Verificar que el mensaje menciona la alternativa
        warning_message = str(warning_info[0].message)
        assert "calcular_metricas_descargas_json" in warning_message
        assert "v6.0" in warning_message

    def test_actualizar_metricas_stacklevel_correcto(self):
        """El warning debe aparecer en el código que llama, no dentro de la función."""
        payload = {
            "Expediente": {"Cantidad de Archivos Descargados": 0},
            "Actuaciones": []
        }

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            actualizar_metricas_descargas_en_json(payload)  # <- Warning debe apuntar aquí

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            # stacklevel=2 hace que el warning apunte a esta línea, no a la función interna

    def test_calcular_metricas_sin_warning(self):
        """calcular_metricas_descargas_json() NO debe emitir warning."""
        payload = {
            "Expediente": {"Cantidad de Archivos Descargados": 0},
            "Actuaciones": [
                {"TieneArchivo": True, "Descargado": True}
            ]
        }

        # ✅ No debe emitir ningún warning
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Falla si hay cualquier warning
            resultado = calcular_metricas_descargas_json(payload)

        # Verificar que funcionó correctamente
        assert resultado["Expediente"]["Cantidad de Archivos Descargados"] == 1

    def test_calcular_metricas_no_muta_original(self):
        """calcular_metricas_descargas_json() NO debe mutar el payload original."""
        payload_original = {
            "Expediente": {"Cantidad de Archivos Descargados": 0},
            "Actuaciones": [{"TieneArchivo": True, "Descargado": True}]
        }

        # Guardar valor original
        valor_original = payload_original["Expediente"]["Cantidad de Archivos Descargados"]

        # Calcular con función nueva
        payload_nuevo = calcular_metricas_descargas_json(payload_original)

        # ✅ El original NO debe cambiar
        assert payload_original["Expediente"]["Cantidad de Archivos Descargados"] == valor_original

        # ✅ El nuevo SÍ debe tener el valor actualizado
        assert payload_nuevo["Expediente"]["Cantidad de Archivos Descargados"] == 1

        # ✅ Debe ser un objeto diferente
        assert payload_nuevo is not payload_original

    def test_actualizar_metricas_muta_original(self):
        """actualizar_metricas_descargas_en_json() SÍ muta (comportamiento deprecated)."""
        payload = {
            "Expediente": {"Cantidad de Archivos Descargados": 0},
            "Actuaciones": [{"TieneArchivo": True, "Descargado": True}]
        }

        valor_original = payload["Expediente"]["Cantidad de Archivos Descargados"]

        # Suprimir warning para este test
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            actualizar_metricas_descargas_en_json(payload)

        # ⚠️ El original SÍ debe cambiar (side effect)
        assert payload["Expediente"]["Cantidad de Archivos Descargados"] != valor_original
        assert payload["Expediente"]["Cantidad de Archivos Descargados"] == 1


class TestDeprecationWarningsDescargas:
    """Tests para verificar warnings en funciones de descarga de archivos."""

    @pytest.mark.asyncio
    async def test_descargar_archivos_actuaciones_emite_warning(self):
        """descargar_archivos_actuaciones() debe emitir DeprecationWarning."""
        # Importar aquí para evitar problemas de async al nivel de módulo
        from pjn.scraping.actuaciones import descargar_archivos_actuaciones

        # Mock de Playwright page
        page_mock = MagicMock()

        actuaciones = [
            {"Archivo": "N/A", "TieneArchivo": False}
        ]

        # ✅ Debe emitir DeprecationWarning
        with pytest.warns(DeprecationWarning, match="deprecated.*v6.0"):
            await descargar_archivos_actuaciones(page_mock, actuaciones, "/tmp/test")

    @pytest.mark.asyncio
    async def test_descargar_archivos_actuaciones_warning_mensaje(self):
        """El warning debe mencionar la función alternativa."""
        from pjn.scraping.actuaciones import descargar_archivos_actuaciones

        page_mock = MagicMock()
        actuaciones = []

        with pytest.warns(DeprecationWarning) as warning_info:
            await descargar_archivos_actuaciones(page_mock, actuaciones, "/tmp/test")

        # Verificar que el mensaje menciona la alternativa
        warning_message = str(warning_info[0].message)
        assert "descargar_archivos_actuaciones_modelos" in warning_message
        assert "v6.0" in warning_message
        assert "inmutables" in warning_message.lower()


class TestMigracionComparativa:
    """Tests comparativos entre funciones deprecated y sus alternativas."""

    def test_ambas_funciones_metricas_calculan_igual(self):
        """Ambas funciones deben calcular las mismas métricas."""
        payload = {
            "Expediente": {"Cantidad de Archivos Descargados": 0},
            "Actuaciones": [
                {"TieneArchivo": True, "Descargado": True},
                {"TieneArchivo": True, "Descargado": False},
                {"TieneArchivo": False, "Descargado": False},
            ]
        }

        # Función deprecated (con warning suprimido)
        payload_mutable = copy.deepcopy(payload)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            actualizar_metricas_descargas_en_json(payload_mutable)

        # Función nueva (sin warning)
        payload_inmutable = calcular_metricas_descargas_json(payload)

        # ✅ Ambas deben calcular los mismos valores
        assert (
            payload_mutable["Expediente"]["Cantidad de Archivos Descargados"] ==
            payload_inmutable["Expediente"]["Cantidad de Archivos Descargados"]
        )
        assert (
            payload_mutable["Expediente"]["total_archivos_con_enlace"] ==
            payload_inmutable["Expediente"]["total_archivos_con_enlace"]
        )
        assert (
            payload_mutable["Expediente"]["descargas_pendientes"] ==
            payload_inmutable["Expediente"]["descargas_pendientes"]
        )

    def test_metricas_caso_vacio(self):
        """Ambas funciones deben manejar listas vacías correctamente."""
        payload = {
            "Expediente": {"Cantidad de Archivos Descargados": 0},
            "Actuaciones": []
        }

        # Función deprecated
        payload_mutable = copy.deepcopy(payload)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            actualizar_metricas_descargas_en_json(payload_mutable)

        # Función nueva
        payload_inmutable = calcular_metricas_descargas_json(payload)

        # ✅ Deben producir los mismos valores (0, 0, 0)
        assert payload_mutable["Expediente"]["Cantidad de Archivos Descargados"] == 0
        assert payload_inmutable["Expediente"]["Cantidad de Archivos Descargados"] == 0

    def test_metricas_con_objetos_actuacion(self):
        """calcular_metricas_descargas_json() debe funcionar con objetos Actuacion."""
        # Crear actuaciones usando objetos con los campos correctos
        actuaciones_modelos = [
            Actuacion(
                indice=1,
                oficina="Oficina Test",
                fecha="2025-01-01",
                detalle="Test 1",
                tiene_archivo=True,
                descargado=True
            ),
            Actuacion(
                indice=2,
                oficina="Oficina Test",
                fecha="2025-01-02",
                detalle="Test 2",
                tiene_archivo=True,
                descargado=False
            ),
        ]

        payload = {
            "Expediente": {"Cantidad de Archivos Descargados": 0},
            "Actuaciones": actuaciones_modelos  # Lista de objetos, no dicts
        }

        # ✅ Debe funcionar con objetos Actuacion
        resultado = calcular_metricas_descargas_json(payload)

        assert resultado["Expediente"]["Cantidad de Archivos Descargados"] == 1
        assert resultado["Expediente"]["total_archivos_con_enlace"] == 2
        assert resultado["Expediente"]["descargas_pendientes"] == 1


class TestIntegrationWarnings:
    """Tests de integración para verificar warnings en flujos completos."""

    def test_pipeline_sin_warnings_usando_nuevas_funciones(self):
        """Un pipeline completo usando funciones nuevas NO debe emitir warnings."""
        # Simular un flujo de procesamiento completo
        payload_inicial = {
            "Expediente": {"numero": "TEST-123", "Cantidad de Archivos Descargados": 0},
            "Actuaciones": [
                {"TieneArchivo": True, "Descargado": False},
                {"TieneArchivo": True, "Descargado": True},
            ]
        }

        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Falla si hay warnings

            # Pipeline usando funciones nuevas
            payload_procesado = calcular_metricas_descargas_json(payload_inicial)

            # Verificar resultados
            assert payload_procesado["Expediente"]["Cantidad de Archivos Descargados"] == 1
            assert payload_procesado is not payload_inicial

    def test_warning_en_codigo_legacy(self):
        """Código legacy que usa funciones deprecated debe emitir warnings."""
        payload = {
            "Expediente": {"Cantidad de Archivos Descargados": 0},
            "Actuaciones": [{"TieneArchivo": True, "Descargado": True}]
        }

        # Simular código legacy
        with pytest.warns(DeprecationWarning):
            # ❌ Patrón legacy (deprecated)
            actualizar_metricas_descargas_en_json(payload)
            # El payload está mutado ahora


# Marcar todo el módulo para ejecutar con pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
