#!/usr/bin/env python3
"""
Script ROBUSTO para arreglar el usuario admin
Funciona con cualquier esquema de base de datos
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
    print(f"   Archivos buscados: {', '.join(possible_names)}")
    return None

def analyze_database_structure(cursor):
    """Analizar estructura de la base de datos"""
    print("\n🔍 ANALIZANDO ESTRUCTURA DE LA BASE DE DATOS:")
    print("=" * 60)
    
    # Listar todas las tablas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    print(f"📋 Tablas encontradas: {', '.join(tables)}")
    
    # Si existe la tabla usuarios, mostrar su estructura
    if 'usuarios' in tables:
        cursor.execute("PRAGMA table_info(usuarios)")
        columns_info = cursor.fetchall()
        
        print(f"\n📊 Estructura de tabla 'usuarios':")
        for col_info in columns_info:
            col_id, name, data_type, not_null, default_val, pk = col_info
            pk_mark = " (PRIMARY KEY)" if pk else ""
            null_mark = " NOT NULL" if not_null else ""
            default_mark = f" DEFAULT {default_val}" if default_val else ""
            print(f"   - {name}: {data_type}{pk_mark}{null_mark}{default_mark}")
    
    return tables, [info[1] for info in columns_info] if 'usuarios' in tables else []

def fix_admin_user_robust():
    """Arreglar usuario admin de forma robusta"""
    
    # Encontrar base de datos
    db_path = find_database()
    if not db_path:
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print(f"✅ Conectado a: {db_path}")
        
        # Analizar estructura
        tables, user_columns = analyze_database_structure(cursor)
        
        if 'usuarios' not in tables:
            print("\n❌ No se encontró la tabla 'usuarios'")
            return False
        
        print("\n🔍 BUSCANDO USUARIO ADMIN:")
        print("=" * 40)
        
        # Buscar usuario admin
        cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
        admin_data = cursor.fetchone()
        
        if not admin_data:
            print("❌ Usuario 'admin' no encontrado")
            
            # Mostrar usuarios existentes
            cursor.execute("SELECT username FROM usuarios LIMIT 10")
            existing_users = [row[0] for row in cursor.fetchall()]
            print(f"👥 Usuarios existentes: {', '.join(existing_users)}")
            return False
        
        print(f"✅ Usuario 'admin' encontrado")
        
        # Obtener índice de la columna password_hash
        password_col_index = None
        id_col_index = None
        
        for i, col_name in enumerate(user_columns):
            if col_name.lower() in ['password_hash', 'password', 'contraseña']:
                password_col_index = i
            if col_name.lower() in ['id', 'usuario_id']:
                id_col_index = i
        
        if password_col_index is None:
            print("❌ No se encontró columna de contraseña")
            print(f"   Columnas disponibles: {', '.join(user_columns)}")
            return False
        
        current_hash = admin_data[password_col_index]
        admin_id = admin_data[id_col_index] if id_col_index is not None else "N/A"
        
        print(f"📊 ID: {admin_id}")
        print(f"📊 Hash actual: {current_hash[:50]}...")
        
        print("\n🔧 ACTUALIZANDO CONTRASEÑA:")
        print("=" * 40)
        
        # Crear nuevo hash
        new_password = "admin123"
        new_hash = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        print(f"✅ Nuevo hash generado: {new_hash[:50]}...")
        
        # Actualizar (solo columna de contraseña)
        password_column = user_columns[password_col_index]
        cursor.execute(f"""
            UPDATE usuarios 
            SET {password_column} = ?
            WHERE username = 'admin'
        """, (new_hash,))
        
        # Verificar actualización
        affected_rows = cursor.rowcount
        if affected_rows > 0:
            conn.commit()
            print(f"✅ {affected_rows} registro(s) actualizado(s)")
        else:
            print("❌ No se pudo actualizar el registro")
            return False
        
        print("\n🧪 PROBANDO NUEVA CONTRASEÑA:")
        print("=" * 40)
        
        # Verificar que el hash funciona
        test_result = bcrypt.checkpw(new_password.encode('utf-8'), new_hash.encode('utf-8'))
        print(f"🔐 Verificación: {'✅ CORRECTO' if test_result else '❌ ERROR'}")
        
        conn.close()
        return test_result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"💡 Detalle: {type(e).__name__}")
        return False

if __name__ == "__main__":
    print("🔧 ARREGLANDO USUARIO ADMIN - VERSIÓN ROBUSTA")
    print("=" * 60)
    
    success = fix_admin_user_robust()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ¡USUARIO ADMIN ARREGLADO EXITOSAMENTE!")
        print("💡 Credenciales: admin / admin123")
        print("🚀 Ya puedes ejecutar el programa principal")
    else:
        print("❌ ERROR ARREGLANDO EL USUARIO ADMIN")
        print("💡 Revisa los mensajes de error arriba")
        print("💬 Si necesitas ayuda, comparte la salida completa")