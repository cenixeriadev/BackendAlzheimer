from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func
from typing import List, Optional, Tuple
from datetime import datetime, timedelta, date
from fastapi import HTTPException, status

from app.models.cita import Cita, EstadoCita
from app.models.paciente import Paciente, EstadoAlzheimer
from app.models.medico import Medico
from app.models.hospital import Hospital
from app.models.usuario import Usuario, TipoUsuario
from app.schemas.cita import CitaCreate, CitaUpdate, CitaCambiarEstado, CitaResponse


class CitaService:
    """
    Servicio para gestión de citas con lógica de permisos híbrida:
    - Pacientes independientes gestionan sus propias citas
    - Cuidadores gestionan citas de pacientes con cuidador
    - Admins tienen acceso total
    """

    def __init__(self, db: Session):
        self.db = db

    # ==========================================
    # VALIDACIÓN DE PERMISOS
    # ==========================================

    async def validar_permisos_creacion(
        self, 
        usuario_id: int, 
        tipo_usuario: TipoUsuario, 
        paciente_id: int
    ) -> dict:
        """
        Valida permisos para crear cita según:
        - Paciente independiente: puede crear sus propias citas
        - Paciente con cuidador: solo el cuidador puede crear citas
        - Cuidador: puede crear citas para sus pacientes asignados
        - Admin: acceso total
        """
        # Obtener paciente con sus relaciones
        paciente = self.db.query(Paciente).filter(Paciente.id == paciente_id).first()
        
        if not paciente:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Paciente no encontrado"
            )

        # Si es PACIENTE
        if tipo_usuario == TipoUsuario.paciente:
            # Verificar que sea su propio perfil
            if paciente.usuario_id != usuario_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No puede crear citas para otros pacientes"
                )
            
            # Si tiene cuidador asignado, solo puede VER pero no CREAR
            if paciente.estado_alzheimer == EstadoAlzheimer.con_cuidador and paciente.cuidador_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Las citas deben ser gestionadas por su cuidador asignado"
                )
            
            return {"permitido": True, "rol": "paciente", "paciente": paciente}

        # Si es CUIDADOR
        if tipo_usuario == TipoUsuario.cuidador:
            # Verificar que sea el cuidador asignado
            if paciente.cuidador_id != usuario_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="No es el cuidador asignado a este paciente"
                )
            return {"permitido": True, "rol": "cuidador", "paciente": paciente}

        # Si es ADMIN
        if tipo_usuario == TipoUsuario.admin:
            return {"permitido": True, "rol": "admin", "paciente": paciente}

        # Médicos no pueden crear citas
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tiene permisos para crear citas"
        )

    async def validar_permisos_lectura(
        self, 
        usuario_id: int, 
        tipo_usuario: TipoUsuario, 
        cita_id: Optional[int] = None,
        paciente_id: Optional[int] = None
    ) -> dict:
        """
        Valida permisos de lectura para citas
        """
        # Admin tiene acceso total
        if tipo_usuario == TipoUsuario.admin:
            return {"permitido": True, "filtro_necesario": False}

        # Si es para una cita específica
        if cita_id:
            cita = self.db.query(Cita).options(
                joinedload(Cita.paciente)
            ).filter(Cita.id == cita_id).first()
            
            if not cita:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Cita no encontrada"
                )

            # Validar acceso según tipo de usuario
            if tipo_usuario == TipoUsuario.paciente:
                if cita.paciente.usuario_id != usuario_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="No tiene acceso a esta cita"
                    )
            elif tipo_usuario == TipoUsuario.cuidador:
                if cita.paciente.cuidador_id != usuario_id:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="No es el cuidador asignado"
                    )
            elif tipo_usuario == TipoUsuario.medico:
                if cita.medico_id != self._obtener_medico_id(usuario_id):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="No es el médico asignado a esta cita"
                    )

            return {"permitido": True, "cita": cita}

        # Para listados, devolver filtros necesarios
        return {"permitido": True, "filtro_necesario": True, "usuario_id": usuario_id}

    def _obtener_medico_id(self, usuario_id: int) -> Optional[int]:
        """Obtiene el ID de médico asociado al usuario"""
        medico = self.db.query(Medico).filter(Medico.usuario_id == usuario_id).first()
        return medico.id if medico else None

    def _obtener_paciente_id(self, usuario_id: int) -> Optional[int]:
        """Obtiene el ID de paciente asociado al usuario"""
        paciente = self.db.query(Paciente).filter(Paciente.usuario_id == usuario_id).first()
        return paciente.id if paciente else None

    # ==========================================
    # OPERACIONES CRUD
    # ==========================================

    async def crear_cita(
        self,
        cita_data: CitaCreate,
        usuario_id: int,
        tipo_usuario: TipoUsuario
    ) -> Cita:
        """Crear una nueva cita con validación de permisos"""
        
        # Validar permisos
        await self.validar_permisos_creacion(usuario_id, tipo_usuario, cita_data.paciente_id)

        # Validar que el médico exista
        medico = self.db.query(Medico).filter(Medico.id == cita_data.medico_id).first()
        if not medico:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Médico no encontrado"
            )

        # Validar que el hospital exista (si se proporciona)
        if cita_data.hospital_id:
            hospital = self.db.query(Hospital).filter(Hospital.id == cita_data.hospital_id).first()
            if not hospital:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Hospital no encontrado"
                )

        # Validar disponibilidad del médico
        conflicto = await self._verificar_conflicto_horario(
            cita_data.medico_id,
            cita_data.fecha_hora
        )
        if conflicto:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"El médico ya tiene una cita programada a las {cita_data.fecha_hora}"
            )

        # Crear la cita
        nueva_cita = Cita(**cita_data.model_dump())
        self.db.add(nueva_cita)
        self.db.commit()
        self.db.refresh(nueva_cita)

        return nueva_cita

    async def obtener_cita(
        self,
        cita_id: int,
        usuario_id: int,
        tipo_usuario: TipoUsuario
    ) -> Cita:
        """Obtener una cita específica"""
        
        # Validar permisos
        permisos = await self.validar_permisos_lectura(usuario_id, tipo_usuario, cita_id=cita_id)
        
        cita = self.db.query(Cita).options(
            joinedload(Cita.paciente),
            joinedload(Cita.medico),
            joinedload(Cita.hospital)
        ).filter(Cita.id == cita_id).first()

        if not cita:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cita no encontrada"
            )

        return cita

    async def listar_citas(
        self,
        usuario_id: int,
        tipo_usuario: TipoUsuario,
        paciente_id: Optional[int] = None,
        medico_id: Optional[int] = None,
        hospital_id: Optional[int] = None,
        estado: Optional[EstadoCita] = None,
        fecha_desde: Optional[str] = None,
        fecha_hasta: Optional[str] = None,
        page: int = 1,
        limit: int = 10
    ) -> Tuple[List[Cita], int]:
        """Listar citas con filtros y paginación"""
        
        # Construir query base
        query = self.db.query(Cita).options(
            joinedload(Cita.paciente),
            joinedload(Cita.medico),
            joinedload(Cita.hospital)
        )

        # Aplicar filtros según tipo de usuario
        if tipo_usuario == TipoUsuario.paciente:
            # Solo sus propias citas
            paciente_propio_id = self._obtener_paciente_id(usuario_id)
            query = query.filter(Cita.paciente_id == paciente_propio_id)
        
        elif tipo_usuario == TipoUsuario.cuidador:
            # Citas de pacientes a su cargo
            pacientes_a_cargo = self.db.query(Paciente.id).filter(
                Paciente.cuidador_id == usuario_id
            ).all()
            paciente_ids = [p.id for p in pacientes_a_cargo]
            query = query.filter(Cita.paciente_id.in_(paciente_ids))
        
        elif tipo_usuario == TipoUsuario.medico:
            # Solo sus citas como médico
            medico_propio_id = self._obtener_medico_id(usuario_id)
            query = query.filter(Cita.medico_id == medico_propio_id)

        # Aplicar filtros adicionales
        if paciente_id:
            query = query.filter(Cita.paciente_id == paciente_id)
        if medico_id:
            query = query.filter(Cita.medico_id == medico_id)
        if hospital_id:
            query = query.filter(Cita.hospital_id == hospital_id)
        if estado:
            query = query.filter(Cita.estado == estado)
        if fecha_desde:
            query = query.filter(Cita.fecha_hora >= datetime.fromisoformat(fecha_desde))
        if fecha_hasta:
            query = query.filter(Cita.fecha_hora <= datetime.fromisoformat(fecha_hasta))

        # Obtener total
        total = query.count()

        # Aplicar paginación y ordenar por fecha
        citas = query.order_by(Cita.fecha_hora.desc()).offset((page - 1) * limit).limit(limit).all()

        return citas, total

    async def actualizar_cita(
        self,
        cita_id: int,
        cita_data: CitaUpdate,
        usuario_id: int,
        tipo_usuario: TipoUsuario
    ) -> Cita:
        """Actualizar una cita existente"""
        
        # Obtener cita y validar permisos
        cita = await self.obtener_cita(cita_id, usuario_id, tipo_usuario)

        # No permitir actualizar citas completadas o canceladas
        if cita.estado in [EstadoCita.completada, EstadoCita.cancelada]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No se puede actualizar una cita {cita.estado}"
            )

        # Validar permisos de edición
        await self.validar_permisos_creacion(usuario_id, tipo_usuario, cita.paciente_id)

        # Si se cambia la fecha, validar disponibilidad
        if cita_data.fecha_hora and cita_data.fecha_hora != cita.fecha_hora:
            conflicto = await self._verificar_conflicto_horario(
                cita.medico_id,
                cita_data.fecha_hora,
                excluir_cita_id=cita_id
            )
            if conflicto:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"El médico ya tiene una cita programada a las {cita_data.fecha_hora}"
                )

        # Actualizar campos
        update_data = cita_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(cita, field, value)

        cita.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(cita)

        return cita

    async def cambiar_estado_cita(
        self,
        cita_id: int,
        estado_data: CitaCambiarEstado,
        usuario_id: int,
        tipo_usuario: TipoUsuario
    ) -> Cita:
        """Cambiar el estado de una cita"""
        
        # Obtener cita y validar permisos
        cita = await self.obtener_cita(cita_id, usuario_id, tipo_usuario)

        # Validar transiciones de estado
        if cita.estado == EstadoCita.completada:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede cambiar el estado de una cita completada"
            )

        # Actualizar estado
        cita.estado = estado_data.estado
        
        # Agregar motivo del cambio a las notas si se proporciona
        if estado_data.motivo_cambio:
            nota_cambio = f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M')}] Estado cambiado a '{estado_data.estado}': {estado_data.motivo_cambio}"
            cita.notas = (cita.notas or "") + nota_cambio

        cita.updated_at = datetime.now()
        self.db.commit()
        self.db.refresh(cita)

        return cita

    async def cancelar_cita(
        self,
        cita_id: int,
        motivo: str,
        usuario_id: int,
        tipo_usuario: TipoUsuario
    ) -> Cita:
        """Cancelar una cita"""
        
        estado_data = CitaCambiarEstado(
            estado=EstadoCita.cancelada,
            motivo_cambio=motivo
        )
        
        return await self.cambiar_estado_cita(cita_id, estado_data, usuario_id, tipo_usuario)

    # ==========================================
    # FUNCIONES AUXILIARES
    # ==========================================

    async def _verificar_conflicto_horario(
        self,
        medico_id: int,
        fecha_hora: datetime,
        excluir_cita_id: Optional[int] = None,
        duracion_minutos: int = 60
    ) -> bool:
        """
        Verifica si hay conflicto de horario para el médico
        Asume que cada cita dura 60 minutos por defecto
        """
        hora_inicio = fecha_hora
        hora_fin = fecha_hora + timedelta(minutes=duracion_minutos)

        query = self.db.query(Cita).filter(
            and_(
                Cita.medico_id == medico_id,
                Cita.estado.in_([EstadoCita.programada, EstadoCita.reprogramada]),
                or_(
                    # La nueva cita empieza durante una cita existente
                    and_(
                        Cita.fecha_hora <= hora_inicio,
                        Cita.fecha_hora + timedelta(minutes=duracion_minutos) > hora_inicio
                    ),
                    # La nueva cita termina durante una cita existente
                    and_(
                        Cita.fecha_hora < hora_fin,
                        Cita.fecha_hora + timedelta(minutes=duracion_minutos) >= hora_fin
                    ),
                    # La nueva cita engloba una cita existente
                    and_(
                        Cita.fecha_hora >= hora_inicio,
                        Cita.fecha_hora < hora_fin
                    )
                )
            )
        )

        if excluir_cita_id:
            query = query.filter(Cita.id != excluir_cita_id)

        return query.first() is not None

    async def obtener_disponibilidad_medico(
        self,
        medico_id: int,
        fecha: date,
        hospital_id: Optional[int] = None
    ) -> dict:
        """
        Obtiene la disponibilidad del médico para un día específico
        Retorna horarios disponibles en bloques de 1 hora (8:00 - 18:00)
        """
        # Validar que el médico exista
        medico = self.db.query(Medico).filter(Medico.id == medico_id).first()
        if not medico:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Médico no encontrado"
            )

        # Obtener citas programadas para ese día
        inicio_dia = datetime.combine(fecha, datetime.min.time())
        fin_dia = datetime.combine(fecha, datetime.max.time())

        citas_programadas = self.db.query(Cita).filter(
            and_(
                Cita.medico_id == medico_id,
                Cita.fecha_hora >= inicio_dia,
                Cita.fecha_hora <= fin_dia,
                Cita.estado.in_([EstadoCita.programada, EstadoCita.reprogramada])
            )
        ).all()

        # Generar horarios disponibles (8:00 - 18:00, bloques de 1 hora)
        horarios = []
        hora_actual = inicio_dia.replace(hour=8, minute=0, second=0, microsecond=0)
        hora_fin_jornada = inicio_dia.replace(hour=18, minute=0, second=0, microsecond=0)

        while hora_actual < hora_fin_jornada:
            # Verificar si hay conflicto
            ocupado = any(
                cita.fecha_hora <= hora_actual < cita.fecha_hora + timedelta(hours=1)
                for cita in citas_programadas
            )

            horarios.append({
                "hora_inicio": hora_actual.strftime("%H:%M"),
                "hora_fin": (hora_actual + timedelta(hours=1)).strftime("%H:%M"),
                "disponible": not ocupado
            })

            hora_actual += timedelta(hours=1)

        return {
            "medico_id": medico_id,
            "fecha": fecha.isoformat(),
            "horarios": horarios
        }

    async def obtener_citas_proximas(
        self,
        usuario_id: int,
        tipo_usuario: TipoUsuario,
        dias: int = 7
    ) -> List[Cita]:
        """Obtener citas próximas para un usuario"""
        
        fecha_inicio = datetime.now()
        fecha_fin = fecha_inicio + timedelta(days=dias)

        citas, _ = await self.listar_citas(
            usuario_id=usuario_id,
            tipo_usuario=tipo_usuario,
            estado=EstadoCita.programada,
            fecha_desde=fecha_inicio.isoformat(),
            fecha_hasta=fecha_fin.isoformat(),
            page=1,
            limit=100
        )

        return citas
