"""
Detector de duplicados en actuaciones judiciales.

Detecta duplicados exactos (por hash) y prepara la infraestructura
para detección semántica (SimHash/MinHash) en versiones futuras.
"""

import hashlib
import re
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
from .models import DuplicadoDetectado, TipoDuplicado


class DetectorDuplicados:
    """
    Detector de actuaciones duplicadas.

    Versión 1: Duplicados exactos por hash de contenido normalizado.
    Versión 2 (futura): Duplicados semánticos con SimHash/MinHash.
    """

    def __init__(self):
        """Inicializa el detector."""
        self._cache_hashes: Dict[str, int] = {}  # hash -> actuacion_id
        self._patrones_normalizacion = self._compilar_patrones()

    def _compilar_patrones(self) -> List[Tuple[re.Pattern, str]]:
        """
        Compila patrones para normalización de texto.

        Returns:
            Lista de tuplas (patrón compilado, reemplazo)
        """
        return [
            # Fechas y horas
            (re.compile(r"\d{1,2}[/-]\d{1,2}[/-]\d{2,4}"), ""),
            (re.compile(r"\d{1,2}:\d{2}(:\d{2})?"), ""),

            # Números de folio, cargo, hash
            (re.compile(r"folio\s+n?[°º]?\s*\d+", re.IGNORECASE), ""),
            (re.compile(r"cargo\s+n?[°º]?\s*\d+", re.IGNORECASE), ""),
            (re.compile(r"hash\s*:?\s*[a-f0-9]{6,}", re.IGNORECASE), ""),

            # Nombres y DNI (básico, puede mejorarse)
            (re.compile(r"DNI\s+N?[°º]?\s*\d{7,8}", re.IGNORECASE), "DNI_XXX"),
            (re.compile(r"CUIT\s+N?[°º]?\s*\d{2}-\d{8}-\d", re.IGNORECASE), "CUIT_XXX"),

            # Domicilios electrónicos
            (re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"), "EMAIL"),

            # Múltiples espacios en blanco
            (re.compile(r"\s+"), " "),
        ]

    def normalizar_para_comparacion(self, texto: str) -> str:
        """
        Normaliza texto para comparación de duplicados.

        Elimina elementos variables (fechas, horas, nombres, folios)
        conservando el contenido sustancial.

        Args:
            texto: Texto a normalizar

        Returns:
            Texto normalizado
        """
        if not texto:
            return ""

        texto_norm = texto.strip().lower()

        # Aplicar patrones de normalización
        for patron, reemplazo in self._patrones_normalizacion:
            texto_norm = patron.sub(reemplazo, texto_norm)

        return texto_norm.strip()

    def calcular_hash_normalizado(self, texto: str) -> str:
        """
        Calcula hash MD5 del texto normalizado.

        Args:
            texto: Texto a hashear

        Returns:
            Hash MD5 hexadecimal
        """
        texto_norm = self.normalizar_para_comparacion(texto)
        return hashlib.md5(texto_norm.encode('utf-8')).hexdigest()

    def detectar_duplicados_exactos(
        self,
        actuaciones: List[Dict[str, any]],
        campo_texto: str = "Detalle"
    ) -> List[DuplicadoDetectado]:
        """
        Detecta duplicados exactos en un lote de actuaciones.

        Args:
            actuaciones: Lista de actuaciones (dicts)
            campo_texto: Nombre del campo a comparar

        Returns:
            Lista de DuplicadoDetectado
        """
        duplicados = []
        hash_a_ids: Dict[str, List[int]] = defaultdict(list)

        # Calcular hashes y agrupar
        for act in actuaciones:
            act_id = act.get("id") or act.get("Indice")
            texto = act.get(campo_texto, "")

            if not texto or len(texto.strip()) < 10:
                continue

            hash_norm = self.calcular_hash_normalizado(texto)
            hash_a_ids[hash_norm].append(act_id)

        # Identificar duplicados
        for hash_norm, ids in hash_a_ids.items():
            if len(ids) > 1:
                # El primero es el "original", los demás son duplicados
                id_original = ids[0]
                for id_duplicado in ids[1:]:
                    duplicados.append(
                        DuplicadoDetectado(
                            actuacion_id_original=id_original,
                            actuacion_id_duplicada=id_duplicado,
                            tipo=TipoDuplicado.EXACTO,
                            similitud=1.0,
                            hash_normalizado=hash_norm,
                            motivo="Contenido normalizado idéntico"
                        )
                    )

        return duplicados

    def detectar_cedulas_duplicadas(
        self,
        actuaciones: List[Dict[str, any]]
    ) -> List[DuplicadoDetectado]:
        """
        Detecta cédulas de notificación duplicadas.

        Caso especial: múltiples cédulas del mismo acto para distintos actores.

        Args:
            actuaciones: Lista de actuaciones

        Returns:
            Lista de DuplicadoDetectado
        """
        duplicados = []

        # Filtrar solo cédulas
        cedulas = [
            act for act in actuaciones
            if self._es_cedula(act.get("Tipo", ""))
        ]

        if len(cedulas) < 2:
            return duplicados

        # Agrupar por contenido normalizado (sin destinatario)
        contenido_a_ids: Dict[str, List[int]] = defaultdict(list)

        for cedula in cedulas:
            ced_id = cedula.get("id") or cedula.get("Indice")
            detalle = cedula.get("Detalle", "")

            # Normalizar eliminando nombres propios (simplificado)
            texto_norm = self._normalizar_cedula(detalle)
            hash_norm = self.calcular_hash_normalizado(texto_norm)

            contenido_a_ids[hash_norm].append(ced_id)

        # Identificar duplicados
        for hash_norm, ids in contenido_a_ids.items():
            if len(ids) > 1:
                id_original = ids[0]
                for id_duplicado in ids[1:]:
                    duplicados.append(
                        DuplicadoDetectado(
                            actuacion_id_original=id_original,
                            actuacion_id_duplicada=id_duplicado,
                            tipo=TipoDuplicado.EXACTO,
                            similitud=1.0,
                            hash_normalizado=hash_norm,
                            motivo="Cédula duplicada (probablemente para distinto destinatario)"
                        )
                    )

        return duplicados

    def _es_cedula(self, tipo: str) -> bool:
        """Verifica si el tipo corresponde a una cédula."""
        tipo_upper = tipo.upper()
        keywords = ["CEDULA", "NOTIF", "NOTIFICACION"]
        return any(kw in tipo_upper for kw in keywords)

    def _normalizar_cedula(self, texto: str) -> str:
        """
        Normalización especial para cédulas.

        Elimina nombres propios y datos específicos del destinatario.
        """
        texto_norm = self.normalizar_para_comparacion(texto)

        # Eliminar patrones típicos de destinatarios
        patrones_destinatario = [
            r"a\s+[A-Z][a-záéíóúñ]+\s+[A-Z][a-záéíóúñ]+",  # A Fulano Mengano
            r"notif[ií]quese\s+a\s+\w+",
            r"domicilio.*constituido",
            r"domicilio.*electr[oó]nico",
        ]

        for patron in patrones_destinatario:
            texto_norm = re.sub(patron, "", texto_norm, flags=re.IGNORECASE)

        return texto_norm.strip()

    def agrupar_por_similitud_alta(
        self,
        actuaciones: List[Dict[str, any]],
        umbral_longitud: float = 0.85
    ) -> List[List[int]]:
        """
        Agrupa actuaciones con longitud de texto similar.

        Candidatos para análisis semántico posterior.

        Args:
            actuaciones: Lista de actuaciones
            umbral_longitud: Umbral de similitud de longitud (0.0-1.0)

        Returns:
            Lista de grupos (cada grupo es lista de IDs)
        """
        # Agrupar por longitud similar
        grupos: Dict[int, List[int]] = defaultdict(list)

        for act in actuaciones:
            act_id = act.get("id") or act.get("Indice")
            texto = act.get("Detalle", "")
            longitud = len(texto)

            # Usar longitud redondeada como clave de grupo
            bucket = round(longitud / 50) * 50  # Agrupar cada 50 caracteres
            grupos[bucket].append((act_id, longitud))

        # Filtrar grupos con más de 1 elemento
        grupos_filtrados = []
        for grupo_items in grupos.values():
            if len(grupo_items) < 2:
                continue

            # Subgrupar por similitud exacta de longitud
            subgrupos: Dict[int, List[int]] = defaultdict(list)
            for act_id, longitud in grupo_items:
                subgrupos[longitud].append(act_id)

            for ids in subgrupos.values():
                if len(ids) > 1:
                    grupos_filtrados.append(ids)

        return grupos_filtrados

    def estadisticas_duplicados(
        self,
        duplicados: List[DuplicadoDetectado]
    ) -> Dict[str, any]:
        """
        Genera estadísticas sobre duplicados detectados.

        Args:
            duplicados: Lista de duplicados

        Returns:
            Dict con estadísticas
        """
        if not duplicados:
            return {
                "total_duplicados": 0,
                "por_tipo": {},
                "ids_unicos_afectados": 0
            }

        # Contar por tipo
        por_tipo = defaultdict(int)
        ids_afectados: Set[int] = set()

        for dup in duplicados:
            por_tipo[dup.tipo.value] += 1
            ids_afectados.add(dup.actuacion_id_original)
            ids_afectados.add(dup.actuacion_id_duplicada)

        return {
            "total_duplicados": len(duplicados),
            "por_tipo": dict(por_tipo),
            "ids_unicos_afectados": len(ids_afectados),
            "similitud_promedio": sum(d.similitud for d in duplicados) / len(duplicados)
        }

    # === MÉTODOS PARA FUTURA IMPLEMENTACIÓN (SimHash/MinHash) ===

    def calcular_simhash(self, texto: str, bits: int = 64) -> int:
        """
        PLACEHOLDER: Calcula SimHash del texto.

        Args:
            texto: Texto a analizar
            bits: Cantidad de bits del hash

        Returns:
            SimHash como entero

        Note:
            Requiere implementación con librería simhash
        """
        raise NotImplementedError(
            "SimHash no implementado en v1. "
            "Instalar: pip install simhash"
        )

    def hamming_distance(self, hash1: int, hash2: int) -> int:
        """
        PLACEHOLDER: Calcula distancia de Hamming entre dos hashes.

        Args:
            hash1: Primer hash
            hash2: Segundo hash

        Returns:
            Cantidad de bits diferentes
        """
        raise NotImplementedError("Hamming distance no implementado en v1")

    def detectar_duplicados_semanticos(
        self,
        actuaciones: List[Dict[str, any]],
        umbral_hamming: int = 3
    ) -> List[DuplicadoDetectado]:
        """
        PLACEHOLDER: Detecta duplicados semánticos con SimHash.

        Args:
            actuaciones: Lista de actuaciones
            umbral_hamming: Máxima distancia de Hamming para considerar duplicado

        Returns:
            Lista de duplicados semánticos

        Note:
            Implementación futura (Fase 2)
        """
        raise NotImplementedError(
            "Detección semántica no implementada en v1 (Fase 2). "
            "Requiere SimHash o MinHash + LSH"
        )
