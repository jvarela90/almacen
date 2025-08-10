#!/usr/bin/env python3
"""
Test Integral del Sistema AlmacénPro v2.0
Programa completo de pruebas para verificar toda la funcionalidad del sistema
"""

import sys
import os
import logging
import traceback
from pathlib import Path
from datetime import datetime, date
from decimal import Decimal
import sqlite3
import shutil

# Añadir el directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importaciones del sistema
from config.settings import Settings
from database.manager import DatabaseManager
from managers.user_manager import UserManager
from managers.product_manager import ProductManager
from managers.sales_manager import SalesManager
from managers.purchase_manager import PurchaseManager
from managers.provider_manager import ProviderManager
from managers.customer_manager import CustomerManager
from managers.financial_manager import FinancialManager
from managers.inventory_manager import InventoryManager
from managers.report_manager import ReportManager
from utils.backup_manager import BackupManager

class SistemaTestManager:
    """Gestor principal de pruebas del sistema"""
    
    def __init__(self):
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.test_db_path = "test_almacen_pro.db"
        self.backup_original_db()
        self.managers = {}
        self.test_results = {}
        self.current_user = None
        
        print("="*80)
        print("SISTEMA DE PRUEBAS INTEGRAL - ALMACÉNPRO v2.0")
        print("="*80)
        print(f"Fecha de prueba: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-"*80)

    def setup_logging(self):
        """Configurar logging para las pruebas"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / f"test_sistema_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", encoding='utf-8'),
                logging.StreamHandler()
            ]
        )

    def backup_original_db(self):
        """Hacer backup de la base de datos original"""
        original_db = Path("data/almacen_pro.db")
        if original_db.exists():
            backup_path = original_db.with_suffix('.backup')
            shutil.copy2(original_db, backup_path)
            print(f"OK Base de datos original respaldada en: {backup_path}")

    def create_test_database(self):
        """Crear base de datos de prueba"""
        print("\n1. INICIALIZACIÓN DE BASE DE DATOS")
        print("-" * 40)
        
        try:
            # Usar la configuración para obtener la ruta de BD
            settings = Settings()
            original_db_path = settings.get_database_path()
            test_db_path = str(Path(original_db_path).parent / "test_almacen_pro.db")
            
            # Eliminar BD de prueba anterior si existe
            if Path(test_db_path).exists():
                Path(test_db_path).unlink()
                print("OK Base de datos de prueba anterior eliminada")
            
            # Crear nueva instancia de BD
            self.db_manager = DatabaseManager(test_db_path)
            print(f"OK Base de datos de prueba creada: {test_db_path}")
            
            # Verificar estructura de tablas
            info = self.db_manager.get_database_info()
            print(f"OK Tablas creadas: {len(info['tables'])}")
            
            for table in info['tables']:
                print(f"  - {table['name']}: {table['records']} registros")
            
            return True
            
        except Exception as e:
            print(f"ERROR Error creando base de datos: {e}")
            self.logger.error(f"Error en create_test_database: {e}")
            return False

    def initialize_managers(self):
        """Inicializar todos los gestores del sistema"""
        print("\n2. INICIALIZACIÓN DE GESTORES")
        print("-" * 40)
        
        try:
            # Gestores principales
            self.managers['user'] = UserManager(self.db_manager)
            print("OK UserManager inicializado")
            
            self.managers['product'] = ProductManager(self.db_manager)
            print("OK ProductManager inicializado")
            
            self.managers['sales'] = SalesManager(self.db_manager, self.managers['product'])
            print("OK SalesManager inicializado")
            
            self.managers['purchase'] = PurchaseManager(self.db_manager, self.managers['product'])
            print("OK PurchaseManager inicializado")
            
            self.managers['provider'] = ProviderManager(self.db_manager)
            print("OK ProviderManager inicializado")
            
            self.managers['customer'] = CustomerManager(self.db_manager)
            print("OK CustomerManager inicializado")
            
            self.managers['financial'] = FinancialManager(self.db_manager)
            print("OK FinancialManager inicializado")
            
            self.managers['inventory'] = InventoryManager(self.db_manager)
            print("OK InventoryManager inicializado")
            
            self.managers['report'] = ReportManager(self.db_manager)
            print("OK ReportManager inicializado")
            
            # Utilidades
            self.managers['backup'] = BackupManager(self.db_manager.db_path)
            print("OK BackupManager inicializado")
            
            return True
            
        except Exception as e:
            print(f"ERROR Error inicializando gestores: {e}")
            self.logger.error(f"Error en initialize_managers: {e}")
            return False

    def test_user_management(self):
        """Probar gestión de usuarios y autenticación"""
        print("\n3. PRUEBAS DE GESTIÓN DE USUARIOS")
        print("-" * 40)
        
        try:
            user_manager = self.managers['user']
            
            # Verificar usuario admin por defecto
            success, message, user_data = user_manager.authenticate_user("admin", "admin123")
            if success:
                print("OK Usuario administrador predeterminado funciona")
                self.current_user = user_data
            else:
                print(f"ERROR Error autenticando admin: {message}")
                return False
            
            # Crear usuario de prueba
            test_user_data = {
                'username': 'test_vendedor',
                'password': 'test123',
                'email': 'test@almacenpro.com',
                'nombre_completo': 'Vendedor de Prueba',
                'rol_nombre': 'VENDEDOR'
            }
            
            success, message, user_id = user_manager.create_user(test_user_data, self.current_user['id'])
            if success:
                print("OK Usuario de prueba creado correctamente")
            else:
                print(f"ERROR Error creando usuario: {message}")
                
            # Probar autenticación del nuevo usuario
            success, message, user_data = user_manager.authenticate_user('test_vendedor', 'test123')
            if success:
                print("OK Autenticación de usuario de prueba exitosa")
            else:
                print(f"ERROR Error autenticando usuario de prueba: {message}")
                
            # Listar todos los usuarios
            users = user_manager.get_all_users()
            print(f"OK Total de usuarios en sistema: {len(users)}")
            
            return True
            
        except Exception as e:
            print(f"ERROR Error en pruebas de usuarios: {e}")
            self.logger.error(f"Error en test_user_management: {e}")
            return False

    def test_product_management(self):
        """Probar gestión de productos"""
        print("\n4. PRUEBAS DE GESTIÓN DE PRODUCTOS")
        print("-" * 40)
        
        try:
            product_manager = self.managers['product']
            
            # Crear producto de prueba
            test_product = {
                'nombre': 'Producto de Prueba',
                'codigo_barras': '1234567890123',
                'codigo_interno': 'PROD-TEST-001',
                'precio_venta': 25.50,
                'precio_compra': 15.00,
                'stock_actual': 100,
                'stock_minimo': 10,
                'descripcion': 'Producto creado para pruebas del sistema',
                'categoria_id': 1  # Categoría general
            }
            
            product_id = product_manager.create_product(test_product)
            if product_id:
                print(f"OK Producto creado con ID: {product_id}")
                
                # Buscar producto por código de barras
                found_product = product_manager.get_product_by_barcode('1234567890123')
                if found_product:
                    print("OK Búsqueda por código de barras exitosa")
                    
                # Buscar producto por nombre
                search_results = product_manager.search_products('Prueba')
                if search_results:
                    print(f"OK Búsqueda por nombre encontró {len(search_results)} resultados")
                    
                # Actualizar stock
                success, message = product_manager.update_stock(
                    product_id=product_id, 
                    new_quantity=50, 
                    movement_type='ENTRADA', 
                    reason='AJUSTE_MANUAL', 
                    user_id=self.current_user['id']
                )
                if success:
                    print("OK Actualización de stock exitosa")
                else:
                    print(f"ERROR Actualizando stock: {message}")
                    
            else:
                print("ERROR Error creando producto de prueba")
                return False
                
            # Crear múltiples productos para pruebas de inventario
            test_products = [
                {'nombre': 'Coca Cola 500ml', 'codigo_barras': '7790001001001', 'codigo_interno': 'CC500', 'precio_venta': 85.00, 'precio_compra': 50.00, 'stock_actual': 50},
                {'nombre': 'Pan Lactal', 'codigo_barras': '7790001001002', 'codigo_interno': 'PL001', 'precio_venta': 120.00, 'precio_compra': 80.00, 'stock_actual': 30},
                {'nombre': 'Leche Entera 1L', 'codigo_barras': '7790001001003', 'codigo_interno': 'LE1L', 'precio_venta': 95.00, 'precio_compra': 65.00, 'stock_actual': 25},
                {'nombre': 'Arroz 1kg', 'codigo_barras': '7790001001004', 'codigo_interno': 'AR1K', 'precio_venta': 180.00, 'precio_compra': 120.00, 'stock_actual': 40}
            ]
            
            created_count = 0
            for prod in test_products:
                if product_manager.create_product(prod):
                    created_count += 1
                    
            print(f"OK {created_count}/{len(test_products)} productos adicionales creados")
            return True
            
        except Exception as e:
            print(f"ERROR Error en pruebas de productos: {e}")
            self.logger.error(f"Error en test_product_management: {e}")
            return False

    def test_customer_management(self):
        """Probar gestión de clientes"""
        print("\n5. PRUEBAS DE GESTIÓN DE CLIENTES")
        print("-" * 40)
        
        try:
            customer_manager = self.managers['customer']
            
            # Crear cliente de prueba
            test_customer = {
                'nombre': 'Juan',
                'apellido': 'Pérez',
                'documento_tipo': 'DNI',
                'documento_numero': '12345678',
                'telefono': '11-1234-5678',
                'email': 'juan.perez@email.com',
                'direccion': 'Av. Principal 123',
                'ciudad': 'Buenos Aires'
            }
            
            customer_id = customer_manager.create_customer(test_customer)
            if customer_id:
                print(f"OK Cliente creado con ID: {customer_id}")
                
                # Buscar cliente
                found_customer = customer_manager.get_customer_by_id(customer_id)
                if found_customer:
                    print("OK Búsqueda de cliente por ID exitosa")
                    
                # Listar todos los clientes
                customers = customer_manager.get_all_customers()
                print(f"OK Total de clientes: {len(customers)}")
                
            else:
                print("ERROR Error creando cliente de prueba")
                return False
                
            return True
            
        except Exception as e:
            print(f"ERROR Error en pruebas de clientes: {e}")
            self.logger.error(f"Error en test_customer_management: {e}")
            return False

    def test_sales_process(self):
        """Probar proceso completo de ventas"""
        print("\n6. PRUEBAS DE PROCESO DE VENTAS")
        print("-" * 40)
        
        try:
            sales_manager = self.managers['sales']
            product_manager = self.managers['product']
            
            # Obtener productos para la venta
            products = product_manager.search_products('Coca Cola')
            if not products:
                print("ERROR No se encontraron productos para vender")
                return False
                
            product = products[0]
            print(f"OK Producto seleccionado: {product['nombre']}")
            
            # Crear venta de prueba
            sale_data = {
                'customer_id': None,  # Venta sin cliente registrado
                'user_id': self.current_user['id'],
                'payment_method': 'EFECTIVO',
                'items': [
                    {
                        'product_id': product['id'],
                        'quantity': 2,
                        'unit_price': float(product['precio_venta']),
                        'discount': 0
                    }
                ],
                'discount': 0,
                'notes': 'Venta de prueba del sistema'
            }
            
            sale_id = sales_manager.create_sale(sale_data)
            if sale_id:
                print(f"OK Venta creada con ID: {sale_id}")
                
                # Verificar la venta
                sale = sales_manager.get_sale_by_id(sale_id)
                if sale:
                    print(f"OK Venta verificada - Total: ${sale['total']}")
                    
                # Verificar actualización de stock
                updated_product = product_manager.get_product_by_id(product['id'])
                if updated_product:
                    stock_difference = float(product['stock_actual']) - float(updated_product['stock_actual'])
                    print(f"OK Stock actualizado - Diferencia: {stock_difference}")
                    
            else:
                print("ERROR Error creando venta de prueba")
                return False
                
            # Obtener ventas del día
            today_sales = sales_manager.get_sales_by_date(datetime.now().date())
            print(f"OK Ventas del día: {len(today_sales)}")
            
            return True
            
        except Exception as e:
            print(f"ERROR Error en pruebas de ventas: {e}")
            self.logger.error(f"Error en test_sales_process: {e}")
            return False

    def test_provider_management(self):
        """Probar gestión de proveedores"""
        print("\n7. PRUEBAS DE GESTIÓN DE PROVEEDORES")
        print("-" * 40)
        
        try:
            provider_manager = self.managers['provider']
            
            # Crear proveedor de prueba
            test_provider = {
                'nombre': 'Distribuidora Test SRL',
                'razon_social': 'Distribuidora Test Sociedad de Responsabilidad Limitada',
                'cuit': '20-12345678-9',
                'telefono': '11-9876-5432',
                'email': 'ventas@distribuidoratest.com',
                'direccion': 'Calle Industrial 456',
                'contacto_nombre': 'María González',
                'observaciones': 'Proveedor creado para pruebas'
            }
            
            provider_id = provider_manager.create_provider(test_provider)
            if provider_id:
                print(f"OK Proveedor creado con ID: {provider_id}")
                
                # Buscar proveedor
                found_provider = provider_manager.get_provider_by_id(provider_id)
                if found_provider:
                    print("OK Búsqueda de proveedor por ID exitosa")
                    
                # Listar todos los proveedores
                providers = provider_manager.get_all_providers()
                print(f"OK Total de proveedores: {len(providers)}")
                
            else:
                print("ERROR Error creando proveedor de prueba")
                return False
                
            return True
            
        except Exception as e:
            print(f"ERROR Error en pruebas de proveedores: {e}")
            self.logger.error(f"Error en test_provider_management: {e}")
            return False

    def test_backup_system(self):
        """Probar sistema de backup"""
        print("\n8. PRUEBAS DE SISTEMA DE BACKUP")
        print("-" * 40)
        
        try:
            backup_manager = self.managers['backup']
            
            # Crear backup manual
            backup_path = backup_manager.create_manual_backup("Backup de prueba del sistema")
            if backup_path:
                print(f"OK Backup manual creado: {backup_path}")
                
                # Verificar que el archivo de backup existe
                if Path(backup_path).exists():
                    print("OK Archivo de backup verificado en disco")
                    
                    # Obtener información del backup
                    backup_info = backup_manager.get_backup_info(backup_path)
                    if backup_info:
                        print(f"OK Información de backup obtenida: {backup_info['size']} MB")
                        
            else:
                print("ERROR Error creando backup manual")
                return False
                
            # Listar backups disponibles
            backups = backup_manager.list_available_backups()
            print(f"OK Backups disponibles: {len(backups)}")
            
            return True
            
        except Exception as e:
            print(f"ERROR Error en pruebas de backup: {e}")
            self.logger.error(f"Error en test_backup_system: {e}")
            return False

    def test_reports_generation(self):
        """Probar generación de reportes"""
        print("\n9. PRUEBAS DE GENERACIÓN DE REPORTES")
        print("-" * 40)
        
        try:
            report_manager = self.managers['report']
            
            # Reporte de ventas del día
            today = datetime.now().date()
            sales_report = report_manager.generate_sales_report(today, today)
            if sales_report:
                print(f"OK Reporte de ventas generado: {len(sales_report)} registros")
            else:
                print("OK Reporte de ventas generado (sin datos)")
                
            # Reporte de productos con stock bajo
            low_stock_report = report_manager.generate_low_stock_report()
            if low_stock_report is not None:
                print(f"OK Reporte de stock bajo: {len(low_stock_report)} productos")
            else:
                print("OK Reporte de stock bajo generado (sin productos)")
                
            # Estadísticas generales
            stats = report_manager.get_dashboard_stats()
            if stats:
                print("OK Estadísticas del dashboard obtenidas:")
                for key, value in stats.items():
                    print(f"  - {key}: {value}")
            else:
                print("ERROR Error obteniendo estadísticas del dashboard")
                return False
                
            return True
            
        except Exception as e:
            print(f"ERROR Error en pruebas de reportes: {e}")
            self.logger.error(f"Error en test_reports_generation: {e}")
            return False

    def test_database_integrity(self):
        """Probar integridad de base de datos"""
        print("\n10. PRUEBAS DE INTEGRIDAD DE BASE DE DATOS")
        print("-" * 40)
        
        try:
            # Verificar integridad SQLite
            integrity_result = self.db_manager.execute_single("PRAGMA integrity_check")
            if integrity_result and integrity_result.get('integrity_check') == 'ok':
                print("OK Integridad de base de datos verificada")
            else:
                print("ERROR Problemas de integridad detectados")
                return False
                
            # Verificar foreign keys
            fk_result = self.db_manager.execute_single("PRAGMA foreign_key_check")
            if not fk_result:
                print("OK Relaciones de claves foráneas correctas")
            else:
                print("ERROR Problemas con claves foráneas detectados")
                
            # Estadísticas de base de datos
            db_info = self.db_manager.get_database_info()
            print(f"OK Base de datos: {db_info['size_mb']} MB")
            print(f"OK Total de registros: {db_info['total_records']}")
            
            return True
            
        except Exception as e:
            print(f"ERROR Error en pruebas de integridad: {e}")
            self.logger.error(f"Error en test_database_integrity: {e}")
            return False

    def run_performance_tests(self):
        """Ejecutar pruebas de rendimiento"""
        print("\n11. PRUEBAS DE RENDIMIENTO")
        print("-" * 40)
        
        try:
            import time
            
            # Prueba de inserción masiva de productos
            start_time = time.time()
            product_manager = self.managers['product']
            
            products_created = 0
            for i in range(100):
                test_product = {
                    'name': f'Producto Performance {i}',
                    'barcode': f'999999999{i:04d}',
                    'sku': f'PERF-{i:04d}',
                    'price': 10.0 + (i * 0.5),
                    'cost': 5.0 + (i * 0.25),
                    'stock': 50 + i,
                    'description': f'Producto {i} para pruebas de rendimiento'
                }
                
                if product_manager.create_product(test_product):
                    products_created += 1
                    
            end_time = time.time()
            duration = end_time - start_time
            
            print(f"OK Creados {products_created}/100 productos en {duration:.2f} segundos")
            print(f"OK Rendimiento: {products_created/duration:.1f} productos/segundo")
            
            # Prueba de búsqueda de productos
            start_time = time.time()
            search_results = product_manager.search_products('Performance')
            search_time = time.time() - start_time
            
            print(f"OK Búsqueda completada en {search_time:.3f} segundos")
            print(f"OK Encontrados {len(search_results)} productos")
            
            return True
            
        except Exception as e:
            print(f"ERROR Error en pruebas de rendimiento: {e}")
            self.logger.error(f"Error en run_performance_tests: {e}")
            return False

    def cleanup_test_data(self):
        """Limpiar datos de prueba"""
        print("\n12. LIMPIEZA DE DATOS DE PRUEBA")
        print("-" * 40)
        
        try:
            # Cerrar conexión de BD
            if hasattr(self, 'db_manager'):
                self.db_manager.close_connection()
                print("OK Conexión de base de datos cerrada")
                
            # Eliminar base de datos de prueba
            test_db_path = Path(self.test_db_path)
            if test_db_path.exists():
                test_db_path.unlink()
                print("OK Base de datos de prueba eliminada")
                
            return True
            
        except Exception as e:
            print(f"ERROR Error en limpieza: {e}")
            self.logger.error(f"Error en cleanup_test_data: {e}")
            return False

    def generate_test_report(self, results):
        """Generar reporte de pruebas"""
        print("\n" + "="*80)
        print("REPORTE FINAL DE PRUEBAS")
        print("="*80)
        
        total_tests = len(results)
        passed_tests = sum(1 for result in results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"Total de pruebas: {total_tests}")
        print(f"Pruebas exitosas: {passed_tests}")
        print(f"Pruebas fallidas: {failed_tests}")
        print(f"Tasa de éxito: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetalle de pruebas:")
        print("-" * 40)
        
        for test_name, result in results.items():
            status = "OK EXITOSA" if result else "ERROR FALLIDA"
            print(f"{test_name}: {status}")
            
        if failed_tests > 0:
            print(f"\nWARNING  {failed_tests} pruebas fallaron. Revisar logs para detalles.")
        else:
            print(f"\nSUCCESS ¡Todas las pruebas pasaron exitosamente!")
            
        print("\nLogs de prueba disponibles en: logs/")
        print("="*80)
        
        return passed_tests == total_tests

    def run_all_tests(self):
        """Ejecutar todas las pruebas del sistema"""
        try:
            # Diccionario de pruebas a ejecutar
            tests = {
                'Creación de Base de Datos': self.create_test_database,
                'Inicialización de Gestores': self.initialize_managers,
                'Gestión de Usuarios': self.test_user_management,
                'Gestión de Productos': self.test_product_management,
                'Gestión de Clientes': self.test_customer_management,
                'Proceso de Ventas': self.test_sales_process,
                'Gestión de Proveedores': self.test_provider_management,
                'Sistema de Backup': self.test_backup_system,
                'Generación de Reportes': self.test_reports_generation,
                'Integridad de Base de Datos': self.test_database_integrity,
                'Pruebas de Rendimiento': self.run_performance_tests
            }
            
            results = {}
            
            # Ejecutar cada prueba
            for test_name, test_function in tests.items():
                try:
                    result = test_function()
                    results[test_name] = result
                except Exception as e:
                    self.logger.error(f"Error en {test_name}: {e}")
                    results[test_name] = False
                    print(f"ERROR Error en {test_name}: {e}")
            
            # Limpiar datos de prueba
            results['Limpieza de Datos'] = self.cleanup_test_data()
            
            # Generar reporte final
            return self.generate_test_report(results)
            
        except Exception as e:
            self.logger.error(f"Error general en run_all_tests: {e}")
            print(f"ERROR Error general en las pruebas: {e}")
            return False

def main():
    """Función principal"""
    try:
        test_manager = SistemaTestManager()
        success = test_manager.run_all_tests()
        return 0 if success else 1
        
    except KeyboardInterrupt:
        print("\nSTOPPED Pruebas interrumpidas por el usuario")
        return 2
        
    except Exception as e:
        print(f"CRITICAL ERROR Error crítico: {e}")
        traceback.print_exc()
        return 3

if __name__ == "__main__":
    exit_code = main()
    print(f"\nCódigo de salida: {exit_code}")
    sys.exit(exit_code)