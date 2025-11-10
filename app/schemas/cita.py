from pydantic import BaseModel, Field, validator, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class EstadoCita(str, Enum):
    programada = "programada"
    completada = "completada"
    cancelada = "cancelada"
    reprogramada = "reprogramada"


# Schema base para Cita
class CitaBase(BaseModel):
    paciente_id: int = Field(..., gt=0, description="ID del paciente")
    medico_id: int = Field(..., gt=0, description="ID del médico")
    hospital_id: Optional[int] = Field(None, gt=0, description="ID del hospital")
    fecha_hora: datetime = Field(..., description="Fecha y hora de la cita")
    motivo: Optional[str] = Field(None, min_length=10, max_length=1000, description="Motivo de la cita")
    notas: Optional[str] = Field(None, max_length=2000, description="Notas adicionales")

    @field_validator('fecha_hora')
    @classmethod
    def validar_fecha_futura(cls, v):
        if v <= datetime.now():
            raise ValueError('La fecha de la cita debe ser futura')
        return v


# Schema para crear una cita
class CitaCreate(CitaBase):
    pass


# Schema para actualizar una cita
class CitaUpdate(BaseModel):
    fecha_hora: Optional[datetime] = None
    hospital_id: Optional[int] = Field(None, gt=0)
    motivo: Optional[str] = Field(None, min_length=10, max_length=1000)
    notas: Optional[str] = Field(None, max_length=2000)

    @field_validator('fecha_hora')
    @classmethod
    def validar_fecha_futura(cls, v):
        if v and v <= datetime.now():
            raise ValueError('La fecha de la cita debe ser futura')
        return v


# Schema para cambiar el estado de una cita
class CitaCambiarEstado(BaseModel):
    estado: EstadoCita = Field(..., description="Nuevo estado de la cita")
    motivo_cambio: Optional[str] = Field(None, min_length=5, max_length=500, description="Motivo del cambio de estado")


# Schema para la respuesta de cita (incluye datos relacionados)
class CitaResponse(BaseModel):
    id: int
    paciente_id: int
    medico_id: int
    hospital_id: Optional[int]
    fecha_hora: datetime
    estado: EstadoCita
    motivo: Optional[str]
    notas: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Datos relacionados (opcional)
    paciente_nombre: Optional[str] = None
    paciente_apellido: Optional[str] = None
    medico_nombre: Optional[str] = None
    medico_apellido: Optional[str] = None
    hospital_nombre: Optional[str] = None

    class Config:
        from_attributes = True


# Schema para listar citas con paginación
class CitaListResponse(BaseModel):
    total: int
    page: int
    limit: int
    total_pages: int
    citas: List[CitaResponse]


# Schema para consultar disponibilidad de médico
class DisponibilidadQuery(BaseModel):
    medico_id: int = Field(..., gt=0)
    fecha: str = Field(..., pattern=r'^\d{4}-\d{2}-\d{2}$', description="Formato: YYYY-MM-DD")
    hospital_id: Optional[int] = Field(None, gt=0)


# Schema para respuesta de disponibilidad
class HorarioDisponible(BaseModel):
    hora_inicio: str
    hora_fin: str
    disponible: bool


class DisponibilidadResponse(BaseModel):
    medico_id: int
    fecha: str
    horarios: List[HorarioDisponible]


# Schema para filtros de búsqueda
class CitaFiltros(BaseModel):
    paciente_id: Optional[int] = None
    medico_id: Optional[int] = None
    hospital_id: Optional[int] = None
    estado: Optional[EstadoCita] = None
    fecha_desde: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    fecha_hasta: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    page: int = Field(1, ge=1)
    limit: int = Field(10, ge=1, le=100)
