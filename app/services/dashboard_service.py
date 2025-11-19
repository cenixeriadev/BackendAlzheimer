from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Any
from app.schemas.dashboard import (
    EstadisticasGenerales,
    DiagnosticosPorClasificacion,
    CitasPorHospital,
    PacienteDetallado,
    MedicoEstadisticas,
    ActividadReciente,
    DiagnosticosPorMes,
    DashboardResponse
)


class DashboardService:
    """
    Servicio para obtener datos del dashboard utilizando las vistas SQL creadas.
    
    Las vistas SQL son tablas virtuales que ejecutan consultas complejas
    y devuelven resultados precalculados. En FastAPI, las consultamos como
    si fueran tablas normales usando SQLAlchemy.
    """

    @staticmethod
    def obtener_estadisticas_generales(db: Session) -> EstadisticasGenerales:
        """
        Obtiene las estadísticas generales del sistema usando la vista SQL.
        
        La vista 'vista_estadisticas_generales' devuelve un solo registro con
        conteos agregados de usuarios, citas y diagnósticos.
        """
        query = text("SELECT * FROM vista_estadisticas_generales")
        result = db.execute(query).fetchone()
        
        if not result:
            # Valores por defecto si no hay datos
            return EstadisticasGenerales(
                total_pacientes_activos=0,
                total_medicos_activos=0,
                total_admins_activos=0,
                total_usuarios_activos=0,
                citas_programadas=0,
                citas_completadas=0,
                citas_canceladas=0,
                total_diagnosticos=0,
                total_hospitales=0,
                total_asignaciones=0
            )
        
        # Convertir el resultado a un diccionario usando _mapping
        return EstadisticasGenerales(**dict(result._mapping))

    @staticmethod
    def obtener_diagnosticos_por_clasificacion(db: Session) -> List[DiagnosticosPorClasificacion]:
        """
        Obtiene la distribución de diagnósticos por clasificación.
        
        La vista agrupa diagnósticos por tipo de demencia y calcula
        estadísticas como cantidad y confianza promedio.
        """
        query = text("SELECT * FROM vista_diagnosticos_por_clasificacion")
        results = db.execute(query).fetchall()
        
        return [DiagnosticosPorClasificacion(**dict(row._mapping)) for row in results]

    @staticmethod
    def obtener_citas_por_hospital(db: Session) -> List[CitasPorHospital]:
        """
        Obtiene estadísticas de citas agrupadas por hospital.
        
        Muestra el volumen de citas y su distribución por estado
        para cada hospital en el sistema.
        """
        query = text("SELECT * FROM vista_citas_por_hospital")
        results = db.execute(query).fetchall()
        
        return [CitasPorHospital(**dict(row._mapping)) for row in results]

    @staticmethod
    def obtener_pacientes_detallados(db: Session, limit: int = 10) -> List[PacienteDetallado]:
        """
        Obtiene información detallada de pacientes con sus métricas.
        
        Incluye información demográfica y estadísticas de actividad
        como número de diagnósticos y citas.
        """
        query = text(f"""
            SELECT * FROM vista_pacientes_detallada 
            ORDER BY total_diagnosticos DESC, ultimo_diagnostico DESC
            LIMIT :limit
        """)
        results = db.execute(query, {"limit": limit}).fetchall()
        
        return [PacienteDetallado(**dict(row._mapping)) for row in results]

    @staticmethod
    def obtener_medicos_estadisticas(db: Session, limit: int = 10) -> List[MedicoEstadisticas]:
        """
        Obtiene estadísticas de rendimiento de médicos.
        
        Incluye número de citas, pacientes asignados y próximas citas.
        """
        query = text(f"""
            SELECT * FROM vista_medicos_estadisticas 
            ORDER BY total_citas DESC, citas_completadas DESC
            LIMIT :limit
        """)
        results = db.execute(query, {"limit": limit}).fetchall()
        
        return [MedicoEstadisticas(**dict(row._mapping)) for row in results]

    @staticmethod
    def obtener_actividad_reciente(db: Session, limit: int = 20) -> List[ActividadReciente]:
        """
        Obtiene los eventos más recientes del sistema.
        
        La vista combina diagnósticos, citas y registros de usuarios
        en una línea de tiempo unificada.
        """
        query = text(f"""
            SELECT * FROM vista_actividad_reciente 
            LIMIT :limit
        """)
        results = db.execute(query, {"limit": limit}).fetchall()
        
        return [ActividadReciente(**dict(row._mapping)) for row in results]

    @staticmethod
    def obtener_diagnosticos_por_mes(db: Session, meses: int = 6) -> List[DiagnosticosPorMes]:
        """
        Obtiene tendencias mensuales de diagnósticos.
        
        Muestra el volumen de diagnósticos por mes y su distribución
        por clasificación de demencia.
        """
        query = text(f"""
            SELECT * FROM vista_diagnosticos_por_mes 
            ORDER BY mes DESC
            LIMIT :meses
        """)
        results = db.execute(query, {"meses": meses}).fetchall()
        
        return [DiagnosticosPorMes(**dict(row._mapping)) for row in results]

    @staticmethod
    def obtener_dashboard_completo(db: Session) -> DashboardResponse:
        """
        Obtiene todos los datos del dashboard en una sola llamada.
        
        Combina todas las vistas para proporcionar una vista completa
        del estado del sistema.
        """
        return DashboardResponse(
            estadisticas_generales=DashboardService.obtener_estadisticas_generales(db),
            diagnosticos_clasificacion=DashboardService.obtener_diagnosticos_por_clasificacion(db),
            citas_por_hospital=DashboardService.obtener_citas_por_hospital(db),
            actividad_reciente=DashboardService.obtener_actividad_reciente(db),
            diagnosticos_por_mes=DashboardService.obtener_diagnosticos_por_mes(db),
            pacientes_destacados=DashboardService.obtener_pacientes_detallados(db, limit=5),
            medicos_destacados=DashboardService.obtener_medicos_estadisticas(db, limit=5)
        )

    @staticmethod
    def obtener_estadisticas_personalizadas(
        db: Session,
        fecha_inicio: str = None,
        fecha_fin: str = None
    ) -> Dict[str, Any]:
        """
        Permite consultas personalizadas con filtros de fecha.
        
        Ejemplo de cómo puedes extender las vistas con filtros adicionales.
        """
        query = text("""
            SELECT 
                COUNT(DISTINCT d.paciente_id) as pacientes_unicos,
                COUNT(d.id) as total_diagnosticos,
                AVG(d.confianza) as confianza_promedio
            FROM diagnostico d
            WHERE (:fecha_inicio IS NULL OR d.created_at >= :fecha_inicio::timestamp)
              AND (:fecha_fin IS NULL OR d.created_at <= :fecha_fin::timestamp)
        """)
        
        result = db.execute(query, {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin
        }).fetchone()
        
        return dict(result._mapping) if result else {}
