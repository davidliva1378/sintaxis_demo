"""
Servicio de Integración de IA con Procesamiento de Actuaciones.

Este servicio actúa como intermediario entre el procesamiento de actuaciones
y los servicios de IA, proporcionando:
- Clasificación automática de actuaciones
- Indexación en Qdrant para búsqueda semántica
- Extracción de entidades jurídicas

Se integra con ProcesadorActuacionesService para procesamiento automático.
"""

import logging
import os
import re
from typing import Optional
from datetime import datetime

from infrastructure.persistence.entidades_repository import EntidadesRepository


def normalizar_numero_expediente(numero: str) -> str:
    """
    Normaliza el número de expediente al formato de la BD.

    Convierte formatos como:
    - "FPO-006767-2025" -> "FPO_006767_2025"
    - "FPO 006767/2025" -> "FPO_006767_2025"

    Args:
        numero: Número de expediente en cualquier formato

    Returns:
        Número normalizado con guiones bajos
    """
    if not numero:
        return ""
    # Reemplazar espacios, guiones y barras por guiones bajos
    normalizado = re.sub(r'[\s\-/]', '_', numero)
    return normalizado

logger = logging.getLogger(__name__)


class IAIntegrationService:
    """
    Servicio de integración de IA para procesamiento de actuaciones.

    Proporciona una interfaz unificada para aplicar servicios de IA
    cuando se procesan actuaciones, con lazy loading de los modelos.
    """

    def __init__(
        self,
        habilitar_clasificacion: bool = True,
        habilitar_rag: bool = True,
        habilitar_ner: bool = True,
        vector_store_path: str = "./data/vector_store"
    ):
        """
        Inicializa el servicio de integración.

        Args:
            habilitar_clasificacion: Si usar clasificación IA
            habilitar_rag: Si indexar en Qdrant
            habilitar_ner: Si extraer entidades
            vector_store_path: DEPRECADO - ya no se usa
        """
        self.habilitar_clasificacion = habilitar_clasificacion
        self.habilitar_rag = habilitar_rag
        self.habilitar_ner = habilitar_ner
        self.vector_store_path = vector_store_path

        # Servicios (lazy loading)
        self._clasificador = None
        self._rag_service = None
        self._ner_service = None

        # Repositorio para persistencia de entidades
        self._entidades_repo = EntidadesRepository()

        logger.info(
            f"IAIntegrationService inicializado - "
            f"clasificacion={habilitar_clasificacion}, "
            f"rag={habilitar_rag}, "
            f"ner={habilitar_ner}"
        )

    @property
    def clasificador(self):
        """Obtiene el clasificador (lazy loading)."""
        if self._clasificador is None and self.habilitar_clasificacion:
            from .clasificador_service import ClasificadorService
            self._clasificador = ClasificadorService()
            logger.info("ClasificadorService cargado")
        return self._clasificador

    @property
    def rag_service(self):
        """Obtiene el servicio RAG (lazy loading). Usa Qdrant internamente."""
        if self._rag_service is None and self.habilitar_rag:
            from .rag_service import RAGService
            self._rag_service = RAGService()  # RAGService ya usa Qdrant internamente
            logger.info("RAGService cargado (usando Qdrant)")
        return self._rag_service

    @property
    def ner_service(self):
        """Obtiene el servicio NER (lazy loading)."""
        if self._ner_service is None and self.habilitar_ner:
            from .ner_service import NERService
            self._ner_service = NERService()
            logger.info("NERService cargado")
        return self._ner_service

    def procesar_actuacion(
        self,
        actuacion_id: str,
        texto: str,
        metadata: dict = None,
        clasificar: bool = True,
        indexar: bool = True,
        extraer_entidades: bool = False
    ) -> dict:
        """
        Procesa una actuación con todos los servicios de IA habilitados.

        Args:
            actuacion_id: ID único de la actuación
            texto: Texto completo de la actuación
            metadata: Metadatos adicionales
            clasificar: Si clasificar la actuación
            indexar: Si indexar en Qdrant
            extraer_entidades: Si extraer entidades

        Returns:
            Dict con resultados de cada servicio
        """
        if not texto or len(texto.strip()) < 50:
            logger.debug(f"Texto muy corto para actuación {actuacion_id}, saltando IA")
            return {"skipped": True, "reason": "texto_muy_corto"}

        resultado = {
            "actuacion_id": actuacion_id,
            "clasificacion": None,
            "indexado": False,
            "entidades": None,
            "errores": []
        }

        # === Clasificación ===
        if clasificar and self.habilitar_clasificacion:
            try:
                clasificacion = self.clasificador.clasificar(
                    texto=texto,
                    contexto=metadata.get("tipo", "") if metadata else "",
                    usar_llm=True
                )
                # clasificacion es un dict con keys: tipo, confianza, justificacion, metodo
                resultado["clasificacion"] = {
                    "tipo": clasificacion.get("tipo", "DESCONOCIDO"),
                    "confianza": clasificacion.get("confianza", 0.0),
                    "justificacion": clasificacion.get("justificacion", ""),
                    "metodo": clasificacion.get("metodo", "")
                }
                logger.debug(
                    f"Actuación {actuacion_id} clasificada como "
                    f"{clasificacion.get('tipo')} ({clasificacion.get('confianza', 0):.2f})"
                )
            except Exception as e:
                logger.error(f"Error clasificando actuación {actuacion_id}: {e}")
                resultado["errores"].append(f"clasificacion: {str(e)}")

        # === Indexación RAG ===
        if indexar and self.habilitar_rag:
            try:
                # Preparar metadata para Qdrant
                qdrant_metadata = {
                    "expediente_id": str(metadata.get("expediente_id", "")),
                    "expediente_numero": metadata.get("expediente_numero", ""),
                    "tipo": metadata.get("tipo", "DESCONOCIDO"),
                    "fecha": metadata.get("fecha", ""),
                    "detalle": metadata.get("detalle", ""),
                    "caratula": metadata.get("caratula", "")
                } if metadata else {}

                # Agregar clasificación IA si está disponible
                if resultado["clasificacion"]:
                    qdrant_metadata["tipo_ia"] = resultado["clasificacion"]["tipo"]
                    qdrant_metadata["confianza_ia"] = str(resultado["clasificacion"]["confianza"])

                self.rag_service.indexar_actuacion(
                    id_actuacion=str(actuacion_id),
                    texto=texto,
                    metadata=qdrant_metadata
                )
                resultado["indexado"] = True
                logger.debug(f"Actuación {actuacion_id} indexada en Qdrant")
            except Exception as e:
                logger.error(f"Error indexando actuación {actuacion_id}: {e}")
                resultado["errores"].append(f"indexacion: {str(e)}")

        # === Extracción de Entidades ===
        if extraer_entidades and self.habilitar_ner:
            print(f"[NER DEBUG] Iniciando NER para actuación {actuacion_id}")
            logger.info(f"Iniciando extracción NER para actuación {actuacion_id} (texto: {len(texto)} chars)")
            try:
                entidades = self.ner_service.extract_juridico(texto)
                resultado["entidades"] = entidades
                print(f"[NER DEBUG] Entidades extraídas: {len(entidades)} tipos")

                # Persistir entidades extraídas
                expediente_numero_raw = metadata.get("expediente_numero", "") if metadata else ""
                # Normalizar al formato de la BD (con guiones bajos)
                expediente_numero = normalizar_numero_expediente(expediente_numero_raw)
                act_id = metadata.get("actuacion_id") if metadata else None

                print(f"[NER DEBUG] Raw: '{expediente_numero_raw}' -> Norm: '{expediente_numero}'")

                # Eliminar entidades IA anteriores para esta actuación antes de insertar nuevas
                if expediente_numero and act_id:
                    try:
                        from infrastructure.persistence.entidades_repository import EntidadesRepository
                        temp_repo = EntidadesRepository()
                        # Solo eliminar las de esta actuación específica
                        conn = temp_repo._get_connection()
                        cursor = conn.cursor()
                        cursor.execute(
                            "DELETE FROM entidades_extraidas WHERE expediente_numero = %s AND actuacion_id = %s AND origen = 'ia'",
                            (expediente_numero, act_id)
                        )
                        deleted = cursor.rowcount
                        conn.commit()
                        cursor.close()
                        conn.close()
                        if deleted > 0:
                            print(f"[NER DEBUG] Eliminadas {deleted} entidades IA anteriores de actuación {act_id}")
                    except Exception as e:
                        logger.warning(f"Error eliminando entidades anteriores: {e}")
                logger.info(f"NER: expediente_numero_raw='{expediente_numero_raw}' -> normalizado='{expediente_numero}'")

                if expediente_numero and entidades:
                    # Usar un set para evitar duplicados dentro de la misma extracción
                    entidades_unicas = set()
                    entidades_para_batch = []

                    for entity_type, items in entidades.items():
                        for item in items:
                            # Crear clave única (tipo + valor normalizado)
                            clave = (entity_type, item.strip().lower())
                            if clave not in entidades_unicas:
                                entidades_unicas.add(clave)
                                entidades_para_batch.append({
                                    "expediente_numero": expediente_numero,
                                    "actuacion_id": act_id,
                                    "entity_type": entity_type,
                                    "entity_value": item,
                                    "score": None,
                                    "start_pos": None,
                                    "end_pos": None,
                                    "origen": 'ia'
                                })

                    if entidades_para_batch:
                        print(f"[NER DEBUG] Intentando persistir {len(entidades_para_batch)} entidades únicas...")
                        count = self._entidades_repo.crear_batch(entidades_para_batch)
                        print(f"[NER DEBUG] Persistidas {count} entidades para {expediente_numero}")
                        logger.info(f"NER: Persistidas {count} entidades para {expediente_numero}")
                    else:
                        logger.info(f"NER: No hay entidades para persistir en {expediente_numero}")
                else:
                    logger.info(f"NER: expediente_numero='{expediente_numero}', entidades={bool(entidades)}")

                total_entidades = sum(len(v) for v in entidades.values())
                logger.info(f"NER: Extraídas {total_entidades} entidades de actuación {actuacion_id}")
            except Exception as e:
                logger.error(f"Error extrayendo entidades de actuación {actuacion_id}: {e}", exc_info=True)
                resultado["errores"].append(f"ner: {str(e)}")
        else:
            if not extraer_entidades:
                logger.debug(f"NER: extraer_entidades=False para actuación {actuacion_id}")
            if not self.habilitar_ner:
                logger.warning(f"NER: habilitar_ner=False en IAIntegrationService")

        return resultado

    def procesar_batch(
        self,
        actuaciones: list[dict],
        clasificar: bool = True,
        indexar: bool = True
    ) -> dict:
        """
        Procesa un lote de actuaciones.

        Args:
            actuaciones: Lista de dicts con {id, texto, metadata}
            clasificar: Si clasificar
            indexar: Si indexar

        Returns:
            Dict con estadísticas y resultados
        """
        total = len(actuaciones)
        procesadas = 0
        errores = 0
        resultados = []

        logger.info(f"Procesando batch de {total} actuaciones con IA")

        for i, act in enumerate(actuaciones):
            try:
                resultado = self.procesar_actuacion(
                    actuacion_id=act.get("id", str(i)),
                    texto=act.get("texto", ""),
                    metadata=act.get("metadata", {}),
                    clasificar=clasificar,
                    indexar=indexar
                )
                resultados.append(resultado)

                if resultado.get("skipped"):
                    continue

                if resultado.get("errores"):
                    errores += 1
                else:
                    procesadas += 1

                # Log de progreso cada 50 actuaciones
                if (i + 1) % 50 == 0:
                    logger.info(f"Progreso: {i + 1}/{total}")

            except Exception as e:
                logger.error(f"Error procesando actuación {act.get('id')}: {e}")
                errores += 1

        logger.info(
            f"Batch completado: {procesadas}/{total} procesadas, "
            f"{errores} errores"
        )

        return {
            "total": total,
            "procesadas": procesadas,
            "errores": errores,
            "resultados": resultados
        }

    def get_stats(self) -> dict:
        """
        Obtiene estadísticas del servicio.

        Returns:
            Dict con estadísticas
        """
        stats = {
            "clasificacion_habilitada": self.habilitar_clasificacion,
            "rag_habilitado": self.habilitar_rag,
            "ner_habilitado": self.habilitar_ner,
            "clasificador_cargado": self._clasificador is not None,
            "rag_cargado": self._rag_service is not None,
            "ner_cargado": self._ner_service is not None
        }

        # Agregar stats de Qdrant si está disponible
        if self._rag_service:
            try:
                rag_stats = self._rag_service.get_stats()
                stats["documentos_indexados"] = rag_stats.get("total_indexed", 0)
            except Exception:
                stats["documentos_indexados"] = -1

        return stats


# Singleton para uso global
_ia_integration_instance: Optional[IAIntegrationService] = None


def get_ia_integration_service(
    habilitar_clasificacion: bool = True,
    habilitar_rag: bool = True,
    habilitar_ner: bool = True
) -> IAIntegrationService:
    """
    Obtiene la instancia singleton del servicio de integración IA.

    Args:
        habilitar_clasificacion: Si usar clasificación
        habilitar_rag: Si usar RAG
        habilitar_ner: Si usar NER

    Returns:
        Instancia del servicio
    """
    global _ia_integration_instance

    if _ia_integration_instance is None:
        _ia_integration_instance = IAIntegrationService(
            habilitar_clasificacion=habilitar_clasificacion,
            habilitar_rag=habilitar_rag,
            habilitar_ner=habilitar_ner
        )

    return _ia_integration_instance


def reset_ia_integration_service():
    """
    Resetea el singleton para permitir reconfiguración.

    Útil cuando se necesita cambiar la configuración del servicio
    después de la inicialización inicial.
    """
    global _ia_integration_instance
    _ia_integration_instance = None
    logger.info("IAIntegrationService singleton reseteado")
