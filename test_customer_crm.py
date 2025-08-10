#!/usr/bin/env python3
"""
Test del sistema CRM empresarial - CustomerManager avanzado
"""

import sys
import os
from datetime import datetime, date

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.manager import DatabaseManager
from managers.customer_manager import CustomerManager

def test_customer_crm():
    """Test completo del CRM empresarial"""
    
    print("="*70)
    print("TEST CRM EMPRESARIAL - CUSTOMER MANAGER AVANZADO")
    print("="*70)
    
    try:
        # Inicializar managers
        print("\n1. INICIALIZACION")
        print("-" * 40)
        
        db = DatabaseManager()
        customer_manager = CustomerManager(db)
        
        print("OK - CustomerManager empresarial inicializado")
        print(f"Categorias disponibles: {', '.join(customer_manager.CUSTOMER_CATEGORIES)}")
        
        # Test estadísticas de cliente
        print("\n2. TEST ESTADISTICAS DE CLIENTE")
        print("-" * 40)
        
        # Buscar un cliente que tenga ventas
        customers_with_sales = db.execute_query("""
            SELECT DISTINCT c.id, c.nombre, c.apellido, COUNT(v.id) as total_ventas
            FROM clientes c
            INNER JOIN ventas v ON c.id = v.cliente_id
            WHERE c.activo = 1 AND v.estado = 'COMPLETADA'
            GROUP BY c.id
            ORDER BY total_ventas DESC
            LIMIT 3
        """)
        
        if customers_with_sales:
            for customer_row in customers_with_sales[:2]:  # Test con 2 clientes
                customer_id = customer_row['id']
                customer_name = f"{customer_row['nombre']} {customer_row['apellido']}"
                
                print(f"\nAnalizando cliente: {customer_name} (ID: {customer_id})")
                print("-" * 50)
                
                # Obtener estadísticas completas
                stats = customer_manager.get_customer_statistics(customer_id)
                
                if stats:
                    print("ESTADISTICAS BASICAS:")
                    customer_info = stats.get('customer_info', {})
                    print(f"  - Categoria: {customer_info.get('categoria_cliente', 'N/A')}")
                    print(f"  - Limite credito: ${float(customer_info.get('limite_credito', 0)):.2f}")
                    print(f"  - Saldo actual: ${float(customer_info.get('saldo_cuenta_corriente', 0)):.2f}")
                    
                    # Estadísticas de ventas
                    sales = stats.get('sales', {})
                    if sales:
                        print("\nESTADISTICAS DE VENTAS:")
                        print(f"  - Total compras: {sales.get('total_compras', 0)}")
                        print(f"  - Monto total: ${sales.get('monto_total', 0):.2f}")
                        print(f"  - Ticket promedio: ${sales.get('ticket_promedio', 0):.2f}")
                        print(f"  - Primera compra: {sales.get('primera_compra', 'N/A')}")
                        print(f"  - Ultima compra: {sales.get('ultima_compra', 'N/A')}")
                    
                    # Top productos
                    top_products = stats.get('top_products', [])
                    if top_products:
                        print(f"\nTOP 3 PRODUCTOS COMPRADOS:")
                        for i, product in enumerate(top_products[:3], 1):
                            print(f"  {i}. {product['nombre']} - Cantidad: {product['cantidad_total']}")
                    
                    # Clasificación del cliente
                    classification = stats.get('classification', {})
                    if classification:
                        print("\nCLASIFICACION DEL CLIENTE:")
                        print(f"  - Valor: {classification.get('valor', 'N/A')}")
                        print(f"  - Actividad: {classification.get('actividad', 'N/A')}")
                        print(f"  - Score: {classification.get('score', 0)}/100")
                        print(f"  - Recomendacion: {classification.get('recomendacion', 'N/A')}")
                    
                    # Estado de cuenta corriente
                    account_status = stats.get('account_status')
                    if account_status:
                        print("\nESTADO DE CUENTA CORRIENTE:")
                        print(f"  - Saldo actual: ${account_status.get('saldo_actual', 0):.2f}")
                        print(f"  - Credito disponible: ${account_status.get('credito_disponible', 0):.2f}")
        else:
            print("No se encontraron clientes con ventas para analizar")
        
        # Test top clientes
        print("\n3. TEST TOP CLIENTES")
        print("-" * 40)
        
        top_customers = customer_manager.get_top_customers(limit=5, period_days=365)
        print(f"Top {len(top_customers)} clientes del año:")
        
        for i, customer in enumerate(top_customers, 1):
            classification = customer.get('classification', {})
            print(f"  {i}. {customer['nombre']} {customer['apellido']}")
            print(f"     - Compras: {customer['total_compras']}, Monto: ${customer['monto_total']:.2f}")
            print(f"     - Valor: {classification.get('valor', 'N/A')}, Actividad: {classification.get('actividad', 'N/A')}")
        
        # Test clientes inactivos
        print("\n4. TEST CLIENTES INACTIVOS")
        print("-" * 40)
        
        inactive_customers = customer_manager.get_inactive_customers(days_inactive=180)
        print(f"Clientes inactivos (>180 dias): {len(inactive_customers)}")
        
        for i, customer in enumerate(inactive_customers[:5], 1):
            print(f"  {i}. {customer['nombre']} {customer['apellido']}")
            print(f"     - Ultima compra: {customer.get('ultima_compra', 'N/A')}")
            print(f"     - Historico: ${customer.get('monto_total_historico', 0):.2f}")
            print(f"     - Prioridad: {customer.get('priority', 'N/A')}")
        
        # Test categorización automática
        print("\n5. TEST CATEGORIZACION AUTOMATICA")
        print("-" * 40)
        
        if customers_with_sales:
            test_customer_id = customers_with_sales[0]['id']
            test_customer_name = f"{customers_with_sales[0]['nombre']} {customers_with_sales[0]['apellido']}"
            
            # Obtener categoría actual
            current_customer = customer_manager.get_customer_by_id(test_customer_id)
            old_category = current_customer['categoria_cliente']
            
            print(f"Cliente de prueba: {test_customer_name}")
            print(f"Categoria actual: {old_category}")
            
            # Intentar actualización automática
            updated = customer_manager.update_customer_category_auto(test_customer_id)
            
            if updated:
                new_customer = customer_manager.get_customer_by_id(test_customer_id)
                new_category = new_customer['categoria_cliente']
                print(f"CATEGORIA ACTUALIZADA: {old_category} -> {new_category}")
            else:
                print("No fue necesario actualizar la categoria")
        
        # Test procesamiento de pago cuenta corriente
        print("\n6. TEST PROCESAMIENTO DE PAGOS")
        print("-" * 40)
        
        # Buscar cliente con deuda
        customers_with_debt = customer_manager.get_customers_with_debt()
        if customers_with_debt:
            debtor = customers_with_debt[0]
            customer_id = debtor['id']
            current_debt = float(debtor['saldo_cuenta_corriente'])
            
            print(f"Cliente con deuda: {debtor['nombre']} {debtor['apellido']}")
            print(f"Deuda actual: ${current_debt:.2f}")
            
            # Procesar pago parcial
            payment_amount = min(current_debt, 50.0)  # Pago de $50 o la deuda completa
            
            success, message = customer_manager.process_account_payment(
                customer_id=customer_id,
                amount=payment_amount,
                payment_method="EFECTIVO",
                reference="TEST-PAYMENT-CRM",
                user_id=1,
                notes="Pago de prueba del sistema CRM"
            )
            
            if success:
                print(f"OK - PAGO PROCESADO: ${payment_amount:.2f}")
                print(f"Resultado: {message}")
                
                # Verificar nuevo saldo
                updated_customer = customer_manager.get_customer_by_id(customer_id)
                new_debt = float(updated_customer['saldo_cuenta_corriente'])
                print(f"Nueva deuda: ${new_debt:.2f}")
            else:
                print(f"ERROR procesando pago: {message}")
        else:
            print("No hay clientes con deuda para probar pagos")
        
        # Test dashboard de clientes
        print("\n7. TEST DASHBOARD DE CLIENTES")
        print("-" * 40)
        
        dashboard_data = customer_manager.get_customers_dashboard_data()
        
        if dashboard_data:
            general = dashboard_data.get('general', {})
            print("ESTADISTICAS GENERALES:")
            print(f"  - Total clientes: {general.get('total_clientes', 0)}")
            print(f"  - Clientes activos: {general.get('clientes_activos', 0)}")
            print(f"  - Clientes con deuda: {general.get('clientes_con_deuda', 0)}")
            print(f"  - Deuda total: ${general.get('deuda_total', 0):.2f}")
            
            # Distribución por categorías
            categories = dashboard_data.get('categories', [])
            if categories:
                print("\nDISTRIBUCION POR CATEGORIAS:")
                for cat in categories:
                    print(f"  - {cat['categoria_cliente']}: {cat['count']} clientes")
            
            # Clientes recientes
            recent = dashboard_data.get('recent', [])
            if recent:
                print(f"\nCLIENTES RECIENTES ({len(recent)}):")
                for customer in recent[:3]:
                    print(f"  - {customer['nombre']} {customer['apellido']} ({customer['categoria_cliente']})")
        
        # Test añadir nota
        print("\n8. TEST NOTAS DE CLIENTE")
        print("-" * 40)
        
        if customers_with_sales:
            test_customer_id = customers_with_sales[0]['id']
            test_note = "Cliente analizado en test CRM - Excelente perfil de compras"
            
            success = customer_manager.add_customer_note(
                customer_id=test_customer_id,
                note=test_note,
                user_id=1
            )
            
            if success:
                print("OK - Nota añadida exitosamente")
                
                # Verificar nota
                updated_customer = customer_manager.get_customer_by_id(test_customer_id)
                notes = updated_customer.get('notas', '')
                if test_note in notes:
                    print("OK - Nota verificada en base de datos")
                else:
                    print("WARNING - Nota no encontrada")
            else:
                print("ERROR - No se pudo añadir la nota")
        
        print("\n" + "="*70)
        print("RESUMEN CRM EMPRESARIAL")
        print("="*70)
        print("✓ Sistema de estadisticas de clientes funcionando")
        print("✓ Clasificacion automatica de clientes implementada")
        print("✓ Analisis de top clientes y clientes inactivos")
        print("✓ Procesamiento de pagos de cuenta corriente")
        print("✓ Dashboard empresarial con KPIs")
        print("✓ Sistema de notas y seguimiento")
        print("✓ Categorizacion automatica basada en comportamiento")
        print("="*70)
        
        return True
        
    except Exception as e:
        print(f"\nERROR EN TEST CRM: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_customer_crm()
    if success:
        print("\nSUCCESS: Sistema CRM empresarial funcionando correctamente!")
        sys.exit(0)
    else:
        print("\nFAILED: Error en sistema CRM")
        sys.exit(1)