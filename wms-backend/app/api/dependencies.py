from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal
from app.models.user import User

async def get_db() -> AsyncSession:
    """Generador de sesiones asíncronas para FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_current_user() -> User:
    """Mock temporal para poder avanzar. Luego se reemplazará por validación JWT."""
    # Retorna un usuario ficticio con ID 1 para que las tablas registren quién hizo la acción
    mock_user = User(id=1, email="admin@limatco.cl", is_active=True, role_id=1)
    return mock_user