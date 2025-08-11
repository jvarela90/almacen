"""
Gestor de Estilos - AlmacénPro v2.0 MVC
Centraliza todos los estilos CSS de la aplicación
"""

import os
import logging
from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import QFile, QTextStream
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class StyleManager:
    """Gestor centralizado de estilos CSS"""
    
    # Estilos base del sistema
    BASE_STYLE = """
    /* === ESTILOS GENERALES === */
    QWidget {
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 12px;
        color: #2c3e50;
    }
    
    /* === BOTONES === */
    QPushButton {
        background-color: #3498db;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 10px 16px;
        font-weight: bold;
        min-width: 80px;
        font-size: 13px;
    }
    
    QPushButton:hover {
        background-color: #2980b9;
    }
    
    QPushButton:pressed {
        background-color: #21618c;
    }
    
    QPushButton:disabled {
        background-color: #bdc3c7;
        color: #7f8c8d;
    }
    
    /* Botones especiales */
    QPushButton#btnSuccess, QPushButton[class="success"] {
        background-color: #27ae60;
    }
    
    QPushButton#btnSuccess:hover, QPushButton[class="success"]:hover {
        background-color: #229954;
    }
    
    QPushButton#btnDanger, QPushButton[class="danger"] {
        background-color: #e74c3c;
    }
    
    QPushButton#btnDanger:hover, QPushButton[class="danger"]:hover {
        background-color: #c0392b;
    }
    
    QPushButton#btnWarning, QPushButton[class="warning"] {
        background-color: #f39c12;
    }
    
    QPushButton#btnWarning:hover, QPushButton[class="warning"]:hover {
        background-color: #d35400;
    }
    
    /* === CAMPOS DE ENTRADA === */
    QLineEdit, QTextEdit, QPlainTextEdit {
        border: 2px solid #ddd;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 14px;
        background-color: white;
    }
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border-color: #3498db;
        outline: none;
    }
    
    QLineEdit:disabled, QTextEdit:disabled, QPlainTextEdit:disabled {
        background-color: #f8f9fa;
        color: #6c757d;
        border-color: #e9ecef;
    }
    
    /* === SPINBOXES Y COMBOBOXES === */
    QSpinBox, QDoubleSpinBox, QComboBox {
        border: 2px solid #ddd;
        border-radius: 6px;
        padding: 8px 12px;
        font-size: 14px;
        background-color: white;
        min-height: 20px;
    }
    
    QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
        border-color: #3498db;
    }
    
    QComboBox::drop-down {
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid #ddd;
        border-radius: 3px;
        background-color: #f8f9fa;
    }
    
    QComboBox::down-arrow {
        image: url(:/icons/arrow-down.png);
        width: 12px;
        height: 12px;
    }
    
    /* === TABLAS === */
    QTableWidget {
        border: 1px solid #dee2e6;
        border-radius: 8px;
        gridline-color: #f1f3f4;
        alternate-background-color: #f8f9fa;
        selection-background-color: #3498db;
        background-color: white;
    }
    
    QTableWidget::item {
        padding: 12px 8px;
        border-bottom: 1px solid #f1f3f4;
    }
    
    QTableWidget::item:selected {
        background-color: #3498db;
        color: white;
    }
    
    QTableWidget::item:hover {
        background-color: #ebf3fd;
    }
    
    QHeaderView::section {
        background-color: #f8f9fa;
        padding: 12px 8px;
        border: none;
        border-right: 1px solid #dee2e6;
        border-bottom: 2px solid #dee2e6;
        font-weight: bold;
        color: #495057;
    }
    
    QHeaderView::section:hover {
        background-color: #e9ecef;
    }
    
    /* === GROUPBOXES === */
    QGroupBox {
        font-weight: bold;
        font-size: 14px;
        border: 2px solid #dee2e6;
        border-radius: 8px;
        margin: 8px 0px;
        padding-top: 16px;
        color: #495057;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 8px 0 8px;
        background-color: white;
        color: #2c3e50;
    }
    
    /* === TABS === */
    QTabWidget::pane {
        border: 1px solid #dee2e6;
        border-radius: 6px;
        background-color: white;
        margin-top: -1px;
    }
    
    QTabBar::tab {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        padding: 10px 16px;
        margin-right: 2px;
        border-top-left-radius: 6px;
        border-top-right-radius: 6px;
    }
    
    QTabBar::tab:selected {
        background-color: white;
        border-bottom-color: white;
    }
    
    QTabBar::tab:hover:!selected {
        background-color: #e9ecef;
    }
    
    /* === LABELS === */
    QLabel {
        color: #2c3e50;
    }
    
    QLabel#lblTitle, QLabel[class="title"] {
        font-size: 18px;
        font-weight: bold;
        color: #2c3e50;
        margin: 10px 0px;
    }
    
    QLabel#lblSubtitle, QLabel[class="subtitle"] {
        font-size: 14px;
        font-weight: bold;
        color: #495057;
        margin: 5px 0px;
    }
    
    QLabel#lblError, QLabel[class="error"] {
        color: #e74c3c;
        font-weight: bold;
    }
    
    QLabel#lblSuccess, QLabel[class="success"] {
        color: #27ae60;
        font-weight: bold;
    }
    
    QLabel#lblWarning, QLabel[class="warning"] {
        color: #f39c12;
        font-weight: bold;
    }
    
    /* === PROGRESS BARS === */
    QProgressBar {
        border: 1px solid #dee2e6;
        border-radius: 6px;
        text-align: center;
        background-color: #f8f9fa;
        height: 20px;
    }
    
    QProgressBar::chunk {
        background-color: #3498db;
        border-radius: 5px;
        margin: 1px;
    }
    
    /* === SCROLLBARS === */
    QScrollBar:vertical {
        background-color: #f8f9fa;
        width: 12px;
        border-radius: 6px;
        margin: 0px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #ced4da;
        border-radius: 6px;
        min-height: 20px;
        margin: 2px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #adb5bd;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }
    
    QScrollBar:horizontal {
        background-color: #f8f9fa;
        height: 12px;
        border-radius: 6px;
        margin: 0px;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #ced4da;
        border-radius: 6px;
        min-width: 20px;
        margin: 2px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #adb5bd;
    }
    
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }
    
    /* === CHECKBOXES Y RADIOBUTTONS === */
    QCheckBox, QRadioButton {
        font-size: 13px;
        color: #2c3e50;
        spacing: 8px;
    }
    
    QCheckBox::indicator, QRadioButton::indicator {
        width: 18px;
        height: 18px;
    }
    
    QCheckBox::indicator:unchecked {
        border: 2px solid #ced4da;
        border-radius: 3px;
        background-color: white;
    }
    
    QCheckBox::indicator:checked {
        border: 2px solid #3498db;
        border-radius: 3px;
        background-color: #3498db;
        image: url(:/icons/check.png);
    }
    
    QRadioButton::indicator:unchecked {
        border: 2px solid #ced4da;
        border-radius: 9px;
        background-color: white;
    }
    
    QRadioButton::indicator:checked {
        border: 2px solid #3498db;
        border-radius: 9px;
        background-color: #3498db;
    }
    
    /* === TOOLTIPS === */
    QToolTip {
        background-color: #2c3e50;
        color: white;
        border: none;
        padding: 8px;
        border-radius: 4px;
        font-size: 12px;
    }
    
    /* === STATUS BAR === */
    QStatusBar {
        background-color: #f8f9fa;
        border-top: 1px solid #dee2e6;
        color: #495057;
    }
    
    QStatusBar::item {
        border: none;
    }
    
    /* === MENU BAR === */
    QMenuBar {
        background-color: #2c3e50;
        color: white;
        border: none;
        font-weight: bold;
    }
    
    QMenuBar::item {
        padding: 8px 12px;
        background-color: transparent;
    }
    
    QMenuBar::item:selected {
        background-color: #34495e;
    }
    
    QMenu {
        background-color: white;
        border: 1px solid #dee2e6;
        border-radius: 4px;
        color: #2c3e50;
    }
    
    QMenu::item {
        padding: 8px 16px;
    }
    
    QMenu::item:selected {
        background-color: #3498db;
        color: white;
    }
    
    /* === TOOLBAR === */
    QToolBar {
        background-color: #f8f9fa;
        border: none;
        spacing: 4px;
    }
    
    QToolButton {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 4px;
        padding: 8px;
        margin: 2px;
    }
    
    QToolButton:hover {
        background-color: #e9ecef;
        border-color: #ced4da;
    }
    
    QToolButton:pressed {
        background-color: #dee2e6;
    }
    
    /* === SPLITTERS === */
    QSplitter::handle {
        background-color: #dee2e6;
        border: 1px solid #ced4da;
    }
    
    QSplitter::handle:horizontal {
        width: 6px;
        margin-left: 2px;
        margin-right: 2px;
    }
    
    QSplitter::handle:vertical {
        height: 6px;
        margin-top: 2px;
        margin-bottom: 2px;
    }
    """
    
    # Estilos específicos por módulo
    SALES_STYLE = """
    /* Estilos específicos para el módulo de ventas */
    #frameTotales {
        background-color: #f8f9fa;
        border: 2px solid #28a745;
        border-radius: 8px;
        padding: 10px;
    }
    
    #lblTotalValor {
        font-size: 24px;
        font-weight: bold;
        color: #28a745;
    }
    
    #btnProcesarVenta {
        background-color: #28a745;
        font-size: 16px;
        padding: 12px 20px;
        min-height: 40px;
    }
    
    #btnProcesarVenta:hover {
        background-color: #218838;
    }
    
    #tblCarrito {
        font-size: 13px;
    }
    
    #tblCarrito::item {
        padding: 10px 6px;
    }
    """
    
    INVENTORY_STYLE = """
    /* Estilos específicos para el módulo de inventario */
    #lblStockBajo {
        color: #dc3545;
        font-weight: bold;
    }
    
    #lblStockNormal {
        color: #28a745;
        font-weight: bold;
    }
    
    #lblStockMedio {
        color: #ffc107;
        font-weight: bold;
    }
    """
    
    CUSTOMER_STYLE = """
    /* Estilos específicos para el módulo de clientes */
    #frameClienteVIP {
        background-color: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 8px;
    }
    
    #frameClienteRegular {
        background-color: #d1ecf1;
        border: 2px solid #17a2b8;
        border-radius: 8px;
    }
    """
    
    @classmethod
    def apply_default_styles(cls, widget: QWidget):
        """Aplicar estilos por defecto a un widget"""
        try:
            widget.setStyleSheet(cls.BASE_STYLE)
            logger.debug(f"Estilos aplicados a {widget.__class__.__name__}")
        except Exception as e:
            logger.error(f"Error aplicando estilos: {e}")
    
    @classmethod
    def apply_module_styles(cls, widget: QWidget, module: str):
        """Aplicar estilos específicos de módulo"""
        try:
            base_style = cls.BASE_STYLE
            
            if module.lower() == 'sales':
                combined_style = base_style + cls.SALES_STYLE
            elif module.lower() == 'inventory':
                combined_style = base_style + cls.INVENTORY_STYLE
            elif module.lower() == 'customer':
                combined_style = base_style + cls.CUSTOMER_STYLE
            else:
                combined_style = base_style
            
            widget.setStyleSheet(combined_style)
            logger.debug(f"Estilos de módulo {module} aplicados a {widget.__class__.__name__}")
            
        except Exception as e:
            logger.error(f"Error aplicando estilos de módulo {module}: {e}")
    
    @classmethod
    def load_stylesheet_from_file(cls, file_path: str) -> Optional[str]:
        """Cargar stylesheet desde archivo"""
        try:
            if not os.path.exists(file_path):
                logger.warning(f"Archivo de estilos no encontrado: {file_path}")
                return None
            
            file = QFile(file_path)
            if file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(file)
                stylesheet = stream.readAll()
                file.close()
                return stylesheet
            else:
                logger.error(f"No se pudo abrir archivo de estilos: {file_path}")
                return None
                
        except Exception as e:
            logger.error(f"Error cargando stylesheet desde archivo: {e}")
            return None
    
    @classmethod
    def apply_theme(cls, app: QApplication, theme: str = "default"):
        """Aplicar tema a toda la aplicación"""
        try:
            if theme == "dark":
                cls._apply_dark_theme(app)
            elif theme == "high_contrast":
                cls._apply_high_contrast_theme(app)
            else:
                app.setStyleSheet(cls.BASE_STYLE)
            
            logger.info(f"Tema {theme} aplicado a la aplicación")
            
        except Exception as e:
            logger.error(f"Error aplicando tema {theme}: {e}")
    
    @classmethod
    def _apply_dark_theme(cls, app: QApplication):
        """Aplicar tema oscuro"""
        dark_style = cls.BASE_STYLE.replace("#2c3e50", "#ecf0f1")
        dark_style = dark_style.replace("#3498db", "#5dade2")
        dark_style = dark_style.replace("white", "#2c3e50")
        dark_style = dark_style.replace("#f8f9fa", "#34495e")
        dark_style = dark_style.replace("#dee2e6", "#4a5f7a")
        
        app.setStyleSheet(dark_style)
    
    @classmethod
    def _apply_high_contrast_theme(cls, app: QApplication):
        """Aplicar tema de alto contraste"""
        high_contrast_style = """
        QWidget {
            background-color: black;
            color: white;
            font-weight: bold;
        }
        
        QPushButton {
            background-color: white;
            color: black;
            border: 2px solid white;
            font-weight: bold;
        }
        
        QLineEdit, QTextEdit {
            background-color: white;
            color: black;
            border: 2px solid yellow;
        }
        
        QTableWidget {
            background-color: black;
            color: white;
            gridline-color: white;
        }
        
        QTableWidget::item:selected {
            background-color: yellow;
            color: black;
        }
        """
        
        app.setStyleSheet(high_contrast_style)
    
    @classmethod
    def get_color_palette(cls) -> Dict[str, str]:
        """Obtener paleta de colores del sistema"""
        return {
            'primary': '#3498db',
            'secondary': '#95a5a6',
            'success': '#27ae60',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'info': '#17a2b8',
            'light': '#f8f9fa',
            'dark': '#2c3e50',
            'white': '#ffffff',
            'gray': '#6c757d'
        }
    
    @classmethod
    def create_gradient_style(cls, start_color: str, end_color: str, direction: str = "vertical") -> str:
        """Crear estilo con degradado"""
        direction_map = {
            "vertical": "0, 0, 0, 1",
            "horizontal": "0, 0, 1, 0",
            "diagonal": "0, 0, 1, 1"
        }
        
        direction_coords = direction_map.get(direction, "0, 0, 0, 1")
        
        return f"""
        background: qlineargradient(x1:{direction_coords}, 
                                  stop:0 {start_color}, 
                                  stop:1 {end_color});
        """