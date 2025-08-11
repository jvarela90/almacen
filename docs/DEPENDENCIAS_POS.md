# Sistema POS - Dependencias y Relaciones

## Arquitectura del Sistema POS

### Diagrama de Dependencias

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   UserManager   │    │ DatabaseManager │    │ ConfigSettings  │
│   (Autenticación)│    │ (Base de datos)  │    │ (Configuración) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ ProductManager  │    │  SalesManager   │    │FinancialManager │
│ (Productos)     │◄───│ (Ventas/POS)    │───►│ (Cajas/Pagos)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│CustomerManager  │    │  ReportManager  │    │InventoryManager │
│(Clientes/CRM)   │    │ (Reportes)      │    │ (Inventarios)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Managers del Sistema POS

#### SalesManager (Núcleo del POS)
**Ubicación**: `managers/sales_manager.py`
**Dependencias**:
- `DatabaseManager` - Para todas las operaciones de base de datos
- `ProductManager` - Para validar productos y actualizar stock
- `FinancialManager` - Para registrar movimientos de caja
- **Tablas utilizadas**:
  - `ventas` (tabla principal)
  - `detalle_ventas` (items de venta)
  - `pagos_venta` (métodos de pago)
  - `cuenta_corriente` (créditos de clientes)

**Métodos principales**:
- `create_sale()` - Crear nueva venta completa
- `cancel_sale()` - Cancelar venta y restaurar stock
- `process_return()` - Procesar devoluciones
- `get_sales_statistics()` - Estadísticas de ventas
- `get_daily_summary()` - Resumen diario

#### ProductManager (Catálogo)
**Ubicación**: `managers/product_manager.py`
**Dependencias**:
- `DatabaseManager`
- **Tablas utilizadas**:
  - `productos` (tabla principal)
  - `categorias` (clasificación)
  - `proveedores` (proveedores)
  - `movimientos_stock` (trazabilidad)

**Métodos principales**:
- `search_products()` - Búsqueda por código/nombre
- `get_product_by_barcode()` - Búsqueda por código de barras
- `create_product()` - Crear producto
- `update_stock()` - Actualizar stock con movimientos

#### FinancialManager (Gestión de Caja)
**Ubicación**: `managers/financial_manager.py`
**Dependencias**:
- `DatabaseManager`
- **Tablas utilizadas**:
  - `cajas` (configuración de cajas)
  - `sesiones_caja` (sesiones de trabajo)
  - `movimientos_caja` (movimientos de efectivo)

**Métodos principales**:
- `open_cash_session()` - Abrir sesión de caja
- `close_cash_session()` - Cerrar sesión de caja
- `record_sale_payment()` - Registrar pago de venta
- `get_session_summary()` - Resumen de sesión

#### CustomerManager (CRM)
**Ubicación**: `managers/customer_manager.py`
**Dependencias**:
- `DatabaseManager`
- **Tablas utilizadas**:
  - `clientes` (información de clientes)
  - `cuenta_corriente` (cuentas corrientes)

### Interface de Usuario POS

#### SalesWidget (Interfaz Principal)
**Ubicación**: `ui/widgets/sales_widget.py`
**Dependencias**:
- Todos los managers del sistema
- `PyQt5` para la interfaz
- **Componentes**:
  - Panel de búsqueda/scanner
  - Lista de productos
  - Carrito de compras
  - Panel de checkout
  - Selección de cliente
  - Métodos de pago

#### MainWindow (Contenedor Principal)
**Ubicación**: `ui/main_window.py`
**Dependencias**:
- `SalesWidget`
- `DashboardWidget`
- Todos los managers

### Flujo de Datos en una Venta

```
1. Usuario escanea/busca producto
   ↓
2. ProductManager.search_products() / get_product_by_barcode()
   ↓
3. Producto se agrega al carrito (UI)
   ↓
4. Usuario procede al checkout
   ↓
5. SalesManager.create_sale()
   ├── Validar stock (ProductManager)
   ├── Crear registro de venta (DB)
   ├── Crear detalles de venta (DB)
   ├── Actualizar stock (ProductManager.update_stock())
   ├── Registrar pagos (DB)
   ├── Si es efectivo: FinancialManager.record_sale_payment()
   └── Actualizar cuenta corriente si aplica (DB)
   ↓
6. Venta completada / Ticket generado
```

### Configuración del Sistema

#### Base de Datos
- **Archivo**: `data/almacen_pro.db` (SQLite)
- **Configuración**: `config/settings.py`
- **19 tablas** con relaciones completas
- **Foreign keys habilitadas**
- **Triggers automáticos** para auditoría

#### Configuraciones Importantes
```python
# config/settings.py
'sales': {
    'auto_print_ticket': False,
    'allow_negative_stock': False,
    'default_payment_method': 'EFECTIVO',
    'tax_included': True,
    'default_tax_rate': 21.0
}

'security': {
    'session_timeout': 480,  # minutos
    'max_login_attempts': 5,
    'lockout_duration': 15   # minutos
}
```

### Inicialización del Sistema

#### Secuencia de Carga (main.py)
1. **DatabaseManager** - Conexión a BD
2. **UserManager** - Sistema de usuarios
3. **ProductManager** - Catálogo de productos
4. **FinancialManager** - Sistema de cajas
5. **SalesManager** - Sistema de ventas (con deps anteriores)
6. **CustomerManager** - Sistema de clientes
7. **InventoryManager** - Gestión de inventarios
8. **ReportManager** - Sistema de reportes
9. **BackupManager** - Sistema de respaldos

### Errores Comunes y Soluciones

#### Error: "Usuario no encontrado"
- **Causa**: UserManager no inicializado
- **Solución**: Verificar orden de carga en main.py

#### Error: "Stock insuficiente"
- **Causa**: Validación en SalesManager.create_sale()
- **Solución**: Configurar `allow_negative_stock: true`

#### Error: "Sesión de caja no encontrada"
- **Causa**: FinancialManager requiere sesión activa
- **Solución**: Abrir sesión con `open_cash_session()`

#### Error: "Producto no encontrado"
- **Causa**: ProductManager.get_product_by_id() retorna None
- **Solución**: Verificar que el producto exista y esté activo

### Pruebas del Sistema

#### Suite de Pruebas
**Archivo**: `test_sistema_almacen.py`
**Cubre**:
- Inicialización de todos los managers
- Operaciones CRUD básicas
- Flujo completo de ventas
- Integridad referencial
- Pruebas de rendimiento

#### Ejecutar Pruebas
```bash
cd F:\almacen
python test_sistema_almacen.py
```

### Métricas de Rendimiento

- **Inicialización**: ~2-3 segundos
- **Búsqueda de productos**: <100ms
- **Creación de venta**: <500ms
- **Actualización de stock**: <200ms
- **Base de datos**: SQLite con WAL mode
- **Capacidad**: Hasta 100,000 productos
- **Concurrencia**: Sesiones múltiples soportadas

### Mantenimiento

#### Logs del Sistema
- **Ubicación**: `logs/`
- **Rotación**: Diaria
- **Niveles**: INFO, ERROR, DEBUG
- **Audit trail**: Tabla `auditoria`

#### Backups Automáticos
- **Frecuencia**: Cada 24 horas
- **Compresión**: 80-90% reducción
- **Ubicación**: `backups/`
- **Retención**: 30 días por defecto

### Escalabilidad

#### Límites Actuales
- **SQLite**: Recomendado hasta 1TB
- **Productos**: Sin límite práctico
- **Ventas diarias**: Hasta 10,000 transacciones
- **Usuarios concurrentes**: 5-10 (SQLite limitation)

#### Migración a Servidor
Para mayor escalabilidad, el sistema puede migrar a:
- **PostgreSQL** o **MySQL**
- **Servidor dedicado**
- **API REST** para múltiples puntos de venta
- **Replicación** para alta disponibilidad