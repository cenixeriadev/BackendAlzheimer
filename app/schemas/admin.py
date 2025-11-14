from pydantic import BaseModel
from typing import Dict, Any

class EstadisticasResponse(BaseModel):
    total_usuarios: int
    usuarios_por_tipo: Dict[str, int]
    total_diagnosticos: int
    diagnosticos_por_resultado: Dict[str, int]
    total_citas: int
    citas_por_estado: Dict[str, int]
    diagnosticos_ultimo_mes: int

    class Config:
        from_attributes = True