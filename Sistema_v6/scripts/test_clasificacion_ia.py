"""
Script de prueba para clasificación IA de actuaciones.
Prueba la integración de la Fase 1 del plan de IA.
"""

import os
import sys

# Setup paths
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.dirname(project_root))

import mysql.connector
from datetime import datetime

# Configuración BD
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': os.environ.get('MYSQL_PASSWORD', 'Sulaco01'),
    'database': 'sintaxis'
}


def get_connection():
    return mysql.connector.connect(**DB_CONFIG)


def test_clasificacion():
    """Prueba la clasificación IA de actuaciones."""

    print("=" * 60)
    print("Test de Clasificación IA - Fase 1")
    print("=" * 60)

    # Importar servicios
    from application.services.ia.clasificador_service import ClasificadorService
    from application.services.ia.ia_integration_service import IAIntegrationService

    # Inicializar clasificador
    print("\n1. Inicializando ClasificadorService...")
    clasificador = ClasificadorService()
    print("   OK - ClasificadorService listo")

    # Obtener actuaciones sin clasificar
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
        SELECT id, tipo, detalle, texto_extraido, expediente_numero
        FROM actuaciones
        WHERE tiene_texto_extraido = 1
          AND tipo_ia IS NULL
          AND LENGTH(texto_extraido) > 100
        LIMIT 5
    """
    cursor.execute(query)
    actuaciones = cursor.fetchall()

    print(f"\n2. Encontradas {len(actuaciones)} actuaciones para clasificar")

    if not actuaciones:
        print("   No hay actuaciones pendientes de clasificar")
        return

    # Clasificar cada actuación
    resultados = []

    for act in actuaciones:
        print(f"\n3. Clasificando actuación {act['id']}...")
        print(f"   Tipo original: {act['tipo']}")
        print(f"   Detalle: {act['detalle'][:50]}...")

        try:
            texto = act['texto_extraido']
            if not texto or len(texto) < 50:
                print(f"   SKIP - Texto muy corto")
                continue

            # Clasificar con LLM
            resultado = clasificador.clasificar(
                texto=texto[:3000],  # Limitar texto
                contexto=act['tipo'] or "",
                usar_llm=True
            )

            print(f"   Resultado:")
            print(f"   - Tipo IA: {resultado.get('tipo', 'N/A')}")
            print(f"   - Confianza: {resultado.get('confianza', 0):.2f}")
            print(f"   - Método: {resultado.get('metodo', 'N/A')}")
            print(f"   - Justificación: {resultado.get('justificacion', '')[:100]}...")

            # Guardar en BD
            update_query = """
                UPDATE actuaciones SET
                    tipo_ia = %s,
                    confianza_ia = %s,
                    justificacion_ia = %s,
                    metodo_ia = %s,
                    fecha_clasificacion_ia = %s
                WHERE id = %s
            """
            cursor.execute(update_query, (
                resultado.get('tipo'),
                resultado.get('confianza'),
                resultado.get('justificacion'),
                resultado.get('metodo'),
                datetime.now(),
                act['id']
            ))
            conn.commit()
            print(f"   GUARDADO en BD")

            resultados.append({
                'id': act['id'],
                'tipo_ia': resultado.get('tipo'),
                'confianza': resultado.get('confianza')
            })

        except Exception as e:
            print(f"   ERROR: {e}")

    cursor.close()
    conn.close()

    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Actuaciones procesadas: {len(resultados)}")

    if resultados:
        confianza_promedio = sum(r['confianza'] for r in resultados) / len(resultados)
        print(f"Confianza promedio: {confianza_promedio:.2f}")

        tipos = {}
        for r in resultados:
            tipo = r['tipo_ia']
            tipos[tipo] = tipos.get(tipo, 0) + 1

        print("\nTipos clasificados:")
        for tipo, count in tipos.items():
            print(f"  - {tipo}: {count}")


if __name__ == "__main__":
    test_clasificacion()
