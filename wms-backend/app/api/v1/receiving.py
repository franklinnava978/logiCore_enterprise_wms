from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

# Dependencias (Asumimos que existen en api/dependencies.py)
# from app.api.dependencies import get_db, get_current_user

from app.services.erp_parser_srv import ERPParserService
from app.services.inbound_srv import InboundService
from app.utils.file_storage import save_upload_file_safely

router = APIRouter(prefix="/receiving", tags=["Receiving"])

@router.post("/purchase-orders/import", status_code=status.HTTP_201_CREATED)
async def import_purchase_order(
    erp_reference: str = Form(..., description="Número de Orden de Compra del ERP"),
    file: UploadFile = File(..., description="Archivo Excel, PDF, HTML o CSV"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user) # Inyección del usuario autenticado
):
    """
    Endpoint para importar una Orden de Compra desde el ERP mediante archivo adjunto.
    Ejecuta validación estricta antes de impactar la base de datos.
    """
    
    # 1. Guardar el archivo temporalmente de forma segura
    try:
        saved_file_path = save_upload_file_safely(file)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al guardar el archivo en el servidor: {str(e)}"
        )

    # 2. Ejecutar Parser Multipropósito y Validación
    import_result = await ERPParserService.validate_purchase_order_file(
        db=db,
        file_path=saved_file_path,
        mime_type=file.content_type,
        erp_reference=erp_reference
    )

    # 3. Evaluar resultado de validación
    if not import_result.is_valid:
        # Opcional: Eliminar el archivo físico si falló la validación para no generar basura
        import os
        if os.path.exists(saved_file_path):
            os.remove(saved_file_path)
            
        # Devolver error HTTP 400 con la lista detallada de errores (Regla 7.5 - 7.8)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "El archivo no superó las validaciones", "errors": import_result.errors}
        )

    # 4. Inserción Transaccional
    try:
        new_po = await InboundService.create_purchase_order_from_import(
            db=db,
            import_result=import_result,
            original_filename=file.filename,
            saved_file_path=saved_file_path,
            mime_type=file.content_type,
            user_id=current_user.id
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al registrar la orden: {str(e)}"
        )

    return {
        "message": "Orden de compra importada exitosamente",
        "purchase_order_id": new_po.id,
        "erp_reference": new_po.erp_reference,
        "total_items": import_result.total_items
    }