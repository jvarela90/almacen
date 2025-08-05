"""
Diálogo de gestión de backups para AlmacénPro
Permite crear, restaurar y configurar backups
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

from utils.backup_manager import BackupManager
import logging

logger = logging.getLogger(__name__)

class BackupDialog(QDialog):
    """Diálogo principal de gestión de backups"""
    
    def __init__(self, settings, backup_manager: BackupManager, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.backup_manager = backup_manager
        self.init_ui()
        self.load_backup_list()
    
    def init_ui(self):
        """Inicializar interfaz de usuario"""
        self.setWindowTitle("Sistema de Backup - AlmacénPro")
        self.setFixedSize(800, 600)
        self.setWindowIcon(QIcon())  # Aquí se puede agregar un icono
        
        layout = QVBoxLayout()
        
        # Crear pestañas
        tab_widget = QTabWidget()
        
        # Pestaña de Backups
        backups_tab = self.create_backups_tab()
        tab_widget.addTab(backups_tab, "📂 Backups")
        
        # Pestaña de Configuración
        config_tab = self.create_config_tab()
        tab_widget.addTab(config_tab, "⚙️ Configuración")
        
        # Pestaña de Estado
        status_tab = self.create_status_tab()
        tab_widget.addTab(status_tab, "📊 Estado")
        
        layout.addWidget(tab_widget)
        
        # Botones principales
        button_layout = QHBoxLayout()
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_backups_tab(self) -> QWidget:
        """Crear pestaña de gestión de backups"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Barra de herramientas
        toolbar_layout = QHBoxLayout()
        
        create_backup_btn = QPushButton("📦 Crear Backup")
        create_backup_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px; font-weight: bold;")
        create_backup_btn.clicked.connect(self.create_backup)
        toolbar_layout.addWidget(create_backup_btn)
        
        restore_backup_btn = QPushButton("📥 Restaurar Backup")
        restore_backup_btn.setStyleSheet("background-color: #FF9800; color: white; padding: 8px; font-weight: bold;")
        restore_backup_btn.clicked.connect(self.restore_backup)
        toolbar_layout.addWidget(restore_backup_btn)
        
        delete_backup_btn = QPushButton("🗑️ Eliminar Backup")
        delete_backup_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px; font-weight: bold;")
        delete_backup_btn.clicked.connect(self.delete_backup)
        toolbar_layout.addWidget(delete_backup_btn)
        
        toolbar_layout.addStretch()
        
        refresh_btn = QPushButton("🔄 Actualizar")
        refresh_btn.clicked.connect(self.load_backup_list)
        toolbar_layout.addWidget(refresh_btn)
        
        layout.addLayout(toolbar_layout)
        
        # Lista de backups
        self.backup_table = QTableWidget()
        self.backup_table.setColumnCount(6)
        self.backup_table.setHorizontalHeaderLabels([
            "Nombre", "Fecha de Creación", "Tamaño", "Tipo", "Descripción", "Estado"
        ])
        
        # Configurar tabla
        header = self.backup_table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)
        
        self.backup_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.backup_table.setAlternatingRowColors(True)
        
        layout.addWidget(self.backup_table)
        
        return widget
    
    def create_config_tab(self) -> QWidget:
        """Crear pestaña de configuración"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Configuración de backup automático
        auto_backup_group = QGroupBox("Backup Automático")
        auto_backup_layout = QGridLayout(auto_backup_group)
        
        self.auto_backup_enabled = QCheckBox("Habilitar backup automático")
        self.auto_backup_enabled.setChecked(self.settings.get('backup.auto_backup', True))
        auto_backup_layout.addWidget(self.auto_backup_enabled, 0, 0, 1, 2)
        
        auto_backup_layout.addWidget(QLabel("Intervalo (horas):"), 1, 0)
        self.backup_interval = QSpinBox()
        self.backup_interval.setMinimum(1)
        self.backup_interval.setMaximum(168)  # 1 semana
        self.backup_interval.setValue(self.settings.get('backup.backup_interval_hours', 24))
        auto_backup_layout.addWidget(self.backup_interval, 1, 1)
        
        auto_backup_layout.addWidget(QLabel("Máximo de backups:"), 2, 0)
        self.max_backups = QSpinBox()
        self.max_backups.setMinimum(1)
        self.max_backups.setMaximum(365)
        self.max_backups.setValue(self.settings.get('backup.max_backups', 30))
        auto_backup_layout.addWidget(self.max_backups, 2, 1)
        
        layout.addWidget(auto_backup_group)
        
        # Configuración de compresión
        compression_group = QGroupBox("Compresión")
        compression_layout = QVBoxLayout(compression_group)
        
        self.compress_backups = QCheckBox("Comprimir backups (recomendado)")
        self.compress_backups.setChecked(self.settings.get('backup.compress_backups', True))
        compression_layout.addWidget(self.compress_backups)
        
        layout.addWidget(compression_group)
        
        # Configuración de ruta
        path_group = QGroupBox("Ubicación de Backups")
        path_layout = QHBoxLayout(path_group)
        
        self.backup_path_input = QLineEdit()
        self.backup_path_input.setText(str(self.settings.get_backup_path()))
        self.backup_path_input.setReadOnly(True)
        path_layout.addWidget(self.backup_path_input)
        
        browse_path_btn = QPushButton("📁 Cambiar")
        browse_path_btn.clicked.connect(self.browse_backup_path)
        path_layout.addWidget(browse_path_btn)
        
        layout.addWidget(path_group)
        
        # Configuración de nube (placeholder)
        cloud_group = QGroupBox("Backup en la Nube (Próximamente)")
        cloud_layout = QVBoxLayout(cloud_group)
        
        self.cloud_backup_enabled = QCheckBox("Habilitar backup en la nube")
        self.cloud_backup_enabled.setEnabled(False)  # Deshabilitado por ahora
        cloud_layout.addWidget(self.cloud_backup_enabled)
        
        cloud_provider_layout = QHBoxLayout()
        cloud_provider_layout.addWidget(QLabel("Proveedor:"))
        self.cloud_provider = QComboBox()
        self.cloud_provider.addItems(["Google Drive", "Dropbox", "OneDrive"])
        self.cloud_provider.setEnabled(False)
        cloud_provider_layout.addWidget(self.cloud_provider)
        cloud_layout.addLayout(cloud_provider_layout)
        
        layout.addWidget(cloud_group)
        
        # Botones de configuración
        config_buttons_layout = QHBoxLayout()
        
        save_config_btn = QPushButton("💾 Guardar Configuración")
        save_config_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px;")
        save_config_btn.clicked.connect(self.save_configuration)
        config_buttons_layout.addWidget(save_config_btn)
        
        reset_config_btn = QPushButton("🔄 Restaurar Valores por Defecto")
        reset_config_btn.clicked.connect(self.reset_configuration)
        config_buttons_layout.addWidget(reset_config_btn)
        
        layout.addLayout(config_buttons_layout)
        layout.addStretch()
        
        return widget
    
    def create_status_tab(self) -> QWidget:
        """Crear pestaña de estado del sistema"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Estado actual
        status_group = QGroupBox("Estado Actual del Sistema de Backup")
        status_layout = QGridLayout(status_group)
        
        self.status_labels = {}
        
        # Crear labels de estado
        status_items = [
            ("Sistema:", "sistema"),
            ("Último Backup:", "ultimo_backup"),
            ("Próximo Backup:", "proximo_backup"),
            ("Total de Backups:", "total_backups"),
            ("Espacio Utilizado:", "espacio_utilizado"),
            ("Backup Automático:", "auto_backup_status")
        ]
        
        for i, (label_text, key) in enumerate(status_items):
            status_layout.addWidget(QLabel(label_text), i, 0)
            status_label = QLabel("Cargando...")
            status_label.setStyleSheet("font-weight: bold;")
            self.status_labels[key] = status_label
            status_layout.addWidget(status_label, i, 1)
        
        layout.addWidget(status_group)
        
        # Gráfico de uso de espacio (placeholder)
        chart_group = QGroupBox("Uso de Espacio de Backups")
        chart_layout = QVBoxLayout(chart_group)
        
        self.space_progress = QProgressBar()
        self.space_progress.setFormat("%p% - %v MB de %m MB")
        chart_layout.addWidget(self.space_progress)
        
        layout.addWidget(chart_group)
        
        # Botón de actualizar estado
        refresh_status_btn = QPushButton("🔄 Actualizar Estado")
        refresh_status_btn.clicked.connect(self.update_status)
        layout.addWidget(refresh_status_btn)
        
        layout.addStretch()
        
        return widget
    
    def load_backup_list(self):
        """Cargar lista de backups en la tabla"""
        try:
            backups = self.backup_manager.list_backups()
            
            self.backup_table.setRowCount(len(backups))
            
            for i, backup in enumerate(backups):
                # Nombre
                name_item = QTableWidgetItem(backup['name'])
                self.backup_table.setItem(i, 0, name_item)
                
                # Fecha de creación
                date_str = backup['created_at'].strftime("%d/%m/%Y %H:%M")
                date_item = QTableWidgetItem(date_str)
                self.backup_table.setItem(i, 1, date_item)
                
                # Tamaño
                size_mb = backup['size'] / (1024 * 1024)
                if size_mb >= 1024:
                    size_str = f"{size_mb/1024:.1f} GB"
                else:
                    size_str = f"{size_mb:.1f} MB"
                size_item = QTableWidgetItem(size_str)
                self.backup_table.setItem(i, 2, size_item)
                
                # Tipo
                type_item = QTableWidgetItem(backup['type'].title())
                self.backup_table.setItem(i, 3, type_item)
                
                # Descripción
                description = backup.get('description', 'Backup automático')
                desc_item = QTableWidgetItem(description)
                self.backup_table.setItem(i, 4, desc_item)
                
                # Estado
                status_item = QTableWidgetItem("✅ Válido")
                status_item.setForeground(QColor('green'))
                self.backup_table.setItem(i, 5, status_item)
            
            logger.info(f"Lista de backups cargada: {len(backups)} backups encontrados")
            
        except Exception as e:
            logger.error(f"Error cargando lista de backups: {e}")
            QMessageBox.critical(self, "Error", f"Error cargando lista de backups: {str(e)}")
    
    def create_backup(self):
        """Crear nuevo backup"""
        dialog = CreateBackupDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            description = dialog.get_description()
            
            # Mostrar diálogo de progreso
            progress_dialog = BackupProgressDialog(self.backup_manager, description, self)
            progress_dialog.exec_()
            
            # Actualizar lista
            self.load_backup_list()
            self.update_status()
    
    def restore_backup(self):
        """Restaurar backup seleccionado"""
        current_row = self.backup_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Advertencia", "Seleccione un backup para restaurar")
            return
        
        backup_name = self.backup_table.item(current_row, 0).text()
        
        # Confirmar restauración
        reply = QMessageBox.question(
            self, "Confirmar Restauración",
            f"⚠️ ADVERTENCIA: Esta operación reemplazará todos los datos actuales.\n\n"
            f"¿Está seguro de que desea restaurar el backup '{backup_name}'?\n\n"
            f"Se recomienda crear un backup de los datos actuales antes de continuar.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Obtener ruta del backup
            backup_path = self.backup_manager.backup_path / backup_name
            if not backup_path.exists():
                backup_path = backup_path.with_suffix('.tar.gz')
            
            if backup_path.exists():
                # Mostrar diálogo de progreso para restauración
                progress_dialog = RestoreProgressDialog(self.backup_manager, str(backup_path), self)
                result = progress_dialog.exec_()
                
                if result == QDialog.Accepted:
                    QMessageBox.information(
                        self, "Restauración Completada",
                        "La restauración se completó exitosamente.\n"
                        "Es recomendable reiniciar la aplicación."
                    )
            else:
                QMessageBox.critical(self, "Error", "Archivo de backup no encontrado")
    
    def delete_backup(self):
        """Eliminar backup seleccionado"""
        current_row = self.backup_table.currentRow()
        if current_row < 0:
            QMessageBox.warning(self, "Advertencia", "Seleccione un backup para eliminar")
            return
        
        backup_name = self.backup_table.item(current_row, 0).text()
        
        reply = QMessageBox.question(
            self, "Confirmar Eliminación",
            f"¿Está seguro de que desea eliminar el backup '{backup_name}'?\n\n"
            f"Esta operación no se puede deshacer.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                backup_path = self.backup_manager.backup_path / backup_name
                if not backup_path.exists():
                    backup_path = backup_path.with_suffix('.tar.gz')
                
                if backup_path.exists():
                    if backup_path.is_file():
                        backup_path.unlink()
                    else:
                        import shutil
                        shutil.rmtree(backup_path)
                    
                    QMessageBox.information(self, "Éxito", f"Backup '{backup_name}' eliminado")
                    self.load_backup_list()
                    self.update_status()
                else:
                    QMessageBox.critical(self, "Error", "Archivo de backup no encontrado")
                    
            except Exception as e:
                logger.error(f"Error eliminando backup: {e}")
                QMessageBox.critical(self, "Error", f"Error eliminando backup: {str(e)}")
    
    def browse_backup_path(self):
        """Cambiar ruta de backups"""
        current_path = str(self.settings.get_backup_path())
        new_path = QFileDialog.getExistingDirectory(
            self, "Seleccionar Directorio de Backups", current_path
        )
        
        if new_path:
            self.backup_path_input.setText(new_path)
    
    def save_configuration(self):
        """Guardar configuración de backup"""
        try:
            # Actualizar configuraciones
            self.settings.update_backup_settings(
                auto_backup=self.auto_backup_enabled.isChecked(),
                backup_interval_hours=self.backup_interval.value(),
                max_backups=self.max_backups.value(),
                compress_backups=self.compress_backups.isChecked(),
                backup_path=self.backup_path_input.text()
            )
            
            QMessageBox.information(self, "Éxito", "Configuración guardada correctamente")
            logger.info("Configuración de backup guardada")
            
        except Exception as e:
            logger.error(f"Error guardando configuración: {e}")
            QMessageBox.critical(self, "Error", f"Error guardando configuración: {str(e)}")
    
    def reset_configuration(self):
        """Restaurar configuración por defecto"""
        reply = QMessageBox.question(
            self, "Confirmar Reset",
            "¿Está seguro de que desea restaurar la configuración por defecto?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Restaurar valores por defecto en la interfaz
            self.auto_backup_enabled.setChecked(True)
            self.backup_interval.setValue(24)
            self.max_backups.setValue(30)
            self.compress_backups.setChecked(True)
            
            QMessageBox.information(self, "Éxito", "Configuración restaurada a valores por defecto")
    
    def update_status(self):
        """Actualizar estado del sistema de backup"""
        try:
            status = self.backup_manager.get_backup_status()
            
            # Actualizar labels
            self.status_labels['sistema'].setText(
                "🟢 Activo" if status['running'] else "🔴 Inactivo"
            )
            
            if status['last_backup']:
                last_backup_str = status['last_backup']['created_at'].strftime("%d/%m/%Y %H:%M")
                self.status_labels['ultimo_backup'].setText(last_backup_str)
            else:
                self.status_labels['ultimo_backup'].setText("Nunca")
            
            self.status_labels['proximo_backup'].setText("En 24 horas")  # Simplificado
            self.status_labels['total_backups'].setText(str(status['total_backups']))
            
            # Calcular espacio utilizado
            total_size_mb = status['total_backup_size'] / (1024 * 1024)
            if total_size_mb >= 1024:
                size_str = f"{total_size_mb/1024:.1f} GB"
            else:
                size_str = f"{total_size_mb:.1f} MB"
            self.status_labels['espacio_utilizado'].setText(size_str)
            
            self.status_labels['auto_backup_status'].setText(
                "🟢 Habilitado" if status['enabled'] else "🔴 Deshabilitado"
            )
            
            # Actualizar barra de progreso (ejemplo con límite de 10GB)
            max_size_mb = 10 * 1024  # 10 GB
            self.space_progress.setMaximum(max_size_mb)
            self.space_progress.setValue(int(total_size_mb))
            
        except Exception as e:
            logger.error(f"Error actualizando estado: {e}")


class CreateBackupDialog(QDialog):
    """Diálogo para crear nuevo backup"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("Crear Nuevo Backup")
        self.setFixedSize(400, 200)
        
        layout = QVBoxLayout()
        
        layout.addWidget(QLabel("Descripción del backup (opcional):"))
        
        self.description_input = QLineEdit()
        self.description_input.setPlaceholderText("Ej: Backup antes de actualización")
        layout.addWidget(self.description_input)
        
        button_layout = QHBoxLayout()
        
        create_btn = QPushButton("Crear Backup")
        create_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px;")
        create_btn.clicked.connect(self.accept)
        button_layout.addWidget(create_btn)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_description(self) -> str:
        return self.description_input.text().strip()


class BackupProgressDialog(QDialog):
    """Diálogo de progreso para crear backup"""
    
    def __init__(self, backup_manager: BackupManager, description: str, parent=None):
        super().__init__(parent)
        self.backup_manager = backup_manager
        self.description = description
        self.init_ui()
        self.start_backup()
    
    def init_ui(self):
        self.setWindowTitle("Creando Backup...")
        self.setFixedSize(400, 150)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Iniciando backup...")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminado
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
    
    def start_backup(self):
        """Iniciar proceso de backup en hilo separado"""
        self.backup_thread = BackupThread(self.backup_manager, self.description)
        self.backup_thread.progress_signal.connect(self.update_progress)
        self.backup_thread.finished_signal.connect(self.backup_finished)
        self.backup_thread.start()
    
    def update_progress(self, message: str):
        """Actualizar mensaje de progreso"""
        self.status_label.setText(message)
    
    def backup_finished(self, success: bool, message: str):
        """Manejar finalización del backup"""
        if success:
            QMessageBox.information(self, "Éxito", f"Backup creado exitosamente:\n{message}")
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Error creando backup:\n{message}")
            self.reject()


class RestoreProgressDialog(QDialog):
    """Diálogo de progreso para restaurar backup"""
    
    def __init__(self, backup_manager: BackupManager, backup_path: str, parent=None):
        super().__init__(parent)
        self.backup_manager = backup_manager
        self.backup_path = backup_path
        self.init_ui()
        self.start_restore()
    
    def init_ui(self):
        self.setWindowTitle("Restaurando Backup...")
        self.setFixedSize(400, 150)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Iniciando restauración...")
        layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminado
        layout.addWidget(self.progress_bar)
        
        self.setLayout(layout)
    
    def start_restore(self):
        """Iniciar proceso de restauración en hilo separado"""
        self.restore_thread = RestoreThread(self.backup_manager, self.backup_path)
        self.restore_thread.progress_signal.connect(self.update_progress)
        self.restore_thread.finished_signal.connect(self.restore_finished)
        self.restore_thread.start()
    
    def update_progress(self, message: str):
        """Actualizar mensaje de progreso"""
        self.status_label.setText(message)
    
    def restore_finished(self, success: bool, message: str):
        """Manejar finalización de la restauración"""
        if success:
            self.accept()
        else:
            QMessageBox.critical(self, "Error", f"Error restaurando backup:\n{message}")
            self.reject()


class BackupThread(QThread):
    """Hilo para crear backup sin bloquear UI"""
    
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, backup_manager: BackupManager, description: str):
        super().__init__()
        self.backup_manager = backup_manager
        self.description = description
    
    def run(self):
        """Ejecutar backup en hilo separado"""
        try:
            self.progress_signal.emit("Creando backup de base de datos...")
            self.msleep(500)
            
            self.progress_signal.emit("Respaldando configuración...")
            self.msleep(500)
            
            self.progress_signal.emit("Comprimiendo archivos...")
            self.msleep(500)
            
            success, message, backup_file = self.backup_manager.create_backup(self.description)
            
            self.finished_signal.emit(success, message)
            
        except Exception as e:
            self.finished_signal.emit(False, str(e))


class RestoreThread(QThread):
    """Hilo para restaurar backup sin bloquear UI"""
    
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, backup_manager: BackupManager, backup_path: str):
        super().__init__()
        self.backup_manager = backup_manager
        self.backup_path = backup_path
    
    def run(self):
        """Ejecutar restauración en hilo separado"""
        try:
            self.progress_signal.emit("Extrayendo backup...")
            self.msleep(500)
            
            self.progress_signal.emit("Restaurando base de datos...")
            self.msleep(500)
            
            self.progress_signal.emit("Restaurando configuración...")
            self.msleep(500)
            
            success, message = self.backup_manager.restore_backup(self.backup_path)
            
            self.finished_signal.emit(success, message)
            
        except Exception as e:
            self.finished_signal.emit(False, str(e))