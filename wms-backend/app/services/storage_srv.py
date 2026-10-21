from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from decimal import Decimal
from fastapi import HTTPException, status

from app.models.storage import InternalMovement
from app.models.inventory import Inventory, InventoryMovement


class StorageService:

    @staticmethod
    async def execute_putaway_task(
        db: AsyncSession, task_id: int, actual_destination_id: int, user_id: int
    ) -> InternalMovement:
        """
        Ejecuta físicamente el movimiento de Acopio a Piso.
        Transacción ACID: Resta origen, suma destino, guarda Kardex y cierra tarea.
        """
        # 1. Bloquear la Tarea para evitar ejecución doble (Concurrencia)
        query_task = (
            select(InternalMovement)
            .where(InternalMovement.id == task_id)
            .with_for_update()
        )
        task = (await db.execute(query_task)).scalar_one_or_none()

        if not task or task.status != "PENDING":
            raise HTTPException(
                status_code=400, detail="La tarea no existe o ya fue procesada."
            )

        # 2. Bloquear Inventario Origen (Acopio)
        query_source = (
            select(Inventory)
            .where(
                Inventory.product_id == task.product_id,
                Inventory.location_id == task.source_location_id,
            )
            .with_for_update()
        )
        source_inv = (await db.execute(query_source)).scalar_one_or_none()

        # Validación estricta: ¿Alguien más movió el stock mientras yo caminaba?
        qty_decimal = Decimal(str(task.qty))
        if not source_inv or source_inv.available_qty < qty_decimal:
            raise HTTPException(
                status_code=400,
                detail="Inventario insuficiente en la ubicación de origen.",
            )

        # 3. Bloquear / Obtener Inventario Destino (Rack)
        query_dest = (
            select(Inventory)
            .where(
                Inventory.product_id == task.product_id,
                Inventory.location_id == actual_destination_id,
            )
            .with_for_update()
        )
        dest_inv = (await db.execute(query_dest)).scalar_one_or_none()

        # 4. Modificar Balances (Inmutabilidad protegida por servicio)
        source_inv.available_qty -= qty_decimal

        # Si la fila origen queda en 0 y sin reservas, en un escenario real se podría eliminar
        # para no inflar la tabla, pero mantenerla en 0 es válido para historial de ocupación.

        if dest_inv:
            dest_inv.available_qty += qty_decimal
        else:
            dest_inv = Inventory(
                product_id=task.product_id,
                warehouse_id=source_inv.warehouse_id,  # Asumimos misma bodega
                location_id=actual_destination_id,
                available_qty=qty_decimal,
                reserved_qty=0,
            )
            db.add(dest_inv)

        # 5. Generar Trazabilidad (Kardex - Regla 16/17)
        movement_log = InventoryMovement(
            product_id=task.product_id,
            warehouse_id=source_inv.warehouse_id,
            user_id=user_id,
            source_location_id=task.source_location_id,
            destination_location_id=actual_destination_id,
            movement_type="TRANSFER",
            qty=qty_decimal,
            reference_table="internal_movements",
            reference_id=task.id,
            notes="Putaway (Acopio a Piso)",
        )
        db.add(movement_log)

        # 6. Actualizar Estado de la Tarea
        task.status = "COMPLETED"
        task.actual_destination_id = actual_destination_id
        task.executed_by_id = user_id

        # 7. Confirmar Transacción
        await db.commit()
        await db.refresh(task)

        return task
