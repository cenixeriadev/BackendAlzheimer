from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.utils.database import Base

class TipoUsuario(str, enum.Enum):
    paciente = "paciente"
    medico = "medico"
    admin = "admin"

class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    foto_perfil_url = Column(String(500), nullable=True)
    tipo_usuario = Column(Enum(TipoUsuario), nullable=False)
    estado = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    paciente = relationship(
        "Paciente", 
        back_populates="usuario", 
        uselist=False, 
        foreign_keys="Paciente.usuario_id",  
        cascade="all, delete-orphan"
    )
    
    medico = relationship(
        "Medico", 
        back_populates="usuario", 
        uselist=False, 
        foreign_keys="Medico.usuario_id", 
        cascade="all, delete-orphan"
    )
    
    admin = relationship(
        "Admin", 
        back_populates="usuario", 
        uselist=False, 
        foreign_keys="Admin.usuario_id", 
        cascade="all, delete-orphan"
    )
    
    diagnosticos = relationship(
        "Diagnostico", 
        back_populates="paciente",
        foreign_keys="Diagnostico.paciente_id" 
    )