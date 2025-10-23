"""Tests para el módulo de procesamiento batch de expedientes."""

from __future__ import annotations

import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from Sistema_v5.pjn.models.expediente import ExpedienteResumen
from Sistema_v5.extractor_inicial.batch_processor import (
    ExtractorCompletoBatch,
    ResultadoExpediente,
    ResumenBatch,
    AccionUsuarioError,
)


@pytest.fixture
def expedientes_muestra() -> list[ExpedienteResumen]:
    """Genera expedientes de prueba."""
    return [
        ExpedienteResumen(
            numero="123/2024",
            dependencia="JUZ. CIV. Y COM. FED. 1",
            caratula="TEST S/ PRUEBA",
            situacion="En trámite",
            ultima_actuacion="15/01/2025",
        ),
        ExpedienteResumen(
            numero="456/2024",
            dependencia="JUZ. CIV. Y COM. FED. 2",
            caratula="OTRO S/ DEMANDA",
            situacion="Archivado",
            ultima_actuacion="10/01/2025",
        ),
        ExpedienteResumen(
            numero="789/2024",
            dependencia="JUZ. CONTENCIOSO ADMINISTRATIVO 1",
            caratula="AMPARO S/ ACCION",
            situacion="En trámite",
            ultima_actuacion="20/01/2025",
        ),
    ]


class TestResultadoExpediente:
    """Tests para ResultadoExpediente dataclass."""

    def test_creacion_resultado_exitoso(self):
        """Verifica creación de resultado exitoso."""
        exp = ExpedienteResumen(
            numero="123/2024",
            dependencia="Test",
            caratula="Test",
        )

        resultado = ResultadoExpediente(
            expediente=exp,
            estado="success",
            mensaje="✓ Procesado correctamente",
            json_path=Path("/tmp/test.json"),
        )

        assert resultado.expediente == exp
        assert resultado.estado == "success"
        assert resultado.mensaje == "✓ Procesado correctamente"
        assert resultado.json_path == Path("/tmp/test.json")
        assert resultado.error is None
        assert isinstance(resultado.timestamp, str)

    def test_creacion_resultado_error(self):
        """Verifica creación de resultado con error."""
        exp = ExpedienteResumen(
            numero="456/2024",
            dependencia="Test",
            caratula="Test",
        )

        resultado = ResultadoExpediente(
            expediente=exp,
            estado="error",
            mensaje="❌ Error de navegación",
            error="Timeout after 30s",
        )

        assert resultado.estado == "error"
        assert resultado.error == "Timeout after 30s"
        assert resultado.json_path is None


class TestResumenBatch:
    """Tests para ResumenBatch dataclass."""

    def test_validacion_totales_correctos(self):
        """Verifica que acepta totales consistentes."""
        resumen = ResumenBatch(
            total=10,
            exitosos=7,
            errores=2,
            omitidos=1,
            resultados=[],
            tiempo_inicio="2025-01-23T10:00:00",
            tiempo_fin="2025-01-23T10:30:00",
            duracion_segundos=1800.0,
        )

        assert resumen.total == 10
        assert resumen.exitosos == 7
        assert resumen.errores == 2
        assert resumen.omitidos == 1

    def test_validacion_totales_incorrectos(self):
        """Verifica que rechaza totales inconsistentes."""
        with pytest.raises(ValueError, match="Inconsistencia"):
            ResumenBatch(
                total=10,
                exitosos=7,
                errores=5,  # 7+5+0 = 12 ≠ 10
                omitidos=0,
                resultados=[],
                tiempo_inicio="2025-01-23T10:00:00",
                tiempo_fin="2025-01-23T10:30:00",
                duracion_segundos=1800.0,
            )


class TestExtractorCompletoBatch:
    """Tests para ExtractorCompletoBatch."""

    def test_inicializacion_parametros_default(self):
        """Verifica inicialización con parámetros por defecto."""
        batch = ExtractorCompletoBatch()

        assert batch.umbral_errores_consecutivos == 5
        assert batch.headless is True
        assert batch.descargar_adjuntos is False
        assert batch._errores_consecutivos == 0
        assert batch._resultados == []

    def test_inicializacion_parametros_custom(self):
        """Verifica inicialización con parámetros personalizados."""
        batch = ExtractorCompletoBatch(
            umbral_errores_consecutivos=10,
            headless=False,
            descargar_adjuntos=True,
        )

        assert batch.umbral_errores_consecutivos == 10
        assert batch.headless is False
        assert batch.descargar_adjuntos is True

    def test_set_callback_progreso(self):
        """Verifica configuración de callback de progreso."""
        batch = ExtractorCompletoBatch()
        llamadas = []

        def callback(indice, total, exp):
            llamadas.append((indice, total, exp.numero))

        batch.set_callback_progreso(callback)
        assert batch._callback_progreso is callback

    def test_set_callback_error_umbral(self):
        """Verifica configuración de callback de umbral."""
        batch = ExtractorCompletoBatch()
        llamadas = []

        def callback(num_errores, mensajes):
            llamadas.append((num_errores, len(mensajes)))
            return "continuar"

        batch.set_callback_error_umbral(callback)
        assert batch._callback_error_umbral is callback

    @pytest.mark.asyncio
    async def test_procesar_lote_todos_exitosos(self, expedientes_muestra):
        """Verifica procesamiento exitoso de todos los expedientes."""
        batch = ExtractorCompletoBatch(headless=True)

        # Mock del bridge para retornar éxito siempre
        with patch("Sistema_v5.extractor_inicial.batch_processor.GUIPlaywrightBridge") as MockBridge:
            mock_bridge_instance = MagicMock()
            MockBridge.return_value = mock_bridge_instance

            # Configurar get_expediente_payload para retornar dict válido
            mock_bridge_instance.get_expediente_payload.return_value = {
                "numero": "123/2024",
                "datos": "test",
            }

            # Configurar run_coroutine para retornar resultado exitoso
            mock_bridge_instance.run_coroutine.return_value = (
                "/tmp/test.json",
                {
                    "actuaciones_actuales": 5,
                    "actuaciones_historicas": 10,
                    "descargas_ejecutadas": False,
                },
            )

            resumen = await batch.procesar_lote(expedientes_muestra)

            assert resumen.total == 3
            assert resumen.exitosos == 3
            assert resumen.errores == 0
            assert resumen.omitidos == 0
            assert len(resumen.resultados) == 3
            assert all(r.estado == "success" for r in resumen.resultados)

    @pytest.mark.asyncio
    async def test_procesar_lote_con_errores_bajo_umbral(self, expedientes_muestra):
        """Verifica que errores bajo el umbral continúan automáticamente."""
        batch = ExtractorCompletoBatch(umbral_errores_consecutivos=5)

        with patch("Sistema_v5.extractor_inicial.batch_processor.GUIPlaywrightBridge") as MockBridge:
            mock_bridge_instance = MagicMock()
            MockBridge.return_value = mock_bridge_instance

            # Simular 2 errores + 1 éxito (resetea contador)
            call_count = 0

            def side_effect_payload(*args):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    from Sistema_v5.ui.gui_playwright_bridge import ExpedienteNotFoundError
                    raise ExpedienteNotFoundError("Expediente no encontrado")
                return {"numero": "789/2024"}

            mock_bridge_instance.get_expediente_payload.side_effect = side_effect_payload
            mock_bridge_instance.run_coroutine.return_value = ("/tmp/test.json", {})

            resumen = await batch.procesar_lote(expedientes_muestra)

            # No debe disparar callback de umbral porque 2 < 5
            assert resumen.errores == 2
            assert resumen.exitosos == 1
            assert batch._errores_consecutivos == 0  # Se resetea tras el éxito

    @pytest.mark.asyncio
    async def test_procesar_lote_alcanza_umbral_continuar(self, expedientes_muestra):
        """Verifica comportamiento al alcanzar umbral con acción 'continuar'."""
        batch = ExtractorCompletoBatch(umbral_errores_consecutivos=2)

        # Callback que retorna "continuar"
        callback_llamado = []

        def callback_umbral(num_errores, mensajes):
            callback_llamado.append(num_errores)
            return "continuar"

        batch.set_callback_error_umbral(callback_umbral)

        with patch("Sistema_v5.extractor_inicial.batch_processor.GUIPlaywrightBridge") as MockBridge:
            mock_bridge_instance = MagicMock()
            MockBridge.return_value = mock_bridge_instance

            # Simular: 2 errores (dispara umbral) → continuar → 1 éxito
            call_count = 0

            def side_effect_payload(*args):
                nonlocal call_count
                call_count += 1
                if call_count <= 2:
                    from Sistema_v5.ui.gui_playwright_bridge import ExpedienteNavigationError
                    raise ExpedienteNavigationError("Error navegación")
                return {"numero": "789/2024"}

            mock_bridge_instance.get_expediente_payload.side_effect = side_effect_payload
            mock_bridge_instance.run_coroutine.return_value = ("/tmp/test.json", {})

            resumen = await batch.procesar_lote(expedientes_muestra)

            # Verificar que se llamó al callback
            assert len(callback_llamado) == 1
            assert callback_llamado[0] == 2

            # Debe continuar y procesar el tercer expediente
            assert resumen.errores == 2
            assert resumen.exitosos == 1
            assert batch._errores_consecutivos == 0  # Reseteo tras continuar + éxito

    @pytest.mark.asyncio
    async def test_procesar_lote_alcanza_umbral_saltar(self, expedientes_muestra):
        """Verifica comportamiento al alcanzar umbral con acción 'saltar'."""
        batch = ExtractorCompletoBatch(umbral_errores_consecutivos=2)

        def callback_umbral(num_errores, mensajes):
            return "saltar"

        batch.set_callback_error_umbral(callback_umbral)

        with patch("Sistema_v5.extractor_inicial.batch_processor.GUIPlaywrightBridge") as MockBridge:
            mock_bridge_instance = MagicMock()
            MockBridge.return_value = mock_bridge_instance

            # Todos fallan
            from Sistema_v5.ui.gui_playwright_bridge import ExpedienteNotFoundError
            mock_bridge_instance.get_expediente_payload.side_effect = ExpedienteNotFoundError("Test")

            resumen = await batch.procesar_lote(expedientes_muestra)

            # 2 errores + 1 saltado
            assert resumen.errores == 2
            assert resumen.omitidos == 1
            assert resumen.exitosos == 0

            # El expediente saltado debe tener estado "skipped"
            resultados_saltados = [r for r in resumen.resultados if r.estado == "skipped"]
            assert len(resultados_saltados) == 1
            assert "Omitido por usuario" in resultados_saltados[0].mensaje

    @pytest.mark.asyncio
    async def test_procesar_lote_alcanza_umbral_cancelar(self, expedientes_muestra):
        """Verifica que 'cancelar' lanza AccionUsuarioError."""
        batch = ExtractorCompletoBatch(umbral_errores_consecutivos=2)

        def callback_umbral(num_errores, mensajes):
            return "cancelar"

        batch.set_callback_error_umbral(callback_umbral)

        with patch("Sistema_v5.extractor_inicial.batch_processor.GUIPlaywrightBridge") as MockBridge:
            mock_bridge_instance = MagicMock()
            MockBridge.return_value = mock_bridge_instance

            from Sistema_v5.ui.gui_playwright_bridge import ExpedienteNotFoundError
            mock_bridge_instance.get_expediente_payload.side_effect = ExpedienteNotFoundError("Test")

            with pytest.raises(AccionUsuarioError, match="cancelado por el usuario"):
                await batch.procesar_lote(expedientes_muestra)

    @pytest.mark.asyncio
    async def test_build_mensaje_exito_con_resumen(self):
        """Verifica construcción de mensaje de éxito con resumen."""
        batch = ExtractorCompletoBatch()
        exp = ExpedienteResumen(
            numero="123/2024",
            dependencia="Test",
            caratula="Test",
        )

        resumen_procesamiento = {
            "actuaciones_actuales": 5,
            "actuaciones_historicas": 10,
            "descargas_ejecutadas": True,
        }

        mensaje = batch._build_mensaje_exito(exp, resumen_procesamiento)

        assert "123/2024" in mensaje
        assert "5/10" in mensaje
        assert "Descargas: Sí" in mensaje

    @pytest.mark.asyncio
    async def test_build_mensaje_exito_sin_resumen(self):
        """Verifica construcción de mensaje sin resumen."""
        batch = ExtractorCompletoBatch()
        exp = ExpedienteResumen(
            numero="456/2024",
            dependencia="Test",
            caratula="Test",
        )

        mensaje = batch._build_mensaje_exito(exp, None)

        assert "456/2024" in mensaje
        assert "sin detalles" in mensaje

    def test_consultar_usuario_umbral_sin_callback(self):
        """Verifica fallback cuando no hay callback configurado."""
        batch = ExtractorCompletoBatch()

        accion = batch._consultar_usuario_umbral(5, ["error1", "error2"])

        # Debe retornar "continuar" por defecto
        assert accion == "continuar"

    def test_consultar_usuario_umbral_con_callback(self):
        """Verifica que usa el callback cuando está configurado."""
        batch = ExtractorCompletoBatch()

        def callback(num_errores, mensajes):
            assert num_errores == 5
            assert len(mensajes) == 3
            return "saltar"

        batch.set_callback_error_umbral(callback)

        accion = batch._consultar_usuario_umbral(5, ["e1", "e2", "e3"])
        assert accion == "saltar"

    @pytest.mark.asyncio
    async def test_callback_progreso_se_invoca(self, expedientes_muestra):
        """Verifica que el callback de progreso se llama correctamente."""
        batch = ExtractorCompletoBatch()

        llamadas = []

        def callback_progreso(indice, total, exp):
            llamadas.append((indice, total, exp.numero))

        batch.set_callback_progreso(callback_progreso)

        with patch("Sistema_v5.extractor_inicial.batch_processor.GUIPlaywrightBridge") as MockBridge:
            mock_bridge_instance = MagicMock()
            MockBridge.return_value = mock_bridge_instance
            mock_bridge_instance.get_expediente_payload.return_value = {"numero": "test"}
            mock_bridge_instance.run_coroutine.return_value = ("/tmp/test.json", {})

            await batch.procesar_lote(expedientes_muestra)

            # Debe haberse llamado 3 veces (1 por expediente)
            assert len(llamadas) == 3
            assert llamadas[0] == (1, 3, "123/2024")
            assert llamadas[1] == (2, 3, "456/2024")
            assert llamadas[2] == (3, 3, "789/2024")

    @pytest.mark.asyncio
    async def test_resumen_tiene_timestamps_validos(self, expedientes_muestra):
        """Verifica que el resumen contiene timestamps válidos."""
        batch = ExtractorCompletoBatch()

        with patch("Sistema_v5.extractor_inicial.batch_processor.GUIPlaywrightBridge") as MockBridge:
            mock_bridge_instance = MagicMock()
            MockBridge.return_value = mock_bridge_instance
            mock_bridge_instance.get_expediente_payload.return_value = {"numero": "test"}
            mock_bridge_instance.run_coroutine.return_value = ("/tmp/test.json", {})

            resumen = await batch.procesar_lote(expedientes_muestra)

            # Verificar formato ISO de timestamps
            datetime.fromisoformat(resumen.tiempo_inicio)
            datetime.fromisoformat(resumen.tiempo_fin)

            # La duración debe ser positiva
            assert resumen.duracion_segundos >= 0
