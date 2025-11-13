from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
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
from app.services.storage_service import storage_service
from app.dependencies import get_current_active_user

router = APIRouter(prefix="/api/diagnosticos", tags=["Diagnósticos"])

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ========== RUTAS ESPECÍFICAS PRIMERO ==========

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

    filepath = None
    try:
        contents = await file.read()
        
        if len(contents) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El archivo está vacío"
            )

        # Validar imagen
        try:
            image = Image.open(io.BytesIO(contents))
            if image.mode != 'RGB':
                image = image.convert('RGB')
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"El archivo no es una imagen válida: {str(e)}"
            )

        # Guardar imagen temporal
        filename = f"{uuid.uuid4()}.jpg"
        filepath = os.path.join(UPLOAD_DIR, filename)
        image.save(filepath, 'JPEG', quality=90)
        
        print(f"--- Imagen guardada temporalmente: {filepath}")

        # Analizar con Roboflow
        analisis_result = await roboflow_service.analyze_image(filepath)

        # Guardar en storage y base de datos (sin imagen procesada)
        diagnostico_creado = await _guardar_diagnostico_completo(
            db=db,
            current_user=current_user,
            analisis_result=analisis_result,
            original_filename=file.filename
        )

        return AnalisisResponse(
            resultado=analisis_result["resultado"],
            confianza=analisis_result["confianza"],
            diagnostico_id=diagnostico_creado.id,
            datos_roboflow=analisis_result.get("datos_roboflow")
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"e Error general: {str(e)}")
        import traceback
        print(f"c Traceback completo: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error procesando la imagen: {str(e)}"
        )
    finally:
        # Limpiar archivo temporal
        if filepath and os.path.exists(filepath):
            try:
                os.remove(filepath)
                print(f"--. Archivo temporal eliminado: {filepath}")
            except:
                pass
        await file.close()

@router.get("/historial", response_model=Dict[str, Any])
async def obtener_historial_diagnosticos(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint simple sin paginación para debugging
    """
    diagnosticos = db.query(Diagnostico).filter(
        Diagnostico.paciente_id == current_user.id
    ).order_by(Diagnostico.created_at.desc()).limit(50).all()
    
    # Convertir a esquema Pydantic
    diagnosticos_response = [DiagnosticoResponse.from_orm(diagnostico) for diagnostico in diagnosticos]
    
    return {
        "diagnosticos": diagnosticos_response,
        "total": len(diagnosticos_response)
    }


@router.get("/mis-diagnosticos", response_model=List[DiagnosticoResponse])
async def obtener_mis_diagnosticos(
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtener todos los diagnósticos del usuario (sin paginación)
    """
    diagnosticos = db.query(Diagnostico).filter(
        Diagnostico.paciente_id == current_user.id
    ).order_by(Diagnostico.created_at.desc()).all()
    
    # Convertir a esquema Pydantic
    return [DiagnosticoResponse.from_orm(diagnostico) for diagnostico in diagnosticos]

@router.get("/detalle/{diagnostico_id}", response_model=Dict[str, Any])
async def obtener_detalle_diagnostico(
    diagnostico_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtener detalle completo de un diagnóstico específico
    """
    diagnostico = db.query(Diagnostico).filter(
        Diagnostico.id == diagnostico_id,
        Diagnostico.paciente_id == current_user.id
    ).first()
    
    if not diagnostico:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")
    
    # Procesar datos de Roboflow para frontend
    datos_detallados = await _procesar_datos_roboflow(diagnostico.datos_roboflow)
    
    return {
        "id": diagnostico.id,
        "fecha_analisis": diagnostico.created_at,
        "resultado": diagnostico.resultado,
        "confianza": diagnostico.confianza,
        "clase_original": diagnostico.clase_original,
        "imagen_original_url": diagnostico.imagen_original_url,
        "imagen_procesada_url": diagnostico.imagen_procesada_url,
        "estado": diagnostico.estado,
        "datos_detallados": datos_detallados
    }

@router.get("/{diagnostico_id}", response_model=DiagnosticoResponse)
async def obtener_diagnostico(
    diagnostico_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtener diagnóstico básico por ID
    """
    diagnostico = db.query(Diagnostico).filter(Diagnostico.id == diagnostico_id).first()
    
    if not diagnostico:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")
    
    if (current_user.tipo_usuario == "paciente" and 
        diagnostico.paciente_id != current_user.id):
        raise HTTPException(status_code=403, detail="No tienes acceso a este diagnóstico")
    
    return diagnostico

# ========== FUNCIONES AUXILIARES ==========

async def _guardar_diagnostico_completo(
    db: Session,
    current_user: Usuario,
    analisis_result: Dict[str, Any],
    original_filename: str
) -> Diagnostico:
    """
    Guardar diagnóstico completo SIN imagen procesada
    """
    try:
        # 1. Subir imagen original al storage
        original_upload = await storage_service.upload_file(
            file_content=analisis_result["original_image_data"],
            filename=f"original_{uuid.uuid4()}_{original_filename}",
            content_type="image/jpeg"
        )

        # 2. Crear registro en base de datos SIN imagen procesada
        diagnostico = Diagnostico(
            paciente_id=current_user.id,
            resultado=analisis_result["resultado"],
            confianza=analisis_result["confianza_float"],
            clase_original=analisis_result["clase_original"],
            imagen_original_url=original_upload["url"],
            imagen_procesada_url=None,  # No guardar imagen procesada
            datos_roboflow=analisis_result.get("datos_roboflow"),
            estado="completado"
        )

        db.add(diagnostico)
        db.commit()
        db.refresh(diagnostico)

        print(f"✓ Diagnóstico guardado en BD con ID: {diagnostico.id}")
        return diagnostico

    except Exception as e:
        db.rollback()
        print(f"e Error guardando diagnóstico: {e}")
        import traceback
        print(f"c Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error guardando diagnóstico: {e}"
        )

async def _procesar_datos_roboflow(datos_roboflow: Dict) -> Dict:
    """
    Procesar y estructurar los datos de Roboflow para el frontend
    """
    if not datos_roboflow:
        return {}
    
    try:
        processed_data = {
            "predicciones": [],
            "metadatos_imagen": {},
            "estadisticas": {}
        }
        
        # Extraer predicciones
        if "predictions" in datos_roboflow:
            predictions = datos_roboflow["predictions"]
            
            # Metadatos de imagen
            if "image" in predictions:
                processed_data["metadatos_imagen"] = {
                    "ancho": predictions["image"].get("width"),
                    "alto": predictions["image"].get("height")
                }
            
            # Lista de predicciones
            if "predictions" in predictions and isinstance(predictions["predictions"], list):
                for pred in predictions["predictions"]:
                    processed_data["predicciones"].append({
                        "clase": pred.get("class"),
                        "confianza": pred.get("confidence"),
                        "clase_id": pred.get("class_id"),
                        "bbox": {
                            "x": pred.get("x"),
                            "y": pred.get("y"),
                            "ancho": pred.get("width"),
                            "alto": pred.get("height")
                        } if all(k in pred for k in ["x", "y", "width", "height"]) else None
                    })
        
        # Estadísticas
        if processed_data["predicciones"]:
            confianzas = [p["confianza"] for p in processed_data["predicciones"] if p["confianza"]]
            if confianzas:
                processed_data["estadisticas"] = {
                    "confianza_maxima": max(confianzas),
                    "confianza_promedio": sum(confianzas) / len(confianzas),
                    "total_predicciones": len(processed_data["predicciones"])
                }
        
        return processed_data
        
    except Exception as e:
        print(f"Error procesando datos Roboflow: {e}")
        return {"raw_data": datos_roboflow}