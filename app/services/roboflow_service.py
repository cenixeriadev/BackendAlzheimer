import os
from inference_sdk import InferenceHTTPClient
from fastapi import HTTPException
import tempfile
from typing import Dict, Any
import json

class RoboflowService:
    def __init__(self):
        self.client = InferenceHTTPClient(
            api_url="https://serverless.roboflow.com",
            api_key="Jr33c2o6X30XosXLk1oE" 
        )
        
        self.translations = {
            "Very_Mild_Demented": "Demencia muy leve",
            "Mild_Demented": "Demencia leve", 
            "Non_Demented": "Sin demencia",
            "Moderate_Demented": "Demencia moderada"
        }

    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analiza una imagen usando Roboflow - Versión corregida
        """
        try:
            print(f"🔍 Analizando imagen: {image_path}")
            
            if not os.path.exists(image_path):
                raise HTTPException(status_code=400, detail="Archivo de imagen no encontrado")

            # workflow de Roboflow
            result = self.client.run_workflow(
                workspace_name="cnnpaiii",
                workflow_id="detect-and-classify-5",
                images={"image": image_path},
                use_cache=True
            )
            
            print(f"✅ Respuesta Roboflow recibida")
            
            # 🔴 RESPUESTA COMPLETA
            print("=" * 80)
            print("🔴 RESPUESTA COMPLETA DE ROBOFLOW:")
            print("=" * 80)
            print(json.dumps(result, indent=2, default=str))
            print("=" * 80)
            
            # Validar estructura de respuesta
            if not result or not isinstance(result, list) or len(result) == 0:
                print("❌ Respuesta vacía o estructura inválida")
                raise HTTPException(
                    status_code=400, 
                    detail="No se pudo analizar la imagen - respuesta vacía del servicio IA"
                )

            main_result = result[0]
            print(f"📋 Keys en resultado principal: {list(main_result.keys())}")

            # clasificación
            classification_data = self._extract_classification_data(main_result)
            
            if not classification_data:
                print("❌ No se encontraron datos de clasificación")
                raise HTTPException(
                    status_code=400, 
                    detail="No se detectaron patrones de Alzheimer en la imagen"
                )
            
            confidence = classification_data.get("confidence")
            class_eng = classification_data.get("class")
            
            if not confidence or not class_eng:
                print(f"❌ Datos incompletos: confidence={confidence}, class={class_eng}")
                raise HTTPException(
                    status_code=400, 
                    detail="Datos de clasificación incompletos"
                )

            confidence_percent = float(confidence) * 100
            class_es = self.translations.get(class_eng, "Desconocido")

            print(f"🎯 Resultado final: {class_es} - Confianza: {confidence_percent:.2f}%")

            return {
                "resultado": class_es,
                "confianza": f"{confidence_percent:.2f}%",
                "confianza_float": confidence_percent,
                "clase_original": class_eng,
                "output_image": main_result.get("output_image"),
                "dynamic_crop": main_result.get("dynamic_crop")
            }

        except HTTPException:
            raise
        except Exception as e:
            print(f"❌ Error en analyze_image: {str(e)}")
            import traceback
            print(f"🔴 Traceback completo: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error en servicio de IA: {str(e)}"
            )

    def _extract_classification_data(self, main_result: dict) -> dict:
        """
        Extrae los datos de clasificación de la respuesta de Roboflow.
        CORREGIDO basado en la estructura real de la respuesta.
        """
        print("🔍 Buscando datos de clasificación en la estructura...")
        
        try:
            # I Datos de classification_predictions
            if ("classification_predictions" in main_result and 
                main_result["classification_predictions"] and 
                len(main_result["classification_predictions"]) > 0):
                
                classification_pred = main_result["classification_predictions"][0]
                print(f"✅ Encontrado classification_predictions[0]")
                
                if ("predictions" in classification_pred and 
                    "predictions" in classification_pred["predictions"] and
                    classification_pred["predictions"]["predictions"] and
                    len(classification_pred["predictions"]["predictions"]) > 0):
                    
                    prediction_data = classification_pred["predictions"]["predictions"][0]
                    print(f"✅ Datos extraídos de classification_predictions: {prediction_data.get('class')} - {prediction_data.get('confidence')}")
                    return prediction_data
            
            # II Datos de predictions
            if ("predictions" in main_result and 
                "predictions" in main_result["predictions"] and
                main_result["predictions"]["predictions"] and
                len(main_result["predictions"]["predictions"]) > 0):
                
                prediction_data = main_result["predictions"]["predictions"][0]
                if prediction_data.get("class") and prediction_data.get("confidence"):
                    print(f"✅ Datos extraídos de predictions: {prediction_data.get('class')} - {prediction_data.get('confidence')}")
                    return prediction_data
            
            # III Buscar en cualquier parte del objeto principal
            print("🔍 Buscando recursivamente datos de clasificación...")
            classification_data = self._find_classification_data_recursive(main_result)
            if classification_data:
                return classification_data
                
            print("❌ No se encontraron datos de clasificación en ninguna estructura conocida")
            return None
            
        except Exception as e:
            print(f"❌ Error en _extract_classification_data: {str(e)}")
            import traceback
            print(f"🔴 Traceback: {traceback.format_exc()}")
            return None

    def _find_classification_data_recursive(self, obj, depth=0):
        """
        Busca recursivamente datos de clasificación en la estructura
        """
        if depth > 5: 
            return None
            
        if isinstance(obj, dict):
            if obj.get("class") and obj.get("confidence"):
                print(f"✅ Encontrado en búsqueda recursiva: {obj.get('class')} - {obj.get('confidence')}")
                return obj
            
            for key, value in obj.items():
                result = self._find_classification_data_recursive(value, depth + 1)
                if result:
                    return result
                    
        elif isinstance(obj, list):
            for item in obj:
                result = self._find_classification_data_recursive(item, depth + 1)
                if result:
                    return result
                    
        return None

roboflow_service = RoboflowService()