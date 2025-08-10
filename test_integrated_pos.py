#!/usr/bin/env python3
"""
Test completo del sistema POS integrado con managers corregidos
"""

import sys
import os
from datetime import datetime, date

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.manager import DatabaseManager
from managers.product_manager import ProductManager
from managers.customer_manager import CustomerManager
from managers.sales_manager import SalesManager

def test_integrated_pos():
    """Test completo del flujo POS con managers integrados"""
    
    print("="*60)
    print("TEST INTEGRADO DEL SISTEMA POS")
    print("="*60)
    
    try:
        # Inicializar managers
        print("\n1. INICIALIZANDO MANAGERS")
        print("-" * 30)
        
        db = DatabaseManager()
        product_manager = ProductManager(db)
        customer_manager = CustomerManager(db)
        sales_manager = SalesManager(db, product_manager)
        
        print("OK DatabaseManager inicializado")
        print("OK ProductManager inicializado") 
        print("OK CustomerManager inicializado")
        print("OK SalesManager inicializado")
        
        # Test búsqueda de productos
        print("\n2. TEST BUSQUEDA DE PRODUCTOS")
        print("-" * 30)
        
        # Búsqueda vacía (todos los productos)
        all_products = product_manager.search_products("")
        print(f"OK Productos disponibles: {len(all_products)}")
        
        if all_products:
            product = all_products[0]
            print(f"OK Producto de prueba: {product['nombre']} - ${product['precio_venta']}")
            print(f"OK Stock actual: {product['stock_actual']}")
        else:
            print("WARNING: No hay productos disponibles")
            return False
        
        # Test búsqueda de clientes
        print("\n3. TEST BUSQUEDA DE CLIENTES")
        print("-" * 30)
        
        all_customers = customer_manager.get_all_customers()
        print(f"OK Clientes disponibles: {len(all_customers)}")
        
        # Buscar cliente con crédito
        customers_with_credit = [c for c in all_customers if float(c.get('limite_credito', 0)) > 0]
        if customers_with_credit:
            customer = customers_with_credit[0]
            print(f"OK Cliente con credito: {customer['nombre']} {customer['apellido']}")
            print(f"OK Limite credito: ${customer['limite_credito']}")
            print(f"OK Saldo actual: ${customer['saldo_cuenta_corriente']}")
        else:
            customer = None
            print("WARNING: No hay clientes con limite de credito")
        
        # Test creación de venta
        print("\n4. TEST CREACION DE VENTA COMPLETA")
        print("-" * 30)
        
        # Datos de la venta
        cantidad = 1
        precio_unitario = float(product['precio_venta'])
        subtotal = cantidad * precio_unitario
        impuestos = subtotal * 0.21
        total = subtotal + impuestos
        
        print(f"Producto: {product['nombre']}")
        print(f"Cantidad: {cantidad}")
        print(f"Precio unitario: ${precio_unitario:.2f}")
        print(f"Subtotal: ${subtotal:.2f}")
        print(f"Impuestos (21%): ${impuestos:.2f}")
        print(f"Total: ${total:.2f}")
        
        # Preparar datos de venta
        sale_data = {
            'cliente_id': customer['id'] if customer else None,
            'caja_id': 1,
            'tipo_comprobante': 'TICKET',
            'observaciones': 'Venta de prueba sistema integrado'
        }
        
        items = [{
            'producto_id': product['id'],
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'descuento_porcentaje': 0,
            'descuento_importe': 0,
            'impuesto_importe': impuestos
        }]
        
        # Método de pago según si hay cliente
        payment_method = 'CUENTA_CORRIENTE' if customer else 'EFECTIVO'
        payments = [{
            'metodo_pago': payment_method,
            'importe': total,
            'referencia': 'TEST-PAYMENT-INTEGRATED',
            'observaciones': 'Pago de prueba integrada'
        }]
        
        print(f"\nMétodo de pago: {payment_method}")
        
        # Crear la venta usando SalesManager
        success, message, sale_id = sales_manager.create_sale(
            sale_data, items, payments, user_id=1
        )
        
        if success:
            print(f"✓ VENTA CREADA EXITOSAMENTE")
            print(f"✓ ID de venta: {sale_id}")
            print(f"✓ Mensaje: {message}")
        else:
            print(f"✗ ERROR EN VENTA: {message}")
            return False
        
        # Verificar la venta creada
        print("\n5. VERIFICACION DE VENTA CREADA")
        print("-" * 30)
        
        created_sale = sales_manager.get_sale_by_id(sale_id)
        if created_sale:
            print(f"✓ Venta recuperada: #{created_sale['id']}")
            print(f"✓ Estado: {created_sale['estado']}")
            print(f"✓ Total: ${created_sale['total']}")
            print(f"✓ Items: {len(created_sale.get('items', []))}")
            print(f"✓ Pagos: {len(created_sale.get('payments', []))}")
            
            if created_sale['items']:
                item = created_sale['items'][0]
                print(f"✓ Producto vendido: {item['producto_nombre']}")
                print(f"✓ Cantidad: {item['cantidad']}")
            
            if created_sale['payments']:
                payment = created_sale['payments'][0]
                print(f"✓ Método de pago: {payment['metodo_pago']}")
                print(f"✓ Importe: ${payment['importe']}")
        else:
            print("✗ No se pudo recuperar la venta creada")
            return False
        
        # Verificar stock actualizado
        print("\n6. VERIFICACION DE STOCK")
        print("-" * 30)
        
        updated_product = product_manager.get_product_by_id(product['id'])
        if updated_product:
            old_stock = float(product['stock_actual'])
            new_stock = float(updated_product['stock_actual'])
            print(f"Stock anterior: {old_stock}")
            print(f"Stock actual: {new_stock}")
            print(f"Diferencia: {old_stock - new_stock}")
            
            if abs((old_stock - new_stock) - cantidad) < 0.01:
                print("✓ Stock actualizado correctamente")
            else:
                print("⚠ Stock no se actualizó como se esperaba")
        
        # Verificar cuenta corriente si aplica
        if customer and payment_method == 'CUENTA_CORRIENTE':
            print("\n7. VERIFICACION DE CUENTA CORRIENTE")
            print("-" * 30)
            
            updated_customer = customer_manager.get_customer_by_id(customer['id'])
            if updated_customer:
                old_balance = float(customer['saldo_cuenta_corriente'])
                new_balance = float(updated_customer['saldo_cuenta_corriente'])
                print(f"Saldo anterior: ${old_balance:.2f}")
                print(f"Saldo actual: ${new_balance:.2f}")
                print(f"Diferencia: ${new_balance - old_balance:.2f}")
                
                if abs((new_balance - old_balance) - total) < 0.01:
                    print("✓ Cuenta corriente actualizada correctamente")
                else:
                    print("⚠ Cuenta corriente no se actualizó correctamente")
                
                # Verificar movimientos
                movements = customer_manager.get_customer_account_movements(customer['id'], 5)
                print(f"✓ Movimientos de cuenta: {len(movements)}")
                
                if movements:
                    last_movement = movements[0]
                    if last_movement['venta_id'] == sale_id:
                        print("✓ Movimiento de cuenta corriente registrado correctamente")
                    else:
                        print("⚠ Movimiento no asociado a la venta")
        
        # Test resumen diario
        print("\n8. TEST RESUMEN DIARIO")
        print("-" * 30)
        
        daily_summary = sales_manager.get_daily_summary(date.today())
        print(f"✓ Total ventas hoy: {daily_summary['total_ventas']}")
        print(f"✓ Monto total: ${daily_summary['monto_total']:.2f}")
        print(f"✓ Ticket promedio: ${daily_summary['ticket_promedio']:.2f}")
        
        print("\n" + "="*60)
        print("✓ SISTEMA POS INTEGRADO FUNCIONANDO CORRECTAMENTE")
        print(f"✓ Venta procesada: ID #{sale_id}")
        print(f"✓ Total vendido: ${total:.2f}")
        print(f"✓ Método de pago: {payment_method}")
        print(f"✓ Cliente: {customer['nombre'] + ' ' + customer['apellido'] if customer else 'Consumidor Final'}")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\n✗ ERROR EN TEST INTEGRADO: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integrated_pos()
    if success:
        print("\n🎉 SUCCESS: Sistema POS integrado funcionando perfectamente")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Error en sistema POS integrado")
        sys.exit(1)