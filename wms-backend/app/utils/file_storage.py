import os
import shutil
import uuid
from fastapi import UploadFile

# Directorio base definido en variables de entorno o constante
STORAGE_BASE_DIR = os.getenv("STORAGE_BASE_DIR", "./storage/erp_imports")

def save_upload_file_safely(upload_file: UploadFile) -> str:
    """
    Guarda el archivo en el sistema de archivos generando un nombre único (UUID)
    para evitar sobreescrituras y ataques de Path Traversal.
    Retorna la ruta absoluta o relativa del archivo guardado.
    """
    os.makedirs(STORAGE_BASE_DIR, exist_ok=True)
    
    # Extraer extensión original de forma segura
    _, ext = os.path.splitext(upload_file.filename)
    safe_filename = f"{uuid.uuid4().hex}{ext.lower()}"
    
    file_path = os.path.join(STORAGE_BASE_DIR, safe_filename)
    
    # Escribir el archivo en chunks para no saturar la RAM con archivos grandes
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
        
    return file_path