#!/usr/bin/env python3
"""
Script para COMPLEMENTAR datos existentes en AlmacénPro
Respeta los datos actuales y agrega información adicional realista
"""

import sqlite3
import random
from pathlib import Path
from datetime import datetime, timedelta
from decimal import Decimal

def load_complementary_data():
    """Complementar datos existentes sin sobrescribir"""
    
    # Usar la base de datos principal (la que tiene datos)
    db_path = "almacen_pro.db"
    
    if not Path(db_path).exists():
        print(f"❌ Base de datos principal no encontrada: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"✅ Conectado a la base principal: {db_path}")
        print("\n📊 ANALIZANDO DATOS EXISTENTES:")
        print("=" * 60)
        
        # Verificar datos actuales
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        users_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM productos")
        products_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM clientes")
        clients_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ventas")
        sales_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM compras")
        purchases_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM detalle_ventas")
        sales_details_count = cursor.fetchone()[0]
        
        print(f"👥 Usuarios existentes: {users_count}")
        print(f"📦 Productos existentes: {products_count}")
        print(f"👤 Clientes existentes: {clients_count}")
        print(f"💰 Ventas existentes: {sales_count}")
        print(f"🛒 Compras existentes: {purchases_count}")
        print(f"📋 Detalles de venta: {sales_details_count}")
        
        data_added = {}
        
        # 1. COMPLETAR PRODUCTOS (agregar más para tener variedad)
        if products_count < 25:
            print(f"\n📦 AGREGANDO MÁS PRODUCTOS:")
            print("-" * 40)
            
            # Obtener categorías y proveedores existentes
            cursor.execute("SELECT id, nombre FROM categorias WHERE activo = 1")
            categorias = cursor.fetchall()
            
            cursor.execute("SELECT id, nombre FROM proveedores WHERE activo = 1")
            proveedores = cursor.fetchall()
            
            if not categorias:
                print("⚠️ No hay categorías, no se pueden agregar productos")
            elif not proveedores:
                print("⚠️ No hay proveedores, no se pueden agregar productos")
            else:
                nuevos_productos = [
                    ('7790040333444', 'P020', 'Arroz Gallo 1kg', 'Arroz largo fino premium', 320.00, 450.00, 35),
                    ('7790150777888', 'P021', 'Aceite Cocinero 900ml', 'Aceite de girasol refinado', 520.00, 720.00, 22),
                    ('7790080555666', 'P022', 'Dulce de Leche La Serenísima 400g', 'Dulce de leche tradicional', 380.50, 520.00, 28),
                    ('7790200111222', 'P023', 'Mayonesa Natura 500ml', 'Mayonesa casera tradicional', 290.00, 420.00, 31),
                    ('7790040999888', 'P024', 'Café Nescafé 100g', 'Café instantáneo soluble', 650.00, 880.00, 18),
                    ('7790150444555', 'P025', 'Manteca La Serenísima 200g', 'Manteca sin sal', 420.75, 580.00, 25),
                    ('7790080333222', 'P026', 'Galletitas Oreo 118g', 'Galletitas chocolate rellenas', 350.25, 480.00, 40),
                    ('7790200666777', 'P027', 'Atún La Campagnola 170g', 'Atún al natural en agua', 480.90, 650.00, 33),
                    ('7790040777666', 'P028', 'Mermelada Arcor 454g', 'Mermelada de durazno', 320.40, 450.00, 27),
                    ('7790150111888', 'P029', 'Crema de Leche La Serenísima 200ml', 'Crema de leche para cocinar', 180.60, 280.00, 38),
                    ('7790080999111', 'P030', 'Chocolate Milka 100g', 'Chocolate con leche', 420.00, 580.00, 24),
                    ('7790200444333', 'P031', 'Salsa de Tomate La Campagnola 520g', 'Salsa de tomate natural', 240.75, 360.00, 29)
                ]
                
                productos_agregados = 0
                for codigo_barras, codigo_interno, nombre, descripcion, precio_compra, precio_venta, stock in nuevos_productos:
                    try:
                        # Asignar categoría y proveedor aleatorio
                        categoria_id = random.choice(categorias)[0]
                        proveedor_id = random.choice(proveedores)[0]
                        
                        # Calcular margen
                        margen = ((precio_venta - precio_compra) / precio_compra * 100) if precio_compra > 0 else 0
                        
                        cursor.execute("""
                            INSERT OR IGNORE INTO productos 
                            (codigo_barras, codigo_interno, nombre, descripcion, categoria_id, proveedor_id,
                             precio_compra, precio_venta, margen_ganancia, stock_actual, stock_minimo, stock_maximo, 
                             unidad_medida, iva_porcentaje, activo, creado_en, actualizado_en) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 3, 80, 'UNIDAD', 21, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                        """, (codigo_barras, codigo_interno, nombre, descripcion, categoria_id, proveedor_id,
                              precio_compra, precio_venta, round(margen, 2), stock))
                        
                        if cursor.rowcount > 0:
                            productos_agregados += 1
                            print(f"  ✅ {nombre}")
                        
                    except Exception as e:
                        print(f"  ⚠️ Error en {nombre}: {e}")
                
                data_added['productos'] = productos_agregados
        
        # 2. AGREGAR DETALLES A VENTAS EXISTENTES (si no los tienen)
        if sales_details_count == 0 and sales_count > 0:
            print(f"\n💰 COMPLETANDO DETALLES DE VENTAS EXISTENTES:")
            print("-" * 40)
            
            # Obtener ventas sin detalles
            cursor.execute("SELECT id, total, numero_factura FROM ventas")
            ventas_existentes = cursor.fetchall()
            
            cursor.execute("SELECT id, nombre, precio_venta FROM productos WHERE activo = 1")
            productos_disponibles = cursor.fetchall()
            
            if productos_disponibles:
                detalles_agregados = 0
                for venta_id, total_venta, numero_factura in ventas_existentes:
                    try:
                        # Verificar si ya tiene detalles
                        cursor.execute("SELECT COUNT(*) FROM detalle_ventas WHERE venta_id = ?", (venta_id,))
                        if cursor.fetchone()[0] > 0:
                            continue  # Ya tiene detalles
                        
                        # Crear detalles que sumen aproximadamente el total
                        productos_venta = random.sample(productos_disponibles, random.randint(2, 4))
                        total_calculado = 0
                        
                        for i, (producto_id, nombre_producto, precio_venta) in enumerate(productos_venta):
                            if i == len(productos_venta) - 1:  # Último producto
                                # Ajustar para que coincida el total
                                cantidad = 1
                                precio_unitario = float(total_venta) - total_calculado
                                if precio_unitario <= 0:
                                    precio_unitario = float(precio_venta)
                            else:
                                cantidad = random.randint(1, 3)
                                precio_unitario = float(precio_venta)
                            
                            subtotal = cantidad * precio_unitario
                            total_calculado += subtotal
                            
                            cursor.execute("""
                                INSERT INTO detalle_ventas 
                                (venta_id, producto_id, cantidad, precio_unitario, descuento_porcentaje, subtotal) 
                                VALUES (?, ?, ?, ?, 0, ?)
                            """, (venta_id, producto_id, cantidad, precio_unitario, subtotal))
                            
                            detalles_agregados += 1
                        
                        print(f"  ✅ Venta {numero_factura} - {len(productos_venta)} productos")
                        
                    except Exception as e:
                        print(f"  ⚠️ Error en venta {numero_factura}: {e}")
                
                data_added['detalle_ventas'] = detalles_agregados
        
        # 3. AGREGAR COMPRAS (si no hay)
        if purchases_count == 0:
            print(f"\n🛒 AGREGANDO COMPRAS DE EJEMPLO:")
            print("-" * 40)
            
            cursor.execute("SELECT id FROM usuarios WHERE activo = 1 LIMIT 1")
            usuario_result = cursor.fetchone()
            if not usuario_result:
                print("⚠️ No hay usuarios para asignar compras")
            else:
                usuario_id = usuario_result[0]
                
                cursor.execute("SELECT id, nombre FROM proveedores WHERE activo = 1")
                proveedores_compras = cursor.fetchall()
                
                if proveedores_compras:
                    compras_agregadas = 0
                    for i in range(8):  # 8 compras
                        try:
                            proveedor_id, proveedor_nombre = random.choice(proveedores_compras)
                            
                            # Fecha aleatoria en los últimos 45 días
                            fecha_compra = datetime.now() - timedelta(days=random.randint(15, 45))
                            
                            subtotal = round(random.uniform(2000, 8000), 2)
                            impuestos = round(subtotal * 0.21, 2)
                            total = subtotal + impuestos
                            
                            cursor.execute("""
                                INSERT INTO compras 
                                (numero_factura, proveedor_id, usuario_id, subtotal, descuento, impuestos, total,
                                 fecha_compra, estado) 
                                VALUES (?, ?, ?, ?, 0, ?, ?, ?, 'RECIBIDA')
                            """, (f"FC{(i+1):04d}", proveedor_id, usuario_id, subtotal, impuestos, total, 
                                  fecha_compra.isoformat()))
                            
                            compras_agregadas += 1
                            print(f"  ✅ Compra FC{(i+1):04d} - {proveedor_nombre} - ${total:.2f}")
                            
                        except Exception as e:
                            print(f"  ⚠️ Error en compra {i+1}: {e}")
                    
                    data_added['compras'] = compras_agregadas
        
        # 4. AGREGAR MOVIMIENTOS DE STOCK
        cursor.execute("SELECT COUNT(*) FROM movimientos_stock")
        movimientos_count = cursor.fetchone()[0]
        
        if movimientos_count == 0:
            print(f"\n📊 AGREGANDO MOVIMIENTOS DE STOCK:")
            print("-" * 40)
            
            cursor.execute("SELECT id, nombre, stock_actual FROM productos WHERE activo = 1 LIMIT 10")
            productos_movimientos = cursor.fetchall()
            
            cursor.execute("SELECT id FROM usuarios WHERE activo = 1 LIMIT 1")
            usuario_result = cursor.fetchone()
            
            if productos_movimientos and usuario_result:
                usuario_id = usuario_result[0]
                movimientos_agregados = 0
                
                for producto_id, nombre_producto, stock_actual in productos_movimientos:
                    try:
                        # Movimiento de entrada inicial
                        fecha_entrada = datetime.now() - timedelta(days=random.randint(60, 90))
                        cantidad_entrada = stock_actual + random.randint(20, 50)
                        
                        cursor.execute("""
                            INSERT INTO movimientos_stock 
                            (producto_id, tipo_movimiento, motivo, cantidad_anterior, cantidad_movimiento,
                             cantidad_nueva, usuario_id, fecha_movimiento) 
                            VALUES (?, 'ENTRADA', 'COMPRA', 0, ?, ?, ?, ?)
                        """, (producto_id, cantidad_entrada, cantidad_entrada, usuario_id, fecha_entrada))
                        
                        # Varios movimientos de salida
                        cantidad_actual = cantidad_entrada
                        for j in range(random.randint(3, 6)):
                            if cantidad_actual <= stock_actual:
                                break
                            
                            cantidad_salida = random.randint(1, min(10, cantidad_actual - stock_actual))
                            cantidad_anterior = cantidad_actual
                            cantidad_actual -= cantidad_salida
                            
                            fecha_salida = fecha_entrada + timedelta(days=random.randint(1, 45))
                            
                            cursor.execute("""
                                INSERT INTO movimientos_stock 
                                (producto_id, tipo_movimiento, motivo, cantidad_anterior, cantidad_movimiento,
                                 cantidad_nueva, usuario_id, fecha_movimiento) 
                                VALUES (?, 'SALIDA', 'VENTA', ?, ?, ?, ?, ?)
                            """, (producto_id, cantidad_anterior, cantidad_salida, cantidad_actual, usuario_id, fecha_salida))
                        
                        movimientos_agregados += 4  # Aproximadamente
                        print(f"  ✅ Movimientos para: {nombre_producto}")
                        
                    except Exception as e:
                        print(f"  ⚠️ Error en {nombre_producto}: {e}")
                
                data_added['movimientos_stock'] = movimientos_agregados
        
        # 5. AGREGAR MÁS CLIENTES si son pocos
        if clients_count < 15:
            print(f"\n👥 AGREGANDO MÁS CLIENTES:")
            print("-" * 40)
            
            nuevos_clientes = [
                ('Sofía', 'Herrera', '33445566', '11-3344-5566', 'sofia.herrera@email.com', 'Av. Libertador 456'),
                ('Martín', 'Silva', '44556677', '11-4455-6677', 'martin.silva@email.com', 'Calle Moreno 789'),
                ('Valeria', 'Castro', '55667788', '11-5566-7788', 'valeria.castro@email.com', 'Av. Pueyrredón 123'),
                ('Gonzalo', 'Moreno', '66778899', '11-6677-8899', 'gonzalo.moreno@email.com', 'Calle Alsina 456'),
                ('Carolina', 'Vega', '77889900', '11-7788-9900', 'carolina.vega@email.com', 'Av. Corrientes 789'),
                ('Facundo', 'Romero', '88990011', '11-8899-0011', 'facundo.romero@email.com', 'Calle Rivadavia 321'),
                ('Antonella', 'Giménez', '99001122', '11-9900-1122', 'antonella.gimenez@email.com', 'Av. Santa Fe 654')
            ]
            
            clientes_agregados = 0
            for nombre, apellido, dni, telefono, email, direccion in nuevos_clientes:
                try:
                    nombre_completo = f"{nombre} {apellido}"
                    cursor.execute("""
                        INSERT OR IGNORE INTO clientes 
                        (nombre, apellido, dni_cuit, telefono, email, direccion, limite_credito, activo) 
                        VALUES (?, ?, ?, ?, ?, ?, 3000.00, 1)
                    """, (nombre, apellido, dni, telefono, email, direccion))
                    
                    if cursor.rowcount > 0:
                        clientes_agregados += 1
                        print(f"  ✅ {nombre_completo}")
                    
                except Exception as e:
                    print(f"  ⚠️ Error en {nombre_completo}: {e}")
            
            data_added['clientes'] = clientes_agregados
        
        # Confirmar cambios
        conn.commit()
        
        # RESUMEN FINAL
        print("\n" + "=" * 70)
        print("🎉 DATOS COMPLEMENTARIOS AGREGADOS EXITOSAMENTE")
        print("=" * 70)
        
        total_added = 0
        for categoria, cantidad in data_added.items():
            print(f"➕ {categoria:20} +{cantidad:>8} registros")
            total_added += cantidad
        
        print("-" * 70)
        print(f"📈 TOTAL AGREGADO:      +{total_added:>8}")
        
        # Verificar estado final
        print(f"\n📊 ESTADO FINAL DE LA BASE DE DATOS:")
        print("-" * 70)
        
        cursor.execute("SELECT COUNT(*) FROM productos WHERE activo = 1")
        final_products = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM clientes WHERE activo = 1")
        final_clients = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM ventas")
        final_sales = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM detalle_ventas")
        final_details = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM compras")
        final_purchases = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM movimientos_stock")
        final_movements = cursor.fetchone()[0]
        
        print(f"📦 Productos activos:     {final_products}")
        print(f"👥 Clientes activos:      {final_clients}")
        print(f"💰 Ventas registradas:    {final_sales}")
        print(f"📋 Detalles de venta:     {final_details}")
        print(f"🛒 Compras registradas:   {final_purchases}")
        print(f"📊 Movimientos de stock:  {final_movements}")
        
        print(f"\n✅ Sistema complementado con datos realistas")
        print(f"🎯 Mantuviste todos tus datos existentes")
        print(f"🚀 Ahora tienes más variedad para probar funcionalidades")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 COMPLEMENTANDO DATOS EXISTENTES EN ALMACÉNPRO")
    print("=" * 70)
    print("💡 Este script RESPETA tus datos actuales y agrega información adicional")
    print()
    
    success = load_complementary_data()
    
    print("\n" + "=" * 70)
    if success:
        print("✅ ¡DATOS COMPLEMENTARIOS AGREGADOS EXITOSAMENTE!")
        print("🎯 Tus datos existentes se mantuvieron intactos")
        print("➕ Se agregó información adicional para completar el sistema")
        print("🚀 Ahora tienes un sistema más completo para probar")
    else:
        print("❌ ERROR COMPLEMENTANDO DATOS")
        print("💡 Revisa los mensajes de error arriba")
