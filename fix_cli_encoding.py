#!/usr/bin/env python3
"""
Script para corregir problemas de encoding en ai_team_cli.py
Generado por AI Team - Revisión Colaborativa
"""

import re
from pathlib import Path

def remove_emojis_from_file(file_path):
    """Remueve emojis y caracteres Unicode problemáticos"""
    
    # Mapeo de emojis a texto
    emoji_replacements = {
        '🚀': '[EJECUTANDO]',
        '✅': '[OK]',
        '❌': '[ERROR]',
        '📝': '[TAREA]',
        '📋': '[LISTA]',
        '🎯': '[PRIORIDAD]',
        '🔥': '[ACTIVO]',
        '🟢': '[SISTEMA]',
        '⚠️': '[ADVERTENCIA]',
        '💡': '[TIP]',
        '📊': '[ESTADISTICAS]',
        '🧪': '[TEST]',
        '🤖': '[CLAUDE]',
        '🧠': '[CHATGPT]',
        '⚡': '[CONSENSO]',
        '🎉': '[COMPLETADO]',
        '🔍': '[ANALIZANDO]',
        '⚙️': '[IMPLEMENTADO]',
        '💭': '[RAZONAMIENTO]',
        '🛑': '[CANCELADO]',
        '📄': '[ARCHIVO]',
        '📁': '[DIRECTORIO]',
        '🎭': '[DEMO]',
        '📈': '[METRICAS]',
        '🟡': '[MEDIO]',
        '🟠': '[ALTO]',
        '🔴': '[CRITICO]',
        '⚪': '[DESCONOCIDO]',
        '💬': '',  # Remover sin reemplazo
        '💎': '',
        '🔧': '[HERRAMIENTAS]',
        '🎨': '[DISEÑO]',
        '📦': '[PAQUETE]',
    }
    
    try:
        # Leer archivo
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        
        # Reemplazar emojis
        for emoji, replacement in emoji_replacements.items():
            content = content.replace(emoji, replacement)
        
        # Reemplazar caracteres Unicode problemáticos adicionales
        unicode_patterns = [
            (r'\\U[0-9a-fA-F]{8}', '[EMOJI]'),  # Unicode escapes
            (r'[^\x00-\x7F]+', ''),  # Caracteres no-ASCII restantes
        ]
        
        for pattern, replacement in unicode_patterns:
            content = re.sub(pattern, replacement, content)
        
        # Escribir archivo corregido si hubo cambios
        if content != original_content:
            # Crear backup
            backup_path = file_path.with_suffix('.py.backup')
            backup_path.write_text(original_content, encoding='utf-8')
            
            # Escribir archivo corregido
            file_path.write_text(content, encoding='utf-8')
            
            print(f"[OK] {file_path.name} - Emojis corregidos")
            print(f"     Backup guardado en: {backup_path.name}")
            return True
        else:
            print(f"[OK] {file_path.name} - Sin cambios necesarios")
            return False
            
    except Exception as e:
        print(f"[ERROR] {file_path.name} - {e}")
        return False

def main():
    """Corrige archivos con problemas de encoding"""
    
    print("=" * 50)
    print("CORRECCIÓN DE ENCODING - AI TEAM FIX")
    print("=" * 50)
    
    # Archivos a corregir
    files_to_fix = [
        Path("ai_team_cli.py"),
        Path("ai_team_test.py"),
    ]
    
    fixed_count = 0
    
    for file_path in files_to_fix:
        if file_path.exists():
            if remove_emojis_from_file(file_path):
                fixed_count += 1
        else:
            print(f"[SKIP] {file_path.name} - No encontrado")
    
    print(f"\n[RESUMEN] {fixed_count} archivo(s) corregido(s)")
    
    if fixed_count > 0:
        print("\nPrueba ahora:")
        print("  python ai_team_cli.py demo")
        print("  python ai_team_cli.py list-tasks")

if __name__ == "__main__":
    main()