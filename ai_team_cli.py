#!/usr/bin/env python3
"""
AI Team CLI - Punto de entrada principal para el sistema colaborativo
Permite ejecutar comandos del equipo de desarrollo AI desde la terminal
"""

import sys
import argparse
import asyncio
from pathlib import Path

# Agregar directorio raz al path para imports
sys.path.insert(0, str(Path(__file__).parent))

from ai_agent import (
    CollaborativeAISystem,
    EnhancedAIDevOps, 
    create_collaborative_task,
    run_collaborative_review,
    TaskPriority
)

def print_banner():
    """Muestra el banner del sistema"""
    banner = """
================================================================================
                          AI DEVELOPMENT TEAM                           
                                                                              
  Claude Code (Local) + ChatGPT (Remote) = Senior Development Team           
                                                                              
  Comandos disponibles:                                                       
    * create-task    - Crear nueva tarea colaborativa                        
    * review-task    - Ejecutar revision colaborativa                        
    * list-tasks     - Listar tareas del sistema                            
    * dev-cycle      - Ejecutar ciclo completo de desarrollo                 
    * stats          - Estadisticas del sistema colaborativo                 
    * demo           - Demostracion del flujo colaborativo                   
                                                                              
================================================================================
"""
    print(banner)

def cmd_create_task(args):
    """Crear nueva tarea colaborativa"""
    try:
        print("[EJECUTANDO] Creando nueva tarea colaborativa...")
        
        task = create_collaborative_task(
            title=args.title,
            description=args.description or f"Implementar: {args.title}",
            priority=args.priority,
            proposed_by=args.proposed_by,
            files_affected=args.files.split(',') if args.files else []
        )
        
        print(f"[OK] Tarea creada exitosamente:")
        print(f"   ID: {task.id}")
        print(f"   Ttulo: {task.title}")
        print(f"   Prioridad: {task.priority.value}")
        print(f"   Propuesto por: {task.proposed_by.value}")
        
        if task.files_affected:
            print(f"   Archivos afectados: {', '.join(task.files_affected)}")
        
    except Exception as e:
        print(f"[ERROR] Error creando tarea: {e}")
        sys.exit(1)

async def cmd_review_task(args):
    """Ejecutar revisin colaborativa de una tarea"""
    try:
        print(f"[ANALIZANDO] Iniciando revisin colaborativa para tarea: {args.task_id}")
        print("   [CLAUDE] Claude Code analizando factibilidad tcnica...")
        print("   [CHATGPT] ChatGPT revisando arquitectura y mejores prcticas...")
        
        result = await run_collaborative_review(args.task_id)
        
        consensus = result["consensus"]
        print(f"\n[OK] Revisin completada:")
        print(f"   Tipo de consenso: {consensus['consensus_type']}")
        print(f"   Recomendacin: {consensus['recommendation']}")
        print(f"   Confianza promedio: {consensus['avg_confidence']:.1%}")
        
        # Mostrar aprobaciones
        claude_approval = "[OK]" if consensus['claude_approval'] else "[ERROR]"
        chatgpt_approval = "[OK]" if consensus['chatgpt_approval'] else "[ERROR]"
        print(f"   Claude Code: {claude_approval}")
        print(f"   ChatGPT: {chatgpt_approval}")
        
        # Mostrar factores de riesgo si existen
        if consensus['risk_factors']:
            print(f"   [ADVERTENCIA]  Factores de riesgo: {', '.join(consensus['risk_factors'])}")
        
        # Mostrar sugerencias
        if consensus['suggested_modifications']:
            print(f"   [TIP] Sugerencias:")
            for suggestion in consensus['suggested_modifications'][:3]:
                print(f"       {suggestion}")
        
    except Exception as e:
        print(f"[ERROR] Error en revisin: {e}")
        sys.exit(1)

def cmd_list_tasks(args):
    """Listar tareas colaborativas"""
    try:
        system = CollaborativeAISystem()
        tasks_data = system._load_json(system.tasks_db)
        tasks = tasks_data.get("tasks", [])
        
        if not tasks:
            print("[LISTA] No hay tareas colaborativas registradas")
            return
        
        # Filtrar por estado si se especific
        if args.status:
            tasks = [t for t in tasks if t["status"] == args.status]
        
        # Ordenar por fecha
        tasks.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        print(f"[LISTA] Tareas colaborativas ({len(tasks)} total):\n")
        
        for i, task in enumerate(tasks[:args.limit], 1):
            status_emoji = {
                "proposed": "[RAZONAMIENTO]",
                "under_review": "[ANALIZANDO]", 
                "approved": "[OK]",
                "in_progress": "[IMPLEMENTADO]",
                "completed": "[COMPLETADO]",
                "rejected": "[ERROR]",
                "conflict": "[ADVERTENCIA]"
            }.get(task["status"], "")
            
            priority_emoji = {
                "low": "[SISTEMA]",
                "medium": "[MEDIO]", 
                "high": "[ALTO]",
                "critical": "[CRITICO]"
            }.get(task["priority"], "[DESCONOCIDO]")
            
            print(f"{i:2d}. {status_emoji} [{task['id'][-8:]}] {task['title'][:50]}")
            print(f"     {priority_emoji} {task['priority']} | Por: {task['proposed_by']} | Estado: {task['status']}")
            
            if task.get("files_affected"):
                file_count = len(task["files_affected"])
                print(f"     [DIRECTORIO] {file_count} archivo(s) afectado(s)")
            print()
        
    except Exception as e:
        print(f"[ERROR] Error listando tareas: {e}")
        sys.exit(1)

async def cmd_dev_cycle(args):
    """Ejecutar ciclo completo de desarrollo"""
    try:
        print("[EJECUTANDO] Iniciando ciclo de desarrollo colaborativo inteligente...")
        print("   [ESTADISTICAS] Analizando estado del repositorio...")
        
        # Configuracin del ciclo
        ai_devops = EnhancedAIDevOps(
            dry_run=args.dry_run,
            auto_push=args.auto_push
        )
        
        # Ejecutar ciclo
        cycle_summary = await ai_devops.intelligent_development_cycle(
            base_branch=args.branch,
            focus_areas=args.focus if args.focus else None,
            min_confidence=args.min_confidence
        )
        
        # Mostrar resultados
        print(f"\n[OK] Ciclo completado:")
        print(f"   [TAREA] Tareas propuestas: {cycle_summary['proposed_tasks']}")
        print(f"   [OK] Tareas aprobadas: {cycle_summary['approved_tasks']}")
        print(f"   [IMPLEMENTADO]  Tareas implementadas: {cycle_summary['implemented_tasks']}")
        print(f"   [TEST] Modo: {'Simulacin' if cycle_summary['dry_run'] else 'Implementacin real'}")
        
        # Detalles de tareas si las hay
        if cycle_summary.get("tasks_details"):
            print(f"\n[LISTA] Detalles de tareas procesadas:")
            for task in cycle_summary["tasks_details"]:
                consensus_emoji = {
                    "STRONG_CONSENSUS": "[PRIORIDAD]",
                    "WEAK_CONSENSUS": "", 
                    "STRONG_REJECTION": "[ERROR]",
                    "CONFLICT": "[ADVERTENCIA]"
                }.get(task["consensus"], "")
                
                print(f"   {consensus_emoji} {task['title'][:40]}")
                print(f"       Consenso: {task['consensus']}")
        
        # Generar reporte si se solicita
        if args.report:
            report = ai_devops.generate_cycle_report(cycle_summary)
            report_file = f"ai_cycle_report_{cycle_summary.get('cycle_timestamp', 'unknown')}.md"
            Path(report_file).write_text(report, encoding='utf-8')
            print(f"\n[ARCHIVO] Reporte guardado en: {report_file}")
        
    except Exception as e:
        print(f"[ERROR] Error en ciclo de desarrollo: {e}")
        sys.exit(1)

def cmd_stats(args):
    """Mostrar estadsticas del sistema"""
    try:
        system = CollaborativeAISystem()
        stats = system.get_collaboration_stats()
        
        print("[ESTADISTICAS] Estadsticas del Sistema Colaborativo AI:")
        print(f"   [LISTA] Total de tareas: {stats['total_tasks']}")
        print(f"   [ACTIVO] Actividad reciente: {stats['recent_activity']} tareas")
        print(f"   [SISTEMA] Estado del sistema: {stats['system_health']}")
        
        # Estadsticas de consenso
        if stats.get('consensus_stats'):
            print(f"\n[METRICAS] Estadsticas de consenso:")
            for consensus_type, count in stats['consensus_stats'].items():
                emoji = {
                    "STRONG_CONSENSUS": "[PRIORIDAD]",
                    "WEAK_CONSENSUS": "",
                    "STRONG_REJECTION": "[ERROR]", 
                    "CONFLICT": "[ADVERTENCIA]"
                }.get(consensus_type, "[ESTADISTICAS]")
                print(f"   {emoji} {consensus_type}: {count}")
        
    except Exception as e:
        print(f"[ERROR] Error obteniendo estadsticas: {e}")
        sys.exit(1)

def cmd_demo(args):
    """Ejecutar demostracin del sistema"""
    print("[DEMO] Demostracin del Equipo de Desarrollo AI Senior\n")
    
    print("Escenario: Claude Code detecta oportunidad de optimizacin")
    print("1. [CLAUDE] Claude Code propone mejora de performance...")
    
    # Crear tarea de demo
    task = create_collaborative_task(
        title="Optimizar queries de base de datos",
        description="Implementar lazy loading y cache en consultas pesadas del sistema de reportes",
        priority="high",
        proposed_by="claude",
        files_affected=["managers/report_manager.py", "database/manager.py"]
    )
    
    print(f"   [OK] Tarea propuesta: {task.id}")
    
    print("\n2.  Revisin colaborativa simulada...")
    print("   [CLAUDE] Claude Code: 'Implementacin factible, riesgo bajo'")
    print("   [CHATGPT] ChatGPT: 'Arquitectura coherente, considerar tests adicionales'")
    print("   [CONSENSO] Sistema: 'CONSENSO FUERTE - PROCEDER'")
    
    print("\n3. [OK] Resultado:")
    print("   [PRIORIDAD] Ambas IAs aprueban (confianza: 89%)")
    print("   [IMPLEMENTADO]  Claude implementa cambios localmente")
    print("   [TEST] Tests automatizados ejecutados")
    print("    Commit y push automtico")
    
    print("\n4. [COMPLETADO] Beneficios del equipo AI:")
    print("    Revisin cruzada automtica")
    print("    Consenso antes de implementar") 
    print("    Calidad y coherencia arquitectural")
    print("    Velocidad de desarrollo senior")

def main():
    """Punto de entrada principal"""
    parser = argparse.ArgumentParser(
        description="AI Development Team - Claude Code + ChatGPT",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Argumento global para mostrar banner
    parser.add_argument('--no-banner', action='store_true', 
                       help='No mostrar banner de inicio')
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # create-task
    create_parser = subparsers.add_parser('create-task', help='Crear nueva tarea colaborativa')
    create_parser.add_argument('--title', required=True, help='Ttulo de la tarea')
    create_parser.add_argument('--description', help='Descripcin detallada')
    create_parser.add_argument('--priority', choices=['low', 'medium', 'high', 'critical'],
                              default='medium', help='Prioridad de la tarea')
    create_parser.add_argument('--proposed-by', choices=['claude', 'chatgpt'],
                              default='claude', help='IA que propone la tarea')
    create_parser.add_argument('--files', help='Archivos afectados (separados por coma)')
    
    # review-task
    review_parser = subparsers.add_parser('review-task', help='Ejecutar revisin colaborativa')
    review_parser.add_argument('task_id', help='ID de la tarea a revisar')
    
    # list-tasks
    list_parser = subparsers.add_parser('list-tasks', help='Listar tareas colaborativas')
    list_parser.add_argument('--status', help='Filtrar por estado')
    list_parser.add_argument('--limit', type=int, default=10, help='Lmite de tareas a mostrar')
    
    # dev-cycle
    cycle_parser = subparsers.add_parser('dev-cycle', help='Ejecutar ciclo completo de desarrollo')
    cycle_parser.add_argument('--branch', help='Rama base para cambios')
    cycle_parser.add_argument('--dry-run', action='store_true', 
                             help='Modo simulacin (no aplica cambios)')
    cycle_parser.add_argument('--auto-push', action='store_true',
                             help='Push automtico despus del commit')
    cycle_parser.add_argument('--min-confidence', type=float, default=0.7,
                             help='Confianza mnima para proceder (0.0-1.0)')
    cycle_parser.add_argument('--focus', nargs='*',
                             help='reas de enfoque especficas')
    cycle_parser.add_argument('--report', action='store_true',
                             help='Generar reporte detallado')
    
    # stats
    stats_parser = subparsers.add_parser('stats', help='Mostrar estadsticas del sistema')
    
    # demo
    demo_parser = subparsers.add_parser('demo', help='Ejecutar demostracin del sistema')
    
    args = parser.parse_args()
    
    # Mostrar banner si no se deshabilit
    if not args.no_banner:
        print_banner()
    
    # Si no se especific comando, mostrar ayuda
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Ejecutar comando correspondiente
    try:
        if args.command == 'create-task':
            cmd_create_task(args)
        elif args.command == 'review-task':
            asyncio.run(cmd_review_task(args))
        elif args.command == 'list-tasks':
            cmd_list_tasks(args)
        elif args.command == 'dev-cycle':
            asyncio.run(cmd_dev_cycle(args))
        elif args.command == 'stats':
            cmd_stats(args)
        elif args.command == 'demo':
            cmd_demo(args)
            
    except KeyboardInterrupt:
        print("\n[CANCELADO] Operacin cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] Error inesperado: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()