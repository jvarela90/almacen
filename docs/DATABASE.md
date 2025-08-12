# Base de Datos - AlmacénPro v2.0

## 📋 Resumen Ejecutivo

AlmacénPro v2.0 utiliza una base de datos **SQLite** optimizada con más de 25 tablas normalizadas, sistema de migraciones con **Alembic**, triggers automáticos y vistas de análisis para reportes avanzados.

---

## 🏗️ Arquitectura de Base de Datos

### **Características Principales**
- ✅ **SQLite** con modo WAL para concurrencia
- ✅ **25+ tablas** normalizadas con integridad referencial
- ✅ **Triggers** para auditoría automática
- ✅ **Índices optimizados** para consultas frecuentes
- ✅ **Vistas de análisis** para reportes
- ✅ **Migraciones versionadas** con Alembic

---

## 📊 Esquema Principal

### **Tablas Principales**

#### **👥 Gestión de Usuarios**
```sql
usuarios          # Usuarios del sistema con roles
roles            # Roles y permisos granulares
sesiones_usuario # Control de sesiones activas
```

#### **🛒 Módulo de Ventas**
```sql
ventas           # Transacciones de venta
detalle_ventas   # Productos vendidos por transacción
clientes         # Base de datos de clientes B2B/B2C
pagos            # Registros de pagos recibidos
```

#### **📦 Gestión de Productos**
```sql
productos        # Catálogo de productos
categorias       # Categorización de productos
proveedores      # Base de datos de proveedores
compras          # Órdenes de compra
detalle_compras  # Productos comprados
```

#### **📋 Control de Inventario**
```sql
stock            # Existencias por almacén
movimientos_stock # Historial de movimientos
almacenes        # Ubicaciones de almacenamiento
transferencias   # Movimientos entre almacenes
```

#### **💰 Gestión Financiera**
```sql
cajas            # Cajas registradoras
sesiones_caja    # Sesiones de trabajo por caja
gastos           # Registro de gastos operativos
categorias_gasto # Categorización de gastos
cuentas_bancarias # Cuentas del negocio
```

---

## 🔄 Sistema de Migraciones

### **Alembic Configuration**

El sistema utiliza **Alembic** para gestionar cambios estructurales:

```bash
# Ver estado actual
python database/migrate.py current

# Aplicar migraciones pendientes
python database/migrate.py upgrade

# Crear nueva migración
python database/migrate.py create "Descripción del cambio"

# Ver historial
python database/migrate.py history
```

### **Migraciones Implementadas**
1. `001_initial_schema.py` - Esquema base completo
2. `002_add_detalle_ventas_created_at.py` - Timestamps en ventas
3. `003_add_audit_columns.py` - Columnas de auditoría

---

## 📈 Vistas de Análisis

### **Vistas para Reportes**
```sql
-- Ventas diarias consolidadas
CREATE VIEW vista_ventas_diarias AS
SELECT DATE(fecha_venta) as fecha, SUM(total) as total_dia
FROM ventas WHERE activo = 1
GROUP BY DATE(fecha_venta);

-- Top productos más vendidos
CREATE VIEW vista_productos_top AS
SELECT p.nombre, SUM(dv.cantidad) as total_vendido
FROM productos p
JOIN detalle_ventas dv ON p.id = dv.producto_id
GROUP BY p.id ORDER BY total_vendido DESC;

-- Análisis de clientes
CREATE VIEW vista_analisis_clientes AS
SELECT c.*, COUNT(v.id) as total_compras,
       SUM(v.total) as total_gastado
FROM clientes c
LEFT JOIN ventas v ON c.id = v.cliente_id
GROUP BY c.id;
```

---

## ⚡ Optimizaciones Implementadas

### **Configuración SQLite**
```sql
PRAGMA foreign_keys = ON;        -- Integridad referencial
PRAGMA journal_mode = WAL;       -- Concurrencia mejorada
PRAGMA synchronous = NORMAL;     -- Balance rendimiento/seguridad
PRAGMA cache_size = 10000;       -- Cache 10MB
PRAGMA temp_store = MEMORY;      -- Tablas temp en memoria
```

### **Índices Estratégicos**
```sql
-- Búsquedas de productos
CREATE INDEX idx_productos_nombre ON productos(nombre);
CREATE INDEX idx_productos_codigo ON productos(codigo);

-- Consultas de ventas
CREATE INDEX idx_ventas_fecha ON ventas(fecha_venta);
CREATE INDEX idx_ventas_cliente ON ventas(cliente_id);

-- Control de stock
CREATE INDEX idx_stock_producto ON stock(producto_id);
CREATE INDEX idx_movimientos_fecha ON movimientos_stock(fecha_movimiento);
```

---

## 🛠️ Herramientas de Gestión

### **DBeaver Integration**
```python
# Configuración para DBeaver
import sqlite3

def connect_dbeaver():
    conn = sqlite3.connect('data/almacen_pro.db')
    conn.execute('PRAGMA foreign_keys = ON')
    return conn
```

### **Backup y Restauración**
```python
# Comando de backup
python -m utils.backup_manager --create

# Restaurar desde backup
python -m utils.backup_manager --restore backup_20250811.db.gz
```

---

## 🔒 Seguridad y Auditoría

### **Triggers de Auditoría**
```sql
-- Auditoría automática en ventas
CREATE TRIGGER tr_ventas_audit
    AFTER UPDATE ON ventas
BEGIN
    INSERT INTO auditoria (tabla, accion, registro_id, usuario, fecha)
    VALUES ('ventas', 'UPDATE', NEW.id, NEW.usuario_id, datetime('now'));
END;
```

### **Control de Permisos**
- Acceso a nivel de aplicación con sistema de roles
- Validación de operaciones por tipo de usuario
- Logging completo de operaciones críticas

---

## 📋 Mantenimiento

### **Comandos de Mantenimiento**
```sql
-- Verificar integridad
PRAGMA integrity_check;

-- Análisis de estadísticas
ANALYZE;

-- Compactación (en caso necesario)
VACUUM;
```

### **Limpieza Automática**
- Logs rotativos con retención de 30 días
- Backups automáticos con retención configurable
- Archivado de datos históricos

---

## 🚀 Próximas Mejoras

### **Performance**
- Particionado de tablas históricas
- Optimización de consultas complejas
- Cache de consultas frecuentes

### **Funcionalidad**
- Replicación para alta disponibilidad
- Integración con sistemas externos
- Dashboard en tiempo real

---

*Actualizado: 11 de agosto de 2025*  
*Versión: 2.0*