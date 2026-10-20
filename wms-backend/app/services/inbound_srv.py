from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.inbound import PurchaseOrder, PurchaseOrderItem, Attachment
from app.models.product import Product
from app.schemas.erp_import import ERPImportResult
import os

class InboundService:
    
    @staticmethod
    async def create_purchase_order_from_import(
        db: AsyncSession, 
        import_result: ERPImportResult, 
        original_filename: str,
        saved_file_path: str,
        mime_type: str,
        user_id: int
    ) -> PurchaseOrder:
        """
        Crea la orden de compra, sus ítems y el registro del archivo adjunto
        de forma atómica (Todo o Nada).
        """
        # 1. Crear documento principal
        new_po = PurchaseOrder(
            erp_reference=import_result.erp_reference,
            status="PENDING"
        )
        db.add(new_po)
        await db.flush() # Obtiene new_po.id

        # 2. Mapear SKUs a IDs internos de productos para las llaves foráneas
        # (El parser ya garantizó que todos estos SKUs existen)
        skus = [item.sku for item in import_result.validated_data]
        query_products = select(Product.id, Product.sku).where(Product.sku.in_(skus))
        db_products = (await db.execute(query_products)).all()
        sku_to_id_map = {prod.sku: prod.id for prod in db_products}

        # 3. Crear los ítems de la orden (Cumpliendo Regla 9 y 35)
        for valid_item in import_result.validated_data:
            po_item = PurchaseOrderItem(
                purchase_order_id=new_po.id,
                product_id=sku_to_id_map[valid_item.sku],
                expected_qty=valid_item.quantity,
                received_qty=0,
                pending_qty=valid_item.quantity # Al inicio, lo pendiente es igual a lo esperado
            )
            db.add(po_item)

        # 4. Crear el registro del archivo adjunto (Regla 6)
        attachment = Attachment(
            reference_table="purchase_orders",
            reference_id=new_po.id,
            original_name=original_filename,
            file_name=os.path.basename(saved_file_path),
            mime_type=mime_type,
            file_size=os.path.getsize(saved_file_path),
            version=1,
            uploaded_by=user_id,
            storage_path=saved_file_path
        )
        db.add(attachment)

        # 5. Confirmar transacción
        await db.commit()
        await db.refresh(new_po)
        
        return new_po