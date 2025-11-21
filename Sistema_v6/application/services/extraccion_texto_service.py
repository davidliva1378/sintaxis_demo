"""
Servicio para gestionar la extracción y almacenamiento estructurado de texto de PDFs.

Convierte el TextoExtraido del procesador_pdf a formato JSON optimizado para IA/RAG.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any, List

from Sistema_v5.procesador_pdf.models import TextoExtraido, ResultadoProcesamiento
from Sistema_v5.procesador_pdf.extractor_texto import ExtractorTexto
from Sistema_v5.procesador_pdf.limpiador_texto import LimpiadorTexto

logger = logging.getLogger(__name__)


@dataclass
class TextoEstructurado:
    """
    Estructura de texto extraído optimizada para almacenamiento y uso con IA.
    """
    texto_completo: str
    texto_normalizado: str
    texto_por_pagina: List[Dict[str, Any]]
    metadata: Dict[str, Any]
    preview: str

    def to_json(self) -> str:
        """Serializa a JSON string."""
        return json.dumps(self.to_dict(), ensure_ascii=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario."""
        return {
            "texto_completo": self.texto_completo,
            "texto_normalizado": self.texto_normalizado,
            "texto_por_pagina": self.texto_por_pagina,
            "metadata": self.metadata,
            "preview": self.preview
        }


class ExtraccionTextoService:
    """
    Servicio para extraer y estructurar texto de PDFs.

    Funciones principales:
    - Extraer texto de PDFs con múltiples métodos
    - Estructurar el texto para almacenamiento JSON
    - Generar metadata para búsquedas y análisis IA
    """

    def __init__(self, usar_ocr: bool = True):
        """
        Inicializa el servicio.

        Args:
            usar_ocr: Si usar OCR como fallback cuando no hay texto embebido
        """
        self.extractor = ExtractorTexto(usar_ocr=usar_ocr)
        self.limpiador = LimpiadorTexto()
        self._preview_length = 500

    def extraer_y_estructurar(self, ruta_pdf: str) -> Optional[TextoEstructurado]:
        """
        Extrae texto de un PDF y lo estructura para almacenamiento.

        Args:
            ruta_pdf: Ruta al archivo PDF

        Returns:
            TextoEstructurado con el texto procesado, o None si hay error
        """
        try:
            # Extraer texto usando el extractor existente
            texto_extraido = self.extractor.extraer(ruta_pdf)

            if texto_extraido.esta_vacio:
                logger.warning(f"PDF vacío o sin texto extraíble: {ruta_pdf}")
                return None

            # Convertir a estructura optimizada
            return self._convertir_a_estructurado(texto_extraido, ruta_pdf)

        except Exception as e:
            logger.error(f"Error extrayendo texto de {ruta_pdf}: {e}")
            return None

    def convertir_resultado(
        self,
        resultado: ResultadoProcesamiento,
        tipo_documento: str = "DEFAULT"
    ) -> Optional[TextoEstructurado]:
        """
        Convierte un ResultadoProcesamiento existente a TextoEstructurado.

        Args:
            resultado: Resultado del procesamiento de actuación
            tipo_documento: Tipo de documento para aplicar reglas de limpieza específicas
                          (SENTENCIA, CEDULA, RESOLUCION, etc.)

        Returns:
            TextoEstructurado o None si no hay texto
        """
        if not resultado.texto:
            return None

        return self._convertir_texto_extraido(resultado.texto, tipo_documento)

    def _convertir_texto_extraido(
        self,
        texto_extraido: TextoExtraido,
        tipo_documento: str = "DEFAULT"
    ) -> TextoEstructurado:
        """
        Convierte un TextoExtraido a TextoEstructurado.

        Args:
            texto_extraido: Objeto TextoExtraido del procesador
            tipo_documento: Tipo de documento para aplicar reglas de limpieza

        Returns:
            TextoEstructurado con formato optimizado
        """
        # Aplicar limpieza específica por tipo de documento
        texto_limpio = self.limpiador.limpiar(
            texto_extraido.texto_normalizado,
            tipo_documento
        )

        # También limpiar el texto completo para consistencia
        texto_completo_limpio = self.limpiador.limpiar(
            texto_extraido.texto_completo,
            tipo_documento
        )

        # Generar texto por página (simplificado - una sola página si no hay info)
        texto_por_pagina = self._generar_texto_por_pagina(
            texto_completo_limpio,
            texto_extraido.num_paginas,
            texto_extraido.metodo_extraccion
        )

        # Generar metadata
        metadata = {
            "metodo_extraccion": texto_extraido.metodo_extraccion,
            "total_paginas": texto_extraido.num_paginas,
            "total_caracteres": len(texto_limpio),
            "total_palabras": len(texto_limpio.split()),
            "tiene_texto_embebido": texto_extraido.tiene_texto_embebido,
            "tiene_tablas": self._detectar_tablas(texto_completo_limpio),
            "tiene_imagenes": texto_extraido.metodo_extraccion in ['ocr', 'mixto'],
            "requirio_ocr": texto_extraido.metodo_extraccion in ['ocr', 'mixto'],
            "confianza_ocr": 0.8 if texto_extraido.metodo_extraccion == 'ocr' else 1.0,
            "hash_contenido": texto_extraido.hash_contenido,
            "esta_vacio": texto_extraido.esta_vacio,
            "es_muy_corto": texto_extraido.es_muy_corto,
            "fecha_extraccion": texto_extraido.timestamp.isoformat(),
            "tipo_documento": tipo_documento,
            "reglas_limpieza_aplicadas": self.limpiador.obtener_descripcion_tipo(tipo_documento)
        }

        # Generar preview del texto limpio
        preview = self._generar_preview(texto_limpio)

        return TextoEstructurado(
            texto_completo=texto_completo_limpio,
            texto_normalizado=texto_limpio,
            texto_por_pagina=texto_por_pagina,
            metadata=metadata,
            preview=preview
        )

    def _convertir_a_estructurado(
        self,
        texto_extraido: TextoExtraido,
        ruta_pdf: str,
        tipo_documento: str = "DEFAULT"
    ) -> TextoEstructurado:
        """
        Convierte TextoExtraido a TextoEstructurado con información adicional.
        """
        estructurado = self._convertir_texto_extraido(texto_extraido, tipo_documento)

        # Agregar ruta del archivo a metadata
        estructurado.metadata["ruta_archivo"] = ruta_pdf

        return estructurado

    def _generar_texto_por_pagina(
        self,
        texto_completo: str,
        num_paginas: int,
        metodo: str
    ) -> List[Dict[str, Any]]:
        """
        Genera lista de texto por página.

        Por ahora divide el texto proporcionalmente si hay múltiples páginas.
        En el futuro se puede mejorar con extracción real por página.
        """
        if num_paginas <= 1:
            return [{
                "pagina": 1,
                "contenido": texto_completo,
                "tipo": self._determinar_tipo_contenido(texto_completo, metodo),
                "caracteres": len(texto_completo)
            }]

        # Dividir texto proporcionalmente entre páginas
        texto_por_pagina = []
        chars_por_pagina = len(texto_completo) // num_paginas

        for i in range(num_paginas):
            inicio = i * chars_por_pagina
            if i == num_paginas - 1:
                # Última página toma el resto
                contenido = texto_completo[inicio:]
            else:
                contenido = texto_completo[inicio:inicio + chars_por_pagina]

            texto_por_pagina.append({
                "pagina": i + 1,
                "contenido": contenido,
                "tipo": self._determinar_tipo_contenido(contenido, metodo),
                "caracteres": len(contenido)
            })

        return texto_por_pagina

    def _determinar_tipo_contenido(self, texto: str, metodo: str) -> str:
        """
        Determina el tipo de contenido de una página.

        Returns:
            'texto', 'imagen', 'mixto', o 'tabla'
        """
        if self._detectar_tablas(texto):
            return "tabla"
        elif metodo == 'ocr':
            return "imagen"
        elif metodo == 'mixto':
            return "mixto"
        else:
            return "texto"

    def _detectar_tablas(self, texto: str) -> bool:
        """
        Detecta si el texto contiene tablas.

        Heurística simple basada en patrones comunes en tablas.
        """
        # Patrones que sugieren tablas
        indicadores = [
            # Múltiples espacios o tabs alineados
            '   ' in texto and texto.count('   ') > 5,
            # Caracteres de tabla
            '|' in texto and texto.count('|') > 3,
            # Líneas horizontales
            '---' in texto or '___' in texto,
            # Patrones numéricos alineados (ej: liquidaciones)
            any(patron in texto.lower() for patron in [
                'total:', 'subtotal:', 'capital:', 'intereses:',
                'honorarios:', 'iva:', 'tasa:'
            ])
        ]

        return any(indicadores)

    def _generar_preview(self, texto: str) -> str:
        """
        Genera preview del texto para visualización rápida.

        Args:
            texto: Texto normalizado

        Returns:
            Primeros N caracteres con elipsis si se trunca
        """
        texto_limpio = ' '.join(texto.split())  # Normalizar espacios

        if len(texto_limpio) <= self._preview_length:
            return texto_limpio

        # Truncar en palabra completa
        truncado = texto_limpio[:self._preview_length]
        ultimo_espacio = truncado.rfind(' ')

        if ultimo_espacio > self._preview_length * 0.8:
            truncado = truncado[:ultimo_espacio]

        return truncado + '...'

    @staticmethod
    def generar_json_para_db(texto_estructurado: TextoEstructurado) -> str:
        """
        Genera JSON listo para almacenar en la base de datos.

        Args:
            texto_estructurado: Objeto TextoEstructurado

        Returns:
            String JSON para la columna texto_json
        """
        return texto_estructurado.to_json()

    @staticmethod
    def cargar_desde_json(json_str: str) -> Optional[TextoEstructurado]:
        """
        Carga un TextoEstructurado desde JSON almacenado.

        Args:
            json_str: JSON string de la base de datos

        Returns:
            TextoEstructurado o None si hay error
        """
        try:
            data = json.loads(json_str)
            return TextoEstructurado(
                texto_completo=data.get('texto_completo', ''),
                texto_normalizado=data.get('texto_normalizado', ''),
                texto_por_pagina=data.get('texto_por_pagina', []),
                metadata=data.get('metadata', {}),
                preview=data.get('preview', '')
            )
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error cargando JSON de texto: {e}")
            return None

    def preparar_para_ia(self, texto_estructurado: TextoEstructurado) -> Dict[str, Any]:
        """
        Prepara el texto para uso con IA/LLM.

        Retorna estructura optimizada para prompts de IA.

        Args:
            texto_estructurado: Texto extraído

        Returns:
            Dict con texto formateado para IA
        """
        return {
            "contenido": texto_estructurado.texto_normalizado,
            "resumen_metadata": {
                "paginas": texto_estructurado.metadata.get('total_paginas', 1),
                "palabras": texto_estructurado.metadata.get('total_palabras', 0),
                "tiene_tablas": texto_estructurado.metadata.get('tiene_tablas', False),
                "metodo": texto_estructurado.metadata.get('metodo_extraccion', 'desconocido')
            },
            "preview": texto_estructurado.preview,
            "chunks": self._generar_chunks_para_rag(texto_estructurado)
        }

    def _generar_chunks_para_rag(
        self,
        texto_estructurado: TextoEstructurado,
        chunk_size: int = 1000,
        overlap: int = 200
    ) -> List[Dict[str, Any]]:
        """
        Genera chunks de texto para sistemas RAG.

        Args:
            texto_estructurado: Texto a dividir
            chunk_size: Tamaño de cada chunk en caracteres
            overlap: Solapamiento entre chunks

        Returns:
            Lista de chunks con metadata
        """
        texto = texto_estructurado.texto_normalizado
        chunks = []

        if len(texto) <= chunk_size:
            return [{
                "id": 0,
                "contenido": texto,
                "inicio": 0,
                "fin": len(texto)
            }]

        inicio = 0
        chunk_id = 0

        while inicio < len(texto):
            fin = min(inicio + chunk_size, len(texto))

            # Ajustar fin para no cortar palabras
            if fin < len(texto):
                ultimo_espacio = texto.rfind(' ', inicio, fin)
                if ultimo_espacio > inicio + chunk_size * 0.8:
                    fin = ultimo_espacio

            chunks.append({
                "id": chunk_id,
                "contenido": texto[inicio:fin],
                "inicio": inicio,
                "fin": fin
            })

            # Siguiente chunk con overlap
            inicio = fin - overlap if fin < len(texto) else len(texto)
            chunk_id += 1

        return chunks
