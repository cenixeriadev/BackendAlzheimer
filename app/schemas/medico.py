from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class MedicoBase(BaseModel):
    nombre: str
    apellido: str
    cmp: str
    especialidad: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    hospital_afiliacion: Optional[str] = None

class MedicoResponse(MedicoBase):
    id: int

    class Config:
        from_attributes = True

class MedicoDetalleResponse(MedicoResponse):
    estadisticas: Dict[str, Any]

    class Config:
        from_attributes = True

class PacienteMedicoResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    email: Optional[str]
    telefono: Optional[str]
    edad: Optional[int]
    estado_alzheimer: Optional[str]
    ultimo_diagnostico: Optional[str]
    fecha_ultimo_diagnostico: Optional[datetime]
    proxima_cita: Optional[datetime]

    class Config:
        from_attributes = True