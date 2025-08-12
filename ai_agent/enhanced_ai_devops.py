#!/usr/bin/env python3
"""
Sistema AI DevOps Mejorado con Colaboración Inteligente
Integra el sistema colaborativo en el flujo de DevOps existente
"""

import asyncio
import argparse
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from .ai_devops import (
    collect_repo_summary, run_checks, create_branch, 
    apply_ai_files, save_ai_response, git_repo, logger
)
from .collaborative_ai_system import (
    CollaborativeAISystem, create_collaborative_task,
    run_collaborative_review, TaskPriority, AIAgent, TaskStatus
)
from .config import (
    ROOT, AUTO_PUSH_DEFAULT, DRY_RUN_DEFAULT, AI_SYNC_DIR,
    GIT_REMOTE, GIT_AUTHOR_NAME, GIT_AUTHOR_EMAIL
)
from .ai_helpers import call_openai_chat, call_claude, extract_json_from_text

class EnhancedAIDevOps:
    """Sistema DevOps mejorado con colaboración inteligente entre AIs"""
    
    def __init__(self, dry_run: bool = True, auto_push: bool = False):
        self.dry_run = dry_run
        self.auto_push = auto_push
        self.collab_system = CollaborativeAISystem()
        
    async def intelligent_development_cycle(
        self, 
        base_branch: str = None,
        focus_areas: List[str] = None,
        min_confidence: float = 0.7
    ) -> Dict:
        """Ejecuta un ciclo completo de desarrollo inteligente"""
        
        logger.info("Iniciando ciclo de desarrollo colaborativo inteligente")
        
        # 1. Análisis inicial del repositorio
        repo_analysis = await self._analyze_repository(focus_areas)
        
        # 2. Claude propone mejoras basadas en el análisis
        claude_proposals = await self._get_claude_proposals(repo_analysis)
        
        # 3. Crear tareas colaborativas para cada propuesta
        tasks = []
        for proposal in claude_proposals:
            task = create_collaborative_task(
                title=proposal["title"],
                description=proposal["description"],
                priority=proposal.get("priority", "medium"),
                proposed_by="claude",
                files_affected=proposal.get("files_affected", [])
            )
            tasks.append(task)
        
        # 4. Ejecutar revisión colaborativa para cada tarea
        approved_tasks = []
        for task in tasks:
            logger.info(f"Revisando tarea: {task.title}")
            review_result = await run_collaborative_review(task.id)
            
            if self._should_proceed(review_result, min_confidence):
                approved_tasks.append((task, review_result))
                logger.info(f"Tarea aprobada: {task.title}")
            else:
                logger.info(f"Tarea rechazada o requiere mediación: {task.title}")
        
        # 5. Implementar tareas aprobadas
        implementation_results = []
        if approved_tasks and not self.dry_run:
            branch_name = create_branch(base_branch)
            
            for task, review_result in approved_tasks:
                impl_result = await self._implement_task(task, review_result)
                implementation_results.append(impl_result)
            
            # 6. Post-implementación: tests y validación
            post_checks = run_checks()
            
            if post_checks["pytest_rc"] == 0:  # Tests pasaron
                if self.auto_push:
                    repo = git_repo()
                    repo.git.push("--set-upstream", GIT_REMOTE, branch_name)
                    logger.info(f"Rama {branch_name} pusheada exitosamente")
            else:
                logger.warning("Tests fallaron, revisión manual requerida")
        
        # 7. Resumen del ciclo
        cycle_summary = {
            "repository_analysis": repo_analysis,
            "proposed_tasks": len(tasks),
            "approved_tasks": len(approved_tasks),
            "implemented_tasks": len(implementation_results),
            "tasks_details": [
                {
                    "task_id": task.id,
                    "title": task.title,
                    "consensus": review_result["consensus"]["consensus_type"],
                    "implemented": not self.dry_run
                }
                for task, review_result in approved_tasks
            ],
            "dry_run": self.dry_run,
            "cycle_timestamp": task.created_at if tasks else None
        }
        
        return cycle_summary
    
    async def _analyze_repository(self, focus_areas: List[str] = None) -> Dict:
        """Analiza el estado actual del repositorio"""
        repo_summary = collect_repo_summary()
        checks_result = run_checks()
        
        # Prompt para análisis profundo
        analysis_prompt = f"""
Eres un ANALISTA DE REPOSITORIO senior. Analiza el estado actual del proyecto:

Resumen del repositorio:
{json.dumps(repo_summary, indent=2)}

Resultados de checks:
{json.dumps(checks_result, indent=2)}

Áreas de enfoque {f'(priorizar: {focus_areas})' if focus_areas else '(todas)'}:
- Arquitectura y diseño
- Performance y optimización
- Mantenibilidad y limpieza de código
- Tests y cobertura
- Documentación
- Seguridad

Responde con JSON:
{{
    "health_score": 0-100,
    "critical_issues": ["issue1", "issue2"],
    "improvement_opportunities": [
        {{
            "area": "nombre_area",
            "priority": "low/medium/high/critical",
            "description": "descripción",
            "estimated_impact": "descripción del impacto"
        }}
    ],
    "technical_debt_score": 0-100,
    "recommendations": ["rec1", "rec2"]
}}
"""
        
        try:
            analysis_response = call_claude(analysis_prompt)
            analysis_data = extract_json_from_text(analysis_response)
            
            return {
                "raw_repo_summary": repo_summary,
                "checks_result": checks_result,
                "ai_analysis": analysis_data or {},
                "focus_areas": focus_areas,
                "analysis_timestamp": repo_summary.get("timestamp")
            }
        except Exception as e:
            logger.error(f"Error en análisis de repositorio: {e}")
            return {
                "raw_repo_summary": repo_summary,
                "checks_result": checks_result,
                "ai_analysis": {"error": str(e)},
                "focus_areas": focus_areas
            }
    
    async def _get_claude_proposals(self, repo_analysis: Dict) -> List[Dict]:
        """Obtiene propuestas de mejora de Claude Code"""
        
        prompt = f"""
Eres CLAUDE CODE, desarrollador senior implementador. Basado en este análisis:

{json.dumps(repo_analysis, indent=2)}

Propone mejoras concretas e implementables. Prioriza:
1. Impacto alto con esfuerzo medio-bajo
2. Mejoras que reduzcan deuda técnica
3. Optimizaciones de performance
4. Mejoras en mantenibilidad

Responde con JSON array:
[
    {{
        "title": "Título corto de la mejora",
        "description": "Descripción detallada de qué hacer",
        "priority": "low/medium/high/critical",
        "estimated_effort": "low/medium/high",
        "impact_description": "Qué beneficios aportará",
        "files_affected": ["archivo1.py", "archivo2.py"],
        "implementation_approach": "Cómo implementaría",
        "risk_factors": ["riesgo1", "riesgo2"]
    }}
]

Máximo 5 propuestas, ordenadas por prioridad descendente.
"""
        
        try:
            response = call_claude(prompt)
            proposals = extract_json_from_text(response)
            
            if isinstance(proposals, list):
                return proposals[:5]  # Limitar a 5 propuestas
            else:
                logger.warning("Claude no retornó lista de propuestas válida")
                return []
                
        except Exception as e:
            logger.error(f"Error obteniendo propuestas de Claude: {e}")
            return []
    
    def _should_proceed(self, review_result: Dict, min_confidence: float) -> bool:
        """Determina si se debe proceder con una tarea basado en el consenso"""
        consensus = review_result["consensus"]
        
        # Criterios para proceder
        if consensus["recommendation"] == "PROCEED":
            return True
        elif consensus["recommendation"] == "PROCEED_WITH_CAUTION":
            return consensus["avg_confidence"] >= min_confidence
        else:
            return False
    
    async def _implement_task(self, task, review_result: Dict) -> Dict:
        """Implementa una tarea específica"""
        
        # Preparar contexto de implementación
        implementation_context = {
            "task": {
                "title": task.title,
                "description": task.description,
                "files_affected": task.files_affected
            },
            "consensus_result": review_result["consensus"],
            "claude_opinion": review_result["claude_opinion"],
            "chatgpt_opinion": review_result["chatgpt_opinion"]
        }
        
        # Prompt para implementación
        impl_prompt = f"""
Eres CLAUDE CODE implementador. Implementa esta tarea aprobada por consenso:

{json.dumps(implementation_context, indent=2)}

Considera:
1. Las sugerencias de ambas IAs
2. Los factores de riesgo identificados
3. Mantener coherencia con la arquitectura existente
4. Implementar tests si es necesario

Responde con JSON:
{{
    "files": {{
        "ruta/archivo.py": "contenido completo del archivo",
        "tests/test_archivo.py": "tests correspondientes"
    }},
    "commit_message": "Mensaje de commit descriptivo",
    "implementation_notes": "Notas sobre la implementación",
    "post_implementation_tasks": ["tarea1", "tarea2"]
}}

Si no puedes implementar algo, devuelve archivos vacíos y explica en implementation_notes.
"""
        
        try:
            response = call_claude(impl_prompt)
            implementation_data = extract_json_from_text(response)
            
            if implementation_data and implementation_data.get("files"):
                # Aplicar cambios
                files_map = implementation_data["files"]
                commit_message = implementation_data.get(
                    "commit_message", 
                    f"AI: Implementa {task.title}"
                )
                
                apply_ai_files(files_map, commit_message, "Claude (collaborative)")
                
                return {
                    "task_id": task.id,
                    "status": "implemented",
                    "files_changed": list(files_map.keys()),
                    "implementation_notes": implementation_data.get("implementation_notes", ""),
                    "post_tasks": implementation_data.get("post_implementation_tasks", [])
                }
            else:
                return {
                    "task_id": task.id,
                    "status": "skipped",
                    "reason": "No implementation data returned"
                }
                
        except Exception as e:
            logger.error(f"Error implementando tarea {task.id}: {e}")
            return {
                "task_id": task.id,
                "status": "error",
                "error": str(e)
            }
    
    def generate_cycle_report(self, cycle_summary: Dict) -> str:
        """Genera un reporte del ciclo de desarrollo"""
        
        report = f"""
# Reporte de Ciclo de Desarrollo AI Colaborativo

## Resumen General
- **Tareas Propuestas**: {cycle_summary['proposed_tasks']}
- **Tareas Aprobadas**: {cycle_summary['approved_tasks']}
- **Tareas Implementadas**: {cycle_summary['implemented_tasks']}
- **Modo**: {'Dry Run' if cycle_summary['dry_run'] else 'Implementación Real'}

## Análisis del Repositorio
"""
        
        ai_analysis = cycle_summary["repository_analysis"].get("ai_analysis", {})
        if ai_analysis and "health_score" in ai_analysis:
            report += f"""
- **Health Score**: {ai_analysis['health_score']}/100
- **Technical Debt Score**: {ai_analysis.get('technical_debt_score', 'N/A')}/100
- **Issues Críticos**: {len(ai_analysis.get('critical_issues', []))}
"""
        
        # Detalles de tareas
        if cycle_summary["tasks_details"]:
            report += "\n## Tareas Procesadas\n"
            for i, task in enumerate(cycle_summary["tasks_details"], 1):
                report += f"""
### {i}. {task['title']}
- **ID**: {task['task_id']}
- **Consenso**: {task['consensus']}
- **Estado**: {'Implementada' if task['implemented'] else 'Simulada'}
"""
        
        # Recomendaciones
        recommendations = ai_analysis.get('recommendations', [])
        if recommendations:
            report += "\n## Recomendaciones para Próximos Ciclos\n"
            for rec in recommendations:
                report += f"- {rec}\n"
        
        report += f"""

---
*Generado por Enhanced AI DevOps - {cycle_summary.get('cycle_timestamp', 'timestamp N/A')}*
"""
        
        return report

# === Funciones de CLI ===

async def main():
    """Punto de entrada principal mejorado"""
    parser = argparse.ArgumentParser(
        description="Enhanced AI DevOps - Sistema colaborativo Claude + ChatGPT"
    )
    
    parser.add_argument("--branch", help="Rama base para los cambios")
    parser.add_argument("--dry-run", action="store_true", 
                       help="Modo simulación (no aplica cambios)")
    parser.add_argument("--auto-push", action="store_true",
                       help="Push automático después del commit")
    parser.add_argument("--min-confidence", type=float, default=0.7,
                       help="Confianza mínima para proceder (0.0-1.0)")
    parser.add_argument("--focus", nargs="*", 
                       help="Áreas de enfoque específicas")
    parser.add_argument("--report-file", 
                       help="Archivo donde guardar el reporte")
    
    args = parser.parse_args()
    
    # Configuración
    dry_run = args.dry_run or DRY_RUN_DEFAULT
    auto_push = args.auto_push or AUTO_PUSH_DEFAULT
    
    # Inicializar sistema
    ai_devops = EnhancedAIDevOps(dry_run=dry_run, auto_push=auto_push)
    
    try:
        # Ejecutar ciclo inteligente
        logger.info("Iniciando Enhanced AI DevOps...")
        cycle_summary = await ai_devops.intelligent_development_cycle(
            base_branch=args.branch,
            focus_areas=args.focus,
            min_confidence=args.min_confidence
        )
        
        # Generar reporte
        report = ai_devops.generate_cycle_report(cycle_summary)
        
        # Guardar reporte
        if args.report_file:
            Path(args.report_file).write_text(report, encoding="utf-8")
            logger.info(f"Reporte guardado en: {args.report_file}")
        else:
            print("\n" + "="*60)
            print(report)
            print("="*60)
        
        # Guardar resumen JSON
        summary_file = AI_SYNC_DIR / f"cycle_summary_{cycle_summary.get('cycle_timestamp', 'unknown')}.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(cycle_summary, f, indent=2, ensure_ascii=False)
        
        logger.info("Ciclo de desarrollo colaborativo completado exitosamente")
        
    except Exception as e:
        logger.error(f"Error en ciclo de desarrollo: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
