"""Tests para GestorEstadosExpedientes.

Tests unitarios para el gestor de estados de monitoreo de expedientes.
"""

import json
from pathlib import Path

import pytest

from infrastructure.persistence.estados_expedientes import (
    ESTADO_DEFAULT,
    ESTADOS_VALIDOS,
    GestorEstadosExpedientes,
)


class TestGestorEstadosExpedientes:
    """Tests para la clase GestorEstadosExpedientes."""

    @pytest.mark.asyncio
    async def test_inicializar_gestor_crea_archivo(self, tmp_path):
        """Debe crear el archivo de estados si no existe."""
        gestor = GestorEstadosExpedientes(tmp_path)

        archivo = tmp_path / "estados_expedientes.json"
        assert archivo.exists()
        assert archivo.read_text() == "{}"

    @pytest.mark.asyncio
    async def test_guardar_y_cargar_estado(self, tmp_path):
        """Debe guardar y cargar estados correctamente."""
        gestor = GestorEstadosExpedientes(tmp_path)

        await gestor.guardar_estado("FPA-000632-2017", "activo")
        estados = await gestor.cargar_estados()

        assert estados["FPA-000632-2017"] == "activo"

    @pytest.mark.asyncio
    async def test_obtener_estado_existente(self, tmp_path):
        """Debe retornar el estado de un expediente existente."""
        gestor = GestorEstadosExpedientes(tmp_path)

        await gestor.guardar_estado("FPA-000632-2017", "pausado")
        estado = await gestor.obtener_estado("FPA-000632-2017")

        assert estado == "pausado"

    @pytest.mark.asyncio
    async def test_obtener_estado_default_si_no_existe(self, tmp_path):
        """Debe retornar estado default si el expediente no existe."""
        gestor = GestorEstadosExpedientes(tmp_path)

        estado = await gestor.obtener_estado("FPA-999999-2025")

        assert estado == ESTADO_DEFAULT

    @pytest.mark.asyncio
    async def test_actualizar_estado_existente(self, tmp_path):
        """Debe actualizar el estado de un expediente existente."""
        gestor = GestorEstadosExpedientes(tmp_path)

        await gestor.guardar_estado("FPA-000632-2017", "activo")
        await gestor.guardar_estado("FPA-000632-2017", "pausado")
        estado = await gestor.obtener_estado("FPA-000632-2017")

        assert estado == "pausado"

    @pytest.mark.asyncio
    async def test_error_estado_invalido(self, tmp_path):
        """Debe lanzar ValueError si el estado es inválido."""
        gestor = GestorEstadosExpedientes(tmp_path)

        with pytest.raises(ValueError, match="Estado 'invalido' inválido"):
            await gestor.guardar_estado("FPA-000632-2017", "invalido")

    @pytest.mark.asyncio
    async def test_obtener_activos(self, tmp_path):
        """Debe retornar solo expedientes con estado 'activo'."""
        gestor = GestorEstadosExpedientes(tmp_path)

        await gestor.guardar_estado("FPA-000632-2017", "activo")
        await gestor.guardar_estado("FPA-000633-2017", "pausado")
        await gestor.guardar_estado("FPA-000634-2017", "activo")
        await gestor.guardar_estado("FPA-000635-2017", "omitido")

        activos = await gestor.obtener_activos()

        assert len(activos) == 2
        assert "FPA-000632-2017" in activos
        assert "FPA-000634-2017" in activos
        assert "FPA-000633-2017" not in activos
        assert "FPA-000635-2017" not in activos

    @pytest.mark.asyncio
    async def test_obtener_por_estado_pausado(self, tmp_path):
        """Debe retornar expedientes con estado específico."""
        gestor = GestorEstadosExpedientes(tmp_path)

        await gestor.guardar_estado("FPA-000632-2017", "activo")
        await gestor.guardar_estado("FPA-000633-2017", "pausado")
        await gestor.guardar_estado("FPA-000634-2017", "pausado")
        await gestor.guardar_estado("FPA-000635-2017", "omitido")

        pausados = await gestor.obtener_por_estado("pausado")

        assert len(pausados) == 2
        assert "FPA-000633-2017" in pausados
        assert "FPA-000634-2017" in pausados

    @pytest.mark.asyncio
    async def test_obtener_por_estado_invalido_error(self, tmp_path):
        """Debe lanzar ValueError si el estado filtrado es inválido."""
        gestor = GestorEstadosExpedientes(tmp_path)

        with pytest.raises(ValueError, match="Estado 'inexistente' inválido"):
            await gestor.obtener_por_estado("inexistente")

    @pytest.mark.asyncio
    async def test_remover_estado(self, tmp_path):
        """Debe remover el estado de un expediente."""
        gestor = GestorEstadosExpedientes(tmp_path)

        await gestor.guardar_estado("FPA-000632-2017", "pausado")
        await gestor.remover_estado("FPA-000632-2017")
        estado = await gestor.obtener_estado("FPA-000632-2017")

        # Debe retornar default después de remover
        assert estado == ESTADO_DEFAULT

    @pytest.mark.asyncio
    async def test_remover_estado_inexistente_no_error(self, tmp_path):
        """No debe dar error al remover estado de expediente inexistente."""
        gestor = GestorEstadosExpedientes(tmp_path)

        # No debe lanzar excepción
        await gestor.remover_estado("FPA-999999-2025")

    @pytest.mark.asyncio
    async def test_obtener_estadisticas(self, tmp_path):
        """Debe retornar estadísticas correctas de estados."""
        gestor = GestorEstadosExpedientes(tmp_path)

        await gestor.guardar_estado("FPA-000632-2017", "activo")
        await gestor.guardar_estado("FPA-000633-2017", "activo")
        await gestor.guardar_estado("FPA-000634-2017", "pausado")
        await gestor.guardar_estado("FPA-000635-2017", "omitido")
        await gestor.guardar_estado("FPA-000636-2017", "omitido")
        await gestor.guardar_estado("FPA-000637-2017", "omitido")
        await gestor.guardar_estado("FPA-000638-2017", "archivado")

        stats = await gestor.obtener_estadisticas()

        assert stats["activo"] == 2
        assert stats["pausado"] == 1
        assert stats["omitido"] == 3
        assert stats["archivado"] == 1
        assert stats["total"] == 7

    @pytest.mark.asyncio
    async def test_obtener_estadisticas_con_gestor_vacio(self, tmp_path):
        """Debe retornar estadísticas en cero para gestor vacío."""
        gestor = GestorEstadosExpedientes(tmp_path)

        stats = await gestor.obtener_estadisticas()

        assert stats["activo"] == 0
        assert stats["pausado"] == 0
        assert stats["omitido"] == 0
        assert stats["archivado"] == 0
        assert stats["total"] == 0

    @pytest.mark.asyncio
    async def test_actualizar_multiples_estados(self, tmp_path):
        """Debe actualizar múltiples estados en una operación."""
        gestor = GestorEstadosExpedientes(tmp_path)

        actualizaciones = {
            "FPA-000632-2017": "pausado",
            "FPA-000633-2017": "activo",
            "FPA-000634-2017": "omitido",
        }

        await gestor.actualizar_multiples(actualizaciones)
        estados = await gestor.cargar_estados()

        assert estados["FPA-000632-2017"] == "pausado"
        assert estados["FPA-000633-2017"] == "activo"
        assert estados["FPA-000634-2017"] == "omitido"

    @pytest.mark.asyncio
    async def test_actualizar_multiples_estados_invalidos_error(self, tmp_path):
        """Debe lanzar error si algún estado es inválido en actualización múltiple."""
        gestor = GestorEstadosExpedientes(tmp_path)

        actualizaciones = {
            "FPA-000632-2017": "pausado",
            "FPA-000633-2017": "invalido",  # Estado inválido
            "FPA-000634-2017": "omitido",
        }

        with pytest.raises(ValueError, match="Estado 'invalido' inválido"):
            await gestor.actualizar_multiples(actualizaciones)

    @pytest.mark.asyncio
    async def test_persistencia_entre_instancias(self, tmp_path):
        """Los estados deben persistir entre diferentes instancias del gestor."""
        # Primera instancia
        gestor1 = GestorEstadosExpedientes(tmp_path)
        await gestor1.guardar_estado("FPA-000632-2017", "pausado")
        await gestor1.guardar_estado("FPA-000633-2017", "activo")

        # Segunda instancia (simulando reinicio)
        gestor2 = GestorEstadosExpedientes(tmp_path)
        estados = await gestor2.cargar_estados()

        assert estados["FPA-000632-2017"] == "pausado"
        assert estados["FPA-000633-2017"] == "activo"

    @pytest.mark.asyncio
    async def test_manejo_archivo_json_corrupto(self, tmp_path):
        """Debe manejar archivo JSON corrupto retornando dict vacío."""
        gestor = GestorEstadosExpedientes(tmp_path)
        archivo = tmp_path / "estados_expedientes.json"

        # Corromper archivo
        archivo.write_text("{ esto no es json válido }")

        # Debe retornar dict vacío sin lanzar excepción
        estados = await gestor.cargar_estados()
        assert estados == {}

    @pytest.mark.asyncio
    async def test_manejo_archivo_json_no_dict(self, tmp_path):
        """Debe manejar archivo JSON con formato incorrecto (no dict)."""
        gestor = GestorEstadosExpedientes(tmp_path)
        archivo = tmp_path / "estados_expedientes.json"

        # Escribir JSON válido pero no es diccionario
        archivo.write_text('["array", "en", "lugar", "de", "dict"]')

        # Debe retornar dict vacío sin lanzar excepción
        estados = await gestor.cargar_estados()
        assert estados == {}

    @pytest.mark.asyncio
    async def test_todos_los_estados_validos(self, tmp_path):
        """Debe aceptar todos los estados definidos como válidos."""
        gestor = GestorEstadosExpedientes(tmp_path)

        for idx, estado in enumerate(ESTADOS_VALIDOS):
            numero = f"FPA-{idx:06d}-2017"
            await gestor.guardar_estado(numero, estado)
            estado_obtenido = await gestor.obtener_estado(numero)
            assert estado_obtenido == estado

    @pytest.mark.asyncio
    async def test_formato_json_legible(self, tmp_path):
        """El archivo JSON debe ser legible (indentado)."""
        gestor = GestorEstadosExpedientes(tmp_path)
        archivo = tmp_path / "estados_expedientes.json"

        await gestor.guardar_estado("FPA-000632-2017", "pausado")
        await gestor.guardar_estado("FPA-000633-2017", "activo")

        contenido = archivo.read_text()

        # Debe estar indentado (contener saltos de línea)
        assert "\n" in contenido

        # Debe ser JSON válido
        data = json.loads(contenido)
        assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_unicode_en_nombres_archivo(self, tmp_path):
        """Debe manejar correctamente caracteres Unicode (ensure_ascii=False)."""
        gestor = GestorEstadosExpedientes(tmp_path)
        archivo = tmp_path / "estados_expedientes.json"

        # Guardar un estado
        await gestor.guardar_estado("FPA-000632-2017", "activo")

        # Leer el archivo directamente
        contenido = archivo.read_text(encoding="utf-8")

        # Verificar que no tiene secuencias escape unicode (\u...)
        assert "\\u" not in contenido


class TestConstantesEstados:
    """Tests para las constantes de estados."""

    def test_estados_validos_contiene_todos(self):
        """ESTADOS_VALIDOS debe contener todos los estados esperados."""
        assert "activo" in ESTADOS_VALIDOS
        assert "pausado" in ESTADOS_VALIDOS
        assert "omitido" in ESTADOS_VALIDOS
        assert "archivado" in ESTADOS_VALIDOS
        assert len(ESTADOS_VALIDOS) == 4

    def test_estado_default_es_activo(self):
        """ESTADO_DEFAULT debe ser 'activo'."""
        assert ESTADO_DEFAULT == "activo"

    def test_estado_default_esta_en_validos(self):
        """ESTADO_DEFAULT debe estar en ESTADOS_VALIDOS."""
        assert ESTADO_DEFAULT in ESTADOS_VALIDOS
