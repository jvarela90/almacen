# 🎯 Guía Completa de Pre-commit - AlmacénPro v2.0

Pre-commit es un framework que ejecuta automáticamente verificaciones de código antes de cada commit, asegurando calidad y consistencia en el desarrollo.

## 📋 Tabla de Contenidos

- [Instalación y Configuración](#instalación-y-configuración)
- [Herramientas Configuradas](#herramientas-configuradas)
- [Uso Diario](#uso-diario)
- [Comandos Útiles](#comandos-útiles)
- [Personalización](#personalización)
- [Solución de Problemas](#solución-de-problemas)
- [Integración con CI/CD](#integración-con-cicd)

## 🚀 Instalación y Configuración

### Opción 1: Configuración Automática (Recomendado)

```bash
# Ejecutar script de configuración automática
python setup_precommit.py
```

Este script:
- ✅ Instala todas las dependencias de desarrollo
- ✅ Configura los hooks de pre-commit
- ✅ Ejecuta verificaciones iniciales
- ✅ Crea scripts auxiliares de desarrollo

### Opción 2: Configuración Manual

```bash
# 1. Instalar dependencias de desarrollo
pip install -e .[dev]

# 2. Instalar hooks de pre-commit
pre-commit install

# 3. (Opcional) Instalar hooks de pre-push
pre-commit install --hook-type pre-push

# 4. Ejecutar verificación inicial en todo el código
pre-commit run --all-files
```

## 🛠️ Herramientas Configuradas

### 1. **Black** - Formateo Automático de Código
- **Propósito**: Formateo consistente y automático del código Python
- **Configuración**: Líneas de máximo 100 caracteres
- **Automático**: Corrige el formato automáticamente

```bash
# Ejecutar manualmente
black .
```

### 2. **isort** - Ordenamiento de Imports
- **Propósito**: Organizar y ordenar declaraciones de import
- **Configuración**: Compatible con Black, agrupa por categorías
- **Automático**: Reorganiza los imports automáticamente

```bash
# Ejecutar manualmente
isort .
```

### 3. **Flake8** - Análisis de Calidad de Código
- **Propósito**: Detectar errores de estilo, sintaxis y complejidad
- **Configuración**: Máximo 100 caracteres, complejidad ciclomática ≤12
- **Manual**: Requiere corrección manual de problemas

```bash
# Ejecutar manualmente
flake8 .
```

### 4. **Bandit** - Análisis de Seguridad
- **Propósito**: Detectar vulnerabilidades de seguridad comunes
- **Configuración**: Omite falsos positivos comunes
- **Manual**: Requiere revisión manual de hallazgos

```bash
# Ejecutar manualmente
bandit -r . --format custom
```

### 5. **MyPy** - Verificación de Tipos (Opcional)
- **Propósito**: Verificación estática de tipos
- **Configuración**: Modo gradual para migración
- **Manual**: Mejora la calidad del código progresivamente

```bash
# Ejecutar manualmente
mypy .
```

### 6. **Autoflake** - Limpieza de Código
- **Propósito**: Eliminar imports no utilizados y variables
- **Automático**: Limpia automáticamente el código

### 7. **pyupgrade** - Modernización de Sintaxis
- **Propósito**: Actualizar sintaxis a Python 3.8+
- **Automático**: Moderniza automáticamente el código

## 📝 Uso Diario

### Flujo Normal de Desarrollo

```bash
# 1. Hacer cambios en el código
# 2. Añadir archivos al staging
git add .

# 3. Hacer commit (pre-commit se ejecuta automáticamente)
git commit -m "feat: nueva funcionalidad de inventario"

# Los hooks se ejecutan automáticamente:
# ✅ Black reformatea el código si es necesario
# ✅ isort reorganiza imports si es necesario  
# ✅ Flake8 verifica calidad de código
# ✅ Bandit verifica seguridad
# ✅ Otros checks básicos

# 4. Si hay correcciones automáticas, añadir y commitear de nuevo
git add .
git commit -m "feat: nueva funcionalidad de inventario"
```

### Si los Hooks Fallan

```bash
# Ver qué falló exactamente
git commit -m "mi mensaje"
# Output mostrará qué hook falló y por qué

# Corregir manualmente los problemas reportados
# Luego intentar commit de nuevo
git add .
git commit -m "mi mensaje"
```

## ⚡ Comandos Útiles

### Comandos de Pre-commit

```bash
# Ejecutar todos los hooks manualmente
pre-commit run --all-files

# Ejecutar un hook específico
pre-commit run black
pre-commit run flake8
pre-commit run isort

# Ejecutar hooks solo en archivos modificados
pre-commit run

# Actualizar versiones de hooks
pre-commit autoupdate

# Limpiar cache de hooks
pre-commit clean

# Ver información de hooks instalados
pre-commit --version
```

### Scripts de Desarrollo Incluidos

```bash
# Formatear código automáticamente
python scripts/format_code.py

# Verificar calidad de código
python scripts/check_code.py
```

### Omitir Hooks Temporalmente

```bash
# Omitir TODOS los hooks (solo en emergencias)
git commit --no-verify -m "commit de emergencia"

# Omitir hooks específicos
SKIP=flake8,bandit git commit -m "commit parcial"

# Omitir solo un hook
SKIP=mypy git commit -m "commit sin type checking"
```

## ⚙️ Personalización

### Modificar Configuración de Herramientas

Editar `pyproject.toml` para personalizar:

```toml
[tool.black]
line-length = 100  # Cambiar longitud de línea

[tool.flake8]
max-complexity = 12  # Cambiar complejidad máxima
extend-ignore = ["E203", "W503"]  # Ignorar reglas específicas

[tool.isort]
profile = "black"
line_length = 100
```

### Añadir o Quitar Hooks

Editar `.pre-commit-config.yaml`:

```yaml
repos:
  # Añadir nuevo hook
  - repo: https://github.com/pycqa/pydocstyle
    rev: 6.3.0
    hooks:
      - id: pydocstyle
        
  # Comentar para deshabilitar
  # - repo: https://github.com/pre-commit/mirrors-mypy
  #   rev: v1.11.2
  #   hooks:
  #     - id: mypy
```

### Configuración por Archivos

En `pyproject.toml`:

```toml
[tool.flake8]
per-file-ignores = [
    "__init__.py:F401",  # Permitir imports no utilizados en __init__.py
    "test_*.py:S101",    # Permitir asserts en tests
    "ui/*.py:E402"       # Permitir imports tardíos en UI
]
```

## 🔧 Solución de Problemas

### Problema: Hook es Muy Lento

```bash
# Identificar hooks lentos
pre-commit run --all-files --verbose

# Saltar hooks pesados en CI
# Editar .pre-commit-config.yaml
ci:
  skip: [bandit, mypy]
```

### Problema: Conflictos entre Herramientas

```bash
# Black vs Flake8 - asegurar compatibilidad en pyproject.toml
[tool.flake8]
extend-ignore = ["E203", "E501", "W503"]  # Compatibilidad con Black

[tool.isort] 
profile = "black"  # Compatibilidad con Black
```

### Problema: Muchos Errores en Código Existente

```bash
# Aplicar correcciones gradualmente
pre-commit run black --all-files  # Solo formateo
pre-commit run isort --all-files   # Solo imports
pre-commit run autoflake --all-files  # Solo limpieza

# Luego abordar flake8 archivo por archivo
flake8 managers/
flake8 controllers/
# etc.
```

### Problema: Pre-commit No Se Ejecuta

```bash
# Verificar instalación
pre-commit --version

# Reinstalar hooks
pre-commit uninstall
pre-commit install

# Verificar configuración de git
git config --list | grep hooks
```

## 🚀 Integración con CI/CD

### GitHub Actions (Ya Configurado)

El CI/CD ya incluye las mismas verificaciones:

```yaml
- name: Run pre-commit
  uses: pre-commit/action@v3.0.1
```

### pre-commit.ci (Servicio Automático)

Pre-commit.ci ejecuta automáticamente los hooks en PRs:

1. **Configuración**: Ya incluida en `.pre-commit-config.yaml`
2. **Automático**: Crea commits de corrección automática
3. **Gratuito**: Para repositorios públicos

## 📚 Buenas Prácticas

### Para Desarrolladores

1. **Ejecutar verificaciones antes de commit**:
   ```bash
   pre-commit run --all-files
   ```

2. **Mantener commits pequeños**: Los hooks son más rápidos

3. **No omitir hooks sin razón**: `--no-verify` solo en emergencias

4. **Revisar correcciones automáticas**: Entender qué cambia

### Para el Equipo

1. **Actualizar hooks regularmente**:
   ```bash
   pre-commit autoupdate
   ```

2. **Documentar excepciones**: Si se necesita omitir reglas

3. **Capacitar en herramientas**: Entender qué hace cada hook

4. **Configuración consistente**: Misma configuración para todos

## 🎯 Beneficios del Sistema

### ✅ Calidad de Código Automática
- Formateo consistente sin discusiones
- Detección temprana de errores
- Código más legible y mantenible

### ✅ Seguridad Integrada
- Análisis de vulnerabilidades automático
- Prevención de commits inseguros
- Cumplimiento de mejores prácticas

### ✅ Productividad Mejorada
- Menos tiempo en revisiones de código
- Menos bugs en producción
- Onboarding más fácil para nuevos desarrolladores

### ✅ Integración Continua
- Mismas reglas en desarrollo y CI/CD
- Detección temprana de problemas
- Builds más estables

---

## 🆘 Soporte y Ayuda

- **Documentación oficial**: [pre-commit.com](https://pre-commit.com)
- **Configuración del proyecto**: `.pre-commit-config.yaml`
- **Configuración de herramientas**: `pyproject.toml`
- **Scripts auxiliares**: `scripts/format_code.py` y `scripts/check_code.py`

**¿Problemas?** Ejecutar `python setup_precommit.py` para reinstalar configuración completa.