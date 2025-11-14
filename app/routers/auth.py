from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.utils.database import get_db
from app.schemas.auth import Token, LoginRequest, RegisterRequest
from app.schemas.usuario import UsuarioResponse
from app.models.usuario import Usuario
from app.models.paciente import Paciente
from app.models.cuidador import Cuidador
from app.models.medico import Medico
from app.models.admin import Admin
from app.utils.security import verify_password, get_password_hash, create_access_token
from app.utils.config import settings
from app.utils.dependencies import get_current_active_user

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


@router.post("/register", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: RegisterRequest, db: Session = Depends(get_db)):

    existing_user = db.query(Usuario).filter(Usuario.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de usuario ya está registrado"
        )
    
    if user_data.email:
        if user_data.tipo_usuario == "paciente":
            existing_email = db.query(Paciente).filter(Paciente.email == user_data.email).first()
        elif user_data.tipo_usuario == "cuidador":
            existing_email = db.query(Cuidador).filter(Cuidador.email == user_data.email).first()
        elif user_data.tipo_usuario == "medico":
            existing_email = db.query(Medico).filter(Medico.email == user_data.email).first()
        else:
            existing_email = None
            
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está registrado"
            )
    
    if user_data.tipo_usuario == "paciente" and not user_data.fecha_nacimiento:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La fecha de nacimiento es requerida para pacientes"
        )
    
    if user_data.tipo_usuario == "cuidador" and not user_data.relacion_paciente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La relación con el paciente es requerida para cuidadores"
        )
    
    if user_data.tipo_usuario == "medico":
        if not user_data.cmp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El CMP es requerido para médicos"
            )
        existing_cmp = db.query(Medico).filter(Medico.cmp == user_data.cmp).first()
        if existing_cmp:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El CMP ya está registrado"
            )
    
    hashed_password = get_password_hash(user_data.password)
    new_user = Usuario(
        username=user_data.username,
        password_hash=hashed_password,
        tipo_usuario=user_data.tipo_usuario,
        estado=True
    )
    
    db.add(new_user)
    db.flush() 
    
    if user_data.tipo_usuario == "paciente":
        perfil = Paciente(
            usuario_id=new_user.id,
            nombre=user_data.nombre,
            apellido=user_data.apellido,
            fecha_nacimiento=user_data.fecha_nacimiento,
            genero=user_data.genero,
            numero_identidad=user_data.numero_identidad,
            telefono=user_data.telefono,
            email=user_data.email,
            direccion=user_data.direccion,
            ciudad=user_data.ciudad,
            estado_alzheimer=user_data.estado_alzheimer
        )
        db.add(perfil)
    
    elif user_data.tipo_usuario == "cuidador":
        perfil = Cuidador(
            usuario_id=new_user.id,
            nombre=user_data.nombre,
            apellido=user_data.apellido,
            relacion_paciente=user_data.relacion_paciente,
            telefono=user_data.telefono,
            email=user_data.email,
            direccion=user_data.direccion
        )
        db.add(perfil)
    
    elif user_data.tipo_usuario == "medico":
        perfil = Medico(
            usuario_id=new_user.id,
            nombre=user_data.nombre,
            apellido=user_data.apellido,
            cmp=user_data.cmp,
            especialidad=user_data.especialidad,
            numero_identidad=user_data.numero_identidad,
            telefono=user_data.telefono,
            email=user_data.email,
            hospital_afiliacion=user_data.hospital_afiliacion
        )
        db.add(perfil)
    
    elif user_data.tipo_usuario == "admin":
        perfil = Admin(
            usuario_id=new_user.id,
            nivel_acceso=user_data.nivel_acceso,
            permisos=user_data.permisos
        )
        db.add(perfil)
    
    db.commit()
    db.refresh(new_user)
    
    response = UsuarioResponse(
        id=new_user.id,
        username=new_user.username,
        tipo_usuario=new_user.tipo_usuario,
        foto_perfil_url=new_user.foto_perfil_url,
        estado=new_user.estado,
        created_at=new_user.created_at,
        nombre=user_data.nombre,
        apellido=user_data.apellido,
        email=user_data.email,
        telefono=user_data.telefono
    )
    
    return response


@router.post("/login", response_model=Token)
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):

    user = db.query(Usuario).filter(Usuario.username == login_data.username).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar contraseña
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar si el usuario está activo
    if not user.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo. Contacte al administrador"
        )
    
    # Crear token JWT
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "tipo_usuario": user.tipo_usuario},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login/form", response_model=Token)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Endpoint alternativo de login compatible con OAuth2PasswordRequestForm.
    
    Permite el uso de formularios estándar de OAuth2.
    """
    user = db.query(Usuario).filter(Usuario.username == form_data.username).first()
    
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.estado:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario inactivo"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "tipo_usuario": user.tipo_usuario},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UsuarioResponse)
async def read_users_me(current_user: Usuario = Depends(get_current_active_user), db: Session = Depends(get_db)):
    """
    Obtiene la información del usuario actual autenticado.
    
    Requiere un token JWT válido.
    """
    nombre = None
    apellido = None
    email = None
    telefono = None
    
    # Cargar las relaciones explícitamente si es necesario
    if current_user.tipo_usuario == "paciente":
        # Forzar la carga de la relación paciente
        db.refresh(current_user, ["paciente"])
        if current_user.paciente:
            nombre = current_user.paciente.nombre
            apellido = current_user.paciente.apellido
            email = current_user.paciente.email
            telefono = current_user.paciente.telefono
            
    elif current_user.tipo_usuario == "cuidador":
        db.refresh(current_user, ["cuidador"])
        if current_user.cuidador:
            nombre = current_user.cuidador.nombre
            apellido = current_user.cuidador.apellido
            email = current_user.cuidador.email
            telefono = current_user.cuidador.telefono
            
    elif current_user.tipo_usuario == "medico":
        db.refresh(current_user, ["medico"])
        if current_user.medico:
            nombre = current_user.medico.nombre
            apellido = current_user.medico.apellido
            email = current_user.medico.email
            telefono = current_user.medico.telefono
    
    return UsuarioResponse(
        id=current_user.id,
        username=current_user.username,
        tipo_usuario=current_user.tipo_usuario,
        foto_perfil_url=current_user.foto_perfil_url,
        estado=current_user.estado,
        created_at=current_user.created_at,
        nombre=nombre,
        apellido=apellido,
        email=email,
        telefono=telefono
    )