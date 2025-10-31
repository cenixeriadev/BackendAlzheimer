from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
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
    if current_user.tipo_usuario != "paciente":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los pacientes pueden subir imágenes para diagnóstico"
        )

    # DEBUG 
    print(f" Archivo recibido: {file.filename}")
    print(f" Content-Type: {file.content_type}")

    filepath = None
    try:
        contents = await file.read()
        
        if len(contents) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo está vacío"
            )

        print(f"a Tamaño archivo: {len(contents)} bytes")

        # Validar imagen
        try:
            image = Image.open(io.BytesIO(contents))
            print(f"b Formato detectado: {image.format}")
            print(f"c Dimensiones: {image.size}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo no es una imagen válida: {str(e)}"
            )

        if image.mode != 'RGB':
            image = image.convert('RGB')

        # Guardar imagen temporal
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(UPLOAD_DIR, filename)
        image.save(filepath, 'JPEG', quality=90)
        
        print(f"---Imagen guardada temporalmente: {filepath}")

        analisis_result = await roboflow_service.analyze_image(filepath)

        print(f"Análisis completado")

        return AnalisisResponse(
            resultado=analisis_result["resultado"],
            confianza=analisis_result["confianza"],
            output_image=analisis_result.get("output_image"),
            dynamic_crop=analisis_result.get("dynamic_crop"),
            diagnostico_id=0,  # temporal
            datos_roboflow=analisis_result.get("datos_roboflow")
        )

    except HTTPException:
        raise
    except Exception as e:
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"--. Archivo temporal eliminado: {filepath}")
            except:
                pass
        
        print(f"e Error general: {str(e)}")
        import traceback
        print(f"c Traceback completo: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando la imagen: {str(e)}"
        )
    finally:
        await file.close()


#  RUTAS BD
"""
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
"""