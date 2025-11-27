"""
Entity Normalizer Service - Normalización Inteligente de Entidades (TAREA 2.3)

Funcionalidades:
- Estandariza formatos de fechas (DD/MM/YYYY)
- Normaliza nombres (mayúsculas, sin tildes para matching)
- Unifica montos a formato numérico estándar
- Normaliza referencias a normas legales
- Cache de normalizaciones frecuentes
"""

import re
import logging
import hashlib
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class NormalizedEntity:
    """Entidad normalizada"""
    original: str
    normalized: str
    label: str
    score: float
    normalization_type: Optional[str] = None  # fecha, monto, nombre, norma


class EntityNormalizer:
    """
    Servicio para normalización inteligente de entidades jurídicas.

    Estandariza formatos de:
    - Fechas: DD/MM/YYYY
    - Nombres: APELLIDO, Nombre
    - Montos: $X.XXX,XX
    - Normas: Ley N° XXXXX, Art. X
    """

    def __init__(self, llm_service=None):
        """
        Args:
            llm_service: Servicio LLM para normalizaciones complejas (opcional)
        """
        self._llm = llm_service
        self._cache: Dict[str, NormalizedEntity] = {}

        # Patrones de fechas (orden importa: ISO primero para evitar conflictos)
        self.DATE_PATTERNS = [
            # YYYY-MM-DD (ISO) - debe ir primero para no confundir con DMY
            (r'^(\d{4})-(\d{2})-(\d{2})$', self._normalize_date_iso),
            # DD/MM/YYYY o DD-MM-YYYY
            (r'(\d{1,2})[/\-](\d{1,2})[/\-](\d{2,4})', self._normalize_date_dmy),
            # "X de mes de YYYY"
            (r'(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})', self._normalize_date_spanish),
        ]

        # Meses en español
        self.MESES = {
            'enero': '01', 'febrero': '02', 'marzo': '03', 'abril': '04',
            'mayo': '05', 'junio': '06', 'julio': '07', 'agosto': '08',
            'septiembre': '09', 'octubre': '10', 'noviembre': '11', 'diciembre': '12'
        }

        # Patrones de montos
        self.MONTO_PATTERNS = [
            # $1.234,56 o $ 1.234,56
            r'\$\s*([\d.]+),(\d{2})',
            # 1234.56 (formato americano)
            r'([\d,]+)\.(\d{2})\s*(?:pesos|ARS|\$)',
            # "pesos X" o "$ X"
            r'(?:pesos|ARS|\$)\s*([\d.,]+)',
        ]

        logger.info("EntityNormalizer inicializado")

    @property
    def llm(self):
        """Lazy loading del LLM service"""
        if self._llm is None:
            try:
                from infrastructure.rag.services.llm_service import LLMService
                self._llm = LLMService()
            except Exception as e:
                logger.warning(f"LLM no disponible para normalización: {e}")
        return self._llm

    def normalize(
        self,
        entities: List[Dict[str, Any]],
        use_cache: bool = True
    ) -> List[NormalizedEntity]:
        """
        Normaliza una lista de entidades.

        Args:
            entities: Lista de entidades [{"text": "...", "label": "...", "score": ...}]
            use_cache: Si usar cache

        Returns:
            Lista de NormalizedEntity
        """
        results = []

        for entity in entities:
            text = entity.get("text", "")
            label = entity.get("label", "UNKNOWN")
            score = entity.get("score", 1.0)

            # Verificar cache
            cache_key = self._get_cache_key(text, label)
            if use_cache and cache_key in self._cache:
                results.append(self._cache[cache_key])
                continue

            # Normalizar según tipo
            normalized = self._normalize_by_type(text, label)

            result = NormalizedEntity(
                original=text,
                normalized=normalized["text"],
                label=label,
                score=score,
                normalization_type=normalized.get("type")
            )

            # Guardar en cache
            if use_cache:
                self._cache[cache_key] = result

            results.append(result)

        return results

    def _normalize_by_type(self, text: str, label: str) -> Dict[str, str]:
        """Normaliza según el tipo de entidad"""

        # Fechas
        if label in ("FECHA", "PLAZO", "VENCIMIENTO"):
            return {"text": self._normalize_fecha(text), "type": "fecha"}

        # Montos
        if label in ("MONTO", "DINERO", "HONORARIOS", "CAPITAL"):
            return {"text": self._normalize_monto(text), "type": "monto"}

        # Nombres de personas
        if label in ("PERSONA", "JUEZ", "ABOGADO", "ACTOR", "DEMANDADO", "PERITO", "TESTIGO"):
            return {"text": self._normalize_nombre(text), "type": "nombre"}

        # Normas legales
        if label in ("NORMA", "LEY", "ARTICULO", "DECRETO"):
            return {"text": self._normalize_norma(text), "type": "norma"}

        # Tribunales
        if label == "TRIBUNAL":
            return {"text": self._normalize_tribunal(text), "type": "tribunal"}

        # Default: limpieza básica
        return {"text": self._clean_text(text), "type": None}

    def _normalize_fecha(self, text: str) -> str:
        """Normaliza fecha a formato DD/MM/YYYY"""
        text = text.strip()

        for pattern, normalizer in self.DATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    return normalizer(match)
                except Exception:
                    continue

        # Si no matchea ningún patrón, retornar limpio
        return self._clean_text(text)

    def _normalize_date_dmy(self, match) -> str:
        """Normaliza DD/MM/YYYY"""
        day, month, year = match.groups()
        day = day.zfill(2)
        month = month.zfill(2)
        year = year if len(year) == 4 else f"20{year}" if int(year) < 50 else f"19{year}"
        return f"{day}/{month}/{year}"

    def _normalize_date_spanish(self, match) -> str:
        """Normaliza 'X de mes de YYYY'"""
        day, month_name, year = match.groups()
        day = day.zfill(2)
        month = self.MESES.get(month_name.lower(), "00")
        return f"{day}/{month}/{year}"

    def _normalize_date_iso(self, match) -> str:
        """Normaliza YYYY-MM-DD a DD/MM/YYYY"""
        year, month, day = match.groups()
        return f"{day.zfill(2)}/{month.zfill(2)}/{year}"

    def _normalize_monto(self, text: str) -> str:
        """Normaliza monto a formato $X.XXX,XX"""
        text = text.strip()

        # Extraer números
        numbers = re.findall(r'[\d.,]+', text)
        if not numbers:
            return text

        # Tomar el número más largo (probablemente el monto)
        num_str = max(numbers, key=len)

        # Determinar formato (argentino: 1.234,56 vs americano: 1,234.56)
        if ',' in num_str and '.' in num_str:
            # Determinar cuál es decimal
            last_sep = max(num_str.rfind(','), num_str.rfind('.'))
            if num_str[last_sep] == ',':
                # Formato argentino
                num_str = num_str.replace('.', '').replace(',', '.')
            else:
                # Formato americano
                num_str = num_str.replace(',', '')
        elif ',' in num_str:
            # Solo coma - podría ser decimal o miles
            if num_str.count(',') == 1 and len(num_str.split(',')[1]) == 2:
                # Es decimal
                num_str = num_str.replace(',', '.')
            else:
                # Son miles
                num_str = num_str.replace(',', '')

        try:
            valor = float(num_str)
            # Formatear como argentino
            formatted = f"${valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            return formatted
        except ValueError:
            return text

    def _normalize_nombre(self, text: str) -> str:
        """Normaliza nombre a formato APELLIDO, Nombre"""
        text = self._clean_text(text)

        # Detectar si ya está en formato correcto
        if ',' in text:
            return text.upper()

        # Intentar separar apellido de nombre
        parts = text.split()
        if len(parts) >= 2:
            # Heurística: apellidos suelen estar primero en documentos legales
            # y pueden ser compuestos (de, del, etc.)
            apellido_parts = []
            nombre_parts = []
            in_nombre = False

            for i, part in enumerate(parts):
                if part.lower() in ('de', 'del', 'la', 'los', 'las', 'y'):
                    if in_nombre:
                        nombre_parts.append(part)
                    else:
                        apellido_parts.append(part)
                elif i == 0:
                    apellido_parts.append(part)
                elif part[0].isupper() and not in_nombre:
                    # Segundo nombre en mayúscula podría ser apellido compuesto
                    if i == 1 and len(parts) > 2:
                        apellido_parts.append(part)
                    else:
                        in_nombre = True
                        nombre_parts.append(part)
                else:
                    in_nombre = True
                    nombre_parts.append(part)

            if apellido_parts and nombre_parts:
                apellido = " ".join(apellido_parts).upper()
                nombre = " ".join(nombre_parts).title()
                return f"{apellido}, {nombre}"

        return text.upper()

    def _normalize_norma(self, text: str) -> str:
        """Normaliza referencia a norma legal"""
        text = self._clean_text(text)

        # Patrones comunes
        patterns = [
            # Ley N° XXXXX
            (r'ley\s*n[°º]?\s*(\d+)', r'Ley N° \1'),
            # Art. X / Artículo X
            (r'art[íi]culo\s*(\d+)', r'Art. \1'),
            (r'art\.?\s*(\d+)', r'Art. \1'),
            # Decreto N° XXXXX/YYYY
            (r'decreto\s*n[°º]?\s*(\d+)[/\-](\d+)', r'Dto. N° \1/\2'),
            # CCCN / Código Civil
            (r'c[óo]digo\s+civil\s+y\s+comercial', 'CCCN'),
            (r'c\.?c\.?c\.?n\.?', 'CCCN'),
        ]

        result = text
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def _normalize_tribunal(self, text: str) -> str:
        """Normaliza nombre de tribunal"""
        text = self._clean_text(text)

        # Abreviaturas estándar
        replacements = {
            r'juzgado\s+federal': 'Jdo. Fed.',
            r'juzgado\s+civil': 'Jdo. Civ.',
            r'juzgado\s+penal': 'Jdo. Pen.',
            r'c[aá]mara\s+federal': 'Cám. Fed.',
            r'c[aá]mara\s+civil': 'Cám. Civ.',
            r'corte\s+suprema': 'CSJN',
        }

        result = text
        for pattern, replacement in replacements.items():
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        return result

    def _clean_text(self, text: str) -> str:
        """Limpieza básica de texto"""
        # Remover espacios múltiples
        text = re.sub(r'\s+', ' ', text)
        # Remover espacios al inicio/fin
        text = text.strip()
        return text

    def _get_cache_key(self, text: str, label: str) -> str:
        """Genera clave de cache"""
        combined = f"{text.lower()}:{label}"
        return hashlib.md5(combined.encode()).hexdigest()

    def normalize_with_llm(
        self,
        entity: Dict[str, Any],
        context: str = ""
    ) -> NormalizedEntity:
        """
        Normaliza una entidad usando LLM para casos complejos.

        Args:
            entity: Entidad a normalizar
            context: Contexto adicional

        Returns:
            NormalizedEntity
        """
        if not self.llm:
            # Fallback a normalización básica
            return self.normalize([entity])[0]

        text = entity.get("text", "")
        label = entity.get("label", "")

        prompt = f"""Normaliza esta entidad jurídica argentina:

Tipo: {label}
Texto original: "{text}"
Contexto: {context[:500] if context else "N/A"}

INSTRUCCIONES según tipo:
- FECHA: Formato DD/MM/YYYY
- MONTO: Formato $X.XXX,XX (pesos argentinos)
- PERSONA/JUEZ/ABOGADO: APELLIDO, Nombre
- NORMA/LEY: Ley N° XXXXX o Art. X
- TRIBUNAL: Abreviatura estándar

Responde SOLO con el texto normalizado, sin explicaciones."""

        try:
            normalized_text = self.llm.generate(prompt, temperature=0.1, max_tokens=100)
            normalized_text = normalized_text.strip().strip('"').strip("'")

            return NormalizedEntity(
                original=text,
                normalized=normalized_text,
                label=label,
                score=entity.get("score", 1.0),
                normalization_type="llm"
            )
        except Exception as e:
            logger.warning(f"Error en normalización LLM: {e}")
            return self.normalize([entity])[0]

    def to_dict_list(self, entities: List[NormalizedEntity]) -> List[Dict[str, Any]]:
        """Convierte lista de NormalizedEntity a lista de dicts"""
        return [
            {
                "original": e.original,
                "normalized": e.normalized,
                "label": e.label,
                "score": e.score,
                "normalization_type": e.normalization_type
            }
            for e in entities
        ]

    def clear_cache(self):
        """Limpia el cache"""
        self._cache = {}
        logger.info("Cache de normalización limpiado")
