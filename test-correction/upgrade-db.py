"""
Base de Datos Completa para AlmacénPro
Sistema ERP/POS Universal para múltiples tipos de negocio

CARACTERÍSTICAS:
- Completamente normalizada (3NF)
- Optimizada con índices estratégicos
- Flexible para múltiples tipos de negocio
- Soporte para productos físicos, servicios, combos
- Manejo de impuestos complejos
- Sistema de promociones avanzado
- Trazabilidad completa
- Multimoneda y multiidioma
"""

import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)

class CompleteDatabaseManager:
    """Gestor completo de base de datos para AlmacénPro"""
    
    def __init__(self, settings):
        self.settings = settings
        self.db_type = settings.get('database.type', 'sqlite')
        self.connection = None
        self._lock = threading.RLock()
        
        if self.db_type == 'sqlite':
            self.db_path = settings.get_database_path()
            logger.info(f"Usando SQLite: {self.db_path}")
        
        self.setup_database()
    
    def setup_database(self):
        """Configurar y crear estructura completa de base de datos"""
        try:
            # Crear directorio de base de datos si no existe
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            # Establecer conexión
            self.connection = sqlite3.connect(
                self.db_path, 
                check_same_thread=False,
                timeout=30.0
            )
            self.connection.row_factory = sqlite3.Row
            
            # Configurar SQLite para mejor rendimiento
            cursor = self.connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA cache_size=20000")
            cursor.execute("PRAGMA temp_store=MEMORY")
            cursor.execute("PRAGMA foreign_keys=ON")
            
            # Crear estructura completa
            self.create_all_tables()
            self.create_all_indexes()
            self.create_all_triggers()
            self.create_all_views()
            self.insert_initial_data()
            
            logger.info("Base de datos completa configurada correctamente")
            
        except Exception as e:
            logger.error(f"Error configurando base de datos: {e}")
            raise
    
    def create_all_tables(self):
        """Crear todas las tablas del sistema"""
        
        # ==================== TABLAS MAESTRAS ====================
        
        # 1. CONFIGURACIÓN DEL SISTEMA
        system_tables = {
            'system_config': '''
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    config_key VARCHAR(100) UNIQUE NOT NULL,
                    config_value TEXT,
                    data_type VARCHAR(20) DEFAULT 'STRING', -- STRING, INTEGER, DECIMAL, BOOLEAN, JSON
                    category VARCHAR(50) DEFAULT 'GENERAL',
                    description TEXT,
                    is_encrypted BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by INTEGER,
                    FOREIGN KEY (updated_by) REFERENCES users(id)
                )
            ''',
            
            # 2. PAÍSES, PROVINCIAS, CIUDADES
            'countries': '''
                CREATE TABLE IF NOT EXISTS countries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(3) UNIQUE NOT NULL, -- ISO 3166-1
                    name VARCHAR(100) NOT NULL,
                    currency_code VARCHAR(3), -- ISO 4217
                    tax_system VARCHAR(50), -- IVA, GST, VAT, etc.
                    active BOOLEAN DEFAULT 1
                )
            ''',
            
            'states_provinces': '''
                CREATE TABLE IF NOT EXISTS states_provinces (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    country_id INTEGER NOT NULL,
                    code VARCHAR(10),
                    name VARCHAR(100) NOT NULL,
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (country_id) REFERENCES countries(id)
                )
            ''',
            
            'cities': '''
                CREATE TABLE IF NOT EXISTS cities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    state_province_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    postal_code VARCHAR(20),
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (state_province_id) REFERENCES states_provinces(id)
                )
            ''',
            
            # 3. MONEDAS Y TIPOS DE CAMBIO
            'currencies': '''
                CREATE TABLE IF NOT EXISTS currencies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(3) UNIQUE NOT NULL, -- ISO 4217
                    name VARCHAR(50) NOT NULL,
                    symbol VARCHAR(10),
                    decimal_places INTEGER DEFAULT 2,
                    is_base_currency BOOLEAN DEFAULT 0,
                    active BOOLEAN DEFAULT 1
                )
            ''',
            
            'exchange_rates': '''
                CREATE TABLE IF NOT EXISTS exchange_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_currency_id INTEGER NOT NULL,
                    to_currency_id INTEGER NOT NULL,
                    rate DECIMAL(15,6) NOT NULL,
                    date DATE NOT NULL,
                    source VARCHAR(50), -- BCRA, Yahoo, Manual, etc.
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (from_currency_id) REFERENCES currencies(id),
                    FOREIGN KEY (to_currency_id) REFERENCES currencies(id),
                    UNIQUE(from_currency_id, to_currency_id, date)
                )
            ''',
            
            # 4. IMPUESTOS Y ALÍCUOTAS
            'tax_types': '''
                CREATE TABLE IF NOT EXISTS tax_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(20) UNIQUE NOT NULL, -- IVA, IIBB, etc.
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    country_id INTEGER,
                    is_percentage BOOLEAN DEFAULT 1,
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (country_id) REFERENCES countries(id)
                )
            ''',
            
            'tax_rates': '''
                CREATE TABLE IF NOT EXISTS tax_rates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tax_type_id INTEGER NOT NULL,
                    rate DECIMAL(8,4) NOT NULL, -- 21.0000 para 21%
                    description VARCHAR(100), -- Gravado, Exento, No Gravado
                    valid_from DATE NOT NULL,
                    valid_to DATE,
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (tax_type_id) REFERENCES tax_types(id)
                )
            ''',
        }
        
        # ==================== USUARIOS Y SEGURIDAD ====================
        
        user_tables = {
            'roles': '''
                CREATE TABLE IF NOT EXISTS roles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    display_name VARCHAR(100),
                    description TEXT,
                    permissions TEXT, -- JSON con permisos detallados
                    level INTEGER DEFAULT 1, -- Nivel jerárquico
                    color VARCHAR(7), -- Color HEX para UI
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''',
            
            'users': '''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    email VARCHAR(100) UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    full_name VARCHAR(200) GENERATED ALWAYS AS (first_name || ' ' || last_name) STORED,
                    phone VARCHAR(50),
                    role_id INTEGER,
                    employee_code VARCHAR(20),
                    hire_date DATE,
                    birth_date DATE,
                    address TEXT,
                    city_id INTEGER,
                    avatar_url VARCHAR(255),
                    language_code VARCHAR(5) DEFAULT 'es',
                    timezone VARCHAR(50) DEFAULT 'America/Argentina/Buenos_Aires',
                    active BOOLEAN DEFAULT 1,
                    verified BOOLEAN DEFAULT 0,
                    last_login TIMESTAMP,
                    login_attempts INTEGER DEFAULT 0,
                    locked_until TIMESTAMP,
                    password_expires_at TIMESTAMP,
                    two_factor_enabled BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (role_id) REFERENCES roles(id),
                    FOREIGN KEY (city_id) REFERENCES cities(id)
                )
            ''',
            
            'user_sessions': '''
                CREATE TABLE IF NOT EXISTS user_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    session_token VARCHAR(255) UNIQUE NOT NULL,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    device_type VARCHAR(50), -- desktop, mobile, tablet
                    location VARCHAR(100),
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''',
        }
        
        # ==================== ORGANIZACIÓN EMPRESARIAL ====================
        
        organization_tables = {
            'companies': '''
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    legal_name VARCHAR(200) NOT NULL,
                    trade_name VARCHAR(200),
                    tax_id VARCHAR(50), -- CUIT, RUT, etc.
                    business_type VARCHAR(100), -- S.A., S.R.L., etc.
                    industry VARCHAR(100),
                    website VARCHAR(200),
                    email VARCHAR(100),
                    phone VARCHAR(50),
                    address TEXT,
                    city_id INTEGER,
                    logo_url VARCHAR(255),
                    primary_currency_id INTEGER DEFAULT 1,
                    fiscal_year_start INTEGER DEFAULT 1, -- Mes de inicio del año fiscal
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (city_id) REFERENCES cities(id),
                    FOREIGN KEY (primary_currency_id) REFERENCES currencies(id)
                )
            ''',
            
            'business_units': '''
                CREATE TABLE IF NOT EXISTS business_units (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    manager_user_id INTEGER,
                    address TEXT,
                    city_id INTEGER,
                    phone VARCHAR(50),
                    email VARCHAR(100),
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (company_id) REFERENCES companies(id),
                    FOREIGN KEY (manager_user_id) REFERENCES users(id),
                    FOREIGN KEY (city_id) REFERENCES cities(id)
                )
            ''',
            
            'locations': '''
                CREATE TABLE IF NOT EXISTS locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    business_unit_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    location_type VARCHAR(50), -- STORE, WAREHOUSE, OFFICE, VIRTUAL
                    address TEXT,
                    city_id INTEGER,
                    latitude DECIMAL(10,8),
                    longitude DECIMAL(11,8),
                    manager_user_id INTEGER,
                    square_meters DECIMAL(8,2),
                    rental_cost DECIMAL(10,2),
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (business_unit_id) REFERENCES business_units(id),
                    FOREIGN KEY (city_id) REFERENCES cities(id),
                    FOREIGN KEY (manager_user_id) REFERENCES users(id)
                )
            ''',
            
            'cash_registers': '''
                CREATE TABLE IF NOT EXISTS cash_registers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    pos_number INTEGER, -- Número de punto de venta
                    printer_name VARCHAR(200),
                    cash_drawer_port VARCHAR(50),
                    barcode_scanner_port VARCHAR(50),
                    scale_port VARCHAR(50),
                    scale_brand VARCHAR(50),
                    receipt_header TEXT,
                    receipt_footer TEXT,
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (location_id) REFERENCES locations(id)
                )
            ''',
        }
        
        # ==================== PRODUCTOS Y CATÁLOGO ====================
        
        product_tables = {
            'product_categories': '''
                CREATE TABLE IF NOT EXISTS product_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_category_id INTEGER,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    image_url VARCHAR(255),
                    sort_order INTEGER DEFAULT 0,
                    tax_rate_id INTEGER, -- Impuesto por defecto para la categoría
                    commission_rate DECIMAL(5,2) DEFAULT 0, -- Comisión para vendedores
                    active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_category_id) REFERENCES product_categories(id),
                    FOREIGN KEY (tax_rate_id) REFERENCES tax_rates(id)
                )
            ''',
            
            'brands': '''
                CREATE TABLE IF NOT EXISTS brands (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    logo_url VARCHAR(255),
                    website VARCHAR(200),
                    country_id INTEGER,
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (country_id) REFERENCES countries(id)
                )
            ''',
            
            'units_of_measure': '''
                CREATE TABLE IF NOT EXISTS units_of_measure (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(10) UNIQUE NOT NULL, -- KG, L, M, UN, etc.
                    name VARCHAR(50) NOT NULL,
                    symbol VARCHAR(10),
                    unit_type VARCHAR(50), -- WEIGHT, VOLUME, LENGTH, COUNT, TIME
                    base_unit_id INTEGER, -- Para conversiones
                    conversion_factor DECIMAL(15,6), -- Factor de conversión a unidad base
                    decimal_places INTEGER DEFAULT 3,
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (base_unit_id) REFERENCES units_of_measure(id)
                )
            ''',
            
            'products': '''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sku VARCHAR(50) UNIQUE, -- Stock Keeping Unit
                    barcode VARCHAR(50) UNIQUE,
                    internal_code VARCHAR(50),
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    short_description VARCHAR(500),
                    product_type VARCHAR(50) DEFAULT 'PHYSICAL', -- PHYSICAL, SERVICE, DIGITAL, COMBO
                    category_id INTEGER,
                    brand_id INTEGER,
                    
                    -- Precios y costos
                    cost_price DECIMAL(15,4) DEFAULT 0,
                    markup_percentage DECIMAL(8,4) DEFAULT 0,
                    sale_price DECIMAL(15,4) NOT NULL,
                    wholesale_price DECIMAL(15,4) DEFAULT 0,
                    retail_price DECIMAL(15,4) DEFAULT 0,
                    minimum_price DECIMAL(15,4) DEFAULT 0, -- Precio mínimo de venta
                    suggested_price DECIMAL(15,4) DEFAULT 0,
                    
                    -- Unidades y medidas
                    primary_unit_id INTEGER NOT NULL,
                    secondary_unit_id INTEGER, -- Para productos que se venden en dos unidades
                    conversion_factor DECIMAL(10,4) DEFAULT 1, -- Factor entre unidad primaria y secundaria
                    is_weighable BOOLEAN DEFAULT 0,
                    weight DECIMAL(10,4),
                    weight_unit_id INTEGER,
                    volume DECIMAL(10,4),
                    volume_unit_id INTEGER,
                    dimensions VARCHAR(50), -- 10x20x30 cm
                    
                    -- Stock y inventario
                    track_stock BOOLEAN DEFAULT 1,
                    current_stock DECIMAL(12,4) DEFAULT 0,
                    minimum_stock DECIMAL(12,4) DEFAULT 0,
                    maximum_stock DECIMAL(12,4) DEFAULT 0,
                    reorder_point DECIMAL(12,4) DEFAULT 0,
                    reorder_quantity DECIMAL(12,4) DEFAULT 0,
                    allow_negative_stock BOOLEAN DEFAULT 0,
                    stock_location VARCHAR(100), -- Ubicación en depósito
                    
                    -- Información adicional
                    manufacturer VARCHAR(100),
                    model VARCHAR(100),
                    color VARCHAR(50),
                    size VARCHAR(50),
                    season VARCHAR(20), -- SPRING, SUMMER, etc.
                    gender VARCHAR(20), -- MALE, FEMALE, UNISEX, KIDS
                    age_group VARCHAR(50), -- ADULT, CHILD, BABY, etc.
                    
                    -- Control de calidad y trazabilidad
                    requires_lot_tracking BOOLEAN DEFAULT 0,
                    requires_serial_tracking BOOLEAN DEFAULT 0,
                    has_expiration_date BOOLEAN DEFAULT 0,
                    shelf_life_days INTEGER, -- Vida útil en días
                    
                    -- Impuestos
                    tax_rate_id INTEGER,
                    tax_exempt BOOLEAN DEFAULT 0,
                    
                    -- Proveedores
                    primary_supplier_id INTEGER,
                    supplier_sku VARCHAR(50), -- SKU del proveedor
                    lead_time_days INTEGER DEFAULT 0, -- Días de entrega del proveedor
                    
                    -- Producción propia
                    is_manufactured BOOLEAN DEFAULT 0,
                    recipe_id INTEGER, -- Si se fabrica internamente
                    production_time_minutes INTEGER,
                    
                    -- Venta y visualización
                    is_active BOOLEAN DEFAULT 1,
                    is_featured BOOLEAN DEFAULT 0,
                    is_on_sale BOOLEAN DEFAULT 0,
                    sale_price_from DATE,
                    sale_price_to DATE,
                    
                    -- SEO y marketing
                    meta_title VARCHAR(200),
                    meta_description TEXT,
                    tags TEXT, -- Separados por comas
                    
                    -- Imágenes y multimedia
                    primary_image_url VARCHAR(255),
                    
                    -- Auditoría
                    created_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (category_id) REFERENCES product_categories(id),
                    FOREIGN KEY (brand_id) REFERENCES brands(id),
                    FOREIGN KEY (primary_unit_id) REFERENCES units_of_measure(id),
                    FOREIGN KEY (secondary_unit_id) REFERENCES units_of_measure(id),
                    FOREIGN KEY (weight_unit_id) REFERENCES units_of_measure(id),
                    FOREIGN KEY (volume_unit_id) REFERENCES units_of_measure(id),
                    FOREIGN KEY (tax_rate_id) REFERENCES tax_rates(id),
                    FOREIGN KEY (primary_supplier_id) REFERENCES suppliers(id),
                    FOREIGN KEY (recipe_id) REFERENCES recipes(id),
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (updated_by) REFERENCES users(id)
                )
            ''',
            
            'product_images': '''
                CREATE TABLE IF NOT EXISTS product_images (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    image_url VARCHAR(255) NOT NULL,
                    alt_text VARCHAR(200),
                    sort_order INTEGER DEFAULT 0,
                    is_primary BOOLEAN DEFAULT 0,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            ''',
            
            'product_variants': '''
                CREATE TABLE IF NOT EXISTS product_variants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_product_id INTEGER NOT NULL,
                    variant_name VARCHAR(100), -- Rojo-L, Azul-XL, etc.
                    sku VARCHAR(50) UNIQUE,
                    barcode VARCHAR(50) UNIQUE,
                    additional_cost DECIMAL(15,4) DEFAULT 0,
                    additional_price DECIMAL(15,4) DEFAULT 0,
                    current_stock DECIMAL(12,4) DEFAULT 0,
                    image_url VARCHAR(255),
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (parent_product_id) REFERENCES products(id) ON DELETE CASCADE
                )
            ''',
            
            'product_attributes': '''
                CREATE TABLE IF NOT EXISTS product_attributes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(50) NOT NULL, -- Color, Talla, Material, etc.
                    display_name VARCHAR(100),
                    attribute_type VARCHAR(20) DEFAULT 'TEXT', -- TEXT, NUMBER, BOOLEAN, SELECT
                    is_required BOOLEAN DEFAULT 0,
                    is_variant_attribute BOOLEAN DEFAULT 0, -- Si genera variantes
                    sort_order INTEGER DEFAULT 0
                )
            ''',
            
            'product_attribute_values': '''
                CREATE TABLE IF NOT EXISTS product_attribute_values (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    attribute_id INTEGER NOT NULL,
                    value TEXT NOT NULL,
                    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
                    FOREIGN KEY (attribute_id) REFERENCES product_attributes(id),
                    UNIQUE(product_id, attribute_id)
                )
            ''',
        }
        
        # ==================== INVENTARIO Y STOCK ====================
        
        inventory_tables = {
            'warehouses': '''
                CREATE TABLE IF NOT EXISTS warehouses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    location_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    warehouse_type VARCHAR(50), -- MAIN, SECONDARY, VIRTUAL, CONSIGNMENT
                    address TEXT,
                    manager_user_id INTEGER,
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (location_id) REFERENCES locations(id),
                    FOREIGN KEY (manager_user_id) REFERENCES users(id)
                )
            ''',
            
            'warehouse_zones': '''
                CREATE TABLE IF NOT EXISTS warehouse_zones (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    warehouse_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    zone_type VARCHAR(50), -- RECEIVING, STORAGE, PICKING, SHIPPING
                    capacity_units DECIMAL(12,4),
                    current_occupancy DECIMAL(12,4) DEFAULT 0,
                    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id)
                )
            ''',
            
            'storage_locations': '''
                CREATE TABLE IF NOT EXISTS storage_locations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    warehouse_zone_id INTEGER NOT NULL,
                    location_code VARCHAR(50) UNIQUE NOT NULL, -- A01-B02-C03
                    description TEXT,
                    capacity_units DECIMAL(12,4),
                    current_occupancy DECIMAL(12,4) DEFAULT 0,
                    location_type VARCHAR(50), -- SHELF, PALLET, FLOOR, REFRIGERATED
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (warehouse_zone_id) REFERENCES warehouse_zones(id)
                )
            ''',
            
            'stock_movements': '''
                CREATE TABLE IF NOT EXISTS stock_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    warehouse_id INTEGER NOT NULL,
                    movement_type VARCHAR(30) NOT NULL, -- IN, OUT, TRANSFER, ADJUSTMENT
                    movement_reason VARCHAR(50), -- SALE, PURCHASE, RETURN, DAMAGE, THEFT, etc.
                    reference_type VARCHAR(50), -- SALE, PURCHASE, TRANSFER, ADJUSTMENT, etc.
                    reference_id INTEGER, -- ID del documento relacionado
                    
                    quantity_before DECIMAL(12,4),
                    quantity_moved DECIMAL(12,4) NOT NULL,
                    quantity_after DECIMAL(12,4),
                    
                    unit_cost DECIMAL(15,4),
                    total_cost DECIMAL(15,4),
                    
                    lot_number VARCHAR(50),
                    serial_number VARCHAR(100),
                    expiration_date DATE,
                    
                    storage_location_id INTEGER,
                    from_warehouse_id INTEGER, -- Para transferencias
                    to_warehouse_id INTEGER, -- Para transferencias
                    
                    notes TEXT,
                    user_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                    FOREIGN KEY (storage_location_id) REFERENCES storage_locations(id),
                    FOREIGN KEY (from_warehouse_id) REFERENCES warehouses(id),
                    FOREIGN KEY (to_warehouse_id) REFERENCES warehouses(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''',
            
            'stock_by_location': '''
                CREATE TABLE IF NOT EXISTS stock_by_location (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    warehouse_id INTEGER NOT NULL,
                    storage_location_id INTEGER,
                    current_stock DECIMAL(12,4) DEFAULT 0,
                    reserved_stock DECIMAL(12,4) DEFAULT 0, -- Stock reservado para órdenes
                    available_stock DECIMAL(12,4) GENERATED ALWAYS AS (current_stock - reserved_stock) STORED,
                    lot_number VARCHAR(50),
                    serial_number VARCHAR(100),
                    expiration_date DATE,
                    last_movement_date TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                    FOREIGN KEY (storage_location_id) REFERENCES storage_locations(id),
                    UNIQUE(product_id, warehouse_id, storage_location_id, lot_number, serial_number)
                )
            ''',
            
            'inventory_adjustments': '''
                CREATE TABLE IF NOT EXISTS inventory_adjustments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adjustment_number VARCHAR(50) UNIQUE NOT NULL,
                    warehouse_id INTEGER NOT NULL,
                    adjustment_type VARCHAR(30), -- PHYSICAL_COUNT, DAMAGE, THEFT, EXPIRATION
                    status VARCHAR(20) DEFAULT 'DRAFT', -- DRAFT, APPROVED, POSTED
                    total_adjustment_value DECIMAL(15,4) DEFAULT 0,
                    reason TEXT,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                    FOREIGN KEY (approved_by) REFERENCES users(id),
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            ''',
            
            'inventory_adjustment_details': '''
                CREATE TABLE IF NOT EXISTS inventory_adjustment_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    adjustment_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    storage_location_id INTEGER,
                    lot_number VARCHAR(50),
                    serial_number VARCHAR(100),
                    expected_quantity DECIMAL(12,4),
                    actual_quantity DECIMAL(12,4),
                    quantity_difference DECIMAL(12,4) GENERATED ALWAYS AS (actual_quantity - expected_quantity) STORED,
                    unit_cost DECIMAL(15,4),
                    adjustment_value DECIMAL(15,4) GENERATED ALWAYS AS (quantity_difference * unit_cost) STORED,
                    reason TEXT,
                    FOREIGN KEY (adjustment_id) REFERENCES inventory_adjustments(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    FOREIGN KEY (storage_location_id) REFERENCES storage_locations(id)
                )
            ''',
        }
        
        # ==================== PROVEEDORES Y COMPRAS ====================
        
        supplier_tables = {
            'suppliers': '''
                CREATE TABLE IF NOT EXISTS suppliers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_code VARCHAR(50) UNIQUE,
                    legal_name VARCHAR(200) NOT NULL,
                    trade_name VARCHAR(200),
                    tax_id VARCHAR(50), -- CUIT, RUT, etc.
                    tax_category VARCHAR(50), -- Responsable Inscripto, Monotributista, etc.
                    
                    -- Contacto principal
                    contact_person VARCHAR(100),
                    contact_position VARCHAR(100),
                    phone VARCHAR(50),
                    mobile VARCHAR(50),
                    email VARCHAR(100),
                    website VARCHAR(200),
                    
                    -- Dirección
                    address TEXT,
                    city_id INTEGER,
                    
                    -- Términos comerciales
                    payment_terms_days INTEGER DEFAULT 0, -- Días de crédito
                    credit_limit DECIMAL(15,4) DEFAULT 0,
                    discount_percentage DECIMAL(5,2) DEFAULT 0,
                    currency_id INTEGER DEFAULT 1,
                    
                    -- Calificación
                    rating INTEGER DEFAULT 5, -- 1-5 estrellas
                    delivery_rating INTEGER DEFAULT 5,
                    quality_rating INTEGER DEFAULT 5,
                    service_rating INTEGER DEFAULT 5,
                    
                    -- Categorización
                    supplier_type VARCHAR(50), -- MANUFACTURER, DISTRIBUTOR, WHOLESALER, SERVICE
                    business_size VARCHAR(20), -- MICRO, SMALL, MEDIUM, LARGE
                    
                    -- Estado
                    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, INACTIVE, BLOCKED
                    blocked_reason TEXT,
                    
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (city_id) REFERENCES cities(id),
                    FOREIGN KEY (currency_id) REFERENCES currencies(id)
                )
            ''',
            
            'supplier_contacts': '''
                CREATE TABLE IF NOT EXISTS supplier_contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    position VARCHAR(100),
                    department VARCHAR(100),
                    phone VARCHAR(50),
                    mobile VARCHAR(50),
                    email VARCHAR(100),
                    is_primary BOOLEAN DEFAULT 0,
                    notes TEXT,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE
                )
            ''',
            
            'supplier_products': '''
                CREATE TABLE IF NOT EXISTS supplier_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    supplier_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    supplier_sku VARCHAR(100),
                    supplier_name VARCHAR(200),
                    cost_price DECIMAL(15,4),
                    currency_id INTEGER DEFAULT 1,
                    minimum_order_quantity DECIMAL(12,4) DEFAULT 1,
                    lead_time_days INTEGER DEFAULT 0,
                    is_preferred_supplier BOOLEAN DEFAULT 0,
                    discount_percentage DECIMAL(5,2) DEFAULT 0,
                    active BOOLEAN DEFAULT 1,
                    last_cost_update TIMESTAMP,
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    FOREIGN KEY (currency_id) REFERENCES currencies(id),
                    UNIQUE(supplier_id, product_id)
                )
            ''',
            
            'purchase_orders': '''
                CREATE TABLE IF NOT EXISTS purchase_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number VARCHAR(50) UNIQUE NOT NULL,
                    supplier_id INTEGER NOT NULL,
                    warehouse_id INTEGER NOT NULL,
                    currency_id INTEGER NOT NULL,
                    exchange_rate DECIMAL(15,6) DEFAULT 1,
                    
                    order_date DATE NOT NULL,
                    expected_delivery_date DATE,
                    actual_delivery_date DATE,
                    
                    status VARCHAR(20) DEFAULT 'DRAFT', -- DRAFT, SENT, CONFIRMED, PARTIAL, RECEIVED, CANCELLED
                    
                    subtotal DECIMAL(15,4) DEFAULT 0,
                    discount_amount DECIMAL(15,4) DEFAULT 0,
                    tax_amount DECIMAL(15,4) DEFAULT 0,
                    total_amount DECIMAL(15,4) NOT NULL,
                    
                    payment_terms_days INTEGER DEFAULT 0,
                    payment_method VARCHAR(50),
                    
                    shipping_address TEXT,
                    billing_address TEXT,
                    
                    notes TEXT,
                    internal_notes TEXT,
                    
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                    FOREIGN KEY (currency_id) REFERENCES currencies(id),
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (approved_by) REFERENCES users(id)
                )
            ''',
            
            'purchase_order_details': '''
                CREATE TABLE IF NOT EXISTS purchase_order_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    purchase_order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity_ordered DECIMAL(12,4) NOT NULL,
                    quantity_received DECIMAL(12,4) DEFAULT 0,
                    quantity_pending DECIMAL(12,4) GENERATED ALWAYS AS (quantity_ordered - quantity_received) STORED,
                    unit_cost DECIMAL(15,4) NOT NULL,
                    discount_percentage DECIMAL(5,2) DEFAULT 0,
                    discount_amount DECIMAL(15,4) DEFAULT 0,
                    tax_rate_id INTEGER,
                    tax_amount DECIMAL(15,4) DEFAULT 0,
                    line_total DECIMAL(15,4) NOT NULL,
                    notes TEXT,
                    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    FOREIGN KEY (tax_rate_id) REFERENCES tax_rates(id)
                )
            ''',
            
            'goods_receipts': '''
                CREATE TABLE IF NOT EXISTS goods_receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_number VARCHAR(50) UNIQUE NOT NULL,
                    purchase_order_id INTEGER,
                    supplier_id INTEGER NOT NULL,
                    warehouse_id INTEGER NOT NULL,
                    
                    receipt_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    supplier_invoice_number VARCHAR(100),
                    supplier_invoice_date DATE,
                    
                    status VARCHAR(20) DEFAULT 'DRAFT', -- DRAFT, POSTED
                    
                    total_items INTEGER DEFAULT 0,
                    total_quantity DECIMAL(12,4) DEFAULT 0,
                    total_amount DECIMAL(15,4) DEFAULT 0,
                    
                    notes TEXT,
                    
                    received_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    posted_by INTEGER,
                    posted_at TIMESTAMP,
                    
                    FOREIGN KEY (purchase_order_id) REFERENCES purchase_orders(id),
                    FOREIGN KEY (supplier_id) REFERENCES suppliers(id),
                    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                    FOREIGN KEY (received_by) REFERENCES users(id),
                    FOREIGN KEY (posted_by) REFERENCES users(id)
                )
            ''',
            
            'goods_receipt_details': '''
                CREATE TABLE IF NOT EXISTS goods_receipt_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goods_receipt_id INTEGER NOT NULL,
                    purchase_order_detail_id INTEGER,
                    product_id INTEGER NOT NULL,
                    quantity_received DECIMAL(12,4) NOT NULL,
                    unit_cost DECIMAL(15,4) NOT NULL,
                    lot_number VARCHAR(50),
                    serial_number VARCHAR(100),
                    expiration_date DATE,
                    storage_location_id INTEGER,
                    quality_status VARCHAR(20) DEFAULT 'APPROVED', -- APPROVED, REJECTED, QUARANTINE
                    notes TEXT,
                    FOREIGN KEY (goods_receipt_id) REFERENCES goods_receipts(id) ON DELETE CASCADE,
                    FOREIGN KEY (purchase_order_detail_id) REFERENCES purchase_order_details(id),
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    FOREIGN KEY (storage_location_id) REFERENCES storage_locations(id)
                )
            ''',
        }
        
        # ==================== CLIENTES Y VENTAS ====================
        
        customer_tables = {
            'customer_categories': '''
                CREATE TABLE IF NOT EXISTS customer_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT,
                    discount_percentage DECIMAL(5,2) DEFAULT 0,
                    credit_limit DECIMAL(15,4) DEFAULT 0,
                    payment_terms_days INTEGER DEFAULT 0,
                    color VARCHAR(7), -- Color HEX para UI
                    active BOOLEAN DEFAULT 1
                )
            ''',
            
            'customers': '''
                CREATE TABLE IF NOT EXISTS customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_code VARCHAR(50) UNIQUE,
                    customer_type VARCHAR(20) DEFAULT 'INDIVIDUAL', -- INDIVIDUAL, BUSINESS
                    
                    -- Información personal/empresarial
                    first_name VARCHAR(100),
                    last_name VARCHAR(100),
                    full_name VARCHAR(200) GENERATED ALWAYS AS (
                        CASE 
                            WHEN customer_type = 'BUSINESS' THEN company_name
                            ELSE first_name || ' ' || COALESCE(last_name, '')
                        END
                    ) STORED,
                    company_name VARCHAR(200),
                    tax_id VARCHAR(50), -- DNI, CUIT, etc.
                    tax_category VARCHAR(50),
                    
                    -- Contacto
                    phone VARCHAR(50),
                    mobile VARCHAR(50),
                    email VARCHAR(100),
                    website VARCHAR(200),
                    
                    -- Dirección principal
                    address TEXT,
                    city_id INTEGER,
                    
                    -- Información comercial
                    customer_category_id INTEGER,
                    credit_limit DECIMAL(15,4) DEFAULT 0,
                    current_balance DECIMAL(15,4) DEFAULT 0,
                    payment_terms_days INTEGER DEFAULT 0,
                    discount_percentage DECIMAL(5,2) DEFAULT 0,
                    price_list VARCHAR(50) DEFAULT 'RETAIL', -- RETAIL, WHOLESALE, VIP
                    
                    -- Fechas importantes
                    birth_date DATE,
                    registration_date DATE DEFAULT (DATE('now')),
                    last_purchase_date DATE,
                    
                    -- Preferencias
                    preferred_language VARCHAR(5) DEFAULT 'es',
                    marketing_consent BOOLEAN DEFAULT 0,
                    newsletter_subscription BOOLEAN DEFAULT 0,
                    
                    -- Estado
                    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, INACTIVE, BLOCKED
                    blocked_reason TEXT,
                    
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (city_id) REFERENCES cities(id),
                    FOREIGN KEY (customer_category_id) REFERENCES customer_categories(id)
                )
            ''',
            
            'customer_addresses': '''
                CREATE TABLE IF NOT EXISTS customer_addresses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    address_type VARCHAR(20) DEFAULT 'BILLING', -- BILLING, SHIPPING, OTHER
                    address_name VARCHAR(100), -- Casa, Oficina, etc.
                    contact_name VARCHAR(100),
                    address TEXT NOT NULL,
                    city_id INTEGER,
                    postal_code VARCHAR(20),
                    phone VARCHAR(50),
                    is_default BOOLEAN DEFAULT 0,
                    delivery_notes TEXT,
                    FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE,
                    FOREIGN KEY (city_id) REFERENCES cities(id)
                )
            ''',
            
            'sales_orders': '''
                CREATE TABLE IF NOT EXISTS sales_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number VARCHAR(50) UNIQUE NOT NULL,
                    customer_id INTEGER,
                    cash_register_id INTEGER NOT NULL,
                    warehouse_id INTEGER NOT NULL,
                    
                    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    delivery_date DATE,
                    
                    order_type VARCHAR(20) DEFAULT 'CASH', -- CASH, CREDIT, ACCOUNT
                    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, CONFIRMED, SHIPPED, DELIVERED, CANCELLED
                    
                    currency_id INTEGER DEFAULT 1,
                    exchange_rate DECIMAL(15,6) DEFAULT 1,
                    
                    subtotal DECIMAL(15,4) DEFAULT 0,
                    discount_amount DECIMAL(15,4) DEFAULT 0,
                    tax_amount DECIMAL(15,4) DEFAULT 0,
                    total_amount DECIMAL(15,4) NOT NULL,
                    
                    payment_method VARCHAR(50), -- CASH, CARD, TRANSFER, CHECK, ACCOUNT
                    payment_reference VARCHAR(100), -- Número de cheque, autorización, etc.
                    
                    -- Direcciones
                    billing_address_id INTEGER,
                    shipping_address_id INTEGER,
                    
                    notes TEXT,
                    internal_notes TEXT,
                    
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (cash_register_id) REFERENCES cash_registers(id),
                    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                    FOREIGN KEY (currency_id) REFERENCES currencies(id),
                    FOREIGN KEY (billing_address_id) REFERENCES customer_addresses(id),
                    FOREIGN KEY (shipping_address_id) REFERENCES customer_addresses(id),
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            ''',
            
            'sales_order_details': '''
                CREATE TABLE IF NOT EXISTS sales_order_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sales_order_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    quantity DECIMAL(12,4) NOT NULL,
                    unit_price DECIMAL(15,4) NOT NULL,
                    discount_percentage DECIMAL(5,2) DEFAULT 0,
                    discount_amount DECIMAL(15,4) DEFAULT 0,
                    tax_rate_id INTEGER,
                    tax_amount DECIMAL(15,4) DEFAULT 0,
                    line_total DECIMAL(15,4) NOT NULL,
                    
                    -- Para productos pesables
                    weight DECIMAL(10,4),
                    tare DECIMAL(10,4),
                    net_weight DECIMAL(10,4),
                    
                    -- Trazabilidad
                    lot_number VARCHAR(50),
                    serial_number VARCHAR(100),
                    
                    notes TEXT,
                    
                    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    FOREIGN KEY (tax_rate_id) REFERENCES tax_rates(id)
                )
            ''',
            
            'receipts': '''
                CREATE TABLE IF NOT EXISTS receipts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    receipt_number VARCHAR(50) UNIQUE NOT NULL,
                    sales_order_id INTEGER NOT NULL,
                    receipt_type VARCHAR(20) DEFAULT 'TICKET', -- TICKET, INVOICE_A, INVOICE_B, etc.
                    
                    issue_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    due_date DATE,
                    
                    -- Facturación electrónica
                    electronic_invoice BOOLEAN DEFAULT 0,
                    cae VARCHAR(20), -- Código de Autorización Electrónica
                    cae_due_date DATE,
                    barcode VARCHAR(100),
                    qr_code TEXT,
                    
                    -- Estado
                    status VARCHAR(20) DEFAULT 'ISSUED', -- ISSUED, CANCELLED, CREDITED
                    cancellation_reason TEXT,
                    
                    -- Impresión
                    print_count INTEGER DEFAULT 0,
                    last_printed_at TIMESTAMP,
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id)
                )
            ''',
        }
        
        # ==================== CUENTAS CORRIENTES ====================
        
        account_tables = {
            'customer_accounts': '''
                CREATE TABLE IF NOT EXISTS customer_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_id INTEGER NOT NULL,
                    account_number VARCHAR(50) UNIQUE,
                    current_balance DECIMAL(15,4) DEFAULT 0,
                    credit_limit DECIMAL(15,4) DEFAULT 0,
                    available_credit DECIMAL(15,4) GENERATED ALWAYS AS (credit_limit - current_balance) STORED,
                    last_payment_date DATE,
                    last_charge_date DATE,
                    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, SUSPENDED, CLOSED
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    UNIQUE(customer_id)
                )
            ''',
            
            'account_movements': '''
                CREATE TABLE IF NOT EXISTS account_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_account_id INTEGER NOT NULL,
                    movement_type VARCHAR(20) NOT NULL, -- CHARGE, PAYMENT, ADJUSTMENT
                    reference_type VARCHAR(50), -- SALE, PAYMENT, CREDIT_NOTE, etc.
                    reference_id INTEGER,
                    reference_number VARCHAR(50),
                    
                    amount DECIMAL(15,4) NOT NULL,
                    balance_before DECIMAL(15,4),
                    balance_after DECIMAL(15,4),
                    
                    currency_id INTEGER DEFAULT 1,
                    exchange_rate DECIMAL(15,6) DEFAULT 1,
                    
                    due_date DATE,
                    payment_method VARCHAR(50),
                    
                    description TEXT,
                    notes TEXT,
                    
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (customer_account_id) REFERENCES customer_accounts(id),
                    FOREIGN KEY (currency_id) REFERENCES currencies(id),
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            ''',
            
            'payment_methods': '''
                CREATE TABLE IF NOT EXISTS payment_methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(20) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    method_type VARCHAR(50), -- CASH, CARD, TRANSFER, CHECK, DIGITAL_WALLET
                    requires_reference BOOLEAN DEFAULT 0,
                    processing_fee_percentage DECIMAL(5,4) DEFAULT 0,
                    processing_fee_fixed DECIMAL(15,4) DEFAULT 0,
                    settlement_days INTEGER DEFAULT 0, -- Días hasta que se acredita
                    active BOOLEAN DEFAULT 1,
                    sort_order INTEGER DEFAULT 0
                )
            ''',
            
            'payments': '''
                CREATE TABLE IF NOT EXISTS payments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_number VARCHAR(50) UNIQUE NOT NULL,
                    customer_id INTEGER NOT NULL,
                    payment_method_id INTEGER NOT NULL,
                    
                    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    amount DECIMAL(15,4) NOT NULL,
                    
                    currency_id INTEGER DEFAULT 1,
                    exchange_rate DECIMAL(15,6) DEFAULT 1,
                    
                    reference_number VARCHAR(100), -- Número de cheque, autorización, etc.
                    bank_name VARCHAR(100),
                    account_number VARCHAR(50),
                    
                    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, APPROVED, REJECTED, CANCELLED
                    
                    notes TEXT,
                    
                    received_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    approved_by INTEGER,
                    approved_at TIMESTAMP,
                    
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id),
                    FOREIGN KEY (currency_id) REFERENCES currencies(id),
                    FOREIGN KEY (received_by) REFERENCES users(id),
                    FOREIGN KEY (approved_by) REFERENCES users(id)
                )
            ''',
            
            'payment_allocations': '''
                CREATE TABLE IF NOT EXISTS payment_allocations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    payment_id INTEGER NOT NULL,
                    account_movement_id INTEGER NOT NULL,
                    allocated_amount DECIMAL(15,4) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (payment_id) REFERENCES payments(id),
                    FOREIGN KEY (account_movement_id) REFERENCES account_movements(id)
                )
            ''',
        }
        
        # ==================== CAJAS Y TURNOS ====================
        
        cash_tables = {
            'cash_sessions': '''
                CREATE TABLE IF NOT EXISTS cash_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_number VARCHAR(50) UNIQUE NOT NULL,
                    cash_register_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    
                    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    closed_at TIMESTAMP,
                    
                    opening_balance DECIMAL(15,4) DEFAULT 0,
                    closing_balance DECIMAL(15,4) DEFAULT 0,
                    expected_balance DECIMAL(15,4) DEFAULT 0,
                    difference DECIMAL(15,4) GENERATED ALWAYS AS (closing_balance - expected_balance) STORED,
                    
                    total_sales DECIMAL(15,4) DEFAULT 0,
                    total_payments DECIMAL(15,4) DEFAULT 0,
                    total_expenses DECIMAL(15,4) DEFAULT 0,
                    
                    status VARCHAR(20) DEFAULT 'OPEN', -- OPEN, CLOSED, SUSPENDED
                    
                    opening_notes TEXT,
                    closing_notes TEXT,
                    
                    closed_by INTEGER,
                    
                    FOREIGN KEY (cash_register_id) REFERENCES cash_registers(id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (closed_by) REFERENCES users(id)
                )
            ''',
            
            'cash_movements': '''
                CREATE TABLE IF NOT EXISTS cash_movements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cash_session_id INTEGER NOT NULL,
                    movement_type VARCHAR(20) NOT NULL, -- SALE, PAYMENT, EXPENSE, OPENING, CLOSING
                    reference_type VARCHAR(50), -- SALES_ORDER, PAYMENT, EXPENSE, etc.
                    reference_id INTEGER,
                    reference_number VARCHAR(50),
                    
                    amount DECIMAL(15,4) NOT NULL,
                    payment_method_id INTEGER NOT NULL,
                    
                    balance_before DECIMAL(15,4),
                    balance_after DECIMAL(15,4),
                    
                    description TEXT,
                    notes TEXT,
                    
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (cash_session_id) REFERENCES cash_sessions(id),
                    FOREIGN KEY (payment_method_id) REFERENCES payment_methods(id),
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            ''',
            
            'cash_denominations': '''
                CREATE TABLE IF NOT EXISTS cash_denominations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    currency_id INTEGER NOT NULL,
                    denomination_value DECIMAL(10,2) NOT NULL,
                    denomination_type VARCHAR(10) NOT NULL, -- BILL, COIN
                    active BOOLEAN DEFAULT 1,
                    FOREIGN KEY (currency_id) REFERENCES currencies(id)
                )
            ''',
            
            'cash_counts': '''
                CREATE TABLE IF NOT EXISTS cash_counts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cash_session_id INTEGER NOT NULL,
                    count_type VARCHAR(20), -- OPENING, CLOSING, INTERMEDIATE
                    count_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    total_counted DECIMAL(15,4) DEFAULT 0,
                    notes TEXT,
                    counted_by INTEGER NOT NULL,
                    FOREIGN KEY (cash_session_id) REFERENCES cash_sessions(id),
                    FOREIGN KEY (counted_by) REFERENCES users(id)
                )
            ''',
            
            'cash_count_details': '''
                CREATE TABLE IF NOT EXISTS cash_count_details (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cash_count_id INTEGER NOT NULL,
                    denomination_id INTEGER NOT NULL,
                    quantity INTEGER NOT NULL,
                    amount DECIMAL(15,4) GENERATED ALWAYS AS (quantity * (SELECT denomination_value FROM cash_denominations WHERE id = denomination_id)) STORED,
                    FOREIGN KEY (cash_count_id) REFERENCES cash_counts(id) ON DELETE CASCADE,
                    FOREIGN KEY (denomination_id) REFERENCES cash_denominations(id)
                )
            ''',
        }
        
        # ==================== PROMOCIONES Y DESCUENTOS ====================
        
        promotion_tables = {
            'promotion_types': '''
                CREATE TABLE IF NOT EXISTS promotion_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(20) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    active BOOLEAN DEFAULT 1
                )
            ''',
            
            'promotions': '''
                CREATE TABLE IF NOT EXISTS promotions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    promotion_type_id INTEGER NOT NULL,
                    
                    start_date DATE NOT NULL,
                    end_date DATE,
                    start_time TIME,
                    end_time TIME,
                    
                    days_of_week VARCHAR(20), -- MTWTFSS format or JSON
                    
                    discount_type VARCHAR(20), -- PERCENTAGE, FIXED_AMOUNT, BUY_X_GET_Y
                    discount_value DECIMAL(15,4),
                    max_discount_amount DECIMAL(15,4),
                    
                    min_quantity DECIMAL(12,4) DEFAULT 1,
                    max_quantity DECIMAL(12,4),
                    min_amount DECIMAL(15,4),
                    max_amount DECIMAL(15,4),
                    
                    usage_limit INTEGER, -- Límite total de usos
                    usage_count INTEGER DEFAULT 0,
                    customer_usage_limit INTEGER, -- Límite por cliente
                    
                    requires_coupon BOOLEAN DEFAULT 0,
                    coupon_code VARCHAR(50),
                    
                    combinable_with_others BOOLEAN DEFAULT 1,
                    priority INTEGER DEFAULT 1,
                    
                    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, INACTIVE, EXPIRED
                    
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (promotion_type_id) REFERENCES promotion_types(id),
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            ''',
            
            'promotion_products': '''
                CREATE TABLE IF NOT EXISTS promotion_products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    promotion_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    FOREIGN KEY (promotion_id) REFERENCES promotions(id) ON DELETE CASCADE,
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    UNIQUE(promotion_id, product_id)
                )
            ''',
            
            'promotion_categories': '''
                CREATE TABLE IF NOT EXISTS promotion_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    promotion_id INTEGER NOT NULL,
                    category_id INTEGER NOT NULL,
                    FOREIGN KEY (promotion_id) REFERENCES promotions(id) ON DELETE CASCADE,
                    FOREIGN KEY (category_id) REFERENCES product_categories(id),
                    UNIQUE(promotion_id, category_id)
                )
            ''',
            
            'promotion_customers': '''
                CREATE TABLE IF NOT EXISTS promotion_customers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    promotion_id INTEGER NOT NULL,
                    customer_id INTEGER,
                    customer_category_id INTEGER,
                    FOREIGN KEY (promotion_id) REFERENCES promotions(id) ON DELETE CASCADE,
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (customer_category_id) REFERENCES customer_categories(id)
                )
            ''',
            
            'promotion_usage': '''
                CREATE TABLE IF NOT EXISTS promotion_usage (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    promotion_id INTEGER NOT NULL,
                    sales_order_id INTEGER NOT NULL,
                    customer_id INTEGER,
                    discount_amount DECIMAL(15,4) NOT NULL,
                    used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (promotion_id) REFERENCES promotions(id),
                    FOREIGN KEY (sales_order_id) REFERENCES sales_orders(id),
                    FOREIGN KEY (customer_id) REFERENCES customers(id)
                )
            ''',
        }
        
        # ==================== PRODUCCIÓN Y RECETAS ====================
        
        production_tables = {
            'recipes': '''
                CREATE TABLE IF NOT EXISTS recipes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_code VARCHAR(50) UNIQUE NOT NULL,
                    product_id INTEGER NOT NULL, -- Producto que se produce
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    version VARCHAR(20) DEFAULT '1.0',
                    
                    yield_quantity DECIMAL(12,4) NOT NULL, -- Cantidad que produce
                    yield_unit_id INTEGER NOT NULL,
                    
                    preparation_time_minutes INTEGER,
                    cooking_time_minutes INTEGER,
                    total_time_minutes INTEGER,
                    
                    difficulty_level INTEGER DEFAULT 1, -- 1-5
                    
                    instructions TEXT,
                    notes TEXT,
                    
                    cost_per_unit DECIMAL(15,4) DEFAULT 0,
                    
                    status VARCHAR(20) DEFAULT 'ACTIVE', -- ACTIVE, INACTIVE, DRAFT
                    
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_by INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (product_id) REFERENCES products(id),
                    FOREIGN KEY (yield_unit_id) REFERENCES units_of_measure(id),
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (updated_by) REFERENCES users(id)
                )
            ''',
            
            'recipe_ingredients': '''
                CREATE TABLE IF NOT EXISTS recipe_ingredients (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    recipe_id INTEGER NOT NULL,
                    ingredient_product_id INTEGER NOT NULL,
                    quantity DECIMAL(12,4) NOT NULL,
                    unit_id INTEGER NOT NULL,
                    cost_per_unit DECIMAL(15,4) DEFAULT 0,
                    total_cost DECIMAL(15,4) GENERATED ALWAYS AS (quantity * cost_per_unit) STORED,
                    is_critical BOOLEAN DEFAULT 0, -- Si es ingrediente crítico
                    notes TEXT,
                    sort_order INTEGER DEFAULT 0,
                    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
                    FOREIGN KEY (ingredient_product_id) REFERENCES products(id),
                    FOREIGN KEY (unit_id) REFERENCES units_of_measure(id)
                )
            ''',
            
            'production_orders': '''
                CREATE TABLE IF NOT EXISTS production_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number VARCHAR(50) UNIQUE NOT NULL,
                    recipe_id INTEGER NOT NULL,
                    warehouse_id INTEGER NOT NULL,
                    
                    planned_start_date DATE,
                    planned_end_date DATE,
                    actual_start_date TIMESTAMP,
                    actual_end_date TIMESTAMP,
                    
                    planned_quantity DECIMAL(12,4) NOT NULL,
                    produced_quantity DECIMAL(12,4) DEFAULT 0,
                    
                    status VARCHAR(20) DEFAULT 'PLANNED', -- PLANNED, IN_PROGRESS, COMPLETED, CANCELLED
                    
                    priority INTEGER DEFAULT 3, -- 1-5 (5 es mayor prioridad)
                    
                    notes TEXT,
                    
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_by INTEGER,
                    completed_by INTEGER,
                    
                    FOREIGN KEY (recipe_id) REFERENCES recipes(id),
                    FOREIGN KEY (warehouse_id) REFERENCES warehouses(id),
                    FOREIGN KEY (created_by) REFERENCES users(id),
                    FOREIGN KEY (started_by) REFERENCES users(id),
                    FOREIGN KEY (completed_by) REFERENCES users(id)
                )
            ''',
            
            'production_consumption': '''
                CREATE TABLE IF NOT EXISTS production_consumption (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    production_order_id INTEGER NOT NULL,
                    ingredient_product_id INTEGER NOT NULL,
                    planned_quantity DECIMAL(12,4) NOT NULL,
                    consumed_quantity DECIMAL(12,4) DEFAULT 0,
                    waste_quantity DECIMAL(12,4) DEFAULT 0,
                    lot_number VARCHAR(50),
                    notes TEXT,
                    FOREIGN KEY (production_order_id) REFERENCES production_orders(id),
                    FOREIGN KEY (ingredient_product_id) REFERENCES products(id)
                )
            ''',
        }
        
        # ==================== SERVICIOS Y TRABAJO ====================
        
        service_tables = {
            'service_categories': '''
                CREATE TABLE IF NOT EXISTS service_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    hourly_rate DECIMAL(15,4) DEFAULT 0,
                    active BOOLEAN DEFAULT 1
                )
            ''',
            
            'services': '''
                CREATE TABLE IF NOT EXISTS services (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_code VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    category_id INTEGER,
                    
                    service_type VARCHAR(20) DEFAULT 'HOURLY', -- HOURLY, FIXED, PER_UNIT
                    
                    base_price DECIMAL(15,4) NOT NULL,
                    hourly_rate DECIMAL(15,4),
                    estimated_duration_hours DECIMAL(6,2),
                    
                    requires_appointment BOOLEAN DEFAULT 0,
                    active BOOLEAN DEFAULT 1,
                    
                    FOREIGN KEY (category_id) REFERENCES service_categories(id)
                )
            ''',
            
            'service_orders': '''
                CREATE TABLE IF NOT EXISTS service_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    order_number VARCHAR(50) UNIQUE NOT NULL,
                    customer_id INTEGER NOT NULL,
                    service_id INTEGER NOT NULL,
                    
                    scheduled_date TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    
                    estimated_hours DECIMAL(6,2),
                    actual_hours DECIMAL(6,2),
                    
                    hourly_rate DECIMAL(15,4),
                    fixed_price DECIMAL(15,4),
                    total_amount DECIMAL(15,4),
                    
                    status VARCHAR(20) DEFAULT 'SCHEDULED', -- SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
                    
                    technician_id INTEGER,
                    notes TEXT,
                    customer_notes TEXT,
                    
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (customer_id) REFERENCES customers(id),
                    FOREIGN KEY (service_id) REFERENCES services(id),
                    FOREIGN KEY (technician_id) REFERENCES users(id),
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            ''',
            
            'work_sessions': '''
                CREATE TABLE IF NOT EXISTS work_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service_order_id INTEGER NOT NULL,
                    technician_id INTEGER NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ended_at TIMESTAMP,
                    hours_worked DECIMAL(6,2),
                    hourly_rate DECIMAL(15,4),
                    session_cost DECIMAL(15,4),
                    notes TEXT,
                    FOREIGN KEY (service_order_id) REFERENCES service_orders(id),
                    FOREIGN KEY (technician_id) REFERENCES users(id)
                )
            ''',
        }
        
        # ==================== REPORTES Y ANÁLISIS ====================
        
        analytics_tables = {
            'saved_reports': '''
                CREATE TABLE IF NOT EXISTS saved_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    report_type VARCHAR(50), -- SALES, INVENTORY, FINANCIAL, etc.
                    query_text TEXT,
                    parameters TEXT, -- JSON con parámetros
                    is_scheduled BOOLEAN DEFAULT 0,
                    schedule_frequency VARCHAR(20), -- DAILY, WEEKLY, MONTHLY
                    schedule_day_of_month INTEGER,
                    schedule_day_of_week INTEGER,
                    schedule_time TIME,
                    last_run_at TIMESTAMP,
                    created_by INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            ''',
            
            'kpi_definitions': '''
                CREATE TABLE IF NOT EXISTS kpi_definitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(200) NOT NULL,
                    description TEXT,
                    formula TEXT, -- SQL o fórmula de cálculo
                    unit VARCHAR(20), -- %, $, units, etc.
                    target_value DECIMAL(15,4),
                    warning_threshold DECIMAL(15,4),
                    critical_threshold DECIMAL(15,4),
                    active BOOLEAN DEFAULT 1
                )
            ''',
            
            'kpi_values': '''
                CREATE TABLE IF NOT EXISTS kpi_values (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kpi_definition_id INTEGER NOT NULL,
                    calculation_date DATE NOT NULL,
                    value DECIMAL(15,4) NOT NULL,
                    location_id INTEGER,
                    user_id INTEGER,
                    calculated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (kpi_definition_id) REFERENCES kpi_definitions(id),
                    FOREIGN KEY (location_id) REFERENCES locations(id),
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    UNIQUE(kpi_definition_id, calculation_date, location_id, user_id)
                )
            ''',
        }
        
        # ==================== AUDITORÍA Y LOGS ====================
        
        audit_tables = {
            'audit_log': '''
                CREATE TABLE IF NOT EXISTS audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name VARCHAR(50) NOT NULL,
                    record_id INTEGER,
                    operation VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
                    old_values TEXT, -- JSON con valores anteriores
                    new_values TEXT, -- JSON con valores nuevos
                    user_id INTEGER,
                    ip_address VARCHAR(45),
                    user_agent TEXT,
                    session_id VARCHAR(255),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''',
            
            'system_logs': '''
                CREATE TABLE IF NOT EXISTS system_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    log_level VARCHAR(10), -- DEBUG, INFO, WARNING, ERROR, CRITICAL
                    module VARCHAR(100),
                    message TEXT NOT NULL,
                    exception_type VARCHAR(100),
                    stack_trace TEXT,
                    user_id INTEGER,
                    session_id VARCHAR(255),
                    ip_address VARCHAR(45),
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''',
            
            'data_sync_log': '''
                CREATE TABLE IF NOT EXISTS data_sync_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sync_type VARCHAR(50), -- CLOUD_BACKUP, BRANCH_SYNC, API_SYNC
                    direction VARCHAR(20), -- UPLOAD, DOWNLOAD, BIDIRECTIONAL
                    table_name VARCHAR(50),
                    record_count INTEGER,
                    status VARCHAR(20), -- SUCCESS, FAILED, PARTIAL
                    error_message TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    duration_seconds INTEGER,
                    user_id INTEGER,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''',
        }
        
        # ==================== NOTIFICACIONES ====================
        
        notification_tables = {
            'notification_types': '''
                CREATE TABLE IF NOT EXISTS notification_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code VARCHAR(50) UNIQUE NOT NULL,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    icon VARCHAR(50),
                    color VARCHAR(7),
                    default_enabled BOOLEAN DEFAULT 1,
                    priority INTEGER DEFAULT 3, -- 1-5
                    active BOOLEAN DEFAULT 1
                )
            ''',
            
            'notifications': '''
                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    notification_type_id INTEGER NOT NULL,
                    user_id INTEGER, -- NULL = notificación global
                    title VARCHAR(200) NOT NULL,
                    message TEXT,
                    action_url VARCHAR(500), -- URL para acción
                    action_text VARCHAR(100), -- Texto del botón de acción
                    
                    priority INTEGER DEFAULT 3, -- 1-5
                    
                    read BOOLEAN DEFAULT 0,
                    read_at TIMESTAMP,
                    
                    expires_at TIMESTAMP,
                    
                    metadata TEXT, -- JSON con datos adicionales
                    
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    FOREIGN KEY (notification_type_id) REFERENCES notification_types(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            ''',
            
            'user_notification_preferences': '''
                CREATE TABLE IF NOT EXISTS user_notification_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    notification_type_id INTEGER NOT NULL,
                    enabled BOOLEAN DEFAULT 1,
                    email_enabled BOOLEAN DEFAULT 0,
                    sms_enabled BOOLEAN DEFAULT 0,
                    push_enabled BOOLEAN DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (notification_type_id) REFERENCES notification_types(id),
                    UNIQUE(user_id, notification_type_id)
                )
            ''',
        }
        
        # Ejecutar creación de todas las tablas
        all_tables = {
            **system_tables,
            **user_tables,
            **organization_tables,
            **product_tables,
            **inventory_tables,
            **supplier_tables,
            **customer_tables,
            **account_tables,
            **cash_tables,
            **promotion_tables,
            **production_tables,
            **service_tables,
            **analytics_tables,
            **audit_tables,
            **notification_tables
        }
        
        with self.connection:
            cursor = self.connection.cursor()
            for trigger_sql in triggers:
                try:
                    cursor.execute(trigger_sql)
                except Exception as e:
                    logger.error(f"Error creando trigger: {e}")
    
    def create_all_views(self):
        """Crear vistas para consultas complejas frecuentes"""
        
        views = [
            # Vista de productos con información completa
            '''
            CREATE VIEW IF NOT EXISTS v_products_complete AS
            SELECT 
                p.id,
                p.sku,
                p.barcode,
                p.internal_code,
                p.name,
                p.description,
                p.product_type,
                p.cost_price,
                p.sale_price,
                p.wholesale_price,
                p.current_stock,
                p.minimum_stock,
                p.maximum_stock,
                p.is_active,
                c.name as category_name,
                b.name as brand_name,
                u.name as unit_name,
                u.symbol as unit_symbol,
                s.legal_name as supplier_name,
                tr.rate as tax_rate,
                CASE 
                    WHEN p.current_stock <= 0 THEN 'OUT_OF_STOCK'
                    WHEN p.current_stock <= p.minimum_stock THEN 'LOW_STOCK'
                    WHEN p.current_stock >= p.maximum_stock THEN 'OVERSTOCK'
                    ELSE 'NORMAL'
                END as stock_status,
                (p.sale_price - p.cost_price) as gross_profit,
                CASE 
                    WHEN p.cost_price > 0 THEN ((p.sale_price - p.cost_price) / p.cost_price * 100)
                    ELSE 0
                END as margin_percentage
            FROM products p
            LEFT JOIN product_categories c ON p.category_id = c.id
            LEFT JOIN brands b ON p.brand_id = b.id
            LEFT JOIN units_of_measure u ON p.primary_unit_id = u.id
            LEFT JOIN suppliers s ON p.primary_supplier_id = s.id
            LEFT JOIN tax_rates tr ON p.tax_rate_id = tr.id
            ''',
            
            # Vista de ventas con información completa
            '''
            CREATE VIEW IF NOT EXISTS v_sales_complete AS
            SELECT 
                so.id,
                so.order_number,
                so.order_date,
                so.order_type,
                so.status,
                so.subtotal,
                so.discount_amount,
                so.tax_amount,
                so.total_amount,
                so.payment_method,
                c.full_name as customer_name,
                c.tax_id as customer_tax_id,
                u.full_name as cashier_name,
                cr.name as cash_register_name,
                l.name as location_name,
                COUNT(sod.id) as item_count,
                SUM(sod.quantity) as total_quantity
            FROM sales_orders so
            LEFT JOIN customers c ON so.customer_id = c.id
            LEFT JOIN users u ON so.created_by = u.id
            LEFT JOIN cash_registers cr ON so.cash_register_id = cr.id
            LEFT JOIN locations l ON cr.location_id = l.id
            LEFT JOIN sales_order_details sod ON so.id = sod.sales_order_id
            GROUP BY so.id, so.order_number, so.order_date, so.order_type, so.status, 
                     so.subtotal, so.discount_amount, so.tax_amount, so.total_amount, 
                     so.payment_method, c.full_name, c.tax_id, u.full_name, 
                     cr.name, l.name
            ''',
            
            # Vista de cuentas corrientes con balance
            '''
            CREATE VIEW IF NOT EXISTS v_customer_accounts_balance AS
            SELECT 
                ca.id,
                ca.customer_id,
                c.full_name as customer_name,
                c.tax_id as customer_tax_id,
                ca.current_balance,
                ca.credit_limit,
                ca.available_credit,
                ca.last_payment_date,
                ca.last_charge_date,
                COUNT(am.id) as total_movements,
                SUM(CASE WHEN am.movement_type = 'CHARGE' THEN am.amount ELSE 0 END) as total_charges,
                SUM(CASE WHEN am.movement_type = 'PAYMENT' THEN am.amount ELSE 0 END) as total_payments,
                SUM(CASE WHEN am.movement_type = 'CHARGE' AND am.due_date < DATE('now') THEN am.amount ELSE 0 END) as overdue_amount,
                COUNT(CASE WHEN am.movement_type = 'CHARGE' AND am.due_date < DATE('now') THEN 1 END) as overdue_invoices
            FROM customer_accounts ca
            JOIN customers c ON ca.customer_id = c.id
            LEFT JOIN account_movements am ON ca.id = am.customer_account_id
            GROUP BY ca.id, ca.customer_id, c.full_name, c.tax_id, ca.current_balance, 
                     ca.credit_limit, ca.available_credit, ca.last_payment_date, ca.last_charge_date
            ''',
            
            # Vista resumen de stock por ubicación
            '''
            CREATE VIEW IF NOT EXISTS v_stock_by_location_summary AS
            SELECT 
                sbl.product_id,
                p.name as product_name,
                p.sku,
                p.barcode,
                sbl.warehouse_id,
                w.name as warehouse_name,
                SUM(sbl.current_stock) as total_stock,
                SUM(sbl.reserved_stock) as total_reserved,
                SUM(sbl.available_stock) as total_available,
                COUNT(CASE WHEN sbl.expiration_date IS NOT NULL AND sbl.expiration_date <= DATE('now', '+30 days') THEN 1 END) as expiring_soon_count,
                MIN(sbl.expiration_date) as earliest_expiration,
                COUNT(DISTINCT sbl.lot_number) as lot_count
            FROM stock_by_location sbl
            JOIN products p ON sbl.product_id = p.id
            JOIN warehouses w ON sbl.warehouse_id = w.id
            WHERE sbl.current_stock > 0
            GROUP BY sbl.product_id, p.name, p.sku, p.barcode, sbl.warehouse_id, w.name
            ''',
            
            # Vista de top productos vendidos
            '''
            CREATE VIEW IF NOT EXISTS v_top_selling_products AS
            SELECT 
                p.id as product_id,
                p.name as product_name,
                p.sku,
                p.barcode,
                c.name as category_name,
                SUM(sod.quantity) as total_quantity_sold,
                SUM(sod.line_total) as total_revenue,
                COUNT(DISTINCT so.id) as transaction_count,
                AVG(sod.unit_price) as average_price,
                MAX(so.order_date) as last_sold_date,
                (SUM(sod.line_total) - SUM(sod.quantity * p.cost_price)) as total_profit
            FROM sales_order_details sod
            JOIN products p ON sod.product_id = p.id
            JOIN sales_orders so ON sod.sales_order_id = so.id
            LEFT JOIN product_categories c ON p.category_id = c.id
            WHERE so.status IN ('COMPLETED', 'DELIVERED')
            GROUP BY p.id, p.name, p.sku, p.barcode, c.name
            ''',
            
            # Vista de métricas de ventas por período
            '''
            CREATE VIEW IF NOT EXISTS v_sales_metrics_daily AS
            SELECT 
                DATE(so.order_date) as sale_date,
                COUNT(so.id) as transaction_count,
                SUM(so.total_amount) as total_revenue,
                AVG(so.total_amount) as average_transaction,
                SUM(sod.quantity) as total_items_sold,
                COUNT(DISTINCT so.customer_id) as unique_customers,
                COUNT(DISTINCT so.created_by) as active_cashiers,
                MAX(so.total_amount) as highest_transaction,
                MIN(so.total_amount) as lowest_transaction
            FROM sales_orders so
            LEFT JOIN sales_order_details sod ON so.id = sod.sales_order_id
            WHERE so.status IN ('COMPLETED', 'DELIVERED')
            GROUP BY DATE(so.order_date)
            ''',
            
            # Vista de proveedores con estadísticas
            '''
            CREATE VIEW IF NOT EXISTS v_supplier_statistics AS
            SELECT 
                s.id,
                s.supplier_code,
                s.legal_name,
                s.contact_person,
                s.phone,
                s.email,
                s.rating,
                s.status,
                COUNT(DISTINCT sp.product_id) as products_supplied,
                COUNT(DISTINCT po.id) as total_orders,
                SUM(po.total_amount) as total_purchased,
                AVG(po.total_amount) as average_order_value,
                MAX(po.order_date) as last_order_date,
                AVG(JULIANDAY(po.actual_delivery_date) - JULIANDAY(po.expected_delivery_date)) as avg_delivery_delay,
                COUNT(CASE WHEN po.status = 'RECEIVED' THEN 1 END) as completed_orders,
                COUNT(CASE WHEN po.status IN ('PENDING', 'CONFIRMED') THEN 1 END) as pending_orders
            FROM suppliers s
            LEFT JOIN supplier_products sp ON s.id = sp.supplier_id
            LEFT JOIN purchase_orders po ON s.id = po.supplier_id
            GROUP BY s.id, s.supplier_code, s.legal_name, s.contact_person, s.phone, s.email, s.rating, s.status
            ''',
            
            # Vista de alertas de stock
            '''
            CREATE VIEW IF NOT EXISTS v_stock_alerts AS
            SELECT 
                p.id as product_id,
                p.name as product_name,
                p.sku,
                p.barcode,
                p.current_stock,
                p.minimum_stock,
                p.maximum_stock,
                c.name as category_name,
                s.legal_name as supplier_name,
                CASE 
                    WHEN p.current_stock <= 0 THEN 'OUT_OF_STOCK'
                    WHEN p.current_stock <= p.minimum_stock THEN 'LOW_STOCK'
                    WHEN p.current_stock >= p.maximum_stock THEN 'OVERSTOCK'
                END as alert_type,
                CASE 
                    WHEN p.current_stock <= 0 THEN 5
                    WHEN p.current_stock <= p.minimum_stock THEN 4
                    WHEN p.current_stock >= p.maximum_stock THEN 2
                    ELSE 1
                END as priority,
                p.reorder_point,
                p.reorder_quantity,
                (p.minimum_stock - p.current_stock) as quantity_needed
            FROM products p
            LEFT JOIN product_categories c ON p.category_id = c.id
            LEFT JOIN suppliers s ON p.primary_supplier_id = s.id
            WHERE p.is_active = 1 
            AND p.track_stock = 1 
            AND (p.current_stock <= 0 OR p.current_stock <= p.minimum_stock OR p.current_stock >= p.maximum_stock)
            ''',
            
            # Vista de productos próximos a vencer
            '''
            CREATE VIEW IF NOT EXISTS v_expiring_products AS
            SELECT 
                sbl.product_id,
                p.name as product_name,
                p.sku,
                p.barcode,
                sbl.lot_number,
                sbl.expiration_date,
                sbl.current_stock,
                w.name as warehouse_name,
                sl.location_code,
                JULIANDAY(sbl.expiration_date) - JULIANDAY('now') as days_to_expiry,
                CASE 
                    WHEN sbl.expiration_date <= DATE('now') THEN 'EXPIRED'
                    WHEN sbl.expiration_date <= DATE('now', '+7 days') THEN 'EXPIRES_THIS_WEEK'
                    WHEN sbl.expiration_date <= DATE('now', '+30 days') THEN 'EXPIRES_THIS_MONTH'
                    ELSE 'NORMAL'
                END as expiry_status,
                (sbl.current_stock * p.cost_price) as inventory_value_at_risk
            FROM stock_by_location sbl
            JOIN products p ON sbl.product_id = p.id
            JOIN warehouses w ON sbl.warehouse_id = w.id
            LEFT JOIN storage_locations sl ON sbl.storage_location_id = sl.id
            WHERE sbl.expiration_date IS NOT NULL 
            AND sbl.current_stock > 0
            AND sbl.expiration_date <= DATE('now', '+90 days')
            ORDER BY sbl.expiration_date ASC
            ''',
        ]
        
        with self.connection:
            cursor = self.connection.cursor()
            for view_sql in views:
                try:
                    cursor.execute(view_sql)
                except Exception as e:
                    logger.error(f"Error creando vista: {e}")
    
    def insert_initial_data(self):
        """Insertar datos iniciales y de configuración"""
        
        with self.connection:
            cursor = self.connection.cursor()
            
            # Países
            countries_data = [
                ('ARG', 'Argentina', 'ARS', 'IVA'),
                ('URY', 'Uruguay', 'UYU', 'IVA'),
                ('BRA', 'Brasil', 'BRL', 'IVA'),
                ('CHL', 'Chile', 'CLP', 'IVA'),
                ('USA', 'Estados Unidos', 'USD', 'GST'),
                ('ESP', 'España', 'EUR', 'IVA'),
            ]
            
            for code, name, currency, tax_system in countries_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO countries (code, name, currency_code, tax_system) 
                        VALUES (?, ?, ?, ?)
                    """, (code, name, currency, tax_system))
                except Exception as e:
                    logger.error(f"Error insertando país {name}: {e}")
            
            # Provincias argentinas (ejemplo)
            argentina_provinces = [
                (1, 'CABA', 'Ciudad Autónoma de Buenos Aires'),
                (1, 'BA', 'Buenos Aires'),
                (1, 'CAT', 'Catamarca'),
                (1, 'CHA', 'Chaco'),
                (1, 'CHU', 'Chubut'),
                (1, 'COR', 'Córdoba'),
                (1, 'COR', 'Corrientes'),
                (1, 'ER', 'Entre Ríos'),
                (1, 'FOR', 'Formosa'),
                (1, 'JUJ', 'Jujuy'),
                (1, 'LP', 'La Pampa'),
                (1, 'LR', 'La Rioja'),
                (1, 'MEN', 'Mendoza'),
                (1, 'MIS', 'Misiones'),
                (1, 'NEU', 'Neuquén'),
                (1, 'RN', 'Río Negro'),
                (1, 'SAL', 'Salta'),
                (1, 'SJ', 'San Juan'),
                (1, 'SL', 'San Luis'),
                (1, 'SC', 'Santa Cruz'),
                (1, 'SF', 'Santa Fe'),
                (1, 'SDE', 'Santiago del Estero'),
                (1, 'TF', 'Tierra del Fuego'),
                (1, 'TUC', 'Tucumán'),
            ]
            
            for country_id, code, name in argentina_provinces:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO states_provinces (country_id, code, name) 
                        VALUES (?, ?, ?)
                    """, (country_id, code, name))
                except Exception as e:
                    logger.error(f"Error insertando provincia {name}: {e}")
            
            # Monedas
            currencies_data = [
                ('ARS', 'Peso Argentino', 'cursor()
            for table_name, sql in all_tables.items():
                try:
                    cursor.execute(sql)
                    logger.info(f"Tabla {table_name} creada/verificada")
                except Exception as e:
                    logger.error(f"Error creando tabla {table_name}: {e}")
                    raise
    
    def create_all_indexes(self):
        """Crear todos los índices para optimización"""
        
        indexes = [
            # Índices para búsquedas comunes en productos
            "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)",
            "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)",
            "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)",
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock ON products(current_stock)",
            "CREATE INDEX IF NOT EXISTS idx_products_type ON products(product_type)",
            
            # Índices para customers
            "CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(customer_code)",
            "CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(first_name, last_name)",
            "CREATE INDEX IF NOT EXISTS idx_customers_tax_id ON customers(tax_id)",
            "CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email)",
            "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)",
            "CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status)",
            "CREATE INDEX IF NOT EXISTS idx_customers_category ON customers(customer_category_id)",
            
            # Índices para suppliers
            "CREATE INDEX IF NOT EXISTS idx_suppliers_code ON suppliers(supplier_code)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(legal_name)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_tax_id ON suppliers(tax_id)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_status ON suppliers(status)",
            
            # Índices para sales_orders
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_number ON sales_orders(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_date ON sales_orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_customer ON sales_orders(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_status ON sales_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_cashier ON sales_orders(created_by)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_register ON sales_orders(cash_register_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_type ON sales_orders(order_type)",
            
            # Índices para sales_order_details
            "CREATE INDEX IF NOT EXISTS idx_sales_order_details_order ON sales_order_details(sales_order_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_order_details_product ON sales_order_details(product_id)",
            
            # Índices para purchase_orders
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_number ON purchase_orders(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date ON purchase_orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status)",
            
            # Índices para stock_movements
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_warehouse ON stock_movements(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_reference ON stock_movements(reference_type, reference_id)",
            
            # Índices para stock_by_location
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_product ON stock_by_location(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_warehouse ON stock_by_location(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_lot ON stock_by_location(lot_number)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_expiration ON stock_by_location(expiration_date)",
            
            # Índices para account_movements
            "CREATE INDEX IF NOT EXISTS idx_account_movements_customer ON account_movements(customer_account_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_date ON account_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_type ON account_movements(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_due_date ON account_movements(due_date)",
            
            # Índices para cash_sessions
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_register ON cash_sessions(cash_register_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_user ON cash_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_date ON cash_sessions(opened_at)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_status ON cash_sessions(status)",
            
            # Índices para cash_movements
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_session ON cash_movements(cash_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_date ON cash_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_type ON cash_movements(movement_type)",
            
            # Índices para users y sesiones
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(active)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(active)",
            
            # Índices para promotions
            "CREATE INDEX IF NOT EXISTS idx_promotions_code ON promotions(code)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_dates ON promotions(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_status ON promotions(status)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_coupon ON promotions(coupon_code)",
            
            # Índices para recipes y production
            "CREATE INDEX IF NOT EXISTS idx_recipes_product ON recipes(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_recipes_status ON recipes(status)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_recipe ON production_orders(recipe_id)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_status ON production_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_dates ON production_orders(planned_start_date, planned_end_date)",
            
            # Índices para notifications
            "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_expires ON notifications(expires_at)",
            
            # Índices para audit_log
            "CREATE INDEX IF NOT EXISTS idx_audit_log_table ON audit_log(table_name)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_record ON audit_log(table_name, record_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation)",
            
            # Índices para system_logs
            "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(log_level)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_user ON system_logs(user_id)",
            
            # Índices compuestos importantes
            "CREATE INDEX IF NOT EXISTS idx_products_category_active ON products(category_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock_status ON products(current_stock, minimum_stock) WHERE track_stock = 1",
            "CREATE INDEX IF NOT EXISTS idx_sales_customer_date ON sales_orders(customer_id, order_date)",
            "CREATE INDEX IF NOT EXISTS idx_stock_product_warehouse ON stock_by_location(product_id, warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_customer_type ON account_movements(customer_account_id, movement_type)",
            
            # Índices para fechas comunes en reportes
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_date_status ON sales_orders(order_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date_status ON purchase_orders(order_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_date_method ON payments(payment_date, payment_method_id)",
            
            # Índices para códigos y números únicos
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku_unique ON products(sku) WHERE sku IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode_unique ON products(barcode) WHERE barcode IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_code_unique ON customers(customer_code) WHERE customer_code IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_suppliers_code_unique ON suppliers(supplier_code) WHERE supplier_code IS NOT NULL",
        ]
        
        with self.connection:
            cursor = self.connection.cursor()
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.error(f"Error creando índice: {e}")
    
    def create_all_triggers(self):
        """Crear triggers para automatización y integridad"""
        
        triggers = [
            # Trigger para actualizar timestamps
            '''
            CREATE TRIGGER IF NOT EXISTS update_products_timestamp 
            AFTER UPDATE ON products
            BEGIN
                UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_customers_timestamp 
            AFTER UPDATE ON customers
            BEGIN
                UPDATE customers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_suppliers_timestamp 
            AFTER UPDATE ON suppliers
            BEGIN
                UPDATE suppliers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            # Trigger para auditoría automática
            '''
            CREATE TRIGGER IF NOT EXISTS audit_products_insert 
            AFTER INSERT ON products
            BEGIN
                INSERT INTO audit_log (table_name, record_id, operation, new_values, user_id, timestamp)
                VALUES ('products', NEW.id, 'INSERT', 
                       json_object('name', NEW.name, 'sku', NEW.sku, 'sale_price', NEW.sale_price),
                       NEW.created_by, CURRENT_TIMESTAMP);
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS audit_products_update 
            AFTER UPDATE ON products
            BEGIN
                INSERT INTO audit_log (table_name, record_id, operation, old_values, new_values, user_id, timestamp)
                VALUES ('products', NEW.id, 'UPDATE',
                       json_object('name', OLD.name, 'sku', OLD.sku, 'sale_price', OLD.sale_price),
                       json_object('name', NEW.name, 'sku', NEW.sku, 'sale_price', NEW.sale_price),
                       NEW.updated_by, CURRENT_TIMESTAMP);
            END
            ''',
            
            # Trigger para mantener balance de cuentas corrientes
            '''
            CREATE TRIGGER IF NOT EXISTS update_customer_balance_insert
            AFTER INSERT ON account_movements
            BEGIN
                UPDATE customer_accounts 
                SET current_balance = current_balance + 
                    CASE WHEN NEW.movement_type = 'CHARGE' THEN NEW.amount ELSE -NEW.amount END,
                    last_charge_date = CASE WHEN NEW.movement_type = 'CHARGE' THEN DATE('now') ELSE last_charge_date END,
                    last_payment_date = CASE WHEN NEW.movement_type = 'PAYMENT' THEN DATE('now') ELSE last_payment_date END
                WHERE id = NEW.customer_account_id;
            END
            ''',
            
            # Trigger para actualizar stock cuando se mueve inventario
            '''
            CREATE TRIGGER IF NOT EXISTS update_stock_on_movement
            AFTER INSERT ON stock_movements
            BEGIN
                -- Actualizar stock del producto principal
                UPDATE products 
                SET current_stock = current_stock + 
                    CASE WHEN NEW.movement_type = 'IN' THEN NEW.quantity_moved 
                         ELSE -NEW.quantity_moved END
                WHERE id = NEW.product_id AND track_stock = 1;
                
                -- Actualizar stock por ubicación
                INSERT OR REPLACE INTO stock_by_location 
                (product_id, warehouse_id, storage_location_id, current_stock, lot_number, serial_number, expiration_date, last_movement_date)
                VALUES (
                    NEW.product_id, 
                    NEW.warehouse_id,
                    NEW.storage_location_id,
                    COALESCE((SELECT current_stock FROM stock_by_location 
                             WHERE product_id = NEW.product_id 
                             AND warehouse_id = NEW.warehouse_id 
                             AND COALESCE(storage_location_id, 0) = COALESCE(NEW.storage_location_id, 0)
                             AND COALESCE(lot_number, '') = COALESCE(NEW.lot_number, '')
                             AND COALESCE(serial_number, '') = COALESCE(NEW.serial_number, '')), 0) +
                    CASE WHEN NEW.movement_type = 'IN' THEN NEW.quantity_moved 
                         ELSE -NEW.quantity_moved END,
                    NEW.lot_number,
                    NEW.serial_number,
                    NEW.expiration_date,
                    CURRENT_TIMESTAMP
                );
            END
            ''',
            
            # Trigger para calcular totales de órdenes
            '''
            CREATE TRIGGER IF NOT EXISTS update_sales_order_total
            AFTER INSERT ON sales_order_details
            BEGIN
                UPDATE sales_orders 
                SET subtotal = (SELECT SUM(line_total) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    tax_amount = (SELECT SUM(tax_amount) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    total_amount = subtotal - discount_amount + tax_amount
                WHERE id = NEW.sales_order_id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_sales_order_total_on_update
            AFTER UPDATE ON sales_order_details
            BEGIN
                UPDATE sales_orders 
                SET subtotal = (SELECT SUM(line_total) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    tax_amount = (SELECT SUM(tax_amount) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    total_amount = subtotal - discount_amount + tax_amount
                WHERE id = NEW.sales_order_id;
            END
            ''',
            
            # Trigger para actualizar contadores de uso de promociones
            '''
            CREATE TRIGGER IF NOT EXISTS update_promotion_usage
            AFTER INSERT ON promotion_usage
            BEGIN
                UPDATE promotions 
                SET usage_count = usage_count + 1
                WHERE id = NEW.promotion_id;
            END
            ''',
            
            # Trigger para verificar límites de crédito
            '''
            CREATE TRIGGER IF NOT EXISTS check_credit_limit
            BEFORE INSERT ON account_movements
            WHEN NEW.movement_type = 'CHARGE'
            BEGIN
                SELECT CASE 
                    WHEN (SELECT current_balance + NEW.amount FROM customer_accounts WHERE id = NEW.customer_account_id) > 
                         (SELECT credit_limit FROM customer_accounts WHERE id = NEW.customer_account_id)
                    THEN RAISE(ABORT, 'Credit limit exceeded')
                END;
            END
            ''',
        ]
        
        with self.connection:
            cursor = self.connection., 2, True),
                ('USD', 'Dólar Estadounidense', 'UScursor()
            for table_name, sql in all_tables.items():
                try:
                    cursor.execute(sql)
                    logger.info(f"Tabla {table_name} creada/verificada")
                except Exception as e:
                    logger.error(f"Error creando tabla {table_name}: {e}")
                    raise
    
    def create_all_indexes(self):
        """Crear todos los índices para optimización"""
        
        indexes = [
            # Índices para búsquedas comunes en productos
            "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)",
            "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)",
            "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)",
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock ON products(current_stock)",
            "CREATE INDEX IF NOT EXISTS idx_products_type ON products(product_type)",
            
            # Índices para customers
            "CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(customer_code)",
            "CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(first_name, last_name)",
            "CREATE INDEX IF NOT EXISTS idx_customers_tax_id ON customers(tax_id)",
            "CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email)",
            "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)",
            "CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status)",
            "CREATE INDEX IF NOT EXISTS idx_customers_category ON customers(customer_category_id)",
            
            # Índices para suppliers
            "CREATE INDEX IF NOT EXISTS idx_suppliers_code ON suppliers(supplier_code)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(legal_name)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_tax_id ON suppliers(tax_id)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_status ON suppliers(status)",
            
            # Índices para sales_orders
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_number ON sales_orders(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_date ON sales_orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_customer ON sales_orders(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_status ON sales_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_cashier ON sales_orders(created_by)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_register ON sales_orders(cash_register_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_type ON sales_orders(order_type)",
            
            # Índices para sales_order_details
            "CREATE INDEX IF NOT EXISTS idx_sales_order_details_order ON sales_order_details(sales_order_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_order_details_product ON sales_order_details(product_id)",
            
            # Índices para purchase_orders
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_number ON purchase_orders(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date ON purchase_orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status)",
            
            # Índices para stock_movements
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_warehouse ON stock_movements(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_reference ON stock_movements(reference_type, reference_id)",
            
            # Índices para stock_by_location
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_product ON stock_by_location(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_warehouse ON stock_by_location(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_lot ON stock_by_location(lot_number)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_expiration ON stock_by_location(expiration_date)",
            
            # Índices para account_movements
            "CREATE INDEX IF NOT EXISTS idx_account_movements_customer ON account_movements(customer_account_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_date ON account_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_type ON account_movements(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_due_date ON account_movements(due_date)",
            
            # Índices para cash_sessions
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_register ON cash_sessions(cash_register_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_user ON cash_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_date ON cash_sessions(opened_at)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_status ON cash_sessions(status)",
            
            # Índices para cash_movements
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_session ON cash_movements(cash_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_date ON cash_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_type ON cash_movements(movement_type)",
            
            # Índices para users y sesiones
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(active)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(active)",
            
            # Índices para promotions
            "CREATE INDEX IF NOT EXISTS idx_promotions_code ON promotions(code)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_dates ON promotions(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_status ON promotions(status)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_coupon ON promotions(coupon_code)",
            
            # Índices para recipes y production
            "CREATE INDEX IF NOT EXISTS idx_recipes_product ON recipes(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_recipes_status ON recipes(status)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_recipe ON production_orders(recipe_id)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_status ON production_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_dates ON production_orders(planned_start_date, planned_end_date)",
            
            # Índices para notifications
            "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_expires ON notifications(expires_at)",
            
            # Índices para audit_log
            "CREATE INDEX IF NOT EXISTS idx_audit_log_table ON audit_log(table_name)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_record ON audit_log(table_name, record_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation)",
            
            # Índices para system_logs
            "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(log_level)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_user ON system_logs(user_id)",
            
            # Índices compuestos importantes
            "CREATE INDEX IF NOT EXISTS idx_products_category_active ON products(category_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock_status ON products(current_stock, minimum_stock) WHERE track_stock = 1",
            "CREATE INDEX IF NOT EXISTS idx_sales_customer_date ON sales_orders(customer_id, order_date)",
            "CREATE INDEX IF NOT EXISTS idx_stock_product_warehouse ON stock_by_location(product_id, warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_customer_type ON account_movements(customer_account_id, movement_type)",
            
            # Índices para fechas comunes en reportes
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_date_status ON sales_orders(order_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date_status ON purchase_orders(order_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_date_method ON payments(payment_date, payment_method_id)",
            
            # Índices para códigos y números únicos
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku_unique ON products(sku) WHERE sku IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode_unique ON products(barcode) WHERE barcode IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_code_unique ON customers(customer_code) WHERE customer_code IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_suppliers_code_unique ON suppliers(supplier_code) WHERE supplier_code IS NOT NULL",
        ]
        
        with self.connection:
            cursor = self.connection.cursor()
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.error(f"Error creando índice: {e}")
    
    def create_all_triggers(self):
        """Crear triggers para automatización y integridad"""
        
        triggers = [
            # Trigger para actualizar timestamps
            '''
            CREATE TRIGGER IF NOT EXISTS update_products_timestamp 
            AFTER UPDATE ON products
            BEGIN
                UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_customers_timestamp 
            AFTER UPDATE ON customers
            BEGIN
                UPDATE customers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_suppliers_timestamp 
            AFTER UPDATE ON suppliers
            BEGIN
                UPDATE suppliers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            # Trigger para auditoría automática
            '''
            CREATE TRIGGER IF NOT EXISTS audit_products_insert 
            AFTER INSERT ON products
            BEGIN
                INSERT INTO audit_log (table_name, record_id, operation, new_values, user_id, timestamp)
                VALUES ('products', NEW.id, 'INSERT', 
                       json_object('name', NEW.name, 'sku', NEW.sku, 'sale_price', NEW.sale_price),
                       NEW.created_by, CURRENT_TIMESTAMP);
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS audit_products_update 
            AFTER UPDATE ON products
            BEGIN
                INSERT INTO audit_log (table_name, record_id, operation, old_values, new_values, user_id, timestamp)
                VALUES ('products', NEW.id, 'UPDATE',
                       json_object('name', OLD.name, 'sku', OLD.sku, 'sale_price', OLD.sale_price),
                       json_object('name', NEW.name, 'sku', NEW.sku, 'sale_price', NEW.sale_price),
                       NEW.updated_by, CURRENT_TIMESTAMP);
            END
            ''',
            
            # Trigger para mantener balance de cuentas corrientes
            '''
            CREATE TRIGGER IF NOT EXISTS update_customer_balance_insert
            AFTER INSERT ON account_movements
            BEGIN
                UPDATE customer_accounts 
                SET current_balance = current_balance + 
                    CASE WHEN NEW.movement_type = 'CHARGE' THEN NEW.amount ELSE -NEW.amount END,
                    last_charge_date = CASE WHEN NEW.movement_type = 'CHARGE' THEN DATE('now') ELSE last_charge_date END,
                    last_payment_date = CASE WHEN NEW.movement_type = 'PAYMENT' THEN DATE('now') ELSE last_payment_date END
                WHERE id = NEW.customer_account_id;
            END
            ''',
            
            # Trigger para actualizar stock cuando se mueve inventario
            '''
            CREATE TRIGGER IF NOT EXISTS update_stock_on_movement
            AFTER INSERT ON stock_movements
            BEGIN
                -- Actualizar stock del producto principal
                UPDATE products 
                SET current_stock = current_stock + 
                    CASE WHEN NEW.movement_type = 'IN' THEN NEW.quantity_moved 
                         ELSE -NEW.quantity_moved END
                WHERE id = NEW.product_id AND track_stock = 1;
                
                -- Actualizar stock por ubicación
                INSERT OR REPLACE INTO stock_by_location 
                (product_id, warehouse_id, storage_location_id, current_stock, lot_number, serial_number, expiration_date, last_movement_date)
                VALUES (
                    NEW.product_id, 
                    NEW.warehouse_id,
                    NEW.storage_location_id,
                    COALESCE((SELECT current_stock FROM stock_by_location 
                             WHERE product_id = NEW.product_id 
                             AND warehouse_id = NEW.warehouse_id 
                             AND COALESCE(storage_location_id, 0) = COALESCE(NEW.storage_location_id, 0)
                             AND COALESCE(lot_number, '') = COALESCE(NEW.lot_number, '')
                             AND COALESCE(serial_number, '') = COALESCE(NEW.serial_number, '')), 0) +
                    CASE WHEN NEW.movement_type = 'IN' THEN NEW.quantity_moved 
                         ELSE -NEW.quantity_moved END,
                    NEW.lot_number,
                    NEW.serial_number,
                    NEW.expiration_date,
                    CURRENT_TIMESTAMP
                );
            END
            ''',
            
            # Trigger para calcular totales de órdenes
            '''
            CREATE TRIGGER IF NOT EXISTS update_sales_order_total
            AFTER INSERT ON sales_order_details
            BEGIN
                UPDATE sales_orders 
                SET subtotal = (SELECT SUM(line_total) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    tax_amount = (SELECT SUM(tax_amount) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    total_amount = subtotal - discount_amount + tax_amount
                WHERE id = NEW.sales_order_id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_sales_order_total_on_update
            AFTER UPDATE ON sales_order_details
            BEGIN
                UPDATE sales_orders 
                SET subtotal = (SELECT SUM(line_total) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    tax_amount = (SELECT SUM(tax_amount) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    total_amount = subtotal - discount_amount + tax_amount
                WHERE id = NEW.sales_order_id;
            END
            ''',
            
            # Trigger para actualizar contadores de uso de promociones
            '''
            CREATE TRIGGER IF NOT EXISTS update_promotion_usage
            AFTER INSERT ON promotion_usage
            BEGIN
                UPDATE promotions 
                SET usage_count = usage_count + 1
                WHERE id = NEW.promotion_id;
            END
            ''',
            
            # Trigger para verificar límites de crédito
            '''
            CREATE TRIGGER IF NOT EXISTS check_credit_limit
            BEFORE INSERT ON account_movements
            WHEN NEW.movement_type = 'CHARGE'
            BEGIN
                SELECT CASE 
                    WHEN (SELECT current_balance + NEW.amount FROM customer_accounts WHERE id = NEW.customer_account_id) > 
                         (SELECT credit_limit FROM customer_accounts WHERE id = NEW.customer_account_id)
                    THEN RAISE(ABORT, 'Credit limit exceeded')
                END;
            END
            ''',
        ]
        
        with self.connection:
            cursor = self.connection., 2, False),
                ('EUR', 'Euro', '€', 2, False),
                ('BRL', 'Real Brasileño', 'Rcursor()
            for table_name, sql in all_tables.items():
                try:
                    cursor.execute(sql)
                    logger.info(f"Tabla {table_name} creada/verificada")
                except Exception as e:
                    logger.error(f"Error creando tabla {table_name}: {e}")
                    raise
    
    def create_all_indexes(self):
        """Crear todos los índices para optimización"""
        
        indexes = [
            # Índices para búsquedas comunes en productos
            "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)",
            "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)",
            "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)",
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock ON products(current_stock)",
            "CREATE INDEX IF NOT EXISTS idx_products_type ON products(product_type)",
            
            # Índices para customers
            "CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(customer_code)",
            "CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(first_name, last_name)",
            "CREATE INDEX IF NOT EXISTS idx_customers_tax_id ON customers(tax_id)",
            "CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email)",
            "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)",
            "CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status)",
            "CREATE INDEX IF NOT EXISTS idx_customers_category ON customers(customer_category_id)",
            
            # Índices para suppliers
            "CREATE INDEX IF NOT EXISTS idx_suppliers_code ON suppliers(supplier_code)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(legal_name)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_tax_id ON suppliers(tax_id)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_status ON suppliers(status)",
            
            # Índices para sales_orders
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_number ON sales_orders(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_date ON sales_orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_customer ON sales_orders(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_status ON sales_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_cashier ON sales_orders(created_by)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_register ON sales_orders(cash_register_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_type ON sales_orders(order_type)",
            
            # Índices para sales_order_details
            "CREATE INDEX IF NOT EXISTS idx_sales_order_details_order ON sales_order_details(sales_order_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_order_details_product ON sales_order_details(product_id)",
            
            # Índices para purchase_orders
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_number ON purchase_orders(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date ON purchase_orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status)",
            
            # Índices para stock_movements
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_warehouse ON stock_movements(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_reference ON stock_movements(reference_type, reference_id)",
            
            # Índices para stock_by_location
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_product ON stock_by_location(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_warehouse ON stock_by_location(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_lot ON stock_by_location(lot_number)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_expiration ON stock_by_location(expiration_date)",
            
            # Índices para account_movements
            "CREATE INDEX IF NOT EXISTS idx_account_movements_customer ON account_movements(customer_account_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_date ON account_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_type ON account_movements(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_due_date ON account_movements(due_date)",
            
            # Índices para cash_sessions
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_register ON cash_sessions(cash_register_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_user ON cash_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_date ON cash_sessions(opened_at)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_status ON cash_sessions(status)",
            
            # Índices para cash_movements
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_session ON cash_movements(cash_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_date ON cash_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_type ON cash_movements(movement_type)",
            
            # Índices para users y sesiones
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(active)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(active)",
            
            # Índices para promotions
            "CREATE INDEX IF NOT EXISTS idx_promotions_code ON promotions(code)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_dates ON promotions(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_status ON promotions(status)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_coupon ON promotions(coupon_code)",
            
            # Índices para recipes y production
            "CREATE INDEX IF NOT EXISTS idx_recipes_product ON recipes(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_recipes_status ON recipes(status)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_recipe ON production_orders(recipe_id)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_status ON production_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_dates ON production_orders(planned_start_date, planned_end_date)",
            
            # Índices para notifications
            "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_expires ON notifications(expires_at)",
            
            # Índices para audit_log
            "CREATE INDEX IF NOT EXISTS idx_audit_log_table ON audit_log(table_name)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_record ON audit_log(table_name, record_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation)",
            
            # Índices para system_logs
            "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(log_level)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_user ON system_logs(user_id)",
            
            # Índices compuestos importantes
            "CREATE INDEX IF NOT EXISTS idx_products_category_active ON products(category_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock_status ON products(current_stock, minimum_stock) WHERE track_stock = 1",
            "CREATE INDEX IF NOT EXISTS idx_sales_customer_date ON sales_orders(customer_id, order_date)",
            "CREATE INDEX IF NOT EXISTS idx_stock_product_warehouse ON stock_by_location(product_id, warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_customer_type ON account_movements(customer_account_id, movement_type)",
            
            # Índices para fechas comunes en reportes
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_date_status ON sales_orders(order_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date_status ON purchase_orders(order_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_date_method ON payments(payment_date, payment_method_id)",
            
            # Índices para códigos y números únicos
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku_unique ON products(sku) WHERE sku IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode_unique ON products(barcode) WHERE barcode IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_code_unique ON customers(customer_code) WHERE customer_code IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_suppliers_code_unique ON suppliers(supplier_code) WHERE supplier_code IS NOT NULL",
        ]
        
        with self.connection:
            cursor = self.connection.cursor()
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.error(f"Error creando índice: {e}")
    
    def create_all_triggers(self):
        """Crear triggers para automatización y integridad"""
        
        triggers = [
            # Trigger para actualizar timestamps
            '''
            CREATE TRIGGER IF NOT EXISTS update_products_timestamp 
            AFTER UPDATE ON products
            BEGIN
                UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_customers_timestamp 
            AFTER UPDATE ON customers
            BEGIN
                UPDATE customers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_suppliers_timestamp 
            AFTER UPDATE ON suppliers
            BEGIN
                UPDATE suppliers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            # Trigger para auditoría automática
            '''
            CREATE TRIGGER IF NOT EXISTS audit_products_insert 
            AFTER INSERT ON products
            BEGIN
                INSERT INTO audit_log (table_name, record_id, operation, new_values, user_id, timestamp)
                VALUES ('products', NEW.id, 'INSERT', 
                       json_object('name', NEW.name, 'sku', NEW.sku, 'sale_price', NEW.sale_price),
                       NEW.created_by, CURRENT_TIMESTAMP);
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS audit_products_update 
            AFTER UPDATE ON products
            BEGIN
                INSERT INTO audit_log (table_name, record_id, operation, old_values, new_values, user_id, timestamp)
                VALUES ('products', NEW.id, 'UPDATE',
                       json_object('name', OLD.name, 'sku', OLD.sku, 'sale_price', OLD.sale_price),
                       json_object('name', NEW.name, 'sku', NEW.sku, 'sale_price', NEW.sale_price),
                       NEW.updated_by, CURRENT_TIMESTAMP);
            END
            ''',
            
            # Trigger para mantener balance de cuentas corrientes
            '''
            CREATE TRIGGER IF NOT EXISTS update_customer_balance_insert
            AFTER INSERT ON account_movements
            BEGIN
                UPDATE customer_accounts 
                SET current_balance = current_balance + 
                    CASE WHEN NEW.movement_type = 'CHARGE' THEN NEW.amount ELSE -NEW.amount END,
                    last_charge_date = CASE WHEN NEW.movement_type = 'CHARGE' THEN DATE('now') ELSE last_charge_date END,
                    last_payment_date = CASE WHEN NEW.movement_type = 'PAYMENT' THEN DATE('now') ELSE last_payment_date END
                WHERE id = NEW.customer_account_id;
            END
            ''',
            
            # Trigger para actualizar stock cuando se mueve inventario
            '''
            CREATE TRIGGER IF NOT EXISTS update_stock_on_movement
            AFTER INSERT ON stock_movements
            BEGIN
                -- Actualizar stock del producto principal
                UPDATE products 
                SET current_stock = current_stock + 
                    CASE WHEN NEW.movement_type = 'IN' THEN NEW.quantity_moved 
                         ELSE -NEW.quantity_moved END
                WHERE id = NEW.product_id AND track_stock = 1;
                
                -- Actualizar stock por ubicación
                INSERT OR REPLACE INTO stock_by_location 
                (product_id, warehouse_id, storage_location_id, current_stock, lot_number, serial_number, expiration_date, last_movement_date)
                VALUES (
                    NEW.product_id, 
                    NEW.warehouse_id,
                    NEW.storage_location_id,
                    COALESCE((SELECT current_stock FROM stock_by_location 
                             WHERE product_id = NEW.product_id 
                             AND warehouse_id = NEW.warehouse_id 
                             AND COALESCE(storage_location_id, 0) = COALESCE(NEW.storage_location_id, 0)
                             AND COALESCE(lot_number, '') = COALESCE(NEW.lot_number, '')
                             AND COALESCE(serial_number, '') = COALESCE(NEW.serial_number, '')), 0) +
                    CASE WHEN NEW.movement_type = 'IN' THEN NEW.quantity_moved 
                         ELSE -NEW.quantity_moved END,
                    NEW.lot_number,
                    NEW.serial_number,
                    NEW.expiration_date,
                    CURRENT_TIMESTAMP
                );
            END
            ''',
            
            # Trigger para calcular totales de órdenes
            '''
            CREATE TRIGGER IF NOT EXISTS update_sales_order_total
            AFTER INSERT ON sales_order_details
            BEGIN
                UPDATE sales_orders 
                SET subtotal = (SELECT SUM(line_total) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    tax_amount = (SELECT SUM(tax_amount) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    total_amount = subtotal - discount_amount + tax_amount
                WHERE id = NEW.sales_order_id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_sales_order_total_on_update
            AFTER UPDATE ON sales_order_details
            BEGIN
                UPDATE sales_orders 
                SET subtotal = (SELECT SUM(line_total) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    tax_amount = (SELECT SUM(tax_amount) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    total_amount = subtotal - discount_amount + tax_amount
                WHERE id = NEW.sales_order_id;
            END
            ''',
            
            # Trigger para actualizar contadores de uso de promociones
            '''
            CREATE TRIGGER IF NOT EXISTS update_promotion_usage
            AFTER INSERT ON promotion_usage
            BEGIN
                UPDATE promotions 
                SET usage_count = usage_count + 1
                WHERE id = NEW.promotion_id;
            END
            ''',
            
            # Trigger para verificar límites de crédito
            '''
            CREATE TRIGGER IF NOT EXISTS check_credit_limit
            BEFORE INSERT ON account_movements
            WHEN NEW.movement_type = 'CHARGE'
            BEGIN
                SELECT CASE 
                    WHEN (SELECT current_balance + NEW.amount FROM customer_accounts WHERE id = NEW.customer_account_id) > 
                         (SELECT credit_limit FROM customer_accounts WHERE id = NEW.customer_account_id)
                    THEN RAISE(ABORT, 'Credit limit exceeded')
                END;
            END
            ''',
        ]
        
        with self.connection:
            cursor = self.connection., 2, False),
                ('UYU', 'Peso Uruguayo', '$U', 2, False),
                ('CLP', 'Peso Chileno', 'cursor()
            for table_name, sql in all_tables.items():
                try:
                    cursor.execute(sql)
                    logger.info(f"Tabla {table_name} creada/verificada")
                except Exception as e:
                    logger.error(f"Error creando tabla {table_name}: {e}")
                    raise
    
    def create_all_indexes(self):
        """Crear todos los índices para optimización"""
        
        indexes = [
            # Índices para búsquedas comunes en productos
            "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)",
            "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)",
            "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)",
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock ON products(current_stock)",
            "CREATE INDEX IF NOT EXISTS idx_products_type ON products(product_type)",
            
            # Índices para customers
            "CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(customer_code)",
            "CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(first_name, last_name)",
            "CREATE INDEX IF NOT EXISTS idx_customers_tax_id ON customers(tax_id)",
            "CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email)",
            "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)",
            "CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status)",
            "CREATE INDEX IF NOT EXISTS idx_customers_category ON customers(customer_category_id)",
            
            # Índices para suppliers
            "CREATE INDEX IF NOT EXISTS idx_suppliers_code ON suppliers(supplier_code)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(legal_name)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_tax_id ON suppliers(tax_id)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_status ON suppliers(status)",
            
            # Índices para sales_orders
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_number ON sales_orders(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_date ON sales_orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_customer ON sales_orders(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_status ON sales_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_cashier ON sales_orders(created_by)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_register ON sales_orders(cash_register_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_type ON sales_orders(order_type)",
            
            # Índices para sales_order_details
            "CREATE INDEX IF NOT EXISTS idx_sales_order_details_order ON sales_order_details(sales_order_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_order_details_product ON sales_order_details(product_id)",
            
            # Índices para purchase_orders
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_number ON purchase_orders(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date ON purchase_orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status)",
            
            # Índices para stock_movements
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_warehouse ON stock_movements(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_reference ON stock_movements(reference_type, reference_id)",
            
            # Índices para stock_by_location
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_product ON stock_by_location(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_warehouse ON stock_by_location(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_lot ON stock_by_location(lot_number)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_expiration ON stock_by_location(expiration_date)",
            
            # Índices para account_movements
            "CREATE INDEX IF NOT EXISTS idx_account_movements_customer ON account_movements(customer_account_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_date ON account_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_type ON account_movements(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_due_date ON account_movements(due_date)",
            
            # Índices para cash_sessions
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_register ON cash_sessions(cash_register_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_user ON cash_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_date ON cash_sessions(opened_at)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_status ON cash_sessions(status)",
            
            # Índices para cash_movements
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_session ON cash_movements(cash_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_date ON cash_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_type ON cash_movements(movement_type)",
            
            # Índices para users y sesiones
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(active)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(active)",
            
            # Índices para promotions
            "CREATE INDEX IF NOT EXISTS idx_promotions_code ON promotions(code)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_dates ON promotions(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_status ON promotions(status)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_coupon ON promotions(coupon_code)",
            
            # Índices para recipes y production
            "CREATE INDEX IF NOT EXISTS idx_recipes_product ON recipes(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_recipes_status ON recipes(status)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_recipe ON production_orders(recipe_id)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_status ON production_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_dates ON production_orders(planned_start_date, planned_end_date)",
            
            # Índices para notifications
            "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_expires ON notifications(expires_at)",
            
            # Índices para audit_log
            "CREATE INDEX IF NOT EXISTS idx_audit_log_table ON audit_log(table_name)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_record ON audit_log(table_name, record_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation)",
            
            # Índices para system_logs
            "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(log_level)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_user ON system_logs(user_id)",
            
            # Índices compuestos importantes
            "CREATE INDEX IF NOT EXISTS idx_products_category_active ON products(category_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock_status ON products(current_stock, minimum_stock) WHERE track_stock = 1",
            "CREATE INDEX IF NOT EXISTS idx_sales_customer_date ON sales_orders(customer_id, order_date)",
            "CREATE INDEX IF NOT EXISTS idx_stock_product_warehouse ON stock_by_location(product_id, warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_customer_type ON account_movements(customer_account_id, movement_type)",
            
            # Índices para fechas comunes en reportes
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_date_status ON sales_orders(order_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date_status ON purchase_orders(order_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_date_method ON payments(payment_date, payment_method_id)",
            
            # Índices para códigos y números únicos
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku_unique ON products(sku) WHERE sku IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode_unique ON products(barcode) WHERE barcode IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_code_unique ON customers(customer_code) WHERE customer_code IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_suppliers_code_unique ON suppliers(supplier_code) WHERE supplier_code IS NOT NULL",
        ]
        
        with self.connection:
            cursor = self.connection.cursor()
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.error(f"Error creando índice: {e}")
    
    def create_all_triggers(self):
        """Crear triggers para automatización y integridad"""
        
        triggers = [
            # Trigger para actualizar timestamps
            '''
            CREATE TRIGGER IF NOT EXISTS update_products_timestamp 
            AFTER UPDATE ON products
            BEGIN
                UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_customers_timestamp 
            AFTER UPDATE ON customers
            BEGIN
                UPDATE customers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_suppliers_timestamp 
            AFTER UPDATE ON suppliers
            BEGIN
                UPDATE suppliers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            # Trigger para auditoría automática
            '''
            CREATE TRIGGER IF NOT EXISTS audit_products_insert 
            AFTER INSERT ON products
            BEGIN
                INSERT INTO audit_log (table_name, record_id, operation, new_values, user_id, timestamp)
                VALUES ('products', NEW.id, 'INSERT', 
                       json_object('name', NEW.name, 'sku', NEW.sku, 'sale_price', NEW.sale_price),
                       NEW.created_by, CURRENT_TIMESTAMP);
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS audit_products_update 
            AFTER UPDATE ON products
            BEGIN
                INSERT INTO audit_log (table_name, record_id, operation, old_values, new_values, user_id, timestamp)
                VALUES ('products', NEW.id, 'UPDATE',
                       json_object('name', OLD.name, 'sku', OLD.sku, 'sale_price', OLD.sale_price),
                       json_object('name', NEW.name, 'sku', NEW.sku, 'sale_price', NEW.sale_price),
                       NEW.updated_by, CURRENT_TIMESTAMP);
            END
            ''',
            
            # Trigger para mantener balance de cuentas corrientes
            '''
            CREATE TRIGGER IF NOT EXISTS update_customer_balance_insert
            AFTER INSERT ON account_movements
            BEGIN
                UPDATE customer_accounts 
                SET current_balance = current_balance + 
                    CASE WHEN NEW.movement_type = 'CHARGE' THEN NEW.amount ELSE -NEW.amount END,
                    last_charge_date = CASE WHEN NEW.movement_type = 'CHARGE' THEN DATE('now') ELSE last_charge_date END,
                    last_payment_date = CASE WHEN NEW.movement_type = 'PAYMENT' THEN DATE('now') ELSE last_payment_date END
                WHERE id = NEW.customer_account_id;
            END
            ''',
            
            # Trigger para actualizar stock cuando se mueve inventario
            '''
            CREATE TRIGGER IF NOT EXISTS update_stock_on_movement
            AFTER INSERT ON stock_movements
            BEGIN
                -- Actualizar stock del producto principal
                UPDATE products 
                SET current_stock = current_stock + 
                    CASE WHEN NEW.movement_type = 'IN' THEN NEW.quantity_moved 
                         ELSE -NEW.quantity_moved END
                WHERE id = NEW.product_id AND track_stock = 1;
                
                -- Actualizar stock por ubicación
                INSERT OR REPLACE INTO stock_by_location 
                (product_id, warehouse_id, storage_location_id, current_stock, lot_number, serial_number, expiration_date, last_movement_date)
                VALUES (
                    NEW.product_id, 
                    NEW.warehouse_id,
                    NEW.storage_location_id,
                    COALESCE((SELECT current_stock FROM stock_by_location 
                             WHERE product_id = NEW.product_id 
                             AND warehouse_id = NEW.warehouse_id 
                             AND COALESCE(storage_location_id, 0) = COALESCE(NEW.storage_location_id, 0)
                             AND COALESCE(lot_number, '') = COALESCE(NEW.lot_number, '')
                             AND COALESCE(serial_number, '') = COALESCE(NEW.serial_number, '')), 0) +
                    CASE WHEN NEW.movement_type = 'IN' THEN NEW.quantity_moved 
                         ELSE -NEW.quantity_moved END,
                    NEW.lot_number,
                    NEW.serial_number,
                    NEW.expiration_date,
                    CURRENT_TIMESTAMP
                );
            END
            ''',
            
            # Trigger para calcular totales de órdenes
            '''
            CREATE TRIGGER IF NOT EXISTS update_sales_order_total
            AFTER INSERT ON sales_order_details
            BEGIN
                UPDATE sales_orders 
                SET subtotal = (SELECT SUM(line_total) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    tax_amount = (SELECT SUM(tax_amount) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    total_amount = subtotal - discount_amount + tax_amount
                WHERE id = NEW.sales_order_id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_sales_order_total_on_update
            AFTER UPDATE ON sales_order_details
            BEGIN
                UPDATE sales_orders 
                SET subtotal = (SELECT SUM(line_total) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    tax_amount = (SELECT SUM(tax_amount) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    total_amount = subtotal - discount_amount + tax_amount
                WHERE id = NEW.sales_order_id;
            END
            ''',
            
            # Trigger para actualizar contadores de uso de promociones
            '''
            CREATE TRIGGER IF NOT EXISTS update_promotion_usage
            AFTER INSERT ON promotion_usage
            BEGIN
                UPDATE promotions 
                SET usage_count = usage_count + 1
                WHERE id = NEW.promotion_id;
            END
            ''',
            
            # Trigger para verificar límites de crédito
            '''
            CREATE TRIGGER IF NOT EXISTS check_credit_limit
            BEFORE INSERT ON account_movements
            WHEN NEW.movement_type = 'CHARGE'
            BEGIN
                SELECT CASE 
                    WHEN (SELECT current_balance + NEW.amount FROM customer_accounts WHERE id = NEW.customer_account_id) > 
                         (SELECT credit_limit FROM customer_accounts WHERE id = NEW.customer_account_id)
                    THEN RAISE(ABORT, 'Credit limit exceeded')
                END;
            END
            ''',
        ]
        
        with self.connection:
            cursor = self.connection., 0, False),
            ]
            
            for code, name, symbol, decimals, is_base in currencies_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO currencies (code, name, symbol, decimal_places, is_base_currency) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (code, name, symbol, decimals, is_base))
                except Exception as e:
                    logger.error(f"Error insertando moneda {name}: {e}")
            
            # Tipos de impuestos
            tax_types_data = [
                ('IVA', 'Impuesto al Valor Agregado', 'Impuesto general al consumo', 1, True),
                ('IIBB', 'Ingresos Brutos', 'Impuesto provincial a los ingresos brutos', 1, True),
                ('IMP_INT', 'Impuestos Internos', 'Impuestos internos específicos', 1, True),
                ('PERC_IVA', 'Percepción IVA', 'Percepción de IVA', 1, True),
                ('PERC_IIBB', 'Percepción IIBB', 'Percepción de Ingresos Brutos', 1, True),
            ]
            
            for code, name, description, country_id, is_percentage in tax_types_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO tax_types (code, name, description, country_id, is_percentage) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (code, name, description, country_id, is_percentage))
                except Exception as e:
                    logger.error(f"Error insertando tipo de impuesto {name}: {e}")
            
            # Alícuotas de IVA
            iva_rates_data = [
                (1, 0.0000, 'Exento', '2024-01-01', None),
                (1, 10.5000, 'Reducida', '2024-01-01', None),
                (1, 21.0000, 'General', '2024-01-01', None),
                (1, 27.0000, 'Aumentada', '2024-01-01', None),
            ]
            
            for tax_type_id, rate, description, valid_from, valid_to in iva_rates_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO tax_rates (tax_type_id, rate, description, valid_from, valid_to) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (tax_type_id, rate, description, valid_from, valid_to))
                except Exception as e:
                    logger.error(f"Error insertando alícuota IVA {description}: {e}")
            
            # Roles del sistema
            roles_data = [
                ('SUPER_ADMIN', 'Super Administrador', 'Acceso completo al sistema', '{"all": true}', 10, '#FF0000'),
                ('ADMIN', 'Administrador', 'Administrador general', '{"admin": true, "users": true, "config": true, "reports": true}', 9, '#FF6600'),
                ('MANAGER', 'Gerente', 'Gerente de sucursal', '{"sales": true, "purchases": true, "inventory": true, "reports": true, "customers": true}', 8, '#FF9900'),
                ('SUPERVISOR', 'Supervisor', 'Supervisor de ventas', '{"sales": true, "inventory": true, "customers": true, "reports_basic": true}', 7, '#FFCC00'),
                ('CASHIER', 'Cajero', 'Operador de caja', '{"sales": true, "customers_basic": true}', 5, '#00CC00'),
                ('STOCK_CLERK', 'Repositor', 'Encargado de stock', '{"inventory": true, "purchases_receive": true}', 4, '#0099CC'),
                ('BUTCHER', 'Carnicero', 'Especialista en carnicería', '{"sales": true, "inventory": true, "butcher_module": true}', 6, '#CC0000'),
                ('DELI_CLERK', 'Fiambrero', 'Especialista en fiambrería', '{"sales": true, "inventory": true, "deli_module": true}', 6, '#CC6600'),
                ('BAKER', 'Panadero', 'Especialista en panadería', '{"sales": true, "inventory": true, "production": true, "baker_module": true}', 6, '#FFAA00'),
                ('VIEWER', 'Consulta', 'Solo lectura', '{"reports_view": true}', 2, '#666666'),
            ]
            
            for name, display_name, description, permissions, level, color in roles_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO roles (name, display_name, description, permissions, level, color) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (name, display_name, description, permissions, level, color))
                except Exception as e:
                    logger.error(f"Error insertando rol {name}: {e}")
            
            # Usuario administrador por defecto
            import hashlib
            admin_password = hashlib.sha256("admin123".encode()).hexdigest()
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO users (username, email, password_hash, first_name, last_name, role_id, active, verified) 
                    VALUES ('admin', 'admin@almacenpro.com', ?, 'Administrador', 'del Sistema', 1, 1, 1)
                """, (admin_password,))
            except Exception as e:
                logger.error(f"Error creando usuario admin: {e}")
            
            # Unidades de medida
            units_data = [
                ('UN', 'Unidad', 'un', 'COUNT', None, 1, 0),
                ('KG', 'Kilogramo', 'kg', 'WEIGHT', None, 1, 3),
                ('GR', 'Gramo', 'g', 'WEIGHT', 2, 0.001, 1),
                ('LB', 'Libra', 'lb', 'WEIGHT', 2, 0.453592, 3),
                ('L', 'Litro', 'l', 'VOLUME', None, 1, 3),
                ('ML', 'Mililitro', 'ml', 'VOLUME', 5, 0.001, 0),
                ('M', 'Metro', 'm', 'LENGTH', None, 1, 2),
                ('CM', 'Centímetro', 'cm', 'LENGTH', 7, 0.01, 1),
                ('M2', 'Metro cuadrado', 'm²', 'AREA', None, 1, 2),
                ('M3', 'Metro cúbico', 'm³', 'VOLUME', None, 1, 3),
                ('DOC', 'Docena', 'doc', 'COUNT', 1, 12, 0),
                ('PAQ', 'Paquete', 'paq', 'COUNT', 1, 1, 0),
                ('CAJ', 'Caja', 'caj', 'COUNT', 1, 1, 0),
                ('MIN', 'Minuto', 'min', 'TIME', None, 1, 0),
                ('HR', 'Hora', 'h', 'TIME', 14, 60, 2),
            ]
            
            for code, name, symbol, unit_type, base_unit_id, conversion_factor, decimal_places in units_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO units_of_measure (code, name, symbol, unit_type, base_unit_id, conversion_factor, decimal_places) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (code, name, symbol, unit_type, base_unit_id, conversion_factor, decimal_places))
                except Exception as e:
                    logger.error(f"Error insertando unidad {name}: {e}")
            
            # Categorías de productos por defecto
            categories_data = [
                (None, 'GENERAL', 'Productos generales', None, 0, 3),
                (None, 'ALIMENTACION', 'Alimentos y bebidas', None, 1, 3),
                (None, 'LIMPIEZA', 'Productos de limpieza', None, 2, 3),
                (None, 'PERFUMERIA', 'Perfumería y cosmética', None, 3, 3),
                (None, 'LIBRERIA', 'Librería y papelería', None, 4, 3),
                (None, 'FERRETERIA', 'Ferretería y herramientas', None, 5, 3),
                (None, 'TEXTIL', 'Ropa y textiles', None, 6, 3),
                (None, 'ELECTRONICA', 'Electrónicos y tecnología', None, 7, 3),
                (None, 'HOGAR', 'Artículos para el hogar', None, 8, 3),
                (None, 'DEPORTES', 'Deportes y recreación', None, 9, 3),
                
                # Subcategorías de alimentación
                (2, 'PANADERIA', 'Panadería y repostería', None, 10, 3),
                (2, 'CARNICERIA', 'Carnes y embutidos', None, 11, 3),
                (2, 'FIAMBRERIA', 'Fiambres y lácteos', None, 12, 3),
                (2, 'VERDULERIA', 'Frutas y verduras', None, 13, 3),
                (2, 'BEBIDAS', 'Bebidas y refrescos', None, 14, 3),
                (2, 'GOLOSINAS', 'Golosinas y snacks', None, 15, 3),
                (2, 'CONSERVAS', 'Conservas y enlatados', None, 16, 3),
                (2, 'LACTEOS', 'Productos lácteos', None, 17, 3),
                (2, 'CONGELADOS', 'Productos congelados', None, 18, 3),
                (2, 'CEREALES', 'Cereales y legumbres', None, 19, 3),
                
                # Subcategorías de limpieza
                (3, 'DETERGENTES', 'Detergentes y jabones', None, 20, 3),
                (3, 'DESINFECTANTES', 'Desinfectantes', None, 21, 3),
                (3, 'PAPEL', 'Papel higiénico y servilletas', None, 22, 3),
                (3, 'ESCOBAS', 'Escobas y utensilios', None, 23, 3),
            ]
            
            for parent_id, name, description, image_url, sort_order, tax_rate_id in categories_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO product_categories (parent_category_id, name, description, image_url, sort_order, tax_rate_id) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (parent_id, name, description, image_url, sort_order, tax_rate_id))
                except Exception as e:
                    logger.error(f"Error insertando categoría {name}: {e}")
            
            # Categorías de clientes
            customer_categories_data = [
                ('MINORISTA', 'Cliente Minorista', 0, 0, 0, '#00AA00'),
                ('MAYORISTA', 'Cliente Mayorista', 10, 50000, 30, '#0066CC'),
                ('VIP', 'Cliente VIP', 15, 100000, 60, '#FF6600'),
                ('EMPLEADO', 'Empleado', 20, 10000, 0, '#9900CC'),
                ('PROVEEDOR', 'Proveedor Cliente', 5, 20000, 15, '#CC6600'),
            ]
            
            for name, description, discount, credit_limit, payment_terms, color in customer_categories_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO customer_categories (name, description, discount_percentage, credit_limit, payment_terms_days, color) 
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (name, description, discount, credit_limit, payment_terms, color))
                except Exception as e:
                    logger.error(f"Error insertando categoría cliente {name}: {e}")
            
            # Métodos de pago
            payment_methods_data = [
                ('CASH', 'Efectivo', 'Pago en efectivo', 'CASH', False, 0, 0, 0, True, 1),
                ('DEBIT', 'Tarjeta de Débito', 'Pago con tarjeta de débito', 'CARD', True, 2.5, 0, 1, True, 2),
                ('CREDIT', 'Tarjeta de Crédito', 'Pago con tarjeta de crédito', 'CARD', True, 4.5, 0, 2, True, 3),
                ('TRANSFER', 'Transferencia', 'Transferencia bancaria', 'TRANSFER', True, 0, 0, 1, True, 4),
                ('CHECK', 'Cheque', 'Pago con cheque', 'CHECK', True, 0, 0, 3, True, 5),
                ('ACCOUNT', 'Cuenta Corriente', 'Cuenta corriente del cliente', 'ACCOUNT', False, 0, 0, 0, True, 6),
                ('MERCADOPAGO', 'MercadoPago', 'Pago con MercadoPago', 'DIGITAL_WALLET', True, 3.8, 5, 1, True, 7),
                ('PAYPAL', 'PayPal', 'Pago con PayPal', 'DIGITAL_WALLET', True, 4.2, 0, 2, False, 8),
            ]
            
            for code, name, description, method_type, requires_ref, fee_pct, fee_fixed, settlement_days, active, sort_order in payment_methods_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO payment_methods (code, name, description, method_type, requires_reference, processing_fee_percentage, processing_fee_fixed, settlement_days, active, sort_order) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (code, name, description, method_type, requires_ref, fee_pct, fee_fixed, settlement_days, active, sort_order))
                except Exception as e:
                    logger.error(f"Error insertando método de pago {name}: {e}")
            
            # Denominaciones de moneda (billetes y monedas argentinas)
            denominations_data = [
                (1, 1000, 'BILL'), (1, 500, 'BILL'), (1, 200, 'BILL'), (1, 100, 'BILL'),
                (1, 50, 'BILL'), (1, 20, 'BILL'), (1, 10, 'BILL'),
                (1, 10, 'COIN'), (1, 5, 'COIN'), (1, 2, 'COIN'), (1, 1, 'COIN'),
                (1, 0.50, 'COIN'), (1, 0.25, 'COIN'), (1, 0.10, 'COIN'), (1, 0.05, 'COIN'),
            ]
            
            for currency_id, value, denom_type in denominations_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO cash_denominations (currency_id, denomination_value, denomination_type) 
                        VALUES (?, ?, ?)
                    """, (currency_id, value, denom_type))
                except Exception as e:
                    logger.error(f"Error insertando denominación {value}: {e}")
            
            # Tipos de promociones
            promotion_types_data = [
                ('DISCOUNT_PERCENTAGE', 'Descuento Porcentual', 'Descuento por porcentaje'),
                ('DISCOUNT_FIXED', 'Descuento Fijo', 'Descuento por monto fijo'),
                ('BUY_X_GET_Y', 'Lleve X Pague Y', 'Promoción de cantidad'),
                ('FREE_SHIPPING', 'Envío Gratis', 'Envío sin costo'),
                ('COMBO', 'Combo Promocional', 'Combo de productos'),
                ('HAPPY_HOUR', 'Happy Hour', 'Descuento por horario'),
                ('SEASONAL', 'Promoción Estacional', 'Promoción por temporada'),
            ]
            
            for code, name, description in promotion_types_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO promotion_types (code, name, description) 
                        VALUES (?, ?, ?)
                    """, (code, name, description))
                except Exception as e:
                    logger.error(f"Error insertando tipo de promoción {name}: {e}")
            
            # Tipos de notificaciones
            notification_types_data = [
                ('LOW_STOCK', 'Stock Bajo', 'Notificación de stock bajo', 'warning', '#FF9800', True, 4),
                ('OUT_OF_STOCK', 'Sin Stock', 'Producto sin stock', 'error', '#F44336', True, 5),
                ('EXPIRING_PRODUCT', 'Producto por Vencer', 'Producto próximo a vencer', 'warning', '#FF5722', True, 3),
                ('SALE_COMPLETED', 'Venta Realizada', 'Venta completada exitosamente', 'success', '#4CAF50', False, 2),
                ('PAYMENT_RECEIVED', 'Pago Recibido', 'Pago de cuenta corriente recibido', 'success', '#2196F3', True, 3),
                ('OVERDUE_ACCOUNT', 'Cuenta Vencida', 'Cuenta corriente vencida', 'error', '#F44336', True, 4),
                ('BACKUP_COMPLETED', 'Backup Completado', 'Backup realizado exitosamente', 'info', '#00BCD4', True, 2),
                ('BACKUP_FAILED', 'Error en Backup', 'Error al realizar backup', 'error', '#F44336', True, 5),
                ('SYSTEM_ERROR', 'Error del Sistema', 'Error interno del sistema', 'error', '#F44336', True, 5),
                ('NEW_USER', 'Nuevo Usuario', 'Usuario registrado en el sistema', 'info', '#673AB7', True, 2),
                ('PROMOTION_STARTED', 'Promoción Iniciada', 'Nueva promoción activada', 'info', '#FF9800', False, 2),
                ('DAILY_REPORT', 'Reporte Diario', 'Resumen diario de ventas', 'info', '#607D8B', True, 1),
            ]
            
            for code, name, description, icon, color, default_enabled, priority in notification_types_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO notification_types (code, name, description, icon, color, default_enabled, priority) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (code, name, description, icon, color, default_enabled, priority))
                except Exception as e:
                    logger.error(f"Error insertando tipo de notificación {name}: {e}")
            
            # KPIs por defecto
            kpi_definitions_data = [
                ('DAILY_SALES', 'Ventas Diarias', 'Total de ventas del día', 'SELECT SUM(total_amount) FROM sales_orders WHERE DATE(order_date) = DATE("now")', 'cursor()
            for table_name, sql in all_tables.items():
                try:
                    cursor.execute(sql)
                    logger.info(f"Tabla {table_name} creada/verificada")
                except Exception as e:
                    logger.error(f"Error creando tabla {table_name}: {e}")
                    raise
    
    def create_all_indexes(self):
        """Crear todos los índices para optimización"""
        
        indexes = [
            # Índices para búsquedas comunes en productos
            "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)",
            "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)",
            "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)",
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock ON products(current_stock)",
            "CREATE INDEX IF NOT EXISTS idx_products_type ON products(product_type)",
            
            # Índices para customers
            "CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(customer_code)",
            "CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(first_name, last_name)",
            "CREATE INDEX IF NOT EXISTS idx_customers_tax_id ON customers(tax_id)",
            "CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email)",
            "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)",
            "CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status)",
            "CREATE INDEX IF NOT EXISTS idx_customers_category ON customers(customer_category_id)",
            
            # Índices para suppliers
            "CREATE INDEX IF NOT EXISTS idx_suppliers_code ON suppliers(supplier_code)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(legal_name)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_tax_id ON suppliers(tax_id)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_status ON suppliers(status)",
            
            # Índices para sales_orders
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_number ON sales_orders(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_date ON sales_orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_customer ON sales_orders(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_status ON sales_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_cashier ON sales_orders(created_by)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_register ON sales_orders(cash_register_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_type ON sales_orders(order_type)",
            
            # Índices para sales_order_details
            "CREATE INDEX IF NOT EXISTS idx_sales_order_details_order ON sales_order_details(sales_order_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_order_details_product ON sales_order_details(product_id)",
            
            # Índices para purchase_orders
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_number ON purchase_orders(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date ON purchase_orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status)",
            
            # Índices para stock_movements
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_warehouse ON stock_movements(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_reference ON stock_movements(reference_type, reference_id)",
            
            # Índices para stock_by_location
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_product ON stock_by_location(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_warehouse ON stock_by_location(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_lot ON stock_by_location(lot_number)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_expiration ON stock_by_location(expiration_date)",
            
            # Índices para account_movements
            "CREATE INDEX IF NOT EXISTS idx_account_movements_customer ON account_movements(customer_account_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_date ON account_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_type ON account_movements(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_due_date ON account_movements(due_date)",
            
            # Índices para cash_sessions
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_register ON cash_sessions(cash_register_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_user ON cash_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_date ON cash_sessions(opened_at)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_status ON cash_sessions(status)",
            
            # Índices para cash_movements
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_session ON cash_movements(cash_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_date ON cash_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_type ON cash_movements(movement_type)",
            
            # Índices para users y sesiones
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(active)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(active)",
            
            # Índices para promotions
            "CREATE INDEX IF NOT EXISTS idx_promotions_code ON promotions(code)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_dates ON promotions(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_status ON promotions(status)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_coupon ON promotions(coupon_code)",
            
            # Índices para recipes y production
            "CREATE INDEX IF NOT EXISTS idx_recipes_product ON recipes(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_recipes_status ON recipes(status)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_recipe ON production_orders(recipe_id)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_status ON production_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_dates ON production_orders(planned_start_date, planned_end_date)",
            
            # Índices para notifications
            "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_expires ON notifications(expires_at)",
            
            # Índices para audit_log
            "CREATE INDEX IF NOT EXISTS idx_audit_log_table ON audit_log(table_name)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_record ON audit_log(table_name, record_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation)",
            
            # Índices para system_logs
            "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(log_level)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_user ON system_logs(user_id)",
            
            # Índices compuestos importantes
            "CREATE INDEX IF NOT EXISTS idx_products_category_active ON products(category_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock_status ON products(current_stock, minimum_stock) WHERE track_stock = 1",
            "CREATE INDEX IF NOT EXISTS idx_sales_customer_date ON sales_orders(customer_id, order_date)",
            "CREATE INDEX IF NOT EXISTS idx_stock_product_warehouse ON stock_by_location(product_id, warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_customer_type ON account_movements(customer_account_id, movement_type)",
            
            # Índices para fechas comunes en reportes
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_date_status ON sales_orders(order_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date_status ON purchase_orders(order_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_date_method ON payments(payment_date, payment_method_id)",
            
            # Índices para códigos y números únicos
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku_unique ON products(sku) WHERE sku IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode_unique ON products(barcode) WHERE barcode IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_code_unique ON customers(customer_code) WHERE customer_code IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_suppliers_code_unique ON suppliers(supplier_code) WHERE supplier_code IS NOT NULL",
        ]
        
        with self.connection:
            cursor = self.connection.cursor()
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.error(f"Error creando índice: {e}")
    
    def create_all_triggers(self):
        """Crear triggers para automatización y integridad"""
        
        triggers = [
            # Trigger para actualizar timestamps
            '''
            CREATE TRIGGER IF NOT EXISTS update_products_timestamp 
            AFTER UPDATE ON products
            BEGIN
                UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_customers_timestamp 
            AFTER UPDATE ON customers
            BEGIN
                UPDATE customers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_suppliers_timestamp 
            AFTER UPDATE ON suppliers
            BEGIN
                UPDATE suppliers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            # Trigger para auditoría automática
            '''
            CREATE TRIGGER IF NOT EXISTS audit_products_insert 
            AFTER INSERT ON products
            BEGIN
                INSERT INTO audit_log (table_name, record_id, operation, new_values, user_id, timestamp)
                VALUES ('products', NEW.id, 'INSERT', 
                       json_object('name', NEW.name, 'sku', NEW.sku, 'sale_price', NEW.sale_price),
                       NEW.created_by, CURRENT_TIMESTAMP);
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS audit_products_update 
            AFTER UPDATE ON products
            BEGIN
                INSERT INTO audit_log (table_name, record_id, operation, old_values, new_values, user_id, timestamp)
                VALUES ('products', NEW.id, 'UPDATE',
                       json_object('name', OLD.name, 'sku', OLD.sku, 'sale_price', OLD.sale_price),
                       json_object('name', NEW.name, 'sku', NEW.sku, 'sale_price', NEW.sale_price),
                       NEW.updated_by, CURRENT_TIMESTAMP);
            END
            ''',
            
            # Trigger para mantener balance de cuentas corrientes
            '''
            CREATE TRIGGER IF NOT EXISTS update_customer_balance_insert
            AFTER INSERT ON account_movements
            BEGIN
                UPDATE customer_accounts 
                SET current_balance = current_balance + 
                    CASE WHEN NEW.movement_type = 'CHARGE' THEN NEW.amount ELSE -NEW.amount END,
                    last_charge_date = CASE WHEN NEW.movement_type = 'CHARGE' THEN DATE('now') ELSE last_charge_date END,
                    last_payment_date = CASE WHEN NEW.movement_type = 'PAYMENT' THEN DATE('now') ELSE last_payment_date END
                WHERE id = NEW.customer_account_id;
            END
            ''',
            
            # Trigger para actualizar stock cuando se mueve inventario
            '''
            CREATE TRIGGER IF NOT EXISTS update_stock_on_movement
            AFTER INSERT ON stock_movements
            BEGIN
                -- Actualizar stock del producto principal
                UPDATE products 
                SET current_stock = current_stock + 
                    CASE WHEN NEW.movement_type = 'IN' THEN NEW.quantity_moved 
                         ELSE -NEW.quantity_moved END
                WHERE id = NEW.product_id AND track_stock = 1;
                
                -- Actualizar stock por ubicación
                INSERT OR REPLACE INTO stock_by_location 
                (product_id, warehouse_id, storage_location_id, current_stock, lot_number, serial_number, expiration_date, last_movement_date)
                VALUES (
                    NEW.product_id, 
                    NEW.warehouse_id,
                    NEW.storage_location_id,
                    COALESCE((SELECT current_stock FROM stock_by_location 
                             WHERE product_id = NEW.product_id 
                             AND warehouse_id = NEW.warehouse_id 
                             AND COALESCE(storage_location_id, 0) = COALESCE(NEW.storage_location_id, 0)
                             AND COALESCE(lot_number, '') = COALESCE(NEW.lot_number, '')
                             AND COALESCE(serial_number, '') = COALESCE(NEW.serial_number, '')), 0) +
                    CASE WHEN NEW.movement_type = 'IN' THEN NEW.quantity_moved 
                         ELSE -NEW.quantity_moved END,
                    NEW.lot_number,
                    NEW.serial_number,
                    NEW.expiration_date,
                    CURRENT_TIMESTAMP
                );
            END
            ''',
            
            # Trigger para calcular totales de órdenes
            '''
            CREATE TRIGGER IF NOT EXISTS update_sales_order_total
            AFTER INSERT ON sales_order_details
            BEGIN
                UPDATE sales_orders 
                SET subtotal = (SELECT SUM(line_total) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    tax_amount = (SELECT SUM(tax_amount) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    total_amount = subtotal - discount_amount + tax_amount
                WHERE id = NEW.sales_order_id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_sales_order_total_on_update
            AFTER UPDATE ON sales_order_details
            BEGIN
                UPDATE sales_orders 
                SET subtotal = (SELECT SUM(line_total) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    tax_amount = (SELECT SUM(tax_amount) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    total_amount = subtotal - discount_amount + tax_amount
                WHERE id = NEW.sales_order_id;
            END
            ''',
            
            # Trigger para actualizar contadores de uso de promociones
            '''
            CREATE TRIGGER IF NOT EXISTS update_promotion_usage
            AFTER INSERT ON promotion_usage
            BEGIN
                UPDATE promotions 
                SET usage_count = usage_count + 1
                WHERE id = NEW.promotion_id;
            END
            ''',
            
            # Trigger para verificar límites de crédito
            '''
            CREATE TRIGGER IF NOT EXISTS check_credit_limit
            BEFORE INSERT ON account_movements
            WHEN NEW.movement_type = 'CHARGE'
            BEGIN
                SELECT CASE 
                    WHEN (SELECT current_balance + NEW.amount FROM customer_accounts WHERE id = NEW.customer_account_id) > 
                         (SELECT credit_limit FROM customer_accounts WHERE id = NEW.customer_account_id)
                    THEN RAISE(ABORT, 'Credit limit exceeded')
                END;
            END
            ''',
        ]
        
        with self.connection:
            cursor = self.connection., 0, 0, 0),
                ('DAILY_TRANSACTIONS', 'Transacciones Diarias', 'Número de transacciones del día', 'SELECT COUNT(*) FROM sales_orders WHERE DATE(order_date) = DATE("now")', 'units', 0, 0, 0),
                ('AVERAGE_TICKET', 'Ticket Promedio', 'Valor promedio por venta', 'SELECT AVG(total_amount) FROM sales_orders WHERE DATE(order_date) = DATE("now")', 'cursor()
            for table_name, sql in all_tables.items():
                try:
                    cursor.execute(sql)
                    logger.info(f"Tabla {table_name} creada/verificada")
                except Exception as e:
                    logger.error(f"Error creando tabla {table_name}: {e}")
                    raise
    
    def create_all_indexes(self):
        """Crear todos los índices para optimización"""
        
        indexes = [
            # Índices para búsquedas comunes en productos
            "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)",
            "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)",
            "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)",
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock ON products(current_stock)",
            "CREATE INDEX IF NOT EXISTS idx_products_type ON products(product_type)",
            
            # Índices para customers
            "CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(customer_code)",
            "CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(first_name, last_name)",
            "CREATE INDEX IF NOT EXISTS idx_customers_tax_id ON customers(tax_id)",
            "CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email)",
            "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)",
            "CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status)",
            "CREATE INDEX IF NOT EXISTS idx_customers_category ON customers(customer_category_id)",
            
            # Índices para suppliers
            "CREATE INDEX IF NOT EXISTS idx_suppliers_code ON suppliers(supplier_code)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(legal_name)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_tax_id ON suppliers(tax_id)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_status ON suppliers(status)",
            
            # Índices para sales_orders
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_number ON sales_orders(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_date ON sales_orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_customer ON sales_orders(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_status ON sales_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_cashier ON sales_orders(created_by)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_register ON sales_orders(cash_register_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_type ON sales_orders(order_type)",
            
            # Índices para sales_order_details
            "CREATE INDEX IF NOT EXISTS idx_sales_order_details_order ON sales_order_details(sales_order_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_order_details_product ON sales_order_details(product_id)",
            
            # Índices para purchase_orders
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_number ON purchase_orders(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date ON purchase_orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status)",
            
            # Índices para stock_movements
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_warehouse ON stock_movements(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_reference ON stock_movements(reference_type, reference_id)",
            
            # Índices para stock_by_location
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_product ON stock_by_location(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_warehouse ON stock_by_location(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_lot ON stock_by_location(lot_number)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_expiration ON stock_by_location(expiration_date)",
            
            # Índices para account_movements
            "CREATE INDEX IF NOT EXISTS idx_account_movements_customer ON account_movements(customer_account_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_date ON account_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_type ON account_movements(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_due_date ON account_movements(due_date)",
            
            # Índices para cash_sessions
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_register ON cash_sessions(cash_register_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_user ON cash_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_date ON cash_sessions(opened_at)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_status ON cash_sessions(status)",
            
            # Índices para cash_movements
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_session ON cash_movements(cash_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_date ON cash_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_type ON cash_movements(movement_type)",
            
            # Índices para users y sesiones
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(active)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(active)",
            
            # Índices para promotions
            "CREATE INDEX IF NOT EXISTS idx_promotions_code ON promotions(code)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_dates ON promotions(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_status ON promotions(status)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_coupon ON promotions(coupon_code)",
            
            # Índices para recipes y production
            "CREATE INDEX IF NOT EXISTS idx_recipes_product ON recipes(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_recipes_status ON recipes(status)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_recipe ON production_orders(recipe_id)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_status ON production_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_dates ON production_orders(planned_start_date, planned_end_date)",
            
            # Índices para notifications
            "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_expires ON notifications(expires_at)",
            
            # Índices para audit_log
            "CREATE INDEX IF NOT EXISTS idx_audit_log_table ON audit_log(table_name)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_record ON audit_log(table_name, record_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation)",
            
            # Índices para system_logs
            "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(log_level)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_user ON system_logs(user_id)",
            
            # Índices compuestos importantes
            "CREATE INDEX IF NOT EXISTS idx_products_category_active ON products(category_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock_status ON products(current_stock, minimum_stock) WHERE track_stock = 1",
            "CREATE INDEX IF NOT EXISTS idx_sales_customer_date ON sales_orders(customer_id, order_date)",
            "CREATE INDEX IF NOT EXISTS idx_stock_product_warehouse ON stock_by_location(product_id, warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_customer_type ON account_movements(customer_account_id, movement_type)",
            
            # Índices para fechas comunes en reportes
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_date_status ON sales_orders(order_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date_status ON purchase_orders(order_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_date_method ON payments(payment_date, payment_method_id)",
            
            # Índices para códigos y números únicos
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku_unique ON products(sku) WHERE sku IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode_unique ON products(barcode) WHERE barcode IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_code_unique ON customers(customer_code) WHERE customer_code IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_suppliers_code_unique ON suppliers(supplier_code) WHERE supplier_code IS NOT NULL",
        ]
        
        with self.connection:
            cursor = self.connection.cursor()
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.error(f"Error creando índice: {e}")
    
    def create_all_triggers(self):
        """Crear triggers para automatización y integridad"""
        
        triggers = [
            # Trigger para actualizar timestamps
            '''
            CREATE TRIGGER IF NOT EXISTS update_products_timestamp 
            AFTER UPDATE ON products
            BEGIN
                UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_customers_timestamp 
            AFTER UPDATE ON customers
            BEGIN
                UPDATE customers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_suppliers_timestamp 
            AFTER UPDATE ON suppliers
            BEGIN
                UPDATE suppliers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            # Trigger para auditoría automática
            '''
            CREATE TRIGGER IF NOT EXISTS audit_products_insert 
            AFTER INSERT ON products
            BEGIN
                INSERT INTO audit_log (table_name, record_id, operation, new_values, user_id, timestamp)
                VALUES ('products', NEW.id, 'INSERT', 
                       json_object('name', NEW.name, 'sku', NEW.sku, 'sale_price', NEW.sale_price),
                       NEW.created_by, CURRENT_TIMESTAMP);
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS audit_products_update 
            AFTER UPDATE ON products
            BEGIN
                INSERT INTO audit_log (table_name, record_id, operation, old_values, new_values, user_id, timestamp)
                VALUES ('products', NEW.id, 'UPDATE',
                       json_object('name', OLD.name, 'sku', OLD.sku, 'sale_price', OLD.sale_price),
                       json_object('name', NEW.name, 'sku', NEW.sku, 'sale_price', NEW.sale_price),
                       NEW.updated_by, CURRENT_TIMESTAMP);
            END
            ''',
            
            # Trigger para mantener balance de cuentas corrientes
            '''
            CREATE TRIGGER IF NOT EXISTS update_customer_balance_insert
            AFTER INSERT ON account_movements
            BEGIN
                UPDATE customer_accounts 
                SET current_balance = current_balance + 
                    CASE WHEN NEW.movement_type = 'CHARGE' THEN NEW.amount ELSE -NEW.amount END,
                    last_charge_date = CASE WHEN NEW.movement_type = 'CHARGE' THEN DATE('now') ELSE last_charge_date END,
                    last_payment_date = CASE WHEN NEW.movement_type = 'PAYMENT' THEN DATE('now') ELSE last_payment_date END
                WHERE id = NEW.customer_account_id;
            END
            ''',
            
            # Trigger para actualizar stock cuando se mueve inventario
            '''
            CREATE TRIGGER IF NOT EXISTS update_stock_on_movement
            AFTER INSERT ON stock_movements
            BEGIN
                -- Actualizar stock del producto principal
                UPDATE products 
                SET current_stock = current_stock + 
                    CASE WHEN NEW.movement_type = 'IN' THEN NEW.quantity_moved 
                         ELSE -NEW.quantity_moved END
                WHERE id = NEW.product_id AND track_stock = 1;
                
                -- Actualizar stock por ubicación
                INSERT OR REPLACE INTO stock_by_location 
                (product_id, warehouse_id, storage_location_id, current_stock, lot_number, serial_number, expiration_date, last_movement_date)
                VALUES (
                    NEW.product_id, 
                    NEW.warehouse_id,
                    NEW.storage_location_id,
                    COALESCE((SELECT current_stock FROM stock_by_location 
                             WHERE product_id = NEW.product_id 
                             AND warehouse_id = NEW.warehouse_id 
                             AND COALESCE(storage_location_id, 0) = COALESCE(NEW.storage_location_id, 0)
                             AND COALESCE(lot_number, '') = COALESCE(NEW.lot_number, '')
                             AND COALESCE(serial_number, '') = COALESCE(NEW.serial_number, '')), 0) +
                    CASE WHEN NEW.movement_type = 'IN' THEN NEW.quantity_moved 
                         ELSE -NEW.quantity_moved END,
                    NEW.lot_number,
                    NEW.serial_number,
                    NEW.expiration_date,
                    CURRENT_TIMESTAMP
                );
            END
            ''',
            
            # Trigger para calcular totales de órdenes
            '''
            CREATE TRIGGER IF NOT EXISTS update_sales_order_total
            AFTER INSERT ON sales_order_details
            BEGIN
                UPDATE sales_orders 
                SET subtotal = (SELECT SUM(line_total) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    tax_amount = (SELECT SUM(tax_amount) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    total_amount = subtotal - discount_amount + tax_amount
                WHERE id = NEW.sales_order_id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_sales_order_total_on_update
            AFTER UPDATE ON sales_order_details
            BEGIN
                UPDATE sales_orders 
                SET subtotal = (SELECT SUM(line_total) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    tax_amount = (SELECT SUM(tax_amount) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    total_amount = subtotal - discount_amount + tax_amount
                WHERE id = NEW.sales_order_id;
            END
            ''',
            
            # Trigger para actualizar contadores de uso de promociones
            '''
            CREATE TRIGGER IF NOT EXISTS update_promotion_usage
            AFTER INSERT ON promotion_usage
            BEGIN
                UPDATE promotions 
                SET usage_count = usage_count + 1
                WHERE id = NEW.promotion_id;
            END
            ''',
            
            # Trigger para verificar límites de crédito
            '''
            CREATE TRIGGER IF NOT EXISTS check_credit_limit
            BEFORE INSERT ON account_movements
            WHEN NEW.movement_type = 'CHARGE'
            BEGIN
                SELECT CASE 
                    WHEN (SELECT current_balance + NEW.amount FROM customer_accounts WHERE id = NEW.customer_account_id) > 
                         (SELECT credit_limit FROM customer_accounts WHERE id = NEW.customer_account_id)
                    THEN RAISE(ABORT, 'Credit limit exceeded')
                END;
            END
            ''',
        ]
        
        with self.connection:
            cursor = self.connection., 0, 0, 0),
                ('STOCK_TURNOVER', 'Rotación de Stock', 'Rotación de inventario mensual', '', 'ratio', 4, 2, 1),
                ('GROSS_MARGIN', 'Margen Bruto', 'Margen bruto de ventas', '', '%', 30, 20, 15),
                ('CUSTOMER_COUNT', 'Clientes Únicos', 'Clientes únicos del día', 'SELECT COUNT(DISTINCT customer_id) FROM sales_orders WHERE DATE(order_date) = DATE("now")', 'units', 0, 0, 0),
            ]
            
            for code, name, description, formula, unit, target, warning, critical in kpi_definitions_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO kpi_definitions (code, name, description, formula, unit, target_value, warning_threshold, critical_threshold) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (code, name, description, formula, unit, target, warning, critical))
                except Exception as e:
                    logger.error(f"Error insertando KPI {name}: {e}")
            
            # Configuraciones del sistema
            system_config_data = [
                ('system_name', 'AlmacénPro', 'STRING', 'GENERAL', 'Nombre del sistema'),
                ('system_version', '2.0', 'STRING', 'GENERAL', 'Versión del sistema'),
                ('default_currency', '1', 'INTEGER', 'GENERAL', 'Moneda por defecto'),
                ('default_warehouse', '1', 'INTEGER', 'GENERAL', 'Depósito por defecto'),
                ('default_tax_rate', '3', 'INTEGER', 'GENERAL', 'Alícuota de impuesto por defecto'),
                ('backup_auto_enabled', 'true', 'BOOLEAN', 'BACKUP', 'Backup automático habilitado'),
                ('backup_interval_hours', '24', 'INTEGER', 'BACKUP', 'Intervalo de backup en horas'),
                ('backup_max_files', '30', 'INTEGER', 'BACKUP', 'Máximo número de backups a mantener'),
                ('receipt_auto_print', 'false', 'BOOLEAN', 'RECEIPTS', 'Impresión automática de recibos'),
                ('receipt_copies', '1', 'INTEGER', 'RECEIPTS', 'Número de copias de recibo'),
                ('barcode_scanner_enabled', 'true', 'BOOLEAN', 'HARDWARE', 'Scanner de códigos habilitado'),
                ('scale_integration_enabled', 'false', 'BOOLEAN', 'HARDWARE', 'Integración con balanza habilitada'),
                ('cash_drawer_enabled', 'false', 'BOOLEAN', 'HARDWARE', 'Cajón de dinero habilitado'),
                ('low_stock_alert_days', '7', 'INTEGER', 'ALERTS', 'Días de anticipación para alerta de stock bajo'),
                ('expiry_alert_days', '30', 'INTEGER', 'ALERTS', 'Días de anticipación para alerta de vencimiento'),
                ('session_timeout_minutes', '480', 'INTEGER', 'SECURITY', 'Tiempo de expiración de sesión en minutos'),
                ('max_login_attempts', '5', 'INTEGER', 'SECURITY', 'Máximo número de intentos de login'),
                ('password_min_length', '6', 'INTEGER', 'SECURITY', 'Longitud mínima de contraseña'),
            ]
            
            for key, value, data_type, category, description in system_config_data:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO system_config (config_key, config_value, data_type, category, description) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (key, value, data_type, category, description))
                except Exception as e:
                    logger.error(f"Error insertando configuración {key}: {e}")
            
            logger.info("Datos iniciales insertados correctamente")
    
    @contextmanager
    def get_cursor(self):
        """Context manager para obtener cursor con manejo automático de transacciones"""
        with self._lock:
            cursor = self.connection.cursor()
            try:
                yield cursor
                self.connection.commit()
            except Exception as e:
                self.connection.rollback()
                logger.error(f"Error en transacción de base de datos: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Ejecutar consulta SELECT y retornar resultados como lista de diccionarios"""
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def execute_single(self, query: str, params: tuple = None) -> Optional[Dict]:
        """Ejecutar consulta SELECT y retornar un solo resultado como diccionario"""
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def execute_update(self, query: str, params: tuple = None) -> int:
        """Ejecutar consulta INSERT/UPDATE/DELETE y retornar filas afectadas"""
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Ejecutar INSERT y retornar ID del registro insertado"""
        with self.get_cursor() as cursor:
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            return cursor.lastrowid
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Obtener estadísticas completas de la base de datos"""
        try:
            stats = {}
            
            # Información básica del archivo
            if hasattr(self, 'db_path'):
                db_file = Path(self.db_path)
                if db_file.exists():
                    file_size = db_file.stat().st_size
                    stats['file_size_bytes'] = file_size
                    stats['file_size_mb'] = file_size / (1024 * 1024)
                    stats['file_size_gb'] = file_size / (1024 * 1024 * 1024)
            
            # Información de SQLite
            with self.get_cursor() as cursor:
                # Información de páginas
                cursor.execute("PRAGMA page_count")
                page_count = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA page_size")
                page_size = cursor.fetchone()[0]
                
                cursor.execute("PRAGMA freelist_count")
                free_pages = cursor.fetchone()[0]
                
                stats['total_pages'] = page_count
                stats['page_size'] = page_size
                stats['free_pages'] = free_pages
                stats['used_pages'] = page_count - free_pages
                stats['database_size_bytes'] = page_count * page_size
                stats['free_space_bytes'] = free_pages * page_size
                stats['used_space_bytes'] = (page_count - free_pages) * page_size
                
                # Conteo de registros por tabla
                tables_info = cursor.execute("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                """).fetchall()
                
                table_stats = {}
                total_records = 0
                
                for (table_name,) in tables_info:
                    try:
                        count_result = cursor.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
                        count = count_result[0] if count_result else 0
                        table_stats[table_name] = count
                        total_records += count
                    except Exception as e:
                        logger.error(f"Error contando registros en tabla {table_name}: {e}")
                        table_stats[table_name] = 0
                
                stats['table_counts'] = table_stats
                stats['total_records'] = total_records
                
                # Información de índices
                cursor.execute("""
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='index' AND name NOT LIKE 'sqlite_%'
                """)
                stats['total_indexes'] = cursor.fetchone()[0]
                
                # Información de triggers
                cursor.execute("""
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='trigger'
                """)
                stats['total_triggers'] = cursor.fetchone()[0]
                
                # Información de vistas
                cursor.execute("""
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='view'
                """)
                stats['total_views'] = cursor.fetchone()[0]
            
            return stats
            
        except Exception as e:
            logger.error(f"Error obteniendo estadísticas de base de datos: {e}")
            return {}
    
    def vacuum_database(self):
        """Optimizar base de datos ejecutando VACUUM"""
        try:
            with self._lock:
                self.connection.execute("VACUUM")
                logger.info("Base de datos optimizada con VACUUM")
        except Exception as e:
            logger.error(f"Error ejecutando VACUUM: {e}")
            raise
    
    def analyze_database(self):
        """Actualizar estadísticas de la base de datos"""
        try:
            with self._lock:
                self.connection.execute("ANALYZE")
                logger.info("Estadísticas de base de datos actualizadas")
        except Exception as e:
            logger.error(f"Error ejecutando ANALYZE: {e}")
            raise
    
    def close(self):
        """Cerrar conexión a la base de datos"""
        if self.connection:
            try:
                self.connection.close()
                self.connection = None
                logger.info("Conexión a base de datos cerrada")
            except Exception as e:
                logger.error(f"Error cerrando conexión: {e}")
    
    def __del__(self):
        """Cerrar conexión al destruir el objeto"""
        self.close()


# Ejemplo de uso y configuración
if __name__ == "__main__":
    # Esta sección se ejecutaría para crear la base de datos inicial
    
    class MockSettings:
        """Settings mock para testing"""
        def get_database_path(self):
            return "almacen_pro_complete.db"
        
        def get(self, key, default=None):
            config = {
                'database.type': 'sqlite'
            }
            return config.get(key, default)
    
    # Crear base de datos de ejemplo
    settings = MockSettings()
    db = CompleteDatabaseManager(settings)
    
    print("✅ Base de datos completa creada exitosamente")
    print(f"📊 Estadísticas: {db.get_database_stats()}")
    
    db.close()
cursor()
            for table_name, sql in all_tables.items():
                try:
                    cursor.execute(sql)
                    logger.info(f"Tabla {table_name} creada/verificada")
                except Exception as e:
                    logger.error(f"Error creando tabla {table_name}: {e}")
                    raise
    
    def create_all_indexes(self):
        """Crear todos los índices para optimización"""
        
        indexes = [
            # Índices para búsquedas comunes en productos
            "CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku)",
            "CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode)",
            "CREATE INDEX IF NOT EXISTS idx_products_name ON products(name)",
            "CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id)",
            "CREATE INDEX IF NOT EXISTS idx_products_active ON products(is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock ON products(current_stock)",
            "CREATE INDEX IF NOT EXISTS idx_products_type ON products(product_type)",
            
            # Índices para customers
            "CREATE INDEX IF NOT EXISTS idx_customers_code ON customers(customer_code)",
            "CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(first_name, last_name)",
            "CREATE INDEX IF NOT EXISTS idx_customers_tax_id ON customers(tax_id)",
            "CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email)",
            "CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone)",
            "CREATE INDEX IF NOT EXISTS idx_customers_status ON customers(status)",
            "CREATE INDEX IF NOT EXISTS idx_customers_category ON customers(customer_category_id)",
            
            # Índices para suppliers
            "CREATE INDEX IF NOT EXISTS idx_suppliers_code ON suppliers(supplier_code)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_name ON suppliers(legal_name)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_tax_id ON suppliers(tax_id)",
            "CREATE INDEX IF NOT EXISTS idx_suppliers_status ON suppliers(status)",
            
            # Índices para sales_orders
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_number ON sales_orders(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_date ON sales_orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_customer ON sales_orders(customer_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_status ON sales_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_cashier ON sales_orders(created_by)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_register ON sales_orders(cash_register_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_type ON sales_orders(order_type)",
            
            # Índices para sales_order_details
            "CREATE INDEX IF NOT EXISTS idx_sales_order_details_order ON sales_order_details(sales_order_id)",
            "CREATE INDEX IF NOT EXISTS idx_sales_order_details_product ON sales_order_details(product_id)",
            
            # Índices para purchase_orders
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_number ON purchase_orders(order_number)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date ON purchase_orders(order_date)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_supplier ON purchase_orders(supplier_id)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_status ON purchase_orders(status)",
            
            # Índices para stock_movements
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_product ON stock_movements(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_date ON stock_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_type ON stock_movements(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_warehouse ON stock_movements(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_movements_reference ON stock_movements(reference_type, reference_id)",
            
            # Índices para stock_by_location
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_product ON stock_by_location(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_warehouse ON stock_by_location(warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_lot ON stock_by_location(lot_number)",
            "CREATE INDEX IF NOT EXISTS idx_stock_by_location_expiration ON stock_by_location(expiration_date)",
            
            # Índices para account_movements
            "CREATE INDEX IF NOT EXISTS idx_account_movements_customer ON account_movements(customer_account_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_date ON account_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_type ON account_movements(movement_type)",
            "CREATE INDEX IF NOT EXISTS idx_account_movements_due_date ON account_movements(due_date)",
            
            # Índices para cash_sessions
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_register ON cash_sessions(cash_register_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_user ON cash_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_date ON cash_sessions(opened_at)",
            "CREATE INDEX IF NOT EXISTS idx_cash_sessions_status ON cash_sessions(status)",
            
            # Índices para cash_movements
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_session ON cash_movements(cash_session_id)",
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_date ON cash_movements(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_cash_movements_type ON cash_movements(movement_type)",
            
            # Índices para users y sesiones
            "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)",
            "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
            "CREATE INDEX IF NOT EXISTS idx_users_active ON users(active)",
            "CREATE INDEX IF NOT EXISTS idx_users_role ON users(role_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_user ON user_sessions(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_token ON user_sessions(session_token)",
            "CREATE INDEX IF NOT EXISTS idx_user_sessions_active ON user_sessions(active)",
            
            # Índices para promotions
            "CREATE INDEX IF NOT EXISTS idx_promotions_code ON promotions(code)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_dates ON promotions(start_date, end_date)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_status ON promotions(status)",
            "CREATE INDEX IF NOT EXISTS idx_promotions_coupon ON promotions(coupon_code)",
            
            # Índices para recipes y production
            "CREATE INDEX IF NOT EXISTS idx_recipes_product ON recipes(product_id)",
            "CREATE INDEX IF NOT EXISTS idx_recipes_status ON recipes(status)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_recipe ON production_orders(recipe_id)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_status ON production_orders(status)",
            "CREATE INDEX IF NOT EXISTS idx_production_orders_dates ON production_orders(planned_start_date, planned_end_date)",
            
            # Índices para notifications
            "CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_type ON notifications(notification_type_id)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_read ON notifications(read)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_created ON notifications(created_at)",
            "CREATE INDEX IF NOT EXISTS idx_notifications_expires ON notifications(expires_at)",
            
            # Índices para audit_log
            "CREATE INDEX IF NOT EXISTS idx_audit_log_table ON audit_log(table_name)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_record ON audit_log(table_name, record_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_user ON audit_log(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_timestamp ON audit_log(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_audit_log_operation ON audit_log(operation)",
            
            # Índices para system_logs
            "CREATE INDEX IF NOT EXISTS idx_system_logs_level ON system_logs(log_level)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_module ON system_logs(module)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_timestamp ON system_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_system_logs_user ON system_logs(user_id)",
            
            # Índices compuestos importantes
            "CREATE INDEX IF NOT EXISTS idx_products_category_active ON products(category_id, is_active)",
            "CREATE INDEX IF NOT EXISTS idx_products_stock_status ON products(current_stock, minimum_stock) WHERE track_stock = 1",
            "CREATE INDEX IF NOT EXISTS idx_sales_customer_date ON sales_orders(customer_id, order_date)",
            "CREATE INDEX IF NOT EXISTS idx_stock_product_warehouse ON stock_by_location(product_id, warehouse_id)",
            "CREATE INDEX IF NOT EXISTS idx_account_customer_type ON account_movements(customer_account_id, movement_type)",
            
            # Índices para fechas comunes en reportes
            "CREATE INDEX IF NOT EXISTS idx_sales_orders_date_status ON sales_orders(order_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_purchase_orders_date_status ON purchase_orders(order_date, status)",
            "CREATE INDEX IF NOT EXISTS idx_payments_date_method ON payments(payment_date, payment_method_id)",
            
            # Índices para códigos y números únicos
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_sku_unique ON products(sku) WHERE sku IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_products_barcode_unique ON products(barcode) WHERE barcode IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_customers_code_unique ON customers(customer_code) WHERE customer_code IS NOT NULL",
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_suppliers_code_unique ON suppliers(supplier_code) WHERE supplier_code IS NOT NULL",
        ]
        
        with self.connection:
            cursor = self.connection.cursor()
            for index_sql in indexes:
                try:
                    cursor.execute(index_sql)
                except Exception as e:
                    logger.error(f"Error creando índice: {e}")
    
    def create_all_triggers(self):
        """Crear triggers para automatización y integridad"""
        
        triggers = [
            # Trigger para actualizar timestamps
            '''
            CREATE TRIGGER IF NOT EXISTS update_products_timestamp 
            AFTER UPDATE ON products
            BEGIN
                UPDATE products SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_customers_timestamp 
            AFTER UPDATE ON customers
            BEGIN
                UPDATE customers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_suppliers_timestamp 
            AFTER UPDATE ON suppliers
            BEGIN
                UPDATE suppliers SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
            END
            ''',
            
            # Trigger para auditoría automática
            '''
            CREATE TRIGGER IF NOT EXISTS audit_products_insert 
            AFTER INSERT ON products
            BEGIN
                INSERT INTO audit_log (table_name, record_id, operation, new_values, user_id, timestamp)
                VALUES ('products', NEW.id, 'INSERT', 
                       json_object('name', NEW.name, 'sku', NEW.sku, 'sale_price', NEW.sale_price),
                       NEW.created_by, CURRENT_TIMESTAMP);
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS audit_products_update 
            AFTER UPDATE ON products
            BEGIN
                INSERT INTO audit_log (table_name, record_id, operation, old_values, new_values, user_id, timestamp)
                VALUES ('products', NEW.id, 'UPDATE',
                       json_object('name', OLD.name, 'sku', OLD.sku, 'sale_price', OLD.sale_price),
                       json_object('name', NEW.name, 'sku', NEW.sku, 'sale_price', NEW.sale_price),
                       NEW.updated_by, CURRENT_TIMESTAMP);
            END
            ''',
            
            # Trigger para mantener balance de cuentas corrientes
            '''
            CREATE TRIGGER IF NOT EXISTS update_customer_balance_insert
            AFTER INSERT ON account_movements
            BEGIN
                UPDATE customer_accounts 
                SET current_balance = current_balance + 
                    CASE WHEN NEW.movement_type = 'CHARGE' THEN NEW.amount ELSE -NEW.amount END,
                    last_charge_date = CASE WHEN NEW.movement_type = 'CHARGE' THEN DATE('now') ELSE last_charge_date END,
                    last_payment_date = CASE WHEN NEW.movement_type = 'PAYMENT' THEN DATE('now') ELSE last_payment_date END
                WHERE id = NEW.customer_account_id;
            END
            ''',
            
            # Trigger para actualizar stock cuando se mueve inventario
            '''
            CREATE TRIGGER IF NOT EXISTS update_stock_on_movement
            AFTER INSERT ON stock_movements
            BEGIN
                -- Actualizar stock del producto principal
                UPDATE products 
                SET current_stock = current_stock + 
                    CASE WHEN NEW.movement_type = 'IN' THEN NEW.quantity_moved 
                         ELSE -NEW.quantity_moved END
                WHERE id = NEW.product_id AND track_stock = 1;
                
                -- Actualizar stock por ubicación
                INSERT OR REPLACE INTO stock_by_location 
                (product_id, warehouse_id, storage_location_id, current_stock, lot_number, serial_number, expiration_date, last_movement_date)
                VALUES (
                    NEW.product_id, 
                    NEW.warehouse_id,
                    NEW.storage_location_id,
                    COALESCE((SELECT current_stock FROM stock_by_location 
                             WHERE product_id = NEW.product_id 
                             AND warehouse_id = NEW.warehouse_id 
                             AND COALESCE(storage_location_id, 0) = COALESCE(NEW.storage_location_id, 0)
                             AND COALESCE(lot_number, '') = COALESCE(NEW.lot_number, '')
                             AND COALESCE(serial_number, '') = COALESCE(NEW.serial_number, '')), 0) +
                    CASE WHEN NEW.movement_type = 'IN' THEN NEW.quantity_moved 
                         ELSE -NEW.quantity_moved END,
                    NEW.lot_number,
                    NEW.serial_number,
                    NEW.expiration_date,
                    CURRENT_TIMESTAMP
                );
            END
            ''',
            
            # Trigger para calcular totales de órdenes
            '''
            CREATE TRIGGER IF NOT EXISTS update_sales_order_total
            AFTER INSERT ON sales_order_details
            BEGIN
                UPDATE sales_orders 
                SET subtotal = (SELECT SUM(line_total) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    tax_amount = (SELECT SUM(tax_amount) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    total_amount = subtotal - discount_amount + tax_amount
                WHERE id = NEW.sales_order_id;
            END
            ''',
            
            '''
            CREATE TRIGGER IF NOT EXISTS update_sales_order_total_on_update
            AFTER UPDATE ON sales_order_details
            BEGIN
                UPDATE sales_orders 
                SET subtotal = (SELECT SUM(line_total) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    tax_amount = (SELECT SUM(tax_amount) FROM sales_order_details WHERE sales_order_id = NEW.sales_order_id),
                    total_amount = subtotal - discount_amount + tax_amount
                WHERE id = NEW.sales_order_id;
            END
            ''',
            
            # Trigger para actualizar contadores de uso de promociones
            '''
            CREATE TRIGGER IF NOT EXISTS update_promotion_usage
            AFTER INSERT ON promotion_usage
            BEGIN
                UPDATE promotions 
                SET usage_count = usage_count + 1
                WHERE id = NEW.promotion_id;
            END
            ''',
            
            # Trigger para verificar límites de crédito
            '''
            CREATE TRIGGER IF NOT EXISTS check_credit_limit
            BEFORE INSERT ON account_movements
            WHEN NEW.movement_type = 'CHARGE'
            BEGIN
                SELECT CASE 
                    WHEN (SELECT current_balance + NEW.amount FROM customer_accounts WHERE id = NEW.customer_account_id) > 
                         (SELECT credit_limit FROM customer_accounts WHERE id = NEW.customer_account_id)
                    THEN RAISE(ABORT, 'Credit limit exceeded')
                END;
            END
            ''',
        ]
        
        with self.connection:
            cursor = self.connection.