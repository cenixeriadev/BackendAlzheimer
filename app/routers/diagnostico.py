from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import uuid
import os
import io
from PIL import Image
from app.database import get_db
from app.models.diagnostico import Diagnostico
from app.models.usuario import Usuario
from app.schemas.diagnostico import DiagnosticoResponse, AnalisisResponse
from app.services.roboflow_service import roboflow_service
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/api/diagnosticos", tags=["Diagnósticos"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/analizar", response_model=AnalisisResponse)
async def analizar_imagen(
    file: UploadFile = File(...),
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Analiza una imagen médica usando IA de Roboflow
    """
    if current_user.tipo_usuario != "paciente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los pacientes pueden subir imágenes para diagnóstico"
        )

    # DEBUG archivo
    print(f"📁 Archivo recibido: {file.filename}")
    print(f"📋 Content-Type: {file.content_type}")

    filepath = None
    try:
        contents = await file.read()
        
        if len(contents) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo está vacío"
            )

        print(f"📊 Tamaño archivo: {len(contents)} bytes")

        # Validar
        try:
            image = Image.open(io.BytesIO(contents))
            print(f"🖼️ Formato detectado: {image.format}")
            print(f"📐 Dimensiones: {image.size}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo no es una imagen válida: {str(e)}"
            )

        # Convertir a RGB si es necesario
        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Guardar imagen temporal
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(UPLOAD_DIR, filename)
        image.save(filepath, 'JPEG', quality=90)
        
        print(f"💾 Imagen guardada: {filepath}")

        #  Roboflow
        analisis_result = await roboflow_service.analyze_image(filepath)

        # Guardar en base de datos
        nuevo_diagnostico = Diagnostico(
            paciente_id=current_user.id,
            imagen_url=filename,
            resultado_ia=analisis_result["resultado"],
            confianza_ia=analisis_result["confianza_float"],
            estado="pendiente"
        )

        db.add(nuevo_diagnostico)
        db.commit()
        db.refresh(nuevo_diagnostico)

        print(f"✅ Diagnóstico guardado ID: {nuevo_diagnostico.id}")

        return AnalisisResponse(
            resultado=analisis_result["resultado"],
            confianza=analisis_result["confianza"],
            output_image=analisis_result.get("output_image"),
            dynamic_crop=analisis_result.get("dynamic_crop"),
            diagnostico_id=nuevo_diagnostico.id
        )

    except HTTPException:
        raise
    except Exception as e:
        # Limpiar en caso de error
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"🧹 Archivo temporal eliminado: {filepath}")
            except:
                pass
        
        print(f"❌ Error general: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando la imagen: {str(e)}"
        )
    finally:
        await file.close()

# Los otros endpoints se mantienen igual
@router.get("/mis-diagnosticos", response_model=List[DiagnosticoResponse])
async def obtener_mis_diagnosticos(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    diagnosticos = db.query(Diagnostico).filter(
        Diagnostico.paciente_id == current_user.id
    ).order_by(Diagnostico.created_at.desc()).all()
    return diagnosticos

@router.get("/{diagnostico_id}", response_model=DiagnosticoResponse)
async def obtener_diagnostico(
    diagnostico_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    diagnostico = db.query(Diagnostico).filter(Diagnostico.id == diagnostico_id).first()
    
    if not diagnostico:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")
    
    if (current_user.tipo_usuario == "paciente" and 
        diagnostico.paciente_id != current_user.id):
        raise HTTPException(status_code=403, detail="No tienes acceso a este diagnóstico")
    
    return diagnostico