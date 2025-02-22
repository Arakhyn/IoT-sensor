import sys
import os
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

def train_with_dummy_data():
    """Entrena el modelo con datos dummy si no hay datos reales disponibles"""
    logger = logging.getLogger(__name__)
    logger.warning("Usando datos dummy para entrenamiento inicial")
    
    # Generar datos dummy
    n_samples = 1000
    X = np.random.rand(n_samples, 10)  # 10 características
    y = np.random.randint(2, size=n_samples)  # Variable objetivo binaria
    
    # Entrenar modelo
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X, y)
    
    return model, X, y

def main():
    logger = setup_logging()
    try:
        logger.info("Iniciando entrenamiento del modelo...")
        
        # Inicializar agente
        agent = PredictiveMaintenanceAgent()
        
        try:
            # Intentar entrenar con datos reales
            agent.train_model()
        except Exception as db_error:
            logger.error(f"Error accediendo a la base de datos: {db_error}")
            logger.info("Procediendo con entrenamiento usando datos dummy...")
            
            # Entrenar con datos dummy
            model, X, y = train_with_dummy_data()
            
            # Guardar el modelo
            model_path = os.path.join(os.getcwd(), 'maintenance_model.joblib')
            joblib.dump(model, model_path)
            logger.info(f"Modelo guardado en: {model_path}")
            
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