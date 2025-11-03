"""
Módulo de Procesamiento Inteligente de Actuaciones
===================================================

Integra el módulo procesador_pdf con el sistema de extracción de actuaciones
del Portal PJN para proporcionar:
- Clasificación automática por utilidad jurídica
- Detección de duplicados
- Análisis de vencimientos y plazos procesales
- Extracción de texto de PDFs descargados

Autor: Sistema sintaXis
Fecha: 2025-11-03
"""

import json
import os
import logging
from typing import Dict, List, Tuple, Optional
from datetime import datetime
from pathlib import Path

# Importar módulos de procesador_pdf
try:
    from Sistema_v5.procesador_pdf import (
        ClasificadorActuaciones,
        DetectorDuplicados,
        AnalizadorVencimientos,
        ExtractorTexto,
        UtilidadJuridica
    )
    PROCESADOR_DISPONIBLE = True
except ImportError as e:
    logging.warning(f"No se pudo importar procesador_pdf: {e}")
    PROCESADOR_DISPONIBLE = False


logger = logging.getLogger(__name__)


class ProcesadorActuacionesExtraccion:
    """
    Procesa actuaciones extraídas del PJN con análisis inteligente.

    Responsabilidades:
    - Clasificar actuaciones por utilidad jurídica (NULA, BAJA, MEDIA, ALTA)
    - Detectar duplicados exactos y semánticos
    - Analizar vencimientos y plazos procesales
    - Extraer texto de PDFs para análisis posterior

    Ejemplo de uso:
        >>> procesador = ProcesadorActuacionesExtraccion()
        >>> json_path = "actuaciones-1234_2023.json"
        >>> resultado = procesador.procesar_archivo_json(json_path)
        >>> print(resultado["Estadisticas"]["UtilidadAlta"])
        5
    """

    def __init__(self, config: Optional[Dict] = None):
        """
        Inicializa el procesador.

        Args:
            config: Configuración opcional para procesamiento
                {
                    "clasificar": True,
                    "detectar_duplicados": True,
                    "analizar_vencimientos": True,
                    "extraer_texto_pdfs": False,
                    "dias_urgente": 5
                }
        """
        if not PROCESADOR_DISPONIBLE:
            raise ImportError(
                "El módulo procesador_pdf no está disponible. "
                "Verifica que Sistema_v5/procesador_pdf esté correctamente instalado."
            )

        # Configuración por defecto
        self.config = {
            "clasificar": True,
            "detectar_duplicados": True,
            "analizar_vencimientos": True,
            "extraer_texto_pdfs": False,  # Opcional, puede ser lento
            "dias_urgente": 5
        }

        if config:
            self.config.update(config)

        # Inicializar componentes de procesador_pdf
        self.clasificador = ClasificadorActuaciones()
        self.detector_duplicados = DetectorDuplicados()
        self.analizador_vencimientos = AnalizadorVencimientos()
        self.extractor_texto = ExtractorTexto(usar_ocr=False)  # OCR deshabilitado por defecto

        logger.info("ProcesadorActuacionesExtraccion inicializado")

    def procesar_archivo_json(self, ruta_json: str) -> Dict:
        """
        Lee un archivo JSON de actuaciones y lo procesa completamente.

        Args:
            ruta_json: Ruta al archivo JSON con actuaciones extraídas

        Returns:
            Dict con datos procesados y estadísticas:
            {
                "Expediente": {...},
                "Actuaciones": [...],
                "Procesamiento": {
                    "Timestamp": "2025-11-03T14:30:00",
                    "Estadisticas": {...},
                    "Duplicados": [...],
                    "VencimientosUrgentes": [...]
                }
            }

        Ejemplo:
            >>> procesador = ProcesadorActuacionesExtraccion()
            >>> resultado = procesador.procesar_archivo_json("actuaciones-1234_2023.json")
            >>> print(f"Procesadas {resultado['Procesamiento']['Estadisticas']['Total']} actuaciones")
        """
        logger.info(f"Procesando archivo JSON: {ruta_json}")

        if not os.path.exists(ruta_json):
            raise FileNotFoundError(f"No se encontró el archivo: {ruta_json}")

        # Cargar JSON
        with open(ruta_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "Actuaciones" not in data:
            raise ValueError("El JSON no contiene la clave 'Actuaciones'")

        actuaciones = data["Actuaciones"]
        logger.info(f"Cargadas {len(actuaciones)} actuaciones para procesar")

        # Procesar cada actuación
        if self.config["clasificar"]:
            actuaciones = self._clasificar_actuaciones(actuaciones)

        if self.config["analizar_vencimientos"]:
            actuaciones = self._analizar_vencimientos(actuaciones)

        # Detectar duplicados (necesita todas las actuaciones)
        duplicados = []
        if self.config["detectar_duplicados"]:
            duplicados = self._detectar_duplicados(actuaciones)

        # Generar estadísticas
        estadisticas = self._generar_estadisticas(actuaciones, duplicados)

        # Identificar vencimientos urgentes
        vencimientos_urgentes = self._filtrar_vencimientos_urgentes(actuaciones)

        # Actualizar estructura de datos
        data["Actuaciones"] = actuaciones
        data["Procesamiento"] = {
            "Timestamp": datetime.now().isoformat(),
            "Version": "1.0.0",
            "Configuracion": self.config,
            "Estadisticas": estadisticas,
            "Duplicados": duplicados,
            "VencimientosUrgentes": vencimientos_urgentes
        }

        # Guardar JSON procesado
        self._guardar_json_procesado(ruta_json, data)

        logger.info(f"Procesamiento completado: {estadisticas}")
        return data

    def _clasificar_actuaciones(self, actuaciones: List[Dict]) -> List[Dict]:
        """
        Clasifica cada actuación por utilidad jurídica.

        Args:
            actuaciones: Lista de actuaciones extraídas

        Returns:
            Lista de actuaciones con clasificación añadida
        """
        logger.info(f"Clasificando {len(actuaciones)} actuaciones...")

        for idx, actuacion in enumerate(actuaciones):
            try:
                clasificacion = self.clasificador.clasificar(
                    tipo=actuacion.get("Tipo", ""),
                    detalle=actuacion.get("Detalle", ""),
                    tiene_archivo=actuacion.get("TieneArchivo", False)
                )

                # Añadir clasificación a la actuación
                actuacion["Clasificacion"] = {
                    "utilidad": clasificacion.utilidad.value,
                    "score": clasificacion.score,
                    "motivo": clasificacion.motivo,
                    "tiene_plazo_probable": clasificacion.tiene_plazo_probable,
                    "es_duplicado_probable": clasificacion.es_duplicado_probable,
                    "keywords_detectados": clasificacion.keywords_detectados,
                    "requiere_pdf": clasificacion.requiere_pdf
                }

                # Campos adicionales de acceso rápido
                actuacion["UtilidadJuridica"] = clasificacion.utilidad.value
                actuacion["TienePlazo"] = clasificacion.tiene_plazo_probable

            except Exception as e:
                logger.warning(f"Error al clasificar actuación {idx + 1}: {e}")
                actuacion["Clasificacion"] = {
                    "utilidad": "MEDIA",  # Por defecto
                    "score": 50,
                    "motivo": f"Error en clasificación: {str(e)}",
                    "tiene_plazo_probable": False,
                    "es_duplicado_probable": False,
                    "keywords_detectados": [],
                    "requiere_pdf": False
                }
                actuacion["UtilidadJuridica"] = "MEDIA"
                actuacion["TienePlazo"] = False

        logger.info("Clasificación completada")
        return actuaciones

    def _analizar_vencimientos(self, actuaciones: List[Dict]) -> List[Dict]:
        """
        Analiza vencimientos y plazos procesales en actuaciones.

        Args:
            actuaciones: Lista de actuaciones

        Returns:
            Lista de actuaciones con vencimientos añadidos
        """
        logger.info(f"Analizando vencimientos en {len(actuaciones)} actuaciones...")

        for idx, actuacion in enumerate(actuaciones):
            try:
                # Solo analizar si hay probabilidad de plazo
                if actuacion.get("TienePlazo", False) or actuacion.get("Clasificacion", {}).get("tiene_plazo_probable", False):
                    vencimientos = self.analizador_vencimientos.analizar_actuacion(
                        actuacion,
                        extraer_de_pdf=False  # Por ahora sin PDF, solo del texto
                    )

                    if vencimientos:
                        actuacion["Vencimientos"] = [
                            {
                                "tipo": v.tipo.value,
                                "fecha_notificacion": v.fecha_notificacion.isoformat() if v.fecha_notificacion else None,
                                "fecha_vencimiento": v.fecha_vencimiento.isoformat() if v.fecha_vencimiento else None,
                                "dias_restantes": v.dias_restantes,
                                "es_urgente": v.es_urgente,
                                "descripcion": v.descripcion
                            }
                            for v in vencimientos
                        ]
                        actuacion["TieneVencimientos"] = True
                        actuacion["VencimientosUrgentes"] = any(v.es_urgente for v in vencimientos)
                    else:
                        actuacion["Vencimientos"] = []
                        actuacion["TieneVencimientos"] = False
                        actuacion["VencimientosUrgentes"] = False
                else:
                    actuacion["Vencimientos"] = []
                    actuacion["TieneVencimientos"] = False
                    actuacion["VencimientosUrgentes"] = False

            except Exception as e:
                logger.warning(f"Error al analizar vencimientos en actuación {idx + 1}: {e}")
                actuacion["Vencimientos"] = []
                actuacion["TieneVencimientos"] = False
                actuacion["VencimientosUrgentes"] = False

        logger.info("Análisis de vencimientos completado")
        return actuaciones

    def _detectar_duplicados(self, actuaciones: List[Dict]) -> List[Dict]:
        """
        Detecta actuaciones duplicadas.

        Args:
            actuaciones: Lista de actuaciones

        Returns:
            Lista de duplicados detectados
        """
        logger.info(f"Detectando duplicados en {len(actuaciones)} actuaciones...")

        duplicados_resultado = []

        try:
            # Detectar duplicados exactos
            duplicados_exactos = self.detector_duplicados.detectar_duplicados_exactos(actuaciones)

            for dup in duplicados_exactos:
                duplicados_resultado.append({
                    "tipo": "EXACTO",
                    "actuacion_original": dup.actuacion_id_original,
                    "actuacion_duplicada": dup.actuacion_id_duplicada,
                    "motivo": dup.motivo,
                    "similitud": 100.0
                })

            # Detectar cédulas duplicadas
            duplicados_cedulas = self.detector_duplicados.detectar_cedulas_duplicadas(actuaciones)

            for dup in duplicados_cedulas:
                duplicados_resultado.append({
                    "tipo": "CEDULA_DUPLICADA",
                    "actuacion_original": dup.actuacion_id_original,
                    "actuacion_duplicada": dup.actuacion_id_duplicada,
                    "motivo": dup.motivo,
                    "similitud": 100.0
                })

            # Marcar actuaciones como duplicadas
            ids_duplicados = set()
            for dup in duplicados_resultado:
                ids_duplicados.add(dup["actuacion_duplicada"])

            for actuacion in actuaciones:
                indice = actuacion.get("Indice")
                if indice in ids_duplicados:
                    actuacion["EsDuplicado"] = True
                else:
                    actuacion["EsDuplicado"] = False

            logger.info(f"Detectados {len(duplicados_resultado)} duplicados")

        except Exception as e:
            logger.warning(f"Error al detectar duplicados: {e}")

        return duplicados_resultado

    def _filtrar_vencimientos_urgentes(self, actuaciones: List[Dict]) -> List[Dict]:
        """
        Filtra y retorna solo los vencimientos urgentes.

        Args:
            actuaciones: Lista de actuaciones procesadas

        Returns:
            Lista de vencimientos urgentes con referencia a la actuación
        """
        urgentes = []

        for actuacion in actuaciones:
            if actuacion.get("VencimientosUrgentes", False):
                for venc in actuacion.get("Vencimientos", []):
                    if venc.get("es_urgente", False):
                        urgentes.append({
                            "indice_actuacion": actuacion.get("Indice"),
                            "tipo_actuacion": actuacion.get("Tipo"),
                            "fecha_actuacion": actuacion.get("Fecha"),
                            "vencimiento": venc
                        })

        # Ordenar por días restantes (más urgente primero)
        urgentes.sort(key=lambda x: x["vencimiento"].get("dias_restantes", 999))

        return urgentes

    def _generar_estadisticas(self, actuaciones: List[Dict], duplicados: List[Dict]) -> Dict:
        """
        Genera estadísticas del procesamiento.

        Args:
            actuaciones: Lista de actuaciones procesadas
            duplicados: Lista de duplicados detectados

        Returns:
            Dict con estadísticas
        """
        stats = {
            "Total": len(actuaciones),
            "Clasificadas": sum(1 for a in actuaciones if "Clasificacion" in a),
            "UtilidadNula": sum(1 for a in actuaciones if a.get("UtilidadJuridica") == "NULA"),
            "UtilidadBaja": sum(1 for a in actuaciones if a.get("UtilidadJuridica") == "BAJA"),
            "UtilidadMedia": sum(1 for a in actuaciones if a.get("UtilidadJuridica") == "MEDIA"),
            "UtilidadAlta": sum(1 for a in actuaciones if a.get("UtilidadJuridica") == "ALTA"),
            "ConVencimientos": sum(1 for a in actuaciones if a.get("TieneVencimientos", False)),
            "VencimientosUrgentes": sum(1 for a in actuaciones if a.get("VencimientosUrgentes", False)),
            "Duplicados": len(duplicados),
            "ConArchivos": sum(1 for a in actuaciones if a.get("TieneArchivo", False))
        }

        # Calcular reducción estimada
        reducibles = stats["UtilidadNula"] + stats["UtilidadBaja"]
        if stats["Total"] > 0:
            stats["PorcentajeReduccion"] = round((reducibles / stats["Total"]) * 100, 2)
        else:
            stats["PorcentajeReduccion"] = 0.0

        return stats

    def _guardar_json_procesado(self, ruta_original: str, data: Dict):
        """
        Guarda el JSON procesado.

        Args:
            ruta_original: Ruta del archivo JSON original
            data: Datos procesados a guardar
        """
        # Guardar sobre el original (backup opcional)
        try:
            with open(ruta_original, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"JSON procesado guardado en: {ruta_original}")
        except Exception as e:
            logger.error(f"Error al guardar JSON procesado: {e}")

    def procesar_directorio(self, directorio: str, patron: str = "actuaciones-*.json") -> List[Dict]:
        """
        Procesa todos los archivos JSON en un directorio.

        Args:
            directorio: Directorio con archivos JSON
            patron: Patrón de nombres de archivos a procesar

        Returns:
            Lista de resultados de procesamiento
        """
        from glob import glob

        archivos_json = glob(os.path.join(directorio, patron))
        logger.info(f"Encontrados {len(archivos_json)} archivos JSON para procesar")

        resultados = []
        for archivo in archivos_json:
            try:
                resultado = self.procesar_archivo_json(archivo)
                resultados.append({
                    "archivo": archivo,
                    "exito": True,
                    "estadisticas": resultado["Procesamiento"]["Estadisticas"]
                })
            except Exception as e:
                logger.error(f"Error al procesar {archivo}: {e}")
                resultados.append({
                    "archivo": archivo,
                    "exito": False,
                    "error": str(e)
                })

        return resultados


def procesar_actuaciones_extraidas(ruta_json: str, config: Optional[Dict] = None) -> Dict:
    """
    Función helper para procesar un archivo JSON de actuaciones.

    Args:
        ruta_json: Ruta al archivo JSON con actuaciones
        config: Configuración opcional de procesamiento

    Returns:
        Dict con datos procesados

    Ejemplo:
        >>> resultado = procesar_actuaciones_extraidas("actuaciones-1234_2023.json")
        >>> print(f"Utilidad alta: {resultado['Procesamiento']['Estadisticas']['UtilidadAlta']}")
    """
    procesador = ProcesadorActuacionesExtraccion(config=config)
    return procesador.procesar_archivo_json(ruta_json)


if __name__ == "__main__":
    # Ejemplo de uso
    import sys

    if len(sys.argv) < 2:
        print("Uso: python procesamiento.py <ruta_json>")
        sys.exit(1)

    ruta_json = sys.argv[1]

    print(f"Procesando: {ruta_json}")
    resultado = procesar_actuaciones_extraidas(ruta_json)

    print("\n" + "="*60)
    print("ESTADÍSTICAS DE PROCESAMIENTO")
    print("="*60)
    stats = resultado["Procesamiento"]["Estadisticas"]
    for clave, valor in stats.items():
        print(f"{clave:25s}: {valor}")

    print("\n" + "="*60)
    print(f"Duplicados detectados: {len(resultado['Procesamiento']['Duplicados'])}")
    print(f"Vencimientos urgentes: {len(resultado['Procesamiento']['VencimientosUrgentes'])}")
    print("="*60)
