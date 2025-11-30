"""
Tests unitarios para utilidades de expedientes.

Prueba las funciones de normalización y desnormalización de números de expediente.
"""

import pytest
from core.domain.expediente_utils import (
    normalizar_numero_expediente,
    desnormalizar_numero_expediente,
)


@pytest.mark.unit
class TestNormalizacionExpedientes:
    """Tests para normalización de números de expediente."""

    def test_normalizar_con_padding(self):
        """Debe agregar padding de ceros a la parte numérica."""
        assert normalizar_numero_expediente("FPA 3449/2020") == "FPA_003449_2020"
        assert normalizar_numero_expediente("FRE 166/2019") == "FRE_000166_2019"
        assert normalizar_numero_expediente("CAF 1/2021") == "CAF_000001_2021"

    def test_normalizar_ya_normalizado(self):
        """No debe modificar si ya está normalizado."""
        assert normalizar_numero_expediente("FPA_003449_2020") == "FPA_003449_2020"
        assert normalizar_numero_expediente("FRE_000166_2019") == "FRE_000166_2019"

    def test_normalizar_formatos_variados(self):
        """Debe manejar diferentes formatos de entrada."""
        # Con barra
        assert normalizar_numero_expediente("FPA 3449/2020") == "FPA_003449_2020"
        # Con espacios múltiples
        assert normalizar_numero_expediente("FPA  3449  2020") == "FPA_003449_2020"
        # Con barra y espacios
        assert normalizar_numero_expediente("FPA  3449 / 2020") == "FPA_003449_2020"

    def test_normalizar_string_vacio(self):
        """Debe manejar string vacío."""
        assert normalizar_numero_expediente("") == ""

    def test_normalizar_none(self):
        """Debe manejar None."""
        assert normalizar_numero_expediente(None) is None

    def test_normalizar_con_espacios_extra(self):
        """Debe eliminar espacios al inicio y final."""
        assert normalizar_numero_expediente("  FPA 3449/2020  ") == "FPA_003449_2020"

    @pytest.mark.parametrize("entrada,esperado", [
        ("FPA 1/2020", "FPA_000001_2020"),
        ("FPA 99/2020", "FPA_000099_2020"),
        ("FPA 999/2020", "FPA_000999_2020"),
        ("FPA 9999/2020", "FPA_009999_2020"),
        ("FPA 99999/2020", "FPA_099999_2020"),
        ("FPA 999999/2020", "FPA_999999_2020"),
    ])
    def test_padding_diferentes_longitudes(self, entrada, esperado):
        """Debe manejar números de diferentes longitudes."""
        assert normalizar_numero_expediente(entrada) == esperado

    def test_normalizar_sin_formato_estandar(self):
        """Debe manejar formatos no estándar sin fallar."""
        # Formato sin año
        resultado = normalizar_numero_expediente("FPA 3449")
        assert "_" in resultado  # Debe tener algún separador

        # Formato con más partes
        resultado = normalizar_numero_expediente("FPA 3449/2020/I")
        assert "_" in resultado


@pytest.mark.unit
class TestDesnormalizacionExpedientes:
    """Tests para desnormalización de números de expediente."""

    def test_desnormalizar_formato_estandar(self):
        """Debe revertir la normalización al formato PJN."""
        assert desnormalizar_numero_expediente("FPA_003449_2020") == "FPA 003449/2020"
        assert desnormalizar_numero_expediente("FRE_000166_2019") == "FRE 000166/2019"

    def test_desnormalizar_sin_guiones_bajos(self):
        """No debe modificar si no tiene guiones bajos."""
        assert desnormalizar_numero_expediente("FPA 3449/2020") == "FPA 3449/2020"

    def test_desnormalizar_string_vacio(self):
        """Debe manejar string vacío."""
        assert desnormalizar_numero_expediente("") == ""

    def test_desnormalizar_none(self):
        """Debe manejar None."""
        assert desnormalizar_numero_expediente(None) is None

    def test_desnormalizar_formato_no_estandar(self):
        """Debe manejar formatos no estándar sin fallar."""
        # Formato con solo dos partes
        resultado = desnormalizar_numero_expediente("FPA_3449")
        assert resultado == "FPA_3449"  # No modifica si no es formato estándar

        # Formato con más de tres partes
        resultado = desnormalizar_numero_expediente("FPA_3449_2020_I")
        assert resultado == "FPA_3449_2020_I"  # No modifica


@pytest.mark.unit
class TestNormalizacionDesnormalizacionRoundtrip:
    """Tests de ida y vuelta entre normalización y desnormalización."""

    @pytest.mark.parametrize("numero_original", [
        "FPA 3449/2020",
        "FRE 166/2019",
        "CAF 1/2021",
        "FPA 99999/2024",
    ])
    def test_roundtrip_normalizar_desnormalizar(self, numero_original):
        """Normalizar y luego desnormalizar debe preservar el formato."""
        # Normalizar
        normalizado = normalizar_numero_expediente(numero_original)
        
        # Desnormalizar
        desnormalizado = desnormalizar_numero_expediente(normalizado)
        
        # El resultado debe tener el mismo contenido (aunque con padding)
        # Extraer las partes para comparar
        partes_original = numero_original.replace("/", " ").split()
        partes_resultado = desnormalizado.replace("/", " ").split()
        
        # Prefijo debe ser igual
        assert partes_original[0] == partes_resultado[0]
        
        # Año debe ser igual
        assert partes_original[2] == partes_resultado[2]
        
        # Número debe ser el mismo valor (aunque con padding)
        assert int(partes_original[1]) == int(partes_resultado[1])


@pytest.mark.unit
class TestEdgeCases:
    """Tests de casos extremos y edge cases."""

    def test_normalizar_con_caracteres_especiales(self):
        """Debe manejar caracteres especiales."""
        # Con guiones - la función NO convierte guiones a guiones bajos
        resultado = normalizar_numero_expediente("FPA-3449-2020")
        # Los guiones se preservan tal cual
        assert resultado == "FPA-3449-2020"

    def test_normalizar_prefijo_largo(self):
        """Debe manejar prefijos de diferentes longitudes."""
        assert normalizar_numero_expediente("FPACIV 3449/2020") == "FPACIV_003449_2020"
        assert normalizar_numero_expediente("F 3449/2020") == "F_003449_2020"

    def test_normalizar_numero_muy_largo(self):
        """Debe manejar números muy largos sin truncar."""
        resultado = normalizar_numero_expediente("FPA 12345678/2020")
        assert "12345678" in resultado
        # No debe truncar, solo padear si es menor a 6 dígitos

    def test_normalizar_anio_dos_digitos(self):
        """Debe manejar años de 2 dígitos."""
        resultado = normalizar_numero_expediente("FPA 3449/20")
        assert "20" in resultado

    def test_normalizar_case_sensitivity(self):
        """Debe preservar mayúsculas/minúsculas del prefijo."""
        assert normalizar_numero_expediente("fpa 3449/2020") == "fpa_003449_2020"
        assert normalizar_numero_expediente("FPA 3449/2020") == "FPA_003449_2020"
        assert normalizar_numero_expediente("Fpa 3449/2020") == "Fpa_003449_2020"
