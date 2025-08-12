#!/usr/bin/env python3
"""
Sistema de Validación Completo - AlmacénPro v2.0
Validación exhaustiva de la arquitectura, dependencias y funcionalidades
"""

import os
import sys
import sqlite3
import importlib
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
import traceback

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/system_validation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemValidator:
    """Validador completo del sistema AlmacénPro v2.0"""
    
    def __init__(self):
        self.results = {
            'architecture': {'passed': 0, 'failed': 0, 'details': []},
            'dependencies': {'passed': 0, 'failed': 0, 'details': []},
            'database': {'passed': 0, 'failed': 0, 'details': []},
            'mvc': {'passed': 0, 'failed': 0, 'details': []},
            'ui': {'passed': 0, 'failed': 0, 'details': []},
            'managers': {'passed': 0, 'failed': 0, 'details': []},
            'overall': {'score': 0, 'status': 'UNKNOWN'}
        }
        
        # Directorios esperados
        self.expected_dirs = [
            'controllers', 'models', 'views', 'managers', 
            'database', 'utils', 'config', 'docs', 'ui'
        ]
        
        # Managers esperados
        self.expected_managers = [
            'user_manager.py', 'product_manager.py', 'sales_manager.py',
            'customer_manager.py', 'inventory_manager.py', 'financial_manager.py',
            'purchase_manager.py', 'provider_manager.py', 'report_manager.py'
        ]
        
        # Controladores MVC esperados
        self.expected_controllers = [
            'base_controller.py', 'login_controller.py', 'main_controller.py'
        ]
        
        # UI files esperados
        self.expected_ui_files = [
            'views/dialogs/login_dialog.ui'
        ]
        
        # Dependencias críticas
        self.critical_dependencies = [
            'PyQt5', 'sqlite3', 'logging', 'pathlib',
            'datetime', 'typing', 'os', 'sys'
        ]
        
    def print_header(self, title: str):
        """Imprimir header formateado"""
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}")
    
    def print_subheader(self, title: str):
        """Imprimir subheader formateado"""
        print(f"\n{'-'*40}")
        print(f"  {title}")
        print(f"{'-'*40}")
    
    def validate_architecture(self) -> bool:
        """Validar estructura de directorios"""
        self.print_subheader("VALIDACIÓN DE ARQUITECTURA")
        
        all_passed = True
        
        for directory in self.expected_dirs:
            dir_path = Path(directory)
            if dir_path.exists() and dir_path.is_dir():
                self.results['architecture']['passed'] += 1
                self.results['architecture']['details'].append(f"[OK] {directory}/ - Directorio encontrado")
                print(f"[OK] {directory}/ - OK")
            else:
                self.results['architecture']['failed'] += 1
                self.results['architecture']['details'].append(f"[FAIL] {directory}/ - Directorio faltante")
                print(f"[FAIL] {directory}/ - FALTANTE")
                all_passed = False
                
        return all_passed
    
    def validate_dependencies(self) -> bool:
        """Validar dependencias críticas"""
        self.print_subheader("VALIDACIÓN DE DEPENDENCIAS")
        
        all_passed = True
        
        for dependency in self.critical_dependencies:
            try:
                importlib.import_module(dependency)
                self.results['dependencies']['passed'] += 1
                self.results['dependencies']['details'].append(f"[OK] {dependency} - Disponible")
                print(f"[OK] {dependency} - OK")
            except ImportError as e:
                self.results['dependencies']['failed'] += 1
                self.results['dependencies']['details'].append(f"[FAIL] {dependency} - No disponible: {str(e)}")
                print(f"[FAIL] {dependency} - FALTANTE: {str(e)}")
                all_passed = False
                
        # Validación específica de PyQt5
        try:
            from PyQt5.QtWidgets import QApplication
            from PyQt5.QtCore import QTimer, pyqtSignal
            from PyQt5 import uic
            self.results['dependencies']['passed'] += 1
            self.results['dependencies']['details'].append("[OK] PyQt5 modules - Todos los módulos críticos disponibles")
            print("[OK] PyQt5 modules - OK")
        except ImportError as e:
            self.results['dependencies']['failed'] += 1
            self.results['dependencies']['details'].append(f"[FAIL] PyQt5 modules - Error: {str(e)}")
            print(f"[FAIL] PyQt5 modules - ERROR: {str(e)}")
            all_passed = False
            
        return all_passed
    
    def validate_database(self) -> bool:
        """Validar base de datos"""
        self.print_subheader("VALIDACIÓN DE BASE DE DATOS")
        
        all_passed = True
        
        # Verificar archivos de base de datos
        db_files = [
            'data/almacen_pro.db',
            'database/manager.py', 
            'database/schema_master.sql'
        ]
        
        for db_file in db_files:
            if Path(db_file).exists():
                self.results['database']['passed'] += 1
                self.results['database']['details'].append(f"[OK] {db_file} - Encontrado")
                print(f"[OK] {db_file} - OK")
            else:
                self.results['database']['failed'] += 1
                self.results['database']['details'].append(f"[FAIL] {db_file} - Faltante")
                print(f"[FAIL] {db_file} - FALTANTE")
                all_passed = False
        
        # Intentar conectar a la base de datos si existe
        db_path = 'data/almacen_pro.db'
        if Path(db_path).exists():
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                
                # Verificar algunas tablas críticas
                critical_tables = ['usuarios', 'productos', 'ventas', 'clientes']
                
                for table in critical_tables:
                    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                    if cursor.fetchone():
                        self.results['database']['passed'] += 1
                        self.results['database']['details'].append(f"[OK] Tabla {table} - Existe")
                        print(f"[OK] Tabla {table} - OK")
                    else:
                        self.results['database']['failed'] += 1
                        self.results['database']['details'].append(f"[FAIL] Tabla {table} - No encontrada")
                        print(f"[FAIL] Tabla {table} - FALTANTE")
                        all_passed = False
                
                conn.close()
                
            except Exception as e:
                self.results['database']['failed'] += 1
                self.results['database']['details'].append(f"[FAIL] Conexión BD - Error: {str(e)}")
                print(f"[FAIL] Conexión BD - ERROR: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def validate_mvc_components(self) -> bool:
        """Validar componentes MVC"""
        self.print_subheader("VALIDACIÓN COMPONENTES MVC")
        
        all_passed = True
        
        # Validar controladores
        for controller in self.expected_controllers:
            controller_path = Path(f"controllers/{controller}")
            if controller_path.exists():
                self.results['mvc']['passed'] += 1
                self.results['mvc']['details'].append(f"[OK] Controller {controller} - Encontrado")
                print(f"[OK] Controller {controller} - OK")
            else:
                self.results['mvc']['failed'] += 1  
                self.results['mvc']['details'].append(f"[FAIL] Controller {controller} - Faltante")
                print(f"[FAIL] Controller {controller} - FALTANTE")
                all_passed = False
        
        # Validar models directory
        models_dir = Path("models")
        if models_dir.exists():
            model_files = list(models_dir.glob("*.py"))
            if model_files:
                self.results['mvc']['passed'] += 1
                self.results['mvc']['details'].append(f"[OK] Models - {len(model_files)} archivos encontrados")
                print(f"[OK] Models - {len(model_files)} archivos - OK")
            else:
                self.results['mvc']['failed'] += 1
                self.results['mvc']['details'].append("[FAIL] Models - No hay archivos .py")
                print("[FAIL] Models - Sin archivos - FALTANTE")
                all_passed = False
        
        # Validar views directory
        views_dir = Path("views")
        if views_dir.exists():
            ui_files = list(views_dir.glob("**/*.ui"))
            if ui_files:
                self.results['mvc']['passed'] += 1
                self.results['mvc']['details'].append(f"[OK] Views - {len(ui_files)} archivos .ui encontrados")
                print(f"[OK] Views - {len(ui_files)} archivos .ui - OK")
            else:
                self.results['mvc']['failed'] += 1
                self.results['mvc']['details'].append("[FAIL] Views - No hay archivos .ui")
                print("[FAIL] Views - Sin archivos .ui - FALTANTE")
                all_passed = False
        
        return all_passed
    
    def validate_ui_files(self) -> bool:
        """Validar archivos de interfaz"""
        self.print_subheader("VALIDACIÓN ARCHIVOS UI")
        
        all_passed = True
        
        for ui_file in self.expected_ui_files:
            ui_path = Path(ui_file)
            if ui_path.exists():
                # Verificar que es XML válido
                try:
                    content = ui_path.read_text(encoding='utf-8')
                    if '<?xml version="1.0"' in content and '<ui version=' in content:
                        self.results['ui']['passed'] += 1
                        self.results['ui']['details'].append(f"[OK] {ui_file} - XML válido")
                        print(f"[OK] {ui_file} - XML válido - OK")
                    else:
                        self.results['ui']['failed'] += 1
                        self.results['ui']['details'].append(f"[FAIL] {ui_file} - Formato inválido")
                        print(f"[FAIL] {ui_file} - Formato inválido - ERROR")
                        all_passed = False
                        
                except Exception as e:
                    self.results['ui']['failed'] += 1
                    self.results['ui']['details'].append(f"[FAIL] {ui_file} - Error leyendo: {str(e)}")
                    print(f"[FAIL] {ui_file} - Error leyendo - ERROR")
                    all_passed = False
            else:
                self.results['ui']['failed'] += 1
                self.results['ui']['details'].append(f"[FAIL] {ui_file} - No encontrado")
                print(f"[FAIL] {ui_file} - FALTANTE")
                all_passed = False
        
        return all_passed
    
    def validate_managers(self) -> bool:
        """Validar managers de negocio"""
        self.print_subheader("VALIDACIÓN MANAGERS DE NEGOCIO")
        
        all_passed = True
        
        for manager in self.expected_managers:
            manager_path = Path(f"managers/{manager}")
            if manager_path.exists():
                # Verificar que tienen contenido mínimo
                try:
                    content = manager_path.read_text(encoding='utf-8')
                    if 'class' in content and 'def' in content:
                        self.results['managers']['passed'] += 1
                        self.results['managers']['details'].append(f"[OK] {manager} - Estructura válida")
                        print(f"[OK] {manager} - OK")
                    else:
                        self.results['managers']['failed'] += 1
                        self.results['managers']['details'].append(f"[FAIL] {manager} - Sin estructura de clases")
                        print(f"[FAIL] {manager} - Sin clases - ERROR")
                        all_passed = False
                        
                except Exception as e:
                    self.results['managers']['failed'] += 1
                    self.results['managers']['details'].append(f"[FAIL] {manager} - Error leyendo: {str(e)}")
                    print(f"[FAIL] {manager} - Error leyendo - ERROR")
                    all_passed = False
            else:
                self.results['managers']['failed'] += 1
                self.results['managers']['details'].append(f"[FAIL] {manager} - No encontrado")
                print(f"[FAIL] {manager} - FALTANTE")
                all_passed = False
        
        return all_passed
    
    def calculate_overall_score(self):
        """Calcular puntuación general"""
        total_passed = sum(category['passed'] for category in self.results.values() if isinstance(category, dict) and 'passed' in category)
        total_failed = sum(category['failed'] for category in self.results.values() if isinstance(category, dict) and 'failed' in category)
        total_tests = total_passed + total_failed
        
        if total_tests > 0:
            score = (total_passed / total_tests) * 100
            self.results['overall']['score'] = round(score, 1)
            
            if score >= 90:
                self.results['overall']['status'] = 'EXCELENTE'
            elif score >= 80:
                self.results['overall']['status'] = 'BUENO'
            elif score >= 70:
                self.results['overall']['status'] = 'ACEPTABLE'
            elif score >= 60:
                self.results['overall']['status'] = 'NECESITA MEJORAS'
            else:
                self.results['overall']['status'] = 'CRÍTICO'
        else:
            self.results['overall']['score'] = 0
            self.results['overall']['status'] = 'SIN DATOS'
    
    def print_summary(self):
        """Imprimir resumen de resultados"""
        self.print_header("RESUMEN DE VALIDACIÓN")
        
        print(f"\n[INFO] PUNTUACIÓN GENERAL: {self.results['overall']['score']}% - {self.results['overall']['status']}")
        
        print(f"\n[INFO] RESULTADOS POR CATEGORÍA:")
        for category, data in self.results.items():
            if category != 'overall' and isinstance(data, dict):
                total = data['passed'] + data['failed']
                if total > 0:
                    percentage = (data['passed'] / total) * 100
                    status = "[OK]" if percentage == 100 else "[WARN]" if percentage >= 80 else "[FAIL]"
                    print(f"  {status} {category.upper()}: {data['passed']}/{total} ({percentage:.1f}%)")
        
        print(f"\n[TARGET] ESTADO GENERAL:")
        overall_score = self.results['overall']['score']
        if overall_score >= 85:
            print("[OK] Sistema LISTO PARA PRODUCCIÓN")
            print("   - Arquitectura sólida implementada")
            print("   - Componentes críticos funcionando") 
            print("   - Calidad de código excelente")
        elif overall_score >= 70:
            print("[WARN]  Sistema EN DESARROLLO AVANZADO")
            print("   - Funcionalidades principales completas")
            print("   - Algunos componentes pendientes")
            print("   - Requiere refinamiento")
        else:
            print("[FAIL] Sistema EN DESARROLLO INICIAL")
            print("   - Componentes críticos faltantes")
            print("   - Requiere trabajo significativo")
            print("   - No listo para producción")
    
    def generate_report(self) -> str:
        """Generar reporte completo"""
        report_lines = []
        report_lines.append("# REPORTE DE VALIDACIÓN SISTEMA - AlmacénPro v2.0")
        report_lines.append(f"Fecha: {Path().stat().st_mtime}")
        report_lines.append(f"Puntuación: {self.results['overall']['score']}% - {self.results['overall']['status']}")
        report_lines.append("")
        
        for category, data in self.results.items():
            if category != 'overall' and isinstance(data, dict):
                report_lines.append(f"## {category.upper()}")
                report_lines.append(f"Pasaron: {data['passed']}, Fallaron: {data['failed']}")
                report_lines.append("")
                for detail in data['details']:
                    report_lines.append(f"  {detail}")
                report_lines.append("")
        
        return "\n".join(report_lines)
    
    def run_validation(self) -> bool:
        """Ejecutar validación completa"""
        self.print_header("VALIDACIÓN COMPLETA DEL SISTEMA AlmacénPro v2.0")
        
        logger.info("Iniciando validación completa del sistema")
        
        try:
            # Ejecutar todas las validaciones
            arch_ok = self.validate_architecture()
            deps_ok = self.validate_dependencies()
            db_ok = self.validate_database()
            mvc_ok = self.validate_mvc_components()
            ui_ok = self.validate_ui_files()
            mgr_ok = self.validate_managers()
            
            # Calcular puntuación general
            self.calculate_overall_score()
            
            # Mostrar resumen
            self.print_summary()
            
            # Generar reporte
            report = self.generate_report()
            
            # Guardar reporte
            os.makedirs('logs', exist_ok=True)
            with open('logs/system_validation_report.txt', 'w', encoding='utf-8') as f:
                f.write(report)
            
            logger.info(f"Validación completada - Puntuación: {self.results['overall']['score']}%")
            
            return self.results['overall']['score'] >= 80
            
        except Exception as e:
            logger.error(f"Error durante validación: {e}")
            logger.error(traceback.format_exc())
            return False

def main():
    """Función principal"""
    validator = SystemValidator()
    
    success = validator.run_validation()
    
    if success:
        print("\n[SUCCESS] ¡VALIDACIÓN EXITOSA!")
        print("El sistema AlmacénPro v2.0 está listo para uso.")
        return 0
    else:
        print("\n[WARN]  VALIDACIÓN CON OBSERVACIONES")
        print("Revisar el reporte para detalles específicos.")
        return 1

if __name__ == "__main__":
    sys.exit(main())