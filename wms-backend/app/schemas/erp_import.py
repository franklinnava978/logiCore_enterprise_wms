from pydantic import BaseModel, Field, field_validator
from typing import List

class PORowSchema(BaseModel):
    """Esquema estricto para validar cada fila del Excel."""
    sku: str = Field(..., min_length=1, description="Código único del producto")
    quantity: float = Field(..., gt=0, description="Cantidad esperada mayor a 0")

    @field_validator('quantity')
    @classmethod
    def round_quantity(cls, v):
        # Aseguramos máxima precisión de 3 decimales para evitar problemas de coma flotante
        return round(v, 3)

class ERPImportResult(BaseModel):
    """Estructura de respuesta del servicio de validación."""
    is_valid: bool
    erp_reference: str
    total_items: int = 0
    validated_data: List[PORowSchema] = []
    errors: List[str] = []