"""
Analizador de vencimientos y plazos procesales.

Detecta notificaciones con plazos y calcula fechas de vencimiento
considerando días hábiles, feriados y feria judicial.
"""

import re
from datetime import datetime, date, timedelta
from typing import List, Optional, Tuple, Dict, Any
import json
from .models import Vencimiento, TipoVencimiento
from core.config.vencimientos_config import VencimientosConfig
# Importación diferida para evitar ciclos si fuera necesario, 
# pero idealmente LLMService debería estar desacoplado.
from infrastructure.rag.services.llm_service import LLMService


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
        # Cédula con fecha en texto (ej: 28noviembre 2025)
        {
            "tipo": TipoVencimiento.CEDULA_ELECTRONICA,
            "regex": r"(?:notific[oóa]|fecha:?|emisi[oó]n).*?\s*(\d{1,2})\s*(?:de)?\s*([a-z]+)\s*(?:de)?\s*(\d{4})",
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

    # Meses en español
    MESES = {
        "enero": 1, "ener": 1, "ene": 1,
        "febrero": 2, "febr": 2, "feb": 2,
        "marzo": 3, "marz": 3, "mar": 3,
        "abril": 4, "abr": 4,
        "mayo": 5, "may": 5,
        "junio": 6, "jun": 6,
        "julio": 7, "jul": 7,
        "agosto": 8, "agos": 8, "ago": 8,
        "septiembre": 9, "sept": 9, "sep": 9, "setiembre": 9,
        "octubre": 10, "octu": 10, "oct": 10,
        "noviembre": 11, "novi": 11, "nov": 11,
        "diciembre": 12, "dici": 12, "dic": 12
    }

    def __init__(self, considerar_feria: bool = True):
        """
        Inicializa el analizador.

        Args:
            considerar_feria: Si considerar feria judicial en cálculos
        """
        self.considerar_feria = considerar_feria
        self._compilar_patrones()
        self.config_manager = VencimientosConfig.get_instance()
        self.llm_service = LLMService()

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
            if len(grupos) >= 3 and grupos[0] and grupos[0].isdigit():
                # Tiene fecha explícita (día, mes, año)
                dia = int(grupos[0])
                
                # Intentar parsear mes (número o texto)
                mes_raw = grupos[1].lower()
                if mes_raw.isdigit():
                    mes = int(mes_raw)
                else:
                    # Buscar en diccionario de meses
                    mes = self.MESES.get(mes_raw)
                    if not mes:
                        # Intentar limpiar caracteres extraños
                        mes_clean = "".join(filter(str.isalpha, mes_raw))
                        mes = self.MESES.get(mes_clean)
                
                if not mes:
                    return None

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
                # Buscar el grupo que tenga el plazo (puede variar si agregamos grupos de fecha antes)
                # Asumimos que si hay fecha, el plazo es el último grupo, si no, es el primero
                # Esto es frágil, mejor usar nombre de grupos o lógica específica
                # Por ahora, mantenemos compatibilidad: si hay fecha (3 grupos), no es variable usualmente
                # Si es variable, el regex suele ser distinto.
                # Revisando los patrones variables:
                # TRASLADO: r"traslado.*?(?:por|de)\s*(\d+)\s*d[ií]as?" -> 1 grupo (plazo)
                # Si agregamos fecha a traslado, tendremos más grupos.
                
                # Estrategia: buscar el primer grupo que sea dígito y parezca plazo
                plazo_dias = 0
                for g in grupos:
                    if g and g.isdigit():
                        plazo_dias = int(g)
                        break
                if plazo_dias == 0:
                     return None
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
        texto_para_analisis = detalle
        if extraer_de_pdf and ruta_pdf:
            from .extractor_texto import ExtractorTexto
            extractor = ExtractorTexto(usar_ocr=False)  # Sin OCR para vencimientos

            try:
                # Extraer solo primeros 1000 caracteres (suficiente para cédulas)
                texto_pdf = extractor.extraer_primeros_n_caracteres(ruta_pdf, 1000)
                vencimientos_pdf = self.analizar_texto(texto_pdf, act_id)
                vencimientos.extend(vencimientos_pdf)
                texto_para_analisis = texto_pdf # Usar texto PDF si está disponible
            except Exception:
                pass  # Si falla, continuar sin análisis de PDF

        # --- ANÁLISIS HÍBRIDO CON LLM ---
        if self.config_manager.config.hybrid_analysis_enabled:
            try:
                fecha_actuacion = self._parsear_fecha_actuacion(actuacion)
                margen = timedelta(days=self.config_manager.config.analysis_margin_days)
                
                # Solo analizar si es reciente
                if fecha_actuacion and fecha_actuacion >= date.today() - margen:
                    vencimientos_llm = self._analizar_con_llm(texto_para_analisis, act_id)
                    
                    # Estrategia de Unión: Agregar si no existe uno similar
                    for v_llm in vencimientos_llm:
                        if not self._existe_vencimiento_similar(v_llm, vencimientos):
                            vencimientos.append(v_llm)
            except Exception as e:
                print(f"Error en análisis híbrido LLM: {e}")

        return vencimientos

    def _parsear_fecha_actuacion(self, actuacion: dict) -> Optional[date]:
        """Intenta parsear la fecha de la actuación."""
        fecha_str = actuacion.get("Fecha") or actuacion.get("fecha")
        if not fecha_str:
            return None
        try:
            # Formatos comunes: "YYYY-MM-DD", "DD/MM/YYYY"
            if "-" in fecha_str:
                return datetime.strptime(fecha_str[:10], "%Y-%m-%d").date()
            elif "/" in fecha_str:
                return datetime.strptime(fecha_str[:10], "%d/%m/%Y").date()
            return None
        except:
            return None

    def _existe_vencimiento_similar(self, nuevo: Vencimiento, existentes: List[Vencimiento]) -> bool:
        """Verifica si ya existe un vencimiento similar para evitar duplicados."""
        for ex in existentes:
            # Consideramos similar si coincide tipo y fecha de vencimiento
            if ex.tipo == nuevo.tipo and ex.fecha_vencimiento == nuevo.fecha_vencimiento:
                return True
        return False

    def _analizar_con_llm(self, texto: str, actuacion_id: Optional[int]) -> List[Vencimiento]:
        """Ejecuta el análisis usando LLM."""
        if not texto or len(texto) < 10:
            return []

        try:
            prompt = self._build_dynamic_prompt(texto)
            # Usar temperatura baja para determinismo
            response_text = self.llm_service._call_ollama(
                prompt, 
                model=self.config_manager.config.llm_model, 
                temperature=0.0
            )
            
            # Limpiar respuesta para obtener JSON
            json_str = response_text.strip()
            if "```json" in json_str:
                json_str = json_str.split("```json")[1].split("```")[0].strip()
            elif "```" in json_str:
                json_str = json_str.split("```")[1].split("```")[0].strip()
            
            data = json.loads(json_str)
            vencimientos_data = data.get("vencimientos", [])
            
            resultados = []
            for v_data in vencimientos_data:
                try:
                    fecha_notif = datetime.strptime(v_data["fecha_notificacion"], "%Y-%m-%d").date()
                    plazo = int(v_data["plazo_dias"])
                    es_habil = v_data.get("dias_habiles", True)
                    
                    if es_habil:
                        fecha_venc = self.calcular_fecha_vencimiento(fecha_notif, plazo)
                    else:
                        fecha_venc = fecha_notif + timedelta(days=plazo)
                    
                    tipo_str = v_data.get("tipo", "OTRO")
                    # Mapear string a Enum si es posible, sino OTRO
                    tipo = TipoVencimiento.OTRO
                    for t in TipoVencimiento:
                        if t.value == tipo_str or t.name == tipo_str:
                            tipo = t
                            break
                            
                    resultados.append(Vencimiento(
                        tipo=tipo,
                        fecha_notificacion=fecha_notif,
                        plazo_dias=plazo,
                        fecha_vencimiento=fecha_venc,
                        dias_habiles=es_habil,
                        descripcion=f"[IA] {self._generar_descripcion(tipo, fecha_notif, plazo, fecha_venc)}",
                        actuacion_id=actuacion_id,
                        texto_fuente=v_data.get("texto_fuente", "")[:200],
                        confianza=0.85 # Confianza arbitraria para IA
                    ))
                except Exception as e:
                    print(f"Error parseando item LLM: {e}")
                    continue
            
            return resultados

        except Exception as e:
            print(f"Error en llamada LLM: {e}")
            return []

    def _build_dynamic_prompt(self, texto: str) -> str:
        """Construye el prompt con configuración y términos personalizados."""
        base_prompt = self.config_manager.config.system_prompt
        custom_terms = self.config_manager.config.custom_terms
        
        terms_text = ""
        if custom_terms:
            terms_text = "\nREGLAS DE PLAZOS PERSONALIZADAS (Prioridad Alta):\n"
            for term in custom_terms:
                nombre = term.get('nombre', '')
                dias = term.get('dias', 0)
                tipo_dias = 'hábiles' if term.get('habiles', True) else 'corridos'
                if nombre and dias > 0:
                    terms_text += f"- Si detectas '{nombre}': plazo de {dias} días {tipo_dias}.\n"
        
        return f"{base_prompt}\n{terms_text}\n\nTEXTO A ANALIZAR:\n{texto}"

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
