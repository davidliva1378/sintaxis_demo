import asyncio
import json
import logging
import re
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, HTTPException
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="/logs", tags=["logs"])
logger = logging.getLogger(__name__)

LOG_FILE_PATH = Path("/tmp/sintaxis_backend.log")

# Archivo de configuración de modelo LLM (compartido con ia.py)
_LLM_CONFIG_FILE = Path(__file__).parent.parent.parent.parent.parent / "data" / "llm_config.json"


def _load_saved_model() -> Optional[str]:
    """Carga el modelo guardado del archivo de configuración."""
    try:
        if _LLM_CONFIG_FILE.exists():
            with open(_LLM_CONFIG_FILE, 'r') as f:
                config = json.load(f)
                return config.get('model')
    except Exception as e:
        logger.warning(f"Error cargando configuración de modelo: {e}")
    return None


# ============================================================================
# Modelos
# ============================================================================

class LLMErrorLog(BaseModel):
    """Log de error de LLM."""
    timestamp: str
    level: str
    message: str
    actuacion_id: Optional[int] = None
    error_type: Optional[str] = None


class LLMStatusResponse(BaseModel):
    """Estado del servicio LLM."""
    disponible: bool
    modelo_activo: Optional[str] = None
    modelos_disponibles: List[str] = []
    error: Optional[str] = None
    ollama_url: str = "http://localhost:11434"


# ============================================================================
# Endpoints de diagnóstico LLM
# ============================================================================

@router.get("/llm/status", response_model=LLMStatusResponse)
async def verificar_estado_llm():
    """
    Verifica el estado del servicio LLM (Ollama).

    Útil para diagnosticar por qué el análisis híbrido de vencimientos
    podría estar fallando silenciosamente.
    """
    ollama_url = "http://localhost:11434"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Verificar que Ollama responde
            response = await client.get(f"{ollama_url}/api/tags")

            if response.status_code == 200:
                data = response.json()
                modelos = [m.get("name", "") for m in data.get("models", [])]

                # Cargar modelo guardado en configuración
                saved_model = _load_saved_model()

                # Usar modelo guardado si existe y está disponible, sino el primero
                if saved_model and saved_model in modelos:
                    modelo_activo = saved_model
                elif modelos:
                    modelo_activo = modelos[0]
                else:
                    modelo_activo = None

                return LLMStatusResponse(
                    disponible=True,
                    modelos_disponibles=modelos,
                    modelo_activo=modelo_activo,
                    ollama_url=ollama_url
                )
            else:
                return LLMStatusResponse(
                    disponible=False,
                    error=f"Ollama respondió con status {response.status_code}",
                    ollama_url=ollama_url
                )

    except httpx.ConnectError:
        return LLMStatusResponse(
            disponible=False,
            error="No se puede conectar a Ollama. Ejecutar: ollama serve",
            ollama_url=ollama_url
        )
    except httpx.TimeoutException:
        return LLMStatusResponse(
            disponible=False,
            error="Timeout conectando a Ollama",
            ollama_url=ollama_url
        )
    except Exception as e:
        return LLMStatusResponse(
            disponible=False,
            error=str(e),
            ollama_url=ollama_url
        )


@router.get("/llm/errores", response_model=List[LLMErrorLog])
async def obtener_errores_llm(
    limite: int = Query(50, ge=1, le=500, description="Cantidad máxima de errores"),
    desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)")
):
    """
    Obtiene los logs de errores relacionados con LLM.

    Filtra los logs del backend para encontrar errores de:
    - Conexión a Ollama
    - Análisis híbrido de vencimientos
    - Parsing de respuestas LLM
    """
    errores = []

    if not LOG_FILE_PATH.exists():
        return []

    # Patrones para detectar errores LLM
    patrones_llm = [
        r"LLM no disponible",
        r"Error en análisis híbrido",
        r"Ollama",
        r"Error en llamada LLM",
        r"Respuesta LLM con formato inválido",
        r"Error parseando vencimiento LLM"
    ]
    patron_combinado = re.compile("|".join(patrones_llm), re.IGNORECASE)

    # Patrón para extraer timestamp y nivel
    patron_log = re.compile(
        r"(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})"
        r".*?(WARNING|ERROR|INFO)"
        r".*?:.*?(.+)"
    )

    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="replace") as f:
            for linea in f:
                if patron_combinado.search(linea):
                    match = patron_log.match(linea.strip())
                    if match:
                        timestamp_str = match.group(1)

                        # Filtrar por fecha si se especifica
                        if desde:
                            try:
                                fecha_log = datetime.strptime(timestamp_str[:10], "%Y-%m-%d").date()
                                fecha_desde = datetime.strptime(desde, "%Y-%m-%d").date()
                                if fecha_log < fecha_desde:
                                    continue
                            except ValueError:
                                pass

                        # Extraer actuacion_id si está presente
                        actuacion_id = None
                        id_match = re.search(r"actuaci[oó]n\s*(\d+)", linea, re.IGNORECASE)
                        if id_match:
                            actuacion_id = int(id_match.group(1))

                        # Extraer tipo de error
                        error_type = None
                        if "ConnectionError" in linea:
                            error_type = "ConnectionError"
                        elif "JSONDecodeError" in linea:
                            error_type = "JSONDecodeError"
                        elif "timeout" in linea.lower():
                            error_type = "Timeout"

                        errores.append(LLMErrorLog(
                            timestamp=timestamp_str,
                            level=match.group(2),
                            message=match.group(3).strip()[:300],
                            actuacion_id=actuacion_id,
                            error_type=error_type
                        ))

        # Ordenar por timestamp descendente y limitar
        errores.sort(key=lambda x: x.timestamp, reverse=True)
        return errores[:limite]

    except Exception as e:
        logger.error(f"Error leyendo logs de LLM: {e}")
        raise HTTPException(status_code=500, detail=f"Error leyendo logs: {str(e)}")

@router.websocket("/ws")
async def websocket_logs(websocket: WebSocket):
    await websocket.accept()
    
    try:
        # Check if file exists
        if not LOG_FILE_PATH.exists():
            await websocket.send_text(f"Log file not found at {LOG_FILE_PATH}")
            await websocket.close()
            return

        # Open file and seek to end
        with open(LOG_FILE_PATH, "r", encoding="utf-8", errors="replace") as f:
            # Send last 20 lines initially
            lines = f.readlines()
            last_lines = lines[-20:] if len(lines) > 20 else lines
            for line in last_lines:
                await websocket.send_text(line.strip())
            
            # Seek to end to continue tailing
            f.seek(0, 2)
            
            while True:
                line = f.readline()
                if line:
                    await websocket.send_text(line.strip())
                else:
                    await asyncio.sleep(0.1)
                    
    except WebSocketDisconnect:
        logger.info("Client disconnected from log stream")
    except Exception as e:
        logger.error(f"Error streaming logs: {e}")
        try:
            await websocket.close()
        except:
            pass
