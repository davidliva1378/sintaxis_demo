#!/usr/bin/env python3
"""Ejemplo de uso avanzado del Sistema de Extracción Inicial v2.0

Este script demuestra cómo utilizar los componentes del sistema de manera
programática, sin depender del script principal ejecutar_extraccion_inicial_v2.py

Casos de uso:
- Uso programático del FiltradorExpedientes
- Exportación/importación en múltiples formatos
- Configuración avanzada de callbacks para ExtractorCompletoBatch
- Integración con sistemas personalizados
"""

from __future__ import annotations

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Agregar directorio raíz al path para importaciones
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from Sistema_v5.extractor_inicial import (
    FiltradorExpedientes,
    exportar_json,
    exportar_csv,
    cargar_json,
)
from Sistema_v5.extractor_inicial.batch_processor import ExtractorCompletoBatch
from Sistema_v5.pjn.models.expediente import ExpedienteResumen


def ejemplo_1_filtrado_basico():
    """Ejemplo 1: Uso básico del FiltradorExpedientes."""
    print("=" * 60)
    print("EJEMPLO 1: Filtrado Básico")
    print("=" * 60)

    # Datos de ejemplo
    expedientes = [
        ExpedienteResumen(
            numero="123/2024",
            dependencia="JUZ. CIV. Y COM. FED. 1",
            caratula="GARCÍA S/ COBRO DE PESOS",
            situacion="En trámite",
            ultima_actuacion="15/10/2025",
        ),
        ExpedienteResumen(
            numero="456/2024",
            dependencia="JUZ. CIV. Y COM. FED. 2",
            caratula="PÉREZ S/ QUIEBRA",
            situacion="Archivado",
            ultima_actuacion="05/08/2025",
        ),
        ExpedienteResumen(
            numero="789/2024",
            dependencia="JUZ. CONTENCIOSO ADMINISTRATIVO 1",
            caratula="AMPARO POR MORA",
            situacion="En trámite",
            ultima_actuacion="20/10/2025",
        ),
    ]

    # Filtrar por actividad reciente y situación
    filtrador = FiltradorExpedientes(expedientes)
    resultado = (
        filtrador.filtrar_por_dias_atras(60)  # Últimos 60 días
        .filtrar_por_situacion(["En trámite"])  # Solo activos
        .obtener_resultados()
    )

    print(f"\n📊 Resultados del filtrado:")
    print(f"   Total original: {len(expedientes)}")
    print(f"   Después de filtros: {len(resultado)}")
    print(f"\n   Expedientes seleccionados:")
    for exp in resultado:
        print(f"   - {exp.numero}: {exp.caratula}")

    # Mostrar estadísticas
    stats = filtrador.obtener_estadisticas()
    print(f"\n📈 Estadísticas:")
    print(f"   Filtros aplicados: {stats['filtros_aplicados']}")
    print(f"   Porcentaje retenido: {stats['porcentaje_retenido']:.1f}%")


def ejemplo_2_filtrado_avanzado():
    """Ejemplo 2: Filtrado avanzado con regex y personalizado."""
    print("\n" + "=" * 60)
    print("EJEMPLO 2: Filtrado Avanzado")
    print("=" * 60)

    expedientes = [
        ExpedienteResumen(
            numero="100/2024",
            dependencia="JUZ. CIV. Y COM. FED. 1",
            caratula="EMPRESA ABC S.A. S/ CONCURSO PREVENTIVO",
            situacion="En trámite",
        ),
        ExpedienteResumen(
            numero="200/2024",
            dependencia="JUZ. CIV. Y COM. FED. 5",
            caratula="RODRIGUEZ JUAN S/ COBRO",
            situacion="Sentenciado",
        ),
        ExpedienteResumen(
            numero="300/2024",
            dependencia="JUZ. CONTENCIOSO ADMINISTRATIVO 3",
            caratula="EMPRESA XYZ S.R.L. S/ AMPARO",
            situacion="En trámite",
        ),
    ]

    filtrador = FiltradorExpedientes(expedientes)

    # Filtro con regex: solo juzgados civiles que terminen en dígito impar
    resultado_regex = filtrador.filtrar_por_dependencia(
        r"JUZ\. CIV\..*[13579]$", regex=True
    ).obtener_resultados()

    print(f"\n🔍 Filtro regex (juzgados impares): {len(resultado_regex)} resultados")
    for exp in resultado_regex:
        print(f"   - {exp.numero}: {exp.dependencia}")

    # Resetear y aplicar filtro personalizado
    filtrador.resetear()
    resultado_custom = filtrador.filtrar_personalizado(
        lambda exp: "EMPRESA" in exp.caratula.upper(),
        nombre_filtro="contiene_empresa",
    ).obtener_resultados()

    print(f"\n🏢 Filtro personalizado (empresas): {len(resultado_custom)} resultados")
    for exp in resultado_custom:
        print(f"   - {exp.numero}: {exp.caratula}")


def ejemplo_3_exportacion_importacion():
    """Ejemplo 3: Exportación e importación de datos."""
    print("\n" + "=" * 60)
    print("EJEMPLO 3: Exportación/Importación")
    print("=" * 60)

    expedientes = [
        ExpedienteResumen(
            numero="999/2024",
            dependencia="JUZ. FEDERAL 1",
            caratula="PRUEBA DE EXPORTACIÓN",
            situacion="En trámite",
            ultima_actuacion="23/10/2025",
        )
    ]

    # Crear directorio temporal para ejemplos
    output_dir = Path("ejemplos_output")
    output_dir.mkdir(exist_ok=True)

    # Exportar a JSON
    json_path = output_dir / "expedientes_ejemplo.json"
    exportar_json(expedientes, json_path, incluir_metadata=True)
    print(f"\n✅ Exportado a JSON: {json_path}")

    # Exportar a CSV
    csv_path = output_dir / "expedientes_ejemplo.csv"
    exportar_csv(expedientes, csv_path, incluir_header=True)
    print(f"✅ Exportado a CSV: {csv_path}")

    # Importar desde JSON
    expedientes_cargados, metadata = cargar_json(json_path)
    print(f"\n📥 Importado desde JSON:")
    print(f"   Total: {len(expedientes_cargados)}")
    print(f"   Timestamp: {metadata['timestamp']}")
    print(f"   Versión: {metadata['version']}")

    print(f"\n💾 Archivos guardados en: {output_dir.absolute()}")


async def ejemplo_4_batch_processor():
    """Ejemplo 4: Configuración avanzada del ExtractorCompletoBatch."""
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Batch Processor Configurado")
    print("=" * 60)

    # Expedientes de ejemplo
    expedientes = [
        ExpedienteResumen(
            numero=f"{i}/2024",
            dependencia="JUZ. TEST",
            caratula=f"EXPEDIENTE {i}",
            situacion="En trámite",
        )
        for i in range(1, 6)
    ]

    # Crear procesador con configuración personalizada
    batch = ExtractorCompletoBatch(
        umbral_errores_consecutivos=3,
        headless=True,
        descargar_adjuntos=False,
    )

    # Configurar callback de progreso
    progreso_log = []

    def on_progreso(indice: int, total: int, expediente):
        mensaje = f"[{indice}/{total}] Procesando: {expediente.numero}"
        progreso_log.append(mensaje)
        print(f"   {mensaje}")

    batch.set_callback_progreso(on_progreso)

    # Configurar callback de umbral de errores
    def on_umbral_errores(num_errores: int, mensajes: list[str]):
        print(f"\n⚠️  Alcanzado umbral: {num_errores} errores consecutivos")
        print(f"   Últimos errores:")
        for msg in mensajes[-3:]:
            print(f"   - {msg}")
        # En un caso real, aquí se preguntaría al usuario
        # Por ahora, auto-continuar para el ejemplo
        return "continuar"

    batch.set_callback_error_umbral(on_umbral_errores)

    print("\n🚀 Configuración del batch:")
    print(f"   Umbral errores: {batch.umbral_errores_consecutivos}")
    print(f"   Headless: {batch.headless}")
    print(f"   Descargar adjuntos: {batch.descargar_adjuntos}")
    print(f"   Callback progreso: {'✅ Configurado' if batch._callback_progreso else '❌'}")
    print(f"   Callback umbral: {'✅ Configurado' if batch._callback_error_umbral else '❌'}")

    # Nota: No ejecutamos realmente el procesamiento en este ejemplo
    # porque requeriría credenciales reales del PJN
    print("\n💡 Nota: Para ejecutar realmente, usar:")
    print("   resumen = await batch.procesar_lote(expedientes)")


def ejemplo_5_integracion_completa():
    """Ejemplo 5: Flujo completo de filtrado → exportación."""
    print("\n" + "=" * 60)
    print("EJEMPLO 5: Integración Completa")
    print("=" * 60)

    # Simular carga de datos desde archivo
    print("\n1️⃣ Simular extracción inicial...")
    expedientes_simulados = [
        ExpedienteResumen(
            numero=f"{i}/2024",
            dependencia=f"JUZ. {'FED.' if i % 2 == 0 else 'PROV.'} {i}",
            caratula=f"CASO {i}",
            situacion="En trámite" if i % 3 != 0 else "Archivado",
            ultima_actuacion=f"{20 - i}/10/2025" if i <= 20 else None,
        )
        for i in range(1, 31)
    ]
    print(f"   ✅ {len(expedientes_simulados)} expedientes extraídos")

    # Aplicar filtros
    print("\n2️⃣ Aplicar filtros...")
    filtrador = FiltradorExpedientes(expedientes_simulados)
    seleccion = (
        filtrador.filtrar_por_dependencia("FED.", regex=False)
        .filtrar_por_situacion(["En trámite"])
        .obtener_resultados()
    )
    print(f"   ✅ {len(seleccion)} expedientes seleccionados tras filtros")

    # Exportar selección
    print("\n3️⃣ Exportar selección...")
    output_dir = Path("ejemplos_output")
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_path = output_dir / f"seleccion_{timestamp}.json"
    exportar_json(seleccion, export_path)
    print(f"   ✅ Exportado a: {export_path}")

    # Mostrar resumen
    print("\n4️⃣ Resumen del proceso:")
    stats = filtrador.obtener_estadisticas()
    print(f"   Total original: {stats['total_original']}")
    print(f"   Total filtrado: {stats['total_filtrado']}")
    print(f"   Filtros aplicados: {stats['filtros_aplicados']}")
    print(f"   Porcentaje retenido: {stats['porcentaje_retenido']:.1f}%")

    print(f"\n✅ Flujo completo ejecutado exitosamente!")


def main():
    """Ejecuta todos los ejemplos."""
    print("\n" + "🎯" * 30)
    print("EJEMPLOS DE USO - SISTEMA DE EXTRACCIÓN INICIAL V2.0")
    print("🎯" * 30)

    # Ejemplos síncronos
    ejemplo_1_filtrado_basico()
    ejemplo_2_filtrado_avanzado()
    ejemplo_3_exportacion_importacion()
    ejemplo_5_integracion_completa()

    # Ejemplo asíncrono
    print("\n" + "=" * 60)
    print("EJEMPLO 4: Batch Processor (requiere asyncio)")
    print("=" * 60)
    asyncio.run(ejemplo_4_batch_processor())

    print("\n" + "=" * 60)
    print("✅ Todos los ejemplos completados exitosamente!")
    print("=" * 60)
    print("\n💡 Para más información, consulta:")
    print("   - Sistema_v5/docs/GUIA_EXTRACCION_INICIAL_V2.md")
    print("   - Sistema_v5/docs/RESUMEN_V2.0.md")
    print()


if __name__ == "__main__":
    main()
