#!/usr/bin/env python3
"""
Sistema de Diagnósticos - AlmacénPro v2.0
Herramientas de diagnóstico y salud del sistema
"""

import os
import sys
import psutil
import sqlite3
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any
import json

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemDiagnostics:
    """Diagnósticos completos del sistema"""
    
    def __init__(self):
        self.diagnostics = {
            'system_health': {},
            'database_health': {},
            'performance': {},
            'disk_usage': {},
            'logs_analysis': {},
            'recommendations': []
        }
    
    def check_system_resources(self) -> Dict[str, Any]:
        """Verificar recursos del sistema"""
        try:
            # CPU y memoria
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('.')
            
            system_health = {
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'memory_available_gb': round(memory.available / (1024**3), 2),
                'disk_usage': disk.percent,
                'disk_free_gb': round(disk.free / (1024**3), 2),
                'timestamp': datetime.now().isoformat()
            }
            
            # Evaluación de salud
            health_score = 100
            if cpu_percent > 80:
                health_score -= 20
                self.diagnostics['recommendations'].append("⚠️  CPU usage alto - Considerar optimización")
            
            if memory.percent > 85:
                health_score -= 15
                self.diagnostics['recommendations'].append("⚠️  Memoria usage alto - Cerrar aplicaciones innecesarias")
                
            if disk.percent > 90:
                health_score -= 25
                self.diagnostics['recommendations'].append("⚠️  Disco casi lleno - Liberar espacio")
            
            system_health['health_score'] = health_score
            system_health['status'] = 'EXCELLENT' if health_score >= 90 else 'GOOD' if health_score >= 70 else 'WARNING'
            
            self.diagnostics['system_health'] = system_health
            return system_health
            
        except Exception as e:
            logger.error(f"Error checking system resources: {e}")
            return {'error': str(e)}
    
    def check_database_health(self) -> Dict[str, Any]:
        """Verificar salud de la base de datos"""
        try:
            db_health = {}
            db_path = 'data/almacen_pro.db'
            
            if not Path(db_path).exists():
                db_health['status'] = 'ERROR'
                db_health['error'] = 'Base de datos no encontrada'
                return db_health
            
            # Información del archivo
            db_stat = Path(db_path).stat()
            db_health['size_mb'] = round(db_stat.st_size / (1024*1024), 2)
            db_health['last_modified'] = datetime.fromtimestamp(db_stat.st_mtime).isoformat()
            
            # Conectar y verificar
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Verificar integridad
            cursor.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            db_health['integrity'] = integrity
            
            # Información de la BD
            cursor.execute("PRAGMA database_list")
            db_info = cursor.fetchall()
            
            # Contar tablas
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            table_count = cursor.fetchone()[0]
            db_health['table_count'] = table_count
            
            # Estadísticas de algunas tablas principales
            key_tables = ['usuarios', 'productos', 'ventas', 'clientes']
            table_stats = {}
            
            for table in key_tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    table_stats[table] = count
                except sqlite3.OperationalError:
                    table_stats[table] = 'N/A'
            
            db_health['table_stats'] = table_stats
            
            # Configuración WAL
            cursor.execute("PRAGMA journal_mode")
            journal_mode = cursor.fetchone()[0]
            db_health['journal_mode'] = journal_mode
            
            conn.close()
            
            # Evaluación general
            db_health['status'] = 'HEALTHY' if integrity == 'ok' else 'WARNING'
            
            if db_health['size_mb'] > 100:
                self.diagnostics['recommendations'].append("ℹ️  Base de datos grande - Considerar archivado de datos históricos")
            
            self.diagnostics['database_health'] = db_health
            return db_health
            
        except Exception as e:
            logger.error(f"Error checking database health: {e}")
            return {'status': 'ERROR', 'error': str(e)}
    
    def check_performance_metrics(self) -> Dict[str, Any]:
        """Verificar métricas de performance"""
        try:
            performance = {}
            
            # Tiempo de arranque simulado de componentes críticos
            start_time = datetime.now()
            
            # Simular carga de managers
            try:
                from managers.user_manager import UserManager
                from database.manager import DatabaseManager
                
                db = DatabaseManager()
                user_mgr = UserManager(db)
                
                load_time = (datetime.now() - start_time).total_seconds()
                performance['manager_load_time'] = round(load_time, 3)
                
                # Evaluar tiempo de carga
                if load_time < 2.0:
                    performance['load_performance'] = 'EXCELLENT'
                elif load_time < 5.0:
                    performance['load_performance'] = 'GOOD'
                else:
                    performance['load_performance'] = 'SLOW'
                    self.diagnostics['recommendations'].append("🐌 Tiempo de carga lento - Verificar optimizaciones")
                    
            except Exception as e:
                performance['manager_load_error'] = str(e)
                performance['load_performance'] = 'ERROR'
            
            # Verificar archivos de log de performance
            logs_dir = Path('logs')
            if logs_dir.exists():
                log_files = list(logs_dir.glob('*.log'))
                performance['log_files_count'] = len(log_files)
                
                # Analizar logs recientes
                recent_logs = []
                for log_file in log_files[-3:]:  # Últimos 3 logs
                    try:
                        with open(log_file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            recent_logs.append({
                                'file': log_file.name,
                                'size_kb': round(log_file.stat().st_size / 1024, 2),
                                'lines': len(lines)
                            })
                    except Exception:
                        continue
                
                performance['recent_logs'] = recent_logs
            
            self.diagnostics['performance'] = performance
            return performance
            
        except Exception as e:
            logger.error(f"Error checking performance: {e}")
            return {'error': str(e)}
    
    def check_disk_usage(self) -> Dict[str, Any]:
        """Verificar uso de disco por directorios"""
        try:
            disk_usage = {}
            
            # Directorios a verificar
            directories = [
                'data', 'logs', 'backups', 'docs', 
                'managers', 'controllers', 'views'
            ]
            
            for directory in directories:
                dir_path = Path(directory)
                if dir_path.exists():
                    size = self._get_directory_size(dir_path)
                    disk_usage[directory] = {
                        'size_mb': round(size / (1024*1024), 2),
                        'file_count': len(list(dir_path.rglob('*')))
                    }
                else:
                    disk_usage[directory] = {'status': 'NOT_FOUND'}
            
            # Calcular total
            total_size = sum(d.get('size_mb', 0) for d in disk_usage.values() if isinstance(d, dict))
            disk_usage['total_project_size_mb'] = round(total_size, 2)
            
            self.diagnostics['disk_usage'] = disk_usage
            return disk_usage
            
        except Exception as e:
            logger.error(f"Error checking disk usage: {e}")
            return {'error': str(e)}
    
    def _get_directory_size(self, directory: Path) -> int:
        """Calcular tamaño de directorio"""
        total_size = 0
        try:
            for path in directory.rglob('*'):
                if path.is_file():
                    total_size += path.stat().st_size
        except (PermissionError, OSError):
            pass
        return total_size
    
    def analyze_logs(self) -> Dict[str, Any]:
        """Analizar logs para issues"""
        try:
            log_analysis = {
                'error_count': 0,
                'warning_count': 0,
                'critical_count': 0,
                'recent_errors': [],
                'patterns': {}
            }
            
            logs_dir = Path('logs')
            if not logs_dir.exists():
                log_analysis['status'] = 'NO_LOGS'
                return log_analysis
            
            # Analizar logs recientes (últimos 7 días)
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for log_file in logs_dir.glob('*.log'):
                try:
                    if datetime.fromtimestamp(log_file.stat().st_mtime) < cutoff_date:
                        continue
                    
                    with open(log_file, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        
                        for line in lines:
                            if 'ERROR' in line:
                                log_analysis['error_count'] += 1
                                if len(log_analysis['recent_errors']) < 5:
                                    log_analysis['recent_errors'].append(line.strip()[-100:])
                            
                            elif 'WARNING' in line:
                                log_analysis['warning_count'] += 1
                                
                            elif 'CRITICAL' in line:
                                log_analysis['critical_count'] += 1
                
                except Exception:
                    continue
            
            # Evaluación
            if log_analysis['critical_count'] > 0:
                log_analysis['status'] = 'CRITICAL_ISSUES'
                self.diagnostics['recommendations'].append("🚨 Errores críticos en logs - Revisar inmediatamente")
            elif log_analysis['error_count'] > 10:
                log_analysis['status'] = 'HIGH_ERROR_RATE'
                self.diagnostics['recommendations'].append("⚠️  Alto número de errores - Investigar causas")
            else:
                log_analysis['status'] = 'STABLE'
            
            self.diagnostics['logs_analysis'] = log_analysis
            return log_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing logs: {e}")
            return {'error': str(e)}
    
    def generate_recommendations(self) -> List[str]:
        """Generar recomendaciones basadas en diagnósticos"""
        recommendations = self.diagnostics['recommendations'].copy()
        
        # Recomendaciones adicionales basadas en análisis
        system_health = self.diagnostics.get('system_health', {})
        if system_health.get('health_score', 0) < 70:
            recommendations.append("🔧 Sistema requiere atención - Verificar recursos")
        
        db_health = self.diagnostics.get('database_health', {})
        if db_health.get('status') != 'HEALTHY':
            recommendations.append("🗄️  Base de datos requiere mantenimiento")
        
        performance = self.diagnostics.get('performance', {})
        if performance.get('load_performance') == 'SLOW':
            recommendations.append("⚡ Optimizar tiempo de carga - Revisar managers")
        
        if not recommendations:
            recommendations.append("✅ Sistema funcionando óptimamente")
        
        return recommendations
    
    def run_full_diagnostics(self) -> Dict[str, Any]:
        """Ejecutar diagnósticos completos"""
        print("🔍 Ejecutando diagnósticos del sistema...")
        
        # Ejecutar todos los checks
        self.check_system_resources()
        self.check_database_health()
        self.check_performance_metrics()
        self.check_disk_usage()
        self.analyze_logs()
        
        # Generar recomendaciones finales
        self.diagnostics['recommendations'] = self.generate_recommendations()
        self.diagnostics['timestamp'] = datetime.now().isoformat()
        
        return self.diagnostics
    
    def print_report(self):
        """Imprimir reporte formateado"""
        print("\n" + "="*60)
        print("  DIAGNÓSTICOS DEL SISTEMA - AlmacénPro v2.0")
        print("="*60)
        
        # Sistema
        system = self.diagnostics.get('system_health', {})
        if system:
            print(f"\n🖥️  RECURSOS DEL SISTEMA:")
            print(f"   CPU: {system.get('cpu_usage', 0):.1f}%")
            print(f"   Memoria: {system.get('memory_usage', 0):.1f}%")
            print(f"   Disco: {system.get('disk_usage', 0):.1f}%")
            print(f"   Estado: {system.get('status', 'N/A')}")
        
        # Base de datos
        db = self.diagnostics.get('database_health', {})
        if db:
            print(f"\n🗄️  BASE DE DATOS:")
            print(f"   Tamaño: {db.get('size_mb', 0)} MB")
            print(f"   Tablas: {db.get('table_count', 0)}")
            print(f"   Estado: {db.get('status', 'N/A')}")
        
        # Performance
        perf = self.diagnostics.get('performance', {})
        if perf:
            print(f"\n⚡ PERFORMANCE:")
            print(f"   Tiempo de carga: {perf.get('manager_load_time', 0)}s")
            print(f"   Performance: {perf.get('load_performance', 'N/A')}")
        
        # Logs
        logs = self.diagnostics.get('logs_analysis', {})
        if logs:
            print(f"\n📋 ANÁLISIS DE LOGS:")
            print(f"   Errores: {logs.get('error_count', 0)}")
            print(f"   Advertencias: {logs.get('warning_count', 0)}")
            print(f"   Estado: {logs.get('status', 'N/A')}")
        
        # Recomendaciones
        recommendations = self.diagnostics.get('recommendations', [])
        if recommendations:
            print(f"\n💡 RECOMENDACIONES:")
            for rec in recommendations[:5]:  # Mostrar solo las primeras 5
                print(f"   {rec}")
        
        print("\n" + "="*60)
    
    def save_report(self, filename: str = None):
        """Guardar reporte en archivo"""
        if filename is None:
            filename = f"system_diagnostics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        os.makedirs('logs', exist_ok=True)
        filepath = Path('logs') / filename
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(self.diagnostics, f, indent=2, ensure_ascii=False)
            
            print(f"\n💾 Reporte guardado: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"Error guardando reporte: {e}")
            return None

def main():
    """Función principal"""
    print("🚀 AlmacénPro v2.0 - Sistema de Diagnósticos")
    
    diagnostics = SystemDiagnostics()
    
    try:
        # Ejecutar diagnósticos
        results = diagnostics.run_full_diagnostics()
        
        # Mostrar reporte
        diagnostics.print_report()
        
        # Guardar reporte
        diagnostics.save_report()
        
        return 0
        
    except Exception as e:
        print(f"❌ Error ejecutando diagnósticos: {e}")
        logger.error(f"Error in diagnostics: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())