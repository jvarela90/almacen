# 🤖 Sistema de Colaboración AI: Claude Code + ChatGPT

## Descripción General

Este sistema implementa un **equipo de desarrollo senior** compuesto por dos IAs especializadas que trabajan colaborativamente en el desarrollo de AlmacénPro v2.0:

- **🤖 Claude Code (Local)**: Desarrollador implementador especializado en cambios locales
- **🧠 ChatGPT (Remoto)**: Arquitecto revisor que analiza el código desde GitHub

## Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLAUDE CODE   │◄──►│  COORDINATION   │◄──►│    CHATGPT      │
│  (Implementer)  │    │     LAYER       │    │   (Reviewer)    │
│                 │    │                 │    │                 │
│ • Local changes │    │ • Consensus     │    │ • Code review   │
│ • File edits    │    │ • Conflict      │    │ • Architecture  │
│ • Testing       │    │   resolution    │    │ • Best practice │
│ • Git ops       │    │ • Task queue    │    │ • Documentation │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Instalación y Configuración

### 1. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 2. Configurar Variables de Entorno

**¡NO necesitas Claude API Key!** El sistema usa Claude Code directamente.

Editar el archivo `.env`:

```bash
# APIs necesarias (solo OpenAI para ChatGPT)
OPENAI_API_KEY=tu_clave_openai
CLAUDE_ENDPOINT=local_integration         # Usa Claude Code directamente
CLAUDE_API_KEY=not_required               # No es necesario
GITHUB_TOKEN=tu_token_github              # Opcional, para revisión desde GitHub

# Configuración del sistema colaborativo
AI_COLLABORATION_ENABLED=true
AI_MIN_CONFIDENCE_THRESHOLD=0.7
AI_AUTO_IMPLEMENT_CONSENSUS=false
```

**Ventajas de la integración directa:**
- ✅ No necesitas pagar Claude API
- ✅ Usa Claude Code que ya tienes
- ✅ Comunicación más rápida y directa
- ✅ Mejor contexto del proyecto local

### 3. Verificar Configuración

```bash
# Prueba completa del sistema
python ai_team_test.py

# O usar el CLI principal
python ai_team_cli.py stats
```

## Uso del Sistema

### CLI Principal

El sistema se controla a través del CLI `ai_team_cli.py`:

```bash
python ai_team_cli.py --help
```

### Comandos Principales

#### 1. Crear Tarea Colaborativa

```bash
python ai_team_cli.py create-task \
  --title "Optimizar sistema de reportes" \
  --description "Mejorar performance de generación de reportes" \
  --priority high \
  --files "managers/report_manager.py,utils/exporters.py"
```

#### 2. Ejecutar Revisión Colaborativa

```bash
python ai_team_cli.py review-task task_20250812_143052
```

#### 3. Ciclo Completo de Desarrollo

```bash
python ai_team_cli.py dev-cycle \
  --dry-run \
  --min-confidence 0.8 \
  --focus "performance" "architecture" \
  --report
```

#### 4. Listar Tareas

```bash
python ai_team_cli.py list-tasks --status approved
```

#### 5. Demostración del Sistema

```bash
python ai_team_cli.py demo
```

## Flujo de Trabajo Colaborativo

### 1. Propuesta de Tarea
- Claude Code analiza el repositorio local
- Identifica oportunidades de mejora
- Crea tareas colaborativas

### 2. Revisión Cruzada
- **Claude**: Evalúa factibilidad técnica e implementación
- **ChatGPT**: Revisa arquitectura y mejores prácticas desde GitHub
- **Sistema**: Evalúa consenso entre ambas IAs

### 3. Tipos de Consenso
- **STRONG_CONSENSUS**: Ambas IAs aprueban con alta confianza
- **WEAK_CONSENSUS**: Ambas aprueban pero con menor confianza
- **CONFLICT**: Las IAs discrepan, requiere mediación
- **STRONG_REJECTION**: Ambas rechazan la propuesta

### 4. Implementación
- Solo procede si hay consenso suficiente
- Claude Code implementa los cambios localmente
- Se ejecutan tests automáticamente
- Commit y push automático si está habilitado

## Características Avanzadas

### Integración con GitHub
- ChatGPT accede al repositorio remoto para revisión
- Análisis de commits recientes y estructura del proyecto
- Contexto completo para decisiones arquitecturales

### Sistema de Consenso Inteligente
- Evaluación automática de confianza y riesgos
- Factores de riesgo identificados automáticamente
- Sugerencias combinadas de ambas IAs

### Métricas y Reportes
- Estadísticas de colaboración
- Reportes detallados de ciclos de desarrollo
- Logs de consenso y conflictos

## Configuración Avanzada

### Variables de Entorno Disponibles

```bash
# Sistema colaborativo
AI_COLLABORATION_ENABLED=true
AI_MIN_CONFIDENCE_THRESHOLD=0.7
AI_AUTO_IMPLEMENT_CONSENSUS=false
AI_CONFLICT_RESOLUTION_MODE=manual
AI_REVIEW_TIMEOUT_MINUTES=10
AI_MAX_CONCURRENT_TASKS=3

# Configuración Git
GIT_AUTHOR_NAME=tu_nombre
GIT_AUTHOR_EMAIL=tu_email
AUTO_PUSH=false
DRY_RUN=true
```

### Modos de Operación

1. **Modo Simulación** (`DRY_RUN=true`):
   - Analiza y propone cambios sin aplicarlos
   - Ideal para entender el comportamiento del sistema

2. **Modo Implementación** (`DRY_RUN=false`):
   - Aplica cambios reales al código
   - Requiere mayor confianza en el consenso

3. **Modo Automático** (`AI_AUTO_IMPLEMENT_CONSENSUS=true`):
   - Implementa automáticamente si hay consenso fuerte
   - Máxima velocidad de desarrollo

## Casos de Uso

### 1. Desarrollo Guiado por IA
```bash
# Ejecutar análisis completo y mejoras automáticas
python ai_team_cli.py dev-cycle --focus "performance" "architecture"
```

### 2. Revisión de Propuestas Específicas
```bash
# Crear propuesta específica y revisarla
python ai_team_cli.py create-task --title "Migrar a async/await"
python ai_team_cli.py review-task <task_id>
```

### 3. Auditoría de Calidad
```bash
# Revisar estado general del proyecto
python ai_team_cli.py dev-cycle --dry-run --min-confidence 0.9
```

## Solución de Problemas

### Error: "Claude endpoint no configurado"
```bash
# Configurar endpoint de Claude en .env
CLAUDE_ENDPOINT=https://api.anthropic.com/v1/messages
CLAUDE_API_KEY=tu_clave_claude
```

### Error: "GitHub token no válido"
```bash
# Configurar token de GitHub con permisos de repo
GITHUB_TOKEN=ghp_tu_token_personal
```

### Tests Fallan Después de Implementación
```bash
# Revisar logs y ajustar confianza mínima
python ai_team_cli.py dev-cycle --min-confidence 0.9
```

## Archivos del Sistema

```
ai_agent/
├── collaborative_ai_system.py      # Sistema principal de colaboración
├── enhanced_ai_devops.py           # DevOps mejorado con colaboración
├── github_integration.py           # Integración con GitHub
├── ai_coordination_cli.py          # CLI de coordinación
├── ai_helpers.py                   # Utilidades para APIs
├── config.py                       # Configuración del sistema
└── __init__.py                     # Exports principales

ai_team_cli.py                      # CLI principal del equipo AI
ai_sync/                           # Datos de sincronización
├── collaboration_tasks.json       # Base de datos de tareas
├── consensus_log.json             # Log de consensos
└── dev_notes.json                 # Notas de desarrollo
```

## Contribución

Para contribuir al sistema colaborativo:

1. Proponer mejoras usando el propio sistema:
```bash
python ai_team_cli.py create-task --title "Mejora propuesta"
```

2. Las IAs revisarán automáticamente la propuesta
3. Implementación colaborativa si hay consenso

## Licencia

Este sistema es parte de AlmacénPro v2.0 y está sujeto a las mismas condiciones de licencia del proyecto principal.

---

**🎯 Objetivo**: Crear un equipo de desarrollo AI que trabaje como programadores senior reales, con revisión cruzada, consenso inteligente y implementación colaborativa.