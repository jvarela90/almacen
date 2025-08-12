#!/usr/bin/env python3
"""
Integración Directa con Claude Code
Maneja la comunicación con Claude Code que ya está ejecutándose localmente
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

from .config import AI_SYNC_DIR

logger = logging.getLogger("claude_code_integration")

@dataclass
class ClaudeCodeRequest:
    """Representa una solicitud a Claude Code"""
    prompt: str
    request_id: str
    timestamp: str
    context: Dict = None
    priority: str = "medium"

@dataclass
class ClaudeCodeResponse:
    """Representa una respuesta de Claude Code"""
    request_id: str
    response: str
    timestamp: str
    status: str = "completed"
    metadata: Dict = None

class ClaudeCodeInterface:
    """Interfaz para comunicarse directamente con Claude Code local"""
    
    def __init__(self):
        self.requests_dir = AI_SYNC_DIR / "claude_requests"
        self.responses_dir = AI_SYNC_DIR / "claude_responses"
        self.status_file = AI_SYNC_DIR / "claude_status.json"
        
        # Crear directorios si no existen
        self.requests_dir.mkdir(exist_ok=True)
        self.responses_dir.mkdir(exist_ok=True)
        
        # Inicializar archivo de estado
        if not self.status_file.exists():
            self._update_status("initialized", "Claude Code interface ready")
    
    def _update_status(self, status: str, message: str):
        """Actualiza el archivo de estado"""
        status_data = {
            "status": status,
            "message": message,
            "timestamp": time.time(),
            "last_request_id": getattr(self, 'last_request_id', None)
        }
        
        self.status_file.write_text(json.dumps(status_data, indent=2), encoding="utf-8")
    
    def create_request(
        self, 
        prompt: str, 
        context: Dict = None, 
        priority: str = "medium"
    ) -> ClaudeCodeRequest:
        """Crea una nueva solicitud para Claude Code"""
        
        request_id = f"req_{int(time.time())}_{hash(prompt) % 10000}"
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        request = ClaudeCodeRequest(
            prompt=prompt,
            request_id=request_id,
            timestamp=timestamp,
            context=context or {},
            priority=priority
        )
        
        # Guardar solicitud en archivo
        request_file = self.requests_dir / f"{request_id}.json"
        request_data = {
            "request_id": request.request_id,
            "prompt": request.prompt,
            "timestamp": request.timestamp,
            "context": request.context,
            "priority": request.priority,
            "status": "pending"
        }
        
        request_file.write_text(json.dumps(request_data, indent=2), encoding="utf-8")
        
        # Crear archivo de prompt legible para Claude Code
        prompt_file = self.requests_dir / f"{request_id}_prompt.md"
        prompt_content = f"""
# Claude Code Request: {request_id}

**Timestamp**: {timestamp}
**Priority**: {priority}

## Context
{json.dumps(context or {}, indent=2)}

## Prompt
{prompt}

---

**Instructions for Claude Code**: 
Please analyze this request and provide your response. When you're ready to respond:

1. Create a response file: `ai_sync/claude_responses/{request_id}_response.md`
2. Include your analysis in markdown format
3. If returning structured data, include a JSON block
4. Update the status by creating: `ai_sync/claude_responses/{request_id}_status.json`

Thank you!
"""
        
        prompt_file.write_text(prompt_content, encoding="utf-8")
        
        self._update_status("request_created", f"Request {request_id} created")
        self.last_request_id = request_id
        
        logger.info(f"Claude Code request created: {request_id}")
        return request
    
    def check_response(self, request_id: str, timeout: int = 30) -> Optional[ClaudeCodeResponse]:
        """Verifica si hay respuesta de Claude Code para una solicitud"""
        
        response_file = self.responses_dir / f"{request_id}_response.md"
        status_file = self.responses_dir / f"{request_id}_status.json"
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if response_file.exists():
                try:
                    response_content = response_file.read_text(encoding="utf-8")
                    
                    # Leer estado si existe
                    status_data = {"status": "completed", "metadata": {}}
                    if status_file.exists():
                        status_data = json.loads(status_file.read_text(encoding="utf-8"))
                    
                    response = ClaudeCodeResponse(
                        request_id=request_id,
                        response=response_content,
                        timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                        status=status_data.get("status", "completed"),
                        metadata=status_data.get("metadata", {})
                    )
                    
                    logger.info(f"Claude Code response received: {request_id}")
                    return response
                    
                except Exception as e:
                    logger.error(f"Error reading Claude Code response: {e}")
                    break
            
            time.sleep(1)  # Esperar 1 segundo antes de verificar de nuevo
        
        logger.warning(f"No response from Claude Code within {timeout}s for request {request_id}")
        return None
    
    def send_request_and_wait(
        self, 
        prompt: str, 
        context: Dict = None, 
        priority: str = "medium",
        timeout: int = 60
    ) -> Optional[str]:
        """Envía solicitud y espera respuesta de Claude Code"""
        
        # Crear solicitud
        request = self.create_request(prompt, context, priority)
        
        # Notificar a Claude Code (mostrar mensaje)
        print(f"\n📜 Claude Code, tienes una nueva solicitud:")
        print(f"   ID: {request.request_id}")
        print(f"   Archivo: ai_sync/claude_requests/{request.request_id}_prompt.md")
        print(f"   Prioridad: {priority}")
        print(f"\n🕰️ Esperando tu respuesta (timeout: {timeout}s)...\n")
        
        # Esperar respuesta
        response = self.check_response(request.request_id, timeout)
        
        if response:
            print(f"✅ Respuesta recibida de Claude Code")
            return response.response
        else:
            print(f"⏰ Timeout: No se recibió respuesta de Claude Code en {timeout}s")
            return None
    
    def get_pending_requests(self) -> list:
        """Obtiene las solicitudes pendientes para Claude Code"""
        pending = []
        
        for request_file in self.requests_dir.glob("*.json"):
            try:
                request_data = json.loads(request_file.read_text(encoding="utf-8"))
                
                # Verificar si ya hay respuesta
                request_id = request_data["request_id"]
                response_file = self.responses_dir / f"{request_id}_response.md"
                
                if not response_file.exists():
                    pending.append(request_data)
            except Exception as e:
                logger.error(f"Error reading request file {request_file}: {e}")
        
        return sorted(pending, key=lambda x: x.get("timestamp", ""))
    
    def create_mock_response(self, request_id: str, mock_content: str) -> bool:
        """Crea una respuesta simulada (para testing)"""
        try:
            response_file = self.responses_dir / f"{request_id}_response.md"
            status_file = self.responses_dir / f"{request_id}_status.json"
            
            response_file.write_text(mock_content, encoding="utf-8")
            
            status_data = {
                "status": "completed",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "metadata": {"mock": True}
            }
            status_file.write_text(json.dumps(status_data, indent=2), encoding="utf-8")
            
            return True
        except Exception as e:
            logger.error(f"Error creating mock response: {e}")
            return False

# === Funciones de conveniencia ===

def call_claude_code_direct(
    prompt: str, 
    context: Dict = None, 
    priority: str = "medium",
    timeout: int = 60
) -> Optional[str]:
    """Función de conveniencia para llamar a Claude Code directamente"""
    interface = ClaudeCodeInterface()
    return interface.send_request_and_wait(prompt, context, priority, timeout)

def check_claude_code_requests() -> list:
    """Verifica las solicitudes pendientes para Claude Code"""
    interface = ClaudeCodeInterface()
    return interface.get_pending_requests()

def show_claude_code_dashboard():
    """Muestra un dashboard con el estado de Claude Code"""
    interface = ClaudeCodeInterface()
    
    print("┌" + "─" * 60 + "┐")
    print("│" + " " * 18 + "CLAUDE CODE DASHBOARD" + " " * 19 + "│")
    print("├" + "─" * 60 + "┤")
    
    # Estado actual
    if interface.status_file.exists():
        status_data = json.loads(interface.status_file.read_text(encoding="utf-8"))
        print(f"│ Estado: {status_data.get('status', 'unknown'):<47} │")
        print(f"│ Última actividad: {time.ctime(status_data.get('timestamp', 0)):<37} │")
    
    # Solicitudes pendientes
    pending = interface.get_pending_requests()
    print(f"│ Solicitudes pendientes: {len(pending):<37} │")
    
    if pending:
        print("├" + "─" * 60 + "┤")
        print("│" + " " * 20 + "SOLICITUDES PENDIENTES" + " " * 17 + "│")
        print("├" + "─" * 60 + "┤")
        
        for req in pending[:5]:  # Mostrar máximo 5
            req_id = req['request_id'][-10:]  # Últimos 10 caracteres
            priority = req.get('priority', 'medium')
            print(f"│ {req_id} | {priority:<8} | {req.get('timestamp', ''):<25} │")
        
        if len(pending) > 5:
            print(f"│ ... y {len(pending) - 5} más{' ' * 42} │")
    
    print("└" + "─" * 60 + "┘")
