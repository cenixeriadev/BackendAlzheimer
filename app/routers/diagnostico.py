import datetime
from math import ceil
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import uuid
import os
import io
from PIL import Image
from app.utils.database import get_db
from app.models.paciente import Paciente
from app.models.medico import Medico
from app.models.diagnostico import Diagnostico
from app.models.usuario import Usuario
from app.schemas.diagnostico import DiagnosticoResponse, AnalisisResponse
from app.services.roboflow_service import roboflow_service
from app.services.storage_service import storage_service
from app.utils.dependencies import get_current_active_user

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
    
    diagnosticos_data = []
    for diagnostico in diagnosticos:
        diagnostico_dict = {
            "id": diagnostico.id,
            "paciente_id": diagnostico.paciente_id,
            "resultado": diagnostico.resultado,
            "confianza": diagnostico.confianza,
            "clase_original": diagnostico.clase_original,
            "imagen_original_url": diagnostico.imagen_original_url,
            "imagen_procesada_url": diagnostico.imagen_procesada_url,
            "estado": diagnostico.estado,
            "created_at": diagnostico.created_at,
            # Debug info
            "debug_info": {
                "tiene_imagen_original": bool(diagnostico.imagen_original_url),
                "url_length": len(diagnostico.imagen_original_url) if diagnostico.imagen_original_url else 0,
                "url_preview": diagnostico.imagen_original_url[:100] + "..." if diagnostico.imagen_original_url and len(diagnostico.imagen_original_url) > 100 else diagnostico.imagen_original_url
            }
        }
        diagnosticos_data.append(diagnostico_dict)
    
    print(f"🔍 Debug Historial - URLs encontradas:")
    for d in diagnosticos_data:
        print(f"   ID {d['id']}: {d['imagen_original_url']}")
    
    return {
        "diagnosticos": diagnosticos_data,
        "total": len(diagnosticos_data),
        "debug": {
            "total_diagnosticos": len(diagnosticos_data),
            "urls_con_imagen": sum(1 for d in diagnosticos_data if d['imagen_original_url']),
            "ejemplo_url": diagnosticos_data[0]['imagen_original_url'] if diagnosticos_data else "No hay datos"
        }
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
    
    # Debug info
    debug_info = {
        "url_accesible": bool(diagnostico.imagen_original_url),
        "url_completa": diagnostico.imagen_original_url,
        "storage_service": "S3/MinIO"
    }
    
    print(f"🔍 Debug Detalle ID {diagnostico_id}:")
    print(f"   URL: {diagnostico.imagen_original_url}")
    print(f"   Tiene URL: {bool(diagnostico.imagen_original_url)}")
    
    return {
        "id": diagnostico.id,
        "fecha_analisis": diagnostico.created_at,
        "resultado": diagnostico.resultado,
        "confianza": diagnostico.confianza,
        "clase_original": diagnostico.clase_original,
        "imagen_original_url": diagnostico.imagen_original_url,
        "imagen_procesada_url": diagnostico.imagen_procesada_url,
        "estado": diagnostico.estado,
        "datos_detallados": datos_detallados,
        # Agregar debug info al response
        "_debug": debug_info
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

@router.get("/test-url/{diagnostico_id}")
async def test_url_imagen(
    diagnostico_id: int,
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Endpoint específico para testear si la URL de la imagen es accesible
    """
    diagnostico = db.query(Diagnostico).filter(
        Diagnostico.id == diagnostico_id,
        Diagnostico.paciente_id == current_user.id
    ).first()
    
    if not diagnostico:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")
    
    if not diagnostico.imagen_original_url:
        raise HTTPException(status_code=404, detail="No hay URL de imagen")
    
    import requests
    try:
        print(f" Testeando URL: {diagnostico.imagen_original_url}")
        response = requests.get(diagnostico.imagen_original_url, timeout=10)
        
        test_result = {
            "url": diagnostico.imagen_original_url,
            "status_code": response.status_code,
            "content_type": response.headers.get('content-type'),
            "content_length": len(response.content) if response.status_code == 200 else 0,
            "accessible": response.status_code == 200,
            "diagnostico_id": diagnostico_id
        }
        
        print(f" Test URL Result: {test_result}")
        
        return test_result
        
    except Exception as e:
        error_result = {
            "url": diagnostico.imagen_original_url,
            "error": str(e),
            "accessible": False,
            "diagnostico_id": diagnostico_id
        }
        print(f" Test URL Error: {error_result}")
        return error_result
    
async def _guardar_diagnostico_completo(
    db: Session,
    current_user: Usuario,
    analisis_result: Dict[str, Any],
    original_filename: str
) -> Diagnostico:
    try:
        original_upload = await storage_service.upload_file(
            file_content=analisis_result["original_image_data"],
            filename=f"original_{uuid.uuid4()}_{original_filename}",
            content_type="image/jpeg"
        )

        diagnostico = Diagnostico(
            paciente_id=current_user.id,
            resultado=analisis_result["resultado"],
            confianza=analisis_result["confianza_float"],
            clase_original=analisis_result["clase_original"],
            imagen_original_url=original_upload["url"],
            imagen_procesada_url=None,  
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
    

#  RUTAS PARA MEDICOS 

@router.get("/medico/historial-pacientes", response_model=Dict[str, Any])
async def obtener_historial_pacientes_asignados(
    paciente_id: int = Query(None, description="Filtrar por paciente específico"),
    fecha_desde: str = Query(None, description="Fecha desde (YYYY-MM-DD)"),
    fecha_hasta: str = Query(None, description="Fecha hasta (YYYY-MM-DD)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    current_user: Usuario = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Obtener historial de diagnósticos de pacientes asignados al médico
    """
    if current_user.tipo_usuario != "medico":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los médicos pueden acceder a esta información"
        )

    # Obtener el médico actual
    medico = db.query(Medico).filter(Medico.usuario_id == current_user.id).first()
    if not medico:
        raise HTTPException(status_code=404, detail="Perfil de médico no encontrado")

    # Obtener pacientes asignados
    from app.models.asignacion_medico import AsignacionMedicoPaciente
    asignaciones = db.query(AsignacionMedicoPaciente).filter(
        AsignacionMedicoPaciente.medico_id == medico.id
    ).all()

    if not asignaciones:
        return {
            "diagnosticos": [],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": 0,
                "total_pages": 0,
                "has_next": False,
                "has_prev": False
            }
        }

    pacientes_ids = [asignacion.paciente_id for asignacion in asignaciones]
    
    # Obtener usuarios_id de los pacientes
    pacientes_usuarios = db.query(Paciente).filter(Paciente.id.in_(pacientes_ids)).all()
    usuarios_ids = [paciente.usuario_id for paciente in pacientes_usuarios]

    # Construir query base
    query = db.query(Diagnostico).filter(Diagnostico.paciente_id.in_(usuarios_ids))
    
    # Aplicar filtros adicionales
    if paciente_id:
        paciente = db.query(Paciente).filter(Paciente.id == paciente_id).first()
        if paciente and paciente.usuario_id in usuarios_ids:
            query = query.filter(Diagnostico.paciente_id == paciente.usuario_id)
    
    if fecha_desde:
        try:
            fecha_desde_dt = datetime.strptime(fecha_desde, "%Y-%m-%d")
            query = query.filter(Diagnostico.created_at >= fecha_desde_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha_desde inválido")
    
    if fecha_hasta:
        try:
            fecha_hasta_dt = datetime.strptime(fecha_hasta, "%Y-%m-%d") + datetime.timedelta(days=1)
            query = query.filter(Diagnostico.created_at < fecha_hasta_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Formato de fecha_hasta inválido")

    # Calcular paginación
    total = query.count()
    total_pages = ceil(total / per_page) if total > 0 else 1
    offset = (page - 1) * per_page

    # Obtener diagnósticos
    diagnosticos = query.order_by(Diagnostico.created_at.desc()).offset(offset).limit(per_page).all()

    # Enriquecer con información
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
        "total_pacientes_asignados": len(pacientes_ids)
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