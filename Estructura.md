/app/applet/
├── backend/
│   ├── main.py               # Aplicación principal FastAPI (CORS, Middlewares, Routers)
│   ├── database.py           # Conexión a Base de Datos / Modelos de Datos en memoria o PostgreSQL
│   ├── models.py             # Esquemas Pydantic (Validación estricta para O.C., Recepciones, Kardex)
│   ├── routers/
│   │   ├── warehouses.py     # Endpoints de Bodegas, Zonas y Ubicaciones
│   │   ├── products.py       # Catálogo de Productos y Proveedores
│   │   ├── receipts.py       # Recepciones, OCR de O.C. (Gemini SDK) y validación de andén
│   │   └── inventory.py      # Kardex transaccional y balance de stock
│   └── requirements.txt      # Dependencias Python (fastapi, uvicorn, pydantic, google-genai, etc.)
│
├── src/                      # Frontend actual en React + TypeScript + Tailwind
│   └── services/
│       └── api.ts            # Cliente HTTP apuntando a /api/v1/* en el backend FastAPI