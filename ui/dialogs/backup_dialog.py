"""
Diálogo de Gestión de Backup para AlmacénPro
Interfaz completa para crear, restaurar y gestionar backups del sistema
"""

import logging
from datetime import datetime
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

logger = logging.getLogger(__name__)

class BackupDialog(QDialog):
    """Diálogo principal para gestión de backups"""
    
    def __init__(self, backup_manager, parent=None):
        super().__init__(parent)
        self.backup_manager = backup_manager
        
        self.init_ui()
        self.setup_styles()
        self.load_backup_list()
        self.load_statistics()
        
        # Thread para operaciones de backup
        self.backup_thread = None
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        self.setWindowTitle("Gestión de Backups - AlmacénPro")
        self.setFixedSize(900, 700)
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.WindowCloseButtonHint)
        
        # Layout principal
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_widget = self.create_header()
        main_layout.addWidget(header_widget)
        
        # Tabs principales
        tab_widget = QTabWidget()
        
        # Tab de gestión de backups
        management_tab = self.create_management_tab()
        tab_widget.addTab(management_tab, "🗂️ Gestión de Backups")
        
        # Tab de configuración
        config_tab = self.create_configuration_tab()
        tab_widget.addTab(config_tab, "⚙️ Configuración")
        
        # Tab de estadísticas
        stats_tab = self.create_statistics_tab()
        tab_widget.addTab(stats_tab, "📊 Estadísticas")
        
        main_layout.addWidget(tab_widget)
        
        # Botones de acción
        buttons_layout = self.create_buttons()
        main_layout.addLayout(buttons_layout)
    
    def create_header(self) -> QWidget:
        """Crear header del diálogo"""
        header = QWidget()
        header.setObjectName("backup_header")
        layout = QHBoxLayout(header)
        
        # Título
        title_layout = QVBoxLayout()
        title = QLabel("💾 Gestión de Backups")
        title.setObjectName("header_title")
        title_layout.addWidget(title)
        
        subtitle = QLabel("Crear, restaurar y gestionar copias de seguridad del sistema")
        subtitle.setObjectName("header_subtitle")
        title_layout.addWidget(subtitle)
        
        layout.addLayout(title_layout)
        
        layout.addStretch()
        
        # Estado del backup automático
        self.auto_backup_status = QLabel()
        self.auto_backup_status.setObjectName("auto_backup_status")
        layout.addWidget(self.auto_backup_status)
        
        return header
    
    def create_management_tab(self) -> QWidget:
        """Crear tab de gestión de backups"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Panel de acciones rápidas
        actions_group = QGroupBox("Acciones Rápidas")
        actions_layout = QHBoxLayout(actions_group)
        
        # Crear backup manual
        create_backup_btn = QPushButton("📝 Crear Backup Manual")
        create_backup_btn.setMinimumHeight(40)
        create_backup_btn.clicked.connect(self.create_manual_backup)
        actions_layout.addWidget(create_backup_btn)
        
        # Refrescar lista
        refresh_btn = QPushButton("🔄 Actualizar Lista")
        refresh_btn.setMinimumHeight(40)
        refresh_btn.clicked.connect(self.refresh_backup_list)
        actions_layout.addWidget(refresh_btn)
        
        # Abrir carpeta de backups
        open_folder_btn = QPushButton("📁 Abrir Carpeta")
        open_folder_btn.setMinimumHeight(40)
        open_folder_btn.clicked.connect(self.open_backup_folder)
        actions_layout.addWidget(open_folder_btn)
        
        layout.addWidget(actions_group)
        
        # Lista de backups
        backups_group = QGroupBox("Backups Disponibles")
        backups_layout = QVBoxLayout(backups_group)
        
        # Tabla de backups
        self.backups_table = QTableWidget()
        self.backups_table.setColumnCount(6)
        self.backups_table.setHorizontalHeaderLabels([
            "Nombre", "Tipo", "Fecha", "Tamaño", "Estado", "Acciones"
        ])
        
        # Configurar tabla
        self.backups_table.setAlternatingRowColors(True)
        self.backups_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.backups_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.backups_table.horizontalHeader().setStretchLastSection(True)
        
        # Ajustar columnas
        header = self.backups_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)
        
        backups_layout.addWidget(self.backups_table)
        layout.addWidget(backups_group)
        
        return tab
    
    def create_configuration_tab(self) -> QWidget:
        """Crear tab de configuración"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Configuración de backup automático
        auto_backup_group = QGroupBox("Backup Automático")
        auto_backup_layout = QVBoxLayout(auto_backup_group)
        
        # Habilitar backup automático
        self.auto_backup_enabled = QCheckBox("Habilitar backup automático")
        self.auto_backup_enabled.setChecked(self.backup_manager.config.get("auto_backup_enabled", True))
        auto_backup_layout.addWidget(self.auto_backup_enabled)
        
        # Intervalo de backup
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Intervalo:"))
        
        self.backup_interval = QSpinBox()
        self.backup_interval.setRange(1, 168)  # 1 hora a 1 semana
        self.backup_interval.setValue(self.backup_manager.config.get("backup_interval_hours", 24))
        self.backup_interval.setSuffix(" horas")
        interval_layout.addWidget(self.backup_interval)
        
        interval_layout.addStretch()
        auto_backup_layout.addLayout(interval_layout)
        
        layout.addWidget(auto_backup_group)
        
        # Configuración de retención
        retention_group = QGroupBox("Retención de Backups")
        retention_layout = QVBoxLayout(retention_group)
        
        # Días a mantener
        retention_layout.addWidget(QLabel("Mantener backups automáticos por:"))
        
        days_layout = QHBoxLayout()
        self.keep_backups_days = QSpinBox()
        self.keep_backups_days.setRange(1, 365)
        self.keep_backups_days.setValue(self.backup_manager.config.get("keep_backups_days", 30))
        self.keep_backups_days.setSuffix(" días")
        days_layout.addWidget(self.keep_backups_days)
        days_layout.addStretch()
        
        retention_layout.addLayout(days_layout)
        layout.addWidget(retention_group)
        
        # Configuración de compresión
        compression_group = QGroupBox("Opciones de Backup")
        compression_layout = QVBoxLayout(compression_group)
        
        self.compress_backups = QCheckBox("Comprimir backups (recomendado)")
        self.compress_backups.setChecked(self.backup_manager.config.get("compress_backups", True))
        compression_layout.addWidget(self.compress_backups)
        
        self.include_images = QCheckBox("Incluir imágenes de productos")
        self.include_images.setChecked(self.backup_manager.config.get("include_images", True))
        compression_layout.addWidget(self.include_images)
        
        self.include_logs = QCheckBox("Incluir archivos de log")
        self.include_logs.setChecked(self.backup_manager.config.get("include_logs", False))
        compression_layout.addWidget(self.include_logs)
        
        layout.addWidget(compression_group)
        
        # Botones de configuración
        config_buttons_layout = QHBoxLayout()
        config_buttons_layout.addStretch()
        
        save_config_btn = QPushButton("💾 Guardar Configuración")
        save_config_btn.clicked.connect(self.save_configuration)
        config_buttons_layout.addWidget(save_config_btn)
        
        reset_config_btn = QPushButton("🔄 Restaurar Valores")
        reset_config_btn.clicked.connect(self.reset_configuration)
        config_buttons_layout.addWidget(reset_config_btn)
        
        layout.addLayout(config_buttons_layout)
        layout.addStretch()
        
        return tab
    
    def create_statistics_tab(self) -> QWidget:
        """Crear tab de estadísticas"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(15)
        
        # Panel de estadísticas generales
        self.stats_widget = QWidget()
        self.stats_layout = QVBoxLayout(self.stats_widget)
        
        layout.addWidget(self.stats_widget)
        layout.addStretch()
        
        return tab
    
    def create_buttons(self) -> QHBoxLayout:
        """Crear botones de acción del diálogo"""
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        # Botón cerrar
        close_btn = QPushButton("Cerrar")
        close_btn.setMinimumWidth(100)
        close_btn.clicked.connect(self.accept)
        buttons_layout.addWidget(close_btn)
        
        return buttons_layout
    
    def load_backup_list(self):
        """Cargar lista de backups en la tabla"""
        try:
            backups = self.backup_manager.get_backup_list()
            
            self.backups_table.setRowCount(len(backups))
            
            for row, backup in enumerate(backups):
                # Nombre
                name_item = QTableWidgetItem(backup["name"])
                self.backups_table.setItem(row, 0, name_item)
                
                # Tipo
                backup_type = "Manual" if backup["type"] == "manual" else "Automático"
                type_item = QTableWidgetItem(backup_type)
                if backup["type"] == "manual":
                    type_item.setIcon(self.style().standardIcon(QStyle.SP_FileDialogNewFolder))
                else:
                    type_item.setIcon(self.style().standardIcon(QStyle.SP_BrowserReload))
                self.backups_table.setItem(row, 1, type_item)
                
                # Fecha
                try:
                    created_date = datetime.fromisoformat(backup["created_at"])
                    date_str = created_date.strftime("%d/%m/%Y %H:%M")
                except:
                    date_str = "Fecha desconocida"
                
                date_item = QTableWidgetItem(date_str)
                self.backups_table.setItem(row, 2, date_item)
                
                # Tamaño
                size_mb = backup["size_bytes"] / (1024 * 1024)
                if size_mb < 1:
                    size_str = f"{backup['size_bytes'] / 1024:.1f} KB"
                else:
                    size_str = f"{size_mb:.1f} MB"
                
                size_item = QTableWidgetItem(size_str)
                self.backups_table.setItem(row, 3, size_item)
                
                # Estado
                verified = backup.get("verified")
                if verified is True:
                    status = "✅ Verificado"
                elif verified is False:
                    status = "❌ Error"
                else:
                    status = "❓ Sin verificar"
                
                status_item = QTableWidgetItem(status)
                self.backups_table.setItem(row, 4, status_item)
                
                # Botones de acción
                actions_widget = self.create_action_buttons(backup)
                self.backups_table.setCellWidget(row, 5, actions_widget)
            
            # Redimensionar filas
            self.backups_table.resizeRowsToContents()
            
        except Exception as e:
            logger.error(f"Error cargando lista de backups: {e}")
            QMessageBox.warning(self, "Error", f"Error cargando backups: {e}")
    
    def create_action_buttons(self, backup: dict) -> QWidget:
        """Crear botones de acción para cada backup"""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(5)
        
        # Botón restaurar
        restore_btn = QPushButton("📥")
        restore_btn.setToolTip("Restaurar backup")
        restore_btn.setMaximumWidth(30)
        restore_btn.clicked.connect(lambda: self.restore_backup(backup))
        layout.addWidget(restore_btn)
        
        # Botón eliminar (solo para backups manuales o muy antiguos)
        if backup["type"] == "manual" or self.is_old_backup(backup):
            delete_btn = QPushButton("🗑️")
            delete_btn.setToolTip("Eliminar backup")
            delete_btn.setMaximumWidth(30)
            delete_btn.clicked.connect(lambda: self.delete_backup(backup))
            layout.addWidget(delete_btn)
        
        return widget
    
    def is_old_backup(self, backup: dict) -> bool:
        """Verificar si un backup es antiguo"""
        try:
            created_date = datetime.fromisoformat(backup["created_at"])
            days_old = (datetime.now() - created_date).days
            return days_old > 7  # Considerar antiguo después de 7 días
        except:
            return False
    
    def load_statistics(self):
        """Cargar estadísticas de backups"""
        try:
            stats = self.backup_manager.get_backup_statistics()
            
            # Limpiar layout anterior
            for i in reversed(range(self.stats_layout.count())):
                self.stats_layout.itemAt(i).widget().setParent(None)
            
            # Estadísticas generales
            general_group = QGroupBox("Estadísticas Generales")
            general_layout = QGridLayout(general_group)
            
            stats_data = [
                ("Total de backups:", str(stats.get("total_backups", 0))),
                ("Backups manuales:", str(stats.get("manual_backups", 0))),
                ("Backups automáticos:", str(stats.get("automatic_backups", 0))),
                ("Tamaño total:", f"{stats.get('total_size_mb', 0):.1f} MB"),
                ("Backup automático:", "Habilitado" if stats.get("auto_backup_enabled") else "Deshabilitado"),
                ("Intervalo:", f"{stats.get('backup_interval_hours', 24)} horas")
            ]
            
            for row, (label, value) in enumerate(stats_data):
                label_widget = QLabel(label)
                label_widget.setStyleSheet("font-weight: bold;")
                value_widget = QLabel(value)
                
                general_layout.addWidget(label_widget, row, 0)
                general_layout.addWidget(value_widget, row, 1)
            
            self.stats_layout.addWidget(general_group)
            
            # Último backup
            last_backup = stats.get("last_backup")
            if last_backup:
                last_backup_group = QGroupBox("Último Backup")
                last_backup_layout = QVBoxLayout(last_backup_group)
                
                try:
                    last_date = datetime.fromisoformat(last_backup["created_at"])
                    date_str = last_date.strftime("%d/%m/%Y a las %H:%M")
                except:
                    date_str = "Fecha desconocida"
                
                last_backup_info = f"""
                <b>Nombre:</b> {last_backup['name']}<br>
                <b>Tipo:</b> {'Manual' if last_backup['type'] == 'manual' else 'Automático'}<br>
                <b>Fecha:</b> {date_str}<br>
                <b>Tamaño:</b> {last_backup['size_bytes'] / (1024*1024):.1f} MB
                """
                
                info_label = QLabel(last_backup_info)
                info_label.setWordWrap(True)
                last_backup_layout.addWidget(info_label)
                
                self.stats_layout.addWidget(last_backup_group)
            
            # Actualizar estado del backup automático
            if stats.get("auto_backup_enabled"):
                self.auto_backup_status.setText("🟢 Backup automático activo")
                self.auto_backup_status.setStyleSheet("color: #27ae60; font-weight: bold;")
            else:
                self.auto_backup_status.setText("🔴 Backup automático inactivo")
                self.auto_backup_status.setStyleSheet("color: #e74c3c; font-weight: bold;")
            
        except Exception as e:
            logger.error(f"Error cargando estadísticas: {e}")
    
    def create_manual_backup(self):
        """Crear backup manual"""
        try:
            # Pedir descripción opcional
            description, ok = QInputDialog.getText(
                self, 
                "Crear Backup Manual", 
                "Descripción del backup (opcional):",
                text="backup_manual"
            )
            
            if not ok:
                return
            
            # Crear backup en hilo separado
            self.backup_thread = BackupWorkerThread(
                self.backup_manager, 
                "manual", 
                description if description.strip() else None
            )
            
            self.backup_thread.backup_completed.connect(self.on_backup_completed)
            self.backup_thread.backup_failed.connect(self.on_backup_failed)
            
            # Mostrar progreso
            self.show_progress_dialog("Creando backup manual...")
            self.backup_thread.start()
            
        except Exception as e:
            logger.error(f"Error iniciando backup manual: {e}")
            QMessageBox.critical(self, "Error", f"Error creando backup: {e}")
    
    def restore_backup(self, backup: dict):
        """Restaurar backup seleccionado"""
        try:
            # Confirmar restauración
            reply = QMessageBox.question(
                self,
                "Confirmar Restauración",
                f"¿Está seguro que desea restaurar el backup '{backup['name']}'?\n\n"
                "ADVERTENCIA: Esta acción reemplazará todos los datos actuales del sistema.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Restaurar en hilo separado
            self.backup_thread = BackupWorkerThread(
                self.backup_manager,
                "restore",
                backup["path"]
            )
            
            self.backup_thread.backup_completed.connect(self.on_restore_completed)
            self.backup_thread.backup_failed.connect(self.on_restore_failed)
            
            # Mostrar progreso
            self.show_progress_dialog("Restaurando backup...")
            self.backup_thread.start()
            
        except Exception as e:
            logger.error(f"Error iniciando restauración: {e}")
            QMessageBox.critical(self, "Error", f"Error restaurando backup: {e}")
    
    def delete_backup(self, backup: dict):
        """Eliminar backup seleccionado"""
        try:
            # Confirmar eliminación
            reply = QMessageBox.question(
                self,
                "Confirmar Eliminación",
                f"¿Está seguro que desea eliminar el backup '{backup['name']}'?\n\n"
                "Esta acción no se puede deshacer.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Eliminar backup
            if self.backup_manager.delete_backup(backup["path"]):
                QMessageBox.information(self, "Éxito", "Backup eliminado exitosamente")
                self.refresh_backup_list()
            else:
                QMessageBox.warning(self, "Error", "No se pudo eliminar el backup")
                
        except Exception as e:
            logger.error(f"Error eliminando backup: {e}")
            QMessageBox.critical(self, "Error", f"Error eliminando backup: {e}")
    
    def show_progress_dialog(self, message: str):
        """Mostrar diálogo de progreso"""
        self.progress_dialog = QProgressDialog(message, "Cancelar", 0, 0, self)
        self.progress_dialog.setWindowTitle("Procesando...")
        self.progress_dialog.setWindowModality(Qt.WindowModal)
        self.progress_dialog.setMinimumDuration(0)
        self.progress_dialog.setValue(0)
        self.progress_dialog.show()
    
    def hide_progress_dialog(self):
        """Ocultar diálogo de progreso"""
        if hasattr(self, 'progress_dialog'):
            self.progress_dialog.close()
            delattr(self, 'progress_dialog')
    
    def on_backup_completed(self, backup_path: str):
        """Callback cuando backup se completa"""
        self.hide_progress_dialog()
        QMessageBox.information(self, "Éxito", f"Backup creado exitosamente:\n{backup_path}")
        self.refresh_backup_list()
    
    def on_backup_failed(self, error_message: str):
        """Callback cuando backup falla"""
        self.hide_progress_dialog()
        QMessageBox.critical(self, "Error", f"Error creando backup:\n{error_message}")
    
    def on_restore_completed(self, message: str):
        """Callback cuando restauración se completa"""
        self.hide_progress_dialog()
        QMessageBox.information(
            self, 
            "Restauración Completada", 
            "Backup restaurado exitosamente.\n\n"
            "Se recomienda reiniciar la aplicación para asegurar que todos los cambios se apliquen correctamente."
        )
    
    def on_restore_failed(self, error_message: str):
        """Callback cuando restauración falla"""
        self.hide_progress_dialog()
        QMessageBox.critical(self, "Error", f"Error restaurando backup:\n{error_message}")
    
    def refresh_backup_list(self):
        """Actualizar lista de backups"""
        self.load_backup_list()
        self.load_statistics()
    
    def open_backup_folder(self):
        """Abrir carpeta de backups en el explorador"""
        try:
            backup_path = Path(self.backup_manager.backup_directory)
            if backup_path.exists():
                import subprocess
                import sys
                
                if sys.platform == "win32":
                    subprocess.Popen(f'explorer "{backup_path}"')
                elif sys.platform == "darwin":
                    subprocess.Popen(["open", str(backup_path)])
                else:
                    subprocess.Popen(["xdg-open", str(backup_path)])
            else:
                QMessageBox.information(self, "Información", "La carpeta de backups no existe aún")
                
        except Exception as e:
            logger.error(f"Error abriendo carpeta de backups: {e}")
            QMessageBox.warning(self, "Error", f"No se pudo abrir la carpeta: {e}")
    
    def save_configuration(self):
        """Guardar configuración de backup"""
        try:
            new_config = {
                "auto_backup_enabled": self.auto_backup_enabled.isChecked(),
                "backup_interval_hours": self.backup_interval.value(),
                "keep_backups_days": self.keep_backups_days.value(),
                "compress_backups": self.compress_backups.isChecked(),
                "include_images": self.include_images.isChecked(),
                "include_logs": self.include_logs.isChecked()
            }
            
            self.backup_manager.update_config(new_config)
            QMessageBox.information(self, "Éxito", "Configuración guardada exitosamente")
            self.load_statistics()
            
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            QMessageBox.critical(self, "Error", f"Error guardando configuración: {e}")
    
    def reset_configuration(self):
        """Restaurar configuración por defecto"""
        try:
            # Restaurar valores en la interfaz
            self.auto_backup_enabled.setChecked(True)
            self.backup_interval.setValue(24)
            self.keep_backups_days.setValue(30)
            self.compress_backups.setChecked(True)
            self.include_images.setChecked(True)
            self.include_logs.setChecked(False)
            
        except Exception as e:
            logger.error(f"Error restaurando configuración: {e}")
    
    def setup_styles(self):
        """Configurar estilos CSS"""
        self.setStyleSheet("""
            #backup_header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #27ae60, stop:1 #2ecc71);
                border-radius: 10px;
                padding: 15px;
                margin-bottom: 10px;
            }
            
            #header_title {
                color: white;
                font-size: 20px;
                font-weight: bold;
            }
            
            #header_subtitle {
                color: #d5f4e6;
                font-size: 12px;
            }
            
            #auto_backup_status {
                font-size: 12px;
                padding: 5px 10px;
                border-radius: 5px;
                background-color: rgba(255, 255, 255, 0.2);
            }
            
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                margin-top: 8px;
                padding-top: 10px;
            }
            
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px 0 8px;
                color: #2c3e50;
            }
            
            QTableWidget {
                gridline-color: #ecf0f1;
                background-color: white;
                alternate-background-color: #f8f9fa;
                selection-background-color: #3498db;
                selection-color: white;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
            
            QHeaderView::section {
                background-color: #34495e;
                color: white;
                padding: 8px;
                border: none;
                font-weight: bold;
            }
            
            QPushButton {
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
        """)


class BackupWorkerThread(QThread):
    """Hilo worker para operaciones de backup"""
    
    backup_completed = pyqtSignal(str)
    backup_failed = pyqtSignal(str)
    
    def __init__(self, backup_manager, operation: str, parameter=None):
        super().__init__()
        self.backup_manager = backup_manager
        self.operation = operation
        self.parameter = parameter
    
    def run(self):
        """Ejecutar operación de backup"""
        try:
            if self.operation == "manual":
                backup_path = self.backup_manager.create_manual_backup(self.parameter)
                if backup_path:
                    self.backup_completed.emit(str(backup_path))
                else:
                    self.backup_failed.emit("Error desconocido creando backup")
                    
            elif self.operation == "restore":
                success = self.backup_manager.restore_backup(self.parameter)
                if success:
                    self.backup_completed.emit("Backup restaurado exitosamente")
                else:
                    self.backup_failed.emit("Error restaurando backup")
                    
        except Exception as e:
            self.backup_failed.emit(str(e))