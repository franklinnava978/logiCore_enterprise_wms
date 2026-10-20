import pandas as pd
import pdfplumber
import os
from bs4 import BeautifulSoup
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.schemas.erp_import import PORowSchema, ERPImportResult
from app.models.inbound import PurchaseOrder
from app.models.product import Product

class ERPParserService:
    
    ALLOWED_SKU_COLUMNS = ['sku', 'codigo', 'codigo_producto', 'item']
    ALLOWED_QTY_COLUMNS = ['cantidad', 'qty', 'quantity', 'cant']

    @staticmethod
    def _extract_dataframe_from_excel(file_path: str) -> pd.DataFrame:
        """Extrae datos de Excel usando openpyxl."""
        return pd.read_excel(file_path, engine='openpyxl')

    @staticmethod
    def _extract_dataframe_from_html(file_path: str) -> pd.DataFrame:
        """
        Extrae datos de HTML o MHTML.
        Busca las etiquetas <table> dentro del documento.
        """
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Limpieza inicial con BeautifulSoup por si el HTML está mal formado
        soup = BeautifulSoup(content, 'lxml')
        tables = soup.find_all('table')
        
        if not tables:
            raise ValueError("No se encontraron tablas en el documento HTML/MHTML.")
            
        # Pandas read_html devuelve una lista de DataFrames (uno por tabla)
        # Asumimos que la tabla más grande o la primera contiene el detalle de la orden
        dfs = pd.read_html(str(tables[0]))
        return dfs[0]

    @staticmethod
    def _extract_dataframe_from_pdf(file_path: str) -> pd.DataFrame:
        """
        Extrae tablas de un PDF usando pdfplumber.
        Requiere que el PDF sea nativo (texto seleccionable), no una imagen escaneada.
        """
        all_rows = []
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                # extract_table() detecta las líneas de la cuadrícula
                table = page.extract_table()
                if table:
                    all_rows.extend(table)
                    
        if not all_rows:
            raise ValueError("No se detectaron tablas estructuradas en el PDF.")
            
        # La primera fila suele ser la cabecera
        headers = all_rows[0]
        data = all_rows[1:]
        return pd.DataFrame(data, columns=headers)

    @staticmethod
    def _get_raw_dataframe(file_path: str, mime_type: str) -> pd.DataFrame:
        """Patrón Strategy para enrutar el archivo al motor de extracción correcto."""
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.xlsx', '.xls'] or 'spreadsheetml' in mime_type:
            return ERPParserService._extract_dataframe_from_excel(file_path)
        elif ext in ['.html', '.htm', '.mhtml'] or 'html' in mime_type:
            return ERPParserService._extract_dataframe_from_html(file_path)
        elif ext == '.pdf' or 'pdf' in mime_type:
            return ERPParserService._extract_dataframe_from_pdf(file_path)
        else:
            raise ValueError(f"Formato de archivo no soportado: {ext}")

    @staticmethod
    async def validate_purchase_order_file(
        db: AsyncSession, 
        file_path: str, 
        mime_type: str,
        erp_reference: str
    ) -> ERPImportResult:
        
        result = ERPImportResult(is_valid=False, erp_reference=erp_reference)

        # 1. Validación de Duplicidad en DB
        query_po = select(PurchaseOrder.id).where(PurchaseOrder.erp_reference == erp_reference)
        existing_po = (await db.execute(query_po)).scalar_one_or_none()
        
        if existing_po:
            result.errors.append(f"El documento ERP '{erp_reference}' ya fue importado.")
            return result

        # 2. Extracción Agnóstica del Formato (Strategy)
        try:
            df = ERPParserService._get_raw_dataframe(file_path, mime_type)
        except Exception as e:
            result.errors.append(f"Error extrayendo datos del archivo: {str(e)}")
            return result

        # 3. Limpieza Estructural Unificada
        # Las tablas de PDF y HTML suelen traer saltos de línea (\n) o espacios extra
        df.columns = df.columns.astype(str).str.strip().str.lower().str.replace('\n', ' ')
        df.dropna(how='all', inplace=True)

        if df.empty:
            result.errors.append("La tabla extraída no contiene datos.")
            return result

        # 4. Mapeo de Columnas
        sku_col = next((col for col in df.columns if any(alias in col for alias in ERPParserService.ALLOWED_SKU_COLUMNS)), None)
        qty_col = next((col for col in df.columns if any(alias in col for alias in ERPParserService.ALLOWED_QTY_COLUMNS)), None)

        if not sku_col or not qty_col:
            result.errors.append(f"No se detectaron las cabeceras requeridas. Columnas encontradas: {list(df.columns)}")
            return result

        # 5. Validación de SKUs contra la Base de Datos
        unique_skus = df[sku_col].dropna().astype(str).str.strip().unique().tolist()
        
        query_products = select(Product.sku).where(Product.sku.in_(unique_skus))
        db_skus = set((await db.execute(query_products)).scalars().all())

        missing_skus = set(unique_skus) - db_skus
        if missing_skus:
            result.errors.append(f"Productos inexistentes en el maestro: {', '.join(missing_skus)}")

        # 6. Validación Fila por Fila con Pydantic
        validated_rows = []
        for index, row in df.iterrows():
            # Limpieza de caracteres numéricos (ej. si el PDF extrajo "1,000" como texto)
            raw_qty = str(row[qty_col]).replace(',', '')
            
            try:
                validated_item = PORowSchema(
                    sku=str(row[sku_col]).strip(),
                    quantity=float(raw_qty)
                )
                validated_rows.append(validated_item)
            except Exception:
                result.errors.append(f"Fila {index + 1}: Cantidad inválida ('{row[qty_col]}').")

        # 7. Resolución
        if not result.errors:
            result.is_valid = True
            result.validated_data = validated_rows
            result.total_items = len(validated_rows)

        return result