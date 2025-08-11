# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

AlmacénPro v2.0 is a comprehensive ERP/POS system for warehouse and retail management, built with Python 3.8+ and PyQt5. It features a modular architecture with specialized managers for different business domains and includes collaborative management capabilities for multi-partner businesses.

## ESTADO ACTUAL DEL SISTEMA (ACTUALIZADO 2024)
- ✅ Base de datos configurada con 19 tablas funcionales
- ✅ 10 gestores (managers) completamente integrados
- ✅ Sistema de autenticación y roles funcionando
- ✅ Interfaz de usuario conectada a datos reales
- ✅ Sistema de configuración basado en archivos
- ✅ Suite de pruebas integrales implementada
- ✅ Eliminación de valores hardcodeados completada
- ✅ **NUEVAS FUNCIONALIDADES IMPLEMENTADAS:**
  - ✅ Sistema de procesamiento de pagos avanzado (PaymentDialog)
  - ✅ Generador de reportes con exportación multi-formato (ReportDialog)
  - ✅ Sistema de formateo profesional de datos (Formatters)
  - ✅ Exportación a Excel/PDF/CSV con formateo automático (Exporters)
  - ✅ Sistema de impresión de tickets profesional (TicketPrinter)
  - ✅ CRM empresarial avanzado con análisis de clientes (CustomersWidget)
  - ✅ Dashboard dinámico con datos en tiempo real
  - ✅ Vistas basadas en roles (Admin/Gerente/Depósito/Vendedor)
  - ✅ Actualización automática de datos cada 60 segundos
  - ✅ Integración completa backend-frontend

## Quick Start Commands

### Running the Application
```bash
# Main application entry point
python main.py
```

### Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Install required modules for current system
pip install bcrypt

# Run comprehensive system test
python test_sistema_almacen.py

# Development tools (optional)
pip install pytest black flake8

# Code formatting
black .

# Code linting
flake8 --max-line-length=100 --exclude=venv
```

### Database Operations
The system automatically handles database setup and migrations. 
- Database file: `data/almacen_pro.db` (configurable via settings)
- Test database: `data/test_almacen_pro.db` (created during tests)
- 19 tables with complete relationships and foreign key constraints
- Automatic indexing and optimization
- Built-in backup and restore functionality

## Architecture Overview

### Core Modules Structure

**Database Layer** (`database/`)
- `manager.py` - Central database manager with SQLite operations
- `models.py` - Database table definitions and schemas

**Business Logic** (`managers/`)
- `user_manager.py` - User authentication and role management
- `product_manager.py` - Product catalog and inventory
- `sales_manager.py` - Sales processing and transactions
- `purchase_manager.py` - Purchase orders and supplier management
- `provider_manager.py` - Supplier relationship management
- `customer_manager.py` - Customer relationship management (CRM)
- `financial_manager.py` - Financial operations and cash register management
- `inventory_manager.py` - Advanced inventory control with multi-warehouse support
- `report_manager.py` - Analytics and reporting

**User Interface** (`ui/`)
- `main_window.py` - Ventana principal con navegación por tabs y vistas basadas en roles
- `dialogs/` - Diálogos modales especializados:
  - `payment_dialog.py` - Procesamiento avanzado de pagos con múltiples métodos
  - `report_dialog.py` - Generador de reportes con filtros y exportación
  - `add_product_dialog.py` - Gestión completa de productos
  - `customer_dialog.py` - Gestión de clientes con validación
- `widgets/` - Componentes reutilizables:
  - `customers_widget.py` - CRM empresarial con dashboard y analytics
  - `dashboard_widget.py` - Dashboard principal con datos en tiempo real
  - `sales_widget.py` - Interfaz POS integrada con pagos y tickets

**Utilities** (`utils/`)
- `backup_manager.py` - Automated backup system with compression
- `notifications.py` - System-wide notification management
- `audit_logger.py` - Audit trail and activity logging system
- `validators.py` - Comprehensive data validation framework
- `formatters.py` - Sistema de formateo profesional para datos (números, fechas, texto, estados)
- `exporters.py` - Exportación multi-formato (Excel/PDF/CSV) con formateo automático
- `ticket_printer.py` - Sistema de impresión de tickets y comprobantes profesionales
- `helpers.py` - Common utility functions

**Configuration** (`config/`)
- `settings.py` - Centralized configuration management
- `config.json` - Runtime configuration file

### Application Flow

1. **Initialization**: `main.py` creates `AlmacenProApp` class
2. **Component Loading**: `InitializationThread` loads all managers asynchronously
3. **Authentication**: `LoginDialog` authenticates users via `UserManager`
4. **Main Interface**: `MainWindow` provides tabbed interface with role-based access
5. **Business Operations**: Each tab connects to appropriate manager for business logic

### Key Design Patterns

- **Manager Pattern**: Business logic separated into specialized managers
- **Observer Pattern**: PyQt signals/slots for component communication
- **Factory Pattern**: Dynamic creation of UI widgets based on user roles
- **Command Pattern**: Database operations wrapped in transaction methods

## Database Architecture

The system uses a normalized SQLite database with 50+ tables covering:
- User management and authentication
- Product catalog with variants and attributes
- Multi-warehouse inventory control with location tracking
- Sales and purchase transaction processing
- Customer relationship management (CRM) with categories
- Financial operations including cash register management
- Comprehensive audit trails and system logging
- Automated backup and restore functionality

Key database features:
- Foreign key constraints enabled
- Automatic indexing for performance
- Transaction-based operations
- Built-in backup and restore functionality

## Configuration Management

Configuration is handled through:
- `config.json` - Runtime settings (created automatically on first run)
- `config/settings.py` - Default configuration values and validation
- Environment variables for deployment settings

## Backup System

The application includes a sophisticated backup system:
- Automatic scheduled backups (configurable interval)
- Compressed backup files (80-90% size reduction)
- Backup verification and integrity checking
- GUI-based restore functionality
- Configurable retention policies

## Development Guidelines

### Code Organization
- Follow modular architecture - keep managers focused on single responsibility
- UI components should be in appropriate widget/dialog directories
- Database operations should go through `DatabaseManager`
- Use logging extensively for debugging and monitoring

### Adding New Features
1. Create or extend appropriate manager in `managers/`
2. Add database changes via `DatabaseManager.create_tables()`
3. Create UI components in `ui/widgets/` or `ui/dialogs/`
4. Update `MainWindow` to include new functionality
5. Add configuration options to `settings.py` if needed
6. Implement data validation using `utils/validators.py`
7. Add audit logging for important operations using `audit_logger.py`

### Database Changes
- All database operations should use the `DatabaseManager` class
- Use parameterized queries to prevent SQL injection
- Wrap operations in transactions for data consistency
- Add proper error handling and logging
- Implement audit trails for critical data changes using `audit_logger.py`
- Use validation framework in `validators.py` before database operations

### UI Development
- Follow existing PyQt5 patterns and styling
- Use signals/slots for component communication
- Implement proper validation in dialogs
- Maintain consistent styling using global CSS

## Testing

The codebase supports testing with pytest:
- Unit tests for managers and utilities
- UI tests using pytest-qt
- Database integration tests

## User Roles and Permissions

The system supports role-based access control:
- **Admin**: Full system access, user management, configuration
- **Manager**: Operations management, reporting, some configuration
- **Employee**: Daily operations, limited reporting
- **Collaborator**: Partner-specific access for multi-partner businesses

## Logging

Comprehensive logging system:
- Main log: `logs/almacen_pro_YYYYMMDD.log`
- Critical errors: `logs/critical_errors.log`
- Backup operations logged separately

## Dependencies

Key dependencies (see `requirements.txt` for complete list):
- PyQt5 5.15.4+ for GUI
- sqlite3 (built-in) for database
- reportlab for PDF generation
- Pillow for image processing
- cryptography for security
- python-barcode for barcode generation

## Deployment Notes

- Minimum Python 3.8
- Cross-platform (Windows, macOS, Linux)
- Self-contained SQLite database
- Configurable through `config.json`
- Backup system stores files in `backups/` directory
- Logs stored in `logs/` directory with date-based rotation
- Database supports WAL mode for better concurrent access

## Sistema POS (Point of Sale)

### Componentes Principales del POS
- **SalesManager**: Gestión completa de ventas y transacciones
- **ProductManager**: Catálogo de productos y gestión de stock
- **CustomerManager**: Gestión de clientes y CRM
- **FinancialManager**: Manejo de cajas y sesiones de caja
- **UI Widgets**: Interfaz de usuario especializada para POS

### Flujo de Operaciones POS
1. Autenticación de usuario (UserManager)
2. Apertura de sesión de caja (FinancialManager)
3. Búsqueda y selección de productos (ProductManager)
4. Procesamiento de venta (SalesManager)
5. Gestión de pagos (FinancialManager)
6. Actualización de stock automática (ProductManager)
7. Generación de comprobantes (ReportManager)

### Relaciones Entre Managers
- **SalesManager** ↔ **ProductManager**: Actualización automática de stock
- **SalesManager** ↔ **CustomerManager**: Asociación de ventas con clientes
- **SalesManager** ↔ **FinancialManager**: Registro de movimientos de caja
- **FinancialManager** ↔ **UserManager**: Control de sesiones por usuario

## Testing and Validation

Sistema de pruebas integral:
- `test_sistema_almacen.py` - Suite completa de pruebas de integración
- `test_new_features.py` - Tests específicos para nuevas funcionalidades
- Pruebas de todos los managers y sus relaciones
- Pruebas de interfaz de usuario
- Pruebas de rendimiento y carga
- Verificación de integridad de base de datos
- Tests de exportación y formateo de datos
- Tests de sistema de pagos y tickets

## NUEVAS FUNCIONALIDADES IMPLEMENTADAS (2024)

### Sistema de Procesamiento de Pagos Avanzado
- **Archivo**: `ui/dialogs/payment_dialog.py`
- **Funcionalidad**: Diálogo completo para procesamiento de pagos
- **Características**:
  - 8 métodos de pago (Efectivo, Tarjetas, Transferencias, etc.)
  - Validación de límites de crédito automática  
  - Cálculo de cambio en tiempo real
  - Soporte para pagos mixtos
  - Integración con datos de clientes

### Generador de Reportes Profesional
- **Archivo**: `ui/dialogs/report_dialog.py`
- **Funcionalidad**: Configurador avanzado de reportes
- **Características**:
  - 7 tipos de reportes predefinidos
  - Sistema de filtros avanzados
  - Exportación a Excel/PDF/CSV
  - Vista previa en tiempo real
  - Configuración de rangos de fechas

### Sistema de Formateo Profesional
- **Archivo**: `utils/formatters.py`
- **Funcionalidad**: Formateo consistente de datos
- **Características**:
  - Formateo de moneda argentina
  - Formateo de fechas y tiempo relativo
  - Formateo de teléfonos y CUIT
  - Estados con colores y emojis
  - Validación y limpieza de texto

### Sistema de Exportación Multi-formato  
- **Archivo**: `utils/exporters.py`
- **Funcionalidad**: Exportación profesional de datos
- **Características**:
  - Soporte Excel (.xlsx) con estilos
  - Generación PDF con tablas formateadas
  - CSV con codificación UTF-8
  - Detección automática de formato
  - Funciones de conveniencia

### Sistema de Impresión de Tickets
- **Archivo**: `utils/ticket_printer.py`  
- **Funcionalidad**: Generación e impresión de comprobantes
- **Características**:
  - Formato profesional de 42 caracteres
  - Headers personalizables de empresa
  - Detalle completo de productos y pagos
  - Vista previa antes de imprimir
  - Guardado en archivos de texto
  - Soporte multi-plataforma

### CRM Empresarial Avanzado
- **Archivo**: `ui/widgets/customers_widget.py`
- **Funcionalidad**: Gestión completa de relaciones con clientes  
- **Características**:
  - Dashboard con métricas de clientes
  - Clasificación automática de clientes
  - Análisis de top clientes por período
  - Gestión de cuenta corriente
  - Exportación de listas de clientes

### Interfaz Principal Mejorada
- **Archivo**: `ui/main_window.py` (actualizado)
- **Funcionalidad**: Ventana principal con nuevas integraciones
- **Características**:
  - Vistas basadas en roles de usuario
  - Dashboard dinámico con datos reales
  - Actualización automática cada 60 segundos
  - Botones de acceso rápido a reportes
  - Integración completa de todos los sistemas

### Sistema de Roles y Permisos Mejorado
- **Funcionalidad**: Control de acceso granular por rol
- **Características**:
  - **ADMINISTRADOR**: Acceso completo al sistema
  - **GERENTE**: Gestión operativa completa sin administración total
  - **DEPÓSITO**: Solo productos, stock y compras
  - **VENDEDOR**: Solo ventas, clientes (consulta) y tickets
  - Tabs habilitados/deshabilitados según rol
  - Mensajes contextuales por rol

### Funcionalidades en Tiempo Real
- **Funcionalidad**: Actualización automática de datos
- **Características**:
  - Timer de actualización cada 60 segundos
  - Dashboard con métricas dinámicas
  - Refresh automático de productos y clientes
  - Notificaciones de estado en tiempo real
  - Integración de callbacks entre componentes

## ARQUITECTURA MVC MODERNA (IMPLEMENTADA 2025)

### Estructura MVC Completa

**MIGRACIÓN COMPLETADA AL 100%** - El sistema AlmacénPro v2.0 ahora utiliza arquitectura MVC moderna:

```
almacen_pro/
├── main_mvc.py                # 🚀 Punto de entrada MVC (PRINCIPAL)
├── main.py                    # 🚀 Punto de entrada original (respaldo)

├── models/                    # 📊 CAPA DE DATOS (MVC)
│   ├── base_model.py          # Modelo base con señales PyQt
│   ├── entities.py            # Entidades de negocio (dataclasses)
│   ├── sales_model.py         # Modelo especializado ventas
│   └── customer_model.py      # Modelo especializado clientes

├── views/                     # 🎨 CAPA DE PRESENTACIÓN (MVC)
│   ├── forms/                 # Formularios principales (.ui)
│   │   ├── sales_widget.ui    # 🛒 Punto de venta completo
│   │   └── customers_widget.ui # 👥 Gestión clientes CRM
│   ├── dialogs/               # 💬 Diálogos modales (.ui)
│   │   ├── login_dialog.ui          # 🔐 Login con validación
│   │   ├── customer_dialog.ui       # 👤 Gestión cliente avanzada
│   │   ├── payment_dialog.ui        # 💳 Procesamiento pagos
│   │   └── [10 más archivos .ui]    # Interfaces completas
│   └── widgets/               # 🧩 Widgets principales (.ui)
│       ├── dashboard_widget.ui      # 📊 Dashboard ejecutivo
│       ├── stock_widget.ui          # 📦 Gestión inventario
│       └── [8 más archivos .ui]     # Componentes especializados

├── controllers/               # 🎮 CAPA DE CONTROL (MVC)
│   ├── base_controller.py     # Controlador base con funcionalidad común
│   ├── main_controller.py     # Controlador ventana principal
│   ├── sales_controller.py    # Controlador módulo ventas
│   └── customers_controller.py # Controlador módulo clientes

├── managers/                  # 📋 LÓGICA DE NEGOCIO (preservada)
│   ├── [15+ managers]         # Managers especializados existentes
│   └── predictive_analysis_manager.py # Análisis predictivo ML

├── utils/                     # 🛠️ UTILIDADES
│   ├── style_manager.py       # 🎨 Gestión estilos CSS
│   ├── backup_manager.py      # 💾 Sistema backup automático
│   └── validators.py          # ✅ Validadores datos

└── database/                  # 🗄️ GESTIÓN BASE DE DATOS
    ├── scripts/
    │   └── schema_export.sql  # Schema completo DBeaver (20KB)
    └── manager.py             # Gestor principal BD (50+ tablas)
```

### Patrón MVC Implementado

| **Capa** | **Responsabilidad** | **Implementación** | **Archivos** |
|----------|-------------------|-------------------|--------------|
| **Model** | Lógica de datos y estado | BaseModel + modelos especializados | 4 archivos Python |
| **View** | Interfaces de usuario | Archivos .ui cargados dinámicamente | 24 archivos .ui |
| **Controller** | Coordinación y lógica | BaseController + controladores | 4 archivos Python |

### Desarrollo MVC - Guidelines

#### 1. **Crear Nueva Funcionalidad MVC**

```python
# 1. Crear modelo de datos (si es necesario)
# models/mi_nuevo_modelo.py
from models.base_model import BaseModel
from dataclasses import dataclass

@dataclass
class MiEntidad:
    id: int
    nombre: str
    activo: bool

class MiNuevoModelo(BaseModel):
    def __init__(self):
        super().__init__()
        # Lógica del modelo

# 2. Crear interfaz .ui con Qt Designer
# views/dialogs/mi_nuevo_dialog.ui
# - Usar naming conventions: btnGuardar, txtNombre, cmbCategoria
# - Aplicar estilos CSS en el archivo .ui
# - Configurar tab order y shortcuts

# 3. Crear controlador
# controllers/mi_nuevo_controller.py
from controllers.base_controller import BaseController

class MiNuevoController(BaseController):
    def get_ui_file_path(self) -> str:
        return "views/dialogs/mi_nuevo_dialog.ui"
    
    def setup_ui(self):
        # Configurar elementos específicos de la UI
        pass
    
    def connect_signals(self):
        # Conectar señales específicas del controlador
        pass
```

#### 2. **Carga Dinámica de Interfaces**

```python
# En BaseController - NO modificar
def load_ui(self):
    ui_path = self.get_ui_file_path()
    uic.loadUi(ui_path, self)  # Carga runtime, NO genera .py
    self.ui_loaded = True
```

#### 3. **Comunicación Entre Componentes**

```python
# En BaseModel - usar señales PyQt
class BaseModel(QObject):
    data_changed = pyqtSignal()
    error_occurred = pyqtSignal(str)
    loading_started = pyqtSignal()
    loading_finished = pyqtSignal()

# En controladores - conectar señales
def connect_signals(self):
    self.mi_modelo.data_changed.connect(self.on_data_changed)
    self.btnGuardar.clicked.connect(self.on_save_clicked)
```

#### 4. **Estilos CSS en Archivos .ui**

```xml
<!-- En archivo .ui, dentro de <property name="styleSheet"> -->
<string>
QGroupBox {
    font-weight: bold;
    border: 2px solid #cccccc;
    border-radius: 5px;
}

QPushButton {
    background-color: #3498db;
    color: white;
    border-radius: 4px;
    padding: 8px 16px;
}
</string>
```

### Debugging MVC

#### Logs Especializados MVC

```bash
# Logs de la aplicación MVC
logs/almacen_pro_mvc_YYYYMMDD.log

# Buscar problemas específicos:
grep "ERROR" logs/almacen_pro_mvc_*.log
grep "BaseController" logs/almacen_pro_mvc_*.log
grep "load_ui" logs/almacen_pro_mvc_*.log
```

#### Validación de Estructura MVC

```bash
# Ejecutar test de validación MVC
python test_mvc_simple.py

# Verificar que todas las .ui se cargan correctamente
python -c "
from PyQt5 import uic
import os
for root, dirs, files in os.walk('views'):
    for file in files:
        if file.endswith('.ui'):
            print(f'Validando: {file}')
            uic.loadUi(os.path.join(root, file))
print('✅ Todas las interfaces .ui son válidas')
"
```

### Extensión del Sistema MVC

#### Agregar Nuevo Widget

1. **Diseñar interfaz** con Qt Designer → `views/widgets/mi_widget.ui`
2. **Crear controlador** → `controllers/mi_widget_controller.py`
3. **Integrar en main_controller** → Agregar tab o componente
4. **Configurar managers** → Conectar lógica de negocio existente

#### Modificar Interfaz Existente

1. **Abrir .ui en Qt Designer** (NO editar manualmente el XML)
2. **Hacer cambios visuales** → Widgets, layouts, propiedades
3. **Guardar archivo .ui** → Los cambios se aplican automáticamente
4. **Actualizar controlador** si es necesario → Nuevas señales o widgets

### Troubleshooting MVC

#### Errores Comunes

```bash
# 1. Archivo .ui no encontrado
FileNotFoundError: Archivo UI no encontrado: views/...
# Solución: Verificar ruta en get_ui_file_path()

# 2. Widget no encontrado en .ui
AttributeError: 'MiController' object has no attribute 'btnGuardar'
# Solución: Verificar objectName en Qt Designer

# 3. Error de metaclass
TypeError: metaclass conflict
# Solución: NO heredar de ABC en BaseController

# 4. Import error QShortcut
ImportError: cannot import name 'QShortcut'
# Solución: Import desde QtWidgets, no QtGui
```

### Performance MVC

La arquitectura MVC implementada incluye:

- ✅ **Carga diferida** de datos (defer_operation)
- ✅ **Threading** para operaciones pesadas
- ✅ **Caché inteligente** en modelos
- ✅ **Validación eficiente** antes de operaciones de BD
- ✅ **Logging optimizado** para debugging
- ✅ **Memory management** automático en BaseController

### COMANDOS MVC PRINCIPALES

```bash
# Ejecutar aplicación MVC
python main_mvc.py

# Validar estructura MVC
python test_mvc_simple.py

# Generar interfaces adicionales
python generate_ui_simple.py

# Abrir Qt Designer para editar interfaces
designer views/dialogs/mi_dialog.ui
```