from sqlalchemy import String, ForeignKey, Numeric, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class Incident(Base, TimestampMixin):
    """
    Cumple la Regla 25: Sistema unificado de incidencias operativas.
    Permite registrar faltantes, excedentes, daños y errores desde cualquier proceso.
    """

    __tablename__ = "incidents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # 1. Enlace Polimórfico al Documento/Operación de Origen
    # source_table puede ser: 'receipts', 'dispatches', 'picking_tasks', 'inventory'
    source_table: Mapped[str] = mapped_column(String(50), index=True)
    source_id: Mapped[int] = mapped_column(Integer, index=True)

    # 2. Producto Afectado
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)

    # 3. Cantidad Afectada (Utilizamos Numeric para precisión)
    qty: Mapped[float] = mapped_column(Numeric(12, 3))

    # 4. Clasificación
    # Tipos: 'MISSING' (Faltante), 'EXCESS' (Excedente), 'DAMAGED' (Dañado), 'WRONG_PRODUCT' (Incorrecto), 'NO_STOCK' (Quiebre)
    incident_type: Mapped[str] = mapped_column(String(50), index=True)

    # Estados: 'OPEN' (Abierta), 'INVESTIGATING' (En revisión), 'RESOLVED' (Resuelta), 'CLOSED' (Cerrada)
    status: Mapped[str] = mapped_column(String(50), default="OPEN", index=True)

    # 5. Detalles y Trazabilidad
    observation: Mapped[str] = mapped_column(Text)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # 6. Usuarios Involucrados
    reported_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    resolved_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Relaciones
    product: Mapped["Product"] = relationship()
    reported_by: Mapped["User"] = relationship(foreign_keys=[reported_by_id])
    resolved_by: Mapped["User"] = relationship(foreign_keys=[resolved_by_id])
