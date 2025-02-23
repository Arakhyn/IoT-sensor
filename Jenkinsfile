pipeline {
    agent any
    
    environment {
        PYTHON_PATH = 'C:\\Users\\tomy_\\AppData\\Local\\Programs\\Python\\Python39\\python.exe'
        WORKSPACE_DIR = "${WORKSPACE}"
    }
    
    stages {
        stage('Preparación') {
            steps {
                script {
                    echo "🚀 Preparando entorno..."
                    
                    // Crear config.json si no existe
                    bat '''
                        if not exist config.json (
                            echo {"mode": "local","kafka_broker": "localhost:9092","postgres_local": {"dbname": "postgres","user": "postgres","password": "1234","host": "localhost","port": "5432"}} > config.json
                        )
                    '''
                    
                    // Crear entorno virtual e instalar dependencias
                    bat '''
                        if not exist venv\\Scripts\\activate.bat (
                            "%PYTHON_PATH%" -m venv venv
                        )
                        call venv\\Scripts\\activate.bat
                        python -m pip install --upgrade pip
                        pip install -r requirements.txt
                    '''
                }
            }
        }
        
        stage('Ejecutar Proyecto') {
            steps {
                script {
                    echo "🔄 Iniciando servicios..."
                    bat '''
                        call venv\\Scripts\\activate.bat
                        start /B python main.py
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo "✅ Pipeline ejecutado exitosamente"
        }
        failure {
            echo "❌ Error en la ejecución del pipeline"
        }
        always {
            cleanWs()
        }
    }
} 