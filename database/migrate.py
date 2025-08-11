#!/usr/bin/env python3
"""
Script de gestión de migraciones para AlmacénPro v2.0
Wrapper para comandos Alembic con configuración específica del proyecto
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Agregar el directorio del proyecto al path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from config.env_config import EnvironmentConfig


class MigrationManager:
    """Gestor de migraciones de base de datos"""
    
    def __init__(self):
        self.project_root = project_root
        self.alembic_ini = self.project_root / "alembic.ini"
        self.migrations_dir = self.project_root / "database" / "migrations"
        
        # Verificar que existe configuración de Alembic
        if not self.alembic_ini.exists():
            raise FileNotFoundError(
                f"No se encontró alembic.ini en {self.alembic_ini}. "
                "Ejecute primero la configuración inicial."
            )
    
    def run_alembic_command(self, args: list):
        """Ejecutar comando alembic con la configuración del proyecto"""
        cmd = [
            sys.executable, "-m", "alembic",
            "-c", str(self.alembic_ini)
        ] + args
        
        try:
            print(f"Ejecutando: {' '.join(cmd)}")
            result = subprocess.run(cmd, cwd=str(self.project_root), check=True)
            return result.returncode == 0
        except subprocess.CalledProcessError as e:
            print(f"Error ejecutando migración: {e}")
            return False
    
    def check_database_connection(self):
        """Verificar conexión a base de datos"""
        try:
            db_config = EnvironmentConfig.get_database_config()
            if db_config['type'] == 'sqlite':
                db_path = Path(db_config['path'])
                if not db_path.parent.exists():
                    db_path.parent.mkdir(parents=True, exist_ok=True)
                    print(f"Creado directorio: {db_path.parent}")
            
            print(f"Configuración de BD: {db_config['type']}")
            if db_config['type'] == 'sqlite':
                print(f"Archivo SQLite: {db_config['path']}")
            
            return True
        except Exception as e:
            print(f"Error verificando conexión: {e}")
            return False
    
    def init_migrations(self):
        """Inicializar sistema de migraciones (solo primera vez)"""
        print("=== Inicializando Sistema de Migraciones ===")
        
        if not self.check_database_connection():
            return False
        
        # Crear directorio de migraciones si no existe
        self.migrations_dir.mkdir(parents=True, exist_ok=True)
        
        # Verificar si ya está inicializado
        versions_dir = self.migrations_dir / "versions"
        if versions_dir.exists() and list(versions_dir.glob("*.py")):
            print("El sistema de migraciones ya está inicializado.")
            return True
        
        print("Sistema de migraciones configurado correctamente.")
        return True
    
    def create_migration(self, message: str, auto: bool = False):
        """Crear nueva migración"""
        print(f"=== Creando Migración: {message} ===")
        
        if not self.check_database_connection():
            return False
        
        args = ["revision"]
        if auto:
            args.append("--autogenerate")
        args.extend(["-m", message])
        
        return self.run_alembic_command(args)
    
    def upgrade_database(self, revision: str = "head"):
        """Aplicar migraciones (actualizar base de datos)"""
        print(f"=== Aplicando Migraciones: {revision} ===")
        
        if not self.check_database_connection():
            return False
        
        return self.run_alembic_command(["upgrade", revision])
    
    def downgrade_database(self, revision: str):
        """Revertir migraciones"""
        print(f"=== Revirtiendo Migraciones: {revision} ===")
        
        if not self.check_database_connection():
            return False
        
        return self.run_alembic_command(["downgrade", revision])
    
    def show_current_revision(self):
        """Mostrar revisión actual de la base de datos"""
        print("=== Revisión Actual ===")
        return self.run_alembic_command(["current"])
    
    def show_migration_history(self):
        """Mostrar historial de migraciones"""
        print("=== Historial de Migraciones ===")
        return self.run_alembic_command(["history", "--verbose"])
    
    def show_pending_migrations(self):
        """Mostrar migraciones pendientes"""
        print("=== Migraciones Pendientes ===")
        return self.run_alembic_command(["show", "head"])


def main():
    """Función principal del script"""
    parser = argparse.ArgumentParser(
        description="Gestor de migraciones para AlmacénPro v2.0"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")
    
    # Inicializar
    subparsers.add_parser("init", help="Inicializar sistema de migraciones")
    
    # Crear migración
    create_parser = subparsers.add_parser("create", help="Crear nueva migración")
    create_parser.add_argument("message", help="Mensaje descriptivo de la migración")
    create_parser.add_argument("--auto", action="store_true", 
                              help="Autogenerar migración desde cambios en modelos")
    
    # Aplicar migraciones
    upgrade_parser = subparsers.add_parser("upgrade", help="Aplicar migraciones")
    upgrade_parser.add_argument("revision", nargs="?", default="head",
                               help="Revisión objetivo (default: head)")
    
    # Revertir migraciones
    downgrade_parser = subparsers.add_parser("downgrade", help="Revertir migraciones")
    downgrade_parser.add_argument("revision", help="Revisión objetivo")
    
    # Información
    subparsers.add_parser("current", help="Mostrar revisión actual")
    subparsers.add_parser("history", help="Mostrar historial de migraciones")
    subparsers.add_parser("pending", help="Mostrar migraciones pendientes")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        manager = MigrationManager()
        
        if args.command == "init":
            success = manager.init_migrations()
        elif args.command == "create":
            success = manager.create_migration(args.message, auto=args.auto)
        elif args.command == "upgrade":
            success = manager.upgrade_database(args.revision)
        elif args.command == "downgrade":
            success = manager.downgrade_database(args.revision)
        elif args.command == "current":
            success = manager.show_current_revision()
        elif args.command == "history":
            success = manager.show_migration_history()
        elif args.command == "pending":
            success = manager.show_pending_migrations()
        else:
            print(f"Comando no reconocido: {args.command}")
            success = False
        
        if not success:
            sys.exit(1)
            
    except Exception as e:
        print(f"Error ejecutando comando: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()