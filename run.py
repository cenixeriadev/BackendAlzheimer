import asyncio
import os
import sys
import mimetypes
from app.services.storage_service import storage_service

async def test_storage_public_access(filepath: str):
    """
    Sube un archivo desde la ruta local especificada y prueba el acceso público.
    
    Args:
        filepath: La ruta local al archivo a subir.
    """
    # 1. Verificar si el archivo local existe
    if not os.path.exists(filepath):
        print(f"❌ Error: La ruta del archivo no existe: {filepath}")
        return

    # 2. Determinar el nombre del archivo y el tipo de contenido (MIME type)
    filename = os.path.basename(filepath)
    # Intenta adivinar el MIME type; usa un valor por defecto si no se encuentra
    content_type, _ = mimetypes.guess_type(filepath)
    if not content_type:
        content_type = "application/octet-stream" 

    print(f"📂 Archivo a subir: {filename}")
    print(f"📝 Tipo de contenido detectado: {content_type}")
    
    try:
        # 3. Leer el contenido del archivo en modo binario
        with open(filepath, 'rb') as f:
            file_content = f.read()

        print("⬆️ Subiendo archivo...")
        
        # 4. Llamar al servicio de subida con el contenido real
        test_result = await storage_service.upload_file(
            file_content=file_content, 
            filename=filename,
            content_type=content_type
        )
        
        url = test_result.get("url")
        
        if url:
            print("\n✅ Subida exitosa.")
            print("🔗 URL generada:", url)
            
            # Instrucciones para probar el acceso público
            print("\n📋 Copia esta URL y ábrela en tu navegador para verificar el acceso público:")
            print(url)
        else:
            print("\n❌ Error al obtener la URL. La subida pudo haber fallado o el servicio no devolvió una URL.")

        
    except Exception as e:
        print(f"\n❌ Ocurrió un error durante la subida: {e}")

    # 5. Recordatorio para la verificación manual
    print("\n🔍 Si el archivo no carga en el navegador, verifica:")
    print(f"1. Que MinIO/S3 esté corriendo ({'Local' if storage_service.is_local else 'Remoto'}).")
    print("2. Que el bucket de destino tenga una política de acceso 'público' (esencial para la prueba).")
    print("3. Que la URL sea accesible desde tu red (firewalls, proxys).")


# --- Ejecución de la prueba ---
if __name__ == "__main__":
    # Espera un argumento de línea de comandos (la ruta del archivo)
    if len(sys.argv) != 2:
        print("Uso: python test_storage_modified.py <ruta_del_archivo_local>")
        print("Ejemplo: python test_storage_modified.py ./assets/mi_logo.png")
        sys.exit(1)
        
    local_filepath = sys.argv[1]
    # Ejecutar la función asíncrona principal
    asyncio.run(test_storage_public_access(local_filepath))