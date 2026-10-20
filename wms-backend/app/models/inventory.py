from sqlalchemy import String, ForeignKey, Numeric, Integer, UniqueConstraint, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Inventory(Base, TimestampMixin):
    """
    Cumple la Regla 15: Representa la existencia física conocida por el WMS.
    La granularidad es estricta: Producto + Bodega + Ubicación.
    """
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("locations.id"), index=True)

    # Cantidad física real disponible para ser tomada o reservada
    available_qty: Mapped[float] = mapped_column(Numeric(12, 3), default=0)
    
    # Cantidad bloqueada (Hard Allocation) por una orden de despacho en curso (Regla 22)
    reserved_qty: Mapped[float] = mapped_column(Numeric(12, 3), default=0)

    product: Mapped["Product"] = relationship()
    warehouse: Mapped["Warehouse"] = relationship()
    location: Mapped["Location"] = relationship()

    # Garantiza que no existan dos registros separados del mismo producto en la misma ubicación.
    # Si ingresa más producto a esta ubicación, se actualiza la fila existente.
    __table_args__ = (
        UniqueConstraint('product_id', 'location_id', name='uix_product_location'),
    )


class InventoryMovement(Base, TimestampMixin):
    """
    Cumple las Reglas 16 y 17: Trazabilidad Absoluta (Kardex).
    ESTA TABLA ES DE SOLO INSERCIÓN (Append-Only). No se permiten UPDATEs ni DELETEs.
    """
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True) # Trazabilidad de quién lo hizo

    # Origen y Destino (Permiten NULL dependiendo del tipo de movimiento)
    # IN (Recepción): source NULL, destination = Ubicación
    # OUT (Despacho): source = Ubicación, destination NULL
    # TRANSFER (Movimiento Interno): source = Ubicación A, destination = Ubicación B
    source_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)
    destination_location_id: Mapped[int | None] = mapped_column(ForeignKey("locations.id"), nullable=True)

    # Tipos: IN, OUT, TRANSFER, ADJUSTMENT
    movement_type: Mapped[str] = mapped_column(String(20), index=True)
    qty: Mapped[float] = mapped_column(Numeric(12, 3))

    # Trazabilidad documental: ¿Qué operación generó este movimiento?
    reference_table: Mapped[str] = mapped_column(String(50), index=True) # Ej: 'receipts', 'dispatches', 'adjustments'
    reference_id: Mapped[int] = mapped_column(Integer, index=True)
    
    notes