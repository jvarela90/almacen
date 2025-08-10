"""
Script de prueba para el sistema de análisis predictivo
AlmacénPro v2.0 - Test completo de funcionalidades ML
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import unittest
import json
import tempfile
from datetime import datetime, timedelta
from database.manager import DatabaseManager
from managers.predictive_analysis_manager import PredictiveAnalysisManager
from managers.customer_manager import CustomerManager
from managers.product_manager import ProductManager
from managers.sales_manager import SalesManager
from utils.ml_utils import (DataPreprocessor, FeatureEngineer, SimpleMLModels, 
                           PredictionValidator, ModelEvaluator)

class TestPredictiveAnalysis(unittest.TestCase):
    """Test suite para análisis predictivo"""
    
    def setUp(self):
        """Configurar entorno de prueba"""
        # Crear base de datos temporal
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        
        # Inicializar managers
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.db_manager.create_tables()
        
        self.customer_manager = CustomerManager(self.db_manager)
        self.product_manager = ProductManager(self.db_manager)
        self.sales_manager = SalesManager(self.db_manager, self.product_manager)
        self.predictive_manager = PredictiveAnalysisManager(self.db_manager)
        
        # Crear tablas de análisis predictivo
        self.predictive_manager.create_prediction_tables()
        
        # Crear datos de prueba
        self.create_test_data()
    
    def tearDown(self):
        """Limpiar después de pruebas"""
        try:
            os.unlink(self.temp_db.name)
        except:
            pass
    
    def create_test_data(self):
        """Crear datos de prueba"""
        print("Creando datos de prueba para analisis predictivo...")
        
        # Crear productos
        products = [
            {"nombre": "Laptop Dell", "precio": 50000, "categoria": "Electrónicos", "codigo": "DELL001"},
            {"nombre": "Mouse Logitech", "precio": 2500, "categoria": "Electrónicos", "codigo": "LOG001"},
            {"nombre": "Escritorio Madera", "precio": 15000, "categoria": "Muebles", "codigo": "ESC001"},
            {"nombre": "Silla Ergonómica", "precio": 8000, "categoria": "Muebles", "codigo": "SIL001"},
            {"nombre": "Monitor Samsung", "precio": 25000, "categoria": "Electrónicos", "codigo": "SAM001"}
        ]
        
        self.product_ids = []
        for product in products:
            product_id = self.product_manager.add_product(product)
            self.product_ids.append(product_id)
            print(f"  Producto creado: {product['nombre']} (ID: {product_id})")
        
        # Crear clientes con diferentes perfiles
        customers = [
            # Cliente VIP - Alto valor, frecuente
            {"nombre": "Ana García", "email": "ana@email.com", "telefono": "1234567890", 
             "purchases": 15, "avg_amount": 35000, "pattern": "frequent_high_value"},
            
            # Cliente regular - Medio valor, ocasional
            {"nombre": "Carlos López", "email": "carlos@email.com", "telefono": "1234567891",
             "purchases": 8, "avg_amount": 15000, "pattern": "regular"},
            
            # Cliente en riesgo - Pocas compras recientes
            {"nombre": "María Rodríguez", "email": "maria@email.com", "telefono": "1234567892",
             "purchases": 12, "avg_amount": 20000, "pattern": "at_risk"},
            
            # Cliente nuevo - Pocas compras, alto potencial
            {"nombre": "Juan Pérez", "email": "juan@email.com", "telefono": "1234567893",
             "purchases": 3, "avg_amount": 45000, "pattern": "new_high_potential"},
            
            # Cliente estacional - Patrón estacional
            {"nombre": "Laura Martín", "email": "laura@email.com", "telefono": "1234567894",
             "purchases": 6, "avg_amount": 12000, "pattern": "seasonal"}
        ]
        
        self.customer_ids = []
        for customer in customers:
            customer_data = {k: v for k, v in customer.items() if k not in ['purchases', 'avg_amount', 'pattern']}
            customer_id = self.customer_manager.create_customer(customer_data)
            self.customer_ids.append(customer_id)
            print(f"  Cliente creado: {customer['nombre']} (ID: {customer_id})")
            
            # Crear historial de compras según patrón
            self.create_purchase_history(customer_id, customer['purchases'], 
                                       customer['avg_amount'], customer['pattern'])
        
        print(f"Datos de prueba creados: {len(self.customer_ids)} clientes, {len(self.product_ids)} productos")
    
    def create_purchase_history(self, customer_id, num_purchases, avg_amount, pattern):
        """Crear historial de compras para un cliente"""
        import random
        
        base_date = datetime.now()
        
        for i in range(num_purchases):
            if pattern == "frequent_high_value":
                # Compras regulares cada 2-3 semanas
                days_ago = i * random.randint(14, 21)
                amount = avg_amount * random.uniform(0.8, 1.2)
                
            elif pattern == "regular":
                # Compras cada 1-2 meses
                days_ago = i * random.randint(30, 60)
                amount = avg_amount * random.uniform(0.7, 1.3)
                
            elif pattern == "at_risk":
                # Compras frecuentes al principio, luego espaciadas
                if i < num_purchases // 2:
                    days_ago = (num_purchases - i) * random.randint(15, 30)
                else:
                    days_ago = (num_purchases - i) * random.randint(60, 120)
                amount = avg_amount * random.uniform(0.6, 1.1)
                
            elif pattern == "new_high_potential":
                # Pocas compras recientes, montos altos
                days_ago = i * random.randint(20, 40)
                amount = avg_amount * random.uniform(1.1, 1.4)
                
            elif pattern == "seasonal":
                # Compras concentradas en ciertos meses
                if i % 3 == 0:  # Cada 3 meses aproximadamente
                    days_ago = i * random.randint(80, 100)
                    amount = avg_amount * random.uniform(1.2, 1.5)
                else:
                    days_ago = i * random.randint(20, 40)
                    amount = avg_amount * random.uniform(0.8, 1.0)
            
            # Crear venta
            purchase_date = base_date - timedelta(days=days_ago)
            
            # Seleccionar productos aleatorios
            num_items = random.randint(1, 3)
            items = []
            total_amount = 0
            
            for _ in range(num_items):
                product_id = random.choice(self.product_ids)
                quantity = random.randint(1, 2)
                price = amount / num_items / quantity  # Distribuir el monto
                
                items.append({
                    'producto_id': product_id,
                    'cantidad': quantity,
                    'precio_unitario': price
                })
                total_amount += price * quantity
            
            # Crear venta
            sale_data = {
                'cliente_id': customer_id,
                'fecha_venta': purchase_date.strftime('%Y-%m-%d %H:%M:%S'),
                'total': total_amount,
                'subtotal': total_amount,
                'descuento': 0,
                'impuestos': 0,
                'metodo_pago': random.choice(['efectivo', 'tarjeta_credito', 'transferencia']),
                'estado': 'completada'
            }
            
            try:
                sale_id = self.sales_manager.create_sale(sale_data, items)
                if not sale_id:
                    print(f"  Error creando venta para cliente {customer_id}")
            except Exception as e:
                print(f"  Error en venta para cliente {customer_id}: {e}")
    
    def test_data_preprocessing(self):
        """Test de preprocesamiento de datos"""
        print("\nTesting Data Preprocessing...")
        
        # Test normalización
        values = [10, 20, 30, 40, 50]
        normalized = DataPreprocessor.normalize_values(values, 'min_max')
        self.assertEqual(normalized, [0.0, 0.25, 0.5, 0.75, 1.0])
        print("  Normalizacion min-max correcta")
        
        # Test manejo de outliers
        values_with_outliers = [10, 12, 11, 13, 100, 14, 12]  # 100 es outlier
        cleaned = DataPreprocessor.handle_outliers(values_with_outliers, 'iqr')
        self.assertNotIn(100, cleaned)
        print("  ✅ Manejo de outliers correcto")
        
        # Test características temporales
        dates = [
            datetime(2023, 1, 15),  # Domingo
            datetime(2023, 6, 20),  # Martes
            datetime(2023, 12, 25)  # Lunes
        ]
        time_features = DataPreprocessor.create_time_features(dates)
        self.assertEqual(len(time_features['month']), 3)
        self.assertEqual(time_features['month'], [1, 6, 12])
        self.assertEqual(time_features['is_weekend'], [1, 0, 0])
        print("  ✅ Características temporales correctas")
    
    def test_feature_engineering(self):
        """Test de ingeniería de características"""
        print("\n🧪 Testing Feature Engineering...")
        
        # Test RFM scores
        customer_data = {
            'days_since_last': 30,
            'total_purchases': 10,
            'total_spent': 25000
        }
        
        rfm_scores = FeatureEngineer.calculate_rfm_scores(customer_data)
        
        self.assertIn('recency', rfm_scores)
        self.assertIn('frequency', rfm_scores)
        self.assertIn('monetary', rfm_scores)
        self.assertTrue(0 <= rfm_scores['rfm_combined'] <= 1)
        print(f"  ✅ RFM Score calculado: {rfm_scores['rfm_combined']:.2f}")
        
        # Test características de cohorte
        customer_data['first_purchase'] = '2023-01-15 10:00:00'
        cohort_features = FeatureEngineer.calculate_cohort_features(customer_data)
        
        self.assertIn('cohort', cohort_features)
        self.assertIn('periods_active', cohort_features)
        print(f"  ✅ Cohorte: {cohort_features['cohort']}")
        
        # Test características comportamentales
        purchases = [
            {'fecha_venta': '2023-01-15 10:00:00', 'total': 15000},
            {'fecha_venta': '2023-02-15 10:00:00', 'total': 20000},
            {'fecha_venta': '2023-03-15 10:00:00', 'total': 25000}
        ]
        
        behavioral = FeatureEngineer.calculate_behavioral_features(purchases)
        self.assertIn('avg_days_between_purchases', behavioral)
        self.assertGreater(behavioral['avg_days_between_purchases'], 0)
        print(f"  ✅ Intervalo promedio: {behavioral['avg_days_between_purchases']:.1f} días")
    
    def test_simple_ml_models(self):
        """Test de modelos ML simplificados"""
        print("\n🧪 Testing Simple ML Models...")
        
        # Test predicción de churn
        features = {
            'recency': 0.3,    # Baja recencia (riesgo)
            'frequency': 0.8,  # Alta frecuencia (protección)
            'monetary': 0.6,   # Valor medio
            'consistency_score': 0.4  # Consistencia media
        }
        
        churn_prob, contributions = SimpleMLModels.naive_bayes_churn(features, 0.2)
        
        self.assertTrue(0 <= churn_prob <= 1)
        self.assertIn('recency', contributions)
        print(f"  ✅ Probabilidad de churn: {churn_prob:.2f}")
        print(f"      Contribuciones: {contributions}")
        
        # Test predicción de CLV
        predicted_clv = SimpleMLModels.linear_regression_clv(features, 15000)
        
        self.assertGreater(predicted_clv, 0)
        print(f"  ✅ CLV predicho: ${predicted_clv:,.0f}")
        
        # Test segmentación K-means
        customers_features = [
            {'recency': 0.9, 'frequency': 0.8, 'monetary': 0.9},  # VIP
            {'recency': 0.5, 'frequency': 0.5, 'monetary': 0.5},  # Regular
            {'recency': 0.2, 'frequency': 0.3, 'monetary': 0.2},  # En riesgo
        ]
        
        segments = SimpleMLModels.k_means_segmentation(customers_features, 3)
        self.assertEqual(len(segments), 3)
        self.assertTrue(all(0 <= s < 3 for s in segments))
        print(f"  ✅ Segmentos asignados: {segments}")
    
    def test_prediction_validation(self):
        """Test de validación de predicciones"""
        print("\n🧪 Testing Prediction Validation...")
        
        # Test validación de churn
        features = {'recency': 0.2, 'frequency': 0.9, 'monetary': 0.8}
        validation = PredictionValidator.validate_churn_prediction(0.8, features)
        
        self.assertTrue(validation['is_valid'])
        self.assertIn('warnings', validation)
        print(f"  ✅ Validación churn: {validation['confidence']} confianza")
        if validation['warnings']:
            print(f"      Advertencias: {validation['warnings']}")
        
        # Test validación de CLV
        clv_validation = PredictionValidator.validate_clv_prediction(25000, 20000, features)
        
        self.assertTrue(clv_validation['is_valid'])
        print(f"  ✅ Validación CLV: {clv_validation['confidence']} confianza")
        
        # Test cálculo de confianza
        confidence = PredictionValidator.calculate_prediction_confidence(features, 'churn')
        self.assertTrue(0 <= confidence <= 1)
        print(f"  ✅ Confianza calculada: {confidence:.2f}")
    
    def test_predictive_analysis_manager(self):
        """Test del manager de análisis predictivo"""
        print("\n🧪 Testing Predictive Analysis Manager...")
        
        if not self.customer_ids:
            self.skipTest("No hay clientes de prueba disponibles")
        
        # Test análisis individual
        customer_id = self.customer_ids[0]  # Cliente VIP
        analysis = self.predictive_manager.analyze_customer_behavior(customer_id)
        
        self.assertNotIn('error', analysis)
        self.assertIn('customer_id', analysis)
        self.assertIn('churn_prediction', analysis)
        self.assertIn('clv_prediction', analysis)
        self.assertIn('segment', analysis)
        
        print(f"  ✅ Análisis individual completado para cliente {customer_id}")
        print(f"      Segmento: {analysis['segment'].get('segment_name', 'N/A')}")
        
        churn = analysis['churn_prediction']
        if churn:
            print(f"      Riesgo churn: {churn.get('churn_probability', 0):.0%} ({churn.get('risk_level', 'N/A')})")
        
        clv = analysis['clv_prediction']
        if clv:
            print(f"      CLV predicho: ${clv.get('predicted_clv', 0):,.0f}")
        
        # Test análisis de segmentos
        segment_analysis = self.predictive_manager.get_segment_analysis()
        
        self.assertNotIn('error', segment_analysis)
        self.assertIn('segments', segment_analysis)
        self.assertIn('total_customers_analyzed', segment_analysis)
        
        print(f"  ✅ Análisis de segmentos completado")
        print(f"      Clientes analizados: {segment_analysis['total_customers_analyzed']}")
        print(f"      Segmentos encontrados: {len(segment_analysis['segments'])}")
        
        for segment_id, segment_data in segment_analysis['segments'].items():
            if segment_id != 'total_customers_analyzed':
                print(f"        - {segment_data.get('name', segment_id)}: {segment_data.get('customer_count', 0)} clientes")
    
    def test_pattern_analysis(self):
        """Test de análisis de patrones"""
        print("\n🧪 Testing Pattern Analysis...")
        
        if not self.customer_ids:
            self.skipTest("No hay clientes de prueba disponibles")
        
        customer_id = self.customer_ids[0]  # Cliente con más historial
        
        # Obtener datos del cliente
        customer_data = self.predictive_manager._get_customer_data(customer_id)
        self.assertIsNotNone(customer_data)
        
        print(f"  📊 Cliente {customer_id}:")
        print(f"      Compras: {customer_data.get('total_purchases', 0)}")
        print(f"      Total gastado: ${customer_data.get('total_spent', 0):,.0f}")
        print(f"      Días desde última compra: {customer_data.get('days_since_last', 'N/A')}")
        
        # Análizar patrones de compra
        patterns = self.predictive_manager._analyze_purchase_patterns(customer_id)
        
        print(f"  ✅ Patrones detectados: {len(patterns)}")
        for pattern in patterns:
            pattern_type = pattern.get('pattern_type', 'unknown')
            confidence = pattern.get('confidence', 'unknown')
            description = pattern.get('description', 'Sin descripción')
            print(f"      - {pattern_type.title()}: {confidence} confianza")
            print(f"        {description}")
    
    def test_trend_analysis(self):
        """Test de análisis de tendencias"""
        print("\n🧪 Testing Trend Analysis...")
        
        if not self.customer_ids:
            self.skipTest("No hay clientes de prueba disponibles")
        
        customer_id = self.customer_ids[0]
        trends = self.predictive_manager._analyze_trends(customer_id)
        
        if 'insufficient_data' not in trends:
            self.assertIn('frequency_trend', trends)
            self.assertIn('spending_trend', trends)
            self.assertIn('overall_trend', trends)
            
            print(f"  ✅ Análisis de tendencias completado")
            print(f"      Tendencia general: {trends.get('overall_trend', 'N/A')}")
            print(f"      Tendencia frecuencia: {trends.get('frequency_trend', {}).get('direction', 'N/A')}")
            print(f"      Tendencia gastos: {trends.get('spending_trend', {}).get('direction', 'N/A')}")
        else:
            print("  ⚠️ Datos insuficientes para análisis de tendencias")
    
    def test_next_purchase_prediction(self):
        """Test de predicción de próxima compra"""
        print("\n🧪 Testing Next Purchase Prediction...")
        
        if not self.customer_ids:
            self.skipTest("No hay clientes de prueba disponibles")
        
        customer_id = self.customer_ids[0]
        next_purchase = self.predictive_manager._predict_next_purchase(customer_id)
        
        self.assertIn('prediction', next_purchase.keys())
        
        if next_purchase.get('predicted_date'):
            print(f"  ✅ Próxima compra predicha: {next_purchase['predicted_date']}")
            print(f"      Probabilidad: {next_purchase.get('probability', 0):.0%}")
            print(f"      Días hasta predicción: {next_purchase.get('days_until_prediction', 'N/A')}")
            print(f"      Recomendación: {next_purchase.get('recommendation', 'N/A')}")
        else:
            print(f"  ⚠️ No se pudo predecir próxima compra: {next_purchase.get('prediction', 'Sin datos')}")
    
    def test_product_recommendations(self):
        """Test de recomendaciones de productos"""
        print("\n🧪 Testing Product Recommendations...")
        
        if not self.customer_ids:
            self.skipTest("No hay clientes de prueba disponibles")
        
        customer_id = self.customer_ids[0]
        recommendations = self.predictive_manager._recommend_products(customer_id)
        
        print(f"  ✅ Recomendaciones generadas: {len(recommendations)}")
        
        for i, rec in enumerate(recommendations[:3], 1):  # Top 3
            print(f"      {i}. {rec.get('product_name', 'N/A')}")
            print(f"         Categoría: {rec.get('category', 'N/A')}")
            print(f"         Score: {rec.get('score', 0):.2f}")
            print(f"         Razón: {rec.get('reason', 'N/A')}")
    
    def test_model_evaluator(self):
        """Test del evaluador de modelos"""
        print("\n🧪 Testing Model Evaluator...")
        
        # Test métricas de regresión (CLV)
        predictions_reg = [25000, 30000, 20000, 35000, 15000]
        actuals_reg = [24000, 32000, 18000, 36000, 16000]
        
        regression_metrics = ModelEvaluator.calculate_model_metrics(
            predictions_reg, actuals_reg, 'regression'
        )
        
        self.assertIn('mae', regression_metrics)
        self.assertIn('r2', regression_metrics)
        
        print(f"  ✅ Métricas de regresión:")
        print(f"      MAE: ${regression_metrics.get('mae', 0):,.0f}")
        print(f"      R²: {regression_metrics.get('r2', 0):.3f}")
        
        # Test métricas de clasificación (Churn)
        predictions_class = [0.8, 0.2, 0.9, 0.3, 0.7]
        actuals_class = [1, 0, 1, 0, 1]
        
        classification_metrics = ModelEvaluator.calculate_model_metrics(
            predictions_class, actuals_class, 'classification'
        )
        
        self.assertIn('accuracy', classification_metrics)
        self.assertIn('precision', classification_metrics)
        
        print(f"  ✅ Métricas de clasificación:")
        print(f"      Accuracy: {classification_metrics.get('accuracy', 0):.1%}")
        print(f"      Precision: {classification_metrics.get('precision', 0):.1%}")
        print(f"      F1-Score: {classification_metrics.get('f1', 0):.3f}")
    
    def test_integration_workflow(self):
        """Test de flujo completo de análisis predictivo"""
        print("\n🧪 Testing Complete Predictive Analysis Workflow...")
        
        if not self.customer_ids:
            self.skipTest("No hay clientes de prueba disponibles")
        
        total_analyses = 0
        successful_analyses = 0
        
        # Analizar todos los clientes
        for customer_id in self.customer_ids:
            try:
                analysis = self.predictive_manager.analyze_customer_behavior(customer_id)
                total_analyses += 1
                
                if 'error' not in analysis:
                    successful_analyses += 1
                    
                    # Verificar componentes principales
                    components = [
                        'churn_prediction', 'clv_prediction', 'segment',
                        'next_purchase_prediction', 'product_recommendations'
                    ]
                    
                    available_components = sum(1 for comp in components if comp in analysis)
                    print(f"      Cliente {customer_id}: {available_components}/{len(components)} componentes")
                    
            except Exception as e:
                print(f"      ❌ Error analizando cliente {customer_id}: {e}")
        
        success_rate = successful_analyses / total_analyses if total_analyses > 0 else 0
        print(f"  ✅ Análisis completado: {successful_analyses}/{total_analyses} exitosos ({success_rate:.1%})")
        
        # Test análisis de segmentos global
        try:
            segment_analysis = self.predictive_manager.get_segment_analysis()
            if 'error' not in segment_analysis:
                segments_count = len(segment_analysis.get('segments', {}))
                recommendations_count = len(segment_analysis.get('recommendations', []))
                
                print(f"  ✅ Análisis global de segmentos:")
                print(f"      Segmentos identificados: {segments_count}")
                print(f"      Recomendaciones generadas: {recommendations_count}")
            else:
                print(f"  ❌ Error en análisis de segmentos: {segment_analysis['error']}")
                
        except Exception as e:
            print(f"  ❌ Error en análisis global: {e}")
        
        # Verificar que el sistema está funcional
        self.assertGreaterEqual(success_rate, 0.6)  # Al menos 60% de éxito
        
        print(f"\n🎉 Sistema de Análisis Predictivo funcionando con {success_rate:.0%} de éxito")

def run_comprehensive_test():
    """Ejecutar test completo del sistema predictivo"""
    print("="*80)
    print("INICIANDO TEST COMPLETO DEL SISTEMA DE ANALISIS PREDICTIVO")
    print("="*80)
    
    # Crear suite de tests
    suite = unittest.TestSuite()
    
    # Agregar todos los tests
    test_methods = [
        'test_data_preprocessing',
        'test_feature_engineering', 
        'test_simple_ml_models',
        'test_prediction_validation',
        'test_predictive_analysis_manager',
        'test_pattern_analysis',
        'test_trend_analysis',
        'test_next_purchase_prediction',
        'test_product_recommendations',
        'test_model_evaluator',
        'test_integration_workflow'
    ]
    
    for test_method in test_methods:
        suite.addTest(TestPredictiveAnalysis(test_method))
    
    # Ejecutar tests
    runner = unittest.TextTestRunner(verbosity=0)
    result = runner.run(suite)
    
    # Resumen final
    print("\n" + "="*80)
    print("RESUMEN DEL TEST DE ANALISIS PREDICTIVO")
    print("="*80)
    
    total_tests = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    successes = total_tests - failures - errors
    
    print(f"Tests exitosos: {successes}/{total_tests}")
    print(f"Tests fallidos: {failures}")
    print(f"Tests con errores: {errors}")
    print(f"Tasa de exito: {(successes/total_tests)*100:.1f}%")
    
    if result.failures:
        print(f"\nFALLOS DETECTADOS:")
        for test, traceback in result.failures:
            print(f"   - {test}: {traceback.split('AssertionError: ')[-1].split('\\n')[0] if 'AssertionError:' in traceback else 'Error desconocido'}")
    
    if result.errors:
        print(f"\nERRORES DETECTADOS:")
        for test, traceback in result.errors:
            error_msg = traceback.split('\\n')[-2] if '\\n' in traceback else traceback
            print(f"   - {test}: {error_msg}")
    
    print("\n" + "="*80)
    
    if successes == total_tests:
        print("TODOS LOS TESTS PASARON! Sistema de analisis predictivo completamente funcional.")
    elif successes >= total_tests * 0.8:
        print("Sistema mayormente funcional con algunos problemas menores.")
    else:
        print("Sistema necesita revision - multiples componentes fallando.")
    
    print("="*80)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    # Ejecutar test completo
    success = run_comprehensive_test()
    exit(0 if success else 1)