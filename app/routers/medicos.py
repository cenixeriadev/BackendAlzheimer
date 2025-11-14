from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.utils.database import get_db
from app.models.medico import Medico
from app.models.usuario import Usuario
from app.models.paciente import Paciente
from app.models.diagnostico import Diagnostico
from app.schemas.medico import MedicoResponse, MedicoDetalleResponse, PacienteMedicoResponse
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/api/medicos", tags=["Médicos"])

@router.get("/mis-pacientes", response_model=List[PacienteMedicoResponse])
async def obtener_mis_pacientes(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.tipo_usuario != "medico":
        raise HTTPException(status_code=403, detail="Solo los médicos pueden acceder a esta información")
    
    medico = db.query(Medico).filter(Medico.usuario_id == current_user.id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Perfil de médico no encontrado")
    
    from app.models.cita import Cita
    pacientes_ids = db.query(Cita.paciente_id).filter(
        Cita.medico_id == medico.id
    ).distinct().all()
    
    pacientes_ids = [pid[0] for pid in pacientes_ids]
    
    pacientes_data = []
    for paciente_id in pacientes_ids:
        paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
        if paciente:
            # Obtener último diagnóstico
            ultimo_diagnostico = db.query(Diagnostico).filter(
                Diagnostico.paciente_id == paciente.usuario_id
            ).order_by(Diagnostico.created_at.desc()).first()
            
            # Obtener próxima cita
            proxima_cita = db.query(Cita).filter(
                Cita.paciente_id == paciente_id,
                Cita.medico_id == medico.id,
                Cita.estado == "programada"
            ).order_by(Cita.fecha_hora.asc()).first()
            
            pacientes_data.append(PacienteMedicoResponse(
                id=paciente.id,
                nombre=paciente.nombre,
                apellido=paciente.apellido,
                email=paciente.email,
                telefono=paciente.telefono,
                edad=_calcular_edad(paciente.fecha_nacimiento),
                estado_alzheimer=paciente.estado_alzheimer,
                ultimo_diagnostico=ultimo_diagnostico.resultado if ultimo_diagnostico else None,
                fecha_ultimo_diagnostico=ultimo_diagnostico.created_at if ultimo_diagnostico else None,
                proxima_cita=proxima_cita.fecha_hora if proxima_cita else None
            ))
    
    return pacientes_data

@router.get("/perfil", response_model=MedicoDetalleResponse)
async def obtener_perfil_medico(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.tipo_usuario != "medico":
        raise HTTPException(status_code=403, detail="Solo los médicos pueden acceder a esta información")
    
    medico = db.query(Medico).filter(Medico.usuario_id == current_user.id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Perfil de médico no encontrado")
    
    # Obtener estadísticas
    from app.models.cita import Cita
    total_citas = db.query(Cita).filter(Cita.medico_id == medico.id).count()
    citas_pendientes = db.query(Cita).filter(
        Cita.medico_id == medico.id,
        Cita.estado == "programada"
    ).count()
    
    total_pacientes = db.query(Cita.paciente_id).filter(
        Cita.medico_id == medico.id
    ).distinct().count()
    
    return MedicoDetalleResponse(
        id=medico.id,
        nombre=medico.nombre,
        apellido=medico.apellido,
        cmp=medico.cmp,
        especialidad=medico.especialidad,
        email=medico.email,
        telefono=medico.telefono,
        hospital_afiliacion=medico.hospital_afiliacion,
        estadisticas={
            "total_citas": total_citas,
            "citas_pendientes": citas_pendientes,
            "total_pacientes": total_pacientes
        }
    )

@router.get("/", response_model=List[MedicoResponse])
async def listar_medicos(
    especialidad: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Listar todos los médicos (para selección en citas)
    """
    query = db.query(Medico)
    
    if especialidad:
        query = query.filter(Medico.especialidad.ilike(f"%{especialidad}%"))
    
    medicos = query.all()
    
    return [
        MedicoResponse(
            id=medico.id,
            nombre=medico.nombre,
            apellido=medico.apellido,
            cmp=medico.cmp,
            especialidad=medico.especialidad,
            hospital_afiliacion=medico.hospital_afiliacion
        )
        for medico in medicos
    ]

def _calcular_edad(fecha_nacimiento):
    """Calcular edad a partir de fecha de nacimiento"""
    from datetime import date
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))