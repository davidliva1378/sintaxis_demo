"""
Extractor de texto de PDFs de actuaciones judiciales.

Extrae texto embebido o usa OCR cuando es necesario.
Normaliza y limpia el texto para análisis posterior.
"""

import hashlib
import re
from pathlib import Path
from typing import Optional, Tuple
from .models import TextoExtraido


class ExtractorTexto:
    """
    Extractor y normalizador de texto de PDFs.

    Intenta primero extraer texto embebido, si falla o está vacío
    recurre a OCR (requiere pytesseract instalado).
    """

    def __init__(self, usar_ocr: bool = True, idioma_ocr: str = "spa"):
        """
        Inicializa el extractor.

        Args:
            usar_ocr: Si usar OCR cuando no hay texto embebido
            idioma_ocr: Idioma para OCR (default: español)
        """
        self.usar_ocr = usar_ocr
        self.idioma_ocr = idioma_ocr
        self._pypdf2 = None
        self._pdfplumber = None
        self._pytesseract = None
        self._pdf2image = None

    def _lazy_import_pypdf2(self):
        """Importa PyPDF2 solo cuando se necesita."""
        if self._pypdf2 is None:
            try:
                import PyPDF2
                self._pypdf2 = PyPDF2
            except ImportError:
                raise ImportError(
                    "PyPDF2 no está instalado. "
                    "Instalar con: pip install PyPDF2"
                )
        return self._pypdf2

    def _lazy_import_pdfplumber(self):
        """Importa pdfplumber solo cuando se necesita."""
        if self._pdfplumber is None:
            try:
                import pdfplumber
                self._pdfplumber = pdfplumber
            except ImportError:
                raise ImportError(
                    "pdfplumber no está instalado. "
                    "Instalar con: pip install pdfplumber"
                )
        return self._pdfplumber

    def _lazy_import_ocr(self):
        """Importa dependencias de OCR solo cuando se necesitan."""
        if self._pytesseract is None:
            try:
                import pytesseract
                from pdf2image import convert_from_path
                self._pytesseract = pytesseract
                self._pdf2image = convert_from_path
            except ImportError as e:
                raise ImportError(
                    f"Dependencias de OCR no instaladas: {e}\n"
                    "Instalar con: pip install pytesseract pdf2image"
                )
        return self._pytesseract, self._pdf2image

    def extraer(self, ruta_pdf: str) -> TextoExtraido:
        """
        Extrae texto de un PDF.

        Args:
            ruta_pdf: Ruta al archivo PDF

        Returns:
            TextoExtraido con texto y metadatos
        """
        ruta = Path(ruta_pdf)
        if not ruta.exists():
            raise FileNotFoundError(f"PDF no encontrado: {ruta_pdf}")

        # Intentar extracción con PyPDF2
        texto, num_paginas = self._extraer_con_pypdf2(ruta)
        tiene_texto_embebido = len(texto.strip()) > 50

        metodo = "embebido" if tiene_texto_embebido else "vacio"

        # Si no hay texto suficiente, intentar con pdfplumber (mejor para algunos PDFs)
        if not tiene_texto_embebido:
            texto_plumber, _ = self._extraer_con_pdfplumber(ruta)
            if len(texto_plumber.strip()) > len(texto.strip()):
                texto = texto_plumber
                tiene_texto_embebido = len(texto.strip()) > 50
                metodo = "embebido" if tiene_texto_embebido else "vacio"

        # Si aún no hay texto y OCR está habilitado, usar OCR
        if not tiene_texto_embebido and self.usar_ocr:
            try:
                texto_ocr = self._extraer_con_ocr(ruta)
                if len(texto_ocr.strip()) > 50:
                    texto = texto_ocr
                    metodo = "ocr"
            except Exception as e:
                # OCR falló, usar texto vacío/parcial
                metodo = f"ocr_fallido: {str(e)[:50]}"

        # Normalizar texto
        texto_normalizado = self.normalizar_texto(texto)

        # Calcular métricas
        longitud_caracteres = len(texto_normalizado)
        longitud_palabras = len(texto_normalizado.split())
        hash_contenido = hashlib.md5(texto_normalizado.encode('utf-8')).hexdigest()

        return TextoExtraido(
            texto_completo=texto,
            texto_normalizado=texto_normalizado,
            num_paginas=num_paginas,
            metodo_extraccion=metodo,
            tiene_texto_embebido=tiene_texto_embebido,
            longitud_caracteres=longitud_caracteres,
            longitud_palabras=longitud_palabras,
            hash_contenido=hash_contenido
        )

    def _extraer_con_pypdf2(self, ruta: Path) -> Tuple[str, int]:
        """
        Extrae texto con PyPDF2.

        Args:
            ruta: Path al PDF

        Returns:
            (texto, num_paginas)
        """
        PyPDF2 = self._lazy_import_pypdf2()

        texto_completo = []
        num_paginas = 0

        try:
            with open(ruta, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                num_paginas = len(reader.pages)

                for page in reader.pages:
                    texto = page.extract_text()
                    if texto:
                        texto_completo.append(texto)

        except Exception as e:
            # Falló PyPDF2, retornar vacío
            return "", 0

        return "\n".join(texto_completo), num_paginas

    def _extraer_con_pdfplumber(self, ruta: Path) -> Tuple[str, int]:
        """
        Extrae texto con pdfplumber (mejor para algunos PDFs).

        Args:
            ruta: Path al PDF

        Returns:
            (texto, num_paginas)
        """
        pdfplumber = self._lazy_import_pdfplumber()

        texto_completo = []
        num_paginas = 0

        try:
            with pdfplumber.open(ruta) as pdf:
                num_paginas = len(pdf.pages)

                for page in pdf.pages:
                    texto = page.extract_text()
                    if texto:
                        texto_completo.append(texto)

        except Exception as e:
            return "", 0

        return "\n".join(texto_completo), num_paginas

    def _extraer_con_ocr(self, ruta: Path) -> str:
        """
        Extrae texto usando OCR (Tesseract).

        Args:
            ruta: Path al PDF

        Returns:
            Texto extraído
        """
        pytesseract, convert_from_path = self._lazy_import_ocr()

        # Convertir PDF a imágenes
        imagenes = convert_from_path(str(ruta), dpi=300)

        texto_completo = []
        for imagen in imagenes:
            texto = pytesseract.image_to_string(
                imagen,
                lang=self.idioma_ocr
            )
            texto_completo.append(texto)

        return "\n".join(texto_completo)

    def normalizar_texto(self, texto: str) -> str:
        """
        Normaliza texto extraído.

        Elimina encabezados/pies repetidos, corrige espacios,
        unifica saltos de línea.

        Args:
            texto: Texto a normalizar

        Returns:
            Texto normalizado
        """
        if not texto:
            return ""

        # Eliminar caracteres de control excepto saltos de línea
        texto = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', texto)

        # Unificar saltos de línea
        texto = re.sub(r'\r\n', '\n', texto)
        texto = re.sub(r'\r', '\n', texto)

        # Limpiar códigos insertados dentro del texto (antes de dividir en líneas)
        texto = self._limpiar_codigos_insertados(texto)

        # Eliminar líneas muy cortas (probablemente encabezados/pies)
        lineas = texto.split('\n')
        lineas_filtradas = []

        for linea in lineas:
            linea_limpia = linea.strip()

            # Eliminar líneas muy cortas o solo números
            if len(linea_limpia) < 3:
                continue
            if linea_limpia.isdigit() and len(linea_limpia) < 4:
                continue

            # Eliminar códigos de barras y códigos numéricos largos
            if self._es_codigo_barras(linea_limpia):
                continue

            # Eliminar patrones de encabezado/pie típicos
            if self._es_encabezado_pie(linea_limpia):
                continue

            lineas_filtradas.append(linea_limpia)

        texto = '\n'.join(lineas_filtradas)

        # Corregir múltiples espacios
        texto = re.sub(r' +', ' ', texto)

        # Reducir múltiples saltos de línea a máximo 2
        texto = re.sub(r'\n{3,}', '\n\n', texto)

        return texto.strip()

    def _es_encabezado_pie(self, linea: str) -> bool:
        """
        Detecta si una línea es encabezado o pie de página.

        Args:
            linea: Línea a analizar

        Returns:
            True si es encabezado/pie
        """
        patrones_encabezado_pie = [
            r'^página\s+\d+\s+de\s+\d+$',
            r'^\d+\s*/\s*\d+$',
            r'^poder\s+judicial\s+de\s+la\s+nación',
            r'^expediente\s+n[°º]?\s*\d+',
            r'^hoja\s+n[°º]?\s*\d+',
            # Patrones adicionales
            r'^-\s*\d+\s*-$',  # Formato "- 1 -"
            r'^\[\s*\d+\s*\]$',  # Formato "[1]"
            r'^pag\.?\s*\d+$',
        ]

        linea_lower = linea.lower()

        for patron in patrones_encabezado_pie:
            if re.search(patron, linea_lower):
                return True

        return False

    def _es_codigo_barras(self, linea: str) -> bool:
        """
        Detecta si una línea es un código de barras u otro código numérico.

        Args:
            linea: Línea a analizar

        Returns:
            True si es código de barras/numérico
        """
        linea_limpia = linea.strip()

        # Códigos numéricos largos (códigos de barras del PJN)
        if re.match(r'^\d{10,20}$', linea_limpia):
            return True

        # Códigos alfanuméricos largos (hashes, firmas digitales)
        if re.match(r'^[A-Z0-9]{20,}$', linea_limpia):
            return True

        # Patrones de firma digital
        if re.match(r'^#\d+#\d+#\d+', linea_limpia):
            return True

        # Números separados por guiones (códigos de expediente mal formados)
        if re.match(r'^\d+[-/]\d+[-/]\d+[-/]\d+', linea_limpia):
            return True

        return False

    def _limpiar_codigos_insertados(self, texto: str) -> str:
        """
        Elimina códigos numéricos insertados dentro del texto.

        Los códigos de barras a veces se insertan en medio de palabras
        rompiéndolas: "pala25000096559010bra" -> "palabra"

        Args:
            texto: Texto a limpiar

        Returns:
            Texto sin códigos insertados
        """
        # Patrón: letras + números largos + letras (código insertado en palabra)
        texto = re.sub(r'([a-záéíóúñü]+)\d{10,}([a-záéíóúñü]+)', r'\1\2', texto, flags=re.IGNORECASE)

        # Eliminar códigos numéricos largos sueltos (no en medio de palabras)
        texto = re.sub(r'\s\d{10,20}\s', ' ', texto)

        # Eliminar hashes/códigos alfanuméricos largos
        texto = re.sub(r'\s[A-Z0-9]{20,}\s', ' ', texto)

        # Eliminar patrones de firma digital del PJN
        texto = re.sub(r'#\d+#\d+#\d+', '', texto)

        return texto

    def extraer_primeros_n_caracteres(
        self,
        ruta_pdf: str,
        n: int = 500
    ) -> str:
        """
        Extrae solo los primeros N caracteres del PDF.

        Útil para clasificación rápida sin procesar todo el documento.

        Args:
            ruta_pdf: Ruta al PDF
            n: Cantidad de caracteres a extraer

        Returns:
            Primeros N caracteres normalizados
        """
        PyPDF2 = self._lazy_import_pypdf2()

        texto_completo = []
        caracteres_acumulados = 0

        try:
            with open(ruta_pdf, 'rb') as f:
                reader = PyPDF2.PdfReader(f)

                for page in reader.pages:
                    texto = page.extract_text()
                    if texto:
                        texto_completo.append(texto)
                        caracteres_acumulados += len(texto)

                        if caracteres_acumulados >= n:
                            break

        except Exception:
            return ""

        texto = "\n".join(texto_completo)
        texto_normalizado = self.normalizar_texto(texto)

        return texto_normalizado[:n]

    def detectar_estructura_formal(self, texto: str) -> bool:
        """
        Detecta si el texto tiene estructura formal jurídica.

        Args:
            texto: Texto a analizar

        Returns:
            True si tiene estructura formal
        """
        patrones_formales = [
            r'VISTO.*?CONSIDERANDO',
            r'CONSIDERANDO.*?RESUELVE',
            r'RESUELVE.*?ART[IÍ]CULO',
            r'FALLO\s*:',
            r'SENTENCIA\s+N[°º]',
            r'En\s+.*?,\s+a\s+los\s+\d+\s+d[ií]as',  # Fecha formal
        ]

        texto_upper = texto.upper()

        for patron in patrones_formales:
            if re.search(patron, texto_upper):
                return True

        return False
