from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class UsuarioBase(BaseModel):
    username: str
    tipo_usuario: Literal["paciente", "medico", "admin"]
    foto_perfil_url: Optional[str] = None
    estado: bool = True


class UsuarioCreate(UsuarioBase):
    password: str = Field(..., min_length=6)


class UsuarioResponse(UsuarioBase):
    id: int
    created_at: datetime
    
    # Datos adicionales del perfil
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    email: Optional[str] = None
    telefono: Optional[str] = None
    
    # IDs de perfil específico
    paciente_id: Optional[int] = None
    medico_id: Optional[int] = None
    admin_id: Optional[int] = None

    class Config:
        from_attributes = True
