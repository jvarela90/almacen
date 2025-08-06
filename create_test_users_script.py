#!/usr/bin/env python3
"""
Script para crear usuarios de prueba en AlmacénPro
Agrega usuarios para cada rol disponible en el sistema
"""

import sqlite3
import bcrypt
from pathlib import Path

def find_database():
    """Encontrar archivo de base de datos"""
    possible_names = ["almacen_pro.db", "almacen.db", "database.db"]
    
    for db_name in possible_names:
        if Path(db_name).exists():
            return db_name
    
    print("❌ No se encontró ninguna base de datos")
    return None

def create_test_users():
    """Crear usuarios de prueba para cada rol"""
    
    db_path = find_database()
    if not db_path:
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"✅ Conectado a: {db_path}")
        print("\n🔍 ANALIZANDO ROLES DISPONIBLES:")
        print("=" * 50)
        
        # Obtener roles disponibles
        cursor.execute("SELECT id, nombre, descripcion FROM roles ORDER BY id")
        roles = cursor.fetchall()
        
        if not roles:
            print("❌ No se encontraron roles en el sistema")
            return False
        
        print("📋 Roles disponibles:")
        for role_id, nombre, descripcion in roles:
            print(f"   {role_id}. {nombre} - {descripcion}")
        
        print("\n👥 CREANDO USUARIOS DE PRUEBA:")
        print("=" * 50)
        
        # Usuarios de prueba por rol
        usuarios_prueba = [
            {
                'username': 'gerente',
                'password': 'gerente123',
                'nombre_completo': 'Juan Pérez - Gerente',
                'rol': 'GERENTE',
                'email': 'gerente@almacenpro.com'
            },
            {
                'username': 'vendedor',
                'password': 'vendedor123', 
                'nombre_completo': 'María García - Vendedora',
                'rol': 'VENDEDOR',
                'email': 'vendedor@almacenpro.com'
            },
            {
                'username': 'deposito',
                'password': 'deposito123',
                'nombre_completo': 'Carlos López - Depósito',
                'rol': 'DEPOSITO', 
                'email': 'deposito@almacenpro.com'
            },
            {
                'username': 'admin2',
                'password': 'admin2123',
                'nombre_completo': 'Ana Martín - Admin Suplente',
                'rol': 'ADMINISTRADOR',
                'email': 'admin2@almacenpro.com'
            }
        ]
        
        usuarios_creados = []
        
        for usuario in usuarios_prueba:
            try:
                # Verificar si el usuario ya existe
                cursor.execute("SELECT username FROM usuarios WHERE username = ?", (usuario['username'],))
                existing = cursor.fetchone()
                
                if existing:
                    print(f"⚠️  Usuario '{usuario['username']}' ya existe - OMITIENDO")
                    continue
                
                # Obtener ID del rol
                cursor.execute("SELECT id FROM roles WHERE nombre = ?", (usuario['rol'],))
                rol_result = cursor.fetchone()
                
                if not rol_result:
                    print(f"❌ Rol '{usuario['rol']}' no encontrado para {usuario['username']}")
                    continue
                
                rol_id = rol_result[0]
                
                # Crear hash de contraseña
                password_hash = bcrypt.hashpw(usuario['password'].encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                
                # Insertar usuario
                cursor.execute("""
                    INSERT INTO usuarios (username, password_hash, nombre_completo, email, rol_id, activo)
                    VALUES (?, ?, ?, ?, ?, 1)
                """, (usuario['username'], password_hash, usuario['nombre_completo'], usuario['email'], rol_id))
                
                usuarios_creados.append({
                    'username': usuario['username'],
                    'password': usuario['password'],
                    'nombre': usuario['nombre_completo'],
                    'rol': usuario['rol']
                })
                
                print(f"✅ Usuario creado: {usuario['username']} ({usuario['rol']})")
                
            except Exception as e:
                print(f"❌ Error creando usuario {usuario['username']}: {e}")
        
        # Confirmar cambios
        conn.commit()
        
        print(f"\n🎉 USUARIOS CREADOS EXITOSAMENTE: {len(usuarios_creados)}")
        print("=" * 70)
        
        if usuarios_creados:
            print("\n📋 LISTA COMPLETA DE USUARIOS PARA PROBAR:")
            print("=" * 70)
            
            # Agregar admin existente a la lista
            all_users = [{
                'username': 'admin',
                'password': 'admin123', 
                'nombre': 'Administrador del Sistema',
                'rol': 'ADMINISTRADOR'
            }] + usuarios_creados
            
            print(f"{'USUARIO':<12} {'CONTRASEÑA':<15} {'ROL':<15} {'NOMBRE':<25}")
            print("-" * 70)
            
            for user in all_users:
                print(f"{user['username']:<12} {user['password']:<15} {user['rol']:<15} {user['nombre']:<25}")
            
            print("\n🔍 FUNCIONALIDADES POR ROL:")
            print("=" * 50)
            print("👑 ADMINISTRADOR: Acceso completo - Configuración, usuarios, todos los módulos")
            print("👔 GERENTE:       Ventas, compras, productos, reportes, consulta usuarios")  
            print("🛒 VENDEDOR:      Solo ventas y consulta de productos/clientes")
            print("📦 DEPOSITO:      Productos, gestión de stock, recepción de compras")
            
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("👥 CREANDO USUARIOS DE PRUEBA PARA ALMACÉNPRO")
    print("=" * 60)
    
    success = create_test_users()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ¡USUARIOS DE PRUEBA CREADOS EXITOSAMENTE!")
        print("🚀 Ya puedes probar el sistema con diferentes roles")
        print("💡 Usa las credenciales mostradas arriba para hacer login")
    else:
        print("❌ ERROR CREANDO USUARIOS DE PRUEBA")
        print("💡 Revisa los mensajes de error arriba")
