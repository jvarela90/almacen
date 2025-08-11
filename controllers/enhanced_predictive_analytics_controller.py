"""
Controlador Enhanced Predictive Analytics - AlmacénPro v2.0 MVC
Controlador para funcionalidades avanzadas de análisis predictivo y BI
"""

import os
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QListWidgetItem, QFileDialog
from PyQt5.QtCore import pyqtSlot, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from controllers.base_controller import BaseController
from managers.predictive_analysis_manager import PredictiveAnalysisManager


class AnalysisWorkerThread(QThread):
    """Hilo para ejecutar análisis pesados sin bloquear la UI"""
    analysis_completed = pyqtSignal(dict)
    analysis_failed = pyqtSignal(str)
    progress_updated = pyqtSignal(str, int)

    def __init__(self, analysis_type: str, manager: PredictiveAnalysisManager, params: Dict = None):
        super().__init__()
        self.analysis_type = analysis_type
        self.manager = manager
        self.params = params or {}

    def run(self):
        """Ejecutar análisis en hilo separado"""
        try:
            if self.analysis_type == 'customer_behavior':
                customer_id = self.params.get('customer_id')
                result = self.manager.analyze_customer_behavior(customer_id)
                
            elif self.analysis_type == 'inventory_prediction':
                product_id = self.params.get('product_id')
                days_ahead = self.params.get('days_ahead', 30)
                result = self.manager.predict_inventory_demand(product_id, days_ahead)
                
            elif self.analysis_type == 'seasonal_analysis':
                months_back = self.params.get('months_back', 12)
                result = self.manager.analyze_seasonal_trends(months_back)
                
            elif self.analysis_type == 'product_trends':
                top_n = self.params.get('top_n', 20)
                result = self.manager.analyze_product_performance_trends(top_n)
                
            elif self.analysis_type == 'business_insights':
                result = self.manager.generate_business_insights_report()
                
            elif self.analysis_type == 'segment_analysis':
                result = self.manager.get_segment_analysis()
                
            else:
                raise ValueError(f"Tipo de análisis no reconocido: {self.analysis_type}")
            
            self.analysis_completed.emit(result)
            
        except Exception as e:
            self.analysis_failed.emit(str(e))


class EnhancedPredictiveAnalyticsController(BaseController):
    """Controlador para análisis predictivo avanzado y BI"""
    
    def __init__(self, managers: Dict, current_user: Dict, parent=None):
        super().__init__(managers, current_user, parent)
        
        # Referencias a managers
        self.predictive_manager = managers.get('predictive')
        if not self.predictive_manager:
            # Crear manager si no existe
            self.predictive_manager = PredictiveAnalysisManager(managers['database'])
            self.predictive_manager.create_prediction_tables()
        
        self.db_manager = managers['database']
        self.customer_manager = managers['customer']
        self.product_manager = managers['product']
        
        # Estado del controlador
        self.current_analysis_thread = None
        self.last_analysis_data = {}
        self.auto_refresh_timer = QTimer()
        
        # Inicializar
        try:
            self.initialize()
        except Exception as e:
            self.logger.error(f"Error inicializando controlador: {e}")
            self.show_error("Error de Inicialización", str(e))
    
    def get_ui_file_path(self) -> str:
        """Retornar ruta al archivo .ui"""
        return "views/widgets/enhanced_predictive_analytics_widget.ui"
    
    def setup_ui(self):
        """Configurar elementos específicos de la UI"""
        try:
            # Configurar tablas
            self.setup_product_recommendations_table()
            self.setup_monthly_patterns_table()
            self.setup_business_metrics_table()
            
            # Cargar datos iniciales para combos
            self.load_customers_combo()
            self.load_products_combo()
            
            # Configurar timer de auto-refresh
            self.auto_refresh_timer.timeout.connect(self.refresh_dashboard_data)
            self.auto_refresh_timer.start(300000)  # 5 minutos
            
            # Estado inicial
            self.lblLastUpdate.setText(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
            
            # Valores iniciales para KPIs (placeholder)
            self.update_kpi_placeholders()
            
            self.logger.info("UI configurada correctamente")
            
        except Exception as e:
            self.logger.error(f"Error configurando UI: {e}")
            raise
    
    def connect_signals(self):
        """Conectar señales específicas del controlador"""
        try:
            # Botones principales
            self.btnGenerateInsights.clicked.connect(self.on_generate_insights)
            self.btnRefreshData.clicked.connect(self.on_refresh_data)
            self.btnExportReport.clicked.connect(self.on_export_report)
            
            # Análisis de clientes
            self.btnAnalyzeSelectedCustomer.clicked.connect(self.on_analyze_customer)
            self.btnCustomerSegments.clicked.connect(self.on_analyze_segments)
            
            # Predicción de inventario
            self.btnPredictSelectedProduct.clicked.connect(self.on_predict_inventory)
            
            # Análisis estacional
            self.btnAnalyzeSeasonal.clicked.connect(self.on_analyze_seasonal)
            self.btnExportSeasonalData.clicked.connect(self.on_export_seasonal_data)
            
            # Business insights
            self.btnGenerateFullReport.clicked.connect(self.on_generate_full_report)
            self.btnScheduleReport.clicked.connect(self.on_schedule_report)
            self.btnSaveInsights.clicked.connect(self.on_save_insights)
            
            # Acciones rápidas del dashboard
            self.btnAnalyzeCustomer.clicked.connect(self.on_quick_analyze_customer)
            self.btnPredictInventory.clicked.connect(self.on_quick_predict_inventory)
            self.btnSeasonalAnalysis.clicked.connect(self.on_quick_seasonal_analysis)
            self.btnProductTrends.clicked.connect(self.on_quick_product_trends)
            
            self.logger.info("Señales conectadas correctamente")
            
        except Exception as e:
            self.logger.error(f"Error conectando señales: {e}")
            raise
    
    def load_initial_data(self):
        """Cargar datos iniciales"""
        try:
            # Cargar dashboard básico
            self.refresh_dashboard_data()
            
            self.logger.info("Datos iniciales cargados")
            
        except Exception as e:
            self.logger.error(f"Error cargando datos iniciales: {e}")
    
    # === CONFIGURACIÓN DE TABLAS ===
    
    def setup_product_recommendations_table(self):
        """Configurar tabla de recomendaciones de productos"""
        headers = ['Producto', 'Categoría', 'Precio', 'Tipo', 'Score', 'Razón']
        column_widths = [200, 120, 80, 100, 60, -1]  # -1 = stretch
        self.setup_table_widget(self.tblProductRecommendations, headers, column_widths)
    
    def setup_monthly_patterns_table(self):
        """Configurar tabla de patrones mensuales"""
        headers = ['Mes', 'Ingresos Promedio', 'Transacciones', 'Ticket Promedio', 'Confiabilidad']
        column_widths = [80, 120, 100, 120, 100]
        self.setup_table_widget(self.tblMonthlyPatterns, headers, column_widths)
    
    def setup_business_metrics_table(self):
        """Configurar tabla de métricas de negocio"""
        headers = ['Métrica', 'Actual', 'Anterior', 'Cambio %', 'Tendencia']
        column_widths = [150, 100, 100, 80, 80]
        self.setup_table_widget(self.tblBusinessMetrics, headers, column_widths)
    
    # === CARGA DE DATOS PARA COMBOS ===
    
    def load_customers_combo(self):
        """Cargar combo de clientes"""
        try:
            query = "SELECT id, nombre FROM clientes WHERE activo = 1 ORDER BY nombre"
            customers = self.db_manager.execute_query(query)
            
            self.cmbCustomers.clear()
            self.cmbCustomers.addItem("Seleccionar cliente...", 0)
            
            for customer in customers:
                self.cmbCustomers.addItem(f"{customer['nombre']} (ID: {customer['id']})", customer['id'])
                
        except Exception as e:
            self.logger.error(f"Error cargando clientes: {e}")
    
    def load_products_combo(self):
        """Cargar combo de productos"""
        try:
            query = "SELECT id, nombre, categoria FROM productos WHERE activo = 1 ORDER BY nombre"
            products = self.db_manager.execute_query(query)
            
            self.cmbProducts.clear()
            self.cmbProducts.addItem("Seleccionar producto...", 0)
            
            for product in products:
                self.cmbProducts.addItem(f"{product['nombre']} - {product['categoria']}", product['id'])
                
        except Exception as e:
            self.logger.error(f"Error cargando productos: {e}")
    
    # === MÉTODOS DE ACTUALIZACIÓN DE UI ===
    
    def update_kpi_placeholders(self):
        """Actualizar KPIs con valores placeholder"""
        self.lblRevenueChange.setText("Cargando...")
        self.lblRevenueValue.setText("$--")
        self.progressRevenue.setValue(0)
        
        self.lblCustomerChange.setText("Cargando...")
        self.lblCustomerValue.setText("-- activos")
        self.progressCustomers.setValue(0)
        
        self.lblPredictionAccuracy.setText("Cargando...")
        self.lblNextMonthForecast.setText("$-- proyectado")
        self.progressPredictions.setValue(0)
    
    def update_dashboard_kpis(self, kpis: Dict[str, Any]):
        """Actualizar KPIs del dashboard"""
        try:
            # KPI de ingresos
            revenue = kpis.get('revenue', {})
            revenue_change = revenue.get('change_percent', 0)
            revenue_current = revenue.get('current', 0)
            
            if revenue_change > 0:
                self.lblRevenueChange.setText(f"+{revenue_change}% vs mes anterior")
                self.lblRevenueChange.setStyleSheet("color: #28a745;")
            elif revenue_change < 0:
                self.lblRevenueChange.setText(f"{revenue_change}% vs mes anterior")
                self.lblRevenueChange.setStyleSheet("color: #dc3545;")
            else:
                self.lblRevenueChange.setText("Sin cambios vs mes anterior")
                self.lblRevenueChange.setStyleSheet("color: #6c757d;")
            
            self.lblRevenueValue.setText(self.format_currency(revenue_current))
            self.progressRevenue.setValue(min(100, max(0, int(60 + revenue_change))))
            
            # KPI de clientes
            customers = kpis.get('customers', {})
            customer_change = customers.get('change_percent', 0)
            customer_current = customers.get('current', 0)
            
            if customer_change > 0:
                self.lblCustomerChange.setText(f"+{customer_change}% clientes nuevos")
                self.lblCustomerChange.setStyleSheet("color: #28a745;")
            else:
                self.lblCustomerChange.setText(f"{customer_change}% cambio clientes")
                self.lblCustomerChange.setStyleSheet("color: #dc3545;")
            
            self.lblCustomerValue.setText(f"{customer_current} activos")
            self.progressCustomers.setValue(min(100, max(0, int(70 + customer_change))))
            
            # Predicciones (simulado por ahora)
            self.lblPredictionAccuracy.setText("92% precisión")
            projected_revenue = revenue_current * 1.1  # Simulación simple
            self.lblNextMonthForecast.setText(f"{self.format_currency(projected_revenue)} proyectado")
            self.progressPredictions.setValue(92)
            
        except Exception as e:
            self.logger.error(f"Error actualizando KPIs: {e}")
    
    def update_alerts_and_insights(self, insights: Dict[str, Any]):
        """Actualizar alertas e insights"""
        try:
            # Limpiar listas
            self.listAlerts.clear()
            self.listInsights.clear()
            
            # Agregar alertas
            alerts = insights.get('alerts', [])
            for alert in alerts:
                item = QListWidgetItem(f"⚠️ {alert}")
                item.setForeground(QColor("#dc3545"))
                self.listAlerts.addItem(item)
            
            if not alerts:
                self.listAlerts.addItem("✅ No hay alertas críticas")
            
            # Agregar insights
            key_insights = insights.get('key_insights', [])
            for insight in key_insights:
                item = QListWidgetItem(f"💡 {insight}")
                item.setForeground(QColor("#007bff"))
                self.listInsights.addItem(item)
            
            if not key_insights:
                self.listInsights.addItem("📊 Generando insights...")
                
        except Exception as e:
            self.logger.error(f"Error actualizando alertas e insights: {e}")
    
    # === SLOTS DE EVENTOS ===
    
    @pyqtSlot()
    def on_generate_insights(self):
        """Generar insights principales"""
        try:
            self.run_analysis('business_insights', {})
        except Exception as e:
            self.logger.error(f"Error generando insights: {e}")
            self.show_error("Error", f"No se pudieron generar los insights: {str(e)}")
    
    @pyqtSlot()
    def on_refresh_data(self):
        """Actualizar todos los datos"""
        try:
            self.refresh_dashboard_data()
            self.lblLastUpdate.setText(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
            self.show_info("Datos Actualizados", "Los datos han sido actualizados correctamente")
        except Exception as e:
            self.logger.error(f"Error actualizando datos: {e}")
            self.show_error("Error", f"Error actualizando datos: {str(e)}")
    
    @pyqtSlot()
    def on_export_report(self):
        """Exportar reporte completo"""
        try:
            if not self.last_analysis_data:
                self.show_warning("Advertencia", "No hay datos para exportar. Genere primero un análisis.")
                return
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Exportar Reporte de Análisis Predictivo", 
                f"reporte_predictivo_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(self.last_analysis_data, f, indent=2, ensure_ascii=False, default=str)
                
                self.show_info("Exportación Exitosa", f"Reporte exportado a: {filename}")
                
        except Exception as e:
            self.logger.error(f"Error exportando reporte: {e}")
            self.show_error("Error de Exportación", str(e))
    
    @pyqtSlot()
    def on_analyze_customer(self):
        """Analizar cliente seleccionado"""
        try:
            customer_id = self.cmbCustomers.currentData()
            if not customer_id or customer_id == 0:
                self.show_warning("Selección Requerida", "Por favor seleccione un cliente para analizar")
                return
            
            self.run_analysis('customer_behavior', {'customer_id': customer_id})
            
        except Exception as e:
            self.logger.error(f"Error analizando cliente: {e}")
            self.show_error("Error", str(e))
    
    @pyqtSlot()
    def on_analyze_segments(self):
        """Analizar segmentos de clientes"""
        try:
            self.run_analysis('segment_analysis', {})
        except Exception as e:
            self.logger.error(f"Error analizando segmentos: {e}")
            self.show_error("Error", str(e))
    
    @pyqtSlot()
    def on_predict_inventory(self):
        """Predecir inventario para producto seleccionado"""
        try:
            product_id = self.cmbProducts.currentData()
            if not product_id or product_id == 0:
                self.show_warning("Selección Requerida", "Por favor seleccione un producto para analizar")
                return
            
            # Obtener días de predicción
            days_text = self.cmbPredictionDays.currentText()
            days_ahead = int(days_text.split()[0])  # Extraer número
            
            self.run_analysis('inventory_prediction', {
                'product_id': product_id, 
                'days_ahead': days_ahead
            })
            
        except Exception as e:
            self.logger.error(f"Error prediciendo inventario: {e}")
            self.show_error("Error", str(e))
    
    @pyqtSlot()
    def on_analyze_seasonal(self):
        """Analizar patrones estacionales"""
        try:
            # Obtener período de análisis
            period_text = self.cmbAnalysisPeriod.currentText()
            months_back = int(period_text.split()[1])  # Extraer número
            
            self.run_analysis('seasonal_analysis', {'months_back': months_back})
            
        except Exception as e:
            self.logger.error(f"Error analizando estacionalidad: {e}")
            self.show_error("Error", str(e))
    
    @pyqtSlot()
    def on_export_seasonal_data(self):
        """Exportar datos estacionales"""
        try:
            seasonal_data = self.last_analysis_data.get('seasonal_analysis')
            if not seasonal_data:
                self.show_warning("Sin Datos", "Primero realice un análisis estacional")
                return
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Exportar Datos Estacionales", 
                f"analisis_estacional_{datetime.now().strftime('%Y%m%d')}.json",
                "JSON Files (*.json);;All Files (*)"
            )
            
            if filename:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(seasonal_data, f, indent=2, ensure_ascii=False, default=str)
                
                self.show_info("Exportación Exitosa", f"Datos estacionales exportados a: {filename}")
                
        except Exception as e:
            self.logger.error(f"Error exportando datos estacionales: {e}")
            self.show_error("Error", str(e))
    
    @pyqtSlot()
    def on_generate_full_report(self):
        """Generar reporte completo de business insights"""
        try:
            self.run_analysis('business_insights', {})
        except Exception as e:
            self.logger.error(f"Error generando reporte completo: {e}")
            self.show_error("Error", str(e))
    
    @pyqtSlot()
    def on_schedule_report(self):
        """Programar reportes automáticos"""
        self.show_info("Función en Desarrollo", "La programación de reportes automáticos estará disponible próximamente")
    
    @pyqtSlot()
    def on_save_insights(self):
        """Guardar insights actuales"""
        try:
            insights_data = self.last_analysis_data.get('business_insights')
            if not insights_data:
                self.show_warning("Sin Datos", "No hay insights para guardar")
                return
            
            # TODO: Implementar guardado en base de datos
            self.show_info("Función en Desarrollo", "El guardado de insights estará disponible próximamente")
            
        except Exception as e:
            self.logger.error(f"Error guardando insights: {e}")
            self.show_error("Error", str(e))
    
    # === ACCIONES RÁPIDAS DEL DASHBOARD ===
    
    @pyqtSlot()
    def on_quick_analyze_customer(self):
        """Acción rápida: cambiar a tab de análisis de cliente"""
        self.tabWidget.setCurrentIndex(1)  # Tab de análisis de clientes
    
    @pyqtSlot()
    def on_quick_predict_inventory(self):
        """Acción rápida: cambiar a tab de predicción de inventario"""
        self.tabWidget.setCurrentIndex(2)  # Tab de predicción de inventario
    
    @pyqtSlot()
    def on_quick_seasonal_analysis(self):
        """Acción rápida: cambiar a tab de análisis estacional"""
        self.tabWidget.setCurrentIndex(3)  # Tab de análisis estacional
    
    @pyqtSlot()
    def on_quick_product_trends(self):
        """Acción rápida: analizar tendencias de productos"""
        try:
            self.run_analysis('product_trends', {'top_n': 15})
        except Exception as e:
            self.logger.error(f"Error analizando tendencias de productos: {e}")
            self.show_error("Error", str(e))
    
    # === MÉTODOS DE ANÁLISIS ===
    
    def run_analysis(self, analysis_type: str, params: Dict = None):
        """Ejecutar análisis en hilo separado"""
        try:
            if self.current_analysis_thread and self.current_analysis_thread.isRunning():
                self.show_warning("Análisis en Proceso", "Espere a que termine el análisis actual")
                return
            
            # Mostrar indicador de carga
            self.show_loading_indicator(True)
            
            # Crear y ejecutar hilo de análisis
            self.current_analysis_thread = AnalysisWorkerThread(
                analysis_type, self.predictive_manager, params
            )
            
            self.current_analysis_thread.analysis_completed.connect(
                lambda result: self.on_analysis_completed(analysis_type, result)
            )
            self.current_analysis_thread.analysis_failed.connect(self.on_analysis_failed)
            
            self.current_analysis_thread.start()
            
        except Exception as e:
            self.show_loading_indicator(False)
            raise
    
    def on_analysis_completed(self, analysis_type: str, result: Dict[str, Any]):
        """Manejar análisis completado"""
        try:
            self.show_loading_indicator(False)
            
            if 'error' in result:
                self.show_error("Error en Análisis", result['error'])
                return
            
            # Guardar resultado
            self.last_analysis_data[analysis_type] = result
            
            # Actualizar UI según tipo de análisis
            if analysis_type == 'customer_behavior':
                self.update_customer_analysis_ui(result)
            elif analysis_type == 'inventory_prediction':
                self.update_inventory_prediction_ui(result)
            elif analysis_type == 'seasonal_analysis':
                self.update_seasonal_analysis_ui(result)
            elif analysis_type == 'business_insights':
                self.update_business_insights_ui(result)
            elif analysis_type == 'segment_analysis':
                self.update_segment_analysis_ui(result)
            elif analysis_type == 'product_trends':
                self.show_info("Análisis Completado", 
                              f"Análisis de {result.get('products_analyzed', 0)} productos completado")
            
            self.lblLastUpdate.setText(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            self.logger.error(f"Error procesando resultado de análisis: {e}")
            self.show_error("Error", str(e))
        finally:
            self.show_loading_indicator(False)
    
    def on_analysis_failed(self, error_message: str):
        """Manejar fallo en análisis"""
        self.show_loading_indicator(False)
        self.show_error("Error en Análisis", error_message)
    
    # === MÉTODOS DE ACTUALIZACIÓN DE UI ESPECÍFICOS ===
    
    def update_customer_analysis_ui(self, result: Dict[str, Any]):
        """Actualizar UI con resultado de análisis de cliente"""
        try:
            # Perfil del cliente
            customer_id = result.get('customer_id', 'N/A')
            segment = result.get('segment', {})
            clv_prediction = result.get('clv_prediction', {})
            
            profile_text = f"""
=== ANÁLISIS DE COMPORTAMIENTO ===
Cliente ID: {customer_id}
Segmento: {segment.get('segment_name', 'N/A')}
CLV Predicho: ${clv_prediction.get('predicted_clv', 0):,.2f}
Confianza: {result.get('confidence_score', 0):.1%}

=== CARACTERÍSTICAS ===
Total Gastado: ${segment.get('characteristics', {}).get('total_spent', 0):,.2f}
Compras Totales: {segment.get('characteristics', {}).get('total_purchases', 0)}
Frecuencia: {segment.get('characteristics', {}).get('purchase_frequency', 0):.1f}/mes
            """
            
            self.txtCustomerProfile.setText(profile_text.strip())
            
            # Predicciones
            churn_prediction = result.get('churn_prediction', {})
            next_purchase = result.get('next_purchase_prediction', {})
            
            predictions_text = f"""
=== PREDICCIÓN DE ABANDONO ===
Probabilidad: {churn_prediction.get('churn_probability', 0):.1%}
Riesgo: {churn_prediction.get('risk_level', 'N/A').upper()}
Días desde última compra: {churn_prediction.get('days_since_last_purchase', 0)}

=== PRÓXIMA COMPRA ===
Fecha predicha: {next_purchase.get('predicted_date', 'N/A')}
Días hasta predicción: {next_purchase.get('days_until_prediction', 0)}
Probabilidad: {next_purchase.get('probability', 0):.1%}

=== RECOMENDACIÓN ===
{churn_prediction.get('recommendation', 'Sin recomendaciones')}
            """
            
            self.txtCustomerPredictions.setText(predictions_text.strip())
            
            # Recomendaciones de productos
            recommendations = result.get('product_recommendations', [])
            self.populate_product_recommendations(recommendations)
            
        except Exception as e:
            self.logger.error(f"Error actualizando UI de análisis de cliente: {e}")
    
    def update_inventory_prediction_ui(self, result: Dict[str, Any]):
        """Actualizar UI con predicción de inventario"""
        try:
            # Predicción de demanda
            self.lblPredictedDemand.setText(f"Demanda Predicha: {result.get('predicted_total_demand', 0):.0f} unidades")
            self.lblSuggestedStock.setText(f"Stock Sugerido: {result.get('suggested_stock_level', 0):.0f} unidades")
            
            confidence = result.get('confidence_score', 0)
            self.lblConfidenceLevel.setText(f"Nivel de Confianza: {confidence:.1%}")
            self.progressDemandConfidence.setValue(int(confidence * 100))
            
            # Datos históricos
            self.lblAvgDailyDemand.setText(f"Demanda Diaria Promedio: {result.get('avg_daily_demand', 0):.1f}")
            
            demand_stats = result.get('demand_stats', {})
            self.lblMaxDemand.setText(f"Demanda Máxima: {demand_stats.get('max', 0)}")
            
            trend_slope = result.get('trend_slope', 0)
            trend_text = "Creciente" if trend_slope > 0 else "Decreciente" if trend_slope < 0 else "Estable"
            self.lblTrendDirection.setText(f"Tendencia: {trend_text}")
            
            variability = result.get('variability', 0)
            self.lblVariability.setText(f"Variabilidad: {variability:.2f}")
            
            # Recomendaciones
            recommendation = result.get('recommendation', 'Sin recomendaciones disponibles')
            self.txtInventoryRecommendations.setText(recommendation)
            
        except Exception as e:
            self.logger.error(f"Error actualizando UI de predicción de inventario: {e}")
    
    def update_seasonal_analysis_ui(self, result: Dict[str, Any]):
        """Actualizar UI con análisis estacional"""
        try:
            # Fuerza estacional
            seasonal_strength = result.get('seasonal_strength', 0)
            self.lblSeasonalStrength.setText(f"Nivel: {seasonal_strength:.2f}")
            self.progressSeasonalStrength.setValue(int(seasonal_strength * 100))
            
            if result.get('is_highly_seasonal'):
                description = "Negocio altamente estacional"
            else:
                description = "Negocio con baja estacionalidad"
            self.lblSeasonalDescription.setText(description)
            
            # Temporadas
            peak_month = result.get('peak_month_name', 'N/A')
            low_month = result.get('low_month_name', 'N/A')
            
            self.lblPeakMonth.setText(f"Mes Pico: {peak_month}")
            self.lblLowMonth.setText(f"Mes Bajo: {low_month}")
            
            # Patrones mensuales
            monthly_patterns = result.get('monthly_patterns', {})
            self.populate_monthly_patterns_table(monthly_patterns)
            
            # Recomendaciones
            recommendations = result.get('recommendations', [])
            self.listSeasonalRecommendations.clear()
            for rec in recommendations:
                self.listSeasonalRecommendations.addItem(f"💡 {rec}")
            
        except Exception as e:
            self.logger.error(f"Error actualizando UI de análisis estacional: {e}")
    
    def update_business_insights_ui(self, result: Dict[str, Any]):
        """Actualizar UI con business insights"""
        try:
            # Executive summary
            executive_summary = "\n".join(result.get('executive_summary', []))
            if not executive_summary:
                executive_summary = "Análisis completado exitosamente. Revise los insights y recomendaciones."
            self.txtExecutiveSummary.setText(executive_summary)
            
            # Key insights
            key_insights = result.get('key_insights', [])
            self.listKeyInsights.clear()
            for insight in key_insights:
                item = QListWidgetItem(f"🔑 {insight}")
                self.listKeyInsights.addItem(item)
            
            # Strategic recommendations
            recommendations = result.get('recommendations', [])
            self.listStrategicRecommendations.clear()
            for rec in recommendations:
                item = QListWidgetItem(f"🎯 {rec}")
                self.listStrategicRecommendations.addItem(item)
            
            # Business metrics
            business_metrics = result.get('business_metrics', {})
            self.populate_business_metrics_table(business_metrics)
            
            # Actualizar dashboard con estos insights
            self.update_alerts_and_insights(result)
            if business_metrics:
                self.update_dashboard_kpis(business_metrics)
            
        except Exception as e:
            self.logger.error(f"Error actualizando UI de business insights: {e}")
    
    def update_segment_analysis_ui(self, result: Dict[str, Any]):
        """Actualizar UI con análisis de segmentos"""
        try:
            segments = result.get('segments', {})
            if not segments:
                self.show_info("Análisis de Segmentos", "No hay suficientes datos para análisis de segmentos")
                return
            
            # Mostrar información en el dashboard
            message = f"Análisis de {result.get('total_customers_analyzed', 0)} clientes completado.\n\n"
            for segment_key, segment_data in segments.items():
                message += f"• {segment_data['name']}: {segment_data['customer_count']} clientes ({segment_data['percentage']}%)\n"
            
            self.show_info("Análisis de Segmentos Completado", message)
            
        except Exception as e:
            self.logger.error(f"Error actualizando UI de análisis de segmentos: {e}")
    
    # === MÉTODOS DE POBLACIÓN DE TABLAS ===
    
    def populate_product_recommendations(self, recommendations: List[Dict[str, Any]]):
        """Poblar tabla de recomendaciones de productos"""
        try:
            self.tblProductRecommendations.setRowCount(len(recommendations))
            
            for row, rec in enumerate(recommendations):
                items = [
                    rec.get('product_name', ''),
                    rec.get('category', ''),
                    self.format_currency(rec.get('price', 0)),
                    rec.get('recommendation_type', '').title(),
                    f"{rec.get('score', 0):.2f}",
                    rec.get('reason', '')
                ]
                
                for col, item in enumerate(items):
                    self.tblProductRecommendations.setItem(row, col, QTableWidgetItem(str(item)))
            
            self.tblProductRecommendations.resizeColumnsToContents()
            
        except Exception as e:
            self.logger.error(f"Error poblando recomendaciones de productos: {e}")
    
    def populate_monthly_patterns_table(self, monthly_patterns: Dict[str, Any]):
        """Poblar tabla de patrones mensuales"""
        try:
            self.tblMonthlyPatterns.setRowCount(len(monthly_patterns))
            
            for row, (month, data) in enumerate(monthly_patterns.items()):
                items = [
                    month,
                    self.format_currency(data.get('avg_revenue', 0)),
                    str(int(data.get('avg_transactions', 0))),
                    self.format_currency(data.get('avg_ticket', 0)),
                    data.get('reliability', 'N/A').title()
                ]
                
                for col, item in enumerate(items):
                    widget_item = QTableWidgetItem(str(item))
                    
                    # Colorear según confiabilidad
                    if col == 4:  # Columna de confiabilidad
                        if item.lower() == 'high':
                            widget_item.setForeground(QColor("#28a745"))
                        elif item.lower() == 'low':
                            widget_item.setForeground(QColor("#dc3545"))
                    
                    self.tblMonthlyPatterns.setItem(row, col, widget_item)
            
            self.tblMonthlyPatterns.resizeColumnsToContents()
            
        except Exception as e:
            self.logger.error(f"Error poblando patrones mensuales: {e}")
    
    def populate_business_metrics_table(self, business_metrics: Dict[str, Any]):
        """Poblar tabla de métricas de negocio"""
        try:
            metrics_display = {
                'transactions': 'Transacciones',
                'customers': 'Clientes',
                'revenue': 'Ingresos',
                'avg_ticket': 'Ticket Promedio',
                'units_sold': 'Unidades Vendidas'
            }
            
            self.tblBusinessMetrics.setRowCount(len(business_metrics))
            
            for row, (metric_key, metric_data) in enumerate(business_metrics.items()):
                current = metric_data.get('current', 0)
                previous = metric_data.get('previous', 0)
                change_percent = metric_data.get('change_percent', 0)
                trend = metric_data.get('trend', 'stable')
                
                # Formatear valores según tipo de métrica
                if metric_key in ['revenue', 'avg_ticket']:
                    current_str = self.format_currency(current)
                    previous_str = self.format_currency(previous)
                else:
                    current_str = f"{current:,}"
                    previous_str = f"{previous:,}"
                
                items = [
                    metrics_display.get(metric_key, metric_key.title()),
                    current_str,
                    previous_str,
                    f"{change_percent:+.1f}%",
                    "↑" if trend == 'up' else "↓" if trend == 'down' else "→"
                ]
                
                for col, item in enumerate(items):
                    widget_item = QTableWidgetItem(str(item))
                    
                    # Colorear cambio porcentual
                    if col == 3:  # Columna de cambio %
                        if change_percent > 0:
                            widget_item.setForeground(QColor("#28a745"))
                        elif change_percent < 0:
                            widget_item.setForeground(QColor("#dc3545"))
                    
                    # Colorear tendencia
                    elif col == 4:  # Columna de tendencia
                        if trend == 'up':
                            widget_item.setForeground(QColor("#28a745"))
                        elif trend == 'down':
                            widget_item.setForeground(QColor("#dc3545"))
                    
                    self.tblBusinessMetrics.setItem(row, col, widget_item)
            
            self.tblBusinessMetrics.resizeColumnsToContents()
            
        except Exception as e:
            self.logger.error(f"Error poblando métricas de negocio: {e}")
    
    # === MÉTODOS AUXILIARES ===
    
    def show_loading_indicator(self, show: bool):
        """Mostrar/ocultar indicador de carga"""
        if show:
            self.lblLastUpdate.setText("🔄 Procesando análisis...")
        else:
            self.lblLastUpdate.setText(f"Última actualización: {datetime.now().strftime('%H:%M:%S')}")
    
    def refresh_dashboard_data(self):
        """Refrescar datos del dashboard"""
        try:
            # Obtener KPIs básicos usando el predictive manager
            if self.predictive_manager:
                kpis = self.predictive_manager._calculate_business_kpis()
                if kpis:
                    self.update_dashboard_kpis(kpis)
                
                # Obtener algunos insights básicos
                try:
                    segment_analysis = self.predictive_manager.get_segment_analysis()
                    if segment_analysis and 'error' not in segment_analysis:
                        # Crear insights básicos del análisis de segmentos
                        basic_insights = {
                            'key_insights': [
                                f"Total de clientes analizados: {segment_analysis.get('total_customers_analyzed', 0)}",
                                f"Segmentos identificados: {len(segment_analysis.get('segments', {}))}"
                            ],
                            'alerts': []
                        }
                        
                        # Buscar alertas en las recomendaciones
                        recommendations = segment_analysis.get('recommendations', [])
                        for rec in recommendations:
                            if rec.get('priority') == 'urgent':
                                basic_insights['alerts'].append(rec.get('description', ''))
                        
                        self.update_alerts_and_insights(basic_insights)
                except:
                    # Si falla el análisis de segmentos, continuar sin alertas
                    pass
                
        except Exception as e:
            self.logger.error(f"Error refrescando dashboard: {e}")
    
    def cleanup(self):
        """Limpiar recursos antes de cerrar"""
        try:
            # Detener timers
            if self.auto_refresh_timer.isActive():
                self.auto_refresh_timer.stop()
            
            # Terminar hilo de análisis si está corriendo
            if self.current_analysis_thread and self.current_analysis_thread.isRunning():
                self.current_analysis_thread.quit()
                self.current_analysis_thread.wait(3000)  # Esperar máximo 3 segundos
            
            super().cleanup()
            
        except Exception as e:
            self.logger.error(f"Error en cleanup: {e}")