from sqlalchemy import Column, Integer, String, Float, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base

class EstadoDiagnostico(str, enum.Enum):
    pendiente = "pendiente"
    revisado = "revisado"
    confirmado = "confirmado"

class Diagnostico(Base):
    __tablename__ = "diagnostico"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    cita_id = Column(Integer, ForeignKey("cita.id", ondelete="SET NULL"), nullable=True)
    imagen_url = Column(String(500), nullable=True)
    resultado_ia = Column(String(100), nullable=True)
    confianza_ia = Column(Float, nullable=True)
    estado = Column(Enum(EstadoDiagnostico), default=EstadoDiagnostico.pendiente)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    paciente = relationship("Usuario", back_populates="diagnosticos")
    cita = relationship("Cita", back_populates="diagnosticos")

'''
me aburri y pa no lidiar con las 30 tablas de resultados agrege esta vaina a diagnostico ...
ALTER TABLE diagnostico ADD COLUMN imagen_url VARCHAR(255);
ALTER TABLE diagnostico ADD COLUMN resultado_ia VARCHAR(255);
ALTER TABLE diagnostico ADD COLUMN confianza_ia VARCHAR(255);
'''