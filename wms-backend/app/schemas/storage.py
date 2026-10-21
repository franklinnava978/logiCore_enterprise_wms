from pydantic import BaseModel, Field

class PutawayExecuteInput(BaseModel):
    """
    Esquema optimizado para terminales de Radiofrecuencia (RF).
    El operario escanea el código de barras de la ubicación destino, no ingresa IDs manuales.
    """
    destination_barcode: str = Field(
        ..., 
        description="Código de barras escaneado de la ubicación destino (Ej: RACK-A-01)"
    )