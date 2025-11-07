"""
Tests unitarios para el módulo de exportadores.

Prueba las funciones de exportación a diferentes formatos:
- JSON
- CSV
- HTML
- Generación de estadísticas
"""

import sys
import json
import csv
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Sistema_v6.extraccion_masiva.exportadores import (
    exportar_json,
    exportar_csv,
    exportar_csv_resultados,
    generar_estadisticas,
    generar_reporte_html,
)


class TestExportadores:
    """Tests de funciones de exportación."""

    def setup_method(self):
        """Configurar datos de prueba."""
        self.test_dir = Path("/tmp/test_extraccion_masiva")
        self.test_dir.mkdir(exist_ok=True)

        self.expedientes_prueba = [
            {
                "numero": "EXP-001-2024",
                "caratula": "DEMANDA CIVIL SOBRE DAÑOS Y PERJUICIOS",
                "dependencia": "Juzgado Civil Nro 1",
                "situacion": "Activo",
                "ultima_actuacion": "2024-01-15"
            },
            {
                "numero": "EXP-002-2024",
                "caratula": "CAUSA PENAL ROBO AGRAVADO",
                "dependencia": "Juzgado Penal Nro 2",
                "situacion": "Cerrado",
                "ultima_actuacion": "2024-01-20"
            },
            {
                "numero": "EXP-003-2024",
                "caratula": "DEMANDA LABORAL DESPIDO",
                "dependencia": "Juzgado Civil Nro 1",
                "situacion": "Activo",
                "ultima_actuacion": "2024-01-25"
            },
        ]

        self.resultados_prueba = [
            {
                "numero": "EXP-001",
                "estado": "success",
                "mensaje": "Procesado correctamente",
                "error": "",
                "timestamp": "2024-01-01T10:00:00",
                "duracion_segundos": 1.5
            },
            {
                "numero": "EXP-002",
                "estado": "error",
                "mensaje": "Error de timeout",
                "error": "Timeout al extraer datos",
                "timestamp": "2024-01-01T10:01:30",
                "duracion_segundos": 3.0
            },
        ]

    def teardown_method(self):
        """Limpiar archivos de prueba."""
        import shutil
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_exportar_json(self):
        """Test: Exportar datos a formato JSON."""
        print("\n🧪 Test: exportar_json")

        data = {
            "session_id": "test-123",
            "fecha": "2024-01-01",
            "total": 3,
            "expedientes": self.expedientes_prueba
        }

        ruta = self.test_dir / "test.json"
        resultado = exportar_json(data, ruta)

        # Verificar que el archivo fue creado
        assert resultado.exists(), "Archivo JSON no fue creado"
        print("  ✅ Archivo JSON creado")

        # Verificar contenido
        with open(resultado, 'r', encoding='utf-8') as f:
            contenido = json.load(f)

        assert contenido["session_id"] == "test-123", "Session ID incorrecto"
        assert contenido["total"] == 3, "Total incorrecto"
        assert len(contenido["expedientes"]) == 3, "Cantidad de expedientes incorrecta"
        print("  ✅ Contenido JSON válido")

        # Verificar encoding UTF-8
        assert "DAÑOS" in contenido["expedientes"][0]["caratula"], "Encoding UTF-8 incorrecto"
        print("  ✅ Encoding UTF-8 correcto")

        print("  ✅ test_exportar_json PASÓ")

    def test_exportar_csv(self):
        """Test: Exportar expedientes a CSV."""
        print("\n🧪 Test: exportar_csv")

        ruta = self.test_dir / "expedientes.csv"
        resultado = exportar_csv(self.expedientes_prueba, ruta)

        # Verificar que el archivo fue creado
        assert resultado.exists(), "Archivo CSV no fue creado"
        print("  ✅ Archivo CSV creado")

        # Leer y verificar contenido
        with open(resultado, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 3, f"Cantidad de filas incorrecta: {len(rows)}"
        print("  ✅ Cantidad de filas correcta")

        # Verificar primera fila
        assert rows[0]["numero"] == "EXP-001-2024", "Número incorrecto"
        assert "CIVIL" in rows[0]["caratula"], "Carátula incorrecta"
        print("  ✅ Datos correctos en CSV")

        print("  ✅ test_exportar_csv PASÓ")

    def test_exportar_csv_vacio(self):
        """Test: Exportar CSV con lista vacía."""
        print("\n🧪 Test: exportar_csv_vacio")

        ruta = self.test_dir / "vacio.csv"
        resultado = exportar_csv([], ruta)

        assert resultado.exists(), "Archivo CSV vacío no fue creado"
        print("  ✅ Archivo CSV vacío creado")

        # Verificar que tiene headers
        with open(resultado, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)

        assert len(headers) > 0, "No hay headers en CSV vacío"
        print("  ✅ Headers presentes en CSV vacío")

        print("  ✅ test_exportar_csv_vacio PASÓ")

    def test_exportar_csv_resultados(self):
        """Test: Exportar resultados de procesamiento a CSV."""
        print("\n🧪 Test: exportar_csv_resultados")

        ruta = self.test_dir / "resultados.csv"
        resultado = exportar_csv_resultados(self.resultados_prueba, ruta)

        assert resultado.exists(), "Archivo CSV resultados no fue creado"
        print("  ✅ Archivo CSV resultados creado")

        # Verificar contenido
        with open(resultado, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Debe tener header + 2 filas de datos
        assert len(lines) == 3, f"Cantidad de líneas incorrecta: {len(lines)}"
        print("  ✅ Cantidad de líneas correcta")

        # Verificar que tiene los campos esperados
        assert "Número" in lines[0], "Header incorrecto"
        assert "EXP-001" in lines[1], "Datos incorrectos"
        print("  ✅ Datos correctos en CSV resultados")

        print("  ✅ test_exportar_csv_resultados PASÓ")

    def test_generar_estadisticas(self):
        """Test: Generar estadísticas de expedientes."""
        print("\n🧪 Test: generar_estadisticas")

        stats = generar_estadisticas(self.expedientes_prueba)

        # Verificar estructura
        assert "total" in stats, "Falta campo 'total'"
        assert "por_dependencia" in stats, "Falta campo 'por_dependencia'"
        assert "por_situacion" in stats, "Falta campo 'por_situacion'"
        assert "fecha_generacion" in stats, "Falta campo 'fecha_generacion'"
        print("  ✅ Estructura de estadísticas correcta")

        # Verificar valores
        assert stats["total"] == 3, f"Total incorrecto: {stats['total']}"
        print(f"  ✅ Total: {stats['total']}")

        # Verificar agrupación por dependencia
        assert "Juzgado Civil Nro 1" in stats["por_dependencia"], "Falta dependencia"
        assert stats["por_dependencia"]["Juzgado Civil Nro 1"] == 2, "Conteo de dependencia incorrecto"
        print(f"  ✅ Por dependencia: {stats['por_dependencia']}")

        # Verificar agrupación por situación
        assert "Activo" in stats["por_situacion"], "Falta situación"
        assert stats["por_situacion"]["Activo"] == 2, "Conteo de situación incorrecto"
        print(f"  ✅ Por situación: {stats['por_situacion']}")

        # Verificar top palabras
        assert "top_palabras_caratulas" in stats, "Falta top palabras"
        print(f"  ✅ Top palabras: {stats['top_palabras_caratulas']}")

        print("  ✅ test_generar_estadisticas PASÓ")

    def test_generar_estadisticas_vacio(self):
        """Test: Generar estadísticas con lista vacía."""
        print("\n🧪 Test: generar_estadisticas_vacio")

        stats = generar_estadisticas([])

        assert stats["total"] == 0, "Total debe ser 0"
        assert len(stats["por_dependencia"]) == 0, "Dependencias debe estar vacío"
        assert len(stats["por_situacion"]) == 0, "Situaciones debe estar vacío"
        print("  ✅ Estadísticas vacías correctas")

        print("  ✅ test_generar_estadisticas_vacio PASÓ")

    def test_generar_reporte_html(self):
        """Test: Generar reporte HTML."""
        print("\n🧪 Test: generar_reporte_html")

        resumen = {
            "total": 100,
            "exitosos": 85,
            "errores": 10,
            "omitidos": 5,
            "duracion_segundos": 120.5,
            "velocidad_promedio": 42.3,
            "tiempo_inicio": "2024-01-01 10:00:00",
            "tiempo_fin": "2024-01-01 10:02:00"
        }

        ruta = self.test_dir / "reporte.html"
        resultado = generar_reporte_html(resumen, ruta)

        assert resultado.exists(), "Archivo HTML no fue creado"
        print("  ✅ Archivo HTML creado")

        # Verificar contenido
        with open(resultado, 'r', encoding='utf-8') as f:
            html = f.read()

        # Verificar elementos clave
        assert "<!DOCTYPE html>" in html, "No es un HTML válido"
        assert "Reporte de Extracción Masiva" in html, "Falta título"
        assert "100" in html, "Falta total"
        assert "85" in html, "Falta exitosos"
        assert "10" in html, "Falta errores"
        print("  ✅ Contenido HTML válido")

        # Verificar CSS
        assert "background:" in html or "style" in html, "Falta CSS"
        print("  ✅ CSS presente")

        # Verificar barra de progreso
        assert "progress" in html.lower(), "Falta barra de progreso"
        print("  ✅ Barra de progreso presente")

        print("  ✅ test_generar_reporte_html PASÓ")


def run_tests():
    """Ejecutar todos los tests."""
    import traceback

    test = TestExportadores()
    tests_pasados = 0
    tests_fallados = 0
    tests_totales = 0

    test_methods = [
        method for method in dir(test)
        if method.startswith('test_') and callable(getattr(test, method))
    ]

    print("\n" + "="*60)
    print("🧪 EJECUTANDO TESTS DE EXPORTADORES")
    print("="*60)

    for method_name in test_methods:
        tests_totales += 1
        try:
            test.setup_method()
            method = getattr(test, method_name)
            method()
            test.teardown_method()
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
