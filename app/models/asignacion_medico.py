from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.database import Base

class AsignacionMedicoPaciente(Base):
    __tablename__ = "asignacion_medico_paciente"
    
    id = Column(Integer, primary_key=True, index=True)
    medico_id = Column(Integer, ForeignKey("medico.id"), nullable=False)
    paciente_id = Column(Integer, ForeignKey("paciente.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    medico = relationship("Medico", foreign_keys=[medico_id])
    paciente = relationship("Paciente", foreign_keys=[paciente_id])