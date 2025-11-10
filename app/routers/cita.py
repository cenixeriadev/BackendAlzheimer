from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
import math

from app.database import get_db
from app.dependencies import get_current_user
from app.schemas.cita import (
    CitaCreate,
    CitaUpdate,
    CitaResponse,
    CitaCambiarEstado,
    CitaListResponse,
    DisponibilidadResponse,
    EstadoCita
)
from app.schemas.usuario import UsuarioResponse
from app.services.cita_service import CitaService
from app.models.cita import Cita


router = APIRouter(
    prefix="/api/citas",
    tags=["Citas"],
    responses={404: {"description": "No encontrado"}}
)


def cita_a_response(cita: Cita) -> CitaResponse:
    """Convierte modelo Cita a CitaResponse con datos relacionados"""
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
        paciente_nombre=cita.paciente.nombre if cita.paciente else None,
        paciente_apellido=cita.paciente.apellido if cita.paciente else None,
        medico_nombre=cita.medico.nombre if cita.medico else None,
        medico_apellido=cita.medico.apellido if cita.medico else None,
        hospital_nombre=cita.hospital.nombre if cita.hospital else None
    )


# ==========================================
# ENDPOINTS DE CITAS
# ==========================================

@router.post(
    "/",
    response_model=CitaResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear una nueva cita",
    description="""
    Crea una nueva cita médica. Permisos según tipo de usuario:
    - **Paciente independiente**: Puede crear sus propias citas
    - **Paciente con cuidador**: Solo puede ver, no crear (lo hace el cuidador)
    - **Cuidador**: Puede crear citas para sus pacientes asignados
    - **Admin**: Puede crear citas para cualquier paciente
    """
)
async def crear_cita(
    cita_data: CitaCreate,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Crear una nueva cita"""
    service = CitaService(db)
    
    try:
        cita = await service.crear_cita(
            cita_data=cita_data,
            usuario_id=current_user.id,
            tipo_usuario=current_user.tipo_usuario
        )
        return cita_a_response(cita)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear la cita: {str(e)}"
        )


@router.get(
    "/",
    response_model=CitaListResponse,
    summary="Listar citas",
    description="""
    Lista citas con filtros y paginación. Los datos retornados dependen del tipo de usuario:
    - **Paciente**: Solo sus propias citas
    - **Cuidador**: Citas de sus pacientes asignados
    - **Médico**: Solo citas donde es el médico asignado
    - **Admin**: Todas las citas del sistema
    """
)
async def listar_citas(
    paciente_id: Optional[int] = Query(None, description="Filtrar por ID de paciente"),
    medico_id: Optional[int] = Query(None, description="Filtrar por ID de médico"),
    hospital_id: Optional[int] = Query(None, description="Filtrar por ID de hospital"),
    estado: Optional[EstadoCita] = Query(None, description="Filtrar por estado"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (YYYY-MM-DD)", pattern=r'^\d{4}-\d{2}-\d{2}$'),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (YYYY-MM-DD)", pattern=r'^\d{4}-\d{2}-\d{2}$'),
    page: int = Query(1, ge=1, description="Número de página"),
    limit: int = Query(10, ge=1, le=100, description="Registros por página"),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Listar citas con filtros y paginación"""
    service = CitaService(db)
    
    try:
        citas, total = await service.listar_citas(
            usuario_id=current_user.id,
            tipo_usuario=current_user.tipo_usuario,
            paciente_id=paciente_id,
            medico_id=medico_id,
            hospital_id=hospital_id,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            page=page,
            limit=limit
        )
        
        total_pages = math.ceil(total / limit)
        
        return CitaListResponse(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            citas=[cita_a_response(cita) for cita in citas]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al listar citas: {str(e)}"
        )


@router.get(
    "/{cita_id}",
    response_model=CitaResponse,
    summary="Obtener detalle de una cita",
    description="Obtiene los detalles completos de una cita específica"
)
async def obtener_cita(
    cita_id: int,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Obtener una cita específica"""
    service = CitaService(db)
    
    try:
        cita = await service.obtener_cita(
            cita_id=cita_id,
            usuario_id=current_user.id,
            tipo_usuario=current_user.tipo_usuario
        )
        return cita_a_response(cita)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener la cita: {str(e)}"
        )


@router.get(
    "/paciente/{paciente_id}",
    response_model=CitaListResponse,
    summary="Obtener citas de un paciente",
    description="Lista todas las citas de un paciente específico"
)
async def obtener_citas_paciente(
    paciente_id: int,
    estado: Optional[EstadoCita] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Obtener todas las citas de un paciente"""
    service = CitaService(db)
    
    try:
        citas, total = await service.listar_citas(
            usuario_id=current_user.id,
            tipo_usuario=current_user.tipo_usuario,
            paciente_id=paciente_id,
            estado=estado,
            page=page,
            limit=limit
        )
        
        total_pages = math.ceil(total / limit)
        
        return CitaListResponse(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            citas=[cita_a_response(cita) for cita in citas]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener citas del paciente: {str(e)}"
        )


@router.get(
    "/medico/{medico_id}",
    response_model=CitaListResponse,
    summary="Obtener citas de un médico",
    description="Lista todas las citas de un médico específico"
)
async def obtener_citas_medico(
    medico_id: int,
    estado: Optional[EstadoCita] = Query(None),
    fecha_desde: Optional[str] = Query(None, pattern=r'^\d{4}-\d{2}-\d{2}$'),
    fecha_hasta: Optional[str] = Query(None, pattern=r'^\d{4}-\d{2}-\d{2}$'),
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Obtener todas las citas de un médico"""
    service = CitaService(db)
    
    try:
        citas, total = await service.listar_citas(
            usuario_id=current_user.id,
            tipo_usuario=current_user.tipo_usuario,
            medico_id=medico_id,
            estado=estado,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            page=page,
            limit=limit
        )
        
        total_pages = math.ceil(total / limit)
        
        return CitaListResponse(
            total=total,
            page=page,
            limit=limit,
            total_pages=total_pages,
            citas=[cita_a_response(cita) for cita in citas]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener citas del médico: {str(e)}"
        )


@router.get(
    "/proximas/mis-citas",
    response_model=List[CitaResponse],
    summary="Obtener mis próximas citas",
    description="Obtiene las próximas citas programadas del usuario actual (próximos 7 días)"
)
async def obtener_proximas_citas(
    dias: int = Query(7, ge=1, le=30, description="Días hacia adelante"),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Obtener próximas citas del usuario"""
    service = CitaService(db)
    
    try:
        citas = await service.obtener_citas_proximas(
            usuario_id=current_user.id,
            tipo_usuario=current_user.tipo_usuario,
            dias=dias
        )
        return [cita_a_response(cita) for cita in citas]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener próximas citas: {str(e)}"
        )


@router.put(
    "/{cita_id}",
    response_model=CitaResponse,
    summary="Actualizar una cita",
    description="Actualiza los datos de una cita existente. No se pueden actualizar citas completadas o canceladas."
)
async def actualizar_cita(
    cita_id: int,
    cita_data: CitaUpdate,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Actualizar una cita existente"""
    service = CitaService(db)
    
    try:
        cita = await service.actualizar_cita(
            cita_id=cita_id,
            cita_data=cita_data,
            usuario_id=current_user.id,
            tipo_usuario=current_user.tipo_usuario
        )
        return cita_a_response(cita)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al actualizar la cita: {str(e)}"
        )


@router.patch(
    "/{cita_id}/estado",
    response_model=CitaResponse,
    summary="Cambiar estado de una cita",
    description="Cambia el estado de una cita (programada, completada, cancelada, reprogramada)"
)
async def cambiar_estado_cita(
    cita_id: int,
    estado_data: CitaCambiarEstado,
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Cambiar el estado de una cita"""
    service = CitaService(db)
    
    try:
        cita = await service.cambiar_estado_cita(
            cita_id=cita_id,
            estado_data=estado_data,
            usuario_id=current_user.id,
            tipo_usuario=current_user.tipo_usuario
        )
        return cita_a_response(cita)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cambiar estado de la cita: {str(e)}"
        )


@router.delete(
    "/{cita_id}",
    response_model=CitaResponse,
    summary="Cancelar una cita",
    description="Cancela una cita existente. La cita no se elimina, solo cambia su estado a 'cancelada'."
)
async def cancelar_cita(
    cita_id: int,
    motivo: str = Query(..., min_length=5, max_length=500, description="Motivo de la cancelación"),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Cancelar una cita"""
    service = CitaService(db)
    
    try:
        cita = await service.cancelar_cita(
            cita_id=cita_id,
            motivo=motivo,
            usuario_id=current_user.id,
            tipo_usuario=current_user.tipo_usuario
        )
        return cita_a_response(cita)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al cancelar la cita: {str(e)}"
        )


# ==========================================
# ENDPOINTS DE DISPONIBILIDAD
# ==========================================

@router.get(
    "/disponibilidad/medico",
    response_model=DisponibilidadResponse,
    summary="Consultar disponibilidad de médico",
    description="Consulta la disponibilidad horaria de un médico para una fecha específica"
)
async def consultar_disponibilidad(
    medico_id: int = Query(..., description="ID del médico"),
    fecha: str = Query(..., description="Fecha a consultar (YYYY-MM-DD)", pattern=r'^\d{4}-\d{2}-\d{2}$'),
    hospital_id: Optional[int] = Query(None, description="ID del hospital (opcional)"),
    db: Session = Depends(get_db),
    current_user: UsuarioResponse = Depends(get_current_user)
):
    """Consultar disponibilidad de un médico para una fecha"""
    service = CitaService(db)
    
    try:
        # Convertir string a date
        from datetime import datetime
        fecha_obj = datetime.strptime(fecha, "%Y-%m-%d").date()
        
        disponibilidad = await service.obtener_disponibilidad_medico(
            medico_id=medico_id,
            fecha=fecha_obj,
            hospital_id=hospital_id
        )
        return disponibilidad
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato de fecha inválido. Use YYYY-MM-DD"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al consultar disponibilidad: {str(e)}"
        )
