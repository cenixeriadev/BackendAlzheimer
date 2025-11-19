from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class EstadisticasGenerales(BaseModel):
    total_pacientes_activos: int
    total_medicos_activos: int
    total_admins_activos: int
    total_usuarios_activos: int
    citas_programadas: int
    citas_completadas: int
    citas_canceladas: int
    total_diagnosticos: int
    total_hospitales: int
    total_asignaciones: int

    class Config:
        from_attributes = True


class DiagnosticosPorClasificacion(BaseModel):
    clasificacion: Optional[str]
    clasificacion_ingles: Optional[str]
    cantidad_diagnosticos: int
    confianza_promedio: Optional[float]
    pacientes_unicos: int

    class Config:
        from_attributes = True


class CitasPorHospital(BaseModel):
    hospital: str
    ciudad: Optional[str]
    total_citas: int
    citas_programadas: int
    citas_completadas: int
    citas_canceladas: int
    citas_reprogramadas: int

    class Config:
        from_attributes = True


class PacienteDetallado(BaseModel):
    paciente_id: int
    nombre: str
    apellido: str
    fecha_nacimiento: datetime
    edad: Optional[int]
    genero: Optional[str]
    ciudad: Optional[str]
    estado_alzheimer: Optional[str]
    username: str
    usuario_activo: bool
    total_diagnosticos: int
    total_citas: int
    medicos_asignados: int
    ultimo_diagnostico: Optional[datetime]
    ultima_cita: Optional[datetime]

    class Config:
        from_attributes = True


class MedicoEstadisticas(BaseModel):
    medico_id: int
    nombre: str
    apellido: str
    cmp: str
    especialidad: Optional[str]
    hospital_afiliacion: Optional[str]
    username: str
    usuario_activo: bool
    total_citas: int
    citas_completadas: int
    citas_programadas: int
    pacientes_asignados: int
    ultima_cita: Optional[datetime]
    proxima_cita: Optional[datetime]

    class Config:
        from_attributes = True


class ActividadReciente(BaseModel):
    tipo_evento: str
    evento_id: int
    usuario_id: int
    detalle: Optional[str]
    fecha_evento: datetime

    class Config:
        from_attributes = True


class DiagnosticosPorMes(BaseModel):
    mes: datetime
    total_diagnosticos: int
    pacientes_unicos: int
    confianza_promedio: Optional[float]
    sin_demencia: int
    demencia_muy_leve: int
    demencia_leve: int
    demencia_moderada: int

    class Config:
        from_attributes = True


class DashboardResponse(BaseModel):
    estadisticas_generales: EstadisticasGenerales
    diagnosticos_clasificacion: List[DiagnosticosPorClasificacion]
    citas_por_hospital: List[CitasPorHospital]
    actividad_reciente: List[ActividadReciente]
    diagnosticos_por_mes: List[DiagnosticosPorMes]
    pacientes_destacados: List[PacienteDetallado]
    medicos_destacados: List[MedicoEstadisticas]

    class Config:
        from_attributes = True
