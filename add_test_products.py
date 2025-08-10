#!/usr/bin/env python3
"""
Script para agregar productos de prueba
"""

import sys
import os

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.manager import DatabaseManager
from managers.product_manager import ProductManager

def add_test_products():
    """Agregar productos de prueba al sistema"""
    
    print("Agregando productos de prueba al sistema...")
    print("=" * 50)
    
    try:
        # Inicializar managers
        db = DatabaseManager()
        product_manager = ProductManager(db)
        
        # Productos de prueba
        test_products = [
            {
                'nombre': 'Coca Cola 500ml',
                'codigo_barras': '7790001001001',
                'codigo_interno': 'CC500',
                'precio_venta': 85.00,
                'precio_compra': 50.00,
                'stock_actual': 50,
                'stock_minimo': 10,
                'descripcion': 'Gaseosa Coca Cola 500ml',
                'categoria_id': 1,
                'iva_porcentaje': 21
            },
            {
                'nombre': 'Pan Lactal',
                'codigo_barras': '7790001001002',
                'codigo_interno': 'PL001',
                'precio_venta': 120.00,
                'precio_compra': 80.00,
                'stock_actual': 30,
                'stock_minimo': 5,
                'descripcion': 'Pan lactal blanco 500g',
                'categoria_id': 1,
                'iva_porcentaje': 21
            },
            {
                'nombre': 'Leche Entera 1L',
                'codigo_barras': '7790001001003',
                'codigo_interno': 'LE1L',
                'precio_venta': 95.00,
                'precio_compra': 65.00,
                'stock_actual': 25,
                'stock_minimo': 8,
                'descripcion': 'Leche entera pasteurizada 1 litro',
                'categoria_id': 1,
                'iva_porcentaje': 21
            },
            {
                'nombre': 'Arroz 1kg',
                'codigo_barras': '7790001001004',
                'codigo_interno': 'AR1K',
                'precio_venta': 180.00,
                'precio_compra': 120.00,
                'stock_actual': 40,
                'stock_minimo': 10,
                'descripcion': 'Arroz largo fino 1kg',
                'categoria_id': 1,
                'iva_porcentaje': 21
            },
            {
                'nombre': 'Aceite Girasol 900ml',
                'codigo_barras': '7790001001005',
                'codigo_interno': 'AG900',
                'precio_venta': 220.00,
                'precio_compra': 160.00,
                'stock_actual': 20,
                'stock_minimo': 5,
                'descripcion': 'Aceite de girasol 900ml',
                'categoria_id': 1,
                'iva_porcentaje': 21
            }
        ]
        
        created_products = []
        
        for prod_data in test_products:
            try:
                # Verificar si ya existe por codigo de barras
                existing = db.execute_single(
                    "SELECT id FROM productos WHERE codigo_barras = ?", 
                    (prod_data['codigo_barras'],)
                )
                
                if existing:
                    print(f"WARNING: Producto {prod_data['nombre']} ya existe (ID: {existing['id']})")
                    continue
                
                # Crear producto directamente en BD (evitar problemas con ProductManager)
                product_id = db.execute_insert("""
                    INSERT INTO productos (
                        nombre, codigo_barras, codigo_interno, descripcion,
                        precio_venta, precio_compra, stock_actual, stock_minimo,
                        categoria_id, iva_porcentaje, activo, creado_en
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    prod_data['nombre'],
                    prod_data['codigo_barras'],
                    prod_data['codigo_interno'],
                    prod_data['descripcion'],
                    prod_data['precio_venta'],
                    prod_data['precio_compra'],
                    prod_data['stock_actual'],
                    prod_data['stock_minimo'],
                    prod_data['categoria_id'],
                    prod_data['iva_porcentaje'],
                    True
                ))
                
                if product_id:
                    created_products.append({
                        'id': product_id,
                        'nombre': prod_data['nombre'],
                        'precio_venta': prod_data['precio_venta'],
                        'stock': prod_data['stock_actual']
                    })
                    print(f"OK Producto creado: {prod_data['nombre']} (ID: {product_id})")
                else:
                    print(f"ERROR creando producto: {prod_data['nombre']}")
                    
            except Exception as e:
                print(f"ERROR con producto {prod_data['nombre']}: {e}")
        
        print("\n" + "=" * 50)
        print(f"RESUMEN: {len(created_products)} productos agregados exitosamente")
        
        if created_products:
            print("\nProductos agregados:")
            for prod in created_products:
                print(f"  - ID {prod['id']}: {prod['nombre']} - ${prod['precio_venta']:.2f} (Stock: {prod['stock']})")
        
        return True
        
    except Exception as e:
        print(f"ERROR general: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_test_products()
    if success:
        print("\nExito! Productos de prueba agregados exitosamente!")
    else:
        print("\nError agregando productos de prueba")
        sys.exit(1)