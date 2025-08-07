#!/usr/bin/env python3
"""
Script de Análisis Completo de Base de Datos - AlmacénPro
Mapea toda la estructura, relaciones y datos existentes
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

def find_all_databases():
    """Encontrar todas las bases de datos SQLite en el proyecto"""
    databases = []
    
    # Rutas posibles
    possible_paths = [
        "almacen_pro.db",
        "almacen.db", 
        "database.db",
        "data/almacen_pro.db",
        "almacen/data/almacen_pro.db",
        "almacen/almacen_pro.db"
    ]
    
    # Buscar en directorio actual y subdirectorios
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.endswith(".db"):
                db_path = Path(root) / file
                if db_path.exists():
                    databases.append(str(db_path))
    
    # Agregar rutas específicas que pueden no estar en el walk
    for path in possible_paths:
        if Path(path).exists() and str(Path(path)) not in databases:
            databases.append(str(Path(path)))
    
    return databases

def get_table_info(cursor, table_name):
    """Obtener información completa de una tabla"""
    info = {
        'columns': [],
        'indexes': [],
        'foreign_keys': [],
        'triggers': [],
        'row_count': 0,
        'sample_data': []
    }
    
    try:
        # Información de columnas
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        
        for col in columns:
            col_info = {
                'name': col[1],
                'type': col[2],
                'not_null': bool(col[3]),
                'default_value': col[4],
                'primary_key': bool(col[5])
            }
            info['columns'].append(col_info)
        
        # Foreign Keys
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fks = cursor.fetchall()
        for fk in fks:
            fk_info = {
                'column': fk[3],
                'references_table': fk[2],
                'references_column': fk[4],
                'on_update': fk[5],
                'on_delete': fk[6]
            }
            info['foreign_keys'].append(fk_info)
        
        # Índices
        cursor.execute(f"PRAGMA index_list({table_name})")
        indexes = cursor.fetchall()
        for idx in indexes:
            cursor.execute(f"PRAGMA index_info({idx[1]})")
            idx_cols = cursor.fetchall()
            idx_info = {
                'name': idx[1],
                'unique': bool(idx[2]),
                'columns': [col[2] for col in idx_cols]
            }
            info['indexes'].append(idx_info)
        
        # Contar registros
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        info['row_count'] = cursor.fetchone()[0]
        
        # Datos de muestra (primeros 3 registros)
        if info['row_count'] > 0:
            column_names = [col['name'] for col in info['columns']]
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
            sample_rows = cursor.fetchall()
            
            for row in sample_rows:
                row_dict = dict(zip(column_names, row))
                info['sample_data'].append(row_dict)
    
    except Exception as e:
        info['error'] = str(e)
    
    return info

def analyze_database(db_path):
    """Analizar completamente una base de datos"""
    analysis = {
        'path': db_path,
        'size_mb': 0,
        'tables': {},
        'table_count': 0,
        'total_records': 0,
        'relationships': [],
        'error': None
    }
    
    try:
        # Tamaño del archivo
        if Path(db_path).exists():
            analysis['size_mb'] = round(Path(db_path).stat().st_size / (1024*1024), 2)
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Obtener todas las tablas
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        analysis['table_count'] = len(tables)
        
        # Analizar cada tabla
        for table in tables:
            print(f"   Analizando tabla: {table}")
            table_info = get_table_info(cursor, table)
            analysis['tables'][table] = table_info
            analysis['total_records'] += table_info['row_count']
        
        # Mapear relaciones
        for table_name, table_info in analysis['tables'].items():
            for fk in table_info['foreign_keys']:
                relationship = {
                    'from_table': table_name,
                    'from_column': fk['column'],
                    'to_table': fk['references_table'],
                    'to_column': fk['references_column']
                }
                analysis['relationships'].append(relationship)
        
        conn.close()
        
    except Exception as e:
        analysis['error'] = str(e)
    
    return analysis

def generate_report(analyses):
    """Generar reporte completo en markdown"""
    
    report = f"""# 🗄️ Análisis Completo de Bases de Datos - AlmacénPro
**Generado:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---

## 📊 Resumen Ejecutivo

"""
    
    # Resumen de todas las bases de datos
    total_dbs = len(analyses)
    total_tables = sum(a['table_count'] for a in analyses)
    total_records = sum(a['total_records'] for a in analyses)
    total_size = sum(a['size_mb'] for a in analyses)
    
    report += f"""
**Bases de datos encontradas:** {total_dbs}  
**Total de tablas:** {total_tables}  
**Total de registros:** {total_records:,}  
**Tamaño total:** {total_size:.2f} MB  

"""
    
    # Análisis por base de datos
    for i, analysis in enumerate(analyses, 1):
        report += f"""
---

## 🗂️ Base de Datos #{i}: `{Path(analysis['path']).name}`

**📍 Ruta:** `{analysis['path']}`  
**📏 Tamaño:** {analysis['size_mb']:.2f} MB  
**📋 Tablas:** {analysis['table_count']}  
**📊 Registros totales:** {analysis['total_records']:,}  

"""
        
        if analysis['error']:
            report += f"❌ **Error:** {analysis['error']}\n\n"
            continue
        
        # Tabla de resumen de tablas
        report += """### 📋 Resumen de Tablas

| Tabla | Registros | Columnas | Foreign Keys | Índices |
|-------|-----------|----------|--------------|---------|
"""
        
        for table_name, table_info in analysis['tables'].items():
            fk_count = len(table_info['foreign_keys'])
            idx_count = len(table_info['indexes'])
            col_count = len(table_info['columns'])
            
            report += f"| `{table_name}` | {table_info['row_count']:,} | {col_count} | {fk_count} | {idx_count} |\n"
        
        # Detalle de cada tabla
        report += "\n### 🔍 Detalle de Tablas\n\n"
        
        for table_name, table_info in analysis['tables'].items():
            report += f"""
#### 📊 Tabla: `{table_name}`

**Registros:** {table_info['row_count']:,}

**Columnas:**
"""
            
            for col in table_info['columns']:
                pk_mark = " 🔑" if col['primary_key'] else ""
                nn_mark = " ⚠️" if col['not_null'] else ""
                default_info = f" (default: {col['default_value']})" if col['default_value'] else ""
                
                report += f"- `{col['name']}` - {col['type']}{pk_mark}{nn_mark}{default_info}\n"
            
            # Foreign Keys
            if table_info['foreign_keys']:
                report += "\n**Relaciones (Foreign Keys):**\n"
                for fk in table_info['foreign_keys']:
                    report += f"- `{fk['column']}` → `{fk['references_table']}.{fk['references_column']}`\n"
            
            # Índices
            if table_info['indexes']:
                report += "\n**Índices:**\n"
                for idx in table_info['indexes']:
                    unique_mark = " (UNIQUE)" if idx['unique'] else ""
                    cols = ", ".join(idx['columns'])
                    report += f"- `{idx['name']}`: {cols}{unique_mark}\n"
            
            # Datos de muestra
            if table_info['sample_data']:
                report += "\n**Datos de muestra:**\n```json\n"
                for i, sample in enumerate(table_info['sample_data'][:2], 1):
                    # Limitar valores largos
                    clean_sample = {}
                    for key, value in sample.items():
                        if isinstance(value, str) and len(value) > 50:
                            clean_sample[key] = value[:47] + "..."
                        else:
                            clean_sample[key] = value
                    report += f"# Registro {i}\n{clean_sample}\n\n"
                report += "```\n"
            
            report += "\n---\n"
        
        # Mapa de relaciones
        if analysis['relationships']:
            report += "\n### 🔗 Mapa de Relaciones\n\n"
            report += "```mermaid\nerDiagram\n"
            
            # Agregar tablas
            for table_name in analysis['tables'].keys():
                report += f"    {table_name.upper()}\n"
            
            # Agregar relaciones
            for rel in analysis['relationships']:
                from_table = rel['from_table'].upper()
                to_table = rel['to_table'].upper()
                report += f"    {from_table} ||--|| {to_table} : {rel['from_column']}\n"
            
            report += "```\n\n"
            
            report += "**Relaciones detalladas:**\n"
            for rel in analysis['relationships']:
                report += f"- `{rel['from_table']}.{rel['from_column']}` → `{rel['to_table']}.{rel['to_column']}`\n"
    
    # Comparación si hay múltiples bases de datos
    if len(analyses) > 1:
        report += f"""

---

## ⚖️ Comparación de Bases de Datos

| Base de Datos | Tablas | Registros | Tamaño |
|---------------|--------|-----------|--------|
"""
        for analysis in analyses:
            name = Path(analysis['path']).name
            report += f"| `{name}` | {analysis['table_count']} | {analysis['total_records']:,} | {analysis['size_mb']:.2f} MB |\n"
        
        # Tablas comunes y diferentes
        if len(analyses) == 2:
            tables1 = set(analyses[0]['tables'].keys())
            tables2 = set(analyses[1]['tables'].keys())
            
            common_tables = tables1 & tables2
            only_db1 = tables1 - tables2
            only_db2 = tables2 - tables1
            
            if common_tables:
                report += f"\n**Tablas comunes:** {', '.join(sorted(common_tables))}\n"
            if only_db1:
                report += f"\n**Solo en DB1:** {', '.join(sorted(only_db1))}\n"
            if only_db2:
                report += f"\n**Solo en DB2:** {', '.join(sorted(only_db2))}\n"
    
    # Recomendaciones
    report += f"""

---

## 💡 Recomendaciones

"""
    
    for analysis in analyses:
        name = Path(analysis['path']).name
        
        # Tablas vacías
        empty_tables = [name for name, info in analysis['tables'].items() if info['row_count'] == 0]
        if empty_tables:
            report += f"\n**{name} - Tablas vacías:** {', '.join(empty_tables)}\n"
        
        # Tablas sin relaciones
        tables_with_fk = set()
        for rel in analysis['relationships']:
            tables_with_fk.add(rel['from_table'])
        
        isolated_tables = [name for name in analysis['tables'].keys() if name not in tables_with_fk]
        if isolated_tables:
            report += f"\n**{name} - Tablas sin relaciones FK:** {', '.join(isolated_tables)}\n"
    
    report += f"""

---

## 🎯 Próximos Pasos

1. **Elegir base de datos principal** - Verificar cuál usa realmente la aplicación
2. **Crear script de datos** adaptado al esquema real encontrado
3. **Sincronizar esquemas** si hay diferencias entre bases de datos
4. **Poblar tablas vacías** con datos de prueba realistas

---

*Reporte generado automáticamente por el Analizador de BD de AlmacénPro*
"""
    
    return report

def main():
    """Función principal"""
    print("🔍 ANALIZADOR COMPLETO DE BASE DE DATOS - ALMACÉNPRO")
    print("=" * 70)
    
    # Encontrar todas las bases de datos
    print("\n📂 Buscando bases de datos...")
    databases = find_all_databases()
    
    if not databases:
        print("❌ No se encontraron bases de datos SQLite")
        return False
    
    print(f"✅ Encontradas {len(databases)} base(s) de datos:")
    for i, db in enumerate(databases, 1):
        print(f"   {i}. {db}")
    
    # Analizar cada base de datos
    analyses = []
    
    for i, db_path in enumerate(databases, 1):
        print(f"\n🔍 Analizando base de datos {i}/{len(databases)}: {Path(db_path).name}")
        print("-" * 50)
        
        analysis = analyze_database(db_path)
        analyses.append(analysis)
        
        if analysis['error']:
            print(f"❌ Error: {analysis['error']}")
        else:
            print(f"✅ Análisis completado:")
            print(f"   📊 {analysis['table_count']} tablas")
            print(f"   📈 {analysis['total_records']:,} registros totales")
            print(f"   💾 {analysis['size_mb']:.2f} MB")
    
    # Generar reporte
    print(f"\n📄 Generando reporte completo...")
    report = generate_report(analyses)
    
    # Guardar reporte
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"database_analysis_{timestamp}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Reporte guardado: {report_file}")
    
    # Mostrar resumen en consola
    print(f"\n" + "=" * 70)
    print("📊 RESUMEN EJECUTIVO")
    print("=" * 70)
    
    for analysis in analyses:
        name = Path(analysis['path']).name
        print(f"🗂️  {name}:")
        print(f"   📍 {analysis['path']}")
        print(f"   📊 {analysis['table_count']} tablas, {analysis['total_records']:,} registros")
        print(f"   💾 {analysis['size_mb']:.2f} MB")
        print()
    
    print(f"📄 Reporte detallado guardado en: {report_file}")
    print(f"💡 Comparte este archivo para crear el script de datos perfecto")
    
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Análisis completado exitosamente")
    else:
        print("\n❌ Error durante el análisis")
