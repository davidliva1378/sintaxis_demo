"""
Limpiador de texto con reglas configurables por tipo de documento.

Permite aplicar reglas de limpieza específicas para diferentes tipos
de actuaciones judiciales (sentencias, cédulas, resoluciones, etc.)
"""

import re
from typing import Dict, List, Optional, Any


# =============================================================================
# REGLAS DE LIMPIEZA POR TIPO DE DOCUMENTO
# =============================================================================

REGLAS_LIMPIEZA: Dict[str, Dict[str, Any]] = {
    # Reglas para sentencias y resoluciones
    "SENTENCIA": {
        "descripcion": "Sentencias y fallos judiciales",
        "eliminar_patrones": [
            r'\d{13,16}',  # Códigos de barras numéricos largos
            r'#\d+#\d+#\d+',  # Firmas digitales PJN
            r'[A-Z0-9]{25,}',  # Hashes muy largos
        ],
        "eliminar_lineas_patron": [
            r'^\s*firmado\s+digitalmente',
            r'^\s*fecha\s+de\s+firma:',
            r'^\s*validar\s+en:',
        ],
        "preservar_estructura": True,
        "eliminar_footer": True,
        "eliminar_header": True,
    },

    "RESOLUCION": {
        "descripcion": "Resoluciones judiciales",
        "eliminar_patrones": [
            r'\d{13,16}',
            r'#\d+#\d+#\d+',
        ],
        "eliminar_lineas_patron": [
            r'^\s*firmado\s+digitalmente',
        ],
        "preservar_estructura": True,
        "eliminar_footer": True,
        "eliminar_header": True,
    },

    # Reglas para cédulas y notificaciones
    "CEDULA": {
        "descripcion": "Cédulas de notificación",
        "eliminar_patrones": [
            r'\d{13,16}',
            r'#\d+#\d+#\d+',
        ],
        "eliminar_lineas_patron": [
            r'^\s*código\s+de\s+verificación',
        ],
        "preservar_fechas": True,
        "preservar_plazos": True,
        "eliminar_footer": True,
        "eliminar_header": False,  # Las cédulas tienen info útil en header
    },

    "CEDULA_ELECTRONICA": {
        "descripcion": "Cédulas electrónicas",
        "eliminar_patrones": [
            r'\d{13,16}',
            r'#\d+#\d+#\d+',
            r'[A-Z0-9]{20,}',  # Códigos de verificación
        ],
        "eliminar_lineas_patron": [
            r'^\s*código\s+de\s+verificación',
            r'^\s*queda\s+ud\.\s*legalmente\s+notificado',
        ],
        "preservar_fechas": True,
        "preservar_plazos": True,
        "eliminar_footer": True,
        "eliminar_header": False,
    },

    "CEDULA_ELECTRONICA_PARTE": {
        "descripcion": "Cédulas electrónicas a partes",
        "eliminar_patrones": [
            r'\d{13,16}',
            r'#\d+#\d+#\d+',
        ],
        "preservar_fechas": True,
        "preservar_plazos": True,
        "eliminar_footer": True,
    },

    # Reglas para escritos
    "ESCRITO": {
        "descripcion": "Escritos presentados",
        "eliminar_patrones": [
            r'\d{13,16}',
            r'#\d+#\d+#\d+',
        ],
        "eliminar_footer": True,
        "eliminar_header": True,
    },

    "ESCRITO_AGREGADO": {
        "descripcion": "Escritos agregados al expediente",
        "eliminar_patrones": [
            r'\d{13,16}',
            r'#\d+#\d+#\d+',
        ],
        "eliminar_footer": True,
        "eliminar_header": True,
    },

    # Reglas para despachos y providencias
    "FIRMA_DESPACHO": {
        "descripcion": "Despachos firmados",
        "eliminar_patrones": [
            r'\d{13,16}',
            r'#\d+#\d+#\d+',
        ],
        "eliminar_footer": True,
        "eliminar_header": True,
    },

    "PROVIDENCIA": {
        "descripcion": "Providencias simples",
        "eliminar_patrones": [
            r'\d{13,16}',
            r'#\d+#\d+#\d+',
        ],
        "eliminar_footer": True,
        "eliminar_header": True,
    },

    # Cédulas electrónicas del tribunal
    "CEDULA_ELECTRONICA_TRIBUNAL": {
        "descripcion": "Cédulas electrónicas emitidas por el tribunal",
        "eliminar_patrones": [
            r'\d{13,16}',
            r'#\d+#\d+#\d+',
            r'[A-Z0-9]{20,}',  # Códigos de verificación
        ],
        "eliminar_lineas_patron": [
            r'^\s*código\s+de\s+verificación',
            r'^\s*queda\s+ud\.\s*legalmente\s+notificado',
            r'NOTIFICADO\s+EL\s+DIA:',
        ],
        "preservar_fechas": True,
        "preservar_plazos": True,
        "eliminar_footer": True,
        "eliminar_header": False,
    },

    # Publicación de sentencias
    "PUBLICACION_SENTENCIA": {
        "descripcion": "Publicaciones de sentencias",
        "eliminar_patrones": [
            r'\d{13,16}',
            r'#\d+#\d+#\d+',
            r'[A-Z0-9]{25,}',
        ],
        "eliminar_lineas_patron": [
            r'^\s*firmado\s+digitalmente',
            r'^\s*fecha\s+de\s+firma:',
            r'^\s*validar\s+en:',
        ],
        "preservar_estructura": True,
        "eliminar_footer": True,
        "eliminar_header": True,
    },

    # Despacho Electrónico de Oficios
    "DEO": {
        "descripcion": "Despacho Electrónico de Oficios",
        "eliminar_patrones": [
            r'\d{13,16}',
            r'#\d+#\d+#\d+',
            r'ENVIO\s+DEO:\s*\d+',
        ],
        "eliminar_footer": True,
        "eliminar_header": True,
    },

    # Escritos incorporados
    "ESCRITO_INCORPORADO": {
        "descripcion": "Escritos incorporados al expediente",
        "eliminar_patrones": [
            r'\d{13,16}',
            r'#\d+#\d+#\d+',
        ],
        "eliminar_footer": True,
        "eliminar_header": True,
    },

    # Despachos incorporados
    "DESPACHO_INCORPORADO": {
        "descripcion": "Despachos incorporados al expediente",
        "eliminar_patrones": [
            r'\d{13,16}',
            r'#\d+#\d+#\d+',
        ],
        "eliminar_footer": True,
        "eliminar_header": True,
    },

    # Regla por defecto
    "DEFAULT": {
        "descripcion": "Configuración por defecto",
        "eliminar_patrones": [
            r'\d{13,16}',
            r'#\d+#\d+#\d+',
            r'[A-Z0-9]{25,}',
        ],
        "eliminar_footer": True,
        "eliminar_header": True,
    },
}


class LimpiadorTexto:
    """
    Limpiador de texto con reglas configurables por tipo de documento.
    """

    def __init__(self, reglas_personalizadas: Optional[Dict] = None):
        """
        Inicializa el limpiador.

        Args:
            reglas_personalizadas: Reglas adicionales o modificadas
        """
        self.reglas = REGLAS_LIMPIEZA.copy()
        if reglas_personalizadas:
            self.reglas.update(reglas_personalizadas)

    def limpiar(self, texto: str, tipo_documento: str = "DEFAULT") -> str:
        """
        Limpia texto según reglas del tipo de documento.

        Args:
            texto: Texto a limpiar
            tipo_documento: Tipo de documento (SENTENCIA, CEDULA, etc.)

        Returns:
            Texto limpio
        """
        if not texto:
            return ""

        # Obtener reglas para este tipo
        reglas = self._obtener_reglas(tipo_documento)

        # Aplicar patrones de eliminación
        texto = self._aplicar_patrones_eliminacion(texto, reglas)

        # Eliminar líneas que coincidan con patrones específicos
        texto = self._eliminar_lineas_patron(texto, reglas)

        # Limpiar códigos insertados en palabras
        texto = self._limpiar_codigos_insertados(texto)

        # Limpiar espacios y saltos de línea
        texto = self._normalizar_espacios(texto)

        return texto.strip()

    def _obtener_reglas(self, tipo_documento: str) -> Dict[str, Any]:
        """
        Obtiene las reglas para un tipo de documento.

        Args:
            tipo_documento: Tipo de documento

        Returns:
            Diccionario con reglas
        """
        # Normalizar tipo (uppercase, sin espacios)
        tipo_normalizado = tipo_documento.upper().replace(" ", "_")

        # Buscar reglas específicas o usar default
        if tipo_normalizado in self.reglas:
            return self.reglas[tipo_normalizado]

        # Buscar coincidencia parcial
        for tipo, reglas in self.reglas.items():
            if tipo in tipo_normalizado or tipo_normalizado in tipo:
                return reglas

        return self.reglas.get("DEFAULT", {})

    def _aplicar_patrones_eliminacion(self, texto: str, reglas: Dict) -> str:
        """
        Aplica patrones de eliminación al texto.

        Args:
            texto: Texto a limpiar
            reglas: Reglas con patrones

        Returns:
            Texto sin los patrones
        """
        patrones = reglas.get("eliminar_patrones", [])

        for patron in patrones:
            # Eliminar coincidencias con espacios alrededor
            texto = re.sub(rf'\s*{patron}\s*', ' ', texto, flags=re.IGNORECASE)

        return texto

    def _eliminar_lineas_patron(self, texto: str, reglas: Dict) -> str:
        """
        Elimina líneas completas que coinciden con patrones.

        Args:
            texto: Texto a limpiar
            reglas: Reglas con patrones de líneas

        Returns:
            Texto sin las líneas que coinciden
        """
        patrones = reglas.get("eliminar_lineas_patron", [])
        if not patrones:
            return texto

        lineas = texto.split('\n')
        lineas_filtradas = []

        for linea in lineas:
            eliminar = False
            for patron in patrones:
                if re.search(patron, linea, re.IGNORECASE):
                    eliminar = True
                    break

            if not eliminar:
                lineas_filtradas.append(linea)

        return '\n'.join(lineas_filtradas)

    def _limpiar_codigos_insertados(self, texto: str) -> str:
        """
        Elimina códigos numéricos insertados dentro de palabras.

        Args:
            texto: Texto a limpiar

        Returns:
            Texto sin códigos insertados
        """
        # Código insertado en medio de palabra
        texto = re.sub(
            r'([a-záéíóúñü]+)\d{10,}([a-záéíóúñü]+)',
            r'\1\2',
            texto,
            flags=re.IGNORECASE
        )

        return texto

    def _normalizar_espacios(self, texto: str) -> str:
        """
        Normaliza espacios y saltos de línea.

        Args:
            texto: Texto a normalizar

        Returns:
            Texto con espacios normalizados
        """
        # Múltiples espacios a uno
        texto = re.sub(r' +', ' ', texto)

        # Múltiples saltos a máximo 2
        texto = re.sub(r'\n{3,}', '\n\n', texto)

        # Espacios al inicio/fin de líneas
        texto = re.sub(r'^ +', '', texto, flags=re.MULTILINE)
        texto = re.sub(r' +$', '', texto, flags=re.MULTILINE)

        return texto

    def obtener_tipos_disponibles(self) -> List[str]:
        """
        Retorna lista de tipos de documento configurados.

        Returns:
            Lista de tipos
        """
        return list(self.reglas.keys())

    def obtener_descripcion_tipo(self, tipo: str) -> str:
        """
        Retorna la descripción de un tipo de documento.

        Args:
            tipo: Tipo de documento

        Returns:
            Descripción o string vacío
        """
        reglas = self._obtener_reglas(tipo)
        return reglas.get("descripcion", "")

    def agregar_regla(self, tipo: str, reglas: Dict[str, Any]) -> None:
        """
        Agrega o actualiza reglas para un tipo de documento.

        Args:
            tipo: Tipo de documento
            reglas: Diccionario con reglas
        """
        self.reglas[tipo.upper()] = reglas

    def agregar_patron(self, tipo: str, patron: str) -> None:
        """
        Agrega un patrón de eliminación a un tipo existente.

        Args:
            tipo: Tipo de documento
            patron: Patrón regex a agregar
        """
        tipo_upper = tipo.upper()
        if tipo_upper not in self.reglas:
            self.reglas[tipo_upper] = {"eliminar_patrones": []}

        if "eliminar_patrones" not in self.reglas[tipo_upper]:
            self.reglas[tipo_upper]["eliminar_patrones"] = []

        self.reglas[tipo_upper]["eliminar_patrones"].append(patron)
