from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

from application.services.ia.ia_integration_service import get_ia_integration_service, IAIntegrationService

router = APIRouter(prefix="/classification", tags=["classification"])

class RulePattern(BaseModel):
    texto: str
    confianza: float

class ClassificationConfig(BaseModel):
    threshold: float
    model: Optional[str] = None

class ClassificationRule(BaseModel):
    tipo: str
    patrones: List[RulePattern]

class RulesResponse(BaseModel):
    rules: List[ClassificationRule]
    config: ClassificationConfig

class RulesUpdate(BaseModel):
    rules: Optional[List[ClassificationRule]] = None
    config: Optional[ClassificationConfig] = None

class TestRequest(BaseModel):
    texto: str
    contexto: Optional[str] = None

class TestResponse(BaseModel):
    tipo: str
    confianza: float
    justificacion: str
    metodo: str

def get_ia_service():
    service = get_ia_integration_service()
    if not service:
        raise HTTPException(status_code=503, detail="IA Service not available")
    return service

@router.get("/rules", response_model=RulesResponse)
async def get_rules(service: IAIntegrationService = Depends(get_ia_service)):
    """Obtiene las reglas y configuración de clasificación actuales."""
    if not service.clasificador:
        raise HTTPException(status_code=503, detail="Clasificador not initialized")
    
    data = service.clasificador.get_rules()
    return data

@router.post("/rules", response_model=bool)
async def update_rules(
    update: RulesUpdate,
    service: IAIntegrationService = Depends(get_ia_service)
):
    """Actualiza las reglas y configuración de clasificación."""
    if not service.clasificador:
        raise HTTPException(status_code=503, detail="Clasificador not initialized")
    
    # Convertir Pydantic models a dicts
    update_data = {}
    if update.rules is not None:
        update_data["rules"] = [rule.dict() for rule in update.rules]
    if update.config is not None:
        update_data["config"] = update.config.dict()
    
    success = service.clasificador.update_rules(update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to save rules")
    
    return True

@router.post("/test", response_model=TestResponse)
async def test_classification(
    request: TestRequest,
    service: IAIntegrationService = Depends(get_ia_service)
):
    """Prueba la clasificación con un texto."""
    if not service.clasificador:
        raise HTTPException(status_code=503, detail="Clasificador not initialized")
    
    result = service.clasificador.clasificar(
        texto=request.texto,
        contexto=request.contexto,
        usar_llm=True
    )
    
    return result
