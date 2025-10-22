from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class NivelAcceso(str, enum.Enum):
    total = "total"
    limitado = "limitado"


class Admin(Base):
    __tablename__ = "admin"

    id = Column(Integer, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuario.id", ondelete="CASCADE"), unique=True, nullable=False)
    nivel_acceso = Column(Enum(NivelAcceso), default=NivelAcceso.total)
    permisos = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relaciones
    usuario = relationship("Usuario", back_populates="admin" , foreign_keys=[usuario_id])
