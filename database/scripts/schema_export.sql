-- Schema de AlmacénPro v2.0 - Exportado automáticamente
-- Fecha: 2024-11-11
-- Base de datos: almacen_pro.db
-- Arquitectura: MVC con Qt Designer

-- ============================================================================
-- INFORMACIÓN DEL SISTEMA
-- ============================================================================

/*
AlmacénPro v2.0 - Sistema ERP/POS Completo
- Arquitectura MVC (Model-View-Controller)
- Interfaces con Qt Designer
- Base de datos SQLite normalizada
- Más de 50 tablas con relaciones complejas
*/

-- ============================================================================
-- CONFIGURACIÓN DE SQLite
-- ============================================================================

PRAGMA foreign_keys = ON;
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 10000;
PRAGMA temp_store = MEMORY;

-- ============================================================================
-- USUARIOS Y ROLES
-- ============================================================================

-- Tabla de roles del sistema
CREATE TABLE IF NOT EXISTS roles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(50) UNIQUE NOT NULL,
    descripcion TEXT,
    permisos TEXT,
    activo BOOLEAN DEFAULT 1,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    creado_por INTEGER,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_por INTEGER,
    FOREIGN KEY (creado_por) REFERENCES usuarios(id)
);

-- Tabla de usuarios
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100) UNIQUE,
    nombre_completo VARCHAR(100) NOT NULL,
    telefono VARCHAR(20),
    rol_id INTEGER,
    activo BOOLEAN DEFAULT 1,
    ultimo_acceso TIMESTAMP,
    intentos_fallidos INTEGER DEFAULT 0,
    bloqueado_hasta TIMESTAMP,
    configuracion TEXT DEFAULT '{}',
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (rol_id) REFERENCES roles(id)
);

-- ============================================================================
-- GESTIÓN DE PRODUCTOS E INVENTARIO
-- ============================================================================

-- Tabla de categorías
CREATE TABLE IF NOT EXISTS categorias (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT,
    categoria_padre_id INTEGER,
    activo BOOLEAN DEFAULT 1,
    orden INTEGER DEFAULT 0,
    imagen TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_padre_id) REFERENCES categorias(id)
);

-- Tabla de proveedores
CREATE TABLE IF NOT EXISTS proveedores (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    contacto VARCHAR(100),
    email VARCHAR(100),
    telefono VARCHAR(20),
    direccion TEXT,
    ciudad VARCHAR(100),
    documento VARCHAR(50),
    tipo_documento VARCHAR(20) DEFAULT 'RUT',
    activo BOOLEAN DEFAULT 1,
    observaciones TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de productos
CREATE TABLE IF NOT EXISTS productos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion TEXT,
    precio DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    costo DECIMAL(12,2) DEFAULT 0.00,
    stock_actual INTEGER DEFAULT 0,
    stock_minimo INTEGER DEFAULT 0,
    stock_maximo INTEGER DEFAULT 1000,
    categoria_id INTEGER,
    proveedor_id INTEGER,
    unidad_medida VARCHAR(20) DEFAULT 'UNIDAD',
    codigo_barras VARCHAR(100),
    imagen TEXT,
    activo BOOLEAN DEFAULT 1,
    gravable BOOLEAN DEFAULT 1,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (categoria_id) REFERENCES categorias(id),
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id)
);

-- ============================================================================
-- GESTIÓN DE CLIENTES Y CRM
-- ============================================================================

-- Tabla de clientes
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    email VARCHAR(100),
    telefono VARCHAR(20),
    direccion TEXT,
    ciudad VARCHAR(100),
    documento VARCHAR(50),
    tipo_documento VARCHAR(20) DEFAULT 'DNI',
    tipo_cliente VARCHAR(20) DEFAULT 'MINORISTA',
    limite_credito DECIMAL(12,2) DEFAULT 0.00,
    saldo_actual DECIMAL(12,2) DEFAULT 0.00,
    descuento_porcentual DECIMAL(5,2) DEFAULT 0.00,
    activo BOOLEAN DEFAULT 1,
    fecha_nacimiento DATE,
    ultima_compra TIMESTAMP,
    total_compras DECIMAL(12,2) DEFAULT 0.00,
    numero_compras INTEGER DEFAULT 0,
    
    -- Campos CRM avanzado
    origen VARCHAR(50) DEFAULT 'DIRECTO',
    segmento VARCHAR(50) DEFAULT 'REGULAR',
    estado VARCHAR(50) DEFAULT 'ACTIVO',
    observaciones TEXT,
    
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- SISTEMA DE VENTAS
-- ============================================================================

-- Tabla de ventas
CREATE TABLE IF NOT EXISTS ventas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero VARCHAR(50) UNIQUE NOT NULL,
    cliente_id INTEGER,
    usuario_id INTEGER NOT NULL,
    fecha_venta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subtotal DECIMAL(12,2) DEFAULT 0.00,
    descuento DECIMAL(12,2) DEFAULT 0.00,
    impuestos DECIMAL(12,2) DEFAULT 0.00,
    total DECIMAL(12,2) DEFAULT 0.00,
    estado VARCHAR(20) DEFAULT 'PENDIENTE',
    tipo_venta VARCHAR(20) DEFAULT 'CONTADO',
    metodo_pago VARCHAR(50) DEFAULT 'EFECTIVO',
    observaciones TEXT,
    facturada BOOLEAN DEFAULT 0,
    numero_factura VARCHAR(50),
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de detalles de venta
CREATE TABLE IF NOT EXISTS detalles_venta (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    precio_unitario DECIMAL(12,2) NOT NULL,
    descuento_porcentaje DECIMAL(5,2) DEFAULT 0.00,
    descuento_monto DECIMAL(12,2) DEFAULT 0.00,
    subtotal DECIMAL(12,2) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- ============================================================================
-- SISTEMA DE COMPRAS
-- ============================================================================

-- Tabla de compras
CREATE TABLE IF NOT EXISTS compras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero VARCHAR(50) UNIQUE NOT NULL,
    proveedor_id INTEGER NOT NULL,
    usuario_id INTEGER NOT NULL,
    fecha_compra TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    subtotal DECIMAL(12,2) DEFAULT 0.00,
    descuento DECIMAL(12,2) DEFAULT 0.00,
    impuestos DECIMAL(12,2) DEFAULT 0.00,
    total DECIMAL(12,2) DEFAULT 0.00,
    estado VARCHAR(20) DEFAULT 'PENDIENTE',
    observaciones TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Tabla de detalles de compra
CREATE TABLE IF NOT EXISTS detalles_compra (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    compra_id INTEGER NOT NULL,
    producto_id INTEGER NOT NULL,
    cantidad INTEGER NOT NULL DEFAULT 1,
    precio_unitario DECIMAL(12,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
    FOREIGN KEY (producto_id) REFERENCES productos(id)
);

-- ============================================================================
-- SISTEMA DE PAGOS
-- ============================================================================

-- Tabla de pagos
CREATE TABLE IF NOT EXISTS pagos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venta_id INTEGER,
    cliente_id INTEGER,
    monto DECIMAL(12,2) NOT NULL,
    metodo_pago VARCHAR(50) NOT NULL,
    referencia VARCHAR(100),
    fecha_pago TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    estado VARCHAR(20) DEFAULT 'COMPLETADO',
    observaciones TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (venta_id) REFERENCES ventas(id),
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- ============================================================================
-- SISTEMA DE INVENTARIO
-- ============================================================================

-- Tabla de movimientos de inventario
CREATE TABLE IF NOT EXISTS movimientos_inventario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id INTEGER NOT NULL,
    tipo_movimiento VARCHAR(20) NOT NULL, -- ENTRADA, SALIDA, AJUSTE
    cantidad INTEGER NOT NULL,
    precio_unitario DECIMAL(12,2),
    documento_referencia VARCHAR(100),
    motivo TEXT,
    usuario_id INTEGER,
    fecha_movimiento TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (producto_id) REFERENCES productos(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- ============================================================================
-- ANÁLISIS PREDICTIVO
-- ============================================================================

-- Tabla de análisis de clientes
CREATE TABLE IF NOT EXISTS analisis_clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER NOT NULL,
    fecha_analisis TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Scores RFM
    recency_score DECIMAL(3,2),
    frequency_score DECIMAL(3,2),
    monetary_score DECIMAL(3,2),
    rfm_combined DECIMAL(3,2),
    
    -- Predicciones
    churn_probability DECIMAL(3,2),
    clv_prediction DECIMAL(12,2),
    next_purchase_prediction DATE,
    
    -- Segmentación
    segment_id INTEGER,
    segment_name VARCHAR(50),
    
    -- Confianza
    prediction_confidence DECIMAL(3,2),
    
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);

-- Tabla de segmentos predictivos
CREATE TABLE IF NOT EXISTS segmentos_predictivos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre VARCHAR(100) NOT NULL,
    descripcion TEXT,
    criterios TEXT, -- JSON con criterios de segmentación
    color VARCHAR(7), -- Hex color code
    activo BOOLEAN DEFAULT 1,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- CONFIGURACIONES DEL SISTEMA
-- ============================================================================

-- Tabla de configuraciones
CREATE TABLE IF NOT EXISTS configuraciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria VARCHAR(100) NOT NULL,
    clave VARCHAR(100) NOT NULL,
    valor TEXT,
    tipo_dato VARCHAR(20) DEFAULT 'TEXT',
    descripcion TEXT,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    actualizado_por INTEGER,
    FOREIGN KEY (actualizado_por) REFERENCES usuarios(id),
    UNIQUE(categoria, clave)
);

-- Tabla de auditoría
CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tabla VARCHAR(100) NOT NULL,
    registro_id INTEGER,
    accion VARCHAR(20) NOT NULL, -- INSERT, UPDATE, DELETE
    datos_anteriores TEXT, -- JSON
    datos_nuevos TEXT, -- JSON
    usuario_id INTEGER,
    fecha_accion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent TEXT,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- ============================================================================
-- ÍNDICES PARA RENDIMIENTO
-- ============================================================================

-- Índices en tabla de productos
CREATE INDEX IF NOT EXISTS idx_productos_codigo ON productos(codigo);
CREATE INDEX IF NOT EXISTS idx_productos_nombre ON productos(nombre);
CREATE INDEX IF NOT EXISTS idx_productos_categoria ON productos(categoria_id);
CREATE INDEX IF NOT EXISTS idx_productos_activo ON productos(activo);

-- Índices en tabla de clientes  
CREATE INDEX IF NOT EXISTS idx_clientes_codigo ON clientes(codigo);
CREATE INDEX IF NOT EXISTS idx_clientes_nombre ON clientes(nombre);
CREATE INDEX IF NOT EXISTS idx_clientes_email ON clientes(email);
CREATE INDEX IF NOT EXISTS idx_clientes_segmento ON clientes(segmento);
CREATE INDEX IF NOT EXISTS idx_clientes_activo ON clientes(activo);

-- Índices en tabla de ventas
CREATE INDEX IF NOT EXISTS idx_ventas_fecha ON ventas(fecha_venta);
CREATE INDEX IF NOT EXISTS idx_ventas_cliente ON ventas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_ventas_usuario ON ventas(usuario_id);
CREATE INDEX IF NOT EXISTS idx_ventas_estado ON ventas(estado);
CREATE INDEX IF NOT EXISTS idx_ventas_numero ON ventas(numero);

-- Índices en detalles de venta
CREATE INDEX IF NOT EXISTS idx_detalles_venta_venta_id ON detalles_venta(venta_id);
CREATE INDEX IF NOT EXISTS idx_detalles_venta_producto_id ON detalles_venta(producto_id);

-- Índices en movimientos de inventario
CREATE INDEX IF NOT EXISTS idx_movimientos_producto ON movimientos_inventario(producto_id);
CREATE INDEX IF NOT EXISTS idx_movimientos_fecha ON movimientos_inventario(fecha_movimiento);
CREATE INDEX IF NOT EXISTS idx_movimientos_tipo ON movimientos_inventario(tipo_movimiento);

-- Índices en análisis predictivo
CREATE INDEX IF NOT EXISTS idx_analisis_cliente ON analisis_clientes(cliente_id);
CREATE INDEX IF NOT EXISTS idx_analisis_fecha ON analisis_clientes(fecha_analisis);
CREATE INDEX IF NOT EXISTS idx_analisis_segment ON analisis_clientes(segment_id);

-- ============================================================================
-- TRIGGERS DE AUDITORÍA
-- ============================================================================

-- Trigger para auditoría en ventas
CREATE TRIGGER IF NOT EXISTS trg_ventas_audit_insert
    AFTER INSERT ON ventas
    BEGIN
        INSERT INTO auditoria (tabla, registro_id, accion, datos_nuevos, usuario_id, fecha_accion)
        VALUES ('ventas', NEW.id, 'INSERT', 
                json_object(
                    'numero', NEW.numero,
                    'cliente_id', NEW.cliente_id,
                    'total', NEW.total,
                    'estado', NEW.estado
                ),
                NEW.usuario_id, CURRENT_TIMESTAMP);
    END;

-- Trigger para auditoría en productos
CREATE TRIGGER IF NOT EXISTS trg_productos_audit_update
    AFTER UPDATE ON productos
    BEGIN
        INSERT INTO auditoria (tabla, registro_id, accion, datos_anteriores, datos_nuevos, fecha_accion)
        VALUES ('productos', NEW.id, 'UPDATE',
                json_object(
                    'stock_actual', OLD.stock_actual,
                    'precio', OLD.precio
                ),
                json_object(
                    'stock_actual', NEW.stock_actual,
                    'precio', NEW.precio
                ),
                CURRENT_TIMESTAMP);
    END;

-- ============================================================================
-- VISTAS ÚTILES PARA ANÁLISIS
-- ============================================================================

-- Vista de resumen de ventas diarias
CREATE VIEW IF NOT EXISTS vista_ventas_diarias AS
SELECT 
    DATE(fecha_venta) as fecha,
    COUNT(*) as num_ventas,
    SUM(total) as total_ventas,
    AVG(total) as promedio_venta,
    COUNT(DISTINCT cliente_id) as clientes_unicos
FROM ventas
WHERE estado = 'COMPLETADA'
GROUP BY DATE(fecha_venta)
ORDER BY fecha DESC;

-- Vista de productos más vendidos
CREATE VIEW IF NOT EXISTS vista_productos_top AS
SELECT 
    p.codigo,
    p.nombre,
    p.categoria_id,
    c.nombre as categoria_nombre,
    SUM(dv.cantidad) as cantidad_vendida,
    SUM(dv.subtotal) as total_vendido,
    COUNT(DISTINCT dv.venta_id) as num_ventas
FROM productos p
JOIN detalles_venta dv ON p.id = dv.producto_id
JOIN ventas v ON dv.venta_id = v.id
LEFT JOIN categorias c ON p.categoria_id = c.id
WHERE v.estado = 'COMPLETADA'
GROUP BY p.id
ORDER BY cantidad_vendida DESC;

-- Vista de análisis de clientes
CREATE VIEW IF NOT EXISTS vista_analisis_clientes AS
SELECT 
    c.id,
    c.codigo,
    c.nombre,
    c.segmento,
    c.estado,
    c.total_compras,
    c.numero_compras,
    c.ultima_compra,
    JULIANDAY('now') - JULIANDAY(c.ultima_compra) as dias_desde_ultima_compra,
    CASE 
        WHEN c.numero_compras = 0 THEN 0
        ELSE c.total_compras / c.numero_compras
    END as promedio_compra,
    ac.churn_probability,
    ac.clv_prediction,
    ac.segment_name as segment_predictivo
FROM clientes c
LEFT JOIN analisis_clientes ac ON c.id = ac.cliente_id
WHERE c.activo = 1
ORDER BY c.total_compras DESC;

-- Vista de stock bajo
CREATE VIEW IF NOT EXISTS vista_stock_bajo AS
SELECT 
    p.codigo,
    p.nombre,
    p.stock_actual,
    p.stock_minimo,
    (p.stock_minimo - p.stock_actual) as faltante,
    c.nombre as categoria,
    pr.nombre as proveedor
FROM productos p
LEFT JOIN categorias c ON p.categoria_id = c.id
LEFT JOIN proveedores pr ON p.proveedor_id = pr.id
WHERE p.stock_actual <= p.stock_minimo 
  AND p.activo = 1
ORDER BY faltante DESC;

-- ============================================================================
-- DATOS INICIALES DEL SISTEMA
-- ============================================================================

-- Insertar roles básicos
INSERT OR IGNORE INTO roles (nombre, descripcion, permisos) VALUES 
('ADMIN', 'Administrador del sistema', '{"all": true}'),
('MANAGER', 'Gerente de operaciones', '{"ventas": true, "inventario": true, "reportes": true}'),
('CAJERO', 'Operador de punto de venta', '{"ventas": true}'),
('SUPERVISOR', 'Supervisor de área', '{"ventas": true, "inventario": true}');

-- Insertar configuraciones básicas
INSERT OR IGNORE INTO configuraciones (categoria, clave, valor, descripcion) VALUES 
('SISTEMA', 'NOMBRE_EMPRESA', 'AlmacénPro', 'Nombre de la empresa'),
('SISTEMA', 'VERSION', '2.0', 'Versión del sistema'),
('VENTAS', 'IVA_PORCENTAJE', '16', 'Porcentaje de IVA por defecto'),
('VENTAS', 'MONEDA', 'COP', 'Moneda del sistema'),
('INVENTARIO', 'ALERTA_STOCK_BAJO', '1', 'Activar alertas de stock bajo'),
('BACKUP', 'AUTO_BACKUP', '1', 'Backup automático activado'),
('BACKUP', 'BACKUP_INTERVAL', '24', 'Intervalo de backup en horas');

-- Insertar categoría por defecto
INSERT OR IGNORE INTO categorias (nombre, descripcion) VALUES 
('GENERAL', 'Categoría general para productos sin categoría específica');

-- ============================================================================
-- COMENTARIOS FINALES
-- ============================================================================

/*
Este schema representa la estructura completa de AlmacénPro v2.0
con arquitectura MVC y está optimizado para:

1. Rendimiento con índices estratégicos
2. Integridad referencial con foreign keys
3. Auditoría completa de operaciones críticas
4. Análisis predictivo y business intelligence
5. Escalabilidad para crecimiento futuro

Para usar con DBeaver:
1. Conectar a la base de datos SQLite
2. Ejecutar este script para crear/verificar estructura
3. Usar las vistas para análisis rápidos
4. Monitorear la tabla de auditoría para seguimiento

Mantenimiento recomendado:
- VACUUM mensual para optimización
- ANALYZE semanal para estadísticas
- Backup diario automático
- Revisión de logs de auditoría
*/

-- Optimizar base de datos
ANALYZE;
VACUUM;