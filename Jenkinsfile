pipeline {
    agent any
    
    triggers {
        // Programar entrenamiento diario a las 2 AM
        cron('0 2 * * *')
    }
    
    environment {
        PYTHON_PATH = 'C:\\Users\\tomy_\\AppData\\Local\\Programs\\Python\\Python39\\python.exe'
        WORKSPACE_DIR = 'C:\\Users\\tomy_\\Desktop\\Ingenieria inteligencia artificial\\A003-POETRY-SETUP-master\\Proyecto IoT'
    }
    
    stages {
        stage('Preparación') {
            steps {
                script {
                    // Crear entorno virtual si no existe
                    bat '''
                        if not exist venv\\Scripts\\activate.bat (
                            %PYTHON_PATH% -m venv venv
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
                        cd %WORKSPACE_DIR%
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