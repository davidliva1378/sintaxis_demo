"""
Router de API REST para servicios de IA.

Proporciona endpoints para:
- Clasificación de actuaciones
- Extracción de entidades (NER)
- Búsqueda semántica (RAG)
- Generación de texto (LLM)
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# === Función para obtener estadísticas del sistema ===

def _get_system_stats() -> dict:
    """Obtiene estadísticas del sistema para el contexto del LLM."""
    try:
        from infrastructure.persistence.database import get_database_connection

        conn = get_database_connection()
        cursor = conn.cursor(dictionary=True)

        stats = {}

        # Total de expedientes
        cursor.execute("SELECT COUNT(*) as total FROM expedientes")
        result = cursor.fetchone()
        stats["total_expedientes"] = result["total"] if result else 0

        # Total de actuaciones
        cursor.execute("SELECT COUNT(*) as total FROM actuaciones")
        result = cursor.fetchone()
        stats["total_actuaciones"] = result["total"] if result else 0

        # Expedientes por estado (si existe el campo)
        try:
            cursor.execute("""
                SELECT estado, COUNT(*) as total
                FROM expedientes
                GROUP BY estado
            """)
            estados = cursor.fetchall()
            stats["expedientes_por_estado"] = {e["estado"]: e["total"] for e in estados}
        except:
            stats["expedientes_por_estado"] = {}

        # Actuaciones recientes (últimos 7 días)
        try:
            cursor.execute("""
                SELECT COUNT(*) as total
                FROM actuaciones
                WHERE fecha >= DATE_SUB(CURDATE(), INTERVAL 7 DAY)
            """)
            result = cursor.fetchone()
            stats["actuaciones_ultimos_7_dias"] = result["total"] if result else 0
        except:
            stats["actuaciones_ultimos_7_dias"] = 0

        cursor.close()
        conn.close()

        return stats

    except Exception as e:
        logger.warning(f"Error obteniendo estadísticas del sistema: {e}")
        return {
            "total_expedientes": "desconocido",
            "total_actuaciones": "desconocido"
        }

router = APIRouter(prefix="/ia", tags=["IA"])


# === Modelos Pydantic ===

class ClasificarRequest(BaseModel):
    texto: str
    contexto: Optional[str] = None
    usar_llm: bool = True


class ClasificarResponse(BaseModel):
    tipo: str
    confianza: float
    justificacion: str
    metodo: Optional[str] = None


class ClasificarBatchRequest(BaseModel):
    actuaciones: List[dict]
    usar_llm: bool = True


class NERRequest(BaseModel):
    texto: str
    labels: Optional[List[str]] = None


class NERResponse(BaseModel):
    entidades: List[dict]


class BuscarRequest(BaseModel):
    query: str
    n_results: int = 5
    expediente_id: Optional[str] = None
    expediente_numero: Optional[str] = None


class BuscarHibridoRequest(BaseModel):
    query: str
    n_results: int = 5
    expediente_id: Optional[str] = None
    expediente_numero: Optional[str] = None
    use_bm25: bool = True
    use_semantic: bool = True


class BuscarResponse(BaseModel):
    resultados: List[dict]


class PreguntarRequest(BaseModel):
    pregunta: str
    n_contextos: int = 5
    expediente_id: Optional[str] = None


class PreguntarResponse(BaseModel):
    respuesta: str
    confianza: float
    fuentes: List[dict]


class MensajeChat(BaseModel):
    rol: str  # "usuario" o "asistente"
    contenido: str


class ChatRequest(BaseModel):
    mensaje: str
    expediente_numero: Optional[str] = None
    historial: List[MensajeChat] = []
    n_contextos: int = 5
    model: Optional[str] = Field(None, description="Modelo LLM a usar")
    temperature: Optional[float] = Field(None, description="Temperature (0.0-1.0)", ge=0.0, le=1.0)


class ChatResponse(BaseModel):
    respuesta: str
    fuentes: List[dict]


class IndexarRequest(BaseModel):
    id: str
    texto: str
    metadata: Optional[dict] = None


class GenerarRequest(BaseModel):
    prompt: str
    system: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000


class GenerarResponse(BaseModel):
    texto: str


class ResumirRequest(BaseModel):
    texto: str
    max_length: int = 200


# === Servicios (lazy loading) ===

_clasificador = None
_ner = None
_rag = None
_llm = None


def get_clasificador():
    global _clasificador
    if _clasificador is None:
        from application.services.ia import ClasificadorService
        _clasificador = ClasificadorService()
    return _clasificador


def get_ner():
    global _ner
    if _ner is None:
        from application.services.ia import NERService
        _ner = NERService()
    return _ner


def get_rag():
    global _rag
    if _rag is None:
        from application.services.ia import RAGService
        _rag = RAGService()
    return _rag


def get_llm():
    global _llm
    if _llm is None:
        from infrastructure.rag.services.llm_service import LLMService
        _llm = LLMService()
    return _llm


# === Endpoints de Clasificación ===

@router.post("/clasificar", response_model=ClasificarResponse)
async def clasificar_actuacion(request: ClasificarRequest):
    """
    Clasifica una actuación judicial.

    Utiliza reglas y opcionalmente LLM para determinar el tipo.
    """
    try:
        clasificador = get_clasificador()
        resultado = clasificador.clasificar(
            texto=request.texto,
            contexto=request.contexto,
            usar_llm=request.usar_llm
        )
        return ClasificarResponse(**resultado)

    except Exception as e:
        logger.error(f"Error clasificando: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/clasificar/batch")
async def clasificar_batch(request: ClasificarBatchRequest):
    """
    Clasifica múltiples actuaciones.
    """
    try:
        clasificador = get_clasificador()
        resultados = clasificador.clasificar_batch(
            actuaciones=request.actuaciones,
            usar_llm=request.usar_llm
        )
        return {"resultados": resultados}

    except Exception as e:
        logger.error(f"Error en clasificación batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tipos-actuacion")
async def get_tipos_actuacion():
    """
    Obtiene los tipos de actuación disponibles.
    """
    clasificador = get_clasificador()
    return {"tipos": clasificador.get_tipos()}


# === Endpoints de NER ===

@router.post("/ner/extraer", response_model=NERResponse)
async def extraer_entidades(request: NERRequest):
    """
    Extrae entidades de un texto jurídico.
    """
    try:
        ner = get_ner()
        entidades = ner.extract(
            text=request.texto,
            labels=request.labels
        )
        return NERResponse(entidades=entidades)

    except Exception as e:
        logger.error(f"Error en NER: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ner/juridico")
async def extraer_entidades_juridicas(request: NERRequest):
    """
    Extrae entidades jurídicas agrupadas por tipo.
    """
    try:
        ner = get_ner()
        resultado = ner.extract_juridico(request.texto)
        return {"entidades": resultado}

    except Exception as e:
        logger.error(f"Error en NER jurídico: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ner/partes")
async def extraer_partes(request: NERRequest):
    """
    Extrae las partes procesales de un texto.
    """
    try:
        ner = get_ner()
        resultado = ner.extract_partes(request.texto)
        return resultado

    except Exception as e:
        logger.error(f"Error extrayendo partes: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Endpoints de RAG ===

@router.post("/rag/buscar", response_model=BuscarResponse)
async def buscar_semantico(request: BuscarRequest):
    """
    Realiza búsqueda semántica en las actuaciones indexadas.
    """
    try:
        rag = get_rag()
        resultados = rag.buscar(
            query=request.query,
            n_results=request.n_results,
            expediente_id=request.expediente_id,
            expediente_numero=request.expediente_numero
        )
        return BuscarResponse(resultados=resultados)

    except Exception as e:
        logger.error(f"Error en búsqueda: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/buscar-hibrido", response_model=BuscarResponse)
async def buscar_hibrido(request: BuscarHibridoRequest):
    """
    Realiza búsqueda híbrida (BM25 + Semántica) en las actuaciones.

    Combina resultados de búsqueda por keywords y semántica usando
    Reciprocal Rank Fusion (RRF) para mejores resultados.
    """
    try:
        rag = get_rag()
        resultados = rag.buscar_hibrido(
            query=request.query,
            n_results=request.n_results,
            expediente_id=request.expediente_id,
            expediente_numero=request.expediente_numero,
            use_bm25=request.use_bm25,
            use_semantic=request.use_semantic
        )
        return BuscarResponse(resultados=resultados)

    except Exception as e:
        logger.error(f"Error en búsqueda híbrida: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rag/preguntar", response_model=PreguntarResponse)
async def preguntar(request: PreguntarRequest):
    """
    Responde una pregunta usando RAG.
    """
    try:
        rag = get_rag()
        resultado = rag.responder(
            pregunta=request.pregunta,
            n_contextos=request.n_contextos,
            expediente_id=request.expediente_id
        )
        return PreguntarResponse(**resultado)

    except Exception as e:
        logger.error(f"Error respondiendo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat conversacional con contexto RAG e historial.

    Mantiene el contexto de la conversacion y usa RAG para
    buscar informacion relevante en los expedientes.
    """
    try:
        rag = get_rag()
        llm = get_llm()

        # Obtener estadísticas del sistema
        system_stats = _get_system_stats()

        # Buscar contexto relevante usando RAG
        resultados = rag.buscar_hibrido(
            query=request.mensaje,
            n_results=request.n_contextos,
            expediente_numero=request.expediente_numero
        )

        # Construir contexto de documentos
        contexto_docs = ""
        fuentes = []
        for i, r in enumerate(resultados, 1):
            contexto_docs += f"\n[Documento {i}]: {r.get('document', '')[:500]}...\n"
            fuentes.append({
                "id": r.get("id", ""),
                "fragmento": r.get("document", "")[:200],
                "score": r.get("hybrid_score", r.get("score", 0)),
                "expediente": r.get("metadata", {}).get("expediente_numero", "")
            })

        # Construir historial de conversacion
        historial_texto = ""
        for msg in request.historial[-6:]:  # Ultimos 6 mensajes
            rol = "Usuario" if msg.rol == "usuario" else "Asistente"
            historial_texto += f"{rol}: {msg.contenido}\n"

        # Construir estadísticas del sistema para el contexto
        stats_texto = f"""Estadísticas del sistema:
- Total de expedientes en el sistema: {system_stats.get('total_expedientes', 'desconocido')}
- Total de actuaciones registradas: {system_stats.get('total_actuaciones', 'desconocido')}
- Actuaciones en los últimos 7 días: {system_stats.get('actuaciones_ultimos_7_dias', 'desconocido')}"""

        # Agregar estados si hay información
        estados = system_stats.get('expedientes_por_estado', {})
        if estados:
            stats_texto += "\n- Expedientes por estado: " + ", ".join(
                [f"{k}: {v}" for k, v in estados.items()]
            )

        # Construir prompt para el LLM mejorado
        system_prompt = f"""Eres un asistente jurídico especializado en expedientes judiciales argentinos del Poder Judicial de la Nación (PJN).

INFORMACIÓN DEL SISTEMA:
{stats_texto}

INSTRUCCIONES:
1. Responde de forma clara, precisa y profesional en español.
2. Basa tus respuestas en el contexto de documentos proporcionado cuando sea relevante.
3. Si te preguntan sobre estadísticas del sistema (cantidad de expedientes, actuaciones, etc.), usa la información del sistema proporcionada arriba.
4. Cuando cites información de documentos, indica de qué documento proviene (ej: "Según el Documento 1...").
5. Si no encuentras información relevante en los documentos Y no puedes responder con la información del sistema, indica claramente que no tienes datos suficientes.
6. Sé conciso pero completo. Usa listas cuando sea apropiado.
7. Para preguntas sobre plazos o vencimientos, sé especialmente preciso con las fechas.

CONTEXTO ACTUAL:
- Fecha actual: {__import__('datetime').datetime.now().strftime('%d/%m/%Y')}"""

        if request.expediente_numero:
            system_prompt += f"\n- Expediente en consulta: {request.expediente_numero}"

        user_prompt = f"""DOCUMENTOS RELEVANTES:
{contexto_docs if contexto_docs else "No se encontraron documentos específicos para esta consulta."}

HISTORIAL DE CONVERSACIÓN:
{historial_texto if historial_texto else "Sin historial previo."}

PREGUNTA DEL USUARIO: {request.mensaje}

RESPUESTA:"""

        # Generar respuesta
        respuesta = llm.generate(
            prompt=user_prompt,
            system=system_prompt,
            temperature=0.3,
            max_tokens=1000
        )

        return ChatResponse(
            respuesta=respuesta,
            fuentes=fuentes
        )

    except Exception as e:
        logger.error(f"Error en chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Chat conversacional con streaming (SSE).

    Retorna la respuesta token por token en tiempo real.
    """
    import json

    async def generate_stream():
        try:
            rag = get_rag()
            llm = get_llm()

            # Aplicar modelo si se especificó en el request
            if request.model:
                llm.model = request.model

            # Usar temperature del request o default
            use_temp = request.temperature if request.temperature is not None else 0.3

            # Obtener estadísticas del sistema
            system_stats = _get_system_stats()

            # Buscar contexto relevante usando RAG
            resultados = rag.buscar_hibrido(
                query=request.mensaje,
                n_results=request.n_contextos,
                expediente_numero=request.expediente_numero
            )

            # Construir contexto de documentos
            contexto_docs = ""
            fuentes = []
            for i, r in enumerate(resultados, 1):
                contexto_docs += f"\n[Documento {i}]: {r.get('document', '')[:500]}...\n"
                fuentes.append({
                    "id": r.get("id", ""),
                    "fragmento": r.get("document", "")[:200],
                    "score": r.get("hybrid_score", r.get("score", 0)),
                    "expediente": r.get("metadata", {}).get("expediente_numero", "")
                })

            # Enviar fuentes primero
            yield f"data: {json.dumps({'type': 'fuentes', 'data': fuentes})}\n\n"

            # Construir historial de conversacion
            historial_texto = ""
            for msg in request.historial[-6:]:
                rol = "Usuario" if msg.rol == "usuario" else "Asistente"
                historial_texto += f"{rol}: {msg.contenido}\n"

            # Construir estadísticas del sistema para el contexto
            stats_texto = f"""Estadísticas del sistema:
- Total de expedientes en el sistema: {system_stats.get('total_expedientes', 'desconocido')}
- Total de actuaciones registradas: {system_stats.get('total_actuaciones', 'desconocido')}
- Actuaciones en los últimos 7 días: {system_stats.get('actuaciones_ultimos_7_dias', 'desconocido')}"""

            estados = system_stats.get('expedientes_por_estado', {})
            if estados:
                stats_texto += "\n- Expedientes por estado: " + ", ".join(
                    [f"{k}: {v}" for k, v in estados.items()]
                )

            # Construir prompt para el LLM
            system_prompt = f"""Eres un asistente jurídico especializado en expedientes judiciales argentinos del Poder Judicial de la Nación (PJN).

INFORMACIÓN DEL SISTEMA:
{stats_texto}

INSTRUCCIONES:
1. Responde de forma clara, precisa y profesional en español.
2. Basa tus respuestas en el contexto de documentos proporcionado cuando sea relevante.
3. Si te preguntan sobre estadísticas del sistema, usa la información del sistema proporcionada arriba.
4. Cuando cites información de documentos, indica de qué documento proviene.
5. Si no encuentras información relevante, indica claramente que no tienes datos suficientes.
6. Sé conciso pero completo.

CONTEXTO ACTUAL:
- Fecha actual: {__import__('datetime').datetime.now().strftime('%d/%m/%Y')}"""

            if request.expediente_numero:
                system_prompt += f"\n- Expediente en consulta: {request.expediente_numero}"

            user_prompt = f"""DOCUMENTOS RELEVANTES:
{contexto_docs if contexto_docs else "No se encontraron documentos específicos."}

HISTORIAL DE CONVERSACIÓN:
{historial_texto if historial_texto else "Sin historial previo."}

PREGUNTA DEL USUARIO: {request.mensaje}

RESPUESTA:"""

            # Stream de la respuesta
            for chunk in llm.stream(user_prompt, system=system_prompt, temperature=use_temp):
                yield f"data: {json.dumps({'type': 'token', 'data': chunk})}\n\n"

            # Indicar fin del stream
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Error en chat stream: {e}")
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.post("/rag/indexar")
async def indexar_actuacion(
    request: IndexarRequest,
    background_tasks: BackgroundTasks
):
    """
    Indexa una actuación para búsqueda semántica.
    """
    try:
        rag = get_rag()

        # Indexar en background para no bloquear
        background_tasks.add_task(
            rag.indexar_actuacion,
            id_actuacion=request.id,
            texto=request.texto,
            metadata=request.metadata
        )

        return {"message": f"Indexación iniciada para {request.id}"}

    except Exception as e:
        logger.error(f"Error indexando: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/stats")
async def get_rag_stats():
    """
    Obtiene estadísticas del índice RAG.
    """
    try:
        rag = get_rag()
        return rag.get_stats()

    except Exception as e:
        logger.error(f"Error obteniendo stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rag/resumir/{expediente_id}")
async def resumir_expediente(expediente_id: str, max_length: int = 500):
    """
    Genera un resumen del expediente.
    """
    try:
        rag = get_rag()
        resumen = rag.resumir_expediente(expediente_id, max_length)
        return {"resumen": resumen}

    except Exception as e:
        logger.error(f"Error resumiendo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Endpoints de LLM ===

@router.post("/llm/generar", response_model=GenerarResponse)
async def generar_texto(request: GenerarRequest):
    """
    Genera texto usando el LLM.
    """
    try:
        llm = get_llm()
        texto = llm.generate(
            prompt=request.prompt,
            system=request.system,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return GenerarResponse(texto=texto)

    except Exception as e:
        logger.error(f"Error generando: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/resumir")
async def resumir_texto(request: ResumirRequest):
    """
    Resume un texto usando LLM.
    """
    try:
        llm = get_llm()
        resumen = llm.summarize(
            text=request.texto,
            max_length=request.max_length
        )
        return {"resumen": resumen}

    except Exception as e:
        logger.error(f"Error resumiendo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Endpoints de Estado ===

@router.get("/status")
async def get_ia_status():
    """
    Verifica el estado de los servicios de IA.
    """
    status = {
        "clasificador": "no cargado",
        "ner": "no cargado",
        "rag": "no cargado",
        "llm": "no cargado"
    }

    # Verificar Clasificador
    try:
        clasificador = get_clasificador()
        if clasificador is not None:
            status["clasificador"] = "ok"
    except Exception as e:
        status["clasificador"] = f"error: {str(e)}"

    # Verificar NER
    try:
        ner = get_ner()
        if ner is not None:
            # Verificar si el modelo está disponible (lazy load)
            if hasattr(ner, 'model_name'):
                status["ner"] = "ok"
            else:
                status["ner"] = "disponible"
    except Exception as e:
        status["ner"] = f"error: {str(e)}"

    # Verificar RAG
    try:
        rag = get_rag()
        if rag is not None:
            # Intentar obtener stats para verificar conexión
            try:
                stats = rag.get_stats()
                if stats:
                    status["rag"] = f"ok ({stats.get('total_documents', 0)} docs)"
                else:
                    status["rag"] = "ok"
            except:
                status["rag"] = "disponible"
    except Exception as e:
        status["rag"] = f"error: {str(e)}"

    # Verificar LLM
    try:
        llm = get_llm()
        if llm.is_available():
            status["llm"] = f"ok ({llm.get_current_model()})"
        else:
            status["llm"] = "no disponible"
    except Exception as e:
        status["llm"] = f"error: {str(e)}"

    return status


@router.get("/models")
async def get_available_models():
    """
    Lista los modelos disponibles.
    """
    try:
        # Llamar directamente a la API de Ollama para obtener modelos
        import httpx
        models = []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.warning(f"Error obteniendo modelos de Ollama: {e}")

        # Obtener modelo actual del singleton
        llm = get_llm()
        current = llm.get_current_model()

        # Si no hay modelos pero hay un modelo actual, al menos mostrarlo
        if not models and current:
            models = [current]

        return {
            "models": models,
            "current": current
        }

    except Exception as e:
        logger.error(f"Error listando modelos: {e}")
        return {"models": [], "current": None, "error": str(e)}


class SetModelRequest(BaseModel):
    model: str


@router.post("/models/set")
async def set_model(request: SetModelRequest):
    """
    Cambia el modelo LLM activo.
    """
    try:
        # Obtener lista de modelos disponibles directamente de Ollama
        import httpx
        available_models = []

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:11434/api/tags", timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    available_models = [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.warning(f"Error obteniendo modelos de Ollama: {e}")

        # Verificar si el modelo solicitado esta disponible
        model_available = (
            request.model in available_models or
            f"{request.model}:latest" in available_models
        )

        if model_available:
            # Cambiar el modelo en el singleton
            llm = get_llm()
            llm.model = request.model
            # Resetear el cliente para que se reinicialice con el nuevo modelo
            llm._client = None
            logger.info(f"Modelo cambiado a: {request.model}")

            return {
                "success": True,
                "model": request.model,
                "message": f"Modelo cambiado a {request.model}"
            }
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Modelo {request.model} no disponible. Disponibles: {available_models}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cambiando modelo: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/models/current")
async def get_current_model():
    """
    Obtiene el modelo LLM actualmente configurado.
    """
    try:
        llm = get_llm()
        return {
            "model": llm.get_current_model(),
            "info": llm.get_model_info()
        }

    except Exception as e:
        logger.error(f"Error obteniendo modelo actual: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Nuevos Endpoints: NER Mejorado con LLM ===

class NEREnhancedRequest(BaseModel):
    texto: str
    labels: Optional[List[str]] = None
    use_llm_fallback: Optional[bool] = None
    extract_missing: bool = True


class NEREnhancedResponse(BaseModel):
    entidades: List[dict]
    stats: Optional[dict] = None


@router.post("/ner/extraer-enhanced", response_model=NEREnhancedResponse)
async def extraer_entidades_enhanced(request: NEREnhancedRequest):
    """
    Extrae entidades con mejora LLM para entidades de baja confianza.

    Utiliza GLiNER para extracción rápida y opcionalmente LLM para:
    - Validar/corregir entidades de baja confianza
    - Extraer entidades que GLiNER no detectó

    Cada entidad incluye:
    - source: "gliner", "llm", o "llm_corrected"
    - original_label: Si fue corregida por LLM
    """
    try:
        ner = get_ner()
        entidades = ner.extract_enhanced(
            text=request.texto,
            labels=request.labels,
            use_llm_fallback=request.use_llm_fallback,
            extract_missing=request.extract_missing
        )

        # Calcular stats
        stats = {
            "total": len(entidades),
            "from_gliner": sum(1 for e in entidades if e.get("source") == "gliner"),
            "from_llm": sum(1 for e in entidades if e.get("source") == "llm"),
            "corrected_by_llm": sum(1 for e in entidades if e.get("source") == "llm_corrected"),
        }

        return NEREnhancedResponse(entidades=entidades, stats=stats)

    except Exception as e:
        logger.error(f"Error en NER enhanced: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ner/juridico-enhanced")
async def extraer_entidades_juridicas_enhanced(request: NERRequest):
    """
    Extrae entidades jurídicas con mejora LLM, agrupadas por tipo.

    Incluye metadata de source para cada entidad.
    """
    try:
        ner = get_ner()
        resultado = ner.extract_juridico_enhanced(request.texto)
        return {"entidades": resultado}

    except Exception as e:
        logger.error(f"Error en NER jurídico enhanced: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/ner/info")
async def get_ner_info():
    """
    Obtiene información del servicio NER y configuración de LLM fallback.
    """
    try:
        ner = get_ner()
        return ner.get_model_info()

    except Exception as e:
        logger.error(f"Error obteniendo info NER: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Nuevos Endpoints: Extracción de Relaciones ===

class RelationExtractionRequest(BaseModel):
    texto: str
    entidades: Optional[List[dict]] = None
    extract_entities: bool = True


class RelationExtractionResponse(BaseModel):
    entidades: List[dict]
    relaciones: List[dict]
    graph_data: Optional[dict] = None


_relation_service = None


def get_relation_service():
    global _relation_service
    if _relation_service is None:
        from application.services.ia.relation_extraction_service import RelationExtractionService
        _relation_service = RelationExtractionService()
    return _relation_service


@router.post("/relaciones/extraer", response_model=RelationExtractionResponse)
async def extraer_relaciones(request: RelationExtractionRequest):
    """
    Extrae relaciones entre entidades de un texto jurídico.

    Si no se proporcionan entidades, las extrae automáticamente usando NER.

    Tipos de relaciones detectadas:
    - DEMANDA: Actor demanda a demandado
    - REPRESENTA: Abogado representa a parte
    - JUZGA: Juez/tribunal interviene
    - CITA: Documento cita norma
    - Y más...

    Retorna también datos de grafo para visualización.
    """
    try:
        relation_service = get_relation_service()

        # Si no hay entidades, extraerlas primero
        entidades = request.entidades
        if not entidades and request.extract_entities:
            ner = get_ner()
            entidades = ner.extract_enhanced(
                text=request.texto,
                use_llm_fallback=True
            )

        if not entidades:
            return RelationExtractionResponse(
                entidades=[],
                relaciones=[],
                graph_data=None
            )

        # Extraer relaciones
        result = relation_service.extract_relations(
            text=request.texto,
            entities=entidades
        )

        # Convertir a respuesta
        return RelationExtractionResponse(
            entidades=result.entities,
            relaciones=[
                {
                    "source_entity": r.source_entity,
                    "source_label": r.source_label,
                    "target_entity": r.target_entity,
                    "target_label": r.target_label,
                    "relation_type": r.relation_type,
                    "confidence": r.confidence,
                    "context": r.context
                }
                for r in result.relations
            ],
            graph_data=result.graph_data
        )

    except Exception as e:
        logger.error(f"Error extrayendo relaciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/relaciones/partes-procesales")
async def extraer_partes_procesales(request: RelationExtractionRequest):
    """
    Extrae partes procesales basándose en relaciones entre entidades.

    Identifica:
    - Parte actora
    - Parte demandada
    - Representantes de cada parte
    - Juez/tribunal interviniente
    """
    try:
        relation_service = get_relation_service()

        # Si no hay entidades, extraerlas primero
        entidades = request.entidades
        if not entidades and request.extract_entities:
            ner = get_ner()
            entidades = ner.extract_enhanced(
                text=request.texto,
                use_llm_fallback=True
            )

        if not entidades:
            return {"partes": {}}

        partes = relation_service.extract_partes_procesales(
            text=request.texto,
            entities=entidades
        )

        return {"partes": partes}

    except Exception as e:
        logger.error(f"Error extrayendo partes procesales: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/relaciones/tipos")
async def get_tipos_relaciones():
    """
    Lista los tipos de relaciones que se pueden detectar.
    """
    try:
        from application.services.ia.relation_extraction_service import RelationExtractionService
        return {"tipos": RelationExtractionService.RELATION_TYPES}

    except Exception as e:
        logger.error(f"Error obteniendo tipos de relaciones: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# === Endpoint de Hardware Profile ===

@router.get("/hardware/profile")
async def get_hardware_profile():
    """
    Obtiene información del perfil de hardware activo para IA.
    """
    try:
        from infrastructure.config.hardware_profiles import get_profile_info
        return get_profile_info()

    except Exception as e:
        logger.error(f"Error obteniendo perfil de hardware: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class SetHardwareProfileRequest(BaseModel):
    profile: str = Field(..., description="Nombre del perfil: development, production, production_max")


@router.post("/hardware/profile")
async def set_hardware_profile(request: SetHardwareProfileRequest):
    """
    Cambia el perfil de hardware activo.

    Perfiles disponibles:
    - development: Mac/CPU-only
    - production: Intel i7 + RTX 3060
    - production_max: Hardware de alta gama
    """
    try:
        from infrastructure.config.hardware_profiles import set_active_profile, get_profile_info

        set_active_profile(request.profile)

        return {
            "success": True,
            "profile": get_profile_info()
        }

    except Exception as e:
        logger.error(f"Error cambiando perfil de hardware: {e}")
        raise HTTPException(status_code=500, detail=str(e))
