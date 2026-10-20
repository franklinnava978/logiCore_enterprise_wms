from sqlalchemy import String, Boolean, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin

class Warehouse(Base, TimestampMixin):
    __tablename__ = "warehouses"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    locations: Mapped[list["Location"]] = relationship(back_populates="warehouse")
    users: Mapped[list["UserWarehouse"]] = relationship(back_populates="warehouse")

class Location(Base, TimestampMixin):
    __tablename__ = "locations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    warehouse_id: Mapped[int] = mapped_column(ForeignKey("warehouses.id", ondelete="CASCADE"))
    
    barcode: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    type: Mapped[str] = mapped_column(String(50)) # e.g., STORAGE, RECEIVING_DOCK, DISPATCH_DOCK
    
    # Jerarquía física
    sector: Mapped[str] = mapped_column(String(50), nullable=True)
    zone: Mapped[str] = mapped_column(String(50), nullable=True)
    aisle: Mapped[str] = mapped_column(String(50), nullable=True) # Pasillo
    rack: Mapped[str] = mapped_column(String(50), nullable=True)
    level: Mapped[str] = mapped_column(String(50), nullable=True)
    position: Mapped[str] = mapped_column(String(50), nullable=True)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    warehouse: Mapped["Warehouse"] = relationship(back_populates="locations")