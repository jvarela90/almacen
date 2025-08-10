#!/usr/bin/env python3
"""
Diagnóstico completo del sistema POS
"""

import sys
import os
from datetime import datetime

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.manager import DatabaseManager

def diagnostic_pos():
    """Diagnóstico completo del sistema POS"""
    
    print("="*60)
    print("DIAGNÓSTICO COMPLETO DEL SISTEMA POS")
    print("="*60)
    print(f"Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        db = DatabaseManager()
        issues = []
        
        # 1. VERIFICAR ESTRUCTURA DE TABLAS CRÍTICAS
        print("1. VERIFICACIÓN DE ESTRUCTURA DE TABLAS")
        print("-" * 40)
        
        critical_tables = ['productos', 'clientes', 'ventas', 'detalle_ventas', 'pagos_venta', 'cuenta_corriente']
        
        for table in critical_tables:
            try:
                columns = db.execute_query(f'PRAGMA table_info({table})')
                if columns:
                    print(f"OK Tabla {table}: {len(columns)} columnas")
                    
                    # Verificar columnas críticas según la tabla
                    col_names = [dict(col)['name'] for col in columns]
                    
                    if table == 'productos':
                        required_cols = ['id', 'nombre', 'precio_venta', 'stock_actual', 'codigo_barras', 'activo']
                        missing = [col for col in required_cols if col not in col_names]
                        if missing:
                            issues.append(f"Tabla productos: faltan columnas {missing}")
                    
                    elif table == 'clientes':
                        required_cols = ['id', 'nombre', 'apellido', 'dni_cuit', 'limite_credito', 'saldo_cuenta_corriente']
                        missing = [col for col in required_cols if col not in col_names]
                        if missing:
                            issues.append(f"Tabla clientes: faltan columnas {missing}")
                    
                    elif table == 'ventas':
                        required_cols = ['id', 'cliente_id', 'usuario_id', 'total', 'estado', 'fecha_venta']
                        missing = [col for col in required_cols if col not in col_names]
                        if missing:
                            issues.append(f"Tabla ventas: faltan columnas {missing}")
                            
                else:
                    print(f"ERROR Tabla {table}: NO EXISTE")
                    issues.append(f"Tabla crítica {table} no existe")
                    
            except Exception as e:
                print(f"ERROR verificando tabla {table}: {e}")
                issues.append(f"Error en tabla {table}: {e}")
        
        print()
        
        # 2. VERIFICAR DATOS DE PRUEBA
        print("2. VERIFICACIÓN DE DATOS")
        print("-" * 40)
        
        # Productos
        productos = db.execute_query("SELECT COUNT(*) as count FROM productos WHERE activo = 1")
        productos_count = dict(productos[0])['count'] if productos else 0
        print(f"Productos activos: {productos_count}")
        if productos_count == 0:
            issues.append("No hay productos activos en el sistema")
        
        # Clientes
        clientes = db.execute_query("SELECT COUNT(*) as count FROM clientes")
        clientes_count = dict(clientes[0])['count'] if clientes else 0
        print(f"Clientes registrados: {clientes_count}")
        if clientes_count == 0:
            issues.append("No hay clientes registrados")
        
        # Clientes con crédito
        clientes_credito = db.execute_query("SELECT COUNT(*) as count FROM clientes WHERE limite_credito > 0")
        credito_count = dict(clientes_credito[0])['count'] if clientes_credito else 0
        print(f"Clientes con crédito: {credito_count}")
        
        # Ventas
        ventas = db.execute_query("SELECT COUNT(*) as count FROM ventas")
        ventas_count = dict(ventas[0])['count'] if ventas else 0
        print(f"Ventas registradas: {ventas_count}")
        
        print()
        
        # 3. VERIFICAR TRIGGERS Y CONSTRAINTS
        print("3. VERIFICACIÓN DE INTEGRIDAD")
        print("-" * 40)
        
        # Verificar foreign keys
        try:
            fk_check = db.execute_query("PRAGMA foreign_key_check")
            if fk_check:
                print(f"ERROR Problemas de integridad referencial: {len(fk_check)}")
                for fk in fk_check:
                    issues.append(f"Integridad referencial: {dict(fk)}")
            else:
                print("OK Integridad referencial correcta")
        except Exception as e:
            issues.append(f"Error verificando foreign keys: {e}")
        
        # 4. VERIFICAR MANAGERS
        print("4. VERIFICACIÓN DE MANAGERS")
        print("-" * 40)
        
        try:
            from managers.product_manager import ProductManager
            from managers.customer_manager import CustomerManager
            from managers.sales_manager import SalesManager
            from managers.financial_manager import FinancialManager
            
            # Test ProductManager
            product_manager = ProductManager(db)
            try:
                productos_test = product_manager.search_products("", limit=1)
                print("OK ProductManager funcional")
            except Exception as e:
                print(f"ERROR ProductManager fallo: {e}")
                issues.append(f"ProductManager: {e}")
            
            # Test CustomerManager  
            try:
                customer_manager = CustomerManager(db)
                clientes_test = customer_manager.get_all_customers()
                print("OK CustomerManager funcional")
            except Exception as e:
                print(f"ERROR CustomerManager fallo: {e}")
                issues.append(f"CustomerManager: {e}")
            
            # Test SalesManager
            try:
                financial_manager = FinancialManager(db)
                sales_manager = SalesManager(db, product_manager, financial_manager)
                print("OK SalesManager inicializado")
            except Exception as e:
                print(f"ERROR SalesManager fallo: {e}")
                issues.append(f"SalesManager: {e}")
                
        except ImportError as e:
            print(f"ERROR importando managers: {e}")
            issues.append(f"Import error: {e}")
        
        print()
        
        # 5. VERIFICAR UI COMPONENTS
        print("5. VERIFICACIÓN DE COMPONENTES UI")
        print("-" * 40)
        
        ui_files = [
            'ui/widgets/sales_widget.py',
            'ui/dialogs/customer_selector_dialog.py',
            'ui/dialogs/payment_debt_dialog.py'
        ]
        
        for ui_file in ui_files:
            if os.path.exists(ui_file):
                print(f"OK {ui_file} existe")
            else:
                print(f"ERROR {ui_file} NO EXISTE")
                issues.append(f"Archivo UI faltante: {ui_file}")
        
        print()
        
        # 6. RESUMEN DE PROBLEMAS
        print("6. RESUMEN DE PROBLEMAS ENCONTRADOS")
        print("-" * 40)
        
        if issues:
            print(f"SE ENCONTRARON {len(issues)} PROBLEMAS:")
            for i, issue in enumerate(issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("✓ No se encontraron problemas críticos")
        
        print()
        print("="*60)
        print("FIN DEL DIAGNÓSTICO")
        print("="*60)
        
        return issues
        
    except Exception as e:
        print(f"ERROR CRÍTICO en diagnóstico: {e}")
        import traceback
        traceback.print_exc()
        return [f"Error crítico: {e}"]

if __name__ == "__main__":
    issues = diagnostic_pos()
    if issues:
        print(f"\nSe encontraron {len(issues)} problemas que requieren atención.")
        sys.exit(1)
    else:
        print("\nSistema POS en buen estado.")
        sys.exit(0)