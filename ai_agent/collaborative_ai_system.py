#!/usr/bin/env python3
"""
Sistema de Colaboración AI: Claude Code + ChatGPT
Implementa un equipo de desarrollo senior con roles especializados
"""

import asyncio
import json
import logging
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .ai_helpers import call_openai_chat, call_claude, extract_json_from_text
from .config import ROOT, AI_SYNC_DIR

# === Logging ===
logger = logging.getLogger("collaborative_ai")

class TaskPriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class TaskStatus(Enum):
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"
    CONFLICT = "conflict"

class AIAgent(Enum):
    CLAUDE = "claude_code"
    CHATGPT = "chatgpt"
    SYSTEM = "coordination_system"

@dataclass
class CollaborationTask:
    """Representa una tarea en el sistema colaborativo"""
    id: str
    title: str
    description: str
    priority: TaskPriority
    status: TaskStatus
    proposed_by: AIAgent
    assigned_to: Optional[AIAgent]
    created_at: str
    updated_at: str
    claude_opinion: Optional[Dict] = None
    chatgpt_opinion: Optional[Dict] = None
    consensus_reached: bool = False
    conflict_details: Optional[str] = None
    implementation_notes: Optional[str] = None
    review_notes: Optional[str] = None
    files_affected: List[str] = None
    
    def __post_init__(self):
        if self.files_affected is None:
            self.files_affected = []

@dataclass
class AIOpinion:
    """Opinión de una IA sobre una tarea específica"""
    agent: AIAgent
    task_id: str
    approval: bool
    confidence: float  # 0.0 - 1.0
    reasoning: str
    suggested_changes: List[str]
    estimated_effort: str  # "low", "medium", "high"
    risk_assessment: str
    timestamp: str

class CollaborativeAISystem:
    """Sistema de coordinación entre Claude Code y ChatGPT"""
    
    def __init__(self):
        self.tasks_db = AI_SYNC_DIR / "collaboration_tasks.json"
        self.consensus_log = AI_SYNC_DIR / "consensus_log.json"
        self.conflict_resolution_log = AI_SYNC_DIR / "conflicts.json"
        
        # Ensure directories exist
        AI_SYNC_DIR.mkdir(exist_ok=True)
        
        # Initialize databases if they don't exist
        self._init_databases()
        
    def _init_databases(self):
        """Inicializa las bases de datos JSON si no existen"""
        if not self.tasks_db.exists():
            self._save_json(self.tasks_db, {"tasks": [], "metadata": {"version": "1.0"}})
        
        if not self.consensus_log.exists():
            self._save_json(self.consensus_log, {"consensus_history": [], "stats": {}})
            
        if not self.conflict_resolution_log.exists():
            self._save_json(self.conflict_resolution_log, {"conflicts": [], "resolutions": []})
    
    def _load_json(self, path: Path) -> Dict:
        """Carga archivo JSON de forma segura"""
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            logger.error(f"Error loading {path}: {e}")
            return {}
    
    def _save_json(self, path: Path, data: Dict):
        """Guarda archivo JSON de forma segura"""
        try:
            # Serializar enums y otros objetos especiales
            def json_serializer(obj):
                if hasattr(obj, 'value'):  # Para Enums
                    return obj.value
                elif hasattr(obj, '__dict__'):  # Para objetos con atributos
                    return obj.__dict__
                else:
                    return str(obj)
            
            path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False, default=json_serializer), 
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Error saving {path}: {e}")
    
    def create_task(
        self, 
        title: str, 
        description: str, 
        priority: TaskPriority,
        proposed_by: AIAgent,
        files_affected: List[str] = None
    ) -> CollaborationTask:
        """Crea una nueva tarea colaborativa"""
        task_id = f"task_{datetime.datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        task = CollaborationTask(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            status=TaskStatus.PROPOSED,
            proposed_by=proposed_by,
            assigned_to=None,
            created_at=datetime.datetime.utcnow().isoformat(),
            updated_at=datetime.datetime.utcnow().isoformat(),
            files_affected=files_affected or []
        )
        
        # Guardar tarea
        tasks_data = self._load_json(self.tasks_db)
        tasks_data["tasks"].append(asdict(task))
        self._save_json(self.tasks_db, tasks_data)
        
        logger.info(f"Nueva tarea creada: {task_id} - {title}")
        return task
    
    async def request_opinions(self, task: CollaborationTask) -> Tuple[AIOpinion, AIOpinion]:
        """Solicita opiniones de ambas IAs sobre una tarea"""
        
        # Preparar contexto para las IAs
        task_context = {
            "task": asdict(task),
            "project_info": self._get_project_context(),
            "recent_tasks": self._get_recent_tasks(limit=5)
        }
        
        # Solicitar opinión a Claude (en paralelo)
        claude_task = asyncio.create_task(
            self._get_claude_opinion(task, task_context)
        )
        
        # Solicitar opinión a ChatGPT (en paralelo)
        chatgpt_task = asyncio.create_task(
            self._get_chatgpt_opinion(task, task_context)
        )
        
        # Esperar ambas respuestas
        claude_opinion, chatgpt_opinion = await asyncio.gather(claude_task, chatgpt_task)
        
        return claude_opinion, chatgpt_opinion
    
    async def _get_claude_opinion(self, task: CollaborationTask, context: Dict) -> AIOpinion:
        """Obtiene opinión de Claude Code sobre la tarea"""
        prompt = f"""
Eres CLAUDE CODE, un desarrollador senior especializado en implementación local.

Tarea a evaluar:
{json.dumps(asdict(task), indent=2)}

Contexto del proyecto:
{json.dumps(context, indent=2)}

Como desarrollador implementador, evalúa:
1. Factibilidad técnica de la implementación
2. Impacto en el código existente
3. Riesgos de la implementación
4. Esfuerzo estimado
5. Tu nivel de confianza en el éxito

Responde en JSON con:
{{
    "approval": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "tu análisis detallado",
    "suggested_changes": ["cambio1", "cambio2"],
    "estimated_effort": "low/medium/high",
    "risk_assessment": "análisis de riesgos"
}}
"""
        
        try:
            response = call_claude(prompt)
            opinion_data = extract_json_from_text(response)
            
            return AIOpinion(
                agent=AIAgent.CLAUDE,
                task_id=task.id,
                approval=opinion_data.get("approval", False),
                confidence=opinion_data.get("confidence", 0.0),
                reasoning=opinion_data.get("reasoning", ""),
                suggested_changes=opinion_data.get("suggested_changes", []),
                estimated_effort=opinion_data.get("estimated_effort", "medium"),
                risk_assessment=opinion_data.get("risk_assessment", ""),
                timestamp=datetime.datetime.utcnow().isoformat()
            )
        except Exception as e:
            logger.error(f"Error getting Claude opinion: {e}")
            return self._create_error_opinion(AIAgent.CLAUDE, task.id, str(e))
    
    async def _get_chatgpt_opinion(self, task: CollaborationTask, context: Dict) -> AIOpinion:
        """Obtiene opinión de ChatGPT sobre la tarea"""
        prompt = f"""
Tarea a evaluar:
{json.dumps(asdict(task), indent=2)}

Contexto del proyecto:
{json.dumps(context, indent=2)}

Como arquitecto senior revisor, evalúa:
1. Alineación con la arquitectura del proyecto
2. Calidad y mejores prácticas
3. Impacto en mantenibilidad
4. Consideraciones de escalabilidad
5. Tu nivel de confianza en la propuesta

Responde en JSON con:
{{
    "approval": true/false,
    "confidence": 0.0-1.0,
    "reasoning": "tu análisis detallado",
    "suggested_changes": ["cambio1", "cambio2"],
    "estimated_effort": "low/medium/high",
    "risk_assessment": "análisis de riesgos"
}}
"""
        
        system_prompt = "Eres CHATGPT, un arquitecto de software senior especializado en revisión de código y diseño de sistemas."
        
        try:
            response = call_openai_chat(prompt, system=system_prompt, temperature=0.2)
            opinion_data = extract_json_from_text(response)
            
            return AIOpinion(
                agent=AIAgent.CHATGPT,
                task_id=task.id,
                approval=opinion_data.get("approval", False),
                confidence=opinion_data.get("confidence", 0.0),
                reasoning=opinion_data.get("reasoning", ""),
                suggested_changes=opinion_data.get("suggested_changes", []),
                estimated_effort=opinion_data.get("estimated_effort", "medium"),
                risk_assessment=opinion_data.get("risk_assessment", ""),
                timestamp=datetime.datetime.utcnow().isoformat()
            )
        except Exception as e:
            logger.error(f"Error getting ChatGPT opinion: {e}")
            return self._create_error_opinion(AIAgent.CHATGPT, task.id, str(e))
    
    def _create_error_opinion(self, agent: AIAgent, task_id: str, error_msg: str) -> AIOpinion:
        """Crea una opinión de error cuando falla la comunicación con una IA"""
        return AIOpinion(
            agent=agent,
            task_id=task_id,
            approval=False,
            confidence=0.0,
            reasoning=f"Error de comunicación: {error_msg}",
            suggested_changes=[],
            estimated_effort="unknown",
            risk_assessment="No se pudo evaluar debido a error de comunicación",
            timestamp=datetime.datetime.utcnow().isoformat()
        )
    
    def evaluate_consensus(
        self, 
        task: CollaborationTask, 
        claude_opinion: AIOpinion, 
        chatgpt_opinion: AIOpinion
    ) -> Dict:
        """Evalúa si hay consenso entre las dos IAs"""
        
        # Criterios para consenso
        both_approve = claude_opinion.approval and chatgpt_opinion.approval
        confidence_threshold = 0.6
        high_confidence = (
            claude_opinion.confidence >= confidence_threshold and 
            chatgpt_opinion.confidence >= confidence_threshold
        )
        
        # Análisis de consenso
        if both_approve and high_confidence:
            consensus_type = "STRONG_CONSENSUS"
            recommendation = "PROCEED"
        elif both_approve:
            consensus_type = "WEAK_CONSENSUS"
            recommendation = "PROCEED_WITH_CAUTION"
        elif not claude_opinion.approval and not chatgpt_opinion.approval:
            consensus_type = "STRONG_REJECTION"
            recommendation = "REJECT"
        else:
            consensus_type = "CONFLICT"
            recommendation = "MEDIATION_REQUIRED"
        
        consensus_result = {
            "consensus_type": consensus_type,
            "recommendation": recommendation,
            "claude_approval": claude_opinion.approval,
            "chatgpt_approval": chatgpt_opinion.approval,
            "avg_confidence": (claude_opinion.confidence + chatgpt_opinion.confidence) / 2,
            "risk_factors": self._analyze_risk_factors(claude_opinion, chatgpt_opinion),
            "suggested_modifications": self._merge_suggestions(claude_opinion, chatgpt_opinion),
            "evaluation_timestamp": datetime.datetime.utcnow().isoformat()
        }
        
        # Registrar en log de consenso
        self._log_consensus(task.id, consensus_result, claude_opinion, chatgpt_opinion)
        
        return consensus_result
    
    def _analyze_risk_factors(self, claude_opinion: AIOpinion, chatgpt_opinion: AIOpinion) -> List[str]:
        """Analiza factores de riesgo basado en las opiniones"""
        risks = []
        
        if claude_opinion.confidence < 0.5 or chatgpt_opinion.confidence < 0.5:
            risks.append("LOW_CONFIDENCE_DETECTED")
        
        if "high" in [claude_opinion.estimated_effort, chatgpt_opinion.estimated_effort]:
            risks.append("HIGH_EFFORT_REQUIRED")
        
        if claude_opinion.approval != chatgpt_opinion.approval:
            risks.append("DISAGREEMENT_ON_APPROVAL")
        
        # Analizar palabras clave en risk_assessment
        risk_keywords = ["breaking", "dangerous", "unstable", "deprecated", "security"]
        for opinion in [claude_opinion, chatgpt_opinion]:
            for keyword in risk_keywords:
                if keyword in opinion.risk_assessment.lower():
                    risks.append(f"RISK_KEYWORD_{keyword.upper()}")
        
        return risks
    
    def _merge_suggestions(self, claude_opinion: AIOpinion, chatgpt_opinion: AIOpinion) -> List[str]:
        """Combina las sugerencias de ambas IAs eliminando duplicados"""
        all_suggestions = claude_opinion.suggested_changes + chatgpt_opinion.suggested_changes
        return list(set(all_suggestions))  # Eliminar duplicados
    
    def _log_consensus(self, task_id: str, consensus_result: Dict, claude_opinion: AIOpinion, chatgpt_opinion: AIOpinion):
        """Registra el resultado del consenso en el log"""
        log_data = self._load_json(self.consensus_log)
        
        log_entry = {
            "task_id": task_id,
            "consensus_result": consensus_result,
            "claude_opinion": asdict(claude_opinion),
            "chatgpt_opinion": asdict(chatgpt_opinion),
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        
        log_data["consensus_history"].append(log_entry)
        
        # Actualizar estadísticas
        stats = log_data.get("stats", {})
        consensus_type = consensus_result["consensus_type"]
        stats[consensus_type] = stats.get(consensus_type, 0) + 1
        log_data["stats"] = stats
        
        self._save_json(self.consensus_log, log_data)
    
    def _get_project_context(self) -> Dict:
        """Obtiene contexto del proyecto para las IAs"""
        try:
            # Información básica del proyecto
            context = {
                "project_name": "AlmacénPro v2.0",
                "architecture": "MVC with PyQt5",
                "database": "SQLite",
                "main_technologies": ["Python", "PyQt5", "SQLite", "Alembic"],
                "current_phase": "Production Ready",
            }
            
            # Agregar información de archivos recientes si existe
            if (ROOT / "CLAUDE.md").exists():
                context["project_docs"] = "CLAUDE.md available"
            
            return context
        except Exception as e:
            logger.error(f"Error getting project context: {e}")
            return {"error": str(e)}
    
    def _get_recent_tasks(self, limit: int = 5) -> List[Dict]:
        """Obtiene las tareas recientes para contexto"""
        tasks_data = self._load_json(self.tasks_db)
        recent_tasks = sorted(
            tasks_data.get("tasks", []), 
            key=lambda x: x.get("updated_at", ""), 
            reverse=True
        )[:limit]
        return recent_tasks
    
    def get_collaboration_stats(self) -> Dict:
        """Obtiene estadísticas del sistema colaborativo"""
        consensus_data = self._load_json(self.consensus_log)
        tasks_data = self._load_json(self.tasks_db)
        
        return {
            "total_tasks": len(tasks_data.get("tasks", [])),
            "consensus_stats": consensus_data.get("stats", {}),
            "recent_activity": len(self._get_recent_tasks(10)),
            "system_health": "operational"  # Podríamos añadir más métricas
        }


# === Funciones de conveniencia ===

def create_collaborative_task(
    title: str, 
    description: str, 
    priority: str = "medium",
    proposed_by: str = "claude",
    files_affected: List[str] = None
) -> CollaborationTask:
    """Función de conveniencia para crear tareas colaborativas"""
    system = CollaborativeAISystem()
    
    priority_enum = TaskPriority(priority)
    agent_enum = AIAgent.CLAUDE if proposed_by.lower() == "claude" else AIAgent.CHATGPT
    
    return system.create_task(
        title=title,
        description=description,
        priority=priority_enum,
        proposed_by=agent_enum,
        files_affected=files_affected
    )

async def run_collaborative_review(task_id: str) -> Dict:
    """Ejecuta una revisión colaborativa completa para una tarea"""
    system = CollaborativeAISystem()
    
    # Cargar tarea
    tasks_data = system._load_json(system.tasks_db)
    task_dict = next((t for t in tasks_data["tasks"] if t["id"] == task_id), None)
    
    if not task_dict:
        raise ValueError(f"Tarea {task_id} no encontrada")
    
    # Convertir a objeto
    task = CollaborationTask(**task_dict)
    
    # Solicitar opiniones
    claude_opinion, chatgpt_opinion = await system.request_opinions(task)
    
    # Evaluar consenso
    consensus_result = system.evaluate_consensus(task, claude_opinion, chatgpt_opinion)
    
    return {
        "task": asdict(task),
        "claude_opinion": asdict(claude_opinion),
        "chatgpt_opinion": asdict(chatgpt_opinion),
        "consensus": consensus_result
    }
