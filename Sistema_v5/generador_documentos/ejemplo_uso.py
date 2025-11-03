#!/usr/bin/env python3
"""
Ejemplo de uso del Generador de Documentos con procesador_pdf.

Este script demuestra cómo usar el filtrado inteligente para generar
documentos jurídicos de mejor calidad, usando solo contenido relevante.

Uso:
    python ejemplo_uso.py

Autor: Sistema SintaXis
Fecha: 2025-11-03
"""

import json
from pathlib import Path

# Importar el generador
try:
    from Sistema_v5.generador_documentos import (
        FiltroContenidoInteligente,
        GeneradorDocumentosBase,
        generar_contexto_filtrado,
        PROCESADOR_DISPONIBLE
    )
except ImportError as e:
    print(f"❌ Error importando generador: {e}")
    print("   Ejecuta desde la raíz del proyecto: python Sistema_v5/generador_documentos/ejemplo_uso.py")
    exit(1)


def ejemplo_1_filtrado_basico():
    """Ejemplo 1: Filtrado básico de actuaciones."""
    print("\n" + "=" * 70)
    print("EJEMPLO 1: Filtrado Básico de Actuaciones")
    print("=" * 70)

    # Actuaciones de ejemplo
    actuaciones = [
        {
            "Fecha": "01/11/2025",
            "Tipo": "CEDULA_ELECTRONICA",
            "Detalle": "Se notifica sentencia definitiva",
            "TieneArchivo": True
        },
        {
            "Fecha": "28/10/2025",
            "Tipo": "PROVEIDO",
            "Detalle": "Agréguese",
            "TieneArchivo": False
        },
        {
            "Fecha": "25/10/2025",
            "Tipo": "AUTO",
            "Detalle": "Se da por presentado el escrito y por constituido el domicilio electrónico",
            "TieneArchivo": False
        },
        {
            "Fecha": "20/10/2025",
            "Tipo": "SENTENCIA",
            "Detalle": "Se hace lugar a la demanda",
            "TieneArchivo": True
        },
    ]

    if not PROCESADOR_DISPONIBLE:
        print("⚠️ procesador_pdf no disponible - ejemplo no puede ejecutarse")
        return

    # Crear filtro
    filtro = FiltroContenidoInteligente(min_utilidad="MEDIA")

    # Filtrar actuaciones
    resultado = filtro.filtrar_actuaciones(actuaciones, incluir_estadisticas=True)

    # Mostrar estadísticas
    print(f"\n📊 Estadísticas de filtrado:")
    stats = resultado["estadisticas"]
    print(f"  Total actuaciones: {stats['total']}")
    print(f"  Filtradas (incluidas): {stats['filtradas']}")
    print(f"  Utilidad ALTA: {stats['por_utilidad']['ALTA']}")
    print(f"  Utilidad MEDIA: {stats['por_utilidad']['MEDIA']}")
    print(f"  Utilidad BAJA: {stats['por_utilidad']['BAJA']}")
    print(f"  Utilidad NULA: {stats['por_utilidad']['NULA']}")

    # Mostrar actuaciones filtradas
    print(f"\n📋 Actuaciones incluidas (utilidad MEDIA o superior):")
    for act in resultado["actuaciones"]:
        print(f"  • {act.tipo} ({act.utilidad}) - {act.detalle[:50]}...")


def ejemplo_2_contexto_para_llm():
    """Ejemplo 2: Generar contexto optimizado para LLM."""
    print("\n" + "=" * 70)
    print("EJEMPLO 2: Contexto Optimizado para LLM")
    print("=" * 70)

    actuaciones = [
        {
            "Fecha": "01/11/2025",
            "Tipo": "CEDULA_ELECTRONICA",
            "Detalle": "Se notifica sentencia definitiva que hace lugar a la demanda",
            "TieneArchivo": True
        },
        {
            "Fecha": "15/10/2025",
            "Tipo": "SENTENCIA",
            "Detalle": "SENTENCIA DEFINITIVA: Se hace lugar a la demanda por daños y perjuicios",
            "TieneArchivo": True
        },
        {
            "Fecha": "10/10/2025",
            "Tipo": "AUTO",
            "Detalle": "Se tienen presentes las pruebas ofrecidas y se fija audiencia",
            "TieneArchivo": False
        },
    ]

    if not PROCESADOR_DISPONIBLE:
        print("⚠️ procesador_pdf no disponible - ejemplo no puede ejecutarse")
        return

    # Generar contexto en formato markdown
    contexto = generar_contexto_filtrado(
        actuaciones,
        min_utilidad="ALTA",
        formato="markdown",
        max_caracteres=2000
    )

    print("\n📝 Contexto generado (formato Markdown):")
    print(contexto)


def ejemplo_3_generador_documento():
    """Ejemplo 3: Usar generador completo para crear documento."""
    print("\n" + "=" * 70)
    print("EJEMPLO 3: Generador de Documento Completo")
    print("=" * 70)

    if not PROCESADOR_DISPONIBLE:
        print("⚠️ procesador_pdf no disponible - ejemplo no puede ejecutarse")
        return

    # Datos del expediente
    expediente_datos = {
        "numero": "FSM 7000123/2024",
        "caratula": "PEREZ JUAN C/ GOMEZ MARIA S/ DAÑOS Y PERJUICIOS",
        "dependencia": "Juzgado Federal San Martín"
    }

    # Actuaciones del expediente
    actuaciones = [
        {
            "Fecha": "01/11/2025",
            "Tipo": "CEDULA_ELECTRONICA",
            "Detalle": "Se notifica sentencia definitiva que hace lugar a la demanda",
            "TieneArchivo": True
        },
        {
            "Fecha": "28/10/2025",
            "Tipo": "PROVEIDO",
            "Detalle": "Agréguese",
            "TieneArchivo": False
        },
        {
            "Fecha": "15/10/2025",
            "Tipo": "SENTENCIA",
            "Detalle": "SENTENCIA DEFINITIVA: Se hace lugar a la demanda por daños y perjuicios, condenando a la parte demandada al pago de $5.000.000",
            "TieneArchivo": True
        },
        {
            "Fecha": "10/10/2025",
            "Tipo": "AUTO",
            "Detalle": "Se tienen presentes las pruebas ofrecidas y se fija audiencia para el día 12/10/2025",
            "TieneArchivo": False
        },
        {
            "Fecha": "05/10/2025",
            "Tipo": "PROVEIDO",
            "Detalle": "Téngase presente",
            "TieneArchivo": False
        },
    ]

    # Resolución a apelar
    resolucion_apelada = {
        "tipo": "SENTENCIA_DEFINITIVA",
        "fecha": "15/10/2025",
        "detalle": "Sentencia que hace lugar a la demanda"
    }

    # Crear generador
    generador = GeneradorDocumentosBase(usar_filtrado=True)

    # Generar recurso de apelación
    contexto_recurso = generador.generar_recurso_apelacion(
        expediente_datos,
        actuaciones,
        resolucion_apelada,
        usar_solo_relevantes=True
    )

    print("\n📄 Contexto generado para Recurso de Apelación:")
    print(contexto_recurso[:1000])  # Primeros 1000 caracteres
    print("\n[... contexto completo disponible para el LLM ...]")

    print(f"\n✅ Contexto total: {len(contexto_recurso)} caracteres")
    print(f"   Solo incluye actuaciones de utilidad ALTA o MEDIA")
    print(f"   Excluyó automáticamente: {len([a for a in actuaciones if a['Tipo'] == 'PROVEIDO'])} proveídos de mero trámite")


def ejemplo_4_comparacion():
    """Ejemplo 4: Comparar contexto CON y SIN filtrado."""
    print("\n" + "=" * 70)
    print("EJEMPLO 4: Comparación CON vs SIN Filtrado")
    print("=" * 70)

    actuaciones = [
        {"Fecha": "01/11/2025", "Tipo": "CEDULA_ELECTRONICA", "Detalle": "Se notifica sentencia definitiva", "TieneArchivo": True},
        {"Fecha": "28/10/2025", "Tipo": "PROVEIDO", "Detalle": "Agréguese", "TieneArchivo": False},
        {"Fecha": "27/10/2025", "Tipo": "PROVEIDO", "Detalle": "Téngase presente", "TieneArchivo": False},
        {"Fecha": "26/10/2025", "Tipo": "PROVEIDO", "Detalle": "Agréguese", "TieneArchivo": False},
        {"Fecha": "25/10/2025", "Tipo": "AUTO", "Detalle": "Se da por presentado el escrito", "TieneArchivo": False},
        {"Fecha": "20/10/2025", "Tipo": "SENTENCIA", "Detalle": "Se hace lugar a la demanda", "TieneArchivo": True},
        {"Fecha": "15/10/2025", "Tipo": "PROVEIDO", "Detalle": "Agréguese", "TieneArchivo": False},
        {"Fecha": "10/10/2025", "Tipo": "PROVEIDO", "Detalle": "Téngase presente", "TieneArchivo": False},
    ]

    if not PROCESADOR_DISPONIBLE:
        print("⚠️ procesador_pdf no disponible - ejemplo no puede ejecutarse")
        return

    # SIN filtrado
    generador_sin_filtro = GeneradorDocumentosBase(usar_filtrado=False)
    contexto_sin_filtro = generador_sin_filtro.preparar_contexto(
        actuaciones,
        formato="texto"
    )

    # CON filtrado
    generador_con_filtro = GeneradorDocumentosBase(usar_filtrado=True)
    contexto_con_filtro = generador_con_filtro.preparar_contexto(
        actuaciones,
        min_utilidad="MEDIA",
        formato="texto"
    )

    print(f"\n📊 Comparación de resultados:")
    print(f"  Total actuaciones originales: {len(actuaciones)}")
    print(f"  SIN filtrado:")
    print(f"    - Caracteres: {len(contexto_sin_filtro)}")
    print(f"    - Actuaciones incluidas: {len(actuaciones)}")
    print(f"  CON filtrado (min_utilidad=MEDIA):")
    print(f"    - Caracteres: {len(contexto_con_filtro)}")
    print(f"    - Reducción: {100 - (len(contexto_con_filtro) / len(contexto_sin_filtro) * 100):.1f}%")
    print(f"\n✅ El filtrado redujo el tamaño del contexto eliminando proveídos irrelevantes")


def main():
    """Ejecuta todos los ejemplos."""
    print("\n" + "=" * 70)
    print("EJEMPLOS DE USO: GENERADOR DE DOCUMENTOS CON procesador_pdf")
    print("=" * 70)

    if not PROCESADOR_DISPONIBLE:
        print("\n❌ procesador_pdf no está disponible")
        print("   Instala las dependencias: pip install -r Sistema_v5/procesador_pdf/requirements.txt")
        return

    print(f"\n✅ procesador_pdf disponible")
    print("   Ejecutando ejemplos...\n")

    try:
        ejemplo_1_filtrado_basico()
        ejemplo_2_contexto_para_llm()
        ejemplo_3_generador_documento()
        ejemplo_4_comparacion()

        print("\n" + "=" * 70)
        print("✅ EJEMPLOS COMPLETADOS")
        print("=" * 70)
        print("\nPróximos pasos:")
        print("  1. Integrar con un LLM real (OpenAI, Anthropic, Ollama, etc.)")
        print("  2. Crear templates para diferentes tipos de documentos")
        print("  3. Implementar generación automática basada en el contexto filtrado")

    except Exception as e:
        print(f"\n❌ Error ejecutando ejemplos: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
