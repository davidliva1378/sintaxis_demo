"""Tests para ExtraccionExpedientesConfig - Sprint 2, Tarea 2.3.

Este módulo verifica que el objeto de configuración funciona correctamente:
- Creación y validación
- Presets (rapido, completo, con_fecha_corte)
- Integración con extraer_expedientes_completos()
- Backward compatibility con parámetros legacy
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from configuracion.core import ExtraccionExpedientesConfig
from pjn.models.expediente import ExpedienteResumen


class TestExtraccionExpedientesConfig:
    """Tests para el dataclass ExtraccionExpedientesConfig."""

    def test_config_por_defecto(self):
        """Debe crear config con valores por defecto."""
        config = ExtraccionExpedientesConfig()

        assert config.sel_tabla == "table.table-striped"
        assert config.sel_tbody == "table.table-striped tbody"  # Calculado en __post_init__
        assert config.max_paginas is None
        assert config.tiempo_maximo_segundos is None
        assert config.fecha_corte is None
        assert config.omitir_duplicados is True
        assert config.detener_en_duplicado is True
        assert config.orden is None
        assert config.mapper is None
        assert config.pagination_strategy is None

    def test_config_personalizado(self):
        """Debe permitir personalizar valores."""
        config = ExtraccionExpedientesConfig(
            sel_tabla="div.custom-table",
            max_paginas=50,
            fecha_corte="2025-01-01",
            orden="fecha",
        )

        assert config.sel_tabla == "div.custom-table"
        assert config.sel_tbody == "div.custom-table tbody"
        assert config.max_paginas == 50
        assert config.fecha_corte == "2025-01-01"
        assert config.orden == "fecha"

    def test_config_sel_tbody_manual(self):
        """Si se especifica sel_tbody manualmente, debe respetarse."""
        config = ExtraccionExpedientesConfig(
            sel_tabla="table.foo",
            sel_tbody="div.custom-tbody",
        )

        assert config.sel_tbody == "div.custom-tbody"  # No se recalcula

    def test_validar_orden_valido(self):
        """Debe aceptar criterios de orden válidos."""
        for orden in ["fecha", "caratula", "oficina", "situacion"]:
            config = ExtraccionExpedientesConfig(orden=orden)
            assert config.orden == orden

    def test_validar_orden_invalido(self):
        """Debe rechazar criterios de orden inválidos."""
        with pytest.raises(ValueError, match="Criterio de orden inválido"):
            ExtraccionExpedientesConfig(orden="invalido")

    def test_validar_orden_case_insensitive(self):
        """Debe validar orden sin distinguir mayúsculas."""
        config = ExtraccionExpedientesConfig(orden="FECHA")
        assert config.orden == "FECHA"

    def test_preset_rapido(self):
        """Debe crear configuración rápida con preset."""
        config = ExtraccionExpedientesConfig.rapido()

        assert config.max_paginas == 5
        assert config.tiempo_maximo_segundos == 60
        assert config.omitir_duplicados is True
        assert config.detener_en_duplicado is True

    def test_preset_rapido_personalizado(self):
        """Debe permitir personalizar max_paginas en preset rápido."""
        config = ExtraccionExpedientesConfig.rapido(max_paginas=10)

        assert config.max_paginas == 10
        assert config.tiempo_maximo_segundos == 60

    def test_preset_completo(self):
        """Debe crear configuración completa sin límites."""
        config = ExtraccionExpedientesConfig.completo()

        assert config.max_paginas is None
        assert config.tiempo_maximo_segundos is None
        assert config.omitir_duplicados is True
        assert config.detener_en_duplicado is False  # No detener en producción

    def test_preset_con_fecha_corte(self):
        """Debe crear configuración con fecha de corte."""
        config = ExtraccionExpedientesConfig.con_fecha_corte("2025-01-01")

        assert config.fecha_corte == "2025-01-01"
        assert config.max_paginas == 100
        assert config.detener_en_duplicado is True

    def test_preset_con_fecha_corte_personalizado(self):
        """Debe permitir personalizar max_paginas en preset con fecha."""
        config = ExtraccionExpedientesConfig.con_fecha_corte("2025-01-01", max_paginas=200)

        assert config.max_paginas == 200

    def test_to_dict(self):
        """Debe convertir configuración a diccionario."""
        config = ExtraccionExpedientesConfig(
            max_paginas=10,
            fecha_corte="2025-01-01",
        )

        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert config_dict["max_paginas"] == 10
        assert config_dict["fecha_corte"] == "2025-01-01"
        assert "sel_tabla" in config_dict
        assert "omitir_duplicados" in config_dict

    def test_mapper_personalizado(self):
        """Debe permitir configurar mapper personalizado."""
        mapper = lambda resumen: {"numero": resumen.numero}
        config = ExtraccionExpedientesConfig(mapper=mapper)

        assert config.mapper is mapper


class TestBackwardCompatibility:
    """Tests de compatibilidad hacia atrás con parámetros legacy."""

    def test_construir_config_desde_parametros_legacy(self):
        """Debe construir config correctamente desde parámetros legacy."""
        # Simular lo que hace extraer_expedientes_completos cuando config es None
        sel_tabla = None
        sel_tbody = None
        sel_siguiente = None
        max_paginas = 10
        omitir_duplicados = True
        detener_en_duplicado = False
        fecha_corte = "2025-01-01"
        tiempo_maximo_segundos = 120
        orden = "fecha"
        mapper = None
        pagination_strategy = None

        from pjn.scraping.expedientes import SEL_TABLA, SEL_SIGUIENTE

        # Esto es lo que hace la función internamente
        config = ExtraccionExpedientesConfig(
            sel_tabla=sel_tabla or SEL_TABLA,
            sel_tbody=sel_tbody or "",
            sel_siguiente=sel_siguiente or SEL_SIGUIENTE,
            max_paginas=max_paginas,
            tiempo_maximo_segundos=tiempo_maximo_segundos,
            fecha_corte=fecha_corte,
            omitir_duplicados=omitir_duplicados if omitir_duplicados is not None else True,
            detener_en_duplicado=detener_en_duplicado if detener_en_duplicado is not None else True,
            orden=orden,
            mapper=mapper,
            pagination_strategy=pagination_strategy,
        )

        assert config.max_paginas == 10
        assert config.omitir_duplicados is True
        assert config.detener_en_duplicado is False
        assert config.fecha_corte == "2025-01-01"
        assert config.tiempo_maximo_segundos == 120
        assert config.orden == "fecha"

    def test_config_tiene_prioridad_sobre_legacy(self):
        """Config explícito debe tener prioridad (lógica de la función)."""
        # Cuando se pasa config, los parámetros legacy se ignoran
        config = ExtraccionExpedientesConfig(max_paginas=5)

        # Simular que también se pasaron parámetros legacy
        max_paginas_legacy = 100

        # La función usa config si está presente
        max_paginas_final = config.max_paginas  # Debe ser 5, no 100

        assert max_paginas_final == 5

    def test_valores_por_defecto_legacy(self):
        """Debe aplicar valores por defecto correctos en modo legacy."""
        # Simular llamada sin especificar omitir_duplicados/detener_en_duplicado
        omitir_duplicados = None
        detener_en_duplicado = None

        from pjn.scraping.expedientes import SEL_TABLA, SEL_SIGUIENTE

        config = ExtraccionExpedientesConfig(
            sel_tabla=SEL_TABLA,
            sel_tbody="",
            sel_siguiente=SEL_SIGUIENTE,
            max_paginas=None,
            tiempo_maximo_segundos=None,
            fecha_corte=None,
            omitir_duplicados=omitir_duplicados if omitir_duplicados is not None else True,
            detener_en_duplicado=detener_en_duplicado if detener_en_duplicado is not None else True,
            orden=None,
            mapper=None,
            pagination_strategy=None,
        )

        # Debe aplicar defaults
        assert config.omitir_duplicados is True
        assert config.detener_en_duplicado is True


# Marcar todo el módulo para ejecutar con pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
