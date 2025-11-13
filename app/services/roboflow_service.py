import base64
import os
from inference_sdk import InferenceHTTPClient
from fastapi import HTTPException
import tempfile
from typing import Dict, Any, Optional
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
        # testing borrable
        self.last_raw_response = None

    # Modificar el método analyze_image en roboflow_service.py

    async def analyze_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analiza una imagen usando Roboflow - Versión mejorada que extrae imagen de respuesta
        """
        try:
            print(f"--- Analizando imagen: {image_path}")
            
            if not os.path.exists(image_path):
                raise HTTPException(status_code=400, detail="Archivo de imagen no encontrado")

            # Leer imagen original para posible almacenamiento
            with open(image_path, 'rb') as f:
                original_image_data = f.read()

            # workflow de Roboflow
            result = self.client.run_workflow(
                workspace_name="cnnpaiii",
                workflow_id="detect-and-classify-5",
                images={"image": image_path},
                use_cache=True
            )
            
            print(f" Respuesta Roboflow recibida 👻👻👻")
            # TESTING- BORRABLE
            self.last_raw_response = result[0] if result else None

            # Validar respuesta
            if not result or not isinstance(result, list) or len(result) == 0:
                print("e Respuesta vacía o estructura inválida")
                raise HTTPException(
                    status_code=400, 
                    detail="No se pudo analizar la imagen - respuesta vacía del servicio IA"
                )

            main_result = result[0]
            
            # secciones específicas 
            self._print_filtered_response(main_result)

            # clasificación
            classification_data = self._extract_classification_data(main_result)
            
            if not classification_data:
                print("e No se encontraron datos de clasificación")
                raise HTTPException(
                    status_code=400, 
                    detail="No se detectaron patrones de Alzheimer en la imagen"
                )
            
            confidence = classification_data.get("confidence")
            class_eng = classification_data.get("class")
            
            if not confidence or not class_eng:
                print(f"e Datos incompletos: confidence={confidence}, class={class_eng}")
                raise HTTPException(
                    status_code=400, 
                    detail="Datos de clasificación incompletos"
                )

            confidence_percent = float(confidence) * 100
            class_es = self.translations.get(class_eng, "Desconocido")

            print(f"c Resultado final: {class_es} - Confianza: {confidence_percent:.2f}%")

            # Extraer imagen procesada de Roboflow si existe
            processed_image_data = await self._extract_processed_image(main_result)

            return {
                "resultado": class_es,
                "confianza": f"{confidence_percent:.2f}%",
                "confianza_float": confidence_percent,
                "clase_original": class_eng,
                "original_image_data": original_image_data,  # Para almacenar después
                "processed_image_data": processed_image_data,  # Imagen procesada por Roboflow
                "datos_roboflow": main_result  # Datos completos para guardar en BD
            }

        except HTTPException:
            raise
        except Exception as e:
            print(f"e Error en analyze_image: {str(e)}")
            import traceback
            print(f"c Traceback completo: {traceback.format_exc()}")
            raise HTTPException(
                status_code=500, 
                detail=f"Error en servicio de IA: {str(e)}"
            )

    async def _extract_processed_image(self, roboflow_response: dict) -> Optional[bytes]:
        """
        Extraer imagen procesada de la respuesta de Roboflow
        """
        try:
            # Buscar imagen procesada en la respuesta (depende de la estructura de Roboflow)
            # Esto puede variar según la configuración del workflow
            if "image" in roboflow_response:
                image_data = roboflow_response["image"]
                if isinstance(image_data, str) and image_data.startswith("data:image"):
                    # Es base64, decodificar
                    base64_str = image_data.split(",")[1]
                    return base64.b64decode(base64_str)
            
            # Buscar recursivamente imágenes base64
            image_data = self._find_image_data_recursive(roboflow_response)
            if image_data:
                return image_data
                
            print("w No se encontró imagen procesada en la respuesta")
            return None
            
        except Exception as e:
            print(f"e Error extrayendo imagen procesada: {e}")
            return None

    def _find_image_data_recursive(self, obj, depth=0):
        """Buscar recursivamente datos de imagen en base64"""
        if depth > 5:
            return None
            
        if isinstance(obj, dict):
            for key, value in obj.items():
                if (isinstance(value, str) and 
                    value.startswith("data:image") and 
                    "base64" in value):
                    try:
                        base64_str = value.split(",")[1]
                        return base64.b64decode(base64_str)
                    except:
                        pass
                result = self._find_image_data_recursive(value, depth + 1)
                if result:
                    return result
                    
        elif isinstance(obj, list):
            for item in obj:
                result = self._find_image_data_recursive(item, depth + 1)
                if result:
                    return result
                    
        return None

    def _print_filtered_response(self, main_result: dict):
        """
        Imprime solo las secciones específicas del JSON que necesitas
        """
        print("=" * 60)
        print("RESPUESTA FILTRADA DE ROBOFLOW:")
        print("=" * 60)
        
        try:
            # Buscar la estructura de predictions
            if "predictions" in main_result:
                predictions_data = main_result["predictions"]
                
                # Imprimir información de la imagen
                if "image" in predictions_data:
                    image_info = predictions_data["image"]
                    print(" INFORMACIÓN DE LA IMAGEN:")
                    print(f"   • Ancho: {image_info.get('width')}")
                    print(f"   • Alto: {image_info.get('height')}")
                    print()
                
                # Imprimir información de predicciones
                if "predictions" in predictions_data and predictions_data["predictions"]:
                    predictions_list = predictions_data["predictions"]
                    print(" INFORMACIÓN DE PREDICCIÓN:")
                    
                    for i, prediction in enumerate(predictions_list):
                        print(f"   Predicción #{i+1}:")
                        print(f"   • Confianza: {prediction.get('confidence')}")
                        print(f"   • Class ID: {prediction.get('class_id')}")
                        print(f"   • Clase: {prediction.get('class')}")
                        print(f"   • Ancho: {prediction.get('width')}")
                        print(f"   • Alto: {prediction.get('height')}")
                        print()
                
            else:
                print("w No se encontró la estructura 'predictions' en la respuesta")
                
        except Exception as e:
            print(f"e Error al imprimir respuesta filtrada: {e}")
        
        print("=" * 60)

    def _extract_classification_data(self, main_result: dict) -> dict:
        """
        Extrae los datos de clasificación de la respuesta de Roboflow.
        CORREGIDO basado en la estructura real de la respuesta.
        """
        print("-.- Buscando datos de clasificación en la estructura...")
        
        try:
            if ("classification_predictions" in main_result and 
                main_result["classification_predictions"] and 
                len(main_result["classification_predictions"]) > 0):
                
                classification_pred = main_result["classification_predictions"][0]
                print(f"c Encontrado classification_predictions[0]")
                
                if ("predictions" in classification_pred and 
                    "predictions" in classification_pred["predictions"] and
                    classification_pred["predictions"]["predictions"] and
                    len(classification_pred["predictions"]["predictions"]) > 0):
                    
                    prediction_data = classification_pred["predictions"]["predictions"][0]
                    print(f"c Datos extraídos de classification_predictions: {prediction_data.get('class')} - {prediction_data.get('confidence')}")
                    return prediction_data
            
            if ("predictions" in main_result and 
                "predictions" in main_result["predictions"] and
                main_result["predictions"]["predictions"] and
                len(main_result["predictions"]["predictions"]) > 0):
                
                prediction_data = main_result["predictions"]["predictions"][0]
                if prediction_data.get("class") and prediction_data.get("confidence"):
                    print(f"c Datos extraídos de predictions: {prediction_data.get('class')} - {prediction_data.get('confidence')}")
                    return prediction_data
            
            print("🔎 Buscando recursivamente datos de clasificación...")
            classification_data = self._find_classification_data_recursive(main_result)
            if classification_data:
                return classification_data
                
            print("e No se encontraron datos de clasificación en ninguna estructura conocida")
            return None
            
        except Exception as e:
            print(f"e Error en _extract_classification_data: {str(e)}")
            import traceback
            print(f"c Traceback: {traceback.format_exc()}")
            return None

    def _find_classification_data_recursive(self, obj, depth=0):
        """
        Busca recursivamente datos de clasificación en la estructura
        """
        if depth > 5: 
            return None
            
        if isinstance(obj, dict):
            if obj.get("class") and obj.get("confidence"):
                print(f"c Encontrado en búsqueda recursiva: {obj.get('class')} - {obj.get('confidence')}")
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