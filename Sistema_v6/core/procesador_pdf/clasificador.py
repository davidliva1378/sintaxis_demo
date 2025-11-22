"""
Clasificador de utilidad jurídica de actuaciones.

Utiliza reglas heurísticas basadas en tipo y detalle de la actuación
para determinar su relevancia para análisis RAG, agenda o auditoría.
"""

import re
from typing import Dict, List, Optional
from .models import ClasificacionActuacion, UtilidadJuridica


class ClasificadorActuaciones:
    """
    Clasificador de actuaciones por utilidad jurídica.

    Usa reglas heurísticas para asignar un score (0-100) y nivel de utilidad
    sin necesidad de abrir el PDF en la mayoría de los casos.
    """

    # Patrones para providencias simples (utilidad NULA)
    PATRONES_NULA = [
        r"^agreg[uú]ese",
        r"^t[ée]ngase\s+presente",
        r"^en\s+los\s+t[ée]rminos\s+solicitados",
        r"^c[ií]tese",
        r"^pase",
        r"^vuelva",
        r"^reserve",
        r"^archiv[eé]se",
        r"^no\s+ha\s+lugar",
        r"^t[ée]ngase\s+por\s+presentad[oa]",
    ]

    # Keywords para utilidad BAJA
    KEYWORDS_BAJA = [
        "cargo", "constancia", "devoluci[oó]n", "remisi[oó]n",
        "certifico", "secretar[ií]a", "mesa\s+de\s+entradas",
    ]

    # Keywords para utilidad MEDIA
    KEYWORDS_MEDIA = [
        "presentaci[oó]n", "solicitud", "pedido", "informe",
        "vista", "certificado", "intimaci[oó]n", "oficio",
    ]

    # Keywords para utilidad ALTA
    KEYWORDS_ALTA = [
        "sentencia", "resoluci[oó]n", "auto.*fundado", "fallo",
        "demanda", "contestaci[oó]n", "apelaci[oó]n", "alegato",
        "expresi[oó]n.*agravios", "agravios", "amparo",
        "medida.*cautelar", "medida.*precautoria",
        "resuelve", "considerando.*fallo", "visto.*considerando",
    ]

    # Tipos que indican cédulas (potencialmente tienen plazo)
    TIPOS_CEDULA = [
        "CEDULA", "NOTIFICACION", "CEDULA_NOTIF",
        "CEDULA_ELECTRONICA", "NOTIF_ELECTRONICA",
    ]

    # Tipos de alta prioridad
    TIPOS_ALTA_PRIORIDAD = [
        "SENTENCIA", "RESOLUCION", "AUTO", "FALLO", "DEO",
    ]

    # Tipos de baja prioridad
    TIPOS_BAJA_PRIORIDAD = [
        "CARGO", "CONSTANCIA", "DEVOLUCION", "REMISION",
        "PROVIDENCIA_SIMPLE", "DESPACHO",
    ]

    def __init__(self):
        """Inicializa el clasificador con patrones compilados."""
        self._compilar_patrones()

    def _compilar_patrones(self):
        """Compila los patrones regex para mejor performance."""
        self.patrones_nula_compilados = [
            re.compile(p, re.IGNORECASE) for p in self.PATRONES_NULA
        ]
        self.regex_keywords_baja = re.compile(
            "|".join(self.KEYWORDS_BAJA), re.IGNORECASE
        )
        self.regex_keywords_media = re.compile(
            "|".join(self.KEYWORDS_MEDIA), re.IGNORECASE
        )
        self.regex_keywords_alta = re.compile(
            "|".join(self.KEYWORDS_ALTA), re.IGNORECASE
        )

    def clasificar(
        self,
        tipo: str,
        detalle: str,
        tiene_archivo: bool = False,
        longitud_detalle: Optional[int] = None
    ) -> ClasificacionActuacion:
        """
        Clasifica una actuación por su utilidad jurídica.

        Args:
            tipo: Tipo de actuación (ej: "SENTENCIA", "PROVIDENCIA")
            detalle: Detalle/descripción de la actuación
            tiene_archivo: Si la actuación tiene archivo adjunto
            longitud_detalle: Longitud del detalle (si no se calcula automáticamente)

        Returns:
            ClasificacionActuacion con utilidad, score y motivo
        """
        tipo_upper = tipo.upper() if tipo else ""
        detalle_clean = detalle.strip() if detalle else ""

        if longitud_detalle is None:
            longitud_detalle = len(detalle_clean)

        keywords = []
        motivos = []

        # === UTILIDAD NULA ===
        # 1. Providencias simples por patrón
        for patron in self.patrones_nula_compilados:
            if patron.search(detalle_clean):
                keywords.append(patron.pattern)
                return ClasificacionActuacion(
                    utilidad=UtilidadJuridica.NULA,
                    score=5,
                    motivo=f"Providencia simple detectada: '{patron.pattern}'",
                    keywords_detectados=keywords,
                )

        # 2. Providencias/despachos muy cortos
        if (tipo_upper in ["PROVIDENCIA", "DESPACHO", "PROVEIDO"] and
                longitud_detalle < 50):
            return ClasificacionActuacion(
                utilidad=UtilidadJuridica.NULA,
                score=8,
                motivo=f"Providencia/despacho muy corto ({longitud_detalle} caracteres)",
            )

        # === UTILIDAD ALTA ===
        # 1. Por tipo de actuación
        if any(t in tipo_upper for t in self.TIPOS_ALTA_PRIORIDAD):
            score = 85
            motivo = f"Tipo de alta prioridad: {tipo_upper}"

            # Boost si tiene keywords relevantes
            if self.regex_keywords_alta.search(detalle_clean):
                score = min(95, score + 10)
                motivo += " + keywords jurídicos clave"

            return ClasificacionActuacion(
                utilidad=UtilidadJuridica.ALTA,
                score=score,
                motivo=motivo,
                tiene_plazo_probable=False,
                keywords_detectados=keywords,
            )

        # 2. Por keywords en detalle
        match_alta = self.regex_keywords_alta.search(detalle_clean)
        if match_alta:
            keywords.append(match_alta.group())
            return ClasificacionActuacion(
                utilidad=UtilidadJuridica.ALTA,
                score=80,
                motivo=f"Keywords de alta relevancia detectados: {match_alta.group()}",
                keywords_detectados=keywords,
            )

        # === CÉDULAS (pueden ser MEDIA o ALTA según contexto) ===
        es_cedula = any(t in tipo_upper for t in self.TIPOS_CEDULA)
        if es_cedula:
            # Cédulas con posible plazo → ALTA (para agenda)
            if self._tiene_patron_plazo(detalle_clean):
                return ClasificacionActuacion(
                    utilidad=UtilidadJuridica.ALTA,
                    score=75,
                    motivo="Cédula con posible plazo detectado (requiere análisis de vencimiento)",
                    tiene_plazo_probable=True,
                    keywords_detectados=keywords,
                )
            else:
                # Cédula sin plazo obvio → BAJA (sólo para registro)
                return ClasificacionActuacion(
                    utilidad=UtilidadJuridica.BAJA,
                    score=25,
                    motivo="Cédula sin plazo aparente",
                    es_duplicado_probable=True,  # Cédulas suelen duplicarse
                    keywords_detectados=keywords,
                )

        # === UTILIDAD BAJA ===
        # 1. Por tipo
        if any(t in tipo_upper for t in self.TIPOS_BAJA_PRIORIDAD):
            return ClasificacionActuacion(
                utilidad=UtilidadJuridica.BAJA,
                score=15,
                motivo=f"Tipo de baja prioridad: {tipo_upper}",
                keywords_detectados=keywords,
            )

        # 2. Por keywords
        if self.regex_keywords_baja.search(detalle_clean):
            return ClasificacionActuacion(
                utilidad=UtilidadJuridica.BAJA,
                score=20,
                motivo="Keywords de baja relevancia detectados",
                keywords_detectados=keywords,
            )

        # === UTILIDAD MEDIA (por keywords) ===
        if self.regex_keywords_media.search(detalle_clean):
            return ClasificacionActuacion(
                utilidad=UtilidadJuridica.MEDIA,
                score=50,
                motivo="Keywords de relevancia media detectados",
                keywords_detectados=keywords,
            )

        # === DEFAULT: MEDIA con requiere_pdf ===
        # No pudimos determinar con certeza, mejor revisar el PDF
        score = 45 if tiene_archivo else 35
        return ClasificacionActuacion(
            utilidad=UtilidadJuridica.MEDIA,
            score=score,
            motivo="Clasificación ambigua, requiere análisis del PDF",
            requiere_pdf=tiene_archivo,
            keywords_detectados=keywords,
        )

    def _tiene_patron_plazo(self, texto: str) -> bool:
        """
        Detecta si el texto contiene patrones que sugieren un plazo.

        Args:
            texto: Texto a analizar

        Returns:
            True si se detecta patrón de plazo
        """
        patrones_plazo = [
            r"notific[oóa].*\d{1,2}[/-]\d{1,2}[/-]\d{2,4}",
            r"plazo.*\d+\s*d[ií]as?",
            r"vence.*\d{1,2}[/-]\d{1,2}",
            r"traslado.*\d+\s*d[ií]as?",
            r"alegato.*\d+\s*d[ií]as?",
            r"presente.*\d+\s*d[ií]as?",
        ]

        for patron in patrones_plazo:
            if re.search(patron, texto, re.IGNORECASE):
                return True

        return False

    def clasificar_lote(
        self,
        actuaciones: List[Dict[str, any]]
    ) -> Dict[int, ClasificacionActuacion]:
        """
        Clasifica un lote de actuaciones.

        Args:
            actuaciones: Lista de diccionarios con datos de actuaciones
                        Cada dict debe tener: id, tipo, detalle, tiene_archivo

        Returns:
            Diccionario {actuacion_id: ClasificacionActuacion}
        """
        resultados = {}

        for act in actuaciones:
            act_id = act.get("id") or act.get("Indice")
            clasificacion = self.clasificar(
                tipo=act.get("tipo") or act.get("Tipo", ""),
                detalle=act.get("detalle") or act.get("Detalle", ""),
                tiene_archivo=act.get("tiene_archivo") or act.get("TieneArchivo", False),
            )
            resultados[act_id] = clasificacion

        return resultados

    def estadisticas_clasificacion(
        self,
        clasificaciones: Dict[int, ClasificacionActuacion]
    ) -> Dict[str, any]:
        """
        Genera estadísticas sobre un conjunto de clasificaciones.

        Args:
            clasificaciones: Resultado de clasificar_lote()

        Returns:
            Dict con contadores y porcentajes por utilidad
        """
        total = len(clasificaciones)
        if total == 0:
            return {}

        contadores = {
            UtilidadJuridica.NULA: 0,
            UtilidadJuridica.BAJA: 0,
            UtilidadJuridica.MEDIA: 0,
            UtilidadJuridica.ALTA: 0,
        }

        requieren_pdf = 0
        tienen_plazo = 0
        probables_duplicados = 0

        for clasif in clasificaciones.values():
            contadores[clasif.utilidad] += 1
            if clasif.requiere_pdf:
                requieren_pdf += 1
            if clasif.tiene_plazo_probable:
                tienen_plazo += 1
            if clasif.es_duplicado_probable:
                probables_duplicados += 1

        return {
            "total_actuaciones": total,
            "nula": {
                "count": contadores[UtilidadJuridica.NULA],
                "porcentaje": round(contadores[UtilidadJuridica.NULA] / total * 100, 2)
            },
            "baja": {
                "count": contadores[UtilidadJuridica.BAJA],
                "porcentaje": round(contadores[UtilidadJuridica.BAJA] / total * 100, 2)
            },
            "media": {
                "count": contadores[UtilidadJuridica.MEDIA],
                "porcentaje": round(contadores[UtilidadJuridica.MEDIA] / total * 100, 2)
            },
            "alta": {
                "count": contadores[UtilidadJuridica.ALTA],
                "porcentaje": round(contadores[UtilidadJuridica.ALTA] / total * 100, 2)
            },
            "requieren_pdf": requieren_pdf,
            "tienen_plazo_probable": tienen_plazo,
            "probables_duplicados": probables_duplicados,
            "reduccion_estimada": round(
                (contadores[UtilidadJuridica.NULA] + contadores[UtilidadJuridica.BAJA]) / total * 100,
                2
            )
        }
