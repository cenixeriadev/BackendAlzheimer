from pydantic import BaseModel
from typing import Optional, Dict, Any, List

class AnalisisResponse(BaseModel):
    resultado: str
    confianza: str
    output_image: Optional[str] = None
    dynamic_crop: Optional[str] = None
    diagnostico_id: Optional[int] = 0  #  opcional
    datos_roboflow: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True

class DiagnosticoResponse(BaseModel):
    id: int
    paciente_id: int
    imagen_url: str
    resultado_ia: str
    confianza_ia: float
    estado: str
    created_at: str

    class Config:
        from_attributes = True