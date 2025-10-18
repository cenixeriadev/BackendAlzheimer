from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal
from datetime import date


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None
    tipo_usuario: Optional[str] = None


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    tipo_usuario: Literal["paciente", "cuidador", "medico", "admin"]
    
    # Datos específicos según tipo de usuario
    nombre: str = Field(..., min_length=2, max_length=100)
    apellido: str = Field(..., min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    
    # Campos específicos para Paciente
    fecha_nacimiento: Optional[date] = None
    genero: Optional[str] = None
    numero_identidad: Optional[str] = None
    direccion: Optional[str] = None
    ciudad: Optional[str] = None
    estado_alzheimer: Optional[Literal["independiente", "con_cuidador"]] = None
    
    # Campos específicos para Cuidador
    relacion_paciente: Optional[str] = None
    
    # Campos específicos para Médico
    cmp: Optional[str] = None
    especialidad: Optional[str] = None
    hospital_afiliacion: Optional[str] = None
    
    # Campos específicos para Admin
    nivel_acceso: Optional[Literal["total", "limitado"]] = "total"
    permisos: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "username": "juan_perez",
                "password": "password123",
                "tipo_usuario": "paciente",
                "nombre": "Juan",
                "apellido": "Pérez",
                "email": "juan@example.com",
                "telefono": "987654321",
                "fecha_nacimiento": "1950-05-15",
                "genero": "Masculino",
                "numero_identidad": "12345678",
                "ciudad": "Lima"
            }
        }
