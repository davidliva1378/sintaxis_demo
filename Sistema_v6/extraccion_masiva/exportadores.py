"""
Módulo de exportación de reportes en múltiples formatos.

Este módulo proporciona funciones para exportar los resultados de
extracciones masivas a diferentes formatos: JSON, Excel, CSV.
"""

import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


def exportar_json(data: Dict, ruta: Path) -> Path:
    """
    Exportar datos a formato JSON.

    Args:
        data: Datos a exportar
        ruta: Ruta del archivo de salida

    Returns:
        Path del archivo generado

    Raises:
        IOError: Si hay error al escribir el archivo
    """
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exportando a JSON: {ruta}")
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ JSON exportado exitosamente: {ruta}")
        return ruta

    except Exception as e:
        logger.error(f"Error exportando a JSON: {e}")
        raise IOError(f"Error al exportar JSON: {e}")


def exportar_excel(data: Dict, ruta: Path) -> Path:
    """
    Exportar datos a formato Excel (.xlsx).

    Requiere pandas y openpyxl instalados.

    Args:
        data: Datos a exportar (debe contener 'resultados')
        ruta: Ruta del archivo de salida

    Returns:
        Path del archivo generado

    Raises:
        ImportError: Si pandas u openpyxl no están instalados
        IOError: Si hay error al escribir el archivo
    """
    try:
        import pandas as pd
    except ImportError:
        error_msg = "pandas no está instalado. Ejecute: pip install pandas openpyxl"
        logger.error(error_msg)
        raise ImportError(error_msg)

    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exportando a Excel: {ruta}")

        # Convertir resultados a DataFrame
        resultados = data.get("resultado", {}).get("resultados", [])

        if not resultados:
            logger.warning("No hay resultados para exportar")
            resultados = []

        # Crear DataFrame con datos de expedientes
        df_data = []
        for r in resultados:
            df_data.append({
                "Número": r.get("numero", ""),
                "Estado": r.get("estado", ""),
                "Mensaje": r.get("mensaje", ""),
                "Error": r.get("error", ""),
                "Timestamp": r.get("timestamp", ""),
                "Duración (s)": r.get("duracion_segundos", 0),
            })

        df = pd.DataFrame(df_data)

        # Crear hoja de resumen
        resumen = data.get("resultado", {})
        df_resumen = pd.DataFrame([{
            "Session ID": data.get("session_id", ""),
            "Fecha": data.get("fecha", ""),
            "Total": resumen.get("total", 0),
            "Exitosos": resumen.get("exitosos", 0),
            "Errores": resumen.get("errores", 0),
            "Omitidos": resumen.get("omitidos", 0),
            "Duración (s)": resumen.get("duracion_segundos", 0),
            "Velocidad (exp/min)": resumen.get("velocidad_promedio", 0),
        }])

        # Exportar a Excel con múltiples hojas
        with pd.ExcelWriter(ruta, engine="openpyxl") as writer:
            df_resumen.to_excel(writer, sheet_name="Resumen", index=False)
            df.to_excel(writer, sheet_name="Resultados", index=False)

        logger.info(f"✅ Excel exportado exitosamente: {ruta}")
        return ruta

    except ImportError:
        raise
    except Exception as e:
        logger.error(f"Error exportando a Excel: {e}")
        raise IOError(f"Error al exportar Excel: {e}")


def exportar_csv(expedientes: List[Dict], ruta: Path) -> Path:
    """
    Exportar expedientes a formato CSV.

    Args:
        expedientes: Lista de expedientes
        ruta: Ruta del archivo de salida

    Returns:
        Path del archivo generado

    Raises:
        IOError: Si hay error al escribir el archivo
    """
    import csv

    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exportando a CSV: {ruta}")

        if not expedientes:
            logger.warning("No hay expedientes para exportar")
            # Crear archivo vacío
            with open(ruta, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Número", "Carátula", "Dependencia", "Situación", "Última Actuación"])
            return ruta

        # Determinar campos del CSV
        fieldnames = list(expedientes[0].keys())

        with open(ruta, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(expedientes)

        logger.info(f"✅ CSV exportado exitosamente: {ruta} ({len(expedientes)} expedientes)")
        return ruta

    except Exception as e:
        logger.error(f"Error exportando a CSV: {e}")
        raise IOError(f"Error al exportar CSV: {e}")


def exportar_csv_resultados(resultados: List[Dict], ruta: Path) -> Path:
    """
    Exportar resultados de procesamiento a CSV.

    Args:
        resultados: Lista de resultados de procesamiento
        ruta: Ruta del archivo de salida

    Returns:
        Path del archivo generado

    Raises:
        IOError: Si hay error al escribir el archivo
    """
    import csv

    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Exportando resultados a CSV: {ruta}")

        if not resultados:
            logger.warning("No hay resultados para exportar")
            with open(ruta, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Número", "Estado", "Mensaje", "Error", "Timestamp", "Duración (s)"])
            return ruta

        fieldnames = ["numero", "estado", "mensaje", "error", "timestamp", "duracion_segundos"]

        with open(ruta, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # Escribir header con nombres amigables
            writer.writerow({
                "numero": "Número",
                "estado": "Estado",
                "mensaje": "Mensaje",
                "error": "Error",
                "timestamp": "Timestamp",
                "duracion_segundos": "Duración (s)"
            })

            writer.writerows(resultados)

        logger.info(f"✅ CSV resultados exportado: {ruta} ({len(resultados)} resultados)")
        return ruta

    except Exception as e:
        logger.error(f"Error exportando resultados a CSV: {e}")
        raise IOError(f"Error al exportar CSV: {e}")


def generar_estadisticas(expedientes: List[Dict]) -> Dict:
    """
    Generar estadísticas de expedientes.

    Args:
        expedientes: Lista de expedientes

    Returns:
        Diccionario con estadísticas detalladas
    """
    logger.info(f"Generando estadísticas de {len(expedientes)} expedientes")

    total = len(expedientes)

    if total == 0:
        return {
            "total": 0,
            "por_dependencia": {},
            "por_situacion": {},
            "fecha_generacion": datetime.now().isoformat()
        }

    # Agrupar por dependencia
    por_dependencia = {}
    for exp in expedientes:
        dep = exp.get("dependencia", "Sin dependencia")
        por_dependencia[dep] = por_dependencia.get(dep, 0) + 1

    # Agrupar por situación
    por_situacion = {}
    for exp in expedientes:
        sit = exp.get("situacion", "Sin situación")
        por_situacion[sit] = por_situacion.get(sit, 0) + 1

    # Estadísticas de carátulas (top 10 palabras más comunes)
    palabras_caratulas = {}
    for exp in expedientes:
        caratula = exp.get("caratula", "")
        palabras = caratula.upper().split()
        for palabra in palabras:
            # Filtrar palabras cortas y comunes
            if len(palabra) > 3 and palabra not in ["SOBRE", "PARA", "CONTRA"]:
                palabras_caratulas[palabra] = palabras_caratulas.get(palabra, 0) + 1

    # Top 10 palabras
    top_palabras = sorted(palabras_caratulas.items(), key=lambda x: x[1], reverse=True)[:10]

    estadisticas = {
        "total": total,
        "por_dependencia": dict(sorted(por_dependencia.items(), key=lambda x: x[1], reverse=True)),
        "por_situacion": dict(sorted(por_situacion.items(), key=lambda x: x[1], reverse=True)),
        "top_palabras_caratulas": dict(top_palabras),
        "fecha_generacion": datetime.now().isoformat()
    }

    logger.info(f"✅ Estadísticas generadas: {len(por_dependencia)} dependencias, {len(por_situacion)} situaciones")
    return estadisticas


def generar_reporte_html(resumen: Dict, ruta: Path) -> Path:
    """
    Generar reporte HTML con estadísticas visuales.

    Args:
        resumen: Diccionario con resumen del batch
        ruta: Ruta del archivo de salida

    Returns:
        Path del archivo generado

    Raises:
        IOError: Si hay error al escribir el archivo
    """
    try:
        ruta.parent.mkdir(parents=True, exist_ok=True)

        logger.info(f"Generando reporte HTML: {ruta}")

        # Calcular porcentajes
        total = resumen.get("total", 0)
        exitosos = resumen.get("exitosos", 0)
        errores = resumen.get("errores", 0)
        omitidos = resumen.get("omitidos", 0)

        porcentaje_exito = (exitosos / total * 100) if total > 0 else 0
        porcentaje_error = (errores / total * 100) if total > 0 else 0

        # Generar HTML
        html = f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reporte de Extracción Masiva</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 3px solid #4CAF50; padding-bottom: 10px; }}
        .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 30px 0; }}
        .stat-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; text-align: center; }}
        .stat-card.success {{ background: linear-gradient(135deg, #4CAF50 0%, #8BC34A 100%); }}
        .stat-card.error {{ background: linear-gradient(135deg, #f44336 0%, #e91e63 100%); }}
        .stat-card.info {{ background: linear-gradient(135deg, #2196F3 0%, #00BCD4 100%); }}
        .stat-value {{ font-size: 36px; font-weight: bold; margin: 10px 0; }}
        .stat-label {{ font-size: 14px; opacity: 0.9; }}
        .progress-bar {{ width: 100%; height: 30px; background: #e0e0e0; border-radius: 15px; overflow: hidden; margin: 20px 0; }}
        .progress-fill {{ height: 100%; background: linear-gradient(90deg, #4CAF50, #8BC34A); transition: width 0.3s; }}
        .info-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
        .info-table td {{ padding: 10px; border-bottom: 1px solid #ddd; }}
        .info-table td:first-child {{ font-weight: bold; width: 200px; }}
        .timestamp {{ color: #666; font-size: 12px; text-align: center; margin-top: 30px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Reporte de Extracción Masiva</h1>

        <div class="stats">
            <div class="stat-card info">
                <div class="stat-label">Total Procesados</div>
                <div class="stat-value">{total}</div>
            </div>
            <div class="stat-card success">
                <div class="stat-label">Exitosos</div>
                <div class="stat-value">{exitosos}</div>
                <div class="stat-label">{porcentaje_exito:.1f}%</div>
            </div>
            <div class="stat-card error">
                <div class="stat-label">Errores</div>
                <div class="stat-value">{errores}</div>
                <div class="stat-label">{porcentaje_error:.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Omitidos</div>
                <div class="stat-value">{omitidos}</div>
            </div>
        </div>

        <h2>Progreso</h2>
        <div class="progress-bar">
            <div class="progress-fill" style="width: {porcentaje_exito}%"></div>
        </div>

        <h2>Información Detallada</h2>
        <table class="info-table">
            <tr>
                <td>Duración Total</td>
                <td>{resumen.get('duracion_segundos', 0):.2f} segundos</td>
            </tr>
            <tr>
                <td>Velocidad Promedio</td>
                <td>{resumen.get('velocidad_promedio', 0):.2f} expedientes/minuto</td>
            </tr>
            <tr>
                <td>Inicio</td>
                <td>{resumen.get('tiempo_inicio', 'N/A')}</td>
            </tr>
            <tr>
                <td>Fin</td>
                <td>{resumen.get('tiempo_fin', 'N/A')}</td>
            </tr>
        </table>

        <div class="timestamp">
            Reporte generado el {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
        </div>
    </div>
</body>
</html>
"""

        with open(ruta, "w", encoding="utf-8") as f:
            f.write(html)

        logger.info(f"✅ Reporte HTML generado: {ruta}")
        return ruta

    except Exception as e:
        logger.error(f"Error generando reporte HTML: {e}")
        raise IOError(f"Error al generar HTML: {e}")
