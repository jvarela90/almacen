#!/usr/bin/env python3
"""
CLI para el Sistema de Coordinación AI Colaborativo
Permite ejecutar comandos de coordinación entre Claude Code y ChatGPT
"""

import asyncio
import argparse
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich import print as rprint

from .collaborative_ai_system import (
    CollaborativeAISystem, 
    create_collaborative_task,
    run_collaborative_review,
    TaskPriority,
    AIAgent
)

console = Console()

def display_task_table(tasks: list):
    """Muestra las tareas en formato tabla"""
    table = Table(title="Tareas Colaborativas")
    
    table.add_column("ID", style="cyan")
    table.add_column("Título", style="magenta")
    table.add_column("Estado", style="green")
    table.add_column("Prioridad", style="yellow")
    table.add_column("Propuesto por", style="blue")
    table.add_column("Archivos", style="red")
    
    for task in tasks:
        files_count = len(task.get("files_affected", []))
        table.add_row(
            task["id"][-8:],  # Últimos 8 caracteres del ID
            task["title"][:50],  # Truncar título
            task["status"],
            task["priority"],
            task["proposed_by"],
            str(files_count)
        )
    
    console.print(table)

def display_consensus_result(result: dict):
    """Muestra el resultado del consenso"""
    consensus = result["consensus"]
    
    # Panel principal
    title = f"Consenso para Tarea: {result['task']['title']}"
    
    content = f"""
[bold]Tipo de Consenso:[/bold] {consensus['consensus_type']}
[bold]Recomendación:[/bold] {consensus['recommendation']}

[bold]Aprobaciones:[/bold]
  • Claude: {'✅' if consensus['claude_approval'] else '❌'}
  • ChatGPT: {'✅' if consensus['chatgpt_approval'] else '❌'}

[bold]Confianza Promedio:[/bold] {consensus['avg_confidence']:.2%}

[bold]Factores de Riesgo:[/bold]
{chr(10).join(['  • ' + risk for risk in consensus['risk_factors']])}

[bold]Sugerencias Combinadas:[/bold]
{chr(10).join(['  • ' + sug for sug in consensus['suggested_modifications']])}
"""
    
    panel_style = "green" if consensus['recommendation'] == "PROCEED" else "yellow" if "CAUTION" in consensus['recommendation'] else "red"
    
    console.print(Panel(content, title=title, style=panel_style))
    
    # Detalles de opiniones
    claude_opinion = result["claude_opinion"]
    chatgpt_opinion = result["chatgpt_opinion"]
    
    console.print("\n[bold]Opinión de Claude Code:[/bold]")
    console.print(f"  Aprobación: {'✅' if claude_opinion['approval'] else '❌'}")
    console.print(f"  Confianza: {claude_opinion['confidence']:.2%}")
    console.print(f"  Razonamiento: {claude_opinion['reasoning'][:200]}...")
    
    console.print("\n[bold]Opinión de ChatGPT:[/bold]")
    console.print(f"  Aprobación: {'✅' if chatgpt_opinion['approval'] else '❌'}")
    console.print(f"  Confianza: {chatgpt_opinion['confidence']:.2%}")
    console.print(f"  Razonamiento: {chatgpt_opinion['reasoning'][:200]}...")

def cmd_create_task(args):
    """Crear nueva tarea colaborativa"""
    try:
        task = create_collaborative_task(
            title=args.title,
            description=args.description,
            priority=args.priority,
            proposed_by=args.proposed_by,
            files_affected=args.files.split(',') if args.files else None
        )
        
        console.print(f"✅ Tarea creada: {task.id}")
        console.print(f"   Título: {task.title}")
        console.print(f"   Prioridad: {task.priority.value}")
        
    except Exception as e:
        console.print(f"❌ Error creando tarea: {e}")
        sys.exit(1)

def cmd_list_tasks(args):
    """Listar tareas colaborativas"""
    try:
        system = CollaborativeAISystem()
        tasks_data = system._load_json(system.tasks_db)
        tasks = tasks_data.get("tasks", [])
        
        if not tasks:
            console.print("📋 No hay tareas colaborativas")
            return
        
        # Filtrar por estado si se especificó
        if args.status:
            tasks = [t for t in tasks if t["status"] == args.status]
        
        # Ordenar por fecha de actualización
        tasks.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        
        display_task_table(tasks)
        
        console.print(f"\n📊 Total: {len(tasks)} tareas")
        
    except Exception as e:
        console.print(f"❌ Error listando tareas: {e}")
        sys.exit(1)

async def cmd_review_task(args):
    """Ejecutar revisión colaborativa de una tarea"""
    try:
        with console.status("[bold green]Ejecutando revisión colaborativa..."):
            result = await run_collaborative_review(args.task_id)
        
        console.print("\n🤝 Revisión colaborativa completada\n")
        display_consensus_result(result)
        
    except Exception as e:
        console.print(f"❌ Error en revisión: {e}")
        sys.exit(1)

def cmd_stats(args):
    """Mostrar estadísticas del sistema colaborativo"""
    try:
        system = CollaborativeAISystem()
        stats = system.get_collaboration_stats()
        
        console.print("\n📊 [bold]Estadísticas del Sistema Colaborativo[/bold]\n")
        
        console.print(f"Total de Tareas: {stats['total_tasks']}")
        console.print(f"Actividad Reciente: {stats['recent_activity']} tareas")
        console.print(f"Estado del Sistema: {stats['system_health']}")
        
        if stats['consensus_stats']:
            console.print("\n[bold]Estadísticas de Consenso:[/bold]")
            for consensus_type, count in stats['consensus_stats'].items():
                console.print(f"  {consensus_type}: {count}")
        
    except Exception as e:
        console.print(f"❌ Error obteniendo estadísticas: {e}")
        sys.exit(1)

def cmd_simulate_senior_team(args):
    """Simula el flujo completo de un equipo de desarrollo senior"""
    console.print("🚀 [bold]Simulando Equipo de Desarrollo Senior AI[/bold]\n")
    
    # Crear tarea de ejemplo
    console.print("1. Claude Code propone mejora...")
    task = create_collaborative_task(
        title="Optimizar sistema de reportes",
        description="Mejorar performance de generación de reportes y añadir caché inteligente",
        priority="high",
        proposed_by="claude",
        files_affected=["managers/report_manager.py", "utils/exporters.py"]
    )
    
    console.print(f"   ✅ Tarea creada: {task.id}")
    
    # Ejecutar revisión (simulada en modo demo)
    console.print("\n2. Iniciando revisión colaborativa...")
    console.print("   🤖 Claude Code analiza factibilidad técnica...")
    console.print("   🧠 ChatGPT revisa arquitectura y mejores prácticas...")
    console.print("   ⚡ Sistema de coordinación evalúa consenso...")
    
    console.print("\n3. [bold green]Resultado: CONSENSO FUERTE - PROCEDER[/bold]")
    console.print("   ✅ Ambas IAs aprueban la implementación")
    console.print("   📈 Confianza promedio: 87%")
    console.print("   ⚠️  Riesgo: BAJO - Cambios bien aislados")
    
    console.print("\n4. [bold]Próximos pasos sugeridos:[/bold]")
    console.print("   • Claude Code implementa los cambios")
    console.print("   • ChatGPT revisa el código final")
    console.print("   • Sistema ejecuta tests y validaciones")
    console.print("   • Commit automático con mensaje consensuado")

def main():
    """Punto de entrada principal del CLI"""
    parser = argparse.ArgumentParser(
        description="Sistema de Coordinación AI: Claude Code + ChatGPT",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponibles')
    
    # Comando: crear tarea
    create_parser = subparsers.add_parser('create', help='Crear nueva tarea colaborativa')
    create_parser.add_argument('--title', required=True, help='Título de la tarea')
    create_parser.add_argument('--description', required=True, help='Descripción detallada')
    create_parser.add_argument('--priority', choices=['low', 'medium', 'high', 'critical'], 
                              default='medium', help='Prioridad de la tarea')
    create_parser.add_argument('--proposed-by', choices=['claude', 'chatgpt'], 
                              default='claude', help='IA que propone la tarea')
    create_parser.add_argument('--files', help='Archivos afectados (separados por coma)')
    
    # Comando: listar tareas
    list_parser = subparsers.add_parser('list', help='Listar tareas colaborativas')
    list_parser.add_argument('--status', help='Filtrar por estado específico')
    
    # Comando: revisar tarea
    review_parser = subparsers.add_parser('review', help='Ejecutar revisión colaborativa')
    review_parser.add_argument('task_id', help='ID de la tarea a revisar')
    
    # Comando: estadísticas
    stats_parser = subparsers.add_parser('stats', help='Mostrar estadísticas del sistema')
    
    # Comando: simulación
    demo_parser = subparsers.add_parser('demo', help='Simular flujo de equipo senior')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Ejecutar comando correspondiente
    try:
        if args.command == 'create':
            cmd_create_task(args)
        elif args.command == 'list':
            cmd_list_tasks(args)
        elif args.command == 'review':
            asyncio.run(cmd_review_task(args))
        elif args.command == 'stats':
            cmd_stats(args)
        elif args.command == 'demo':
            cmd_simulate_senior_team(args)
    except KeyboardInterrupt:
        console.print("\n❌ Operación cancelada por el usuario")
        sys.exit(1)

if __name__ == "__main__":
    main()
