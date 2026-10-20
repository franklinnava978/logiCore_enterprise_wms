from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from decimal import Decimal

from app.models.inbound import PurchaseOrder, PurchaseOrderItem, Receipt, ReceiptItem
from app.models.inventory import Inventory, InventoryMovement
from app.schemas.receiving import ReceiptCreateInput # Pydantic schema supuesto

class ReceivingService:
    
    @staticmethod
    async def process_receipt(
        db: AsyncSession, 
        user_id: int, 
        warehouse_id: int, 
        receipt_data: ReceiptCreateInput
    ) -> Receipt:
        """
        Ejecuta la recepción física y actualiza el inventario/kardex en una sola transacción ACID.
        """
        
        # 1. Bloqueo Pesimista: Seleccionamos la Orden de Compra y sus items bloqueándolos
        # para que ningún otro usuario pueda modificar esta misma orden al mismo tiempo.
        query_po = (
            select(PurchaseOrder)
            .where(PurchaseOrder.id == receipt_data.purchase_order_id)
            .with_for_update() # SELECT ... FOR UPDATE (Control de Concurrencia)
        )
        result_po = await db.execute(query_po)
        purchase_order = result_po.scalar_one_or_none()

        if not purchase_order:
            raise ValueError("La Orden de Compra no existe.")

        # 2. Inicializar el documento de Recepción (Lo Ejecutado)
        new_receipt = Receipt(
            purchase_order_id=purchase_order.id,
            warehouse_id=warehouse_id,
            user_id=user_id,
            status="CONFIRMED",
            observations=receipt_data.observations
        )
        db.add(new_receipt)
        await db.flush() # Genera el new_receipt.id sin hacer commit todavía

        all_items_completed = True

        # 3. Procesar cada item recibido
        for item_input in receipt_data.items:
            # Obtener la línea de la orden de compra
            query_po_item = select(PurchaseOrderItem).where(
                PurchaseOrderItem.purchase_order_id == purchase_order.id,
                PurchaseOrderItem.product_id == item_input.product_id
            )
            po_item = (await db.execute(query_po_item)).scalar_one_or_none()
            
            if not po_item:
                raise ValueError(f"El producto {item_input.product_id} no pertenece a esta orden.")

            qty_to_receive = Decimal(str(item_input.received_qty))

            # Validación: Regla 10 (Sobre-recepción)
            # Aquí se puede inyectar lógica configurable. Por defecto, bloqueamos.
            if (po_item.received_qty + qty_to_receive) > po_item.expected_qty:
                raise ValueError(f"No se permite sobre-recepción para el producto {item_input.product_id}.")

            # 3.1 Registrar la Recepción Física
            receipt_item = ReceiptItem(
                receipt_id=new_receipt.id,
                product_id=item_input.product_id,
                location_id=item_input.location_id,
                received_qty=qty_to_receive,
                recorded_weight=item_input.recorded_weight
            )
            db.add(receipt_item)

            # 3.2 Actualizar la Orden de Compra (Regla 9 y 35)
            po_item.received_qty += qty_to_receive
            po_item.pending_qty = po_item.expected_qty - po_item.received_qty

            if po_item.pending_qty > 0:
                all_items_completed = False

            # 3.3 Afectar el Inventario Físico y Kardex de forma segura
            await ReceivingService._add_to_inventory(
                db=db,
                product_id=item_input.product_id,
                warehouse_id=warehouse_id,
                location_id=item_input.location_id,
                qty=qty_to_receive,
                user_id=user_id,
                receipt_id=new_receipt.id
            )

        # 4. Actualizar estado del documento (Regla 12)
        if all_items_completed:
            purchase_order.status = "COMPLETED"
        else:
            purchase_order.status = "PARTIAL"

        # 5. Confirmar transacción
        await db.commit()
        await db.refresh(new_receipt)
        return new_receipt

    @staticmethod
    async def _add_to_inventory(
        db: AsyncSession, 
        product_id: int, 
        warehouse_id: int, 
        location_id: int, 
        qty: Decimal, 
        user_id: int, 
        receipt_id: int
    ):
        """
        Lógica centralizada para incrementar inventario. 
        Mantiene el Kardex (InventoryMovement) en total sincronía (Regla 17).
        """
        # Intentar obtener el registro de inventario existente bloqueándolo
        query_inv = (
            select(Inventory)
            .where(
                Inventory.product_id == product_id,
                Inventory.location_id == location_id
            )
            .with_for_update()
        )
        inventory_record = (await db.execute(query_inv)).scalar_one_or_none()

        if inventory_record:
            # Si existe stock de este producto en esta ubicación, sumamos
            inventory_record.available_qty += qty
        else:
            # Si es la primera vez que se guarda este producto aquí, creamos la fila
            inventory_record