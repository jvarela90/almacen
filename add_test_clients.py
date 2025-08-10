#!/usr/bin/env python3
"""
Script para agregar clientes de prueba con funcionalidad de cuenta corriente
"""

import sys
import os
from datetime import datetime, date
from decimal import Decimal

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.manager import DatabaseManager
from managers.customer_manager import CustomerManager

def add_test_clients():
    """Agregar clientes de prueba al sistema"""
    
    print("Agregando clientes de prueba al sistema...")
    print("=" * 50)
    
    try:
        # Inicializar managers
        db = DatabaseManager()
        customer_manager = CustomerManager(db)
        
        # Clientes de prueba
        test_clients = [
            {
                'nombre': 'Juan Carlos',
                'apellido': 'Pérez García',
                'documento_tipo': 'DNI',
                'documento_numero': '12345678',
                'telefono': '11-1234-5678',
                'email': 'juan.perez@email.com',
                'direccion': 'Av. Rivadavia 1234, CABA',
                'ciudad': 'Buenos Aires',
                'limite_credito': 50000.00,
                'categoria_cliente': 'MAYORISTA',
                'descuento_porcentaje': 5.0,
                'notas': 'Cliente mayorista con descuento especial'
            },
            {
                'nombre': 'María Elena',
                'apellido': 'González López',
                'documento_tipo': 'DNI', 
                'documento_numero': '87654321',
                'telefono': '11-8765-4321',
                'email': 'maria.gonzalez@email.com',
                'direccion': 'Calle Florida 567, CABA',
                'ciudad': 'Buenos Aires',
                'limite_credito': 25000.00,
                'categoria_cliente': 'MINORISTA',
                'descuento_porcentaje': 0.0,
                'notas': 'Cliente frecuente con buen historial crediticio'
            },
            {
                'nombre': 'Roberto',
                'apellido': 'Martínez Silva',
                'documento_tipo': 'CUIT',
                'documento_numero': '20-23456789-0',
                'telefono': '11-2345-6789',
                'email': 'roberto.martinez@empresa.com',
                'direccion': 'Av. Corrientes 890, CABA',
                'ciudad': 'Buenos Aires',
                'limite_credito': 100000.00,
                'categoria_cliente': 'CORPORATIVO',
                'descuento_porcentaje': 10.0,
                'notas': 'Cliente corporativo - Empresa constructora'
            },
            {
                'nombre': 'Ana',
                'apellido': 'Rodríguez',
                'documento_tipo': 'DNI',
                'documento_numero': '34567890',
                'telefono': '11-3456-7890',
                'email': 'ana.rodriguez@email.com',
                'direccion': 'San Martín 234, Villa Ballester',
                'ciudad': 'Villa Ballester',
                'limite_credito': 15000.00,
                'categoria_cliente': 'MINORISTA',
                'descuento_porcentaje': 2.5,
                'notas': 'Cliente de barrio con cuenta corriente pequeña'
            },
            {
                'nombre': 'Carlos',
                'apellido': 'Fernández',
                'documento_tipo': 'DNI',
                'documento_numero': '45678901',
                'telefono': '11-4567-8901',
                'email': 'carlos.fernandez@email.com',
                'direccion': 'Belgrano 456, San Isidro',
                'ciudad': 'San Isidro',
                'limite_credito': 75000.00,
                'categoria_cliente': 'MAYORISTA',
                'descuento_porcentaje': 7.5,
                'notas': 'Distribuidor de productos de limpieza'
            }
        ]
        
        created_clients = []
        
        for client_data in test_clients:
            try:
                # Verificar si ya existe
                existing = db.execute_single(
                    "SELECT id FROM clientes WHERE dni_cuit = ?", 
                    (client_data['documento_numero'],)
                )
                
                if existing:
                    print(f"WARNING: Cliente {client_data['nombre']} {client_data['apellido']} ya existe (ID: {existing['id']})")
                    continue
                
                # Insertar cliente directamente en la BD
                client_id = db.execute_insert("""
                    INSERT INTO clientes (
                        nombre, apellido, dni_cuit, direccion, telefono, email,
                        limite_credito, saldo_cuenta_corriente, descuento_porcentaje,
                        categoria_cliente, activo, notas, creado_en
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    client_data['nombre'],
                    client_data['apellido'],
                    client_data['documento_numero'],
                    client_data['direccion'],
                    client_data['telefono'],
                    client_data['email'],
                    client_data['limite_credito'],
                    0.00,  # saldo inicial
                    client_data['descuento_porcentaje'],
                    client_data['categoria_cliente'],
                    True,  # activo
                    client_data['notas'],
                    datetime.now()
                ))
                
                if client_id:
                    created_clients.append({
                        'id': client_id,
                        'nombre': client_data['nombre'],
                        'apellido': client_data['apellido'],
                        'limite_credito': client_data['limite_credito'],
                        'categoria': client_data['categoria_cliente']
                    })
                    print(f"OK Cliente creado: {client_data['nombre']} {client_data['apellido']} (ID: {client_id})")
                else:
                    print(f"ERROR creando cliente: {client_data['nombre']} {client_data['apellido']}")
                    
            except Exception as e:
                print(f"ERROR con cliente {client_data['nombre']} {client_data['apellido']}: {e}")
        
        print("\n" + "=" * 50)
        print(f"RESUMEN: {len(created_clients)} clientes agregados exitosamente")
        
        if created_clients:
            print("\nClientes agregados:")
            for client in created_clients:
                print(f"  - ID {client['id']}: {client['nombre']} {client['apellido']} ({client['categoria']}) - Limite: ${client['limite_credito']:,.2f}")
        
        return True
        
    except Exception as e:
        print(f"ERROR general: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = add_test_clients()
    if success:
        print("\nExito! Clientes de prueba agregados exitosamente!")
    else:
        print("\nError agregando clientes de prueba")
        sys.exit(1)