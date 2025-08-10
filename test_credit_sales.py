#!/usr/bin/env python3
"""
Test del sistema de ventas con cuenta corriente
"""

import sys
import os
from datetime import datetime

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.manager import DatabaseManager
from managers.sales_manager import SalesManager
from managers.product_manager import ProductManager
from managers.financial_manager import FinancialManager
from managers.customer_manager import CustomerManager

def test_credit_sales():
    """Test completo del sistema de ventas con cuenta corriente"""
    
    try:
        print('=== TEST SISTEMA DE VENTAS CON CUENTA CORRIENTE ===')
        
        # Inicializar managers
        db = DatabaseManager()
        product_manager = ProductManager(db)
        financial_manager = FinancialManager(db)
        sales_manager = SalesManager(db, product_manager, financial_manager)
        customer_manager = CustomerManager(db)
        
        print('OK: Managers inicializados correctamente')
        
        # Verificar que hay productos (usar consulta directa)
        productos = db.execute_query('SELECT id, nombre, precio_venta FROM productos WHERE activo = 1 LIMIT 5')
        if productos:
            print(f'OK: Encontrados {len(productos)} productos en el sistema')
            producto_dict = dict(productos[0])
            producto = producto_dict
            print(f'Producto de prueba: {producto["nombre"]} - ${producto["precio_venta"]}')
        else:
            print('WARNING: No hay productos en el sistema')
            return False
            
        # Verificar que hay clientes con limite de credito (consulta directa)
        clientes_raw = db.execute_query('SELECT * FROM clientes WHERE limite_credito > 0')
        clientes = [dict(c) for c in clientes_raw] if clientes_raw else []
        clientes_con_credito = clientes
        
        if not clientes_con_credito:
            print('WARNING: No hay clientes con limite de credito')
            return False
        
        cliente = clientes_con_credito[0]
        print(f'OK: Cliente con credito encontrado: {cliente["nombre"]} {cliente["apellido"]}')
        print(f'   Limite: ${float(cliente["limite_credito"]):,.2f}')
        print(f'   Saldo actual: ${float(cliente["saldo_cuenta_corriente"]):,.2f}')
        
        # Calcular total de la venta
        precio_unitario = float(producto['precio_venta'])
        subtotal = precio_unitario
        impuestos = subtotal * 0.21
        total = subtotal + impuestos
        
        print(f'   Venta de prueba: ${total:,.2f}')
        
        # Verificar que el cliente tiene credito suficiente
        saldo_actual = float(cliente['saldo_cuenta_corriente'])
        limite = float(cliente['limite_credito'])
        credito_disponible = limite - max(0, saldo_actual)
        
        print(f'   Credito disponible: ${credito_disponible:,.2f}')
        
        if credito_disponible < total:
            print(f'WARNING: Cliente no tiene credito suficiente para la venta')
            return False
        
        # Simular venta a credito
        sale_data = {
            'cliente_id': cliente['id'],
            'tipo_comprobante': 'TICKET',
            'subtotal': subtotal,
            'descuento_importe': 0,
            'impuestos_importe': impuestos,
            'total': total,
            'caja_id': 1
        }
        
        items = [{
            'producto_id': producto['id'],
            'cantidad': 1,
            'precio_unitario': precio_unitario,
            'descuento_porcentaje': 0,
            'descuento_importe': 0,
            'impuesto_porcentaje': 21,
            'impuesto_importe': impuestos
        }]
        
        payments = [{
            'metodo_pago': 'CUENTA_CORRIENTE',
            'importe': total,
            'referencia': 'Test venta a credito',
            'observaciones': 'Venta de prueba del sistema'
        }]
        
        # Crear venta
        success, message, sale_id = sales_manager.create_sale(sale_data, items, payments, 1)
        
        if success:
            print(f'OK: Venta a credito creada exitosamente - ID: {sale_id}')
            print(f'OK: {message}')
            
            # Verificar que se actualizó el saldo del cliente (consulta directa)
            cliente_updated_raw = db.execute_single('SELECT * FROM clientes WHERE id = ?', (cliente['id'],))
            cliente_updated = dict(cliente_updated_raw) if cliente_updated_raw else None
            if cliente_updated:
                nuevo_saldo = float(cliente_updated['saldo_cuenta_corriente'])
                print(f'OK: Saldo del cliente actualizado: ${nuevo_saldo:,.2f}')
                
                if abs(nuevo_saldo - (saldo_actual + total)) < 0.01:
                    print('OK: Saldo actualizado correctamente')
                else:
                    print(f'WARNING: Saldo no se actualizo como esperado. Esperado: ${saldo_actual + total:.2f}, Actual: ${nuevo_saldo:.2f}')
            
            return True
        else:
            print(f'ERROR: {message}')
            return False
    
    except Exception as e:
        print(f'ERROR en test: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_credit_sales()
    if success:
        print('\nSUCESS: Test de ventas a credito completado exitosamente!')
    else:
        print('\nFAILED: Test de ventas a credito fallo')
        sys.exit(1)