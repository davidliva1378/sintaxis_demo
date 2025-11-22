#!/usr/bin/env python3
"""
Script para indexar actuaciones existentes en ChromaDB.

Carga todas las actuaciones con texto extraído y las indexa
para búsqueda semántica con RAG.

Uso:
    python scripts/indexar_actuaciones.py [--expediente NUMERO] [--limit N] [--reset]
"""

import os
import sys
import argparse
import logging
from datetime import datetime

# Agregar paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from infrastructure.persistence.mysql_connection import MySQLConnection
from application.services.ia.embeddings_service import EmbeddingsService
from application.services.ia.rag_service import RAGService
from infrastructure.vector_store.chroma_client import ChromaClient

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_actuaciones_con_texto(
    connection,
    expediente_numero: str = None,
    limit: int = None
) -> list:
    """
    Obtiene actuaciones que tienen texto extraído.

    Args:
        connection: Conexión MySQL
        expediente_numero: Filtrar por expediente (opcional)
        limit: Límite de actuaciones

    Returns:
        Lista de actuaciones con texto
    """
    query = """
        SELECT
            a.id,
            a.expediente_id,
            a.tipo,
            a.detalle,
            a.fecha,
            a.texto_extraido,
            e.numero as expediente_numero,
            e.caratula
        FROM actuaciones a
        JOIN expedientes e ON a.expediente_id = e.id
        WHERE a.texto_extraido IS NOT NULL
        AND a.texto_extraido != ''
        AND JSON_LENGTH(a.texto_extraido) > 0
    """

    params = []

    if expediente_numero:
        query += " AND e.numero = %s"
        params.append(expediente_numero)

    query += " ORDER BY a.fecha DESC"

    if limit:
        query += f" LIMIT {limit}"

    cursor = connection.cursor(dictionary=True)
    cursor.execute(query, params)
    return cursor.fetchall()


def extraer_texto_de_json(texto_json) -> str:
    """
    Extrae el texto plano del JSON de texto_extraido.

    Args:
        texto_json: JSON con el texto estructurado

    Returns:
        Texto plano concatenado
    """
    import json

    if isinstance(texto_json, str):
        try:
            texto_json = json.loads(texto_json)
        except json.JSONDecodeError:
            return texto_json

    if not texto_json:
        return ""

    # El texto puede estar en diferentes formatos
    if isinstance(texto_json, dict):
        # Formato con páginas
        if 'paginas' in texto_json:
            textos = []
            for pagina in texto_json['paginas']:
                if isinstance(pagina, dict) and 'texto' in pagina:
                    textos.append(pagina['texto'])
                elif isinstance(pagina, str):
                    textos.append(pagina)
            return '\n\n'.join(textos)

        # Formato con texto directo
        if 'texto' in texto_json:
            return texto_json['texto']

        # Formato con texto_completo
        if 'texto_completo' in texto_json:
            return texto_json['texto_completo']

    # Si es una lista de strings
    if isinstance(texto_json, list):
        return '\n\n'.join([str(t) for t in texto_json if t])

    return str(texto_json)


def indexar_actuaciones(
    expediente_numero: str = None,
    limit: int = None,
    reset: bool = False,
    batch_size: int = 50
):
    """
    Indexa actuaciones en ChromaDB.

    Args:
        expediente_numero: Filtrar por expediente
        limit: Límite de actuaciones
        reset: Si limpiar el índice antes
        batch_size: Tamaño del batch
    """
    logger.info("Iniciando indexación de actuaciones...")

    # Inicializar servicios
    logger.info("Cargando servicios de IA...")
    embeddings = EmbeddingsService(device="cpu")  # Usar CPU para evitar problemas
    chroma = ChromaClient(
        persist_directory="./data/vector_store",
        collection_name="actuaciones"
    )
    rag = RAGService(
        embeddings_service=embeddings,
        chroma_client=chroma
    )

    # Reset si se solicita
    if reset:
        logger.warning("Limpiando índice existente...")
        try:
            chroma.delete_collection("actuaciones")
        except Exception as e:
            logger.warning(f"No se pudo eliminar colección: {e}")

    # Conectar a DB
    logger.info("Conectando a base de datos...")
    password = os.environ.get('MYSQL_PASSWORD', '')
    conn = MySQLConnection(password=password)

    try:
        connection = conn.get_connection()

        # Obtener actuaciones
        logger.info("Obteniendo actuaciones con texto...")
        actuaciones = get_actuaciones_con_texto(
            connection,
            expediente_numero=expediente_numero,
            limit=limit
        )

        total = len(actuaciones)
        logger.info(f"Encontradas {total} actuaciones para indexar")

        if total == 0:
            logger.warning("No hay actuaciones para indexar")
            return

        # Indexar por batches
        indexadas = 0
        errores = 0

        for i, actuacion in enumerate(actuaciones):
            try:
                # Extraer texto
                texto = extraer_texto_de_json(actuacion['texto_extraido'])

                if not texto or len(texto.strip()) < 50:
                    logger.debug(f"Texto muy corto, saltando: {actuacion['id']}")
                    continue

                # Metadata
                metadata = {
                    "expediente_id": str(actuacion['expediente_id']),
                    "expediente_numero": actuacion['expediente_numero'],
                    "tipo": actuacion['tipo'] or "DESCONOCIDO",
                    "fecha": actuacion['fecha'].isoformat() if actuacion['fecha'] else None,
                    "caratula": actuacion['caratula'] or ""
                }

                # Indexar
                rag.indexar_actuacion(
                    id_actuacion=str(actuacion['id']),
                    texto=texto,
                    metadata=metadata
                )

                indexadas += 1

                # Progreso
                if (i + 1) % batch_size == 0:
                    logger.info(f"Progreso: {i + 1}/{total} ({indexadas} indexadas)")

            except Exception as e:
                logger.error(f"Error indexando actuación {actuacion['id']}: {e}")
                errores += 1

        # Resumen
        logger.info("=" * 50)
        logger.info(f"Indexación completada")
        logger.info(f"  Total procesadas: {total}")
        logger.info(f"  Indexadas: {indexadas}")
        logger.info(f"  Errores: {errores}")
        logger.info(f"  Documentos en índice: {chroma.count('actuaciones')}")

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(
        description='Indexar actuaciones en ChromaDB para RAG'
    )
    parser.add_argument(
        '--expediente',
        type=str,
        help='Número de expediente específico'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Límite de actuaciones a indexar'
    )
    parser.add_argument(
        '--reset',
        action='store_true',
        help='Limpiar índice antes de indexar'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Tamaño del batch (default: 50)'
    )

    args = parser.parse_args()

    try:
        indexar_actuaciones(
            expediente_numero=args.expediente,
            limit=args.limit,
            reset=args.reset,
            batch_size=args.batch_size
        )
    except KeyboardInterrupt:
        logger.info("\nIndexación cancelada por usuario")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error fatal: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
