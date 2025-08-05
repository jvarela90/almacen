# 🏪 AlmacénPro v2.0 - Sistema ERP/POS Completo

## 🚀 **Nueva Arquitectura Modular**

AlmacénPro ha sido completamente refactorizado con una **arquitectura modular profesional**, separando funcionalidades en módulos independientes para mejor mantenimiento, escalabilidad y desarrollo colaborativo.

## ✨ **Nuevas Funcionalidades - Fase 1**

### 💾 **Sistema de Backup Automático** ⭐ **NUEVO**
- **Backup automático programable** (cada 1-168 horas)
- **Compresión de archivos** para ahorrar espacio
- **Limpieza automática** de backups antiguos
- **Restauración completa** desde interfaz gráfica
- **Verificación de integridad** de backups
- **Metadatos detallados** de cada backup
- **Configuración avanzada** desde la UI

### 📊 **Dashboard Ejecutivo** ⭐ **PRÓXIMAMENTE**
### 🔔 **Sistema de Notificaciones** ⭐ **PRÓXIMAMENTE**

---

## 📁 **Estructura del Proyecto**

```
almacen_pro/
├── main.py                    # 🚀 Punto de entrada principal
├── requirements.txt           # 📦 Dependencias
├── README.md                  # 📖 Esta documentación
├── config/
│   ├── __init__.py
│   └── settings.py           # ⚙️ Configuraciones globales
├── database/
│   ├── __init__.py
│   ├── manager.py            # 🗄️ Gestor de base de datos
│   └── models.py             # 📋 Definiciones de tablas
├── managers/
│   ├── __init__.py
│   ├── user_manager.py       # 👤 Gestión de usuarios
│   ├── product_manager.py    # 📦 Gestión de productos
│   ├── sales_manager.py      # 💰 Gestión de ventas
│   ├── purchase_manager.py   # 🛍️ Gestión de compras
│   ├── provider_manager.py   # 👥 Gestión de proveedores
│   └── report_manager.py     # 📊 Gestión de reportes
├── ui/
│   ├── __init__.py
│   ├── main_window.py        # 🖥️ Ventana principal
│   ├── dialogs/
│   │   ├── __init__.py
│   │   ├── login_dialog.py   # 🔐 Diálogo de login
│   │   ├── backup_dialog.py  # 💾 Gestión de backups
│   │   └── ...               # Otros diálogos
│   └── widgets/
│       ├── __init__.py
│       ├── sales_widget.py   # 🛒 Widget de ventas
│       ├── dashboard_widget.py # 📈 Dashboard ejecutivo
│       └── ...               # Otros widgets
└── utils/
    ├── __init__.py
    ├── backup_manager.py     # 💾 Sistema de backup
    ├── notifications.py     # 🔔 Notificaciones
    └── helpers.py            # 🛠️ Funciones auxiliares
```

---

## 🔧 **Instalación y Configuración**

### **1. Requisitos del Sistema**
- **Python 3.8+**
- **Windows 10/11, macOS, o Linux**
- **4GB RAM mínimo** (8GB recomendado)
- **500MB espacio libre** (más espacio para backups)

### **2. Instalación de Dependencias**

```bash
# Clonar o descargar el proyecto
cd almacen_pro

# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### **3. Primera Ejecución**

```bash
# Ejecutar la aplicación
python main.py

# Login por defecto:
Usuario: admin
Contraseña: admin123
```

### **4. Configuración Inicial**

Al ejecutar por primera vez, el sistema:
- ✅ Crea automáticamente la base de datos
- ✅ Configura directorios necesarios (`data/`, `backups/`, `logs/`, etc.)
- ✅ Genera archivo de configuración por defecto
- ✅ Inserta datos de prueba (usuario admin, categorías, etc.)

---

## 💾 **Sistema de Backup Automático**

### **Características Principales:**

#### **🔄 Backup Automático**
- **Programación flexible**: 1-168 horas
- **Ejecución silenciosa** en segundo plano
- **Inicio automático** al abrir la aplicación
- **Sin interrupciones** en el trabajo diario

#### **📦 Gestión Inteligente**
- **Compresión automática** (reduce tamaño 80-90%)
- **Limpieza automática** de backups antiguos
- **Máximo configurable** de backups (1-365)
- **Verificación de integridad** automática

#### **🔍 Control Total**
- **Lista completa** de todos los backups
- **Información detallada** (fecha, tamaño, tipo)
- **Restauración con un click**
- **Eliminación selectiva** de backups

### **Uso del Sistema de Backup:**

#### **Acceder al Sistema:**
1. Abrir AlmacénPro
2. Ir a menú `Herramientas` → `Sistema de Backup`
3. Se abre el diálogo completo de gestión

#### **Crear Backup Manual:**
1. En la pestaña "📂 Backups"
2. Click en "📦 Crear Backup"
3. Agregar descripción opcional
4. Confirmar creación

#### **Configurar Backup Automático:**
1. Pestaña "⚙️ Configuración"
2. Marcar "Habilitar backup automático"
3. Configurar intervalo (recomendado: 24 horas)
4. Configurar máximo de backups (recomendado: 30)
5. Click en "💾 Guardar Configuración"

#### **Restaurar un Backup:**
1. En la pestaña "📂 Backups"
2. Seleccionar backup de la lista
3. Click en "📥 Restaurar Backup"
4. **⚠️ CONFIRMAR** (reemplaza datos actuales)
5. Reiniciar aplicación después de restaurar

### **Ubicación de Backups:**
- **Por defecto**: `almacen_pro/backups/`
- **Configurable** desde la interfaz
- **Formato**: `almacen_backup_YYYYMMDD_HHMMSS.tar.gz`

### **Contenido de cada Backup:**
- ✅ **Base de datos completa** (productos, ventas, clientes, etc.)
- ✅ **Configuraciones** del sistema
- ✅ **Archivos adicionales** (imágenes, exports, etc.)
- ✅ **Metadatos** con información del backup

---

## 🔐 **Seguridad y Confiabilidad**

### **Integridad de Datos:**
- **Backup atómico** de base de datos (sin corrupción)
- **Verificación automática** de cada backup
- **Detección de errores** con notificaciones
- **Recuperación robusta** con validaciones

### **Protección contra Pérdidas:**
- **Backup automático** sin intervención humana  
- **Múltiples copias** de seguridad
- **Alertas** cuando fallan los backups
- **Restauración completa** en minutos

---

## ⚙️ **Configuraciones Avanzadas**

### **Archivo de Configuración: `config.json`**

```json
{
  "backup": {
    "enabled": true,
    "auto_backup": true,
    "backup_interval_hours": 24,
    "backup_path": "backups",
    "max_backups": 30,
    "compress_backups": true,
    "cloud_backup": {
      "enabled": false,
      "provider": "google_drive",
      "remote_folder": "AlmacenPro_Backups"
    }
  },
  "company": {
    "name": "Mi Almacén",
    "address": "Dirección de la empresa",
    "phone": "Teléfono",
    "cuit": "CUIT de la empresa"
  },
  "ui": {
    "theme": "light",
    "language": "es",
    "font_size": 9
  }
}
```

### **Personalización:**
- **Información de empresa** (nombre, dirección, CUIT)
- **Configuración de tickets** (impresora, formato)
- **Tema de interfaz** (claro/oscuro)
- **Idioma** y configuraciones regionales

---

## 🚀 **Migración desde Versión Monolítica**

### **Si tienes la versión anterior:**

1. **Hacer backup** de tu base de datos actual:
   ```bash
   # Copiar tu archivo de base de datos existente
   cp almacen_pro.db almacen_pro_backup.db
   ```

2. **Instalar nueva versión** según instrucciones arriba

3. **Migrar datos**:
   - La nueva versión detecta automáticamente bases de datos existentes
   - Se ejecuta migración automática si es necesaria
   - Se crea backup automático antes de migrar

4. **Verificar funcionamiento**:
   - Revisar que todos los datos están presentes
   - Configurar sistema de backup automático
   - Probar funcionalidades principales

---

## 🐛 **Solución de Problemas**

### **Problemas Comunes:**

#### **Error: "No se pueden importar módulos"**
```bash
# Verificar instalación de PyQt5
pip install PyQt5
pip install PyQt5-tools
```

#### **Error: "No se puede crear backup"**
- Verificar permisos de escritura en directorio `backups/`
- Verificar espacio libre en disco
- Revisar logs en `almacen_pro.log`

#### **Error: "Base de datos bloqueada"**
- Cerrar todas las instancias de AlmacénPro
- Esperar unos segundos y volver a abrir
- Si persiste, revisar logs

#### **Backup automático no funciona:**
1. Ir a `Sistema de Backup` → `Configuración`
2. Verificar que esté habilitado
3. Revisar intervalo configurado
4. Ver estado en pestaña "📊 Estado"

### **Archivos de Log:**
- **Principal**: `almacen_pro.log`
- **Backup específico**: en directorio `logs/`
- **Ubicación**: directorio raíz de la aplicación

---

## 📞 **Soporte y Contacto**

### **Documentación:**
- **Wiki completa**: [Próximamente]
- **Videos tutoriales**: [Próximamente]
- **FAQ**: Ver sección de problemas comunes arriba

### **Reportar Errores:**
1. Revisar logs en `almacen_pro.log`
2. Describir pasos para reproducir el error
3. Incluir información del sistema (Windows/macOS/Linux)
4. Adjuntar screenshot si es relevante

---

## 🗺️ **Roadmap - Próximas Funcionalidades**

### **✅ Fase 1 - Base Funcional (COMPLETADA)**
- ✅ Sistema básico de ventas y stock
- ✅ Gestión de compras y proveedores
- ✅ Reportes básicos
- ✅ **Sistema de backup automático**

### **🔄 Fase 2 - Funcionalidades Avanzadas (EN DESARROLLO)**
- 🔄 **Dashboard ejecutivo** con KPIs y gráficos
- 🔄 **Sistema de notificaciones** 
- 🔄 **Multi-caja** con apertura/cierre
- 🔄 **Módulos especializados** (fiambrería, carnicería)

### **📅 Fase 3 - Características Enterprise (PLANIFICADO)**
- 📅 **Producción propia** con recetas
- 📅 **Integración con balanzas** y hardware
- 📅 **Sincronización** entre sucursales
- 📅 **Facturación electrónica** (AFIP)

### **🚀 Fase 4 - Escalabilidad (FUTURO)**
- 🚀 **Migración a PostgreSQL**
- 🚀 **API REST** para integraciones
- 🚀 **App móvil** para inventario
- 🚀 **Backup en la nube**

---

## 📄 **Licencia y Términos**

**AlmacénPro v2.0** - Sistema ERP/POS Profesional
- **Versión actual**: 2.0 (Arquitectura Modular)
- **Última actualización**: Julio 2025
- **Desarrollado en**: Python + PyQt5
- **Licencia**: [Definir según sea necesario]

---

## ⭐ **¿Te gusta AlmacénPro?**

Si el sistema te resulta útil:
- 🌟 **Compártelo** con otros comerciantes
- 💡 **Sugiere mejoras** y nuevas funcionalidades  
- 🐛 **Reporta errores** para mejorar la calidad
- 📝 **Contribuye** con documentación o código

**¡Gracias por usar AlmacénPro!** 🎉#   a l m a c e n  
 