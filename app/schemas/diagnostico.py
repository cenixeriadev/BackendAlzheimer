from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class AnalisisResponse(BaseModel):
    resultado: str
    confianza: str
    diagnostico_id: Optional[int] = 0
    datos_roboflow: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True
        
class DiagnosticoResponse(BaseModel):
    id: int
    paciente_id: int
    resultado: str  
    confianza: float  
    clase_original: Optional[str] = None
    imagen_original_url: Optional[str] = None
    imagen_procesada_url: Optional[str] = None
    datos_roboflow: Optional[Dict[str, Any]] = None
    estado: str
    created_at: datetime

    class Config:
        from_attributes = True


class DiagnosticoResumen(BaseModel):
    """Esquema para listado de historial"""
    id: int
    resultado: str
    confianza: float
    imagen_original_url: str
    fecha_analisis: datetime
    estado: str

    class Config:
        from_attributes = True

class PrediccionDetalle(BaseModel):
    """Esquema para detalles de predicciones"""
    clase: str
    confianza: float
    clase_id: Optional[int] = None
    bbox: Optional[Dict[str, float]] = None

class DatosDetallados(BaseModel):
    """Esquema para datos procesados de Roboflow"""
    predicciones: List[PrediccionDetalle]
    metadatos_imagen: Dict[str, Any]
    estadisticas: Dict[str, Any]

class DiagnosticoDetalleResponse(BaseModel):
    """Esquema para respuesta de detalle completo"""
    id: int
    fecha_analisis: datetime
    resultado: str
    confianza: float
    clase_original: str
    imagen_original_url: str
    imagen_procesada_url: Optional[str]
    estado: str
    datos_detallados: DatosDetallados

    class Config:
        from_attributes = True

class HistorialResponse(BaseModel):
    """Esquema para respuesta paginada"""
    diagnosticos: List[DiagnosticoResumen]
    pagination: Dict[str, Any]

    class Config:
        from_attributes = True