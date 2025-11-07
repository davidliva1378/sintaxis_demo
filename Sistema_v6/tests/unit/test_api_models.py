"""
Tests unitarios para los modelos Pydantic de la API.

Prueba la validación de datos de:
- ConfiguracionExtraccion
- ProgresoExtraccion
- ResumenExtraccion
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Sistema_v6.interfaz_web.backend.api.extraccion import (
    ConfiguracionExtraccion,
    ProgresoExtraccion,
    ResumenExtraccion,
    RespuestaInicio,
)


class TestModelosPydantic:
    """Tests de modelos Pydantic de la API."""

    def test_configuracion_extraccion_completa(self):
        """Test: ConfiguracionExtraccion con todos los campos."""
        print("\n🧪 Test: ConfiguracionExtraccion completa")

        config = ConfiguracionExtraccion(
            fecha_desde="2024-01-01",
            fecha_hasta="2024-12-31",
            estados=["nuevo", "monitoreado"],
            dependencias=["Juzgado 1", "Juzgado 2"],
            umbral_errores=15,
            headless=True,
            exportar_formatos=["json", "excel", "csv"]
        )

        assert config.fecha_desde == "2024-01-01", "Fecha desde incorrecta"
        assert config.fecha_hasta == "2024-12-31", "Fecha hasta incorrecta"
        assert len(config.estados) == 2, "Estados incorrectos"
        assert config.umbral_errores == 15, "Umbral incorrecto"
        assert config.headless is True, "Headless incorrecto"
        assert len(config.exportar_formatos) == 3, "Formatos incorrectos"

        print(f"  ✅ Fecha desde: {config.fecha_desde}")
        print(f"  ✅ Fecha hasta: {config.fecha_hasta}")
        print(f"  ✅ Estados: {config.estados}")
        print(f"  ✅ Formatos: {config.exportar_formatos}")
        print("  ✅ test_configuracion_extraccion_completa PASÓ")

    def test_configuracion_extraccion_minima(self):
        """Test: ConfiguracionExtraccion con valores por defecto."""
        print("\n🧪 Test: ConfiguracionExtraccion mínima")

        config = ConfiguracionExtraccion()

        assert config.fecha_desde is None, "Fecha desde debe ser None"
        assert config.fecha_hasta is None, "Fecha hasta debe ser None"
        assert config.estados is None, "Estados debe ser None"
        assert config.umbral_errores == 10, "Umbral debe ser 10 (default)"
        assert config.headless is True, "Headless debe ser True (default)"
        assert config.exportar_formatos == ["json"], "Formatos debe ser ['json'] (default)"

        print(f"  ✅ Umbral por defecto: {config.umbral_errores}")
        print(f"  ✅ Headless por defecto: {config.headless}")
        print(f"  ✅ Formatos por defecto: {config.exportar_formatos}")
        print("  ✅ test_configuracion_extraccion_minima PASÓ")

    def test_configuracion_dict_conversion(self):
        """Test: Conversión de ConfiguracionExtraccion a dict."""
        print("\n🧪 Test: Conversión a dict")

        config = ConfiguracionExtraccion(
            fecha_desde="2024-01-01",
            umbral_errores=20,
            exportar_formatos=["excel"]
        )

        data = config.dict()

        assert isinstance(data, dict), "Debe ser un diccionario"
        assert "fecha_desde" in data, "Debe tener fecha_desde"
        assert "umbral_errores" in data, "Debe tener umbral_errores"
        assert data["umbral_errores"] == 20, "Valor incorrecto"

        print(f"  ✅ Conversión a dict exitosa")
        print(f"  ✅ Keys: {list(data.keys())[:5]}...")
        print("  ✅ test_configuracion_dict_conversion PASÓ")

    def test_progreso_extraccion_creacion(self):
        """Test: Crear ProgresoExtraccion."""
        print("\n🧪 Test: ProgresoExtraccion creación")

        progreso = ProgresoExtraccion(
            session_id="ext_20240101_120000",
            estado="en_progreso",
            fase="procesamiento",
            progreso_actual=50,
            progreso_total=100,
            porcentaje=50.0,
            mensaje="Procesando expedientes...",
            errores=2,
            tiempo_transcurrido=30.5,
            tiempo_estimado=30.5,
            velocidad=98.4
        )

        assert progreso.session_id == "ext_20240101_120000", "Session ID incorrecto"
        assert progreso.estado == "en_progreso", "Estado incorrecto"
        assert progreso.fase == "procesamiento", "Fase incorrecta"
        assert progreso.progreso_actual == 50, "Progreso actual incorrecto"
        assert progreso.progreso_total == 100, "Progreso total incorrecto"
        assert progreso.porcentaje == 50.0, "Porcentaje incorrecto"
        assert progreso.errores == 2, "Errores incorrectos"

        print(f"  ✅ Session: {progreso.session_id}")
        print(f"  ✅ Progreso: {progreso.progreso_actual}/{progreso.progreso_total} ({progreso.porcentaje}%)")
        print(f"  ✅ Fase: {progreso.fase}")
        print(f"  ✅ Velocidad: {progreso.velocidad} exp/min")
        print("  ✅ test_progreso_extraccion_creacion PASÓ")

    def test_resumen_extraccion_creacion(self):
        """Test: Crear ResumenExtraccion."""
        print("\n🧪 Test: ResumenExtraccion creación")

        resumen = ResumenExtraccion(
            session_id="ext_20240101_120000",
            estado="completado",
            total=100,
            exitosos=85,
            errores=10,
            omitidos=5,
            duracion_segundos=120.5,
            velocidad_promedio=49.8,
            archivos_generados=[
                "/path/to/reporte.json",
                "/path/to/reporte.xlsx"
            ]
        )

        assert resumen.session_id == "ext_20240101_120000", "Session ID incorrecto"
        assert resumen.estado == "completado", "Estado incorrecto"
        assert resumen.total == 100, "Total incorrecto"
        assert resumen.exitosos == 85, "Exitosos incorrecto"
        assert resumen.errores == 10, "Errores incorrecto"
        assert resumen.omitidos == 5, "Omitidos incorrecto"
        assert len(resumen.archivos_generados) == 2, "Archivos incorrectos"

        # Verificar suma
        suma = resumen.exitosos + resumen.errores + resumen.omitidos
        assert suma == resumen.total, f"Suma incorrecta: {suma} != {resumen.total}"

        print(f"  ✅ Total: {resumen.total}")
        print(f"  ✅ Exitosos: {resumen.exitosos}")
        print(f"  ✅ Errores: {resumen.errores}")
        print(f"  ✅ Velocidad: {resumen.velocidad_promedio:.2f} exp/min")
        print(f"  ✅ Archivos: {len(resumen.archivos_generados)}")
        print("  ✅ test_resumen_extraccion_creacion PASÓ")

    def test_respuesta_inicio_creacion(self):
        """Test: Crear RespuestaInicio."""
        print("\n🧪 Test: RespuestaInicio creación")

        respuesta = RespuestaInicio(
            session_id="ext_20240101_120000",
            mensaje="Extracción iniciada correctamente",
            estado="iniciando"
        )

        assert respuesta.session_id == "ext_20240101_120000", "Session ID incorrecto"
        assert respuesta.mensaje == "Extracción iniciada correctamente", "Mensaje incorrecto"
        assert respuesta.estado == "iniciando", "Estado incorrecto"

        print(f"  ✅ Session: {respuesta.session_id}")
        print(f"  ✅ Mensaje: {respuesta.mensaje}")
        print(f"  ✅ Estado: {respuesta.estado}")
        print("  ✅ test_respuesta_inicio_creacion PASÓ")

    def test_validacion_tipos(self):
        """Test: Validación de tipos de Pydantic."""
        print("\n🧪 Test: Validación de tipos")

        # Probar que Pydantic valida tipos correctamente
        try:
            # Esto debe funcionar: str convertible a int
            config = ConfiguracionExtraccion(umbral_errores="15")
            assert config.umbral_errores == 15, "Conversión de str a int falló"
            print("  ✅ Conversión str → int exitosa")
        except Exception as e:
            print(f"  ❌ Error inesperado: {e}")
            raise

        # Probar conversión de bool
        config2 = ConfiguracionExtraccion(headless="false")
        # Pydantic convierte string "false" a True (cualquier string no vacío es True)
        # Para que funcione correctamente, debería enviar boolean
        print(f"  ℹ️  String 'false' → {config2.headless}")

        config3 = ConfiguracionExtraccion(headless=False)
        assert config3.headless is False, "Boolean False incorrecto"
        print("  ✅ Boolean False correcto")

        print("  ✅ test_validacion_tipos PASÓ")


def run_tests():
    """Ejecutar todos los tests."""
    import traceback

    test = TestModelosPydantic()
    tests_pasados = 0
    tests_fallados = 0
    tests_totales = 0

    test_methods = [
        method for method in dir(test)
        if method.startswith('test_') and callable(getattr(test, method))
    ]

    print("\n" + "="*60)
    print("🧪 EJECUTANDO TESTS DE MODELOS PYDANTIC")
    print("="*60)

    for method_name in test_methods:
        tests_totales += 1
        try:
            method = getattr(test, method_name)
            method()
            tests_pasados += 1
        except AssertionError as e:
            tests_fallados += 1
            print(f"\n❌ {method_name} FALLÓ:")
            print(f"   {str(e)}")
            traceback.print_exc()
        except Exception as e:
            tests_fallados += 1
            print(f"\n❌ {method_name} ERROR:")
            print(f"   {str(e)}")
            traceback.print_exc()

    print("\n" + "="*60)
    print("📊 RESUMEN DE TESTS")
    print("="*60)
    print(f"Total: {tests_totales}")
    print(f"✅ Pasados: {tests_pasados}")
    print(f"❌ Fallados: {tests_fallados}")
    print(f"Tasa de éxito: {(tests_pasados/tests_totales*100):.1f}%")
    print("="*60)

    return tests_pasados, tests_fallados


if __name__ == "__main__":
    pasados, fallados = run_tests()
    sys.exit(0 if fallados == 0 else 1)
