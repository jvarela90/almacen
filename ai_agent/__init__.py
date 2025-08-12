"""
Sistema de Colaboración AI para AlmacénPro v2.0
Integra Claude Code (local) y ChatGPT (remoto) como equipo de desarrollo senior
"""

from .collaborative_ai_system import (
    CollaborativeAISystem,
    CollaborationTask,
    AIOpinion,
    TaskPriority,
    TaskStatus,
    AIAgent,
    create_collaborative_task,
    run_collaborative_review
)

from .enhanced_ai_devops import EnhancedAIDevOps

from .github_integration import (
    GitHubIntegration,
    ChatGPTGitHubReviewer,
    create_github_reviewer,
    review_with_github_context
)

from .ai_coordination_cli import main as run_coordination_cli

__version__ = "2.0.0"
__all__ = [
    # Sistema colaborativo principal
    "CollaborativeAISystem",
    "CollaborationTask", 
    "AIOpinion",
    "TaskPriority",
    "TaskStatus",
    "AIAgent",
    "create_collaborative_task",
    "run_collaborative_review",
    
    # DevOps mejorado
    "EnhancedAIDevOps",
    
    # Integración GitHub
    "GitHubIntegration",
    "ChatGPTGitHubReviewer", 
    "create_github_reviewer",
    "review_with_github_context",
    
    # CLI
    "run_coordination_cli"
]