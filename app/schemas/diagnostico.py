from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class DiagnosticoBase(BaseModel):
    paciente_id: int
    imagen_url: Optional[str] = None
    notas_medico: Optional[str] = None

class DiagnosticoCreate(DiagnosticoBase):
    pass

class DiagnosticoResponse(DiagnosticoBase):
    id: int
    resultado_ia: Optional[str] = None
    confianza_ia: Optional[float] = None
    estado: str = "pendiente"
    created_at: datetime
    
    class Config:
        from_attributes = True

class AnalisisRequest(BaseModel):
    paciente_id: int

class AnalisisResponse(BaseModel):
    resultado: str
    confianza: str
    output_image: Optional[str] = None
    dynamic_crop: Optional[str] = None
    diagnostico_id: int