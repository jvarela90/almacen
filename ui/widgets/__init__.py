"""
Widgets personalizados de la interfaz
"""

from .dashboard_widget import DashboardWidget
from .purchases_widget import PurchasesWidget
from .reports_widget import ReportsWidget,ReportResultDialog
from .sales_widget import SalesWidget, PaymentDialog
from .stock_widget import StockWidget,ProductDialog,StockAdjustmentDialog

# Placeholder para futuros widgets
__all__ = [
    'DashboardWidget',
    'PurchasesWidget',
    'ReportsWidget',
    'ReportResultDialog',
    'SalesWidget',
    'PaymentDialog',
    'StockWidget',
    'ProductDialog',
    'StockAdjustmentDialog'
        
]