import datetime
from sqlalchemy import JSON, Column, Integer, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Diagnostico(Base):
    __tablename__ = "diagnostico"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)  # Agregar autoincrement=True
    paciente_id = Column(Integer, ForeignKey("usuario.id"))
    resultado = Column(String)
    confianza = Column(Float)
    clase_original = Column(String)
    imagen_original_url = Column(String)
    imagen_procesada_url = Column(String)
    datos_roboflow = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    estado = Column(String, default="completado")
    
    # Relación
    paciente = relationship(
        "Usuario", 
        back_populates="diagnosticos",
        foreign_keys=[paciente_id]
    )