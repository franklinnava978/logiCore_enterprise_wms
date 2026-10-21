from sqlalchemy import String, ForeignKey, Numeric, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, TimestampMixin


class InternalMovement(Base, TimestampMixin):
    """
    Controla las tareas de Putaway (Acopio -> Rack), Reabastecimiento o Transferencias manuales.
    Separa la "orden de mover" de la ejecución real en el inventario.
    """

    __tablename__ = "internal_movements"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)

    # Origen (Ej: Zona de Acopio / Playa de Recepción)
    source_location_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"), index=True
    )

    # Destino planificado (Ej: Pasillo 3, Rack A, Nivel 2)
    planned_destination_id: Mapped[int] = mapped_column(
        ForeignKey("locations.id"), index=True
    )

    # Destino real (Puede diferir si el operario encontró el rack lleno y lo dejó en otro lado)
    actual_destination_id: Mapped[int | None] = mapped_column(
        ForeignKey("locations.id"), nullable=True
    )

    qty: Mapped[float] = mapped_column(Numeric(12, 3))

    # Estados: PENDING, IN_PROGRESS, COMPLETED, CANCELED
    status: Mapped[str] = mapped_column(String(50), default="PENDING", index=True)

    # Tipos: PUTAWAY, REPLENISHMENT, MANUAL_TRANSFER
    movement_type: Mapped[str] = mapped_column(String(50), default="PUTAWAY")

    # Trazabilidad Operativa
    assigned_to_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    executed_by_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )

    # Origen documental (Ej: Para saber de qué recepción nació este Putaway)
    reference_table: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relaciones
    product: Mapped["Product"] = relationship()
    source_location: Mapped["Location"] = relationship(
        foreign_keys=[source_location_id]
    )
    planned_destination: Mapped["Location"] = relationship(
        foreign_keys=[planned_destination_id]
    )
    actual_destination: Mapped["Location"] = relationship(
        foreign_keys=[actual_destination_id]
    )
    assigned_user: Mapped["User"] = relationship(foreign_keys=[assigned_to_id])
    executed_user: Mapped["User"] = relationship(foreign_keys=[executed_by_id])
