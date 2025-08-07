import sqlite3

# Verificar estructura de la base de datos
conn = sqlite3.connect('data/almacen_pro.db')
cursor = conn.cursor()

print("=== VERIFICACION DEL SISTEMA ===")

# Verificar tabla system_logs
cursor.execute('PRAGMA table_info(system_logs)')
columns = cursor.fetchall()
print("\nColumnas system_logs:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

# Verificar logs existentes
cursor.execute('SELECT * FROM system_logs ORDER BY timestamp DESC LIMIT 5')
logs = cursor.fetchall()
print(f"\nLogs en sistema: {len(logs)}")
for log in logs:
    print(f"  - {log[1]} | {log[3]} | {log[4]} | {'OK' if log[8] else 'ERROR'}")

# Verificar usuarios
cursor.execute('PRAGMA table_info(usuarios)')
user_columns = cursor.fetchall()
print("\nColumnas usuarios:")
for col in user_columns:
    print(f"  {col[1]} ({col[2]})")

cursor.execute('SELECT u.username, r.nombre, u.activo FROM usuarios u LEFT JOIN roles r ON u.rol_id = r.id')
users = cursor.fetchall()
print(f"\nUsuarios del sistema: {len(users)}")
for user in users:
    status = "ACTIVO" if user[2] else "INACTIVO"
    rol = user[1] if user[1] else "SIN ROL"
    print(f"  - {user[0]} ({rol}) - {status}")

# Verificar productos
cursor.execute('SELECT COUNT(*) FROM productos')
productos_count = cursor.fetchone()[0]
print(f"\nProductos en sistema: {productos_count}")

conn.close()
print("\n=== VERIFICACION COMPLETADA ===")