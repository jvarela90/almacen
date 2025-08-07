"""
Script para crear tabla de logs del sistema
"""

import sqlite3
from pathlib import Path

def create_logs_table():
    """Crear tabla de logs de auditoría"""
    
    # Usar la base de datos unificada
    db_path = "data/almacen_pro.db"
    
    try:
        connection = sqlite3.connect(db_path)
        cursor = connection.cursor()
        
        print("🗂️ Creando tabla de logs del sistema...")
        
        # Crear tabla system_logs
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                username VARCHAR(100),
                action VARCHAR(100) NOT NULL,
                table_name VARCHAR(100),
                record_id INTEGER,
                old_values TEXT,  -- JSON
                new_values TEXT,  -- JSON
                ip_address VARCHAR(45),
                user_agent TEXT,
                success BOOLEAN DEFAULT 1,
                error_message TEXT,
                FOREIGN KEY (user_id) REFERENCES usuarios(id)
            )
        """)
        
        # Crear índices para la tabla de logs
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON system_logs(timestamp)",
            "CREATE INDEX IF NOT EXISTS idx_logs_user_id ON system_logs(user_id)",
            "CREATE INDEX IF NOT EXISTS idx_logs_action ON system_logs(action)",
            "CREATE INDEX IF NOT EXISTS idx_logs_table_name ON system_logs(table_name)",
            "CREATE INDEX IF NOT EXISTS idx_logs_success ON system_logs(success)",
            "CREATE INDEX IF NOT EXISTS idx_logs_user_timestamp ON system_logs(user_id, timestamp)"
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
            print(f"   ✅ Índice creado: {index_sql.split('idx_logs_')[1].split(' ')[0]}")
        
        # Crear tabla de configuraciones si no existe (para system_config)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS system_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                config_key VARCHAR(100) UNIQUE NOT NULL,
                config_value TEXT,
                data_type VARCHAR(20) DEFAULT 'STRING',
                category VARCHAR(50) DEFAULT 'GENERAL',
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Insertar log inicial del sistema
        cursor.execute("""
            INSERT INTO system_logs (username, action, success, error_message)
            VALUES ('SYSTEM', 'SYSTEM_LOGS_TABLE_CREATED', 1, NULL)
        """)
        
        connection.commit()
        print("✅ Tabla de logs creada exitosamente")
        
        # Mostrar estadísticas
        cursor.execute("SELECT COUNT(*) FROM system_logs")
        logs_count = cursor.fetchone()[0]
        print(f"📊 Total de logs en sistema: {logs_count}")
        
        connection.close()
        
    except Exception as e:
        print(f"❌ Error creando tabla de logs: {e}")

if __name__ == "__main__":
    create_logs_table()