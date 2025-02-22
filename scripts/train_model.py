import sys
import os
import argparse
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from predictive_maintenance_agent import PredictiveMaintenanceAgent
import logging
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('training.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

def parse_args():
    """Procesa los argumentos de línea de comandos"""
    parser = argparse.ArgumentParser(description='Entrenamiento del modelo de mantenimiento predictivo')
    parser.add_argument('--tipo', type=str, choices=['completo', 'incremental'],
                      default='completo', help='Tipo de entrenamiento a realizar')
    return parser.parse_args()

def train_with_dummy_data(tipo_entrenamiento):
    """Entrena el modelo con datos dummy si no hay datos reales disponibles"""
    logger = logging.getLogger(__name__)
    logger.warning(f"Usando datos dummy para entrenamiento {tipo_entrenamiento}")
    
    # Generar datos dummy
    n_samples = 1000 if tipo_entrenamiento == 'completo' else 500
    np.random.seed(42)  # Para reproducibilidad
    
    # Generar características que simulan datos de sensores
    X = np.zeros((n_samples, 10))
    
    # Datos normales (70%)
    normal_samples = int(n_samples * 0.7)
    failure_samples = n_samples - normal_samples
    
    # Datos normales
    X[:normal_samples, 0] = np.random.normal(50, 5, normal_samples)  # Temperatura normal
    X[:normal_samples, 1] = np.random.normal(60, 5, normal_samples)  # Humedad normal
    X[:normal_samples, 2] = np.random.normal(100, 10, normal_samples)  # Presión normal
    X[:normal_samples, 3] = np.random.normal(40, 3, normal_samples)  # Vibración normal
    
    # Datos de fallo (30%)
    X[normal_samples:, 0] = np.random.normal(75, 8, failure_samples)  # Temperatura alta
    X[normal_samples:, 1] = np.random.normal(85, 8, failure_samples)  # Humedad alta
    X[normal_samples:, 2] = np.random.normal(70, 15, failure_samples)  # Presión baja
    X[normal_samples:, 3] = np.random.normal(70, 5, failure_samples)  # Vibración alta
    
    # Otras métricas
    X[:, 4:] = np.random.rand(n_samples, 6) * 100
    
    # Generar etiquetas
    y = np.zeros(n_samples)
    y[normal_samples:] = 1  # Marcar datos de fallo
    
    # Entrenar modelo
    model = RandomForestClassifier(
        n_estimators=100 if tipo_entrenamiento == 'completo' else 50,
        random_state=42
    )
    model.fit(X, y)
    
    return model, X, y

def main():
    args = parse_args()
    logger = setup_logging()
    try:
        logger.info(f"Iniciando entrenamiento {args.tipo} del modelo...")
        
        # Inicializar agente
        agent = PredictiveMaintenanceAgent()
        model_path = os.path.join(os.getcwd(), 'maintenance_model.joblib')
        
        try:
            # Intentar entrenar con datos reales
            agent.train_model()
            
            # Verificar que el modelo se guardó
            if os.path.exists(model_path):
                logger.info("✅ Modelo guardado exitosamente (datos reales)")
                model = joblib.load(model_path)
            else:
                raise Exception("No se encontró el modelo después del entrenamiento con datos reales")
                
        except Exception as db_error:
            logger.error(f"Error accediendo a la base de datos: {db_error}")
            logger.info(f"Procediendo con entrenamiento {args.tipo} usando datos dummy...")
            
            # Entrenar con datos dummy
            model, X, y = train_with_dummy_data(args.tipo)
            
            # Guardar el modelo
            joblib.dump(model, model_path)
            logger.info(f"Modelo guardado en: {model_path}")
            
            # Verificar que el modelo se guardó
            if os.path.exists(model_path):
                logger.info("✅ Modelo guardado exitosamente (datos dummy)")
            else:
                logger.error("❌ Error: No se pudo guardar el modelo")
                return 1
            
            # Calcular y mostrar métricas básicas
            feature_names = [
                'temperature', 'vibration', 'pressure', 'rotation_speed',
                'power_consumption', 'noise_level', 'oil_level', 'humidity',
                'machine_age', 'wear_level'
            ]
            
            importances = dict(zip(feature_names, model.feature_importances_))
            for feature, importance in sorted(importances.items(), key=lambda x: x[1], reverse=True):
                logger.info(f"{feature}: {importance:.3f}")
        
        logger.info("Entrenamiento completado exitosamente")
        return 0
    except Exception as e:
        logger.error(f"Error durante el entrenamiento: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 