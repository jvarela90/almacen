#!/usr/bin/env python3
"""
Script de prueba para el sistema colaborativo AI
Demuestra el funcionamiento sin necesidad de Claude API Key
"""

import sys
import json
from pathlib import Path

# Agregar directorio raz al path
sys.path.insert(0, str(Path(__file__).parent))

def test_claude_code_integration():
    """Prueba la integracin directa con Claude Code"""
    
    print("[TEST] Probando Sistema Colaborativo AI sin Claude API Key\n")
    
    try:
        # 1. Test de configuracin bsica
        print("1. [OK] Verificando configuracin...")
        from ai_agent.config import ROOT, AI_SYNC_DIR, OPENAI_API_KEY
        print(f"   - Directorio raz: {ROOT}")
        print(f"   - Directorio sync: {AI_SYNC_DIR}")
        print(f"   - OpenAI API configurada: {'S' if OPENAI_API_KEY else 'No'}")
        
        # 2. Crear tarea de prueba (sin importar GitHub)
        print("\n2. [OK] Creando tarea colaborativa de prueba...")
        from ai_agent.collaborative_ai_system import create_collaborative_task
        
        task = create_collaborative_task(
            title="Prueba del sistema colaborativo",
            description="Verificar que el sistema funciona sin Claude API Key",
            priority="medium",
            proposed_by="claude"
        )
        
        print(f"   - Tarea creada: {task.id}")
        print(f"   - Ttulo: {task.title}")
        print(f"   - Prioridad: {task.priority.value}")
        
        # 3. Test de respuestas simuladas de Claude
        print("\n3. [OK] Probando respuestas simuladas de Claude...")
        from ai_agent.ai_helpers import _create_intelligent_mock_response
        
        # Test respuesta de opinin
        opinion_prompt = "Evala esta tarea. Responde con JSON con approval, confidence, reasoning."
        opinion_response = _create_intelligent_mock_response(opinion_prompt)
        opinion_data = json.loads(opinion_response)
        
        print(f"   - Aprobacin simulada: {'[SI]' if opinion_data.get('approval') else '[NO]'}")
        print(f"   - Confianza: {opinion_data.get('confidence', 0):.1%}")
        print(f"   - Razonamiento: {opinion_data.get('reasoning', '')[:60]}...")
        
        # 4. Test de sistema de consenso
        print("\n4. [OK] Probando sistema de consenso...")
        from ai_agent.collaborative_ai_system import CollaborativeAISystem, AIOpinion, AIAgent
        import datetime
        
        system = CollaborativeAISystem()
        
        # Crear opiniones simuladas
        claude_opinion = AIOpinion(
            agent=AIAgent.CLAUDE,
            task_id=task.id,
            approval=True,
            confidence=0.8,
            reasoning="Implementacin factible desde perspectiva tcnica",
            suggested_changes=["Agregar tests", "Documentar cambios"],
            estimated_effort="medium",
            risk_assessment="Riesgo bajo",
            timestamp=datetime.datetime.utcnow().isoformat()
        )
        
        chatgpt_opinion = AIOpinion(
            agent=AIAgent.CHATGPT,
            task_id=task.id,
            approval=True,
            confidence=0.7,
            reasoning="Alineado con arquitectura MVC existente",
            suggested_changes=["Verificar compatibilidad", "Revisar performance"],
            estimated_effort="medium",
            risk_assessment="Riesgo medio-bajo",
            timestamp=datetime.datetime.utcnow().isoformat()
        )
        
        # Evaluar consenso
        consensus = system.evaluate_consensus(task, claude_opinion, chatgpt_opinion)
        
        print(f"   - Tipo de consenso: {consensus['consensus_type']}")
        print(f"   - Recomendacin: {consensus['recommendation']}")
        print(f"   - Confianza promedio: {consensus['avg_confidence']:.1%}")
        
        # 5. Test opcional de ChatGPT real si est configurado
        print("\n5. [TEST] Probando integracin con ChatGPT...")
        if OPENAI_API_KEY and len(OPENAI_API_KEY) > 20:
            try:
                from ai_agent.ai_helpers import call_openai_chat
                
                response = call_openai_chat(
                    "Responde solo con 'SISTEMA_OK' si recibes este mensaje",
                    system="Eres un asistente de prueba",
                    temperature=0.0
                )
                
                if "SISTEMA_OK" in response.upper():
                    print("   - ChatGPT: Comunicacin exitosa")
                else:
                    print(f"   - ChatGPT: Respuesta inesperada - {response[:30]}...")
                    
            except Exception as e:
                print(f"   - ChatGPT: Error - {e}")
                print("   - El sistema funciona sin ChatGPT usando respuestas simuladas")
        else:
            print("   - Tip: Configura OPENAI_API_KEY para habilitar ChatGPT real")
        
        # 6. Verificar estadsticas del sistema
        print("\n6. [OK] Verificando estadsticas del sistema...")
        stats = system.get_collaboration_stats()
        
        print(f"   - Total de tareas: {stats['total_tasks']}")
        print(f"   - Actividad reciente: {stats['recent_activity']}")
        print(f"   - Estado del sistema: {stats['system_health']}")
        
        print("\n[SUCCESS] Test completado exitosamente!")
        
        print("\n[RESUMEN] Resultados:")
        print("   + Sistema colaborativo funcionando")
        print("   + Creacin de tareas operativa")
        print("   + Respuestas simuladas inteligentes")
        print("   + Sistema de consenso activo")
        print("   + Base de datos de tareas funcionando")
        
        print("\n[COMANDOS] Disponibles:")
        print("   python ai_team_cli.py demo")
        print("   python ai_team_cli.py create-task --title 'Mi tarea'")
        print("   python ai_team_cli.py list-tasks")
        print("   python ai_team_cli.py stats")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Error en el test: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_claude_code_integration()
    sys.exit(0 if success else 1)