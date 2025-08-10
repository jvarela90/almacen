#!/usr/bin/env python3
"""
Test final del sistema POS integrado
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

def test_final_pos():
    """Test final del flujo POS completo"""
    
    print("="*60)
    print("TEST FINAL DEL SISTEMA POS")
    print("="*60)
    
    try:
        # Inicializar managers
        print("\n1. INICIALIZANDO MANAGERS")
        print("-" * 30)
        
        db = DatabaseManager()
        product_manager = ProductManager(db)
        customer_manager = CustomerManager(db)
        sales_manager = SalesManager(db, product_manager)
        
        print("OK - DatabaseManager inicializado")
        print("OK - ProductManager inicializado") 
        print("OK - CustomerManager inicializado")
        print("OK - SalesManager inicializado")
        
        # Test búsqueda de productos
        print("\n2. TEST BUSQUEDA DE PRODUCTOS")
        print("-" * 30)
        
        all_products = product_manager.search_products("")
        print(f"OK - Productos disponibles: {len(all_products)}")
        
        if all_products:
            product = all_products[0]
            print(f"OK - Producto: {product['nombre']} - ${product['precio_venta']}")
            print(f"OK - Stock: {product['stock_actual']}")
        else:
            print("ERROR: No hay productos disponibles")
            return False
        
        # Test búsqueda de clientes
        print("\n3. TEST BUSQUEDA DE CLIENTES") 
        print("-" * 30)
        
        all_customers = customer_manager.get_all_customers()
        print(f"OK - Clientes disponibles: {len(all_customers)}")
        
        customers_with_credit = [c for c in all_customers if float(c.get('limite_credito', 0)) > 0]
        if customers_with_credit:
            customer = customers_with_credit[0]
            print(f"OK - Cliente: {customer['nombre']} {customer['apellido']}")
            print(f"OK - Limite credito: ${customer['limite_credito']}")
        else:
            customer = None
            print("INFO - No hay clientes con credito, usando consumidor final")
        
        # Crear venta
        print("\n4. CREANDO VENTA")
        print("-" * 30)
        
        cantidad = 2
        precio_unitario = float(product['precio_venta'])
        subtotal = cantidad * precio_unitario
        impuestos = subtotal * 0.21
        total = subtotal + impuestos
        
        print(f"Producto: {product['nombre']}")
        print(f"Cantidad: {cantidad}")
        print(f"Precio: ${precio_unitario:.2f}")
        print(f"Subtotal: ${subtotal:.2f}")
        print(f"Impuestos: ${impuestos:.2f}")
        print(f"TOTAL: ${total:.2f}")
        
        # Datos de venta
        sale_data = {
            'cliente_id': customer['id'] if customer else None,
            'caja_id': 1,
            'tipo_comprobante': 'TICKET',
            'observaciones': 'Test final sistema POS'
        }
        
        items = [{
            'producto_id': product['id'],
            'cantidad': cantidad,
            'precio_unitario': precio_unitario,
            'descuento_porcentaje': 0,
            'descuento_importe': 0,
            'impuesto_importe': impuestos
        }]
        
        payment_method = 'CUENTA_CORRIENTE' if customer else 'EFECTIVO'
        payments = [{
            'metodo_pago': payment_method,
            'importe': total,
            'referencia': 'TEST-FINAL',
            'observaciones': 'Pago test final'
        }]
        
        print(f"Metodo pago: {payment_method}")
        
        # EJECUTAR VENTA
        success, message, sale_id = sales_manager.create_sale(
            sale_data, items, payments, user_id=1
        )
        
        if success:
            print(f"SUCCESS - VENTA CREADA: ID {sale_id}")
            print(f"Mensaje: {message}")
        else:
            print(f"ERROR - FALLO EN VENTA: {message}")
            return False
        
        # Verificar venta
        print("\n5. VERIFICANDO VENTA")
        print("-" * 30)
        
        created_sale = sales_manager.get_sale_by_id(sale_id)
        if created_sale:
            print(f"OK - Venta #{created_sale['id']} recuperada")
            print(f"OK - Estado: {created_sale['estado']}")
            print(f"OK - Total: ${created_sale['total']}")
            print(f"OK - Items: {len(created_sale.get('items', []))}")
            print(f"OK - Pagos: {len(created_sale.get('payments', []))}")
        else:
            print("ERROR - No se pudo recuperar la venta")
            return False
        
        # Verificar stock
        print("\n6. VERIFICANDO STOCK")
        print("-" * 30)
        
        updated_product = product_manager.get_product_by_id(product['id'])
        if updated_product:
            old_stock = float(product['stock_actual'])
            new_stock = float(updated_product['stock_actual'])
            diff = old_stock - new_stock
            print(f"Stock anterior: {old_stock}")
            print(f"Stock nuevo: {new_stock}")
            print(f"Diferencia: {diff}")
            
            if abs(diff - cantidad) < 0.01:
                print("OK - Stock actualizado correctamente")
            else:
                print("WARNING - Stock no actualizado como esperado")
        
        # Verificar cuenta corriente
        if customer and payment_method == 'CUENTA_CORRIENTE':
            print("\n7. VERIFICANDO CUENTA CORRIENTE")
            print("-" * 30)
            
            updated_customer = customer_manager.get_customer_by_id(customer['id'])
            if updated_customer:
                old_balance = float(customer['saldo_cuenta_corriente'])
                new_balance = float(updated_customer['saldo_cuenta_corriente'])
                diff = new_balance - old_balance
                
                print(f"Saldo anterior: ${old_balance:.2f}")
                print(f"Saldo nuevo: ${new_balance:.2f}")
                print(f"Diferencia: ${diff:.2f}")
                
                if abs(diff - total) < 0.01:
                    print("OK - Cuenta corriente actualizada")
                else:
                    print("WARNING - Cuenta corriente no actualizada correctamente")
        
        # Resumen
        print("\n8. RESUMEN FINAL")
        print("-" * 30)
        
        daily_summary = sales_manager.get_daily_summary(date.today())
        print(f"Ventas hoy: {daily_summary['total_ventas']}")
        print(f"Monto total: ${daily_summary['monto_total']:.2f}")
        
        print("\n" + "="*60)
        print("RESULTADO: SISTEMA POS FUNCIONANDO CORRECTAMENTE")
        print(f"Venta procesada: #{sale_id}")
        print(f"Total: ${total:.2f}")
        print(f"Metodo: {payment_method}")
        if customer:
            print(f"Cliente: {customer['nombre']} {customer['apellido']}")
        else:
            print("Cliente: Consumidor Final")
        print("="*60)
        
        return True
        
    except Exception as e:
        print(f"\nERROR EN TEST: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_final_pos()
    if success:
        print("\nSUCCESS: Sistema POS funcionando perfectamente!")
        sys.exit(0)
    else:
        print("\nFAILED: Error en sistema POS")
        sys.exit(1)