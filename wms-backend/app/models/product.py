# app/models/product.py
from sqlalchemy import String, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class UnitOfMeasure(Base, TimestampMixin):
    __tablename__ = "units_of_measure"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, index=True) # Ej: 'UN', 'KG', 'M', 'CJA'
    description: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    products: Mapped[list["Product"]] = relationship(back_populates="unit")

class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    description: Mapped[str] = mapped_column(String(255))
    unit_id: Mapped[int] = mapped_column(ForeignKey("units_of_measure.id"))
    
    # Atributos físicos (Necesarios para la Regla 13 - Diferencias de peso)
    weight: Mapped[float | None] = mapped_column(Numeric(10, 3), nullable=True) 
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    unit: Mapped["UnitOfMeasure"] = relationship(back_populates="products")
    barcodes: Mapped[list["ProductBarcode"]] = relationship(back_populates="product", cascade="all, delete-orphan")
    
    # Futuras relaciones (Se definirán en sus respectivos archivos para evitar importaciones circulares)
    # inventory: Mapped[list["Inventory"]] = relationship(back_populates="product")
    # purchase_order_items: Mapped[list["PurchaseOrderItem"]] = relationship(back_populates="product")

class ProductBarcode(Base, TimestampMixin):
    __tablename__ = "product_barcodes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"))
    
    barcode: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    barcode_type: Mapped[str] = mapped_column(String(20)) # Ej: 'EAN13', 'UPC', 'INTERNAL', 'QR'
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    product: Mapped["Product"] = relationship(back_populates="barcodes")