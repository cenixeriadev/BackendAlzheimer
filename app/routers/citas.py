from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, date, timedelta
from app.utils.database import get_db
from app.models.cita import Cita
from app.models.usuario import Usuario
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.hospital import Hospital
from app.schemas.cita import (
    CitaCreate, CitaUpdate, CitaResponse, CitaListResponse, 
    CitaCambiarEstado, DisponibilidadQuery, DisponibilidadResponse,
    CitaFiltros
)
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/api/citas", tags=["Citas"])

@router.get("/", response_model=CitaListResponse)
async def listar_citas(
    filtros: CitaFiltros = Depends(),
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    query = db.query(Cita)
    
    if current_user.tipo_usuario == "paciente":
        paciente = db.query(Paciente).filter(Paciente.usuario_id == current_user.id).first()
        if paciente:
            query = query.filter(Cita.paciente_id == paciente.id)
        else:
            return CitaListResponse(total=0, page=filtros.page, limit=filtros.limit, total_pages=0, citas=[])
    
    elif current_user.tipo_usuario == "medico":
        medico = db.query(Medico).filter(Medico.usuario_id == current_user.id).first()
        if medico:
            query = query.filter(Cita.medico_id == medico.id)
        else:
            return CitaListResponse(total=0, page=filtros.page, limit=filtros.limit, total_pages=0, citas=[])
    
    if filtros.paciente_id:
        query = query.filter(Cita.paciente_id == filtros.paciente_id)
    if filtros.medico_id:
        query = query.filter(Cita.medico_id == filtros.medico_id)
    if filtros.hospital_id:
        query = query.filter(Cita.hospital_id == filtros.hospital_id)
    if filtros.estado:
        query = query.filter(Cita.estado == filtros.estado)
    if filtros.fecha_desde:
        query = query.filter(Cita.fecha_hora >= filtros.fecha_desde)
    if filtros.fecha_hasta:
        query = query.filter(Cita.fecha_hora <= filtros.fecha_hasta)
    
    total = query.count()
    total_pages = (total + filtros.limit - 1) // filtros.limit
    offset = (filtros.page - 1) * filtros.limit
    
    citas = query.order_by(Cita.fecha_hora.asc()).offset(offset).limit(filtros.limit).all()
    
    citas_response = []
    for cita in citas:
        paciente = db.query(Paciente).filter(Paciente.id == cita.paciente_id).first()
        medico = db.query(Medico).filter(Medico.id == cita.medico_id).first()
        hospital = db.query(Hospital).filter(Hospital.id == cita.hospital_id).first() if cita.hospital_id else None
        
        citas_response.append(CitaResponse(
            id=cita.id,
            paciente_id=cita.paciente_id,
            medico_id=cita.medico_id,
            hospital_id=cita.hospital_id,
            fecha_hora=cita.fecha_hora,
            estado=cita.estado,
            motivo=cita.motivo,
            notas=cita.notas,
            created_at=cita.created_at,
            updated_at=cita.updated_at,
            paciente_nombre=f"{paciente.nombre} {paciente.apellido}" if paciente else "N/A",
            paciente_apellido=paciente.apellido if paciente else "N/A",
            medico_nombre=f"{medico.nombre} {medico.apellido}" if medico else "N/A",
            medico_apellido=medico.apellido if medico else "N/A",
            hospital_nombre=hospital.nombre if hospital else None
        ))
    
    return CitaListResponse(
        total=total,
        page=filtros.page,
        limit=filtros.limit,
        total_pages=total_pages,
        citas=citas_response
    )

@router.post("/", response_model=CitaResponse)
async def crear_cita(
    cita_data: CitaCreate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    # Verificar que el paciente existe
    paciente = db.query(Paciente).filter(Paciente.id == cita_data.paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    
    # Verificar que el médico existe
    medico = db.query(Medico).filter(Medico.id == cita_data.medico_id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    
    # Verificar que no hay citas duplicadas
    cita_existente = db.query(Cita).filter(
        Cita.medico_id == cita_data.medico_id,
        Cita.fecha_hora == cita_data.fecha_hora,
        Cita.estado.in_(["programada", "reprogramada"])
    ).first()
    
    if cita_existente:
        raise HTTPException(status_code=400, detail="El médico ya tiene una cita programada en ese horario")
    
    # Crear cita
    cita = Cita(**cita_data.dict())
    db.add(cita)
    db.commit()
    db.refresh(cita)
    
    return CitaResponse(
        id=cita.id,
        **cita_data.dict(),
        estado="programada",
        created_at=cita.created_at,
        updated_at=cita.updated_at,
        paciente_nombre=f"{paciente.nombre} {paciente.apellido}",
        paciente_apellido=paciente.apellido,
        medico_nombre=f"{medico.nombre} {medico.apellido}",
        medico_apellido=medico.apellido,
        hospital_nombre=None
    )

@router.get("/{cita_id}", response_model=CitaResponse)
async def obtener_cita(
    cita_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtener cita por ID
    """
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Verificar permisos
    if current_user.tipo_usuario == "paciente":
        paciente = db.query(Paciente).filter(Paciente.usuario_id == current_user.id).first()
        if not paciente or cita.paciente_id != paciente.id:
            raise HTTPException(status_code=403, detail="No tienes acceso a esta cita")
    elif current_user.tipo_usuario == "medico":
        medico = db.query(Medico).filter(Medico.usuario_id == current_user.id).first()
        if not medico or cita.medico_id != medico.id:
            raise HTTPException(status_code=403, detail="No tienes acceso a esta cita")
    
    # Obtener datos relacionados
    paciente = db.query(Paciente).filter(Paciente.id == cita.paciente_id).first()
    medico = db.query(Medico).filter(Medico.id == cita.medico_id).first()
    hospital = db.query(Hospital).filter(Hospital.id == cita.hospital_id).first() if cita.hospital_id else None
    
    return CitaResponse(
        id=cita.id,
        paciente_id=cita.paciente_id,
        medico_id=cita.medico_id,
        hospital_id=cita.hospital_id,
        fecha_hora=cita.fecha_hora,
        estado=cita.estado,
        motivo=cita.motivo,
        notas=cita.notas,
        created_at=cita.created_at,
        updated_at=cita.updated_at,
        paciente_nombre=f"{paciente.nombre} {paciente.apellido}" if paciente else "N/A",
        paciente_apellido=paciente.apellido if paciente else "N/A",
        medico_nombre=f"{medico.nombre} {medico.apellido}" if medico else "N/A",
        medico_apellido=medico.apellido if medico else "N/A",
        hospital_nombre=hospital.nombre if hospital else None
    )

@router.put("/{cita_id}", response_model=CitaResponse)
async def actualizar_cita(
    cita_id: int,
    cita_data: CitaUpdate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Actualizar cita existente
    """
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Solo permitir actualizar citas programadas
    if cita.estado != "programada":
        raise HTTPException(status_code=400, detail="Solo se pueden modificar citas programadas")
    
    # Actualizar campos
    for field, value in cita_data.dict(exclude_unset=True).items():
        setattr(cita, field, value)
    
    cita.updated_at = datetime.now()
    db.commit()
    db.refresh(cita)
    
    return await obtener_cita(cita_id, current_user, db)

@router.patch("/{cita_id}/estado", response_model=CitaResponse)
async def cambiar_estado_cita(
    cita_id: int,
    estado_data: CitaCambiarEstado,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Cambiar estado de una cita
    """
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    cita.estado = estado_data.estado
    if estado_data.motivo_cambio:
        cita.notas = f"{cita.notas or ''}\nCambio de estado: {estado_data.motivo_cambio}".strip()
    
    cita.updated_at = datetime.now()
    db.commit()
    db.refresh(cita)
    
    return await obtener_cita(cita_id, current_user, db)

@router.delete("/{cita_id}")
async def eliminar_cita(
    cita_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Eliminar cita (solo citas programadas)
    """
    cita = db.query(Cita).filter(Cita.id == cita_id).first()
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    if cita.estado != "programada":
        raise HTTPException(status_code=400, detail="Solo se pueden eliminar citas programadas")
    
    db.delete(cita)
    db.commit()
    
    return {"message": "Cita eliminada correctamente"}

@router.get("/medico/{medico_id}/disponibilidad", response_model=DisponibilidadResponse)
async def verificar_disponibilidad(
    medico_id: int,
    fecha: str = Query(..., pattern=r'^\d{4}-\d{2}-\d{2}$'),
    hospital_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    Verificar disponibilidad de un médico en una fecha específica
    """
    try:
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Formato de fecha inválido")
    
    # Verificar que el médico existe
    medico = db.query(Medico).filter(Medico.id == medico_id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")
    
    # Obtener citas del médico en esa fecha
    citas = db.query(Cita).filter(
        Cita.medico_id == medico_id,
        Cita.fecha_hora >= datetime.combine(fecha_obj, datetime.min.time()),
        Cita.fecha_hora < datetime.combine(fecha_obj, datetime.min.time()) + timedelta(days=1),
        Cita.estado.in_(["programada", "reprogramada"])
    ).all()
    
    # Generar horarios disponibles (9:00 - 17:00)
    horarios = []
    for hora in range(9, 17):
        hora_inicio = datetime.combine(fecha_obj, datetime.min.time().replace(hour=hora))
        hora_fin = datetime.combine(fecha_obj, datetime.min.time().replace(hour=hora + 1))
        
        # Verificar si hay cita en este horario
        cita_existente = any(
            cita.fecha_hora.time() == hora_inicio.time() 
            for cita in citas
        )
        
        horarios.append({
            "hora_inicio": hora_inicio.strftime("%H:%M"),
            "hora_fin": hora_fin.strftime("%H:%M"),
            "disponible": not cita_existente
        })
    
    return DisponibilidadResponse(
        medico_id=medico_id,
        fecha=fecha,
        horarios=horarios
    )