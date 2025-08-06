"""
Diálogos de la interfaz de usuario
"""

from .login_dialog import LoginDialog
from .login_dialog import LoginSplashScreen
from .backup_dialog import BackupDialog
from .backup_dialog import BackupWorkerThread
from .add_product_dialog import AddProductDialog
from .add_product_dialog import QuickAddProductDialog
from .add_provider_dialog import AddProviderDialog
from .add_provider_dialog import QuickAddProviderDialog

__all__ = [
    'LoginDialog',
    'LoginSplashScreen',
    'BackupDialog',
    'BackupWorkerThread',
    'AddProductDialog',
    'QuickAddProductDialog',
    'AddProviderDialog',
    'QuickAddProviderDialog'
]