#!/usr/bin/env python3
"""
Script de configuración de Pre-commit - AlmacénPro v2.0
Automatiza la instalación y configuración de herramientas de calidad de código
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Optional


def run_command(cmd: List[str], cwd: Optional[str] = None) -> Tuple[bool, str, str]:
    """
    Ejecutar comando y retornar resultado
    
    Args:
        cmd: Comando a ejecutar como lista
        cwd: Directorio de trabajo
        
    Returns:
        Tuple de (éxito, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)


def check_python_version() -> bool:
    """Verificar versión de Python"""
    version = sys.version_info
    print(f"🐍 Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("✅ Versión de Python compatible")
        return True
    else:
        print("❌ Se requiere Python 3.8 o superior")
        return False


def install_dev_dependencies() -> bool:
    """Instalar dependencias de desarrollo"""
    print("\n📦 Instalando dependencias de desarrollo...")
    
    # Instalar desde pyproject.toml
    success, stdout, stderr = run_command([
        sys.executable, "-m", "pip", "install", "-e", ".[dev]"
    ])
    
    if success:
        print("✅ Dependencias de desarrollo instaladas")
        return True
    else:
        print(f"❌ Error instalando dependencias: {stderr}")
        return False


def install_precommit() -> bool:
    """Instalar y configurar pre-commit"""
    print("\n🔧 Configurando pre-commit...")
    
    # Instalar hooks
    success, stdout, stderr = run_command(["pre-commit", "install"])
    if not success:
        print(f"❌ Error instalando hooks de pre-commit: {stderr}")
        return False
        
    print("✅ Hooks de pre-commit instalados")
    
    # Instalar hooks de pre-push (opcional)
    success, stdout, stderr = run_command([
        "pre-commit", "install", "--hook-type", "pre-push"
    ])
    if success:
        print("✅ Hooks de pre-push instalados")
    else:
        print(f"⚠️ Advertencia: No se pudieron instalar hooks de pre-push: {stderr}")
    
    return True


def run_initial_checks() -> bool:
    """Ejecutar verificaciones iniciales en todos los archivos"""
    print("\n🔍 Ejecutando verificaciones iniciales en todo el código...")
    print("⏰ Esto puede tomar algunos minutos en la primera ejecución...")
    
    success, stdout, stderr = run_command([
        "pre-commit", "run", "--all-files"
    ])
    
    if success:
        print("✅ Todas las verificaciones pasaron exitosamente")
        return True
    else:
        print("⚠️ Algunas verificaciones fallaron o hicieron correcciones automáticas")
        print("\n📋 Salida de pre-commit:")
        print(stdout)
        if stderr:
            print(f"\n❌ Errores: {stderr}")
        
        # Muchas veces los errores son solo correcciones automáticas
        print("\n💡 Tip: Los hooks pueden haber corregido automáticamente algunos problemas.")
        print("     Ejecute 'git status' para ver los cambios realizados.")
        return False


def update_gitignore() -> bool:
    """Actualizar .gitignore con entradas relacionadas a herramientas de desarrollo"""
    gitignore_path = Path(".gitignore")
    
    # Entradas adicionales para herramientas de desarrollo
    dev_entries = [
        "# ============================================================================",
        "# HERRAMIENTAS DE DESARROLLO Y CALIDAD",
        "# ============================================================================",
        ".pre-commit-cache/",
        "pre-commit-hooks.log",
        ".mypy_cache/",
        ".pytest_cache/",
        ".coverage",
        "htmlcov/",
        "coverage.xml",
        ".bandit",
        "*.cover",
        ".hypothesis/",
        ""
    ]
    
    if gitignore_path.exists():
        content = gitignore_path.read_text(encoding='utf-8')
        if "HERRAMIENTAS DE DESARROLLO Y CALIDAD" not in content:
            with open(gitignore_path, 'a', encoding='utf-8') as f:
                f.write("\n".join(dev_entries))
            print("✅ .gitignore actualizado con entradas de herramientas de desarrollo")
        else:
            print("ℹ️ .gitignore ya contiene entradas de herramientas de desarrollo")
    
    return True


def create_dev_scripts() -> bool:
    """Crear scripts útiles para desarrollo"""
    scripts_content = {
        "format_code.py": '''#!/usr/bin/env python3
"""Script para formatear código manualmente"""
import subprocess
import sys

def main():
    """Ejecutar formateo de código"""
    print("🎨 Formateando código...")
    
    # Black
    subprocess.run([sys.executable, "-m", "black", "."], check=False)
    
    # isort
    subprocess.run([sys.executable, "-m", "isort", "."], check=False)
    
    # autoflake
    subprocess.run([
        sys.executable, "-m", "autoflake", 
        "--in-place", "--recursive", 
        "--remove-all-unused-imports",
        "."
    ], check=False)
    
    print("✅ Formateo completado")

if __name__ == "__main__":
    main()
''',
        "check_code.py": '''#!/usr/bin/env python3
"""Script para verificar calidad de código"""
import subprocess
import sys

def main():
    """Ejecutar verificaciones de código"""
    print("🔍 Verificando calidad de código...")
    
    success = True
    
    # Flake8
    print("\n📋 Ejecutando Flake8...")
    result = subprocess.run([sys.executable, "-m", "flake8", "."], check=False)
    if result.returncode != 0:
        success = False
    
    # MyPy
    print("\n🔎 Ejecutando MyPy...")
    result = subprocess.run([sys.executable, "-m", "mypy", "."], check=False)
    if result.returncode != 0:
        print("⚠️ MyPy encontró problemas de tipos (no crítico)")
    
    # Bandit
    print("\n🔒 Ejecutando Bandit (seguridad)...")
    result = subprocess.run([
        sys.executable, "-m", "bandit", 
        "-r", ".", "-f", "custom",
        "--skip", "B101,B601,B701"
    ], check=False)
    if result.returncode != 0:
        print("⚠️ Bandit encontró posibles problemas de seguridad")
    
    if success:
        print("\n✅ Todas las verificaciones pasaron")
    else:
        print("\n❌ Algunas verificaciones fallaron")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    }
    
    scripts_dir = Path("scripts")
    scripts_dir.mkdir(exist_ok=True)
    
    for filename, content in scripts_content.items():
        script_path = scripts_dir / filename
        script_path.write_text(content, encoding='utf-8')
        
        # Hacer ejecutable en sistemas Unix
        if os.name != 'nt':
            os.chmod(script_path, 0o755)
    
    print("✅ Scripts de desarrollo creados en ./scripts/")
    return True


def main():
    """Función principal del script de configuración"""
    print("🚀 AlmacénPro v2.0 - Configuración de Pre-commit")
    print("=" * 60)
    
    # Verificar directorio actual
    if not Path("pyproject.toml").exists():
        print("❌ Error: Este script debe ejecutarse desde el directorio raíz del proyecto")
        print("   (donde está ubicado pyproject.toml)")
        sys.exit(1)
    
    # Verificar versión de Python
    if not check_python_version():
        sys.exit(1)
    
    # Instalar dependencias
    if not install_dev_dependencies():
        sys.exit(1)
    
    # Configurar pre-commit
    if not install_precommit():
        sys.exit(1)
    
    # Actualizar .gitignore
    update_gitignore()
    
    # Crear scripts de desarrollo
    create_dev_scripts()
    
    # Ejecutar verificaciones iniciales
    print("\n" + "=" * 60)
    initial_success = run_initial_checks()
    
    # Resumen final
    print("\n" + "=" * 60)
    print("🎉 ¡Configuración de Pre-commit completada!")
    
    if initial_success:
        print("✅ Todo está listo para usar")
    else:
        print("⚠️ Algunas verificaciones requieren atención")
        print("   Los hooks pueden haber hecho correcciones automáticas")
        print("   Revise los cambios con 'git status' y haga commit si es necesario")
    
    print("\n📋 Próximos pasos:")
    print("1. Revisar cambios automáticos: git status")
    print("2. Hacer commit de cambios si es necesario")
    print("3. Los hooks se ejecutarán automáticamente en cada commit")
    print("4. Para ejecutar manualmente: pre-commit run --all-files")
    print("5. Para actualizar hooks: pre-commit autoupdate")
    
    print("\n🛠️ Scripts disponibles:")
    print("   - python scripts/format_code.py   # Formatear código")
    print("   - python scripts/check_code.py    # Verificar calidad")
    
    print("\n⚙️ Configuración completada exitosamente!")


if __name__ == "__main__":
    main()