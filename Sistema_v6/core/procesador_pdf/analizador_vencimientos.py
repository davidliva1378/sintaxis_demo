"""
Analizador de vencimientos y plazos procesales.

Detecta notificaciones con plazos y calcula fechas de vencimiento
considerando días hábiles, feriados y feria judicial.
"""

import re
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple
from .models import Vencimiento, TipoVencimiento


class AnalizadorVencimientos:
    """
    Analizador de vencimientos procesales.

    Detecta patrones de notificaciones y plazos en texto jurídico
    y calcula fechas de vencimiento considerando el calendario procesal.
    """

    # Patrones de detección de plazos
    PATRONES_PLAZO = [
        # Cédula electrónica con fecha
        {
            "tipo": TipoVencimiento.CEDULA_ELECTRONICA,
            "regex": r"notific[oóa].*?(?:el|fecha:?)\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",
            "plazo_dias": 5,
            "dias_habiles": True,
            "confianza": 0.95
        },
        # Cédula física
        {
            "tipo": TipoVencimiento.CEDULA_FISICA,
            "regex": r"c[eé]dula.*?(?:el|fecha:?)\s*(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})",
            "plazo_dias": 3,
            "dias_habiles": True,
            "confianza": 0.90
        },
        # Traslado con plazo variable
        {
            "tipo": TipoVencimiento.TRASLADO,
            "regex": r"traslado.*?(?:por|de)\s*(\d+)\s*d[ií]as?",
            "plazo_variable": True,
            "dias_habiles": True,
            "confianza": 0.92
        },
        # Alegato
        {
            "tipo": TipoVencimiento.ALEGATO,
            "regex": r"alegato.*?(?:por|de)\s*(\d+)\s*d[ií]as?",
            "plazo_variable": True,
            "dias_habiles": True,
            "confianza": 0.90
        },
        # Plazo genérico para presentar
        {
            "tipo": TipoVencimiento.PRESENTACION,
            "regex": r"present[ea].*?(?:dentro|en)\s*(?:el\s+)?(?:plazo\s+de\s+)?(\d+)\s*d[ií]as?",
            "plazo_variable": True,
            "dias_habiles": True,
            "confianza": 0.85
        },
    ]

    # Feriados nacionales 2024-2025 (simplificado, debería venir de una BD)
    FERIADOS_2024 = [
        date(2024, 1, 1),   # Año Nuevo
        date(2024, 2, 12),  # Carnaval
        date(2024, 2, 13),  # Carnaval
        date(2024, 3, 24),  # Día de la Memoria
        date(2024, 3, 29),  # Viernes Santo
        date(2024, 4, 2),   # Malvinas
        date(2024, 5, 1),   # Día del Trabajador
        date(2024, 5, 25),  # Revolución de Mayo
        date(2024, 6, 17),  # Güemes (trasladado)
        date(2024, 6, 20),  # Día de la Bandera
        date(2024, 7, 9),   # Independencia
        date(2024, 8, 17),  # San Martín (trasladado)
        date(2024, 10, 12), # Respeto a la Diversidad
        date(2024, 11, 18), # Soberanía Nacional
        date(2024, 12, 8),  # Inmaculada Concepción
        date(2024, 12, 25), # Navidad
    ]

    FERIADOS_2025 = [
        date(2025, 1, 1),   # Año Nuevo
        date(2025, 3, 3),   # Carnaval
        date(2025, 3, 4),   # Carnaval
        date(2025, 3, 24),  # Día de la Memoria
        date(2025, 4, 2),   # Malvinas
        date(2025, 4, 18),  # Viernes Santo
        date(2025, 5, 1),   # Día del Trabajador
        date(2025, 5, 25),  # Revolución de Mayo
        date(2025, 6, 16),  # Güemes (trasladado)
        date(2025, 6, 20),  # Día de la Bandera
        date(2025, 7, 9),   # Independencia
        date(2025, 8, 17),  # San Martín
        date(2025, 10, 12), # Respeto a la Diversidad
        date(2025, 11, 24), # Soberanía Nacional (trasladado)
        date(2025, 12, 8),  # Inmaculada Concepción
        date(2025, 12, 25), # Navidad
    ]

    # Feria judicial (enero-febrero en Justicia Nacional)
    FERIA_JUDICIAL_2024 = (date(2024, 1, 1), date(2024, 2, 29))
    FERIA_JUDICIAL_2025 = (date(2025, 1, 1), date(2025, 2, 28))

    def __init__(self, considerar_feria: bool = True):
        """
        Inicializa el analizador.

        Args:
            considerar_feria: Si considerar feria judicial en cálculos
        """
        self.considerar_feria = considerar_feria
        self._compilar_patrones()

    def _compilar_patrones(self):
        """Compila los patrones regex para mejor performance."""
        for patron_dict in self.PATRONES_PLAZO:
            patron_dict["regex_compilado"] = re.compile(
                patron_dict["regex"],
                re.IGNORECASE | re.DOTALL
            )

    def analizar_texto(
        self,
        texto: str,
        actuacion_id: Optional[int] = None
    ) -> List[Vencimiento]:
        """
        Analiza texto en busca de vencimientos.

        Args:
            texto: Texto a analizar
            actuacion_id: ID de la actuación (opcional)

        Returns:
            Lista de Vencimiento detectados
        """
        vencimientos = []

        for patron_dict in self.PATRONES_PLAZO:
            matches = patron_dict["regex_compilado"].finditer(texto)

            for match in matches:
                vencimiento = self._procesar_match(
                    match,
                    patron_dict,
                    texto,
                    actuacion_id
                )
                if vencimiento:
                    vencimientos.append(vencimiento)

        return vencimientos

    def _procesar_match(
        self,
        match: re.Match,
        patron_dict: dict,
        texto_completo: str,
        actuacion_id: Optional[int]
    ) -> Optional[Vencimiento]:
        """
        Procesa un match de regex y crea un Vencimiento.

        Args:
            match: Match de regex
            patron_dict: Diccionario con info del patrón
            texto_completo: Texto completo
            actuacion_id: ID de actuación

        Returns:
            Vencimiento o None si no se pudo crear
        """
        try:
            # Extraer grupos
            grupos = match.groups()

            # Detectar fecha de notificación
            if len(grupos) >= 3 and grupos[0].isdigit():
                # Tiene fecha explícita (día, mes, año)
                dia = int(grupos[0])
                mes = int(grupos[1])
                anio = int(grupos[2])

                # Normalizar año
                if anio < 100:
                    anio += 2000

                fecha_notif = date(anio, mes, dia)

            else:
                # No tiene fecha explícita, usar fecha actual
                fecha_notif = date.today()

            # Determinar plazo en días
            if patron_dict.get("plazo_variable"):
                # El plazo está en el primer grupo capturado
                plazo_dias = int(grupos[0])
            else:
                # El plazo es fijo según el tipo
                plazo_dias = patron_dict["plazo_dias"]

            # Calcular fecha de vencimiento
            if patron_dict["dias_habiles"]:
                fecha_venc = self.calcular_fecha_vencimiento(
                    fecha_notif,
                    plazo_dias
                )
            else:
                fecha_venc = fecha_notif + timedelta(days=plazo_dias)

            # Extraer fragmento de texto fuente
            inicio = max(0, match.start() - 50)
            fin = min(len(texto_completo), match.end() + 50)
            texto_fuente = texto_completo[inicio:fin].strip()

            # Crear descripción
            descripcion = self._generar_descripcion(
                patron_dict["tipo"],
                fecha_notif,
                plazo_dias,
                fecha_venc
            )

            return Vencimiento(
                tipo=patron_dict["tipo"],
                fecha_notificacion=fecha_notif,
                plazo_dias=plazo_dias,
                fecha_vencimiento=fecha_venc,
                dias_habiles=patron_dict["dias_habiles"],
                descripcion=descripcion,
                actuacion_id=actuacion_id,
                texto_fuente=texto_fuente,
                confianza=patron_dict["confianza"]
            )

        except (ValueError, IndexError) as e:
            # Error al parsear fecha o grupos
            return None

    def calcular_fecha_vencimiento(
        self,
        fecha_inicio: date,
        plazo_dias: int
    ) -> date:
        """
        Calcula fecha de vencimiento considerando días hábiles.

        Args:
            fecha_inicio: Fecha de inicio del plazo
            plazo_dias: Cantidad de días hábiles del plazo

        Returns:
            Fecha de vencimiento
        """
        fecha_actual = fecha_inicio
        dias_transcurridos = 0

        # Avanzar hasta completar los días hábiles
        while dias_transcurridos < plazo_dias:
            fecha_actual += timedelta(days=1)

            # Verificar si es día hábil
            if self.es_dia_habil(fecha_actual):
                dias_transcurridos += 1

        return fecha_actual

    def es_dia_habil(self, fecha: date) -> bool:
        """
        Verifica si una fecha es día hábil.

        Args:
            fecha: Fecha a verificar

        Returns:
            True si es día hábil
        """
        # Sábados y domingos no son hábiles
        if fecha.weekday() in [5, 6]:  # 5=sábado, 6=domingo
            return False

        # Feriados no son hábiles
        if self.es_feriado(fecha):
            return False

        # Feria judicial (si está habilitada)
        if self.considerar_feria and self.es_feria_judicial(fecha):
            return False

        return True

    def es_feriado(self, fecha: date) -> bool:
        """
        Verifica si una fecha es feriado.

        Args:
            fecha: Fecha a verificar

        Returns:
            True si es feriado
        """
        if fecha.year == 2024:
            return fecha in self.FERIADOS_2024
        elif fecha.year == 2025:
            return fecha in self.FERIADOS_2025
        else:
            # Para años futuros, usar librería holidays
            return False

    def es_feria_judicial(self, fecha: date) -> bool:
        """
        Verifica si una fecha cae en feria judicial.

        Args:
            fecha: Fecha a verificar

        Returns:
            True si es feria judicial
        """
        if fecha.year == 2024:
            inicio, fin = self.FERIA_JUDICIAL_2024
        elif fecha.year == 2025:
            inicio, fin = self.FERIA_JUDICIAL_2025
        else:
            # Por defecto, feria en enero-febrero
            inicio = date(fecha.year, 1, 1)
            fin = date(fecha.year, 2, 28)

        return inicio <= fecha <= fin

    def _generar_descripcion(
        self,
        tipo: TipoVencimiento,
        fecha_notif: date,
        plazo_dias: int,
        fecha_venc: date
    ) -> str:
        """
        Genera descripción legible del vencimiento.

        Args:
            tipo: Tipo de vencimiento
            fecha_notif: Fecha de notificación
            plazo_dias: Plazo en días
            fecha_venc: Fecha de vencimiento

        Returns:
            Descripción del vencimiento
        """
        descripciones = {
            TipoVencimiento.CEDULA_ELECTRONICA: "Cédula electrónica",
            TipoVencimiento.CEDULA_FISICA: "Cédula física",
            TipoVencimiento.TRASLADO: "Traslado",
            TipoVencimiento.ALEGATO: "Alegato",
            TipoVencimiento.PRESENTACION: "Presentación",
            TipoVencimiento.OTRO: "Plazo"
        }

        tipo_desc = descripciones.get(tipo, "Plazo")

        return (
            f"{tipo_desc} notificada el {fecha_notif.strftime('%d/%m/%Y')} - "
            f"Plazo: {plazo_dias} días hábiles - "
            f"Vence: {fecha_venc.strftime('%d/%m/%Y')}"
        )

    def analizar_actuacion(
        self,
        actuacion: dict,
        extraer_de_pdf: bool = False,
        ruta_pdf: Optional[str] = None
    ) -> List[Vencimiento]:
        """
        Analiza una actuación completa en busca de vencimientos.

        Args:
            actuacion: Dict con datos de la actuación
            extraer_de_pdf: Si extraer texto del PDF
            ruta_pdf: Ruta al PDF (requerido si extraer_de_pdf=True)

        Returns:
            Lista de vencimientos detectados
        """
        vencimientos = []
        act_id = actuacion.get("id") or actuacion.get("Indice")

        # Analizar campo Detalle
        detalle = actuacion.get("Detalle") or actuacion.get("detalle", "")
        if detalle:
            vencimientos.extend(self.analizar_texto(detalle, act_id))

        # Si se solicita, analizar PDF
        if extraer_de_pdf and ruta_pdf:
            from .extractor_texto import ExtractorTexto
            extractor = ExtractorTexto(usar_ocr=False)  # Sin OCR para vencimientos

            try:
                # Extraer solo primeros 1000 caracteres (suficiente para cédulas)
                texto_pdf = extractor.extraer_primeros_n_caracteres(ruta_pdf, 1000)
                vencimientos.extend(self.analizar_texto(texto_pdf, act_id))
            except Exception:
                pass  # Si falla, continuar sin análisis de PDF

        return vencimientos

    def filtrar_vencimientos_urgentes(
        self,
        vencimientos: List[Vencimiento],
        dias_umbral: int = 5
    ) -> List[Vencimiento]:
        """
        Filtra vencimientos urgentes.

        Args:
            vencimientos: Lista de vencimientos
            dias_umbral: Máximo de días para considerar urgente

        Returns:
            Lista de vencimientos urgentes
        """
        return [
            v for v in vencimientos
            if not v.esta_vencido and v.dias_restantes <= dias_umbral
        ]

    def filtrar_vencimientos_vencidos(
        self,
        vencimientos: List[Vencimiento]
    ) -> List[Vencimiento]:
        """
        Filtra vencimientos ya vencidos.

        Args:
            vencimientos: Lista de vencimientos

        Returns:
            Lista de vencimientos vencidos
        """
        return [v for v in vencimientos if v.esta_vencido]
