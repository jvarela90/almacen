#!/usr/bin/env python3
"""
Verificar datos en la base de datos
"""

import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.manager import DatabaseManager

def verify_data():
    """Verificar datos en la base de datos"""
    
    try:
        db = DatabaseManager()
        
        print('=== VERIFICACION DE DATOS ===')
        
        # Verificar productos
        print('\nProductos en la BD:')
        result = db.execute_query('SELECT id, nombre, precio_venta FROM productos ORDER BY id DESC LIMIT 10')
        if result:
            for row in result:
                row_dict = dict(row)
                print(f'  ID {row_dict["id"]}: {row_dict["nombre"]} - ${row_dict["precio_venta"]}')
        else:
            print('  No hay productos')
        
        # Verificar clientes
        print('\nClientes en la BD:')
        result = db.execute_query('SELECT id, nombre, apellido, limite_credito, saldo_cuenta_corriente FROM clientes ORDER BY id DESC LIMIT 10')
        if result:
            for row in result:
                row_dict = dict(row)
                print(f'  ID {row_dict["id"]}: {row_dict["nombre"]} {row_dict["apellido"]} - Limite: ${float(row_dict["limite_credito"]):,.2f}, Saldo: ${float(row_dict["saldo_cuenta_corriente"]):,.2f}')
        else:
            print('  No hay clientes')
        
        # Verificar ventas
        print('\nVentas recientes:')
        result = db.execute_query('SELECT id, cliente_id, total, estado, fecha_venta FROM ventas ORDER BY id DESC LIMIT 5')
        if result:
            for row in result:
                row_dict = dict(row)
                print(f'  ID {row_dict["id"]}: Cliente {row_dict["cliente_id"]} - ${float(row_dict["total"]):,.2f} ({row_dict["estado"]}) - {row_dict["fecha_venta"]}')
        else:
            print('  No hay ventas')
        
        return True
        
    except Exception as e:
        print(f'ERROR: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    verify_data()