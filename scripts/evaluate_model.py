import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
import logging
import json
from datetime import datetime
from sklearn.preprocessing import StandardScaler

def setup_logging():
    """Configura el sistema de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('evaluate_model.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def generate_dummy_data():
    """Genera datos dummy más realistas para evaluación"""
    n_samples = 1000
    np.random.seed(42)  # Para reproducibilidad
    
    # Generar características que simulan datos de sensores
    X_test = np.zeros((n_samples, 10))
    
    # Generar datos normales para condiciones normales
    normal_samples = int(n_samples * 0.7)  # 70% datos normales
    failure_samples = n_samples - normal_samples  # 30% datos de fallo
    
    # Datos normales
    X_test[:normal_samples, 0] = np.random.normal(50, 5, normal_samples)  # Temperatura normal
    X_test[:normal_samples, 1] = np.random.normal(60, 5, normal_samples)  # Humedad normal
    X_test[:normal_samples, 2] = np.random.normal(100, 10, normal_samples)  # Presión normal
    X_test[:normal_samples, 3] = np.random.normal(40, 3, normal_samples)  # Vibración normal
    
    # Datos de fallo
    X_test[normal_samples:, 0] = np.random.normal(75, 8, failure_samples)  # Temperatura alta
    X_test[normal_samples:, 1] = np.random.normal(85, 8, failure_samples)  # Humedad alta
    X_test[normal_samples:, 2] = np.random.normal(70, 15, failure_samples)  # Presión baja
    X_test[normal_samples:, 3] = np.random.normal(70, 5, failure_samples)  # Vibración alta
    
    # Otras métricas
    X_test[:, 4:] = np.random.rand(n_samples, 6) * 100
    
    # Generar etiquetas
    y_test = np.zeros(n_samples)
    y_test[normal_samples:] = 1  # Marcar datos de fallo
    
    # Escalar datos
    scaler = StandardScaler()
    X_test = scaler.fit_transform(X_test)
    
    return X_test, y_test

def evaluate_model():
    """Evalúa el modelo y guarda las métricas"""
    logger = setup_logging()
    
    try:
        # Cargar el modelo
        logger.info("Cargando modelo...")
        model = joblib.load('maintenance_model.joblib')
        
        # Generar datos de prueba
        logger.info("Preparando datos de evaluación...")
        X_test, y_test = generate_dummy_data()
        
        # Realizar predicciones
        logger.info("Realizando predicciones...")
        y_pred = model.predict(X_test)
        
        # Calcular métricas
        metrics = {
            'accuracy': accuracy_score(y_test, y_pred),
            'precision': precision_score(y_test, y_pred),
            'recall': recall_score(y_test, y_pred),
            'f1': f1_score(y_test, y_pred),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # Guardar métricas en CSV
        logger.info("Guardando métricas...")
        metrics_df = pd.DataFrame([metrics])
        metrics_df.to_csv('model_metrics.csv', index=False)
        
        # Mostrar resultados
        logger.info("Métricas del modelo:")
        logger.info(f"Exactitud: {metrics['accuracy']:.2f}")
        logger.info(f"Precisión: {metrics['precision']:.2f}")
        logger.info(f"Recall: {metrics['recall']:.2f}")
        logger.info(f"F1-Score: {metrics['f1']:.2f}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error evaluando el modelo: {e}")
        return False

if __name__ == "__main__":
    success = evaluate_model()
    exit(0 if success else 1) 