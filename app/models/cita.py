from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.database import Base

class Cita(Base):
    __tablename__ = "cita"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("paciente.id", ondelete="CASCADE"), nullable=False)
    medico_id = Column(Integer, ForeignKey("medico.id", ondelete="SET NULL"), nullable=False)
    hospital_id = Column(Integer, ForeignKey("hospital.id", ondelete="SET NULL"), nullable=True)
    fecha_hora = Column(DateTime, nullable=False)
    estado = Column(String(50), default="programada")
    motivo = Column(Text, nullable=True)
    notas = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    paciente = relationship("Paciente", foreign_keys=[paciente_id])
    medico = relationship("Medico", foreign_keys=[medico_id])
    hospital = relationship("Hospital", foreign_keys=[hospital_id])