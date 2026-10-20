from sqlalchemy import String, Boolean, ForeignKey, Numeric, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Attachment(Base, TimestampMixin):
    """
    Cumple la Regla 6: Archivos Adjuntos y Regla 43: Gestión de Archivos.
    Mantiene el historial de documentos provenientes del ERP o evidencias físicas.
    """
    __tablename__ = "attachments"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    
    # Diseño polimórfico simple para adjuntar archivos a cualquier entidad (Órdenes, Incidencias, etc.)
    reference_table: Mapped[str] = mapped_column(String(50), index=True) # Ej: 'purchase_orders', 'incidents'
    reference_id: Mapped[int] = mapped_column(Integer, index=True)
    
    original_name: Mapped[str] = mapped_column(String(255))
    file_name: Mapped[str] = mapped_column(String(255), unique=True) # Nombre interno seguro (Ej: UUID)
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer) # En bytes
    version: Mapped[int] = mapped_column(Integer, default=1)
    
    uploaded_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # El archivo NO se guarda en base de datos, solo su ruta de acceso
    storage_path: Mapped[str] = mapped_column(String(500))

# ==========================================
# LO SOLICITADO (Documento ERP)
# ==========================================

class PurchaseOrder(Base, TimestampMixin):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    erp_reference: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    
    # Estados: PENDING, IN_PROGRESS, PARTIAL, COMPLETED, CLOSED_EXCEPTIONALLY
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True)
    
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    items: Mapped[list["PurchaseOrderItem"]] = relationship(back_populates="purchase_order", cascade="all, delete-orphan")
    receipts: Mapped[list["Receipt"]] = relationship(back_populates="purchase_order")

class PurchaseOrderItem(Base, TimestampMixin):
    """
    Cumple la Regla 9 y 35: Mantiene estrictamente separados los valores
    esperados, recibidos y pendientes.
    """
    __tablename__ = "purchase_order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))

    # Regla de Negocio: Nunca sobrescribir 'expected_qty'
    expected_qty: Mapped[float] = mapped_column(Numeric(12, 3))
    received_qty: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    pending_qty: Mapped[float] = mapped_column(Numeric(12, 3))

    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()

# ==========================================
# LO EJECUTADO FÍSICAMENTE (Operación WMS)
# ==========================================

class Receipt(Base, TimestampMixin):
    __tablename__ = "receipts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    purchase_order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"))
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # Estados: DRAFT, CONFIRMED, CANCELED
    status: Mapped[str] = mapped_column(String(50), default="DRAFT")
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)

    purchase_order: Mapped["PurchaseOrder"] = relationship(back_populates="receipts")
    items: Mapped[list["ReceiptItem"]] = relationship(back_populates="receipt", cascade="all, delete-orphan")

class ReceiptItem(Base, TimestampMixin):
    """
    Registra lo que el operador realmente contó en el piso de la bodega
    y en qué ubicación temporal (dock de recepción) lo dejó.
    """
    __tablename__ = "receipt_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("receipts.id", ondelete="CASCADE"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    
    # Ubicación física donde se descargó (Ej: Playa de Recepción 1)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"))

    # Lo realmente contado en este evento físico específico
    received_qty: Mapped[float] = mapped_column(Numeric(12, 3))
    
    # Si corresponde (Regla 13)
    recorded_weight: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True)

    receipt: Mapped["Receipt"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship()