from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query
from scipy import stats
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, timedelta
from app.utils.database import get_db
from app.models.usuario import Usuario
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.diagnostico import Diagnostico
from app.models.cita import Cita
from app.schemas.usuario import UsuarioResponse
from app.schemas.admin import EstadisticasResponse
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/api/admin", tags=["Administración"])

@router.get("/usuarios", response_model=List[UsuarioResponse])
async def listar_usuarios(
    tipo_usuario: str = Query(None),
    estado: bool = Query(None),
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.tipo_usuario != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden acceder a esta información")
    
    query = db.query(Usuario)
    
    if tipo_usuario:
        query = query.filter(Usuario.tipo_usuario == tipo_usuario)
    if estado is not None:
        query = query.filter(Usuario.estado == estado)
    
    usuarios = query.order_by(Usuario.created_at.desc()).all()
    
    usuarios_response = []
    for usuario in usuarios:
        usuario_data = UsuarioResponse(
            id=usuario.id,
            username=usuario.username,
            tipo_usuario=usuario.tipo_usuario,
            estado=usuario.estado,
            created_at=usuario.created_at
        )
        
        if usuario.tipo_usuario == "paciente" and usuario.paciente:
            usuario_data.nombre = usuario.paciente.nombre
            usuario_data.apellido = usuario.paciente.apellido
            usuario_data.email = usuario.paciente.email
            usuario_data.telefono = usuario.paciente.telefono
        elif usuario.tipo_usuario == "medico" and usuario.medico:
            usuario_data.nombre = usuario.medico.nombre
            usuario_data.apellido = usuario.medico.apellido
            usuario_data.email = usuario.medico.email
            usuario_data.telefono = usuario.medico.telefono
        elif usuario.tipo_usuario == "cuidador" and usuario.cuidador:
            usuario_data.nombre = usuario.cuidador.nombre
            usuario_data.apellido = usuario.cuidador.apellido
            usuario_data.email = usuario.cuidador.email
            usuario_data.telefono = usuario.cuidador.telefono
        
        usuarios_response.append(usuario_data)
    
    return usuarios_response

@router.get("/estadisticas", response_model=EstadisticasResponse)
async def obtener_estadisticas(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.tipo_usuario != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden acceder a esta información")
    
    total_usuarios = db.query(Usuario).count()
    usuarios_por_tipo = db.query(
        Usuario.tipo_usuario,
        db.func.count(Usuario.id)
    ).group_by(Usuario.tipo_usuario).all()
    
    total_diagnosticos = db.query(Diagnostico).count()
    diagnosticos_por_resultado = db.query(
        Diagnostico.resultado,
        db.func.count(Diagnostico.id)
    ).group_by(Diagnostico.resultado).all()
    
    total_citas = db.query(Cita).count()
    citas_por_estado = db.query(
        Cita.estado,
        db.func.count(Cita.id)
    ).group_by(Cita.estado).all()
    
    fecha_limite = datetime.now() - timedelta(days=30)
    diagnosticos_recientes = db.query(Diagnostico).filter(
        Diagnostico.created_at >= fecha_limite
    ).count()
    
    return EstadisticasResponse(
        total_usuarios=total_usuarios,
        usuarios_por_tipo=dict(usuarios_por_tipo),
        total_diagnosticos=total_diagnosticos,
        diagnosticos_por_resultado=dict(diagnosticos_por_resultado),
        total_citas=total_citas,
        citas_por_estado=dict(citas_por_estado),
        diagnosticos_ultimo_mes=diagnosticos_recientes
    )

@router.patch("/usuarios/{usuario_id}/estado")
async def cambiar_estado_usuario(
    usuario_id: int,
    estado: bool,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.tipo_usuario != "admin":
        raise HTTPException(status_code=403, detail="Solo los administradores pueden realizar esta acción")
    
    usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    
    usuario.estado = estado
    db.commit()
    
    return {"message": f"Usuario {'activado' if estado else 'desactivado'} correctamente"}


@router.get("/admin/historial-completo", response_model=Dict[str, Any])
async def obtener_historial_completo(
    paciente_id: int = Query(None, description="Filtrar por paciente específico"),
    fecha_desde: str = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: str = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    resultado: str = Query(None, description="Filtrar por resultado"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.tipo_usuario != "admin":
        raise HTTPException(
            status_code=stats.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden acceder al historial completo"
        )

    query = db.query(Diagnostico)
    
    if paciente_id:
        query = query.filter(Diagnostico.paciente_id == paciente_id)
    
    if resultado:
        query = query.filter(Diagnostico.resultado.ilike(f"%{resultado}%"))
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, "%Y-%m-%d")
            query = query.filter(Diagnostico.created_at >= fecha_desde_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha_desde inválido")
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, "%Y-%m-%d") + timedelta(days=1)
            query = query.filter(Diagnostico.created_at < fecha_hasta_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha_hasta inválido")

    total = query.count()
    total_pages = ceil(total / per_page) if total > 0 else 1
    offset = (page - 1) * per_page

    diagnosticos = query.order_by(Diagnostico.created_at.desc()).offset(offset).limit(per_page).all()

    diagnosticos_enriquecidos = []
    for diagnostico in diagnosticos:
        paciente_info = await _obtener_info_paciente(db, diagnostico.paciente_id)
        
        diagnostico_data = {
            "id": diagnostico.id,
            "paciente_id": diagnostico.paciente_id,
            "resultado": diagnostico.resultado,
            "confianza": diagnostico.confianza,
            "clase_original": diagnostico.clase_original,
            "imagen_original_url": diagnostico.imagen_original_url,
            "imagen_procesada_url": diagnostico.imagen_procesada_url,
            "estado": diagnostico.estado,
            "created_at": diagnostico.created_at,
            "paciente_info": paciente_info
        }
        diagnosticos_enriquecidos.append(diagnostico_data)

    return {
        "diagnosticos": diagnosticos_enriquecidos,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        },
        "filtros_aplicados": {
            "paciente_id": paciente_id,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "resultado": resultado
        }
    }

@router.get("/admin/estadisticas-globales")
async def obtener_estadisticas_globales(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    if current_user.tipo_usuario != "admin":
        raise HTTPException(
            status_code=stats.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden acceder a las estadísticas globales"
        )

    resultados_stats = db.query(
        Diagnostico.resultado,
        db.func.count(Diagnostico.id).label('count')
    ).group_by(Diagnostico.resultado).all()

    total_diagnosticos = db.query(Diagnostico).count()

    seis_meses_atras = datetime.now() - timedelta(days=180)
    diagnosticos_por_mes = db.query(
        db.func.date_trunc('month', Diagnostico.created_at).label('mes'),
        db.func.count(Diagnostico.id).label('count')
    ).filter(
        Diagnostico.created_at >= seis_meses_atras
    ).group_by('mes').order_by('mes').all()

    pacientes_top = db.query(
        Diagnostico.paciente_id,
        db.func.count(Diagnostico.id).label('count')
    ).group_by(Diagnostico.paciente_id).order_by(db.desc('count')).limit(5).all()

    pacientes_top_info = []
    for paciente_id, count in pacientes_top:
        paciente_info = await _obtener_info_paciente(db, paciente_id)
        pacientes_top_info.append({
            "paciente_id": paciente_id,
            "count": count,
            "paciente_info": paciente_info
        })

    return {
        "estadisticas_generales": {
            "total_diagnosticos": total_diagnosticos,
            "total_pacientes": db.query(Diagnostico.paciente_id).distinct().count(),
            "promedio_confianza": db.query(db.func.avg(Diagnostico.confianza)).scalar() or 0
        },
        "distribucion_resultados": [
            {"resultado": resultado, "count": count} 
            for resultado, count in resultados_stats
        ],
        "diagnosticos_por_mes": [
            {"mes": mes.strftime("%Y-%m"), "count": count} 
            for mes, count in diagnosticos_por_mes
        ],
        "pacientes_mas_activos": pacientes_top_info
    }

async def _obtener_info_paciente(db: Session, usuario_id: int) -> Dict[str, Any]:
    """
    Obtener información del paciente a partir del usuario_id
    """
    try:
        paciente = db.query(Paciente).filter(Paciente.usuario_id == usuario_id).first()
        if paciente:
            return {
                "id": paciente.id,
                "nombre": paciente.nombre,
                "apellido": paciente.apellido,
                "email": paciente.email,
                "telefono": paciente.telefono,
                "edad": _calcular_edad(paciente.fecha_nacimiento),
                "estado_alzheimer": paciente.estado_alzheimer
            }
        return {"error": "Paciente no encontrado"}
    except Exception as e:
        return {"error": f"Error obteniendo información: {str(e)}"}

def _calcular_edad(fecha_nacimiento):
    """Calcular edad a partir de fecha de nacimiento"""
    from datetime import date
    hoy = date.today()
    return hoy.year - fecha_nacimiento.year - ((hoy.month, hoy.day) < (fecha_nacimiento.month, fecha_nacimiento.day))