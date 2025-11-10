from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class EstadoCita(str, enum.Enum):
    programada = "programada"
    completada = "completada"
    cancelada = "cancelada"
    reprogramada = "reprogramada"


class Cita(Base):
    __tablename__ = "cita"

    id = Column(Integer, primary_key=True, index=True)
    paciente_id = Column(Integer, ForeignKey("paciente.id", ondelete="CASCADE"), nullable=False, index=True)
    medico_id = Column(Integer, ForeignKey("medico.id", ondelete="SET NULL"), nullable=False, index=True)
    hospital_id = Column(Integer, ForeignKey("hospital.id", ondelete="SET NULL"), nullable=True)
    fecha_hora = Column(DateTime(timezone=True), nullable=False, index=True)
    estado = Column(Enum(EstadoCita), default=EstadoCita.programada, nullable=False)
    motivo = Column(Text, nullable=True)
    notas = Column(Text, nullable=True, comment="Notas del médico o cuidador sobre la cita")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relaciones
    paciente = relationship("Paciente", backref="citas")
    medico = relationship("Medico", backref="citas")
    hospital = relationship("Hospital", backref="citas")
    diagnosticos = relationship("Diagnostico", back_populates="cita", cascade="all, delete-orphan")
