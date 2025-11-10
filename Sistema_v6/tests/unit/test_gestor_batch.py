"""
Tests unitarios para el módulo gestor_batch.

Prueba las dataclasses y funcionalidades básicas del gestor:
- ResultadoProcesamiento
- ResumenBatch
- Funciones auxiliares
"""

import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Sistema_v6.extraccion_masiva.gestor_batch import (
    ResultadoProcesamiento,
    ResumenBatch,
)


class TestDataclasses:
    """Tests de las dataclasses."""

    def test_resultado_procesamiento_creacion(self):
        """Test: Crear ResultadoProcesamiento."""
        print("\n🧪 Test: ResultadoProcesamiento creación")

        expediente = {"numero": "EXP-001", "caratula": "Test"}
        resultado = ResultadoProcesamiento(
            expediente=expediente,
            estado="success",
            mensaje="Procesado correctamente",
            error=None,
            timestamp=datetime.now().isoformat(),
            duracion_segundos=2.5
        )

        assert resultado.expediente["numero"] == "EXP-001", "Número incorrecto"
        assert resultado.estado == "success", "Estado incorrecto"
        assert resultado.mensaje == "Procesado correctamente", "Mensaje incorrecto"
        assert resultado.error is None, "Error debe ser None"
        assert resultado.duracion_segundos == 2.5, "Duración incorrecta"

        print(f"  ✅ Resultado creado: {resultado.expediente['numero']} - {resultado.estado}")
        print("  ✅ test_resultado_procesamiento_creacion PASÓ")

    def test_resultado_procesamiento_con_error(self):
        """Test: ResultadoProcesamiento con error."""
        print("\n🧪 Test: ResultadoProcesamiento con error")

        expediente = {"numero": "EXP-002", "caratula": "Test Error"}
        resultado = ResultadoProcesamiento(
            expediente=expediente,
            estado="error",
            mensaje="Falló el procesamiento",
            error="Timeout al extraer datos",
            timestamp=datetime.now().isoformat(),
            duracion_segundos=5.0
        )

        assert resultado.estado == "error", "Estado debe ser 'error'"
        assert resultado.error is not None, "Error no debe ser None"
        assert "Timeout" in resultado.error, "Mensaje de error incorrecto"

        print(f"  ✅ Error capturado: {resultado.error}")
        print("  ✅ test_resultado_procesamiento_con_error PASÓ")

    def test_resumen_batch_creacion(self):
        """Test: Crear ResumenBatch."""
        print("\n🧪 Test: ResumenBatch creación")

        resultado1 = ResultadoProcesamiento(
            expediente={"numero": "EXP-001"},
            estado="success",
            mensaje="OK",
            error=None,
            timestamp=datetime.now().isoformat(),
            duracion_segundos=1.5
        )

        resultado2 = ResultadoProcesamiento(
            expediente={"numero": "EXP-002"},
            estado="error",
            mensaje="Error",
            error="Timeout",
            timestamp=datetime.now().isoformat(),
            duracion_segundos=3.0
        )

        resumen = ResumenBatch(
            total=10,
            exitosos=8,
            errores=1,
            omitidos=1,
            duracion_segundos=30.5,
            resultados=[resultado1, resultado2],
            velocidad_promedio=19.67,
            tiempo_inicio=datetime.now().isoformat(),
            tiempo_fin=datetime.now().isoformat()
        )

        assert resumen.total == 10, "Total incorrecto"
        assert resumen.exitosos == 8, "Exitosos incorrecto"
        assert resumen.errores == 1, "Errores incorrecto"
        assert resumen.omitidos == 1, "Omitidos incorrecto"
        assert resumen.duracion_segundos == 30.5, "Duración incorrecta"
        assert len(resumen.resultados) == 2, "Cantidad de resultados incorrecta"
        assert resumen.velocidad_promedio == 19.67, "Velocidad incorrecta"

        print(f"  ✅ Resumen creado: {resumen.total} total, {resumen.exitosos} exitosos")
        print(f"  ✅ Velocidad: {resumen.velocidad_promedio:.2f} exp/min")
        print(f"  ✅ Resultados: {len(resumen.resultados)}")
        print("  ✅ test_resumen_batch_creacion PASÓ")

    def test_resumen_batch_calculos(self):
        """Test: Verificar cálculos del ResumenBatch."""
        print("\n🧪 Test: ResumenBatch cálculos")

        resumen = ResumenBatch(
            total=100,
            exitosos=85,
            errores=10,
            omitidos=5,
            duracion_segundos=120.0,  # 2 minutos
            resultados=[],
            velocidad_promedio=50.0,  # 100 exp / 2 min = 50 exp/min
            tiempo_inicio=datetime.now().isoformat(),
            tiempo_fin=datetime.now().isoformat()
        )

        # Verificar que suma total
        suma = resumen.exitosos + resumen.errores + resumen.omitidos
        assert suma == resumen.total, f"Suma incorrecta: {suma} != {resumen.total}"

        # Verificar porcentaje de éxito
        porcentaje_exito = (resumen.exitosos / resumen.total) * 100
        assert porcentaje_exito == 85.0, f"Porcentaje incorrecto: {porcentaje_exito}"

        print(f"  ✅ Suma total verificada: {suma} = {resumen.total}")
        print(f"  ✅ Porcentaje de éxito: {porcentaje_exito}%")
        print(f"  ✅ Duración: {resumen.duracion_segundos}s")
        print("  ✅ test_resumen_batch_calculos PASÓ")

    def test_estados_validos(self):
        """Test: Verificar estados válidos de ResultadoProcesamiento."""
        print("\n🧪 Test: Estados válidos")

        estados_validos = ["success", "error", "skipped"]

        for estado in estados_validos:
            resultado = ResultadoProcesamiento(
                expediente={"numero": f"TEST-{estado}"},
                estado=estado,
                mensaje=f"Mensaje de {estado}",
                error=None if estado == "success" else "Error de prueba",
                timestamp=datetime.now().isoformat(),
                duracion_segundos=1.0
            )

            assert resultado.estado == estado, f"Estado incorrecto: {resultado.estado}"
            print(f"  ✅ Estado '{estado}' válido")

        print("  ✅ test_estados_validos PASÓ")


def run_tests():
    """Ejecutar todos los tests."""
    import traceback

    test = TestDataclasses()
    tests_pasados = 0
    tests_fallados = 0
    tests_totales = 0

    test_methods = [
        method for method in dir(test)
        if method.startswith('test_') and callable(getattr(test, method))
    ]

    print("\n" + "="*60)
    print("🧪 EJECUTANDO TESTS DE GESTOR BATCH")
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
