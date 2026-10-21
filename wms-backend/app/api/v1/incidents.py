from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import os

# Dependencias (Se asumen definidas en app/api/dependencies.py)
from app.api.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.incident import Incident
from app.models.inbound import Attachment  # Usamos la tabla polimórfica ya creada
from app.utils.file_storage import save_upload_file_safely

router = APIRouter(prefix="/incidents", tags=["Incidents"])

# Tipos de incidencias permitidas (Validación rápida a nivel de controlador)
VALID_INCIDENT_TYPES = ["MISSING", "EXCESS", "DAMAGED", "WRONG_PRODUCT", "NO_STOCK"]


@router.post("/", status_code=status.HTTP_201_CREATED)
async def report_incident(
    # Al incluir un 'File', todos los demás campos deben ser 'Form'
    source_table: str = Form(
        ..., description="Ej: 'receipts', 'dispatches', 'picking_tasks'"
    ),
    source_id: int = Form(..., description="ID del documento u operación de origen"),
    product_id: int = Form(..., description="ID del producto afectado"),
    qty: float = Form(..., gt=0, description="Cantidad afectada (debe ser mayor a 0)"),
    incident_type: str = Form(
        ..., description=f"Tipos permitidos: {VALID_INCIDENT_TYPES}"
    ),
    observation: str = Form(
        ..., description="Descripción detallada del problema reportado"
    ),
    # El archivo de evidencia es opcional (no todas las incidencias requieren foto)
    evidence_file: UploadFile | None = File(
        None, description="Foto de evidencia (JPG, PNG, etc.)"
    ),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),  # Usuario inyectado mediante token JWT
):
    """
    Reporta una nueva incidencia operativa desde un dispositivo móvil.
    Permite adjuntar una fotografía como evidencia en la misma transacción.
    """
    # 1. Validaciones de Negocio Rápidas
    incident_type = incident_type.upper()
    if incident_type not in VALID_INCIDENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de incidencia inválido. Valores permitidos: {VALID_INCIDENT_TYPES}",
        )

    # 2. Inicializar la Incidencia
    new_incident = Incident(
        source_table=source_table,
        source_id=source_id,
        product_id=product_id,
        qty=qty,
        incident_type=incident_type,
        observation=observation,
        reported_by_id=current_user.id,
        status="OPEN",
    )

    db.add(new_incident)

    try:
        # Flush para que PostgreSQL genere el new_incident.id sin hacer commit final
        await db.flush()

        # 3. Procesar y vincular la evidencia fotográfica (si existe)
        if evidence_file:
            # Validación simple de seguridad MIME
            if not evidence_file.content_type.startswith("image/"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El archivo adjunto debe ser una imagen.",
                )

            # Guardar en disco seguro
            saved_file_path = save_upload_file_safely(evidence_file)

            # Crear el registro documental apuntando a la incidencia
            attachment = Attachment(
                reference_table="incidents",
                reference_id=new_incident.id,  # Ahora tenemos el ID gracias al flush()
                original_name=evidence_file.filename,
                file_name=os.path.basename(saved_file_path),
                mime_type=evidence_file.content_type,
                file_size=os.path.getsize(saved_file_path),
                version=1,
                uploaded_by=current_user.id,
                storage_path=saved_file_path,
            )
            db.add(attachment)

        # 4. Consolidar Transacción (Todo o Nada)
        await db.commit()
        await db.refresh(new_incident)

    except Exception as e:
        # Si algo falla (BD, disco lleno, etc.), SQLAlchemy hace ROLLBACK automático
        await db.rollback()

        # Opcional: Intentar borrar el archivo físico si se llegó a crear pero la BD falló
        if (
            evidence_file
            and "saved_file_path" in locals()
            and os.path.exists(saved_file_path)
        ):
            os.remove(saved_file_path)

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar la incidencia: {str(e)}",
        )

    return {
        "message": "Incidencia reportada correctamente.",
        "incident_id": new_incident.id,
        "status": new_incident.status,
        "evidence_attached": bool(evidence_file),
    }
