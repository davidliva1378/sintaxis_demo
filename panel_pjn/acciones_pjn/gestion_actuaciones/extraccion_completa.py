import os
import json
import logging
from panel_pjn.acciones_pjn.gestion_actuaciones.extraccion_v2 import obtener_actuaciones_todas_paginas_async #ref
from panel_pjn.acciones_pjn.gestion_actuaciones.bk.historicas import extraer_actuaciones_historicas #ref

# Importar procesamiento inteligente (opcional)
try:
    from panel_pjn.acciones_pjn.gestion_actuaciones.procesamiento import ProcesadorActuacionesExtraccion
    PROCESAMIENTO_DISPONIBLE = True
except ImportError as e:
    logging.warning(f"Procesamiento inteligente no disponible: {e}")
    PROCESAMIENTO_DISPONIBLE = False


async def extraer_actuaciones_completas(
    page_expediente,
    expediente_datos: dict,
    incluir_historicas: bool = True,
    directorio_base: str = "ActuacionesCompletas",
    procesar_actuaciones: bool = True
) -> tuple[list[dict], list[dict], str | None, dict | None]:
    """
    Extrae actuaciones actuales e históricas (opcional) de un expediente y las guarda como JSON.
    También genera un único archivo con estructura detallada, campo EsHistorica y Descargado.

    Args:
        page_expediente: Página de Playwright con expediente abierto
        expediente_datos: Dict con datos del expediente (numero, caratula, etc.)
        incluir_historicas: Si incluir actuaciones históricas (default: True)
        directorio_base: Directorio base para guardar archivos (default: "ActuacionesCompletas")
        procesar_actuaciones: Si procesar con módulo procesador_pdf (default: True)

    Returns:
        tuple: (actuaciones_actuales, actuaciones_historicas, error, estadisticas_procesamiento)
            - estadisticas_procesamiento: Dict con stats si procesar_actuaciones=True, None en caso contrario
    """
    actuaciones_actuales = []
    actuaciones_historicas = []

    try:
        numero_original = expediente_datos['numero']
        numero_normalizado = numero_original.replace('/', '_')
        carpeta_expte = os.path.join(directorio_base, numero_normalizado)

        # Actuaciones actuales
        actuaciones_actuales, error_actuales, carpeta_final = await obtener_actuaciones_todas_paginas_async(
            page_expediente,
            expediente_datos,
            carpeta_destino=carpeta_expte
        )
        if error_actuales:
            return [], [], f"Error al extraer actuaciones actuales: {error_actuales}", None

        for act in actuaciones_actuales:
            act["EsHistorica"] = False
            if act.get("TieneArchivo"):
                act["Descargado"] = False

        indice_base = len(actuaciones_actuales) + 1

        # Actuaciones históricas (si corresponde)
        if incluir_historicas:
            actuaciones_historicas, error_hist = await extraer_actuaciones_historicas(
                page_expediente, expediente_datos, indice_base
            )
            if error_hist:
                return actuaciones_actuales, [], f"Error al extraer actuaciones históricas: {error_hist}", None

            for act in actuaciones_historicas:
                act["EsHistorica"] = True
                if act.get("TieneArchivo"):
                    act["Descargado"] = False
        else:
            actuaciones_historicas = []

        todas = actuaciones_actuales + actuaciones_historicas

        if actuaciones_historicas:
            indice_historico_esperado = len(actuaciones_actuales) + 1
            primer_indice_historico = actuaciones_historicas[0].get("Indice")
            if primer_indice_historico != indice_historico_esperado:
                print(
                    "⚠️ Verificar numeración histórica: se esperaba que iniciara en "
                    f"{indice_historico_esperado}, pero comenzó en {primer_indice_historico}."
                )

        expediente_info = {
            "numero": expediente_datos.get("numero"),
            "caratula": expediente_datos.get("caratula"),
            "dependencia": expediente_datos.get("dependencia"),
            "jurisdiccion": expediente_datos.get("jurisdiccion"),
            "situacion": expediente_datos.get("situacion"),
            "Cantidad de Actuaciones Obtenidas": len(todas),
            "Cantidad de Archivos Descargados": sum(1 for a in todas if a.get("TieneArchivo"))
        }

        estructura_json = {
            "Expediente": expediente_info,
            "Actuaciones": todas
        }

        json_path = os.path.join(carpeta_final, f"actuaciones-{numero_normalizado}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(estructura_json, f, indent=2, ensure_ascii=False)
        print(f"📄 JSON generado: {json_path}")

        # PROCESAMIENTO INTELIGENTE (si está habilitado)
        estadisticas_procesamiento = None
        if procesar_actuaciones and PROCESAMIENTO_DISPONIBLE:
            try:
                print("🔄 Iniciando procesamiento inteligente de actuaciones...")
                procesador = ProcesadorActuacionesExtraccion()
                data_procesada = procesador.procesar_archivo_json(json_path)

                estadisticas_procesamiento = data_procesada["Procesamiento"]["Estadisticas"]

                print("\n" + "="*60)
                print("✅ PROCESAMIENTO COMPLETADO")
                print("="*60)
                print(f"Total actuaciones:        {estadisticas_procesamiento['Total']}")
                print(f"Utilidad ALTA:            {estadisticas_procesamiento['UtilidadAlta']}")
                print(f"Utilidad MEDIA:           {estadisticas_procesamiento['UtilidadMedia']}")
                print(f"Utilidad BAJA:            {estadisticas_procesamiento['UtilidadBaja']}")
                print(f"Utilidad NULA:            {estadisticas_procesamiento['UtilidadNula']}")
                print(f"Con vencimientos:         {estadisticas_procesamiento['ConVencimientos']}")
                print(f"Vencimientos urgentes:    {estadisticas_procesamiento['VencimientosUrgentes']}")
                print(f"Duplicados detectados:    {estadisticas_procesamiento['Duplicados']}")
                print(f"Reducción estimada:       {estadisticas_procesamiento['PorcentajeReduccion']}%")
                print("="*60 + "\n")

            except Exception as e:
                print(f"⚠️ Error en procesamiento inteligente (extracción completada): {e}")
                estadisticas_procesamiento = None
        elif procesar_actuaciones and not PROCESAMIENTO_DISPONIBLE:
            print("⚠️ Procesamiento inteligente no disponible (módulo procesador_pdf no encontrado)")

        return actuaciones_actuales, actuaciones_historicas, None, estadisticas_procesamiento

    except Exception as e:
        return [], [], f"Error general: {type(e).__name__}: {str(e)}", None


