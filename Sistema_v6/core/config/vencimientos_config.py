import json
import os
from typing import List, Dict, Optional
from pydantic import BaseModel

CONFIG_PATH = "config/vencimientos.json"

SYSTEM_PROMPT_BASE = """Eres un experto legal. Analiza el texto y extrae FECHAS DE NOTIFICACIÓN y PLAZOS.
Formato JSON requerido:
{
  "vencimientos": [
    {
      "fecha_notificacion": "YYYY-MM-DD",
      "tipo": "CEDULA_ELECTRONICA" | "CEDULA_FISICA" | "TRASLADO" | "OTRO",
      "plazo_dias": int,
      "dias_habiles": true,
      "texto_fuente": "..."
    }
  ]
}
Si no hay vencimientos, devuelve lista vacía."""

class VencimientosConfigModel(BaseModel):
    hybrid_analysis_enabled: bool = False
    analysis_margin_days: int = 7
    llm_model: Optional[str] = None
    system_prompt: str = SYSTEM_PROMPT_BASE
    custom_terms: List[Dict] = []

class VencimientosConfig:
    _instance = None

    def __init__(self):
        self._config = VencimientosConfigModel()
        self.load()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load(self):
        if os.path.exists(CONFIG_PATH):
            try:
                with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._config = VencimientosConfigModel(**data)
            except Exception as e:
                print(f"Error loading vencimientos config: {e}")

    def save(self):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(self._config.dict(), f, indent=2, ensure_ascii=False)

    @property
    def config(self) -> VencimientosConfigModel:
        return self._config

    def update(self, data: Dict):
        # Update fields
        current_data = self._config.dict()
        current_data.update(data)
        self._config = VencimientosConfigModel(**current_data)
        self.save()
