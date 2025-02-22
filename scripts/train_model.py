import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from predictive_maintenance_agent import PredictiveMaintenanceAgent
import logging

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

def main():
    logger = setup_logging()
    try:
        logger.info("Iniciando entrenamiento del modelo...")
        
        # Inicializar agente
        agent = PredictiveMaintenanceAgent()
        
        # Entrenar modelo
        agent.train_model()
        
        # Analizar importancia de características
        agent.analyze_feature_importance()
        
        logger.info("Entrenamiento completado exitosamente")
        return 0
    except Exception as e:
        logger.error(f"Error durante el entrenamiento: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 