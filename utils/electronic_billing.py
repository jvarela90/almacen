"""
Sistema de Facturación Electrónica - AlmacénPro v2.0
Generación de comprobantes electrónicos según normativa AFIP (Argentina)
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
import json
import hashlib
import re

logger = logging.getLogger(__name__)

class InvoiceType(Enum):
    """Tipos de comprobante AFIP"""
    FACTURA_A = "01"  # Factura A
    NOTA_DEBITO_A = "02"  # Nota de Débito A
    NOTA_CREDITO_A = "03"  # Nota de Crédito A
    FACTURA_B = "06"  # Factura B
    NOTA_DEBITO_B = "07"  # Nota de Débito B
    NOTA_CREDITO_B = "08"  # Nota de Crédito B
    FACTURA_C = "11"  # Factura C
    NOTA_DEBITO_C = "12"  # Nota de Débito C
    NOTA_CREDITO_C = "13"  # Nota de Crédito C
    RECIBO = "99"  # Recibo (interno)

class TaxType(Enum):
    """Tipos de impuestos"""
    IVA_21 = "21.00"
    IVA_10_5 = "10.50"
    IVA_27 = "27.00"
    IVA_5 = "5.00"
    IVA_2_5 = "2.50"
    IVA_0 = "0.00"
    IIBB = "IIBB"
    PERCEPCION_IVA = "PERC_IVA"
    PERCEPCION_IIBB = "PERC_IIBB"

class CustomerType(Enum):
    """Tipos de cliente según AFIP"""
    CONSUMIDOR_FINAL = "CF"
    RESPONSABLE_INSCRIPTO = "RI"
    MONOTRIBUTISTA = "MT"
    EXENTO = "EX"
    NO_CATEGORIZADO = "NC"

class InvoiceValidator:
    """Validador de datos para facturación electrónica"""
    
    @staticmethod
    def validate_cuit(cuit: str) -> bool:
        """Validar CUIT/CUIL argentino"""
        if not cuit or len(cuit) != 11:
            return False
        
        if not cuit.isdigit():
            return False
        
        # Algoritmo de verificación CUIT
        multipliers = [5, 4, 3, 2, 7, 6, 5, 4, 3, 2]
        sum_result = sum(int(cuit[i]) * multipliers[i] for i in range(10))
        
        remainder = sum_result % 11
        if remainder < 2:
            expected_digit = remainder
        else:
            expected_digit = 11 - remainder
            
        return int(cuit[10]) == expected_digit
    
    @staticmethod
    def validate_dni(dni: str) -> bool:
        """Validar DNI argentino"""
        if not dni:
            return False
        
        # Limpiar DNI (quitar puntos y espacios)
        clean_dni = re.sub(r'[^\d]', '', dni)
        
        if len(clean_dni) < 7 or len(clean_dni) > 8:
            return False
            
        return clean_dni.isdigit()
    
    @staticmethod
    def determine_invoice_type(customer_type: str, company_type: str = "RI") -> str:
        """Determinar tipo de comprobante según tipos de cliente y empresa"""
        if company_type == "RI":  # Empresa Responsable Inscripto
            if customer_type == "RI":
                return InvoiceType.FACTURA_A.value
            elif customer_type in ["MT", "EX"]:
                return InvoiceType.FACTURA_B.value
            else:  # CF, NC
                return InvoiceType.FACTURA_B.value
        elif company_type == "MT":  # Empresa Monotributista
            return InvoiceType.FACTURA_C.value
        else:
            return InvoiceType.FACTURA_C.value
    
    @staticmethod
    def validate_amount(amount: float) -> bool:
        """Validar que el monto sea válido"""
        return amount >= 0 and amount <= 999999999.99

class TaxCalculator:
    """Calculadora de impuestos"""
    
    @staticmethod
    def calculate_iva(net_amount: Decimal, iva_rate: Decimal) -> Dict:
        """Calcular IVA"""
        iva_amount = (net_amount * iva_rate / 100).quantize(
            Decimal('0.01'), rounding=ROUND_HALF_UP
        )
        
        return {
            'net_amount': float(net_amount),
            'iva_rate': float(iva_rate),
            'iva_amount': float(iva_amount),
            'gross_amount': float(net_amount + iva_amount)
        }
    
    @staticmethod
    def calculate_item_taxes(items: List[Dict], customer_type: str) -> Dict:
        """Calcular impuestos por items"""
        subtotal = Decimal('0')
        total_iva = Decimal('0')
        tax_details = {}
        
        for item in items:
            quantity = Decimal(str(item.get('cantidad', 0)))
            unit_price = Decimal(str(item.get('precio_unitario', 0)))
            iva_rate = Decimal(str(item.get('iva_rate', '21.00')))
            
            # Calcular subtotal del item
            item_subtotal = quantity * unit_price
            subtotal += item_subtotal
            
            # Calcular IVA solo si el cliente no es consumidor final
            if customer_type != CustomerType.CONSUMIDOR_FINAL.value:
                item_iva = (item_subtotal * iva_rate / 100).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                total_iva += item_iva
                
                # Agrupar por tasa de IVA
                iva_key = f"IVA_{iva_rate}"
                if iva_key not in tax_details:
                    tax_details[iva_key] = {
                        'rate': float(iva_rate),
                        'net_amount': 0,
                        'tax_amount': 0
                    }
                
                tax_details[iva_key]['net_amount'] += float(item_subtotal)
                tax_details[iva_key]['tax_amount'] += float(item_iva)
        
        return {
            'subtotal': float(subtotal),
            'total_iva': float(total_iva),
            'total': float(subtotal + total_iva),
            'tax_details': tax_details
        }

class InvoiceNumberGenerator:
    """Generador de numeración de comprobantes"""
    
    def __init__(self, database_manager):
        self.db = database_manager
    
    def get_next_invoice_number(self, invoice_type: str, point_of_sale: str = "0001") -> str:
        """Obtener siguiente número de comprobante"""
        try:
            # Buscar último número para el tipo y punto de venta
            query = """
                SELECT MAX(CAST(numero_comprobante AS INTEGER)) as max_num
                FROM facturas_electronicas
                WHERE tipo_comprobante = ? AND punto_venta = ?
            """
            
            result = self.db.execute_query(query, (invoice_type, point_of_sale))
            
            if result and result[0][0]:
                next_number = int(result[0][0]) + 1
            else:
                next_number = 1
                
            return f"{next_number:08d}"  # 8 dígitos con ceros a la izquierda
            
        except Exception as e:
            logger.error(f"Error obteniendo siguiente número: {e}")
            return "00000001"
    
    def reserve_invoice_number(self, invoice_type: str, point_of_sale: str = "0001") -> str:
        """Reservar número de comprobante"""
        try:
            number = self.get_next_invoice_number(invoice_type, point_of_sale)
            
            # Crear registro temporal para reservar el número
            query = """
                INSERT INTO facturas_electronicas_temp 
                (tipo_comprobante, punto_venta, numero_comprobante, fecha_reserva)
                VALUES (?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                invoice_type, point_of_sale, number, datetime.now()
            ))
            
            return number
            
        except Exception as e:
            logger.error(f"Error reservando número: {e}")
            return self.get_next_invoice_number(invoice_type, point_of_sale)

class ElectronicInvoice:
    """Representación de una factura electrónica"""
    
    def __init__(self, invoice_data: Dict):
        self.data = invoice_data
        self.validator = InvoiceValidator()
        self.tax_calculator = TaxCalculator()
        self._errors = []
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validar datos de la factura"""
        self._errors = []
        
        # Validar datos básicos
        if not self.data.get('customer_name'):
            self._errors.append("Nombre del cliente es requerido")
        
        if not self.data.get('items') or len(self.data.get('items', [])) == 0:
            self._errors.append("Debe incluir al menos un item")
        
        # Validar CUIT/DNI del cliente
        customer_cuit = self.data.get('customer_cuit', '')
        customer_dni = self.data.get('customer_dni', '')
        
        if customer_cuit and not self.validator.validate_cuit(customer_cuit):
            self._errors.append("CUIT del cliente inválido")
        
        if customer_dni and not self.validator.validate_dni(customer_dni):
            self._errors.append("DNI del cliente inválido")
        
        # Validar items
        for i, item in enumerate(self.data.get('items', [])):
            if not item.get('descripcion'):
                self._errors.append(f"Item {i+1}: Descripción requerida")
            
            if not item.get('cantidad') or float(item.get('cantidad', 0)) <= 0:
                self._errors.append(f"Item {i+1}: Cantidad debe ser mayor a 0")
            
            if not item.get('precio_unitario') or float(item.get('precio_unitario', 0)) <= 0:
                self._errors.append(f"Item {i+1}: Precio unitario debe ser mayor a 0")
        
        # Validar montos
        total = float(self.data.get('total', 0))
        if not self.validator.validate_amount(total):
            self._errors.append("Monto total inválido")
        
        return len(self._errors) == 0, self._errors
    
    def calculate_taxes(self):
        """Calcular impuestos de la factura"""
        customer_type = self.data.get('customer_type', CustomerType.CONSUMIDOR_FINAL.value)
        items = self.data.get('items', [])
        
        tax_calculation = self.tax_calculator.calculate_item_taxes(items, customer_type)
        
        # Actualizar datos con cálculos
        self.data.update(tax_calculation)
        
        return tax_calculation
    
    def generate_hash(self) -> str:
        """Generar hash de la factura para integridad"""
        hash_data = {
            'tipo_comprobante': self.data.get('invoice_type'),
            'punto_venta': self.data.get('point_of_sale'),
            'numero_comprobante': self.data.get('invoice_number'),
            'fecha': self.data.get('invoice_date').isoformat() if self.data.get('invoice_date') else '',
            'cuit_emisor': self.data.get('company_cuit'),
            'cuit_receptor': self.data.get('customer_cuit'),
            'total': str(self.data.get('total', 0))
        }
        
        hash_string = json.dumps(hash_data, sort_keys=True)
        return hashlib.sha256(hash_string.encode()).hexdigest()
    
    def to_afip_format(self) -> Dict:
        """Convertir a formato AFIP para envío"""
        return {
            'CbteTipo': int(self.data.get('invoice_type')),
            'PtoVta': int(self.data.get('point_of_sale', 1)),
            'CbteDesde': int(self.data.get('invoice_number')),
            'CbteHasta': int(self.data.get('invoice_number')),
            'CbteFch': self.data.get('invoice_date').strftime('%Y%m%d') if self.data.get('invoice_date') else '',
            'DocTipo': 80 if self.data.get('customer_cuit') else 96,  # 80=CUIT, 96=DNI
            'DocNro': int(self.data.get('customer_cuit', '0').replace('-', '')),
            'MonId': 'PES',  # Pesos argentinos
            'MonCotiz': 1,
            'ImpTotal': float(self.data.get('total', 0)),
            'ImpTotConc': 0,  # Importe neto no gravado
            'ImpNeto': float(self.data.get('subtotal', 0)),
            'ImpOpEx': 0,  # Importe exento
            'ImpTrib': 0,  # Impuestos nacionales
            'ImpIVA': float(self.data.get('total_iva', 0))
        }

class ElectronicBillingSystem:
    """Sistema principal de facturación electrónica"""
    
    def __init__(self, database_manager, company_config: Dict):
        self.db = database_manager
        self.company_config = company_config
        self.number_generator = InvoiceNumberGenerator(database_manager)
        self.validator = InvoiceValidator()
        
        # Configuración de la empresa
        self.company_cuit = company_config.get('cuit', '')
        self.company_name = company_config.get('name', '')
        self.company_type = company_config.get('type', 'RI')
        self.point_of_sale = company_config.get('point_of_sale', '0001')
        
        # Inicializar tablas si no existen
        self._initialize_tables()
    
    def _initialize_tables(self):
        """Inicializar tablas de facturación electrónica"""
        try:
            # Tabla principal de facturas electrónicas
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS facturas_electronicas (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_comprobante TEXT NOT NULL,
                    punto_venta TEXT NOT NULL,
                    numero_comprobante TEXT NOT NULL,
                    fecha_emision TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    cliente_nombre TEXT NOT NULL,
                    cliente_cuit TEXT,
                    cliente_dni TEXT,
                    cliente_tipo TEXT,
                    subtotal DECIMAL(10,2),
                    total_iva DECIMAL(10,2),
                    total DECIMAL(10,2),
                    estado TEXT DEFAULT 'PENDIENTE',
                    cae TEXT,
                    fecha_vto_cae TIMESTAMP,
                    hash_comprobante TEXT,
                    datos_json TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de items de factura
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS facturas_electronicas_items (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    factura_id INTEGER NOT NULL,
                    descripcion TEXT NOT NULL,
                    cantidad DECIMAL(10,3),
                    precio_unitario DECIMAL(10,2),
                    subtotal DECIMAL(10,2),
                    iva_rate DECIMAL(5,2),
                    iva_amount DECIMAL(10,2),
                    FOREIGN KEY (factura_id) REFERENCES facturas_electronicas(id)
                )
            """)
            
            # Tabla temporal para reservar números
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS facturas_electronicas_temp (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_comprobante TEXT NOT NULL,
                    punto_venta TEXT NOT NULL,
                    numero_comprobante TEXT NOT NULL,
                    fecha_reserva TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Tabla de impuestos por factura
            self.db.execute_query("""
                CREATE TABLE IF NOT EXISTS facturas_electronicas_impuestos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    factura_id INTEGER NOT NULL,
                    tipo_impuesto TEXT NOT NULL,
                    tasa DECIMAL(5,2),
                    base_imponible DECIMAL(10,2),
                    importe DECIMAL(10,2),
                    FOREIGN KEY (factura_id) REFERENCES facturas_electronicas(id)
                )
            """)
            
            # Índices para mejor performance
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_facturas_tipo_punto_numero 
                ON facturas_electronicas(tipo_comprobante, punto_venta, numero_comprobante)
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_facturas_fecha 
                ON facturas_electronicas(fecha_emision)
            """)
            
            self.db.execute_query("""
                CREATE INDEX IF NOT EXISTS idx_facturas_estado 
                ON facturas_electronicas(estado)
            """)
            
        except Exception as e:
            logger.error(f"Error inicializando tablas: {e}")
    
    def create_invoice(self, invoice_data: Dict) -> Tuple[bool, Dict]:
        """Crear nueva factura electrónica"""
        try:
            # Determinar tipo de cliente y comprobante
            customer_type = self._determine_customer_type(invoice_data)
            invoice_type = self.validator.determine_invoice_type(customer_type, self.company_type)
            
            # Generar número de comprobante
            invoice_number = self.number_generator.get_next_invoice_number(invoice_type, self.point_of_sale)
            
            # Completar datos de la factura
            complete_invoice_data = {
                **invoice_data,
                'invoice_type': invoice_type,
                'invoice_number': invoice_number,
                'point_of_sale': self.point_of_sale,
                'invoice_date': invoice_data.get('invoice_date', datetime.now()),
                'company_cuit': self.company_cuit,
                'company_name': self.company_name,
                'customer_type': customer_type
            }
            
            # Crear objeto de factura y validar
            invoice = ElectronicInvoice(complete_invoice_data)
            is_valid, errors = invoice.validate()
            
            if not is_valid:
                return False, {'errors': errors}
            
            # Calcular impuestos
            tax_calculation = invoice.calculate_taxes()
            
            # Generar hash
            invoice_hash = invoice.generate_hash()
            
            # Guardar en base de datos
            invoice_id = self._save_invoice_to_db(invoice, invoice_hash)
            
            if invoice_id:
                return True, {
                    'invoice_id': invoice_id,
                    'invoice_type': invoice_type,
                    'invoice_number': invoice_number,
                    'point_of_sale': self.point_of_sale,
                    'tax_calculation': tax_calculation,
                    'hash': invoice_hash
                }
            else:
                return False, {'errors': ['Error guardando factura en base de datos']}
                
        except Exception as e:
            logger.error(f"Error creando factura: {e}")
            return False, {'errors': [f'Error interno: {str(e)}']}
    
    def _determine_customer_type(self, invoice_data: Dict) -> str:
        """Determinar tipo de cliente"""
        customer_cuit = invoice_data.get('customer_cuit', '')
        customer_dni = invoice_data.get('customer_dni', '')
        
        # Si tiene CUIT válido, asumir Responsable Inscripto
        if customer_cuit and self.validator.validate_cuit(customer_cuit):
            return CustomerType.RESPONSABLE_INSCRIPTO.value
        
        # Si solo tiene DNI o no tiene documentos, es Consumidor Final
        if customer_dni or not customer_cuit:
            return CustomerType.CONSUMIDOR_FINAL.value
        
        return CustomerType.NO_CATEGORIZADO.value
    
    def _save_invoice_to_db(self, invoice: ElectronicInvoice, invoice_hash: str) -> Optional[int]:
        """Guardar factura en base de datos"""
        try:
            # Insertar factura principal
            query = """
                INSERT INTO facturas_electronicas (
                    tipo_comprobante, punto_venta, numero_comprobante,
                    cliente_nombre, cliente_cuit, cliente_dni, cliente_tipo,
                    subtotal, total_iva, total, hash_comprobante, datos_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            result = self.db.execute_query(query, (
                invoice.data.get('invoice_type'),
                invoice.data.get('point_of_sale'),
                invoice.data.get('invoice_number'),
                invoice.data.get('customer_name'),
                invoice.data.get('customer_cuit'),
                invoice.data.get('customer_dni'),
                invoice.data.get('customer_type'),
                invoice.data.get('subtotal'),
                invoice.data.get('total_iva'),
                invoice.data.get('total'),
                invoice_hash,
                json.dumps(invoice.data, default=str)
            ))
            
            if result:
                invoice_id = result[0][0] if result else None
                
                # Guardar items
                self._save_invoice_items(invoice_id, invoice.data.get('items', []))
                
                # Guardar impuestos
                self._save_invoice_taxes(invoice_id, invoice.data.get('tax_details', {}))
                
                return invoice_id
            
            return None
            
        except Exception as e:
            logger.error(f"Error guardando factura: {e}")
            return None
    
    def _save_invoice_items(self, invoice_id: int, items: List[Dict]):
        """Guardar items de la factura"""
        try:
            for item in items:
                query = """
                    INSERT INTO facturas_electronicas_items (
                        factura_id, descripcion, cantidad, precio_unitario,
                        subtotal, iva_rate, iva_amount
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                
                cantidad = Decimal(str(item.get('cantidad', 0)))
                precio_unitario = Decimal(str(item.get('precio_unitario', 0)))
                subtotal = cantidad * precio_unitario
                iva_rate = Decimal(str(item.get('iva_rate', '21.00')))
                iva_amount = (subtotal * iva_rate / 100).quantize(
                    Decimal('0.01'), rounding=ROUND_HALF_UP
                )
                
                self.db.execute_query(query, (
                    invoice_id,
                    item.get('descripcion'),
                    float(cantidad),
                    float(precio_unitario),
                    float(subtotal),
                    float(iva_rate),
                    float(iva_amount)
                ))
                
        except Exception as e:
            logger.error(f"Error guardando items: {e}")
    
    def _save_invoice_taxes(self, invoice_id: int, tax_details: Dict):
        """Guardar impuestos de la factura"""
        try:
            for tax_type, tax_data in tax_details.items():
                query = """
                    INSERT INTO facturas_electronicas_impuestos (
                        factura_id, tipo_impuesto, tasa, base_imponible, importe
                    ) VALUES (?, ?, ?, ?, ?)
                """
                
                self.db.execute_query(query, (
                    invoice_id,
                    tax_type,
                    tax_data.get('rate'),
                    tax_data.get('net_amount'),
                    tax_data.get('tax_amount')
                ))
                
        except Exception as e:
            logger.error(f"Error guardando impuestos: {e}")
    
    def get_invoice_by_id(self, invoice_id: int) -> Optional[Dict]:
        """Obtener factura por ID"""
        try:
            query = """
                SELECT * FROM facturas_electronicas WHERE id = ?
            """
            
            result = self.db.execute_query(query, (invoice_id,))
            
            if result:
                invoice_data = dict(result[0])
                
                # Cargar items
                items_query = """
                    SELECT * FROM facturas_electronicas_items WHERE factura_id = ?
                """
                items_result = self.db.execute_query(items_query, (invoice_id,))
                invoice_data['items'] = [dict(item) for item in items_result] if items_result else []
                
                # Cargar impuestos
                taxes_query = """
                    SELECT * FROM facturas_electronicas_impuestos WHERE factura_id = ?
                """
                taxes_result = self.db.execute_query(taxes_query, (invoice_id,))
                invoice_data['taxes'] = [dict(tax) for tax in taxes_result] if taxes_result else []
                
                return invoice_data
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo factura: {e}")
            return None
    
    def get_invoices_by_date_range(self, date_from: datetime, date_to: datetime) -> List[Dict]:
        """Obtener facturas por rango de fechas"""
        try:
            query = """
                SELECT * FROM facturas_electronicas
                WHERE fecha_emision BETWEEN ? AND ?
                ORDER BY fecha_emision DESC
            """
            
            result = self.db.execute_query(query, (date_from, date_to))
            
            return [dict(invoice) for invoice in result] if result else []
            
        except Exception as e:
            logger.error(f"Error obteniendo facturas por fecha: {e}")
            return []
    
    def generate_tax_book(self, year: int, month: int) -> Dict:
        """Generar libro de IVA digital"""
        try:
            date_from = datetime(year, month, 1)
            if month == 12:
                date_to = datetime(year + 1, 1, 1) - timedelta(days=1)
            else:
                date_to = datetime(year, month + 1, 1) - timedelta(days=1)
            
            invoices = self.get_invoices_by_date_range(date_from, date_to)
            
            # Resumen por tipo de IVA
            iva_summary = {}
            total_net = 0
            total_iva = 0
            total_gross = 0
            
            for invoice in invoices:
                net_amount = float(invoice.get('subtotal', 0))
                iva_amount = float(invoice.get('total_iva', 0))
                gross_amount = float(invoice.get('total', 0))
                
                total_net += net_amount
                total_iva += iva_amount
                total_gross += gross_amount
                
                # Agrupar por tipo de comprobante
                invoice_type = invoice.get('tipo_comprobante')
                if invoice_type not in iva_summary:
                    iva_summary[invoice_type] = {
                        'count': 0,
                        'net_amount': 0,
                        'iva_amount': 0,
                        'gross_amount': 0
                    }
                
                iva_summary[invoice_type]['count'] += 1
                iva_summary[invoice_type]['net_amount'] += net_amount
                iva_summary[invoice_type]['iva_amount'] += iva_amount
                iva_summary[invoice_type]['gross_amount'] += gross_amount
            
            return {
                'period': f"{month:02d}/{year}",
                'total_invoices': len(invoices),
                'total_net': total_net,
                'total_iva': total_iva,
                'total_gross': total_gross,
                'by_type': iva_summary,
                'invoices': invoices
            }
            
        except Exception as e:
            logger.error(f"Error generando libro IVA: {e}")
            return {}
    
    def export_for_afip(self, date_from: datetime, date_to: datetime) -> str:
        """Exportar datos para presentación AFIP"""
        try:
            invoices = self.get_invoices_by_date_range(date_from, date_to)
            
            # Formato para AFIP (ejemplo simplificado)
            afip_data = []
            
            for invoice in invoices:
                afip_record = {
                    'Fecha': invoice.get('fecha_emision'),
                    'Tipo': invoice.get('tipo_comprobante'),
                    'PuntoVenta': invoice.get('punto_venta'),
                    'Numero': invoice.get('numero_comprobante'),
                    'ClienteDoc': invoice.get('cliente_cuit') or invoice.get('cliente_dni'),
                    'ClienteNombre': invoice.get('cliente_nombre'),
                    'NetoGravado': invoice.get('subtotal'),
                    'IVA': invoice.get('total_iva'),
                    'Total': invoice.get('total')
                }
                afip_data.append(afip_record)
            
            # Convertir a JSON para exportación
            export_data = {
                'periodo': f"{date_from.strftime('%Y-%m')} - {date_to.strftime('%Y-%m')}",
                'empresa_cuit': self.company_cuit,
                'empresa_nombre': self.company_name,
                'comprobantes': afip_data
            }
            
            return json.dumps(export_data, indent=2, default=str, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Error exportando para AFIP: {e}")
            return ""

# Funciones de utilidad
def format_cuit(cuit: str) -> str:
    """Formatear CUIT con guiones"""
    if len(cuit) == 11 and cuit.isdigit():
        return f"{cuit[:2]}-{cuit[2:10]}-{cuit[10]}"
    return cuit

def format_invoice_number(point_of_sale: str, number: str) -> str:
    """Formatear número de comprobante"""
    return f"{point_of_sale}-{number}"

def get_invoice_type_name(invoice_type: str) -> str:
    """Obtener nombre del tipo de comprobante"""
    type_names = {
        "01": "Factura A",
        "02": "Nota de Débito A", 
        "03": "Nota de Crédito A",
        "06": "Factura B",
        "07": "Nota de Débito B",
        "08": "Nota de Crédito B", 
        "11": "Factura C",
        "12": "Nota de Débito C",
        "13": "Nota de Crédito C",
        "99": "Recibo"
    }
    return type_names.get(invoice_type, "Comprobante")

# Configuración por defecto de empresa
DEFAULT_COMPANY_CONFIG = {
    'cuit': '20123456789',
    'name': 'AlmacénPro S.A.',
    'type': 'RI',  # Responsable Inscripto
    'point_of_sale': '0001',
    'address': 'Calle Falsa 123, Buenos Aires',
    'phone': '011-1234-5678',
    'email': 'info@almacenpro.com'
}