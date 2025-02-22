pipeline {
    agent any
    
    triggers {
        // Programar entrenamiento diario a las 2 AM
        cron('0 2 * * *')
    }
    
    environment {
        // Usar variables de entorno de Jenkins
        PYTHON_PATH = "${tool 'Python3'}"
        // El workspace se maneja automáticamente por Jenkins
        WORKSPACE_DIR = "${WORKSPACE}"
    }
    
    stages {
        stage('Preparación') {
            steps {
                script {
                    // Crear entorno virtual si no existe
                    bat '''
                        if not exist venv\\Scripts\\activate.bat (
                            python -m venv venv
                        )
                        call venv\\Scripts\\activate.bat
                        pip install -r requirements.txt
                    '''
                }
            }
        }
        
        stage('Verificar Dependencias') {
            steps {
                script {
                    bat '''
                        call venv\\Scripts\\activate.bat
                        python -c "from predictive_maintenance_agent import PredictiveMaintenanceAgent; print('Dependencias OK')"
                    '''
                }
            }
        }
        
        stage('Entrenamiento') {
            steps {
                script {
                    bat '''
                        call venv\\Scripts\\activate.bat
                        python scripts/train_model.py
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo 'Entrenamiento completado exitosamente'
            // Aquí puedes añadir notificaciones por email si lo deseas
        }
        failure {
            echo 'Error durante el entrenamiento'
            // Aquí puedes añadir notificaciones por email si lo deseas
        }
    }
} 