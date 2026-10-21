from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# Dependencias (Asumidas)
# from app.api.dependencies import get_db, get_current_user

from app.schemas.storage import PutawayExecuteInput
from app.services.storage_srv import StorageService
from app.models.facility import Location

router = APIRouter(prefix="/storage", tags=["Storage & Putaway"])

@router.post("/tasks/{task_id}/execute", status_code=status.HTTP_200_OK)
async def execute_putaway(
    task_id: int,
    payload: PutawayExecuteInput,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Endpoint diseñado para pistolas RF. 
    Recibe el ID de la tarea y el código de barras de la ubicación donde el operador dejó la carga.
    """
    
    # 1. Traducir el código de barras escaneado al ID de la ubicación
    query_location = select(Location).where(
        Location.barcode == payload.destination_barcode,
        Location.is_active == True
    )
    destination_location = (await db.execute(query_location)).scalar_one_or_none()

    if not destination_location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ubicación con código '{payload.destination_barcode}' no encontrada o inactiva."
        )

    # 2. Ejecutar la transacción de negocio
    try:
        completed_task = await StorageService.execute_putaway_task(
            db=db,
            task_id=task_id,
            actual_destination_id=destination_location.id,
            user_id=current_user.id
        )
    except HTTPException as http_exc:
        # Re-lanzar excepciones HTTP generadas por el servicio (Ej: Inventario insuficiente)
        raise http_exc
    except Exception as e:
        # Capturar cualquier otro error (BD, conexión)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al procesar el almacenamiento: {str(e)}"
        )

    return {
        "message": "Almacenamiento (Putaway) completado con éxito.",
        "task_id": completed_task.id,
        "product_id": completed_task.product_id,
        "qty_stored": completed_task.qty,
        "destination_barcode": payload.destination_barcode
    }