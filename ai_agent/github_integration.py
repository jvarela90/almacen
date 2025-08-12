#!/usr/bin/env python3
"""
Integración con GitHub para el Sistema Colaborativo AI
Permite a ChatGPT acceder y revisar el repositorio remoto
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass

try:
    import requests
    from github import Github
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    
from .config import ROOT

logger = logging.getLogger("github_integration")

@dataclass
class GitHubRepoInfo:
    """Información del repositorio de GitHub"""
    owner: str
    repo: str
    branch: str
    commit_sha: str
    url: str

class GitHubIntegration:
    """Integra el sistema colaborativo con GitHub para acceso remoto"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token or os.getenv("GITHUB_TOKEN")
        self.github_client = None
        
        if GITHUB_AVAILABLE and self.token:
            try:
                self.github_client = Github(self.token)
                logger.info("GitHub client inicializado correctamente")
            except Exception as e:
                logger.error(f"Error inicializando GitHub client: {e}")
        else:
            logger.warning("GitHub no disponible (falta token o librería PyGithub)")
    
    def get_repo_info(self) -> Optional[GitHubRepoInfo]:
        """Obtiene información del repositorio actual"""
        try:
            # Obtener info del git local
            import git
            repo = git.Repo(str(ROOT))
            
            # Obtener URL del remote origin
            origin_url = repo.remotes.origin.url
            
            # Parsear URL para extraer owner/repo
            if "github.com" in origin_url:
                if origin_url.startswith("git@"):
                    # SSH: git@github.com:owner/repo.git
                    parts = origin_url.replace("git@github.com:", "").replace(".git", "").split("/")
                else:
                    # HTTPS: https://github.com/owner/repo.git
                    parts = origin_url.replace("https://github.com/", "").replace(".git", "").split("/")
                
                if len(parts) >= 2:
                    owner, repo_name = parts[0], parts[1]
                    
                    return GitHubRepoInfo(
                        owner=owner,
                        repo=repo_name,
                        branch=repo.active_branch.name,
                        commit_sha=repo.head.commit.hexsha,
                        url=f"https://github.com/{owner}/{repo_name}"
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error obteniendo info del repo: {e}")
            return None
    
    def get_file_content(self, file_path: str, ref: str = None) -> Optional[str]:
        """Obtiene el contenido de un archivo desde GitHub"""
        if not self.github_client:
            return None
            
        try:
            repo_info = self.get_repo_info()
            if not repo_info:
                return None
            
            repo = self.github_client.get_repo(f"{repo_info.owner}/{repo_info.repo}")
            ref = ref or repo_info.branch
            
            file_content = repo.get_contents(file_path, ref=ref)
            return file_content.decoded_content.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Error obteniendo archivo {file_path}: {e}")
            return None
    
    def get_directory_structure(self, path: str = "", ref: str = None) -> List[Dict]:
        """Obtiene la estructura de directorios desde GitHub"""
        if not self.github_client:
            return []
            
        try:
            repo_info = self.get_repo_info()
            if not repo_info:
                return []
            
            repo = self.github_client.get_repo(f"{repo_info.owner}/{repo_info.repo}")
            ref = ref or repo_info.branch
            
            contents = repo.get_contents(path, ref=ref)
            
            structure = []
            for item in contents:
                structure.append({
                    "name": item.name,
                    "path": item.path,
                    "type": item.type,  # "file" or "dir"
                    "size": item.size if item.type == "file" else None
                })
            
            return structure
            
        except Exception as e:
            logger.error(f"Error obteniendo estructura de {path}: {e}")
            return []
    
    def get_recent_commits(self, limit: int = 10) -> List[Dict]:
        """Obtiene commits recientes del repositorio"""
        if not self.github_client:
            return []
            
        try:
            repo_info = self.get_repo_info()
            if not repo_info:
                return []
            
            repo = self.github_client.get_repo(f"{repo_info.owner}/{repo_info.repo}")
            commits = repo.get_commits()
            
            recent_commits = []
            for commit in commits[:limit]:
                recent_commits.append({
                    "sha": commit.sha,
                    "message": commit.commit.message,
                    "author": commit.commit.author.name,
                    "date": commit.commit.author.date.isoformat(),
                    "url": commit.html_url
                })
            
            return recent_commits
            
        except Exception as e:
            logger.error(f"Error obteniendo commits: {e}")
            return []
    
    def create_chatgpt_context(self, focus_files: List[str] = None) -> Dict:
        """Crea contexto completo para ChatGPT desde GitHub"""
        repo_info = self.get_repo_info()
        if not repo_info:
            return {"error": "No se pudo obtener información del repositorio"}
        
        context = {
            "repository": {
                "owner": repo_info.owner,
                "name": repo_info.repo,
                "branch": repo_info.branch,
                "commit": repo_info.commit_sha,
                "url": repo_info.url
            },
            "structure": {},
            "recent_commits": self.get_recent_commits(5),
            "key_files": {}
        }
        
        # Obtener estructura principal
        root_structure = self.get_directory_structure()
        context["structure"]["root"] = root_structure
        
        # Obtener subdirectorios importantes
        important_dirs = ["managers", "controllers", "models", "ui", "utils", "ai_agent"]
        for dir_name in important_dirs:
            if any(item["name"] == dir_name and item["type"] == "dir" for item in root_structure):
                context["structure"][dir_name] = self.get_directory_structure(dir_name)
        
        # Obtener archivos clave
        key_files = focus_files or [
            "README.md",
            "CLAUDE.md", 
            "requirements.txt",
            "main.py",
            "main_mvc.py"
        ]
        
        for file_path in key_files:
            content = self.get_file_content(file_path)
            if content:
                context["key_files"][file_path] = content[:2000]  # Limitar contenido
        
        return context
    
    def prepare_chatgpt_prompt(self, task_description: str, context: Dict = None) -> str:
        """Prepara prompt especializado para ChatGPT con contexto de GitHub"""
        
        if not context:
            context = self.create_chatgpt_context()
        
        prompt = f"""
Eres CHATGPT, un arquitecto de software senior trabajando en revisión remota desde GitHub.

Repositorio: {context.get('repository', {}).get('url', 'N/A')}
Branch: {context.get('repository', {}).get('branch', 'N/A')}
Commit: {context.get('repository', {}).get('commit', 'N/A')[:8]}

Tarea a revisar:
{task_description}

Contexto del proyecto desde GitHub:

ESTRUCTURA DEL PROYECTO:
{self._format_structure_for_prompt(context.get('structure', {}))}

COMMITS RECIENTES:
{self._format_commits_for_prompt(context.get('recent_commits', []))}

ARCHIVOS CLAVE:
{self._format_files_for_prompt(context.get('key_files', {}))}

Como arquitecto revisor, evalúa:
1. Alineación con arquitectura MVC existente
2. Coherencia con patrones del proyecto
3. Impacto en mantenibilidad y escalabilidad
4. Riesgos arquitecturales
5. Mejores prácticas y estándares

Responde con tu análisis y recomendaciones.
"""
        
        return prompt
    
    def _format_structure_for_prompt(self, structure: Dict) -> str:
        """Formatea la estructura del proyecto para el prompt"""
        formatted = []
        
        for folder, items in structure.items():
            if items:
                formatted.append(f"{folder}/")
                for item in items[:10]:  # Limitar items
                    prefix = "  ├── " if item != items[-1] else "  └── "
                    formatted.append(f"{prefix}{item['name']}{'/' if item['type'] == 'dir' else ''}")
        
        return "\n".join(formatted)
    
    def _format_commits_for_prompt(self, commits: List[Dict]) -> str:
        """Formatea commits para el prompt"""
        formatted = []
        
        for commit in commits:
            formatted.append(
                f"• {commit['sha'][:8]} - {commit['message'][:60]} ({commit['author']})"
            )
        
        return "\n".join(formatted)
    
    def _format_files_for_prompt(self, files: Dict[str, str]) -> str:
        """Formatea archivos clave para el prompt"""
        formatted = []
        
        for file_path, content in files.items():
            formatted.append(f"=== {file_path} ===")
            formatted.append(content)
            formatted.append("")
        
        return "\n".join(formatted)

class ChatGPTGitHubReviewer:
    """Revisor especializado que trabaja con GitHub"""
    
    def __init__(self, github_token: Optional[str] = None):
        self.github_integration = GitHubIntegration(github_token)
    
    async def review_task_from_github(
        self, 
        task_description: str, 
        focus_files: List[str] = None
    ) -> Dict:
        """Ejecuta revisión desde GitHub"""
        
        try:
            # Crear contexto desde GitHub
            context = self.github_integration.create_chatgpt_context(focus_files)
            
            if "error" in context:
                return {
                    "error": context["error"],
                    "review_completed": False
                }
            
            # Preparar prompt especializado
            prompt = self.github_integration.prepare_chatgpt_prompt(
                task_description, context
            )
            
            # Ejecutar revisión con ChatGPT
            from .ai_helpers import call_openai_chat, extract_json_from_text
            
            review_response = call_openai_chat(
                prompt,
                system="Eres un arquitecto senior especializado en revisión de código desde repositorios remotos.",
                temperature=0.1
            )
            
            # Procesar respuesta
            return {
                "review_completed": True,
                "github_context": context["repository"],
                "review_response": review_response,
                "structured_review": extract_json_from_text(review_response),
                "focus_files": focus_files,
                "timestamp": context.get("timestamp")
            }
            
        except Exception as e:
            logger.error(f"Error en revisión desde GitHub: {e}")
            return {
                "error": str(e),
                "review_completed": False
            }

# === Funciones de conveniencia ===

def create_github_reviewer(token: Optional[str] = None) -> ChatGPTGitHubReviewer:
    """Crea un revisor de GitHub"""
    return ChatGPTGitHubReviewer(token)

async def review_with_github_context(
    task_description: str, 
    focus_files: List[str] = None,
    github_token: Optional[str] = None
) -> Dict:
    """Función de conveniencia para revisión con contexto de GitHub"""
    reviewer = create_github_reviewer(github_token)
    return await reviewer.review_task_from_github(task_description, focus_files)
