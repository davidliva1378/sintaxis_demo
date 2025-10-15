"""Tests para validar el módulo de selectores centralizados.

Este módulo verifica que:
- Todos los selectores están definidos correctamente
- No hay selectores vacíos
- Las funciones de escape JSF funcionan correctamente
- No hay duplicados accidentales (informativo)
"""
import pytest

from Sistema_v5.pjn.selectores import (
    SEL_ACTUACIONES,
    SEL_AUTH,
    SEL_ENTRADAS,
    SEL_EXPEDIENTES,
    ActuacionesSelectores,
    AutenticacionSelectores,
    EntradasSelectores,
    ExpedientesSelectores,
    escapar_id_jsf_para_css,
    escapar_id_jsf_para_js,
)


class TestSelectoresBasicos:
    """Tests básicos de definición de selectores."""

    def test_todos_los_selectores_tienen_valor(self):
        """Verifica que ningún selector esté vacío o None."""
        clases = [SEL_AUTH, SEL_ENTRADAS, SEL_EXPEDIENTES, SEL_ACTUACIONES]

        for clase in clases:
            nombre_clase = clase.__class__.__name__.replace("Selectores", "")
            for attr_name in dir(clase):
                # Solo verificar constantes (mayúsculas)
                if attr_name.isupper():
                    valor = getattr(clase, attr_name)
                    assert valor, (
                        f"{nombre_clase}.{attr_name} está vacío. "
                        "Todos los selectores deben tener un valor definido."
                    )
                    assert isinstance(valor, str), (
                        f"{nombre_clase}.{attr_name} debe ser string, "
                        f"pero es {type(valor).__name__}"
                    )

    def test_selectores_son_strings_no_vacios(self):
        """Verifica que los selectores sean strings con contenido."""
        selectores_criticos = [
            SEL_AUTH.USUARIO,
            SEL_AUTH.PASSWORD,
            SEL_AUTH.BOTON_LOGIN,
            SEL_ENTRADAS.TABLA,
            SEL_ENTRADAS.CONTENEDOR_SCROLL,
            SEL_EXPEDIENTES.TABLA_RESULTADOS,
            SEL_ACTUACIONES.TABLA_ACTUALES,
        ]

        for selector in selectores_criticos:
            assert isinstance(selector, str)
            assert len(selector) > 0
            assert selector.strip() == selector, "Selector no debe tener espacios extra"

    def test_instancias_globales_existen(self):
        """Verifica que las instancias globales estén disponibles."""
        assert SEL_AUTH is not None
        assert SEL_ENTRADAS is not None
        assert SEL_EXPEDIENTES is not None
        assert SEL_ACTUACIONES is not None

        # Verificar tipos
        assert isinstance(SEL_AUTH, AutenticacionSelectores)
        assert isinstance(SEL_ENTRADAS, EntradasSelectores)
        assert isinstance(SEL_EXPEDIENTES, ExpedientesSelectores)
        assert isinstance(SEL_ACTUACIONES, ActuacionesSelectores)


class TestFuncionesEscape:
    """Tests para las funciones de escape de IDs JSF."""

    def test_escapar_id_jsf_para_css(self):
        """Verifica escape de dos puntos para selectores CSS."""
        assert escapar_id_jsf_para_css("expediente:action-table") == "expediente\\:action-table"
        assert escapar_id_jsf_para_css("form:button:submit") == "form\\:button\\:submit"
        assert escapar_id_jsf_para_css("simple") == "simple"

        # Verificar que se puede usar con #
        assert f"#{escapar_id_jsf_para_css('expediente:action-table')}" == "#expediente\\:action-table"

    def test_escapar_id_jsf_para_js(self):
        """Verifica escape de dos puntos para JavaScript."""
        assert escapar_id_jsf_para_js("expediente:action-table") == "expediente\\\\:action-table"
        assert escapar_id_jsf_para_js("form:button:submit") == "form\\\\:button\\\\:submit"
        assert escapar_id_jsf_para_js("simple") == "simple"

    def test_escape_con_entrada_normal(self):
        """Verifica que la función trabaje con IDs normales sin escape."""
        # Este es el caso de uso normal: IDs sin escapar
        entrada = "expediente:table"
        resultado = escapar_id_jsf_para_css(entrada)
        assert resultado == "expediente\\:table"
        assert resultado.count("\\:") == 1

    def test_escape_con_caracteres_especiales(self):
        """Verifica escape con otros caracteres especiales."""
        resultado_css = escapar_id_jsf_para_css("form:j_idt123:btn-submit")
        assert "\\:" in resultado_css
        assert "-submit" in resultado_css  # Guión no se escapa
        assert resultado_css == "form\\:j_idt123\\:btn-submit"


class TestSelectoresAutenticacion:
    """Tests específicos para selectores de autenticación."""

    def test_selectores_login_formato_correcto(self):
        """Verifica que selectores de login tengan formato válido."""
        # Usuario y password deben ser selectores por atributo
        assert "name=" in SEL_AUTH.USUARIO
        assert "name=" in SEL_AUTH.PASSWORD

        # Botón debe ser selector por ID
        assert SEL_AUTH.BOTON_LOGIN.startswith("#")

    def test_confirmacion_usa_texto(self):
        """Verifica que la confirmación use selector por texto."""
        assert "text=" in SEL_AUTH.CONFIRMACION_LOGIN or "Menú" in SEL_AUTH.CONFIRMACION_LOGIN


class TestSelectoresEntradas:
    """Tests específicos para selectores de entradas."""

    def test_tabla_usa_material_ui(self):
        """Verifica que los selectores usen clases Material UI."""
        assert "Mui" in SEL_ENTRADAS.TABLA
        assert "Mui" in SEL_ENTRADAS.EXPEDIENTE_NUMERO

    def test_contenedor_scroll_es_id(self):
        """Verifica que el contenedor de scroll sea un ID."""
        assert SEL_ENTRADAS.CONTENEDOR_SCROLL.startswith("#")

    def test_textos_fin_carga_definidos(self):
        """Verifica que los textos de fin/carga estén en español."""
        assert "eventos" in SEL_ENTRADAS.TEXTO_FIN_EVENTOS.lower()
        assert "cargando" in SEL_ENTRADAS.TEXTO_CARGANDO.lower()


class TestSelectoresExpedientes:
    """Tests específicos para selectores de expedientes."""

    def test_tabla_usa_bootstrap(self):
        """Verifica que la tabla use clases Bootstrap."""
        assert "table-striped" in SEL_EXPEDIENTES.TABLA_RESULTADOS

    def test_ids_jsf_tienen_escape(self):
        """Verifica que los IDs JSF estén escapados."""
        assert "\\:" in SEL_EXPEDIENTES.CARATULA_DETALLE
        assert "\\:" in SEL_EXPEDIENTES.DEPENDENCIA_DETALLE


class TestSelectoresActuaciones:
    """Tests específicos para selectores de actuaciones."""

    def test_tabla_actuales_vs_historicas(self):
        """Verifica que las tablas actuales e históricas sean diferentes."""
        assert SEL_ACTUACIONES.TABLA_ACTUALES != SEL_ACTUACIONES.TABLA_HISTORICAS
        assert SEL_ACTUACIONES.TABLA_ACTUALES_ID != SEL_ACTUACIONES.TABLA_HISTORICAS_ID

    def test_icono_descarga_usa_fontawesome(self):
        """Verifica que el icono de descarga use Font Awesome."""
        assert "fa-download" in SEL_ACTUACIONES.ICONO_DESCARGA

    def test_boton_siguiente_no_disabled(self):
        """Verifica que el selector de siguiente excluya disabled."""
        assert ":not(.ui-state-disabled)" in SEL_ACTUACIONES.BOTON_SIGUIENTE


class TestDuplicados:
    """Tests informativos sobre selectores duplicados."""

    def test_selectores_duplicados_informativo(self):
        """Identifica selectores duplicados (puede ser legítimo)."""
        todos_selectores = []

        for clase in [SEL_AUTH, SEL_ENTRADAS, SEL_EXPEDIENTES, SEL_ACTUACIONES]:
            for attr_name in dir(clase):
                if attr_name.isupper():
                    valor = getattr(clase, attr_name)
                    if isinstance(valor, str):
                        todos_selectores.append((clase.__class__.__name__, attr_name, valor))

        # Encontrar duplicados
        valores = [s[2] for s in todos_selectores]
        duplicados = {}

        for selector, attr, valor in todos_selectores:
            if valores.count(valor) > 1 and valor not in duplicados:
                duplicados[valor] = [
                    f"{s[0]}.{s[1]}" for s in todos_selectores if s[2] == valor
                ]

        # Solo informativo (algunos duplicados son esperados como "td")
        if duplicados:
            print("\n⚠️ Selectores duplicados encontrados (puede ser intencional):")
            for valor, ubicaciones in duplicados.items():
                print(f"  '{valor}' en: {', '.join(ubicaciones)}")


class TestConsistencia:
    """Tests de consistencia entre selectores relacionados."""

    def test_filas_vs_columnas_consistente(self):
        """Verifica que FILAS y COLUMNAS_FILA sean consistentes."""
        # Si hay un selector de FILAS, debería haber COLUMNAS
        assert hasattr(SEL_EXPEDIENTES, "FILAS_RESULTADOS")
        assert hasattr(SEL_EXPEDIENTES, "COLUMNAS_FILA")

    def test_tablas_tienen_filas_asociadas(self):
        """Verifica que cada tabla tenga su selector de filas."""
        # Verificar que los selectores de filas contienen el ID escapado de la tabla
        assert "action-table" in SEL_ACTUACIONES.FILAS_ACTUALES
        assert "action-historic-table" in SEL_ACTUACIONES.FILAS_HISTORICAS

        # Verificar que los selectores incluyen tbody tr
        assert "tbody tr" in SEL_ACTUACIONES.FILAS_ACTUALES
        assert "tbody tr" in SEL_ACTUACIONES.FILAS_HISTORICAS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
