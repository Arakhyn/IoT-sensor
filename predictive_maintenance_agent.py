# -*- coding: utf-8 -*-
from notification_service import MaintenanceNotificationService
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
import joblib
from sqlalchemy import create_engine
import logging
import json
from datetime import datetime, timedelta
import time
import warnings
warnings.filterwarnings('ignore')

class PredictiveMaintenanceAgent:
    def __init__(self, config_path='config.json'):
        self.setup_logging()
        self.load_config(config_path)
        self.setup_database_connection()
        self.model = self.initialize_model()
        self.scaler = StandardScaler()
        self.failure_patterns = self._initialize_failure_patterns()
        self.maintenance_history = []
        self.alert_thresholds = {
            'temperature': {'warning': 75, 'critical': 85},
            'vibration': {'warning': 0.7, 'critical': 0.9},
            'pressure': {'warning': 90, 'critical': 85},
            'oil_level': {'warning': 0.3, 'critical': 0.2}
        }
        self.notification_service = MaintenanceNotificationService()
        
    def setup_logging(self):
        """Configura el sistema de logging con UTF-8"""
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        
        # Handler para archivo
        file_handler = logging.FileHandler('predictive_maintenance.log', encoding='utf-8')
        file_handler.setFormatter(formatter)
        
        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        
        # Configurar logger
        logging.basicConfig(
            level=logging.INFO,
            handlers=[file_handler, console_handler]
        )
        
        self.logger = logging.getLogger(__name__)

    def load_config(self, config_path):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        
    def setup_database_connection(self):
        try:
            pg = self.config['postgres_local']
            db_url = f"postgresql://{pg['user']}:{pg['password']}@{pg['host']}:{pg['port']}/{pg['dbname']}"
            self.engine = create_engine(db_url)
            self.logger.info("Conexión a base de datos establecida")
        except Exception as e:
            self.logger.error(f"Error conectando a la base de datos: {e}")

    def fetch_training_data(self, days=30):
        """Obtiene datos históricos para entrenamiento"""
        query = f"""
        SELECT 
            temperature, vibration, pressure, rotation_speed,
            power_consumption, noise_level, oil_level, humidity,
            machine_age, wear_level, maintenance_needed
        FROM plc_mech
        WHERE timestamp >= NOW() - INTERVAL '{days} days'
        """
        return pd.read_sql(query, self.engine)

    def preprocess_data(self, df):
        """Preprocesa los datos para el modelo"""
        # Separar features y target
        X = df.drop('maintenance_needed', axis=1)
        y = df['maintenance_needed']
        
        # Escalar características
        X_scaled = self.scaler.fit_transform(X)
        
        return X_scaled, y

    def train_model(self):
        """Entrena el modelo de mantenimiento predictivo"""
        try:
            # Obtener datos
            self.logger.info("Obteniendo datos de entrenamiento...")
            df = self.fetch_training_data()
            
            if df.empty:
                self.logger.warning("No hay datos reales, usando datos dummy para entrenamiento inicial")
                X = np.random.rand(100, 10)
                y = np.random.randint(2, size=100)
            else:
                # Preprocesar datos reales
                X, y = self.preprocess_data(df)
            
            # Entrenar modelo
            self.model.fit(X, y)
            
            # Guardar modelo
            joblib.dump(self.model, 'maintenance_model.joblib')
            
            self.logger.info("Modelo entrenado y guardado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error en entrenamiento: {e}")

    def predict_maintenance(self, current_data):
        """Predice si se necesita mantenimiento basado en datos actuales"""
        try:
            if self.model is None:
                self.model = joblib.load('maintenance_model.joblib')
                self.scaler = StandardScaler()
            
            # Preparar datos
            data_scaled = self.scaler.transform(current_data)
            
            # Realizar predicción
            prediction = self.model.predict(data_scaled)
            probability = self.model.predict_proba(data_scaled)
            
            return {
                'needs_maintenance': bool(prediction[0]),
                'probability': float(probability[0][1]),
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            self.logger.error(f"Error en predicción: {e}")
            return None

    def analyze_feature_importance(self):
        """Analiza la importancia de cada característica"""
        try:
            if not hasattr(self.model, 'feature_importances_'):
                self.logger.warning("Modelo no entrenado completamente, entrenando con datos dummy...")
                # Crear y entrenar con datos dummy si es necesario
                X = np.random.rand(100, 10)
                y = np.random.randint(2, size=100)
                self.model.fit(X, y)
                
            feature_names = [
                'temperature', 'vibration', 'pressure', 'rotation_speed',
                'power_consumption', 'noise_level', 'oil_level', 'humidity',
                'machine_age', 'wear_level'
            ]
            
            importances = pd.DataFrame({
                'feature': feature_names,
                'importance': self.model.feature_importances_
            }).sort_values('importance', ascending=False)
            
            self.logger.info("\nImportancia de características:")
            for _, row in importances.iterrows():
                self.logger.info(f"{row['feature']}: {row['importance']:.3f}")
            
        except Exception as e:
            self.logger.error(f"Error en análisis de características: {e}")

    def _initialize_failure_patterns(self):
        """Inicializa patrones conocidos de fallo"""
        return {
            'bearing_failure': {
                'conditions': {
                    'vibration': lambda x: x > 0.8,
                    'temperature': lambda x: x > 80,
                    'noise_level': lambda x: x > 85
                },
                'description': 'Posible fallo en rodamientos'
            },
            'oil_degradation': {
                'conditions': {
                    'oil_level': lambda x: x < 0.3,
                    'temperature': lambda x: x > 75
                },
                'description': 'Degradación del aceite detectada'
            },
            'overheating': {
                'conditions': {
                    'temperature': lambda x: x > 85,
                    'power_consumption': lambda x: x > 90
                },
                'description': 'Sobrecalentamiento crítico'
            }
        }

    def calculate_remaining_useful_life(self, current_data):
        """Calcula la vida útil restante estimada"""
        try:
            # Usar modelo de regresión para RUL
            features = self.scaler.transform(current_data)
            wear_rate = self.model.predict_proba(features)[0][1]
            
            # Estimación básica de RUL basada en desgaste
            max_age = 8760  # 1 año en horas
            current_age = current_data['machine_age'].iloc[0]
            rul = max_age * (1 - wear_rate) - current_age
            
            return max(0, rul)
        except Exception as e:
            self.logger.error(f"Error calculando RUL: {e}")
            return None

    def detect_failure_patterns(self, current_data):
        """Detecta patrones de fallo conocidos"""
        active_patterns = []
        
        for pattern_name, pattern in self.failure_patterns.items():
            conditions_met = all(
                condition(current_data[param].iloc[0])
                for param, condition in pattern['conditions'].items()
            )
            
            if conditions_met:
                active_patterns.append({
                    'pattern': pattern_name,
                    'description': pattern['description'],
                    'timestamp': datetime.now()
                })
        
        return active_patterns

    def monitor_and_predict(self):
        """Monitoreo continuo y predicción mejorada"""
        self.logger.info("Iniciando monitoreo continuo...")
        
        while True:
            try:
                query = """
                SELECT temperature, vibration, pressure, rotation_speed,
                       power_consumption, noise_level, oil_level, humidity,
                       machine_age, wear_level
                FROM plc_mech
                ORDER BY timestamp DESC
                LIMIT 1
                """
                current_data = pd.read_sql(query, self.engine)
                
                if not current_data.empty:
                    # Predicción de mantenimiento
                    prediction = self.predict_maintenance(current_data)
                    
                    # Calcular RUL
                    rul = self.calculate_remaining_useful_life(current_data)
                    
                    # Detectar patrones de fallo
                    failure_patterns = self.detect_failure_patterns(current_data)
                    
                    # Generar alertas si es necesario
                    if prediction['needs_maintenance'] or failure_patterns:
                        alert = {
                            'timestamp': datetime.now(),
                            'maintenance_needed': prediction['needs_maintenance'],
                            'probability': prediction['probability'],
                            'rul_hours': rul,
                            'failure_patterns': failure_patterns,
                            'current_values': current_data.to_dict('records')[0]
                        }
                        
                        self.logger.warning(f"""
                        🚨 ALERTA DE MANTENIMIENTO
                        Probabilidad de fallo: {alert['probability']:.2%}
                        Vida útil restante estimada: {alert['rul_hours']:.1f} horas
                        
                        Patrones de fallo detectados:
                        {json.dumps(failure_patterns, indent=2)}
                        
                        Valores actuales:
                        {json.dumps(alert['current_values'], indent=2)}
                        """)
                        
                        # Guardar alerta en historial
                        self.maintenance_history.append(alert)
                    
                    # Reentrenar modelo periódicamente
                    if datetime.now().hour == 0:
                        self.train_model()
                        self.analyze_feature_importance()
                        
                        # Guardar historial de mantenimiento
                        with open('maintenance_history.json', 'w') as f:
                            json.dump(self.maintenance_history, f, default=str)
                
            except Exception as e:
                self.logger.error(f"Error en monitoreo: {e}")
            
            time.sleep(30)

    def get_predictions(self, data):
        maintenance_time = self.estimate_maintenance_time(data)
        anomalies = self.detect_anomalies(data)
        patterns = self.analyze_patterns(data)
        
        return {
            'maintenance_time': maintenance_time,
            'anomalies': anomalies,
            'patterns': patterns
        }

    def initialize_model(self):
        """Inicializa o carga el modelo de ML"""
        try:
            # Intentar cargar modelo existente
            return joblib.load('maintenance_model.joblib')
        except:
            # Si no existe, crear nuevo modelo
            return RandomForestClassifier(
                n_estimators=100,
                random_state=42
            )

if __name__ == "__main__":
    agent = PredictiveMaintenanceAgent()
    agent.train_model()
    agent.analyze_feature_importance()
    agent.monitor_and_predict()