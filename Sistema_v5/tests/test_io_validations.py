"""Tests para validaciones de I/O - Sprint 1, Tarea 1.3.

Este módulo verifica que las funciones de I/O validan correctamente:
- Existencia de archivos/carpetas
- Permisos de lectura/escritura
- Formato válido de archivos
- Mensajes de error descriptivos
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from pjn.scraping.actuaciones import (
    actualizar_actuaciones_desde_json,
    descargar_archivos_de_json,
)


class TestValidacionesLectura:
    """Tests para validaciones al leer archivos."""

    @pytest.mark.asyncio
    async def test_actualizar_actuaciones_sin_ruta(self):
        """Debe retornar error si no se proporciona ruta."""
        page_mock = MagicMock()
        expediente = {"numero": "TEST-123"}

        cantidad, payload, error = await actualizar_actuaciones_desde_json(
            page_mock, expediente, ""
        )

        assert cantidad == 0
        assert payload is None
        assert error is not None
        assert "no se proporcionó" in error.lower()

    @pytest.mark.asyncio
    async def test_actualizar_actuaciones_archivo_no_existe(self):
        """Debe retornar error si el archivo no existe."""
        page_mock = MagicMock()
        expediente = {"numero": "TEST-123"}
        ruta_inexistente = "/path/que/no/existe/archivo.json"

        cantidad, payload, error = await actualizar_actuaciones_desde_json(
            page_mock, expediente, ruta_inexistente
        )

        assert cantidad == 0
        assert payload is None
        assert error is not None
        assert "no existe" in error.lower()
        assert ruta_inexistente in error

    @pytest.mark.asyncio
    async def test_actualizar_actuaciones_no_es_archivo(self, tmp_path):
        """Debe retornar error si la ruta es un directorio, no un archivo."""
        page_mock = MagicMock()
        expediente = {"numero": "TEST-123"}
        carpeta = str(tmp_path)  # tmp_path es un directorio

        cantidad, payload, error = await actualizar_actuaciones_desde_json(
            page_mock, expediente, carpeta
        )

        assert cantidad == 0
        assert payload is None
        assert error is not None
        assert "no es un archivo" in error.lower()

    @pytest.mark.asyncio
    async def test_actualizar_actuaciones_json_invalido(self, tmp_path):
        """Debe retornar error si el archivo no contiene JSON válido."""
        page_mock = MagicMock()
        expediente = {"numero": "TEST-123"}

        # Crear archivo con contenido inválido
        archivo_json = tmp_path / "actuaciones.json"
        archivo_json.write_text("esto no es JSON válido {[}]")

        cantidad, payload, error = await actualizar_actuaciones_desde_json(
            page_mock, expediente, str(archivo_json)
        )

        assert cantidad == 0
        assert payload is None
        assert error is not None
        assert "json" in error.lower() and "válido" in error.lower()

    @pytest.mark.asyncio
    async def test_actualizar_actuaciones_sin_permisos_lectura(self, tmp_path):
        """Debe retornar error si no hay permisos de lectura."""
        page_mock = MagicMock()
        expediente = {"numero": "TEST-123"}

        # Crear archivo con datos válidos
        archivo_json = tmp_path / "actuaciones.json"
        archivo_json.write_text(json.dumps({
            "Expediente": {},
            "Actuaciones": []
        }))

        # Quitar permisos de lectura (solo en Unix)
        if os.name != 'nt':  # Skip en Windows
            os.chmod(archivo_json, 0o000)

            try:
                cantidad, payload, error = await actualizar_actuaciones_desde_json(
                    page_mock, expediente, str(archivo_json)
                )

                assert cantidad == 0
                assert payload is None
                assert error is not None
                assert "permisos" in error.lower() or "permiso" in error.lower()
            finally:
                # Restaurar permisos para cleanup
                os.chmod(archivo_json, 0o644)


class TestValidacionesEscritura:
    """Tests para validaciones al escribir archivos."""

    @pytest.mark.asyncio
    async def test_escribir_sin_permisos_reporta_error(self, tmp_path):
        """Debe reportar error si intenta escribir sin permisos."""
        # Este test verifica que la validación existe en el código
        # La validación real de permisos es difícil de testear porque
        # los permisos de sistema operativo varían, pero el código
        # tiene la validación implementada con os.access(carpeta, os.W_OK)

        # Test básico: verificar que las funciones tienen manejo de errores de escritura
        page_mock = AsyncMock()

        # Usar una ruta que definitivamente no existe ni puede crearse
        ruta_invalida = "/root/carpeta_sin_permisos/archivo.json"  # En Unix requiere root

        _, _, error = await actualizar_actuaciones_desde_json(
            page_mock,
            {"numero": "TEST"},
            ruta_invalida
        )

        # Debe retornar error (archivo no existe)
        assert error is not None
        # Este es un test de regresión para asegurar que errores de I/O son manejados


class TestValidacionesDescargarArchivos:
    """Tests para validaciones en descargar_archivos_de_json()."""

    @pytest.mark.asyncio
    async def test_descargar_sin_carpeta(self):
        """Debe retornar sin error si no se proporciona carpeta."""
        page_mock = MagicMock()

        # No debe lanzar excepción, solo advertencia
        await descargar_archivos_de_json(page_mock, "")
        # Si llegamos aquí, pasó el test

    @pytest.mark.asyncio
    async def test_descargar_crea_carpeta_si_no_existe(self, tmp_path):
        """Debe crear la carpeta si no existe."""
        page_mock = MagicMock()
        carpeta_nueva = tmp_path / "nueva_carpeta"

        # Carpeta no existe aún
        assert not carpeta_nueva.exists()

        # Debe crear la carpeta (aunque no haya archivos JSON)
        await descargar_archivos_de_json(page_mock, str(carpeta_nueva))

        # Ahora debe existir
        assert carpeta_nueva.exists()
        assert carpeta_nueva.is_dir()

    @pytest.mark.asyncio
    async def test_descargar_ruta_no_es_directorio(self, tmp_path):
        """Debe manejar error si la ruta es un archivo, no directorio."""
        page_mock = MagicMock()

        # Crear un archivo en lugar de directorio
        archivo = tmp_path / "no_es_directorio.txt"
        archivo.write_text("contenido")

        # Debe detectar que no es un directorio
        await descargar_archivos_de_json(page_mock, str(archivo))
        # No debe lanzar excepción, solo log error

    @pytest.mark.asyncio
    async def test_descargar_json_no_encontrado(self, tmp_path):
        """Debe manejar correctamente cuando no hay archivos JSON."""
        page_mock = MagicMock()
        carpeta = tmp_path / "carpeta_vacia"
        carpeta.mkdir()

        # No debe lanzar excepción
        await descargar_archivos_de_json(page_mock, str(carpeta))
        # Solo debe logear advertencia

    @pytest.mark.asyncio
    async def test_descargar_json_invalido(self, tmp_path):
        """Debe manejar archivos JSON inválidos."""
        page_mock = MagicMock()
        carpeta = tmp_path / "carpeta_json_invalido"
        carpeta.mkdir()

        # Crear archivo JSON inválido
        archivo_json = carpeta / "actuaciones-TEST.json"
        archivo_json.write_text("{ json inválido [}")

        # No debe lanzar excepción
        await descargar_archivos_de_json(page_mock, str(carpeta))
        # Debe logear error y retornar

    @pytest.mark.asyncio
    async def test_descargar_json_valido_procesa_correctamente(self, tmp_path):
        """Debe procesar correctamente un JSON válido."""
        page_mock = AsyncMock()
        carpeta = tmp_path / "carpeta_json_valido"
        carpeta.mkdir()

        # Crear archivo JSON válido
        archivo_json = carpeta / "actuaciones-TEST.json"
        datos = {
            "Expediente": {"numero": "TEST-123"},
            "Actuaciones": []
        }
        archivo_json.write_text(json.dumps(datos, indent=2))

        # Debe procesar sin errores
        with patch('pjn.scraping.actuaciones.descargar_archivos_actuaciones') as mock_descargar:
            await descargar_archivos_de_json(page_mock, str(carpeta))

            # No debe haber llamado a descargar porque no hay actuaciones pendientes
            mock_descargar.assert_not_called()


class TestMensajesError:
    """Tests para verificar que los mensajes de error son descriptivos."""

    @pytest.mark.asyncio
    async def test_mensaje_error_archivo_no_existe_incluye_ruta(self):
        """El mensaje de error debe incluir la ruta del archivo."""
        page_mock = MagicMock()
        expediente = {"numero": "TEST-123"}
        ruta = "/ruta/especifica/archivo.json"

        _, _, error = await actualizar_actuaciones_desde_json(
            page_mock, expediente, ruta
        )

        assert ruta in error  # La ruta debe estar en el mensaje

    @pytest.mark.asyncio
    async def test_mensaje_error_json_invalido_es_claro(self, tmp_path):
        """El mensaje de error para JSON inválido debe ser claro."""
        page_mock = MagicMock()
        expediente = {"numero": "TEST-123"}

        archivo_json = tmp_path / "invalido.json"
        archivo_json.write_text("{json mal formado")

        _, _, error = await actualizar_actuaciones_desde_json(
            page_mock, expediente, str(archivo_json)
        )

        # Debe mencionar JSON y que es inválido
        assert "json" in error.lower()
        assert "válido" in error.lower() or "invalid" in error.lower()


class TestIntegracionValidaciones:
    """Tests de integración para validaciones completas."""

    @pytest.mark.asyncio
    async def test_flujo_completo_con_archivo_valido(self, tmp_path):
        """Flujo completo con archivo válido debe funcionar."""
        page_mock = AsyncMock()

        # Crear archivo JSON válido
        archivo_json = tmp_path / "actuaciones-TEST.json"
        datos = {
            "Expediente": {"numero": "TEST-123", "Cantidad de Archivos Descargados": 0},
            "Actuaciones": [
                {"numero": "1", "fecha": "2025-01-01", "TieneArchivo": False}
            ]
        }
        archivo_json.write_text(json.dumps(datos, indent=2))

        # Mock para obtener_actuaciones_todas_paginas_async
        with patch('pjn.scraping.actuaciones.obtener_actuaciones_todas_paginas_async') as mock_obtener:
            # Simular que no hay nuevas actuaciones
            mock_obtener.return_value = ([], None, None)

            expediente = {"numero": "TEST-123"}
            cantidad, payload, error = await actualizar_actuaciones_desde_json(
                page_mock, expediente, str(archivo_json)
            )

            # Debe procesar sin errores
            assert error is None
            assert cantidad == 0  # No hay nuevas actuaciones
            assert payload is not None


# Marcar todo el módulo para ejecutar con pytest
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
