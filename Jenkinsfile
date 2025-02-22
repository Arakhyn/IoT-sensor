pipeline {
    agent any
    
    triggers {
        // Programar entrenamiento diario a las 2 AM
        cron('0 2 * * *')
    }
    
    options {
        // Mantener builds por 7 días
        buildDiscarder(logRotator(daysToKeepStr: '7'))
        // No ejecutar builds concurrentes
        disableConcurrentBuilds()
        // Timeout global
        timeout(time: 1, unit: 'HOURS')
    }
    
    environment {
        // Usar la ruta de Python directamente
        PYTHON_PATH = 'C:\\Users\\tomy_\\AppData\\Local\\Programs\\Python\\Python39\\python.exe'
        // El workspace se maneja automáticamente por Jenkins
        WORKSPACE_DIR = "${WORKSPACE}"
    }
    
    stages {
        stage('Verificar Entorno') {
            steps {
                script {
                    echo "Verificando entorno de ejecución..."
                    bat '''
                        "%PYTHON_PATH%" --version
                        "%PYTHON_PATH%" -m pip --version
                        echo "Workspace: %WORKSPACE%"
                    '''
                }
            }
        }
        
        stage('Preparación') {
            steps {
                script {
                    echo "Preparando entorno virtual..."
                    bat '''
                        if not exist venv\\Scripts\\activate.bat (
                            echo "Creando nuevo entorno virtual..."
                            "%PYTHON_PATH%" -m venv venv
                        ) else (
                            echo "Usando entorno virtual existente"
                        )
                        call venv\\Scripts\\activate.bat
                        python -m pip install --upgrade pip
                        pip install -r requirements.txt
                    '''
                }
            }
        }
        
        stage('Verificar Dependencias') {
            steps {
                script {
                    echo "Verificando dependencias del proyecto..."
                    bat '''
                        call venv\\Scripts\\activate.bat
                        python -c "from predictive_maintenance_agent import PredictiveMaintenanceAgent; print('✅ Dependencias OK')"
                    '''
                }
            }
        }
        
        stage('Entrenamiento') {
            steps {
                script {
                    echo "Iniciando entrenamiento del modelo..."
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
            echo '✅ Pipeline ejecutado exitosamente'
            script {
                // Guardar artefactos
                archiveArtifacts artifacts: 'maintenance_model.joblib', fingerprint: true
            }
        }
        failure {
            echo '❌ Error en la ejecución del pipeline'
        }
        always {
            echo 'Limpiando workspace...'
            cleanWs()
        }
    }
} 