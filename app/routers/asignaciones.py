from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from app.utils.database import get_db
from app.models.asignacion_medico import AsignacionMedicoPaciente
from app.models.medico import Medico
from app.models.paciente import Paciente
from app.models.usuario import Usuario
from app.schemas.asignacion_medico import AsignacionCreate, AsignacionResponse
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/api/asignaciones", tags=["Asignaciones Médico-Paciente"])

@router.post("/", response_model=AsignacionResponse)
async def crear_asignacion(
    asignacion_data: AsignacionCreate,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Crear nueva asignación médico-paciente (solo admin)
    """
    if current_user.tipo_usuario != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden crear asignaciones")

    medico = db.query(Medico).filter(Medico.id == asignacion_data.medico_id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Médico no encontrado")

    paciente = db.query(Paciente).filter(Paciente.id == asignacion_data.paciente_id).first()
    if not paciente:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")

    asignacion_existente = db.query(AsignacionMedicoPaciente).filter(
        AsignacionMedicoPaciente.medico_id == asignacion_data.medico_id,
        AsignacionMedicoPaciente.paciente_id == asignacion_data.paciente_id
    ).first()

    if asignacion_existente:
        raise HTTPException(status_code=400, detail="Esta asignación ya existe")

    asignacion = AsignacionMedicoPaciente(**asignacion_data.dict())
    db.add(asignacion)
    db.commit()
    db.refresh(asignacion)

    return AsignacionResponse(
        id=asignacion.id,
        medico_id=asignacion.medico_id,
        paciente_id=asignacion.paciente_id,
        created_at=asignacion.created_at,
        medico_nombre=f"{medico.nombre} {medico.apellido}",
        medico_apellido=medico.apellido,
        paciente_nombre=f"{paciente.nombre} {paciente.apellido}",
        paciente_apellido=paciente.apellido
    )

@router.get("/", response_model=List[AsignacionResponse])
async def listar_asignaciones(
    medico_id: int = Query(None),
    paciente_id: int = Query(None),
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.tipo_usuario not in ["admin", "medico"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver las asignaciones")

    query = db.query(AsignacionMedicoPaciente)

    if current_user.tipo_usuario == "medico":
        medico = db.query(Medico).filter(Medico.usuario_id == current_user.id).first()
        if medico:
            query = query.filter(AsignacionMedicoPaciente.medico_id == medico.id)
        else:
            return []

    if medico_id:
        query = query.filter(AsignacionMedicoPaciente.medico_id == medico_id)
    if paciente_id:
        query = query.filter(AsignacionMedicoPaciente.paciente_id == paciente_id)

    asignaciones = query.all()

    asignaciones_response = []
    for asignacion in asignaciones:
        medico = db.query(Medico).filter(Medico.id == asignacion.medico_id).first()
        paciente = db.query(Paciente).filter(Paciente.id == asignacion.paciente_id).first()

        asignaciones_response.append(AsignacionResponse(
            id=asignacion.id,
            medico_id=asignacion.medico_id,
            paciente_id=asignacion.paciente_id,
            created_at=asignacion.created_at,
            medico_nombre=f"{medico.nombre} {medico.apellido}" if medico else "N/A",
            medico_apellido=medico.apellido if medico else "N/A",
            paciente_nombre=f"{paciente.nombre} {paciente.apellido}" if paciente else "N/A",
            paciente_apellido=paciente.apellido if paciente else "N/A"
        ))

    return asignaciones_response

@router.delete("/{asignacion_id}")
async def eliminar_asignacion(
    asignacion_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.tipo_usuario != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden eliminar asignaciones")

    asignacion = db.query(AsignacionMedicoPaciente).filter(AsignacionMedicoPaciente.id == asignacion_id).first()
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")

    db.delete(asignacion)
    db.commit()

    return {"message": "Asignación eliminada correctamente"}