# lenguaje python

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


# lenguaje typeScripts

├── package.json              # Dependencias del proyecto (React, Vite, Tailwind CSS, Lucide, Recharts, Express)
├── server.ts                 # Servidor Backend (API REST en Express con TypeScript y simulación DB/Kardex transaccional)
├── vite.config.ts            # Configuración de Vite
├── index.html                # Punto de entrada HTML (Meta tags, PWA y fuentes)
├── tsconfig.json             # Configuración TypeScript
└── src/
    ├── main.tsx              # Punto de entrada React SPA
    ├── App.tsx               # Componente principal de navegación y enrutamiento de vistas
    ├── index.css             # Estilos globales y Tailwind CSS (@import "tailwindcss";)
    │
    ├── types/
    │   └── wms.ts            # Interfaces y tipos TypeScript (Warehouse, Receipt, Product, StockBalance, Movement, etc.)
    │
    ├── services/
    │   └── api.ts            # Cliente API REST para comunicación con el backend (server.ts)
    │
    ├── utils/
    │   ├── formatters.ts     # Formateo de fechas, cantidades decimales, RUT y monedas
    │   ├── ceramicCalculations.ts # Motor de cálculo de cerámica (m² <-> Cajas mediante factor de conversión)
    │   ├── barcodeGenerator.ts # Generador de códigos de barras / EAN / QR
    │   ├── labelPrinters.ts  # Configuración e impresión de etiquetas de bultos/pallets (LPN)
    │   └── printHelper.ts    # Utilidades de impresión de reportes y actas de andén
    │
    └── components/
        ├── layout/
        │   ├── Sidebar.tsx   # Menú lateral operativo (con sección de carpeta de recepción y búsqueda)
        │   └── Header.tsx    # Barra superior (Selector de bodegas, perfil de usuario, quick scan)
        │
        ├── dashboard/
        │   └── DashboardView.tsx # Torre de Control con sistema de widgets personalizables (drag-and-drop y toggling)
        │
        ├── receiving/
        │   ├── ReceivingView.tsx       # Módulo de Recepción (Carpeta de búsqueda, terminal de andén y validación)
        │   ├── AttachPurchaseOrderModal.tsx # Adjuntar / OCR de Orden de Compra (PDF / Factura)
        │   ├── ReceiptReportModal.tsx  # Acta de recepción oficial
        │   └── LpnLabelsModal.tsx      # Generación de etiquetas LPN por pallet
        │
        ├── acopio/
        │   └── AcopioPutawayView.tsx   # Gestión de zona de acopio y ejecución de tareas de Putaway
        │
        ├── picking/
        │   └── PickingView.tsx         # Picking Operativo RF y armado de olas
        │
        ├── shipping/
        │   └── ShippingPackingView.tsx # Consolidación de bultos, packing y despacho vehicular
        │
        ├── inventory/
        │   ├── InventoryView.tsx       # Stock actual por ubicación y bodega
        │   └── KardexView.tsx          # Libro mayor transaccional inmutable (Kardex)
        │
        ├── warehouses/
        │   └── WarehouseHierarchyView.tsx # Jerarquía multi-bodega y pasillos/racks
        │
        ├── transfers/
        │   └── TransfersView.tsx       # Transferencias internas entre ubicaciones/bodegas
        │
        ├── barcode/
        │   └── BarcodeStudioView.tsx   # Estudio y pruebas de lectura de códigos de barras
        │
        ├── audit/
        │   └── AuditLogView.tsx        # Auditoría y trazabilidad de acciones de usuarios
        │
        ├── reports/
        │   └── ReportsView.tsx         # Reportes avanzados y exportación de datos
        │
        ├── users/
        │   └── UsersRolesView.tsx      # Gestión de usuarios y control de acceso (RBAC)
        │
        └── config/
            └── SystemConfigView.tsx    # Configuración de sistema, balanzas e impresoras termicas