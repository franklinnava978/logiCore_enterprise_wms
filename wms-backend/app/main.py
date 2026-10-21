# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Importar los routers que hemos construido (y los futuros)
from app.api.v1 import receiving
from app.api.v1 import storage
from app.api.v1 import incidents
# from app.api.v1 import dispatch, inventory, auth... (se agregarán a medida que se construyan)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Maneja el ciclo de vida de la aplicación.
    Aquí se pueden inicializar conexiones a caché (Redis), 
    verificar que las carpetas de almacenamiento existan, etc.
    """
    import os
    # Asegurar que el directorio de archivos adjuntos del ERP exista al arrancar
    os.makedirs(os.getenv("STORAGE_BASE_DIR", "./storage/erp_imports"), exist_ok=True)
    
    # Startup
    yield
    
    # Shutdown (Limpieza de recursos si es necesario)
    pass

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="WMS Enterprise API",
    description="API para la gestión física de bodegas (Recepción, Almacenamiento, Despacho)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",       # Swagger UI
    redoc_url="/redoc"      # ReDoc
)

# ---------------------------------------------------------
# CONFIGURACIÓN DE SEGURIDAD (Regla 42: CORS)
# ---------------------------------------------------------
# En producción, reemplazar "*" por los dominios exactos del frontend React.
ALLOWED_ORIGINS = [
    "http://localhost:3000",      # React local
    "http://localhost:5173",      # Vite/React local
    # "https://wms.miempresa.com" # Producción
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"], # GET, POST, PUT, DELETE, PATCH, OPTIONS
    allow_headers=["*"], # Authorization, Content-Type, etc.
)

# ---------------------------------------------------------
# REGISTRO DE RUTAS (Endpoints)
# ---------------------------------------------------------
# Todos los endpoints estarán bajo el prefijo /api/v1/
API_PREFIX = "/api/v1"

app.include_router(receiving.router, prefix=API_PREFIX)
app.include_router(storage.router, prefix=API_PREFIX)
app.include_router(incidents.router, prefix=API_PREFIX)

# ---------------------------------------------------------
# ENDPOINT DE HEALTH CHECK
# ---------------------------------------------------------
@app.get("/health", tags=["System"])
async def health_check():
    """Endpoint para verificar que el servidor está vivo y respondiendo."""
    return {"status": "ok", "service": "wms-backend"}