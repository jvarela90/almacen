#!/usr/bin/env python3
"""
Script ADAPTATIVO para cargar datos de prueba en AlmacénPro
Se adapta automáticamente a la estructura real de las tablas
"""

import sqlite3
import random
from pathlib import Path
from datetime import datetime, timedelta

def find_database():
    """Encontrar archivo de base de datos"""
    possible_names = ["almacen_pro.db", "almacen.db", "database.db"]
    
    for db_name in possible_names:
        if Path(db_name).exists():
            return db_name
    
    print("❌ No se encontró ninguna base de datos")
    return None

def get_table_columns(cursor, table_name):
    """Obtener columnas de una tabla"""
    try:
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        return {col[1]: col[2] for col in columns}  # {nombre: tipo}
    except:
        return {}

def build_insert_query(table_name, columns_available, data_dict):
    """Construir query INSERT usando solo columnas disponibles"""
    available_keys = [key for key in data_dict.keys() if key in columns_available]
    
    if not available_keys:
        return None, None
    
    placeholders = ', '.join(['?' for _ in available_keys])
    columns_str = ', '.join(available_keys)
    
    query = f"INSERT OR IGNORE INTO {table_name} ({columns_str}) VALUES ({placeholders})"
    values = [data_dict[key] for key in available_keys]
    
    return query, values

def load_adaptive_data():
    """Cargar datos adaptándose a la estructura real"""
    
    db_path = find_database()
    if not db_path:
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"✅ Conectado a: {db_path}")
        print("\n🔍 ANALIZANDO ESTRUCTURA DE TABLAS:")
        print("=" * 60)
        
        # Obtener todas las tablas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📋 Tablas encontradas: {len(tables)}")
        
        data_loaded = {}
        
        # 1. CATEGORÍAS
        if 'categorias' in tables:
            print(f"\n📚 CARGANDO CATEGORÍAS:")
            print("-" * 40)
            
            columns = get_table_columns(cursor, 'categorias')
            print(f"   Columnas: {', '.join(columns.keys())}")
            
            categorias_data = [
                {'nombre': 'ALMACEN', 'descripcion': 'Productos de almacén general', 'color': '#3498db', 'activo': 1},
                {'nombre': 'BEBIDAS', 'descripcion': 'Bebidas alcohólicas y sin alcohol', 'color': '#e74c3c', 'activo': 1},
                {'nombre': 'LACTEOS', 'descripcion': 'Productos lácteos y frescos', 'color': '#f39c12', 'activo': 1},
                {'nombre': 'PANADERIA', 'descripcion': 'Pan, facturas y productos de panadería', 'color': '#d35400', 'activo': 1},
                {'nombre': 'LIMPIEZA', 'descripcion': 'Productos de limpieza e higiene', 'color': '#27ae60', 'activo': 1},
                {'nombre': 'GOLOSINAS', 'descripcion': 'Caramelos, chocolates y snacks', 'color': '#e67e22', 'activo': 1},
                {'nombre': 'CONGELADOS', 'descripcion': 'Productos congelados', 'color': '#3498db', 'activo': 1},
                {'nombre': 'CARNICERIA', 'descripcion': 'Carnes y embutidos', 'color': '#c0392b', 'activo': 1},
                {'nombre': 'VERDULERIA', 'descripcion': 'Frutas y verduras frescas', 'color': '#27ae60', 'activo': 1},
                {'nombre': 'PERFUMERIA', 'descripcion': 'Productos de higiene personal', 'color': '#9b59b6', 'activo': 1},
                {'nombre': 'CIGARRILLOS', 'descripcion': 'Cigarrillos y tabaco', 'color': '#7f8c8d', 'activo': 1},
                {'nombre': 'BAZAR', 'descripcion': 'Artículos de bazar y hogar', 'color': '#34495e', 'activo': 1}
            ]
            
            loaded_count = 0
            for categoria in categorias_data:
                query, values = build_insert_query('categorias', columns, categoria)
                if query:
                    try:
                        cursor.execute(query, values)
                        loaded_count += 1
                        print(f"  ✅ {categoria['nombre']}")
                    except Exception as e:
                        print(f"  ⚠️ {categoria['nombre']}: {e}")
                else:
                    print(f"  ❌ No se pudo crear query para {categoria['nombre']}")
            
            data_loaded['categorias'] = loaded_count
        
        # 2. PROVEEDORES
        if 'proveedores' in tables:
            print(f"\n🏢 CARGANDO PROVEEDORES:")
            print("-" * 40)
            
            columns = get_table_columns(cursor, 'proveedores')
            print(f"   Columnas: {', '.join(columns.keys())}")
            
            proveedores_data = [
                {'codigo': 'PROV001', 'nombre': 'Distribuidora La Serenísima', 'razon_social': 'La Serenísima S.A.', 'cuit_cuil': '30-12345678-9', 'telefono': '11-4444-5555', 'email': 'pedidos@laserenisima.com', 'direccion': 'Av. Corrientes 1234, CABA', 'activo': 1},
                {'codigo': 'PROV002', 'nombre': 'Coca Cola Argentina', 'razon_social': 'The Coca-Cola Company', 'cuit_cuil': '30-87654321-0', 'telefono': '11-5555-6666', 'email': 'ventas@cocacola.com.ar', 'direccion': 'Av. del Libertador 567, CABA', 'activo': 1},
                {'codigo': 'PROV003', 'nombre': 'Arcor Distribución', 'razon_social': 'Arcor SAIC', 'cuit_cuil': '30-11111111-1', 'telefono': '11-6666-7777', 'email': 'distribuccion@arcor.com', 'direccion': 'Parque Industrial Córdoba', 'activo': 1},
                {'codigo': 'PROV004', 'nombre': 'Bimbo Argentina', 'razon_social': 'Grupo Bimbo', 'cuit_cuil': '30-22222222-2', 'telefono': '11-7777-8888', 'email': 'pedidos@bimbo.com.ar', 'direccion': 'Zona Norte, Buenos Aires', 'activo': 1},
                {'codigo': 'PROV005', 'nombre': 'Unilever Argentina', 'razon_social': 'Unilever de Argentina S.A.', 'cuit_cuil': '30-33333333-3', 'telefono': '11-8888-9999', 'email': 'ventas@unilever.com', 'direccion': 'Av. San Martín 890, Martínez', 'activo': 1},
                {'codigo': 'PROV006', 'nombre': 'Molinos Río de la Plata', 'razon_social': 'Molinos Río de la Plata S.A.', 'cuit_cuil': '30-44444444-4', 'telefono': '11-9999-0000', 'email': 'comercial@molinos.com', 'direccion': 'Puerto Madero, CABA', 'activo': 1},
                {'codigo': 'PROV007', 'nombre': 'Mastellone Hermanos', 'razon_social': 'Mastellone Hermanos S.A.', 'cuit_cuil': '30-55555555-5', 'telefono': '11-1111-2222', 'email': 'ventas@mastellone.com', 'direccion': 'General Rodríguez, Buenos Aires', 'activo': 1},
                {'codigo': 'PROV008', 'nombre': 'Felfort S.A.', 'razon_social': 'Chocolates Felfort', 'cuit_cuil': '30-66666666-6', 'telefono': '11-2222-3333', 'email': 'distribuidores@felfort.com', 'direccion': 'Av. Juan B. Justo 1500', 'activo': 1},
                {'codigo': 'PROV009', 'nombre': 'AGD - Almacenes Generales', 'razon_social': 'Almacenes Generales Depósito', 'cuit_cuil': '30-77777777-7', 'telefono': '11-3333-4444', 'email': 'compras@agd.com.ar', 'direccion': 'Zona Oeste, Buenos Aires', 'activo': 1},
                {'codigo': 'PROV010', 'nombre': 'Distribuidora San Jorge', 'razon_social': 'Distribuidora San Jorge S.R.L.', 'cuit_cuil': '30-99999999-9', 'telefono': '11-5555-6666', 'email': 'ventas@sanjorge.com', 'direccion': 'Villa Soldati, CABA', 'activo': 1}
            ]
            
            loaded_count = 0
            for proveedor in proveedores_data:
                query, values = build_insert_query('proveedores', columns, proveedor)
                if query:
                    try:
                        cursor.execute(query, values)
                        loaded_count += 1
                        print(f"  ✅ {proveedor['nombre']}")
                    except Exception as e:
                        print(f"  ⚠️ {proveedor['nombre']}: {e}")
                else:
                    print(f"  ❌ No se pudo crear query para {proveedor['nombre']}")
            
            data_loaded['proveedores'] = loaded_count
        
        # 3. PRODUCTOS
        if 'productos' in tables:
            print(f"\n📦 CARGANDO PRODUCTOS:")
            print("-" * 40)
            
            columns = get_table_columns(cursor, 'productos')
            print(f"   Columnas: {', '.join(columns.keys())}")
            
            # Obtener IDs de categorías y proveedores existentes
            categoria_ids = {}
            try:
                cursor.execute("SELECT id, nombre FROM categorias")
                categoria_ids = {nombre: id for id, nombre in cursor.fetchall()}
            except:
                pass
            
            proveedor_ids = {}
            try:
                cursor.execute("SELECT id, nombre FROM proveedores")
                proveedor_ids = {nombre: id for id, nombre in cursor.fetchall()}
            except:
                pass
            
            productos_data = [
                {'codigo_barras': '7790150491072', 'codigo_interno': 'P001', 'nombre': 'Leche Entera La Serenísima 1L', 'descripcion': 'Leche entera larga vida 1 litro', 'precio_compra': 280.50, 'precio_venta': 350.00, 'stock_actual': 45, 'stock_minimo': 5, 'stock_maximo': 100, 'unidad_medida': 'UNIDAD', 'activo': 1},
                {'codigo_barras': '7790895001234', 'codigo_interno': 'P002', 'nombre': 'Coca Cola 500ml', 'descripcion': 'Gaseosa Coca Cola botella 500ml', 'precio_compra': 180.25, 'precio_venta': 250.00, 'stock_actual': 72, 'stock_minimo': 10, 'stock_maximo': 120, 'unidad_medida': 'UNIDAD', 'activo': 1},
                {'codigo_barras': '7790040295521', 'codigo_interno': 'P003', 'nombre': 'Chocolate Milka Oreo', 'descripcion': 'Chocolate con leche y cookies Oreo 100g', 'precio_compra': 420.75, 'precio_venta': 580.00, 'stock_actual': 28, 'stock_minimo': 5, 'stock_maximo': 50, 'unidad_medida': 'UNIDAD', 'activo': 1},
                {'codigo_barras': '7790070041234', 'codigo_interno': 'P004', 'nombre': 'Pan Lactal Bimbo', 'descripcion': 'Pan de molde lactal grande 500g', 'precio_compra': 290.00, 'precio_venta': 420.00, 'stock_actual': 35, 'stock_minimo': 8, 'stock_maximo': 60, 'unidad_medida': 'UNIDAD', 'activo': 1},
                {'codigo_barras': '7790375001567', 'codigo_interno': 'P005', 'nombre': 'Shampoo Sedal 350ml', 'descripcion': 'Shampoo reparación total 350ml', 'precio_compra': 380.90, 'precio_venta': 520.00, 'stock_actual': 22, 'stock_minimo': 3, 'stock_maximo': 40, 'unidad_medida': 'UNIDAD', 'activo': 1},
                {'codigo_barras': '7790040123456', 'codigo_interno': 'P006', 'nombre': 'Fideos Marolio Mostachol 500g', 'descripcion': 'Pasta mostachol 500g', 'precio_compra': 185.60, 'precio_venta': 280.00, 'stock_actual': 58, 'stock_minimo': 10, 'stock_maximo': 80, 'unidad_medida': 'UNIDAD', 'activo': 1},
                {'codigo_barras': '7790150567890', 'codigo_interno': 'P007', 'nombre': 'Yogur Ser Frutilla 190g', 'descripcion': 'Yogur entero sabor frutilla', 'precio_compra': 145.30, 'precio_venta': 220.00, 'stock_actual': 41, 'stock_minimo': 8, 'stock_maximo': 60, 'unidad_medida': 'UNIDAD', 'activo': 1},
                {'codigo_barras': '7790080234567', 'codigo_interno': 'P008', 'nombre': 'Bon o Bon Blanco x6', 'descripcion': 'Bombones chocolate blanco x6 unidades', 'precio_compra': 320.40, 'precio_venta': 450.00, 'stock_actual': 33, 'stock_minimo': 5, 'stock_maximo': 50, 'unidad_medida': 'UNIDAD', 'activo': 1},
                {'codigo_barras': '7790040987654', 'codigo_interno': 'P009', 'nombre': 'Aceite Natura 900ml', 'descripcion': 'Aceite mezcla botella 900ml', 'precio_compra': 480.20, 'precio_venta': 650.00, 'stock_actual': 25, 'stock_minimo': 4, 'stock_maximo': 35, 'unidad_medida': 'UNIDAD', 'activo': 1},
                {'codigo_barras': '7790200345678', 'codigo_interno': 'P010', 'nombre': 'Marlboro Box x20', 'descripcion': 'Cigarrillos Marlboro rojos x20', 'precio_compra': 580.75, 'precio_venta': 780.00, 'stock_actual': 40, 'stock_minimo': 6, 'stock_maximo': 60, 'unidad_medida': 'UNIDAD', 'activo': 1},
                {'codigo_barras': '7790040111222', 'codigo_interno': 'P011', 'nombre': 'Detergente Magistral 750ml', 'descripcion': 'Detergente líquido concentrado', 'precio_compra': 290.50, 'precio_venta': 420.00, 'stock_actual': 31, 'stock_minimo': 5, 'stock_maximo': 45, 'unidad_medida': 'UNIDAD', 'activo': 1},
                {'codigo_barras': '7790150789012', 'codigo_interno': 'P012', 'nombre': 'Queso Cremoso Mastellone kg', 'descripcion': 'Queso cremoso por kilogramo', 'precio_compra': 1280.00, 'precio_venta': 1680.00, 'stock_actual': 12, 'stock_minimo': 2, 'stock_maximo': 20, 'unidad_medida': 'KILOGRAMO', 'activo': 1}
            ]
            
            # Agregar IDs de categoría y proveedor si están disponibles
            for i, producto in enumerate(productos_data):
                if 'categoria_id' in columns:
                    # Asignar categoría apropiada
                    categoria_map = {
                        'Leche': 'LACTEOS', 'Coca': 'BEBIDAS', 'Chocolate': 'GOLOSINAS',
                        'Pan': 'PANADERIA', 'Shampoo': 'PERFUMERIA', 'Fideos': 'ALMACEN',
                        'Yogur': 'LACTEOS', 'Bon': 'GOLOSINAS', 'Aceite': 'ALMACEN',
                        'Marlboro': 'CIGARRILLOS', 'Detergente': 'LIMPIEZA', 'Queso': 'LACTEOS'
                    }
                    
                    for key_word, categoria in categoria_map.items():
                        if key_word in producto['nombre']:
                            if categoria in categoria_ids:
                                producto['categoria_id'] = categoria_ids[categoria]
                            break
                
                if 'proveedor_id' in columns:
                    # Asignar proveedor
                    if 'Serenísima' in producto['nombre'] and 'Distribuidora La Serenísima' in proveedor_ids:
                        producto['proveedor_id'] = proveedor_ids['Distribuidora La Serenísima']
                    elif 'Coca' in producto['nombre'] and 'Coca Cola Argentina' in proveedor_ids:
                        producto['proveedor_id'] = proveedor_ids['Coca Cola Argentina']
                    elif 'Bimbo' in producto['nombre'] and 'Bimbo Argentina' in proveedor_ids:
                        producto['proveedor_id'] = proveedor_ids['Bimbo Argentina']
                    elif 'Mastellone' in producto['nombre'] and 'Mastellone Hermanos' in proveedor_ids:
                        producto['proveedor_id'] = proveedor_ids['Mastellone Hermanos']
                
                # Calcular margen si está disponible
                if 'margen_ganancia' in columns:
                    precio_compra = producto['precio_compra']
                    precio_venta = producto['precio_venta']
                    if precio_compra > 0:
                        margen = ((precio_venta - precio_compra) / precio_compra) * 100
                        producto['margen_ganancia'] = round(margen, 2)
            
            loaded_count = 0
            for producto in productos_data:
                query, values = build_insert_query('productos', columns, producto)
                if query:
                    try:
                        cursor.execute(query, values)
                        loaded_count += 1
                        print(f"  ✅ {producto['nombre']}")
                    except Exception as e:
                        print(f"  ⚠️ {producto['nombre']}: {e}")
                else:
                    print(f"  ❌ No se pudo crear query para {producto['nombre']}")
            
            data_loaded['productos'] = loaded_count
        
        # 4. CLIENTES
        if 'clientes' in tables:
            print(f"\n👥 CARGANDO CLIENTES:")
            print("-" * 40)
            
            columns = get_table_columns(cursor, 'clientes')
            print(f"   Columnas: {', '.join(columns.keys())}")
            
            clientes_data = [
                {'codigo_cliente': 'CLI001', 'nombre': 'Juan', 'apellido': 'Pérez', 'nombre_completo': 'Juan Pérez', 'numero_documento': '12345678', 'telefono': '11-1234-5678', 'email': 'juan.perez@email.com', 'direccion': 'Av. San Martín 123', 'ciudad': 'Buenos Aires', 'activo': 1},
                {'codigo_cliente': 'CLI002', 'nombre': 'María', 'apellido': 'González', 'nombre_completo': 'María González', 'numero_documento': '23456789', 'telefono': '11-2345-6789', 'email': 'maria.gonzalez@email.com', 'direccion': 'Calle Belgrano 456', 'ciudad': 'Buenos Aires', 'activo': 1},
                {'codigo_cliente': 'CLI003', 'nombre': 'Carlos', 'apellido': 'López', 'nombre_completo': 'Carlos López', 'numero_documento': '34567890', 'telefono': '11-3456-7890', 'email': 'carlos.lopez@email.com', 'direccion': 'Av. Rivadavia 789', 'ciudad': 'Buenos Aires', 'activo': 1},
                {'codigo_cliente': 'CLI004', 'nombre': 'Ana', 'apellido': 'Martínez', 'nombre_completo': 'Ana Martínez', 'numero_documento': '45678901', 'telefono': '11-4567-8901', 'email': 'ana.martinez@email.com', 'direccion': 'Calle Mitre 321', 'ciudad': 'Buenos Aires', 'activo': 1},
                {'codigo_cliente': 'CLI005', 'nombre': 'Roberto', 'apellido': 'García', 'nombre_completo': 'Roberto García', 'numero_documento': '56789012', 'telefono': '11-5678-9012', 'email': 'roberto.garcia@email.com', 'direccion': 'Av. Córdoba 654', 'ciudad': 'Buenos Aires', 'activo': 1},
                {'codigo_cliente': 'CLI006', 'nombre': 'Laura', 'apellido': 'Rodríguez', 'nombre_completo': 'Laura Rodríguez', 'numero_documento': '67890123', 'telefono': '11-6789-0123', 'email': 'laura.rodriguez@email.com', 'direccion': 'Calle Sarmiento 987', 'ciudad': 'Buenos Aires', 'activo': 1},
                {'codigo_cliente': 'CLI007', 'nombre': 'Diego', 'apellido': 'Fernández', 'nombre_completo': 'Diego Fernández', 'numero_documento': '78901234', 'telefono': '11-7890-1234', 'email': 'diego.fernandez@email.com', 'direccion': 'Av. Santa Fe 147', 'ciudad': 'Buenos Aires', 'activo': 1},
                {'codigo_cliente': 'CLI008', 'nombre': 'Carmen', 'apellido': 'Ruiz', 'nombre_completo': 'Carmen Ruiz', 'numero_documento': '89012345', 'telefono': '11-8901-2345', 'email': 'carmen.ruiz@email.com', 'direccion': 'Calle Moreno 258', 'ciudad': 'Buenos Aires', 'activo': 1}
            ]
            
            loaded_count = 0
            for cliente in clientes_data:
                query, values = build_insert_query('clientes', columns, cliente)
                if query:
                    try:
                        cursor.execute(query, values)
                        loaded_count += 1
                        print(f"  ✅ {cliente['nombre_completo']}")
                    except Exception as e:
                        print(f"  ⚠️ {cliente['nombre_completo']}: {e}")
                else:
                    print(f"  ❌ No se pudo crear query para {cliente['nombre_completo']}")
            
            data_loaded['clientes'] = loaded_count
        
        # 5. VENTAS SIMPLES (sin detalles por ahora)
        if 'ventas' in tables:
            print(f"\n💰 CARGANDO VENTAS BÁSICAS:")
            print("-" * 40)
            
            columns = get_table_columns(cursor, 'ventas')
            print(f"   Columnas: {', '.join(columns.keys())}")
            
            # Obtener IDs necesarios
            usuario_ids = []
            try:
                cursor.execute("SELECT id FROM usuarios")
                usuario_ids = [row[0] for row in cursor.fetchall()]
            except:
                pass
            
            cliente_ids = []
            try:
                cursor.execute("SELECT id FROM clientes")
                cliente_ids = [row[0] for row in cursor.fetchall()]
            except:
                pass
            
            if usuario_ids:  # Solo crear ventas si hay usuarios
                loaded_count = 0
                for i in range(12):
                    fecha_venta = datetime.now() - timedelta(days=random.randint(1, 30))
                    
                    venta_data = {
                        'numero_factura': f"V{(i+1):04d}",
                        'subtotal': round(random.uniform(500, 3000), 2),
                        'descuento': 0,
                        'impuestos': 0,
                        'total': 0,  # Se calculará
                        'metodo_pago': random.choice(['EFECTIVO', 'TARJETA', 'TRANSFERENCIA']),
                        'estado': 'COMPLETADA',
                        'fecha_venta': fecha_venta.isoformat(),
                        'vendedor_id': random.choice(usuario_ids) if 'vendedor_id' in columns else None,
                        'usuario_id': random.choice(usuario_ids) if 'usuario_id' in columns else None,
                        'cliente_id': random.choice(cliente_ids + [None]) if cliente_ids and 'cliente_id' in columns else None
                    }
                    
                    # Calcular total
                    subtotal = venta_data['subtotal']
                    impuestos = subtotal * 0.21
                    venta_data['impuestos'] = round(impuestos, 2)
                    venta_data['total'] = round(subtotal + impuestos, 2)
                    
                    query, values = build_insert_query('ventas', columns, venta_data)
                    if query:
                        try:
                            cursor.execute(query, values)
                            loaded_count += 1
                            print(f"  ✅ Venta #{venta_data['numero_factura']} - ${venta_data['total']}")
                        except Exception as e:
                            print(f"  ⚠️ Venta #{venta_data['numero_factura']}: {e}")
                
                data_loaded['ventas'] = loaded_count
            else:
                print("  ❌ No hay usuarios disponibles para crear ventas")
        
        # Confirmar todos los cambios
        conn.commit()
        
        # RESUMEN FINAL
        print("\n" + "=" * 70)
        print("🎉 DATOS DE PRUEBA CARGADOS EXITOSAMENTE")
        print("=" * 70)
        
        total_records = 0
        for tabla, cantidad in data_loaded.items():
            print(f"📊 {tabla:20} {cantidad:>8} registros")
            total_records += cantidad
        
        print("-" * 70)
        print(f"📈 TOTAL DE REGISTROS:   {total_records:>8}")
        
        if total_records > 0:
            print(f"\n✅ Base de datos poblada exitosamente")
            print(f"🎯 Datos adaptados automáticamente a tu esquema")
            print(f"🚀 Ahora puedes probar el sistema con datos realistas")
        else:
            print(f"\n⚠️ No se pudieron cargar datos")
            print(f"💡 Verifica la estructura de las tablas")
        
        conn.close()
        return total_records > 0
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 CARGANDO DATOS ADAPTATIVOS EN ALMACÉNPRO")
    print("=" * 70)
    
    success = load_adaptive_data()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ ¡DATOS CARGADOS EXITOSAMENTE!")
        print("🚀 El script se adaptó automáticamente a tu esquema")
        print("💡 Ejecuta la aplicación y explora las funcionalidades")
    else:
        print("❌ ERROR CARGANDO DATOS DE PRUEBA")
        print("💡 Revisa los mensajes de error arriba")