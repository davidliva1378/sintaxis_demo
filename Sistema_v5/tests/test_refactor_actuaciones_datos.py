"""Tests para la refactorización de extraer_actuaciones_datos() - Sprint 2, Tarea 2.1.

Este módulo verifica que las funciones refactorizadas funcionan correctamente:
- _navegar_paginas_actuaciones()
- _extraer_actuaciones_actuales()
- _extraer_actuaciones_historicas()
- extraer_actuaciones_datos() (versión refactorizada)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from playwright.async_api import TimeoutError as PlaywrightTimeout

from pjn.scraping.actuaciones import (
    _navegar_paginas_actuaciones,
    _extraer_actuaciones_actuales,
    _extraer_actuaciones_historicas,
    extraer_actuaciones_datos,
)
from pjn.exceptions import ActuacionesNoDisponibles, TimeoutExtraccion, ExtraccionError
from pjn.models.actuacion import Actuacion


class TestNavegarPaginasActuaciones:
    """Tests para _navegar_paginas_actuaciones()."""

    @pytest.mark.asyncio
    async def test_extraer_pagina_unica_actuales(self):
        """Debe extraer actuaciones de una sola página (actuales)."""
        page_mock = AsyncMock()
        expediente_datos = {"numero": "TEST-123"}

        # Mock para extraer_actuaciones_pagina_modelos
        with patch('pjn.scraping.actuaciones.extraer_actuaciones_pagina_modelos') as mock_extraer:
            # Primera llamada: retorna 2 actuaciones
            mock_extraer.return_value = [
                Actuacion(indice=1, oficina="Of1", fecha="2025-01-01"),
                Actuacion(indice=2, oficina="Of2", fecha="2025-01-02"),
            ]

            # Mock para query_selector (sin botón siguiente)
            page_mock.query_selector.return_value = None

            resultado = await _navegar_paginas_actuaciones(
                page_mock,
                tabla_id="expediente:action-table",
                expediente_datos=expediente_datos,
                indice_inicial=1,
                es_historica=False
            )

            assert len(resultado) == 2
            assert resultado[0].indice == 1
            assert resultado[1].indice == 2

    @pytest.mark.asyncio
    async def test_extraer_multiples_paginas_actuales(self):
        """Debe navegar y extraer múltiples páginas (actuales)."""
        page_mock = AsyncMock()
        expediente_datos = {"numero": "TEST-123"}

        with patch('pjn.scraping.actuaciones.extraer_actuaciones_pagina_modelos') as mock_extraer:
            with patch('pjn.scraping.actuaciones._obtener_paginador_activo') as mock_paginador:
                with patch('pjn.scraping.actuaciones._esperar_cambio_pagina') as mock_esperar:
                    # Simular 2 páginas con 2 actuaciones cada una
                    mock_extraer.side_effect = [
                        [Actuacion(indice=1, oficina="Of1", fecha="2025-01-01"), Actuacion(indice=2, oficina="Of2", fecha="2025-01-02")],
                        [Actuacion(indice=3, oficina="Of3", fecha="2025-01-03"), Actuacion(indice=4, oficina="Of4", fecha="2025-01-04")],
                        [],  # Tercera página vacía (fin)
                    ]

                    # Simular botón siguiente existe 2 veces, luego None
                    boton_mock = AsyncMock()
                    boton_mock.click = AsyncMock()
                    page_mock.query_selector.side_effect = [
                        boton_mock,  # Primera vez: hay botón
                        boton_mock,  # Segunda vez: hay botón
                        None,  # Tercera vez: no hay botón
                    ]

                    page_mock.inner_html = AsyncMock(return_value="<html>tabla</html>")
                    mock_paginador.return_value = ("selector", "1")

                    resultado = await _navegar_paginas_actuaciones(
                        page_mock,
                        tabla_id="expediente:action-table",
                        expediente_datos=expediente_datos,
                        indice_inicial=1,
                        es_historica=False
                    )

                    assert len(resultado) == 4
                    assert mock_extraer.call_count == 3  # 3 llamadas (2 con datos, 1 vacía)

    @pytest.mark.asyncio
    async def test_extraer_pagina_unica_historicas(self):
        """Debe extraer actuaciones históricas de una sola página."""
        page_mock = AsyncMock()
        expediente_datos = {"numero": "TEST-123"}

        # Mock para query_selector_all (filas)
        fila_mock_1 = MagicMock()
        fila_mock_2 = MagicMock()
        page_mock.query_selector_all.return_value = [fila_mock_1, fila_mock_2]

        # Mock para construir_actuacion_modelo_desde_fila
        with patch('pjn.scraping.actuaciones.construir_actuacion_modelo_desde_fila') as mock_construir:
            mock_construir.side_effect = [
                Actuacion(indice=1, oficina="Of1", fecha="2025-01-01", es_historica=True),
                Actuacion(indice=2, oficina="Of2", fecha="2025-01-02", es_historica=True),
            ]

            # Sin botón siguiente
            page_mock.query_selector.return_value = None

            resultado = await _navegar_paginas_actuaciones(
                page_mock,
                tabla_id="expediente:action-historic-table",
                expediente_datos=expediente_datos,
                indice_inicial=10,
                es_historica=True
            )

            assert len(resultado) == 2
            assert all(act.es_historica for act in resultado)


class TestExtraerActuacionesActuales:
    """Tests para _extraer_actuaciones_actuales()."""

    @pytest.mark.asyncio
    async def test_extrae_actuaciones_actuales_correctamente(self):
        """Debe extraer actuaciones actuales y marcarlas correctamente."""
        page_mock = AsyncMock()
        expediente_datos = {"numero": "TEST-123"}

        # Mock espera de tabla
        page_mock.wait_for_selector = AsyncMock()

        # Mock navegación de páginas
        with patch('pjn.scraping.actuaciones._navegar_paginas_actuaciones') as mock_navegar:
            mock_navegar.return_value = [
                Actuacion(indice=1, oficina="Of1", fecha="2025-01-01", tiene_archivo=True),
                Actuacion(indice=2, oficina="Of2", fecha="2025-01-02", tiene_archivo=False),
            ]

            resultado = await _extraer_actuaciones_actuales(page_mock, expediente_datos)

            assert len(resultado) == 2
            assert all(not act.es_historica for act in resultado)
            assert resultado[0].descargado is False  # tiene_archivo=True -> descargado=False
            assert resultado[1].descargado is False  # tiene_archivo=False también se marca

    @pytest.mark.asyncio
    async def test_lanza_excepcion_si_no_hay_tabla(self):
        """Debe lanzar ActuacionesNoDisponibles si no encuentra la tabla."""
        page_mock = AsyncMock()
        expediente_datos = {"numero": "TEST-123"}

        # Simular timeout al esperar tabla
        page_mock.wait_for_selector.side_effect = PlaywrightTimeout("No table")

        with pytest.raises(ActuacionesNoDisponibles) as exc_info:
            await _extraer_actuaciones_actuales(page_mock, expediente_datos)

        assert "no se encontró la tabla" in str(exc_info.value).lower()


class TestExtraerActuacionesHistoricas:
    """Tests para _extraer_actuaciones_historicas()."""

    @pytest.mark.asyncio
    async def test_extrae_historicas_correctamente(self):
        """Debe extraer actuaciones históricas si existen."""
        page_mock = AsyncMock()
        expediente_datos = {"numero": "TEST-123"}

        # Mock click y espera
        page_mock.click = AsyncMock()
        page_mock.wait_for_selector = AsyncMock()

        # No hay mensaje de alerta (hay tabla)
        page_mock.query_selector.return_value = None

        # Mock navegación de páginas
        with patch('pjn.scraping.actuaciones._navegar_paginas_actuaciones') as mock_navegar:
            mock_navegar.return_value = [
                Actuacion(indice=10, oficina="Of10", fecha="2025-01-01", es_historica=True),
                Actuacion(indice=11, oficina="Of11", fecha="2025-01-02", es_historica=True),
            ]

            resultado = await _extraer_actuaciones_historicas(page_mock, expediente_datos, indice_base=10)

            assert len(resultado) == 2
            assert all(act.es_historica for act in resultado)

    @pytest.mark.asyncio
    async def test_retorna_vacio_si_no_hay_historicas(self):
        """Debe retornar lista vacía si hay mensaje de 'no posee históricas'."""
        page_mock = AsyncMock()
        expediente_datos = {"numero": "TEST-123"}

        page_mock.click = AsyncMock()
        page_mock.wait_for_selector = AsyncMock()

        # Simular mensaje de alerta
        mensaje_mock = AsyncMock()
        mensaje_mock.inner_text.return_value = "El expediente no posee actuaciones históricas"
        page_mock.query_selector.return_value = mensaje_mock

        resultado = await _extraer_actuaciones_historicas(page_mock, expediente_datos, indice_base=10)

        assert len(resultado) == 0

    @pytest.mark.asyncio
    async def test_lanza_excepcion_si_timeout(self):
        """Debe lanzar TimeoutExtraccion si hay timeout."""
        page_mock = AsyncMock()
        expediente_datos = {"numero": "TEST-123"}

        page_mock.click = AsyncMock()
        page_mock.wait_for_selector.side_effect = PlaywrightTimeout("Timeout")

        with pytest.raises(TimeoutExtraccion) as exc_info:
            await _extraer_actuaciones_historicas(page_mock, expediente_datos, indice_base=10)

        assert "timeout" in str(exc_info.value).lower()


class TestExtraerActuacionesDatosRefactorizado:
    """Tests para extraer_actuaciones_datos() refactorizado."""

    @pytest.mark.asyncio
    async def test_extrae_solo_actuales_si_sin_historicas(self):
        """Debe extraer solo actuales si incluir_historicas=False."""
        page_mock = AsyncMock()
        expediente_datos = {"numero": "TEST-123"}

        with patch('pjn.scraping.actuaciones._extraer_actuaciones_actuales') as mock_actuales:
            with patch('pjn.scraping.actuaciones.construir_actuaciones_archivo') as mock_construir:
                mock_actuales.return_value = [
                    Actuacion(indice=1, oficina="Of1", fecha="2025-01-01"),
                    Actuacion(indice=2, oficina="Of2", fecha="2025-01-02"),
                ]

                mock_construir.return_value = MagicMock()

                resultado = await extraer_actuaciones_datos(
                    page_mock,
                    expediente_datos,
                    incluir_historicas=False
                )

                # No debe intentar extraer históricas
                assert mock_actuales.call_count == 1
                assert mock_construir.call_count == 1

                # Verificar que construir_actuaciones_archivo recibió lista vacía para históricas
                call_args = mock_construir.call_args
                assert len(call_args[0][2]) == 0  # actuaciones_historicas vacía

    @pytest.mark.asyncio
    async def test_extrae_actuales_y_historicas(self):
        """Debe extraer ambas si incluir_historicas=True."""
        page_mock = AsyncMock()
        expediente_datos = {"numero": "TEST-123"}

        with patch('pjn.scraping.actuaciones._extraer_actuaciones_actuales') as mock_actuales:
            with patch('pjn.scraping.actuaciones._extraer_actuaciones_historicas') as mock_historicas:
                with patch('pjn.scraping.actuaciones.construir_actuaciones_archivo') as mock_construir:
                    mock_actuales.return_value = [Actuacion(indice=1, oficina="Of1", fecha="2025-01-01")]
                    mock_historicas.return_value = [Actuacion(indice=10, oficina="Of10", fecha="2024-01-01", es_historica=True)]
                    mock_construir.return_value = MagicMock()

                    resultado = await extraer_actuaciones_datos(
                        page_mock,
                        expediente_datos,
                        incluir_historicas=True
                    )

                    assert mock_actuales.call_count == 1
                    assert mock_historicas.call_count == 1
                    assert mock_construir.call_count == 1

                    # Verificar que construir_actuaciones_archivo recibió ambas listas
                    call_args = mock_construir.call_args
                    assert len(call_args[0][1]) == 1  # actuaciones_actuales
                    assert len(call_args[0][2]) == 1  # actuaciones_historicas

    @pytest.mark.asyncio
    async def test_lanza_excepcion_si_no_hay_actuaciones(self):
        """Debe lanzar ActuacionesNoDisponibles si no hay actuaciones."""
        page_mock = AsyncMock()
        expediente_datos = {"numero": "TEST-123"}

        with patch('pjn.scraping.actuaciones._extraer_actuaciones_actuales') as mock_actuales:
            mock_actuales.return_value = []  # Sin actuaciones

            with pytest.raises(ActuacionesNoDisponibles) as exc_info:
                await extraer_actuaciones_datos(page_mock, expediente_datos)

            assert "no se encontraron actuaciones" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_continua_si_falla_extraccion_historicas(self):
        """Debe continuar con solo actuales si falla extracción de históricas."""
        page_mock = AsyncMock()
        expediente_datos = {"numero": "TEST-123"}

        with patch('pjn.scraping.actuaciones._extraer_actuaciones_actuales') as mock_actuales:
            with patch('pjn.scraping.actuaciones._extraer_actuaciones_historicas') as mock_historicas:
                with patch('pjn.scraping.actuaciones.construir_actuaciones_archivo') as mock_construir:
                    mock_actuales.return_value = [Actuacion(indice=1, oficina="Of1", fecha="2025-01-01")]
                    mock_historicas.side_effect = TimeoutExtraccion("Timeout en históricas")
                    mock_construir.return_value = MagicMock()

                    # No debe lanzar excepción, solo continuar sin históricas
                    resultado = await extraer_actuaciones_datos(
                        page_mock,
                        expediente_datos,
                        incluir_historicas=True
                    )

                    assert mock_construir.call_count == 1

                    # Verificar que construir_actuaciones_archivo recibió lista vacía para históricas
                    call_args = mock_construir.call_args
                    assert len(call_args[0][2]) == 0  # actuaciones_historicas vacía


# Marcar todo el módulo para ejecutar con pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
