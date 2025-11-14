from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class AsignacionBase(BaseModel):
    medico_id: int
    paciente_id: int

class AsignacionCreate(AsignacionBase):
    pass

class AsignacionResponse(AsignacionBase):
    id: int
    created_at: datetime
    
    medico_nombre: Optional[str] = None
    medico_apellido: Optional[str] = None
    paciente_nombre: Optional[str] = None
    paciente_apellido: Optional[str] = None

    class Config:
        from_attributes = True