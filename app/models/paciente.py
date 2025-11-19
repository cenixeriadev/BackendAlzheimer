from sqlalchemy import Column, Integer, String, Date, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.utils.database import Base

class EstadoAlzheimer(str, enum.Enum):
    independiente = "independiente"
    dependiente = "dependiente"

class Paciente(Base):
    __tablename__ = "paciente"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), unique=True, nullable=False)
    nombre = Column(String(100), nullable=False)
    apellido = Column(String(100), nullable=False)
    fecha_nacimiento = Column(Date, nullable=False)
    genero = Column(String(20), nullable=True)
    numero_identidad = Column(String(20), unique=True, nullable=True)
    telefono = Column(String(20), nullable=True)
    email = Column(String(100), nullable=True)
    direccion = Column(Text, nullable=True)
    ciudad = Column(String(100), nullable=True)
    estado_alzheimer = Column(Enum(EstadoAlzheimer), nullable=True)
    notas_medicas = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    usuario = relationship(
        "Usuario", 
        back_populates="paciente", 
        foreign_keys=[usuario_id] 
    )