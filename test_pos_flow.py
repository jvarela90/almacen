#!/usr/bin/env python3
"""
Test del flujo completo del POS
"""

import sys
import os
from datetime import datetime

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.manager import DatabaseManager
from managers.product_manager import ProductManager
from managers.customer_manager import CustomerManager
from managers.sales_manager import SalesManager
from managers.financial_manager import FinancialManager

def test_pos_flow():
    """Test completo del flujo POS: productos -> clientes -> venta -> pago"""
    
    print("="*60)
    print("TEST DEL FLUJO COMPLETO DEL POS")
    print("="*60)
    
    errors = []
    
    try:
        db = DatabaseManager()
        
        # PASO 1: INICIALIZAR MANAGERS
        print("\n1. INICIALIZACIÓN DE MANAGERS")
        print("-" * 30)
        
        try:
            product_manager = ProductManager(db)
            print("OK ProductManager inicializado")
        except Exception as e:
            print(f"ERROR ProductManager: {e}")
            errors.append(f"ProductManager: {e}")
            return False
        
        try:
            # CustomerManager con manejo de errores
            customer_manager = CustomerManager(db)
            print("OK CustomerManager inicializado")
        except Exception as e:
            print(f"ERROR CustomerManager: {e}")
            errors.append(f"CustomerManager: {e}")
            # Continuar sin CustomerManager por ahora
            customer_manager = None
        
        try:
            financial_manager = FinancialManager(db)
            sales_manager = SalesManager(db, product_manager, financial_manager)
            print("OK SalesManager y FinancialManager inicializados")
        except Exception as e:
            print(f"ERROR SalesManager/FinancialManager: {e}")
            errors.append(f"SalesManager: {e}")
            return False
        
        # PASO 2: BUSCAR PRODUCTOS
        print("\n2. BÚSQUEDA DE PRODUCTOS")
        print("-" * 30)
        
        try:
            # Probar búsqueda vacía (todos los productos)
            productos = product_manager.search_products("", limit=3)
            if productos:
                print(f"OK Encontrados {len(productos)} productos")
                producto = productos[0]
                print(f"   Producto seleccionado: {producto.get('nombre')} - ${producto.get('precio_venta')}")
            else:
                print("ERROR No se encontraron productos")
                return False
        except Exception as e:
            print(f"ERROR Búsqueda de productos: {e}")
            errors.append(f"Búsqueda productos: {e}")
            
            # Intentar búsqueda directa
            try:
                productos_direct = db.execute_query("SELECT id, nombre, precio_venta, stock_actual FROM productos WHERE activo = 1 LIMIT 3")
                if productos_direct:
                    productos = [dict(p) for p in productos_direct]
                    producto = productos[0]
                    print(f"OK Búsqueda directa exitosa: {len(productos)} productos")
                    print(f"   Producto: {producto['nombre']} - ${producto['precio_venta']}")
                else:
                    return False
            except Exception as e2:
                print(f"ERROR Búsqueda directa también falló: {e2}")
                return False
        
        # PASO 3: SELECCIONAR CLIENTE (OPCIONAL)
        print("\n3. SELECCIÓN DE CLIENTE")
        print("-" * 30)
        
        cliente_selected = None
        if customer_manager:
            try:
                clientes = customer_manager.get_all_customers()
                if clientes:
                    # Buscar cliente con límite de crédito
                    clientes_con_credito = [c for c in clientes if float(c.get('limite_credito', 0)) > 0]
                    if clientes_con_credito:
                        cliente_selected = clientes_con_credito[0]
                        print(f"OK Cliente seleccionado: {cliente_selected['nombre']} {cliente_selected['apellido']}")
                        print(f"   Límite crédito: ${float(cliente_selected['limite_credito']):,.2f}")
                    else:
                        print("WARNING No hay clientes con crédito, venta será sin cliente")
                else:
                    print("WARNING No hay clientes registrados")
            except Exception as e:
                print(f"ERROR Obteniendo clientes: {e}")
                errors.append(f"Obtener clientes: {e}")
        else:
            print("WARNING CustomerManager no disponible, venta sin cliente")
        
        # PASO 4: CREAR VENTA
        print("\n4. CREACIÓN DE VENTA")
        print("-" * 30)
        
        try:
            # Calcular totales
            cantidad = 2
            precio_unitario = float(producto['precio_venta'])
            subtotal = cantidad * precio_unitario
            impuestos = subtotal * 0.21
            total = subtotal + impuestos
            
            print(f"   Cantidad: {cantidad}")
            print(f"   Precio unitario: ${precio_unitario:.2f}")
            print(f"   Subtotal: ${subtotal:.2f}")
            print(f"   Impuestos (21%): ${impuestos:.2f}")
            print(f"   Total: ${total:.2f}")
            
            # Datos de la venta
            sale_data = {
                'cliente_id': cliente_selected['id'] if cliente_selected else None,
                'tipo_comprobante': 'TICKET',
                'subtotal': subtotal,
                'descuento_importe': 0,
                'impuestos_importe': impuestos,
                'total': total,
                'caja_id': 1
            }
            
            # Items de la venta
            items = [{
                'producto_id': producto['id'],
                'cantidad': cantidad,
                'precio_unitario': precio_unitario,
                'descuento_porcentaje': 0,
                'descuento_importe': 0,
                'impuesto_porcentaje': 21,
                'impuesto_importe': impuestos
            }]
            
            # Determinar método de pago
            metodo_pago = 'EFECTIVO'
            if cliente_selected:
                # Preguntar si usar cuenta corriente
                saldo_actual = float(cliente_selected.get('saldo_cuenta_corriente', 0))
                limite = float(cliente_selected.get('limite_credito', 0))
                credito_disponible = limite - max(0, saldo_actual)
                
                if credito_disponible >= total:
                    metodo_pago = 'CUENTA_CORRIENTE'  # Usar crédito
                    print(f"   Usando CUENTA CORRIENTE (crédito disponible: ${credito_disponible:.2f})")
                else:
                    print(f"   Crédito insuficiente, usando EFECTIVO")
            
            # Datos del pago
            payments = [{
                'metodo_pago': metodo_pago,
                'importe': total,
                'referencia': 'Test POS Flow',
                'observaciones': 'Venta de prueba completa'
            }]
            
            # Crear la venta
            success, message, sale_id = sales_manager.create_sale(sale_data, items, payments, 1)
            
            if success:
                print(f"OK Venta creada exitosamente - ID: {sale_id}")
                print(f"   {message}")
                
                # Verificar la venta
                venta_verificacion = db.execute_single("SELECT * FROM ventas WHERE id = ?", (sale_id,))
                if venta_verificacion:
                    venta = dict(venta_verificacion)
                    print(f"   Verificación: Estado={venta['estado']}, Total=${float(venta['total']):.2f}")
                
                return True
            else:
                print(f"ERROR Creando venta: {message}")
                errors.append(f"Crear venta: {message}")
                return False
                
        except Exception as e:
            print(f"ERROR en creación de venta: {e}")
            errors.append(f"Crear venta: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"ERROR GENERAL: {e}")
        errors.append(f"Error general: {e}")
        return False
    
    finally:
        print("\n" + "="*60)
        print("RESUMEN DEL TEST")
        print("="*60)
        
        if errors:
            print(f"SE ENCONTRARON {len(errors)} ERRORES:")
            for i, error in enumerate(errors, 1):
                print(f"  {i}. {error}")
        else:
            print("EXITO: Test completado sin errores")

if __name__ == "__main__":
    success = test_pos_flow()
    if success:
        print("\nSUCCESS: Flujo POS funcionando correctamente")
    else:
        print("\nFAILED: Problemas detectados en el flujo POS")
        sys.exit(1)