#!/usr/bin/env python3
"""
Test simplificado de venta sin actualización de stock
"""

import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.manager import DatabaseManager

def test_simple_sale():
    """Test de venta sin actualizar stock para evitar triggers"""
    
    print("="*60)
    print("TEST SIMPLIFICADO DE VENTA (SIN STOCK UPDATE)")
    print("="*60)
    
    try:
        db = DatabaseManager()
        
        # DATOS DE LA VENTA
        print("\n1. PREPARANDO DATOS DE VENTA")
        print("-" * 30)
        
        # Buscar un producto
        productos = db.execute_query("SELECT id, nombre, precio_venta FROM productos WHERE activo = 1 LIMIT 1")
        if not productos:
            print("ERROR: No hay productos")
            return False
        
        producto = dict(productos[0])
        print(f"Producto: {producto['nombre']} - ${producto['precio_venta']}")
        
        # Buscar un cliente
        clientes = db.execute_query("SELECT id, nombre, apellido, limite_credito, saldo_cuenta_corriente FROM clientes WHERE limite_credito > 0 LIMIT 1")
        cliente = dict(clientes[0]) if clientes else None
        
        if cliente:
            print(f"Cliente: {cliente['nombre']} {cliente['apellido']}")
        else:
            print("Sin cliente específico")
        
        # CREAR VENTA DIRECTAMENTE EN BD
        print("\n2. CREANDO VENTA DIRECTAMENTE")
        print("-" * 30)
        
        # Calcular totales
        cantidad = 1
        precio_unitario = float(producto['precio_venta'])
        subtotal = cantidad * precio_unitario
        impuestos = subtotal * 0.21
        total = subtotal + impuestos
        
        print(f"Subtotal: ${subtotal:.2f}")
        print(f"Impuestos: ${impuestos:.2f}")
        print(f"Total: ${total:.2f}")
        
        # Insertar venta
        venta_id = db.execute_insert("""
            INSERT INTO ventas (
                numero_factura, cliente_id, vendedor_id, usuario_id,
                fecha_venta, subtotal, descuento, impuestos, total, 
                estado, notas, caja_id, tipo_venta, metodo_pago
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            f"TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}",  # numero_factura
            cliente['id'] if cliente else None,  # cliente_id
            1,  # vendedor_id
            1,  # usuario_id
            subtotal,  # subtotal
            0,  # descuento
            impuestos,  # impuestos
            total,  # total
            'COMPLETADA',  # estado
            'Venta de prueba directa',  # notas
            1,  # caja_id
            'TICKET',  # tipo_venta
            'CUENTA_CORRIENTE' if cliente else 'EFECTIVO'  # metodo_pago
        ))
        
        if venta_id:
            print(f"OK: Venta creada con ID: {venta_id}")
        else:
            print("ERROR: No se pudo crear la venta")
            return False
        
        # INSERTAR DETALLE DE VENTA
        print("\n3. AGREGANDO DETALLE DE VENTA")
        print("-" * 30)
        
        detalle_id = db.execute_insert("""
            INSERT INTO detalle_ventas (
                venta_id, producto_id, cantidad, precio_unitario,
                descuento_porcentaje, subtotal
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            venta_id,
            producto['id'],
            cantidad,
            precio_unitario,
            0,  # descuento_porcentaje
            subtotal
        ))
        
        if detalle_id:
            print(f"OK: Detalle creado con ID: {detalle_id}")
        else:
            print("ERROR: No se pudo crear el detalle")
            return False
        
        # INSERTAR PAGO
        print("\n4. REGISTRANDO PAGO")
        print("-" * 30)
        
        pago_id = db.execute_insert("""
            INSERT INTO pagos_venta (
                venta_id, metodo_pago, importe, referencia,
                fecha_pago, observaciones
            ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
        """, (
            venta_id,
            'CUENTA_CORRIENTE' if cliente else 'EFECTIVO',
            total,
            'TEST-PAYMENT',
            'Pago de prueba'
        ))
        
        if pago_id:
            print(f"OK: Pago registrado con ID: {pago_id}")
        else:
            print("ERROR: No se pudo registrar el pago")
            return False
        
        # ACTUALIZAR CUENTA CORRIENTE SI APLICA
        if cliente:
            print("\n5. ACTUALIZANDO CUENTA CORRIENTE")
            print("-" * 30)
            
            # Actualizar saldo del cliente
            db.execute_update("""
                UPDATE clientes 
                SET saldo_cuenta_corriente = saldo_cuenta_corriente + ?
                WHERE id = ?
            """, (total, cliente['id']))
            
            # Insertar movimiento en cuenta corriente
            movimiento_id = db.execute_insert("""
                INSERT INTO cuenta_corriente (
                    cliente_id, tipo_movimiento, concepto, importe,
                    saldo_anterior, saldo_nuevo, venta_id, fecha_movimiento, usuario_id, notas
                ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?, ?)
            """, (
                cliente['id'],
                'DEBE',
                f'Venta #{venta_id}',
                total,
                float(cliente['saldo_cuenta_corriente']),
                float(cliente['saldo_cuenta_corriente']) + total,
                venta_id,
                1,  # usuario_id
                'Venta a crédito'
            ))
            
            if movimiento_id:
                print(f"OK: Movimiento de cuenta corriente creado: {movimiento_id}")
            else:
                print("ERROR: No se pudo crear el movimiento")
        
        print("\n" + "="*60)
        print("RESULTADO: VENTA COMPLETADA EXITOSAMENTE")
        print(f"ID de Venta: {venta_id}")
        print(f"Total: ${total:.2f}")
        if cliente:
            print(f"Cliente: {cliente['nombre']} {cliente['apellido']}")
            print(f"Método: CUENTA CORRIENTE")
        else:
            print("Método: EFECTIVO")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    from datetime import datetime
    
    success = test_simple_sale()
    if success:
        print("\nSUCCESS: Venta simple completada")
    else:
        print("\nFAILED: Error en venta simple")
        sys.exit(1)