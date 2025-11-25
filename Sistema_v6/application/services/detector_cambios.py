"""
Detector de Cambios en Expedientes.

Migrado desde Sistema_v5/pjn/monitor/detector.py
Detecta cambios en 4 campos clave de expedientes.
"""

from dataclasses import dataclass
from typing import Protocol
import logging
import re

logger = logging.getLogger(__name__)


def _normalizar_numero(numero: str) -> str:
    """Normaliza el formato del número de expediente para comparación.

    Convierte diferentes formatos a uno común, preservando sufijos de incidentes:
    - 'FPA_005672_2014' → 'FPA-005672-2014'
    - 'FRE-010171-2019' → 'FRE-010171-2019'
    - 'FRE 004379/2021' → 'FRE-004379-2021'
    - 'FRE 004379/2021/1' → 'FRE-004379-2021-1' (incidente)
    - 'FRE 004379/2021/I' → 'FRE-004379-2021-I' (incidente)

    Args:
        numero: Número de expediente en cualquier formato

    Returns:
        Número normalizado con formato 'XXX-NNNNNN-YYYY' o 'XXX-NNNNNN-YYYY-SUFIJO'
    """
    if not numero:
        return ""
    # Extraer componentes: prefijo (letras), número, año, y opcionalmente sufijo de incidente
    match = re.match(r'([A-Z]+)[\s\-_]?(\d+)[\-/_](\d{4})(?:[\s\-/_](.+))?', numero.strip().upper())
    if match:
        prefijo, num, anio, sufijo = match.groups()
        base = f"{prefijo}-{num}-{anio}"
        # Si hay sufijo (incidente), agregarlo al identificador
        return f"{base}-{sufijo}" if sufijo else base
    return numero.strip().upper()


class ExpedienteResumen(Protocol):
    """Protocol para expediente (compatible con core.domain.entities)"""
    numero: str
    ultima_actuacion: str | None
    situacion: str | None
    dependencia: str | None
    caratula: str | None


@dataclass
class CambioExpediente:
    """
    Representa un cambio detectado en un expediente.

    Attributes:
        expediente: Expediente con los valores actuales
        tipo_cambio: Tipo de cambio detectado
        campos_cambiados: Lista de nombres de campos que cambiaron
        valores_anteriores: Diccionario con valores anteriores de los campos
    """
    expediente: ExpedienteResumen
    tipo_cambio: str
    campos_cambiados: list[str]
    valores_anteriores: dict[str, str | None]

    def __str__(self) -> str:
        return (
            f"CambioExpediente({self.expediente.numero}, "
            f"tipo={self.tipo_cambio}, "
            f"campos={', '.join(self.campos_cambiados)})"
        )


class DetectorCambios:
    """
    Detector de cambios en expedientes.

    Compara listas de expedientes y detecta cambios en 4 campos clave:
    - ultima_actuacion: Fecha de la última actuación
    - situacion: Estado del expediente (ej: "En trámite", "EN LETRA")
    - dependencia: Dependencia asignada
    - caratula: Carátula del expediente

    Tipos de cambios detectados:
    - nueva_actuacion: Solo cambió la fecha de última actuación
    - cambio_situacion: Solo cambió el estado/situación
    - cambio_dependencia: Solo cambió la dependencia
    - cambio_caratula: Solo cambió la carátula
    - multiples_cambios: Cambiaron 2 o más campos

    Example:
        >>> detector = DetectorCambios()
        >>> cambios = detector.detectar_cambios_expedientes(actuales, anteriores)
        >>> for cambio in cambios:
        ...     print(f"Cambio en {cambio.expediente.numero}: {cambio.tipo_cambio}")
    """

    def __init__(self):
        """Inicializa el detector de cambios"""
        self._campos_monitoreados = [
            "ultima_actuacion",
            "situacion",
            "dependencia",
            "caratula"
        ]

    def detectar_cambios_expedientes(
        self,
        actuales: list[ExpedienteResumen],
        anteriores: list[ExpedienteResumen],
    ) -> list[CambioExpediente]:
        """
        Detecta cambios entre dos listas de expedientes.

        Compara cada expediente actual con su versión anterior y detecta
        cambios en los 4 campos monitoreados.

        Args:
            actuales: Lista de expedientes con el estado actual
            anteriores: Lista de expedientes con el estado anterior

        Returns:
            Lista de CambioExpediente detectados

        Example:
            >>> anteriores = [ExpedienteResumen(numero="123", ultima_actuacion="2024-01-01", ...)]
            >>> actuales = [ExpedienteResumen(numero="123", ultima_actuacion="2024-01-15", ...)]
            >>> cambios = detector.detectar_cambios_expedientes(actuales, anteriores)
            >>> len(cambios)
            1
            >>> cambios[0].tipo_cambio
            'nueva_actuacion'
        """
        # Crear mapa de expedientes anteriores para búsqueda eficiente
        # Usar números normalizados como claves para comparación consistente
        mapa_anterior = {
            _normalizar_numero(exp.numero): {
                "ultima_actuacion": exp.ultima_actuacion,
                "situacion": exp.situacion,
                "dependencia": exp.dependencia,
                "caratula": exp.caratula,
            }
            for exp in anteriores
        }

        logger.debug(f"Mapa anterior creado con {len(mapa_anterior)} expedientes")
        cambios: list[CambioExpediente] = []
        no_encontrados = 0

        # Comparar cada expediente actual con su versión anterior
        for exp in actuales:
            num_normalizado = _normalizar_numero(exp.numero)
            if num_normalizado not in mapa_anterior:
                # Expediente nuevo, no hay cambios (se detecta en otro lugar)
                no_encontrados += 1
                logger.debug(f"Expediente {exp.numero} (normalizado: {num_normalizado}) no encontrado en anteriores")
                continue

            anterior = mapa_anterior[num_normalizado]
            campos_cambiados: list[str] = []

            # Comparar cada campo monitoreado
            if self._campo_cambio(exp.ultima_actuacion, anterior["ultima_actuacion"]):
                campos_cambiados.append("ultima_actuacion")
                logger.debug(
                    f"Expediente {exp.numero}: "
                    f"ultima_actuacion cambió de '{anterior['ultima_actuacion']}' a '{exp.ultima_actuacion}'"
                )

            if self._campo_cambio(exp.situacion, anterior["situacion"]):
                campos_cambiados.append("situacion")
                logger.debug(
                    f"Expediente {exp.numero}: "
                    f"situacion cambió de '{anterior['situacion']}' a '{exp.situacion}'"
                )

            if self._campo_cambio(exp.dependencia, anterior["dependencia"]):
                campos_cambiados.append("dependencia")
                logger.debug(
                    f"Expediente {exp.numero}: "
                    f"dependencia cambió de '{anterior['dependencia']}' a '{exp.dependencia}'"
                )

            if self._campo_cambio(exp.caratula, anterior["caratula"]):
                campos_cambiados.append("caratula")
                logger.debug(
                    f"Expediente {exp.numero}: "
                    f"caratula cambió"
                )

            # Si hubo cambios, crear CambioExpediente
            if campos_cambiados:
                tipo_cambio = self._clasificar_cambio(campos_cambiados)

                cambio = CambioExpediente(
                    expediente=exp,
                    tipo_cambio=tipo_cambio,
                    campos_cambiados=campos_cambiados,
                    valores_anteriores=anterior,
                )

                cambios.append(cambio)

                logger.info(
                    f"Cambio detectado en expediente {exp.numero}: "
                    f"{tipo_cambio} ({len(campos_cambiados)} campo(s))"
                )

        if no_encontrados > 0:
            logger.warning(f"Expedientes no encontrados en anteriores: {no_encontrados}")
        logger.info(f"Total de cambios detectados: {len(cambios)} de {len(actuales)} expedientes comparados")
        return cambios

    def _campo_cambio(self, actual: str | None, anterior: str | None) -> bool:
        """
        Determina si un campo cambió.

        Compara valores normalizando None y cadenas vacías.

        Args:
            actual: Valor actual del campo
            anterior: Valor anterior del campo

        Returns:
            True si el campo cambió, False en caso contrario
        """
        # Normalizar None y cadenas vacías
        val_actual = (actual or "").strip()
        val_anterior = (anterior or "").strip()

        return val_actual != val_anterior

    def _clasificar_cambio(self, campos: list[str]) -> str:
        """
        Clasifica el tipo de cambio según los campos afectados.

        Args:
            campos: Lista de nombres de campos que cambiaron

        Returns:
            Tipo de cambio: nueva_actuacion, cambio_situacion,
            cambio_dependencia, cambio_caratula, o multiples_cambios
        """
        if len(campos) > 1:
            return "multiples_cambios"

        campo = campos[0]

        if campo == "ultima_actuacion":
            return "nueva_actuacion"
        elif campo == "situacion":
            return "cambio_situacion"
        elif campo == "dependencia":
            return "cambio_dependencia"
        elif campo == "caratula":
            return "cambio_caratula"
        else:
            # Fallback (no debería ocurrir con los campos monitoreados)
            return f"cambio_{campo}"

    def obtener_resumen_cambios(self, cambios: list[CambioExpediente]) -> dict:
        """
        Genera un resumen estadístico de los cambios detectados.

        Args:
            cambios: Lista de cambios detectados

        Returns:
            Diccionario con estadísticas de cambios

        Example:
            >>> resumen = detector.obtener_resumen_cambios(cambios)
            >>> resumen['total']
            5
            >>> resumen['por_tipo']['nueva_actuacion']
            3
        """
        resumen = {
            "total": len(cambios),
            "por_tipo": {},
            "expedientes_afectados": set()
        }

        for cambio in cambios:
            # Contar por tipo
            tipo = cambio.tipo_cambio
            resumen["por_tipo"][tipo] = resumen["por_tipo"].get(tipo, 0) + 1

            # Agregar expediente afectado
            resumen["expedientes_afectados"].add(cambio.expediente.numero)

        # Convertir set a lista para serialización
        resumen["expedientes_afectados"] = list(resumen["expedientes_afectados"])

        return resumen
