/**
 * Portal de Clientes - AlmacénPro v2.0
 * JavaScript personalizado para funcionalidades del portal
 */

// Configuración global
const PortalConfig = {
    API_BASE_URL: '/api',
    REFRESH_INTERVAL: 300000, // 5 minutos
    TOAST_DURATION: 5000,
    VERSION: '2.0'
};

// Clase principal del Portal
class CustomerPortal {
    constructor() {
        this.init();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    init() {
        console.log('🌐 Portal de Clientes iniciado - v' + PortalConfig.VERSION);
        
        // Inicializar tooltips de Bootstrap
        this.initTooltips();
        
        // Inicializar popovers de Bootstrap
        this.initPopovers();
        
        // Configurar validaciones globales
        this.setupGlobalValidation();
        
        // Configurar manejo de errores
        this.setupErrorHandling();
        
        // Marcar visita
        this.markVisit();
    }

    initTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function(tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    initPopovers() {
        const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
        popoverTriggerList.map(function(popoverTriggerEl) {
            return new bootstrap.Popover(popoverTriggerEl);
        });
    }

    setupEventListeners() {
        // Manejo de formularios
        document.addEventListener('submit', this.handleFormSubmit.bind(this));
        
        // Manejo de botones de carga
        document.addEventListener('click', this.handleButtonClick.bind(this));
        
        // Auto-guardar formularios
        document.addEventListener('input', this.handleFormInput.bind(this));
        
        // Manejo de navegación
        window.addEventListener('beforeunload', this.handleBeforeUnload.bind(this));
        
        // Manejo de errores de red
        window.addEventListener('online', this.handleOnline.bind(this));
        window.addEventListener('offline', this.handleOffline.bind(this));
    }

    setupGlobalValidation() {
        // Validación de emails
        document.addEventListener('input', function(e) {
            if (e.target.type === 'email') {
                const isValid = CustomerPortal.validateEmail(e.target.value);
                e.target.classList.toggle('is-invalid', !isValid && e.target.value.length > 0);
                e.target.classList.toggle('is-valid', isValid && e.target.value.length > 0);
            }
        });

        // Validación de teléfonos
        document.addEventListener('input', function(e) {
            if (e.target.type === 'tel') {
                const isValid = CustomerPortal.validatePhone(e.target.value);
                e.target.classList.toggle('is-invalid', !isValid && e.target.value.length > 0);
                e.target.classList.toggle('is-valid', isValid && e.target.value.length > 0);
            }
        });
    }

    setupErrorHandling() {
        window.addEventListener('error', function(e) {
            console.error('Error del portal:', e);
            CustomerPortal.showToast('Ha ocurrido un error inesperado', 'error');
        });

        window.addEventListener('unhandledrejection', function(e) {
            console.error('Promise rechazado:', e);
            CustomerPortal.showToast('Error en la comunicación con el servidor', 'error');
        });
    }

    handleFormSubmit(e) {
        const form = e.target;
        if (!form.tagName || form.tagName !== 'FORM') return;

        // Verificar si el formulario tiene validaciones
        if (form.checkValidity && !form.checkValidity()) {
            e.preventDefault();
            CustomerPortal.showToast('Complete todos los campos requeridos', 'warning');
            return;
        }

        // Mostrar estado de carga en botón de submit
        const submitBtn = form.querySelector('button[type="submit"]');
        if (submitBtn) {
            this.showButtonLoading(submitBtn);
        }
    }

    handleButtonClick(e) {
        const btn = e.target.closest('button');
        if (!btn) return;

        // Manejo especial para botones con data-action
        const action = btn.dataset.action;
        if (action) {
            this.handleButtonAction(btn, action);
        }

        // Prevenir doble clic
        if (btn.dataset.loading === 'true') {
            e.preventDefault();
            return;
        }
    }

    handleButtonAction(btn, action) {
        switch (action) {
            case 'copy':
                this.handleCopyAction(btn);
                break;
            case 'share':
                this.handleShareAction(btn);
                break;
            case 'export':
                this.handleExportAction(btn);
                break;
            case 'refresh':
                this.handleRefreshAction(btn);
                break;
        }
    }

    handleCopyAction(btn) {
        const target = btn.dataset.target;
        const element = document.querySelector(target);
        if (element) {
            element.select();
            document.execCommand('copy');
            CustomerPortal.showToast('Copiado al portapapeles', 'success');
        }
    }

    handleShareAction(btn) {
        const url = btn.dataset.url || window.location.href;
        const title = btn.dataset.title || document.title;
        
        if (navigator.share) {
            navigator.share({ title, url })
                .catch(console.error);
        } else {
            // Fallback para navegadores sin Web Share API
            this.fallbackShare(url, title);
        }
    }

    fallbackShare(url, title) {
        const shareModal = this.createShareModal(url, title);
        document.body.appendChild(shareModal);
        const modal = new bootstrap.Modal(shareModal);
        modal.show();
        
        shareModal.addEventListener('hidden.bs.modal', function() {
            shareModal.remove();
        });
    }

    createShareModal(url, title) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Compartir</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label">URL:</label>
                            <div class="input-group">
                                <input type="text" class="form-control" value="${url}" readonly id="shareUrl">
                                <button class="btn btn-outline-secondary" type="button" onclick="CustomerPortal.copyToClipboard('shareUrl')">
                                    <i class="bi bi-copy"></i>
                                </button>
                            </div>
                        </div>
                        <div class="d-flex justify-content-center gap-2">
                            <button class="btn btn-primary" onclick="window.open('mailto:?subject=${encodeURIComponent(title)}&body=${encodeURIComponent(url)}')">
                                <i class="bi bi-envelope"></i> Email
                            </button>
                            <button class="btn btn-success" onclick="window.open('https://wa.me/?text=${encodeURIComponent(url)}')">
                                <i class="bi bi-whatsapp"></i> WhatsApp
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        return modal;
    }

    handleExportAction(btn) {
        const format = btn.dataset.format || 'csv';
        const data = this.getTableData(btn.dataset.table);
        
        switch (format) {
            case 'csv':
                this.exportToCSV(data, btn.dataset.filename || 'export.csv');
                break;
            case 'json':
                this.exportToJSON(data, btn.dataset.filename || 'export.json');
                break;
        }
    }

    handleRefreshAction(btn) {
        this.showButtonLoading(btn);
        window.location.reload();
    }

    handleFormInput(e) {
        // Auto-guardar datos en localStorage para formularios largos
        const form = e.target.form;
        if (form && form.dataset.autosave) {
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            localStorage.setItem(`form_${form.id}`, JSON.stringify(data));
        }
    }

    handleBeforeUnload(e) {
        // Advertir sobre cambios no guardados
        const formsWithChanges = document.querySelectorAll('form[data-changed="true"]');
        if (formsWithChanges.length > 0) {
            e.preventDefault();
            e.returnValue = 'Tiene cambios sin guardar. ¿Está seguro que desea salir?';
        }
    }

    handleOnline() {
        CustomerPortal.showToast('Conexión restaurada', 'success');
        // Reenviar datos pendientes si los hay
        this.resendPendingData();
    }

    handleOffline() {
        CustomerPortal.showToast('Sin conexión a internet', 'warning');
    }

    showButtonLoading(btn) {
        const originalContent = btn.innerHTML;
        btn.dataset.originalContent = originalContent;
        btn.dataset.loading = 'true';
        btn.disabled = true;
        
        btn.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            Cargando...
        `;

        // Restaurar después de 10 segundos como fallback
        setTimeout(() => {
            this.hideButtonLoading(btn);
        }, 10000);
    }

    hideButtonLoading(btn) {
        if (btn.dataset.originalContent) {
            btn.innerHTML = btn.dataset.originalContent;
            btn.disabled = false;
            btn.dataset.loading = 'false';
            delete btn.dataset.originalContent;
        }
    }

    getTableData(tableSelector) {
        const table = document.querySelector(tableSelector);
        if (!table) return [];

        const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
        const rows = Array.from(table.querySelectorAll('tbody tr')).map(tr => {
            const cells = Array.from(tr.querySelectorAll('td')).map(td => td.textContent.trim());
            return Object.fromEntries(headers.map((header, index) => [header, cells[index] || '']));
        });

        return rows;
    }

    exportToCSV(data, filename) {
        if (!data.length) return;

        const headers = Object.keys(data[0]);
        const csv = [
            headers.join(','),
            ...data.map(row => headers.map(header => `"${row[header]}"`).join(','))
        ].join('\n');

        this.downloadFile(csv, filename, 'text/csv');
        CustomerPortal.showToast('Archivo CSV descargado', 'success');
    }

    exportToJSON(data, filename) {
        const json = JSON.stringify(data, null, 2);
        this.downloadFile(json, filename, 'application/json');
        CustomerPortal.showToast('Archivo JSON descargado', 'success');
    }

    downloadFile(content, filename, mimeType) {
        const blob = new Blob([content], { type: mimeType });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
    }

    startAutoRefresh() {
        // Auto-refrescar estadísticas cada 5 minutos
        setInterval(() => {
            this.refreshStats();
        }, PortalConfig.REFRESH_INTERVAL);
    }

    async refreshStats() {
        try {
            const response = await fetch(PortalConfig.API_BASE_URL + '/stats');
            const data = await response.json();
            this.updateStatsDisplay(data);
        } catch (error) {
            console.warn('No se pudieron actualizar las estadísticas:', error);
        }
    }

    updateStatsDisplay(data) {
        // Actualizar elementos con datos estadísticos
        Object.keys(data).forEach(key => {
            const element = document.querySelector(`[data-stat="${key}"]`);
            if (element) {
                element.textContent = data[key];
            }
        });
    }

    resendPendingData() {
        // Implementar lógica para reenviar datos almacenados localmente
        const pendingData = localStorage.getItem('pending_data');
        if (pendingData) {
            try {
                const data = JSON.parse(pendingData);
                // Procesar y enviar datos pendientes
                console.log('Reenviando datos pendientes:', data);
                localStorage.removeItem('pending_data');
            } catch (error) {
                console.error('Error reenviando datos:', error);
            }
        }
    }

    markVisit() {
        localStorage.setItem('portal_last_visit', new Date().toISOString());
        
        // Incrementar contador de visitas
        const visits = parseInt(localStorage.getItem('portal_visits') || '0') + 1;
        localStorage.setItem('portal_visits', visits.toString());
    }

    // Métodos estáticos utilitarios
    static validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    static validatePhone(phone) {
        const cleaned = phone.replace(/\D/g, '');
        return cleaned.length >= 10;
    }

    static formatCurrency(amount) {
        return new Intl.NumberFormat('es-AR', {
            style: 'currency',
            currency: 'ARS'
        }).format(amount);
    }

    static formatDate(date) {
        return new Intl.DateTimeFormat('es-AR').format(new Date(date));
    }

    static formatDateTime(date) {
        return new Intl.DateTimeFormat('es-AR', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit'
        }).format(new Date(date));
    }

    static copyToClipboard(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.select();
            element.setSelectionRange(0, 99999);
            document.execCommand('copy');
            
            CustomerPortal.showToast('Copiado al portapapeles', 'success');
            return true;
        }
        return false;
    }

    static showToast(message, type = 'info', duration = PortalConfig.TOAST_DURATION) {
        const toastContainer = CustomerPortal.getOrCreateToastContainer();
        const toast = CustomerPortal.createToast(message, type);
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast, {
            delay: duration
        });
        
        bsToast.show();
        
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }

    static getOrCreateToastContainer() {
        let container = document.querySelector('.toast-container');
        if (!container) {
            container = document.createElement('div');
            container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '9999';
            document.body.appendChild(container);
        }
        return container;
    }

    static createToast(message, type) {
        const iconMap = {
            success: 'bi-check-circle-fill',
            error: 'bi-exclamation-triangle-fill',
            warning: 'bi-exclamation-circle-fill',
            info: 'bi-info-circle-fill'
        };

        const bgMap = {
            success: 'bg-success',
            error: 'bg-danger',
            warning: 'bg-warning',
            info: 'bg-info'
        };

        const toast = document.createElement('div');
        toast.className = 'toast';
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="toast-header ${bgMap[type]} text-white">
                <i class="bi ${iconMap[type]} me-2"></i>
                <strong class="me-auto">Portal</strong>
                <small>ahora</small>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">
                ${message}
            </div>
        `;
        
        return toast;
    }

    static showModal(title, content, buttons = []) {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">${title}</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        ${content}
                    </div>
                    <div class="modal-footer">
                        ${buttons.map(btn => `<button type="button" class="btn ${btn.class || 'btn-secondary'}" ${btn.dismiss ? 'data-bs-dismiss="modal"' : ''} onclick="${btn.onclick || ''}">${btn.text}</button>`).join('')}
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
        
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
        
        modal.addEventListener('hidden.bs.modal', function() {
            modal.remove();
        });
        
        return bsModal;
    }

    static confirm(message, onConfirm, onCancel = null) {
        const buttons = [
            {
                text: 'Cancelar',
                class: 'btn-secondary',
                dismiss: true,
                onclick: onCancel ? `(${onCancel})()` : ''
            },
            {
                text: 'Confirmar',
                class: 'btn-primary',
                dismiss: true,
                onclick: `(${onConfirm})()`
            }
        ];

        return CustomerPortal.showModal('Confirmación', message, buttons);
    }

    static loading(show = true, target = document.body) {
        if (show) {
            const overlay = document.createElement('div');
            overlay.id = 'portal-loading';
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(255, 255, 255, 0.8);
                display: flex;
                justify-content: center;
                align-items: center;
                z-index: 9999;
            `;
            overlay.innerHTML = `
                <div class="text-center">
                    <div class="spinner-border text-primary" role="status" style="width: 3rem; height: 3rem;">
                        <span class="visually-hidden">Cargando...</span>
                    </div>
                    <div class="mt-3">
                        <strong>Cargando...</strong>
                    </div>
                </div>
            `;
            target.appendChild(overlay);
        } else {
            const overlay = document.getElementById('portal-loading');
            if (overlay) {
                overlay.remove();
            }
        }
    }
}

// Funciones utilitarias globales
window.PortalUtils = {
    formatCurrency: CustomerPortal.formatCurrency,
    formatDate: CustomerPortal.formatDate,
    formatDateTime: CustomerPortal.formatDateTime,
    validateEmail: CustomerPortal.validateEmail,
    validatePhone: CustomerPortal.validatePhone,
    showToast: CustomerPortal.showToast,
    showModal: CustomerPortal.showModal,
    confirm: CustomerPortal.confirm,
    loading: CustomerPortal.loading,
    copyToClipboard: CustomerPortal.copyToClipboard
};

// Inicializar portal cuando el DOM esté listo
document.addEventListener('DOMContentLoaded', function() {
    window.customerPortal = new CustomerPortal();
    
    // Configurar atajos de teclado
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + K para búsqueda rápida
        if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
            e.preventDefault();
            const searchInput = document.querySelector('input[type="search"]');
            if (searchInput) {
                searchInput.focus();
            }
        }
        
        // Escape para cerrar modales
        if (e.key === 'Escape') {
            const openModal = document.querySelector('.modal.show');
            if (openModal) {
                const modal = bootstrap.Modal.getInstance(openModal);
                if (modal) modal.hide();
            }
        }
    });
    
    console.log('✅ Portal de Clientes inicializado correctamente');
});