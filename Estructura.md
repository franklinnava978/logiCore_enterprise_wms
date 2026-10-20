# lenguaje python

wms-backend/
├── app/
│   ├── main.py                  # Punto de entrada de la aplicación FastAPI
│   ├── core/                    # Configuraciones globales
│   │   ├── config.py            # Carga de variables de entorno (.env)
│   │   ├── database.py          # Configuración del motor PostgreSQL y sesiones
│   │   ├── security.py          # Hashes de contraseñas, encriptación y JWT
│   │   └── exceptions.py        # Manejadores de errores globales (para devolver HTTP 400/500)
│   │
│   ├── api/                     # Capa de Presentación (Endpoints REST)
│   │   ├── dependencies.py      # Inyección de dependencias (ej. get_db_session, get_current_user)
│   │   └── v1/                  # Rutas versionadas
│   │       ├── auth.py          # Autenticación y login
│   │       ├── warehouses.py    # Maestros de bodegas y ubicaciones
│   │       ├── receiving.py     # Endpoints de órdenes de compra y recepciones
│   │       ├── dispatch.py      # Endpoints de órdenes de despacho y picking
│   │       ├── inventory.py     # Consultas de stock, kardex y movimientos
│   │       └── integrations.py  # Endpoints exclusivos para subir Excel/CSV del ERP
│   │
│   ├── schemas/                 # Modelos Pydantic (Validación de entrada/salida y DTOs)
│   │   ├── user.py              # Esquemas de creación y respuesta de usuarios
│   │   ├── receiving.py         # Validaciones de cantidad esperada vs recibida
│   │   ├── inventory.py         # Esquemas para mostrar trazabilidad
│   │   └── erp_import.py        # Esquemas estrictos para las columnas del Excel
│   │
│   ├── models/                  # Modelos SQLAlchemy (Entidades de BD relacional)
│   │   ├── base.py              # Base declarativa de SQLAlchemy
│   │   ├── user.py              # Tabla users, roles, permissions
│   │   ├── facility.py          # Tablas warehouses, sectors, locations
│   │   ├── inbound.py           # Tablas purchase_orders, receipts, inbound_incidents
│   │   ├── outbound.py          # Tablas dispatch_orders, dispatches, picking_tasks
│   │   └── inventory.py         # Tablas inventory, inventory_movements, reservations
│   │
│   ├── services/                # Capa de Lógica de Negocio (El "corazón" del WMS)
│   │   ├── receiving_srv.py     # Lógica: control de parciales, sobre-recepción y estados
│   │   ├── dispatch_srv.py      # Lógica: reservas (hard allocation) y control de pendientes
│   │   ├── inventory_srv.py     # Lógica: centralización de movimientos, prohibición de UPDATE directo
│   │   └── erp_parser_srv.py    # ERP Integration Layer: Lee archivos, valida y transforma a schemas
│   │
│   └── utils/                   # Herramientas de infraestructura
│       ├── file_storage.py      # Guarda el archivo en disco (y a futuro en AWS S3)
│       └── barcode.py           # Utilidades para parsear y generar códigos de barras
│
├── storage/                     # Directorio local estructurado para archivos adjuntos (Ignorado en Git)
│   ├── erp_imports/             # Originales cargados del ERP
│   └── evidence/                # Fotografías de incidencias (daños)
│
├── tests/                       # Pruebas automatizadas (Pytest)
│   ├── api/                     # Pruebas de integración de endpoints
│   └── services/                # Pruebas unitarias de reglas de negocio (ej. despachos parciales)
│
├── alembic/                     # Sistema de migraciones de base de datos
│   ├── versions/                # Historial de cambios SQL
│   └── env.py
│
├── requirements.txt             # Dependencias (fastapi, sqlalchemy, psycopg2-binary, pandas, etc.)
├── .env                         # Variables de entorno (NO se sube a Git)
└── .gitignore                   # Excluye venv/, .env, storage/, __pycache__/