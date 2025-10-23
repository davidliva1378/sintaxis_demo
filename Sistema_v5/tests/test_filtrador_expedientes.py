"""Tests para el módulo de filtrado de expedientes."""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta

from Sistema_v5.pjn.models.expediente import ExpedienteResumen
from Sistema_v5.extractor_inicial.filtrador import FiltradorExpedientes


@pytest.fixture
def expedientes_muestra() -> list[ExpedienteResumen]:
    """Genera una muestra de expedientes para testing."""
    hoy = datetime.now().date()
    hace_15_dias = (hoy - timedelta(days=15)).strftime("%d/%m/%Y")
    hace_45_dias = (hoy - timedelta(days=45)).strftime("%d/%m/%Y")

    return [
        ExpedienteResumen(
            numero="123/2024",
            dependencia="JUZ. CIV. Y COM. FED. 1",
            caratula="TEST S/ PRUEBA",
            situacion="En trámite",
            ultima_actuacion=hace_15_dias,
        ),
        ExpedienteResumen(
            numero="456/2024",
            dependencia="JUZ. CIV. Y COM. FED. 2",
            caratula="OTRO S/ DEMANDA",
            situacion="Archivado",
            ultima_actuacion=hace_45_dias,
        ),
        ExpedienteResumen(
            numero="789/2024",
            dependencia="JUZ. CONTENCIOSO ADMINISTRATIVO 1",
            caratula="AMPARO S/ ACCION",
            situacion="En trámite",
            ultima_actuacion=hace_15_dias,
        ),
        ExpedienteResumen(
            numero="101/2024",
            dependencia="JUZ. CIV. Y COM. FED. 1",
            caratula="EMBARGO S/ MEDIDA",
            situacion="Sentenciado",
            ultima_actuacion=None,  # Sin última actuación
        ),
    ]


class TestFiltradorExpedientes:
    """Tests para la clase FiltradorExpedientes."""

    def test_inicializacion(self, expedientes_muestra):
        """Verifica inicialización correcta."""
        filtrador = FiltradorExpedientes(expedientes_muestra)

        assert len(filtrador.expedientes_originales) == 4
        assert len(filtrador.expedientes_filtrados) == 4
        assert len(filtrador.filtros_aplicados) == 0

    def test_filtrar_por_dias_atras(self, expedientes_muestra):
        """Verifica filtrado por actividad reciente."""
        filtrador = FiltradorExpedientes(expedientes_muestra)
        resultado = filtrador.filtrar_por_dias_atras(30).obtener_resultados()

        # Solo 2 expedientes con actividad en últimos 30 días
        assert len(resultado) == 2
        assert all(exp.ultima_actuacion for exp in resultado)
        assert len(filtrador.filtros_aplicados) == 1

    def test_filtrar_por_situacion(self, expedientes_muestra):
        """Verifica filtrado por situación procesal."""
        filtrador = FiltradorExpedientes(expedientes_muestra)
        resultado = filtrador.filtrar_por_situacion(["En trámite"]).obtener_resultados()

        assert len(resultado) == 2
        assert all(exp.situacion == "En trámite" for exp in resultado)

    def test_filtrar_por_dependencia_texto_simple(self, expedientes_muestra):
        """Verifica filtrado por dependencia con texto simple."""
        filtrador = FiltradorExpedientes(expedientes_muestra)
        resultado = filtrador.filtrar_por_dependencia("FED.").obtener_resultados()

        assert len(resultado) == 3  # 3 juzgados federales
        assert all("FED." in exp.dependencia for exp in resultado)

    def test_filtrar_por_dependencia_regex(self, expedientes_muestra):
        """Verifica filtrado por dependencia con regex."""
        filtrador = FiltradorExpedientes(expedientes_muestra)
        resultado = filtrador.filtrar_por_dependencia(
            r"JUZ\. CIV\..*1$",
            regex=True
        ).obtener_resultados()

        # Solo juzgados civiles terminados en "1"
        assert len(resultado) == 2
        assert all(exp.dependencia.endswith("1") for exp in resultado)

    def test_filtros_encadenados(self, expedientes_muestra):
        """Verifica encadenamiento de múltiples filtros."""
        filtrador = FiltradorExpedientes(expedientes_muestra)
        resultado = (filtrador
            .filtrar_por_dias_atras(30)
            .filtrar_por_situacion(["En trámite"])
            .obtener_resultados())

        # 2 expedientes cumplen ambos criterios (123/2024 y 789/2024)
        assert len(resultado) == 2
        assert all(exp.situacion == "En trámite" for exp in resultado)
        assert len(filtrador.filtros_aplicados) == 2

    def test_resetear_filtros(self, expedientes_muestra):
        """Verifica que resetear restaura el listado original."""
        filtrador = FiltradorExpedientes(expedientes_muestra)

        # Aplicar filtros
        filtrador.filtrar_por_situacion(["Archivado"])
        assert len(filtrador.obtener_resultados()) == 1

        # Resetear
        filtrador.resetear()
        assert len(filtrador.obtener_resultados()) == 4
        assert len(filtrador.filtros_aplicados) == 0

    def test_obtener_estadisticas(self, expedientes_muestra):
        """Verifica cálculo de estadísticas."""
        filtrador = FiltradorExpedientes(expedientes_muestra)
        filtrador.filtrar_por_situacion(["En trámite"])

        stats = filtrador.obtener_estadisticas()

        assert stats["total_original"] == 4
        assert stats["total_filtrado"] == 2
        assert stats["filtros_aplicados"] == 1
        assert stats["porcentaje_retenido"] == 50.0

    def test_filtro_personalizado(self, expedientes_muestra):
        """Verifica filtro personalizado con predicado."""
        filtrador = FiltradorExpedientes(expedientes_muestra)
        resultado = filtrador.filtrar_personalizado(
            lambda exp: "AMPARO" in exp.caratula.upper(),
            nombre_filtro="contiene_amparo"
        ).obtener_resultados()

        assert len(resultado) == 1
        assert "AMPARO" in resultado[0].caratula

    def test_error_regex_invalido(self, expedientes_muestra):
        """Verifica que regex inválido lanza ValueError."""
        filtrador = FiltradorExpedientes(expedientes_muestra)

        with pytest.raises(ValueError, match="Patrón regex inválido"):
            filtrador.filtrar_por_dependencia(
                r"[invalid(regex",
                regex=True
            )


class TestExpedienteResumet:
    """Tests para el método esta_activo() de ExpedienteResumen."""

    def test_esta_activo_con_actividad_reciente(self):
        """Verifica que detecta actividad reciente."""
        hoy = datetime.now().date()
        hace_10_dias = (hoy - timedelta(days=10)).strftime("%d/%m/%Y")

        exp = ExpedienteResumen(
            numero="123/2024",
            dependencia="Test",
            caratula="Test",
            ultima_actuacion=hace_10_dias,
        )

        assert exp.esta_activo(15) is True  # Dentro de 15 días
        assert exp.esta_activo(5) is False  # Fuera de 5 días

    def test_esta_activo_sin_ultima_actuacion(self):
        """Verifica que retorna False sin última actuación."""
        exp = ExpedienteResumen(
            numero="123/2024",
            dependencia="Test",
            caratula="Test",
            ultima_actuacion=None,
        )

        assert exp.esta_activo(30) is False

    def test_esta_activo_formato_iso(self):
        """Verifica que soporta formato ISO YYYY-MM-DD."""
        hoy = datetime.now().date()
        hace_10_dias = (hoy - timedelta(days=10)).isoformat()

        exp = ExpedienteResumen(
            numero="123/2024",
            dependencia="Test",
            caratula="Test",
            ultima_actuacion=hace_10_dias,
        )

        assert exp.esta_activo(15) is True
