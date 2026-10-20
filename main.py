from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Literal

app = FastAPI(title="LogiCore WMS Enterprise API", version="1.0.0")

# Configuración de CORS para permitir la comunicación con el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 1. MODELOS DE DATOS (Pydantic) ---

class Warehouse(BaseModel):
    id: str
    code: str
    name: str
    address: str
    total_locations: int = 0

class Product(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    unit: Literal["UND", "M2", "CAJA", "KG"]
    conversion_factor: Optional[float] = None
    cost: float
    weight_kg: float
    volume_m3: float
    min_stock: float

class Supplier(BaseModel):
    id: str
    rut: str
    name: str
    contact_person: str
    email: str
    phone: str

# --- 2. BASE DE DATOS EN MEMORIA (Mock Data Inicial) ---

fake_db = {
    "warehouses": [
        {"id": "wh-1", "code": "BOD-L03", "name": "Bodega Vespucio", "address": "Av. Américo Vespucio 4288, Santiago", "total_locations": 45}
    ],
    "sectors": [
        {"id": "sec-1", "warehouse_id": "wh-1", "code": "SEC-A", "name": "Sector Almacenaje Pesado"}
    ],
    "zones": [
        {"id": "zone-1", "warehouse_id": "wh-1", "code": "Z-ANDEN", "name": "Andén de Recepción", "type": "RECEPCION"}
    ],
    "locations": [
        {"id": "loc-1", "warehouse_id": "wh-1", "zone_id": "zone-1", "code": "BOD-CEN-P01-R01-N1-01", "aisle": "P01", "rack": "R01", "level": "N1", "bin": "01", "barcode": "LOC-BOD-CEN-P01-R01-N1-01", "status": "LIBRE", "type": "PALLET", "max_weight_kg": 1500, "max_volume_m3": 3.5, "current_weight_kg": 0}
    ],
    "products": [
        {"id": "prod-1", "sku": "CER-GRIS-01", "name": "Cerámica Etapa Gris 45x45", "category": "Cerámicas", "unit": "CAJA", "conversion_factor": 1.84, "cost": 8500, "weight_kg": 24.5, "volume_m3": 0.04, "min_stock": 50}
    ],
    "suppliers": [
        {"id": "sup-1", "rut": "76.543.210-9", "name": "Distribuidora Limatco S.A.", "contact_person": "Juan Pérez", "email": "contacto@limatco.cl", "phone": "+56912345678"}
    ]
}

# --- 3. ENDPOINTS API REST ---

@app.get("/api/v1/health")
def health_check():
    return {"success": True, "status": "WMS Python Backend Running Smoothly"}

@app.get("/api/v1/warehouses")
def get_warehouses():
    return {"success": True, "data": fake_db["warehouses"]}

@app.get("/api/v1/hierarchy")
def get_hierarchy(warehouseId: Optional[str] = None):
    wh = next((w for w in fake_db["warehouses"] if w["id"] == warehouseId), fake_db["warehouses"][0])
    sectors = [s for s in fake_db["sectors"] if s["warehouse_id"] == wh["id"]]
    zones = [z for z in fake_db["zones"] if z["warehouse_id"] == wh["id"]]
    locations = [l for l in fake_db["locations"] if l["warehouse_id"] == wh["id"]]
    return {
        "success": True,
        "data": {
            "warehouse": wh,
            "sectors": sectors,
            "zones": zones,
            "locations": locations
        }
    }

@app.get("/api/v1/products")
def get_products(
    search: Optional[str] = Query(None, description="Filtrar por SKU o nombre"),
    category: Optional[str] = Query(None, description="Filtrar por categoría")
):
    list_p = fake_db["products"]
    if search:
        q = search.lower()
        list_p = [p for p in list_p if q in p["sku"].lower() or q in p["name"].lower()]
    if category:
        list_p = [p for p in list_p if p["category"] == category]
    return {"success": True, "data": list_p}

@app.post("/api/v1/products")
def create_product(product: Product):
    if any(p["sku"] == product.sku for p in fake_db["products"]):
        raise HTTPException(status_code=400, detail="El SKU ya se encuentra registrado.")
    fake_db["products"].append(product.dict())
    return {"success": True, "data": product}

@app.get("/api/v1/suppliers")
def get_suppliers():
    return {"success": True, "data": fake_db["suppliers"]}