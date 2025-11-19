from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.utils.database import get_db
from app.utils.dependencies import get_current_active_user
from app.models.usuario import Usuario
from app.services.dashboard_service import DashboardService
from app.schemas.dashboard import (
    DashboardResponse,
    EstadisticasGenerales,
    DiagnosticosPorClasificacion,
    CitasPorHospital,
    PacienteDetallado,
    MedicoEstadisticas,
    ActividadReciente,
    DiagnosticosPorMes
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def verificar_admin(current_user: Usuario):
    """
    Verifica que el usuario actual sea un administrador.
    Lanza una excepción si no tiene permisos.
    """
    if current_user.tipo_usuario != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los administradores pueden acceder al dashboard"
        )


@router.get("/", response_model=DashboardResponse)
async def obtener_dashboard_completo(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene todos los datos del dashboard en una sola petición.
    
    Este endpoint combina todas las vistas SQL para proporcionar
    una vista completa del estado del sistema, incluyendo:
    - Estadísticas generales
    - Diagnósticos por clasificación
    - Citas por hospital
    - Actividad reciente
    - Tendencias mensuales
    - Pacientes y médicos destacados
    
    **Requiere:** Rol de administrador
    """
    verificar_admin(current_user)
    
    try:
        dashboard = DashboardService.obtener_dashboard_completo(db)
        return dashboard
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener datos del dashboard: {str(e)}"
        )


@router.get("/estadisticas-generales", response_model=EstadisticasGenerales)
async def obtener_estadisticas_generales(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas generales del sistema.
    
    Utiliza la vista SQL `vista_estadisticas_generales` que precalcula:
    - Total de usuarios activos por tipo
    - Estado de citas (programadas, completadas, canceladas)
    - Total de diagnósticos y hospitales
    
    **Requiere:** Rol de administrador
    """
    verificar_admin(current_user)
    
    try:
        return DashboardService.obtener_estadisticas_generales(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas generales: {str(e)}"
        )


@router.get("/diagnosticos-clasificacion", response_model=List[DiagnosticosPorClasificacion])
async def obtener_diagnosticos_por_clasificacion(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene la distribución de diagnósticos por clasificación.
    
    Utiliza la vista SQL `vista_diagnosticos_por_clasificacion` que agrupa
    diagnósticos por tipo de demencia y calcula:
    - Cantidad de diagnósticos por clasificación
    - Confianza promedio
    - Número de pacientes únicos
    
    **Requiere:** Rol de administrador
    """
    verificar_admin(current_user)
    
    try:
        return DashboardService.obtener_diagnosticos_por_clasificacion(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener diagnósticos por clasificación: {str(e)}"
        )


@router.get("/citas-hospital", response_model=List[CitasPorHospital])
async def obtener_citas_por_hospital(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas de citas agrupadas por hospital.
    
    Utiliza la vista SQL `vista_citas_por_hospital` que muestra:
    - Total de citas por hospital
    - Distribución por estado (programadas, completadas, canceladas, reprogramadas)
    - Ubicación del hospital
    
    **Requiere:** Rol de administrador
    """
    verificar_admin(current_user)
    
    try:
        return DashboardService.obtener_citas_por_hospital(db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener citas por hospital: {str(e)}"
        )


@router.get("/pacientes", response_model=List[PacienteDetallado])
async def obtener_pacientes_detallados(
    limit: int = Query(10, ge=1, le=100, description="Número de pacientes a retornar"),
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene información detallada de pacientes con sus métricas.
    
    Utiliza la vista SQL `vista_pacientes_detallada` que incluye:
    - Información demográfica
    - Total de diagnósticos y citas
    - Médicos asignados
    - Última actividad
    
    **Parámetros:**
    - limit: Número máximo de pacientes a retornar (1-100)
    
    **Requiere:** Rol de administrador
    """
    verificar_admin(current_user)
    
    try:
        return DashboardService.obtener_pacientes_detallados(db, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener pacientes: {str(e)}"
        )


@router.get("/medicos", response_model=List[MedicoEstadisticas])
async def obtener_medicos_estadisticas(
    limit: int = Query(10, ge=1, le=100, description="Número de médicos a retornar"),
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas de rendimiento de médicos.
    
    Utiliza la vista SQL `vista_medicos_estadisticas` que muestra:
    - Total de citas (completadas y programadas)
    - Pacientes asignados
    - Próximas citas
    - Hospital de afiliación
    
    **Parámetros:**
    - limit: Número máximo de médicos a retornar (1-100)
    
    **Requiere:** Rol de administrador
    """
    verificar_admin(current_user)
    
    try:
        return DashboardService.obtener_medicos_estadisticas(db, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas de médicos: {str(e)}"
        )


@router.get("/actividad-reciente", response_model=List[ActividadReciente])
async def obtener_actividad_reciente(
    limit: int = Query(20, ge=1, le=100, description="Número de eventos a retornar"),
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene los eventos más recientes del sistema.
    
    Utiliza la vista SQL `vista_actividad_reciente` que combina:
    - Diagnósticos realizados
    - Citas creadas/actualizadas
    - Nuevos registros de usuarios
    
    Los eventos están ordenados cronológicamente del más reciente al más antiguo.
    
    **Parámetros:**
    - limit: Número máximo de eventos a retornar (1-100)
    
    **Requiere:** Rol de administrador
    """
    verificar_admin(current_user)
    
    try:
        return DashboardService.obtener_actividad_reciente(db, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener actividad reciente: {str(e)}"
        )


@router.get("/tendencias-mensuales", response_model=List[DiagnosticosPorMes])
async def obtener_tendencias_mensuales(
    meses: int = Query(6, ge=1, le=24, description="Número de meses a retornar"),
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene tendencias mensuales de diagnósticos.
    
    Utiliza la vista SQL `vista_diagnosticos_por_mes` que muestra:
    - Volumen de diagnósticos por mes
    - Distribución por clasificación de demencia
    - Confianza promedio
    - Pacientes únicos
    
    **Parámetros:**
    - meses: Número de meses históricos a retornar (1-24)
    
    **Requiere:** Rol de administrador
    """
    verificar_admin(current_user)
    
    try:
        return DashboardService.obtener_diagnosticos_por_mes(db, meses=meses)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener tendencias mensuales: {str(e)}"
        )


@router.get("/estadisticas-personalizadas")
async def obtener_estadisticas_personalizadas(
    fecha_inicio: Optional[str] = Query(None, description="Fecha inicio (YYYY-MM-DD)"),
    fecha_fin: Optional[str] = Query(None, description="Fecha fin (YYYY-MM-DD)"),
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtiene estadísticas personalizadas con filtros de fecha.
    
    Permite analizar diagnósticos en un rango de fechas específico.
    
    **Parámetros:**
    - fecha_inicio: Fecha de inicio del período (formato: YYYY-MM-DD)
    - fecha_fin: Fecha de fin del período (formato: YYYY-MM-DD)
    
    **Requiere:** Rol de administrador
    """
    verificar_admin(current_user)
    
    try:
        return DashboardService.obtener_estadisticas_personalizadas(
            db,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al obtener estadísticas personalizadas: {str(e)}"
        )
