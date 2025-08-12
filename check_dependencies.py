#!/usr/bin/env python3
"""
Script de verificación de dependencias - Generado por AI Team
Corrige problemas identificados en la revisión colaborativa
"""

import sys
import subprocess
import importlib.util
from pathlib import Path

def check_module(module_name, pip_name=None):
    """Verifica si un módulo está disponible"""
    try:
        spec = importlib.util.find_spec(module_name)
        if spec is not None:
            print(f"[OK] {module_name} - Disponible")
            return True
        else:
            print(f"[FALTA] {module_name} - No encontrado")
            if pip_name:
                print(f"   Instalar con: pip install {pip_name}")
            return False
    except Exception as e:
        print(f"[ERROR] {module_name} - {e}")
        return False

def install_missing_package(package_name):
    """Instala un paquete faltante"""
    try:
        print(f"[INSTALANDO] {package_name}...")
        result = subprocess.run([sys.executable, "-m", "pip", "install", package_name], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"[OK] {package_name} instalado exitosamente")
            return True
        else:
            print(f"[ERROR] Error instalando {package_name}: {result.stderr}")
            return False
    except Exception as e:
        print(f"[ERROR] Excepción instalando {package_name}: {e}")
        return False

def main():
    """Verificación y corrección automática de dependencias"""
    
    print("=" * 60)
    print("VERIFICACIÓN DE DEPENDENCIAS - AI TEAM DIAGNOSTIC")
    print("=" * 60)
    
    # Dependencias críticas para la aplicación principal
    critical_deps = [
        ("PyQt5.QtWidgets", "PyQt5"),
        ("PyQt5.QtCore", "PyQt5"),
        ("PyQt5.QtGui", "PyQt5"),
    ]
    
    # Dependencias del sistema colaborativo AI
    ai_deps = [
        ("openai", "openai"),
        ("requests", "requests"),
        ("json", None),  # Built-in
        ("pathlib", None),  # Built-in
    ]
    
    # Dependencias opcionales
    optional_deps = [
        ("github", "PyGithub"),
        ("rich", "rich"),
        ("git", "gitpython"),
    ]
    
    print("\n1. VERIFICANDO DEPENDENCIAS CRÍTICAS...")
    critical_missing = []
    for module, pip_name in critical_deps:
        if not check_module(module, pip_name):
            if pip_name and pip_name not in critical_missing:
                critical_missing.append(pip_name)
    
    print("\n2. VERIFICANDO DEPENDENCIAS AI...")
    ai_missing = []
    for module, pip_name in ai_deps:
        if not check_module(module, pip_name):
            if pip_name and pip_name not in ai_missing:
                ai_missing.append(pip_name)
    
    print("\n3. VERIFICANDO DEPENDENCIAS OPCIONALES...")
    optional_missing = []
    for module, pip_name in optional_deps:
        if not check_module(module, pip_name):
            if pip_name and pip_name not in optional_missing:
                optional_missing.append(pip_name)
    
    # Instalar dependencias faltantes
    if critical_missing:
        print(f"\n[CRÍTICO] Faltan dependencias críticas: {critical_missing}")
        for package in critical_missing:
            install_missing_package(package)
    
    if ai_missing:
        print(f"\n[AI] Faltan dependencias AI: {ai_missing}")
        for package in ai_missing:
            install_missing_package(package)
    
    # Verificación final
    print("\n4. VERIFICACIÓN FINAL...")
    
    # Test de importación main_mvc
    try:
        import main_mvc
        print("[OK] main_mvc.py - Se importa correctamente")
    except Exception as e:
        print(f"[ERROR] main_mvc.py - {e}")
    
    # Test de sistema AI
    try:
        from ai_agent import CollaborativeAISystem
        print("[OK] ai_agent - Sistema colaborativo disponible")
    except Exception as e:
        print(f"[ERROR] ai_agent - {e}")
    
    # Información del entorno
    print("\n5. INFORMACIÓN DEL ENTORNO...")
    print(f"   Python: {sys.version}")
    print(f"   Ejecutable: {sys.executable}")
    print(f"   Directorio: {Path.cwd()}")
    
    # Recomendaciones
    print("\n6. RECOMENDACIONES...")
    if critical_missing:
        print("   - Ejecutar: pip install PyQt5")
        print("   - Verificar que el entorno virtual esté activo")
    
    if optional_missing:
        print("   - Para funcionalidad completa:")
        for pkg in optional_missing:
            print(f"     pip install {pkg}")
    
    print("\n" + "=" * 60)
    print("DIAGNÓSTICO COMPLETADO")
    print("=" * 60)

if __name__ == "__main__":
    main()