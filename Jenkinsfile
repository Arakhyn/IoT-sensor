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
        timeout(time: 30, unit: 'MINUTES')
    }
    
    environment {
        // Usar la ruta de Python directamente
        PYTHON_PATH = 'C:\\Users\\tomy_\\AppData\\Local\\Programs\\Python\\Python39\\python.exe'
        // El workspace se maneja automáticamente por Jenkins
        WORKSPACE_DIR = "${WORKSPACE}"
        // Configurar codificación
        PYTHONIOENCODING = 'utf-8'
        PYTHONUTF8 = '1'
    }
    
    stages {
        stage('Verificar Entorno') {
            steps {
                script {
                    echo "[INICIO] Verificando entorno de ejecucion..."
                    bat '''
                        echo [DEBUG] Configurando codificacion...
                        set PYTHONIOENCODING=utf-8
                        set PYTHONUTF8=1
                        echo [DEBUG] Verificando version de Python...
                        "%PYTHON_PATH%" --version
                        echo [DEBUG] Verificando version de pip...
                        "%PYTHON_PATH%" -m pip --version
                        echo [DEBUG] Workspace actual: %WORKSPACE%
                        echo [DEBUG] Listando contenido del directorio:
                        dir
                    '''
                }
            }
        }
        
        stage('Preparación') {
            steps {
                script {
                    echo "[INICIO] Preparando entorno virtual..."
                    bat '''
                        echo [DEBUG] Configurando codificacion...
                        set PYTHONIOENCODING=utf-8
                        set PYTHONUTF8=1
                        
                        echo [DEBUG] Verificando existencia de entorno virtual...
                        if exist venv (
                            echo [DEBUG] Eliminando entorno virtual anterior...
                            rmdir /s /q venv
                        )
                        
                        echo [INFO] Creando nuevo entorno virtual...
                        "%PYTHON_PATH%" -m venv venv
                        
                        echo [DEBUG] Activando entorno virtual...
                        call venv\\Scripts\\activate.bat
                        
                        echo [DEBUG] Actualizando pip...
                        python -m pip install --upgrade pip
                        
                        echo [DEBUG] Instalando dependencias...
                        pip install -r requirements.txt
                        
                        echo [DEBUG] Listando paquetes instalados:
                        pip list
                    '''
                }
            }
        }
        
        stage('Configuración') {
            steps {
                script {
                    echo "[INICIO] Creando archivo de configuración..."
                    bat '''
                        echo [DEBUG] Generando config.json...
                        echo {> config.json
                        echo   "postgres_local": {>> config.json
                        echo     "host": "localhost",>> config.json
                        echo     "port": 5432,>> config.json
                        echo     "dbname": "maintenance_db",>> config.json
                        echo     "user": "postgres",>> config.json
                        echo     "password": "postgres">> config.json
                        echo   },>> config.json
                        echo   "kafka_broker": "localhost:9092",>> config.json
                        echo   "kinesis_stream": "plc_data",>> config.json
                        echo   "email_notifications": {>> config.json
                        echo     "smtp_server": "smtp.gmail.com",>> config.json
                        echo     "smtp_port": 587,>> config.json
                        echo     "sender_email": "test@example.com",>> config.json
                        echo     "sender_password": "your_password",>> config.json
                        echo     "recipients": ["test@example.com"]>> config.json
                        echo   }>> config.json
                        echo }>> config.json
                        
                        echo [DEBUG] Contenido de config.json:
                        type config.json
                    '''
                }
            }
        }
        
        stage('Verificar Dependencias') {
            steps {
                script {
                    echo "[INICIO] Verificando dependencias del proyecto..."
                    bat '''
                        echo [DEBUG] Configurando codificacion...
                        set PYTHONIOENCODING=utf-8
                        set PYTHONUTF8=1
                        
                        echo [DEBUG] Activando entorno virtual...
                        call venv\\Scripts\\activate.bat
                        
                        echo [DEBUG] Verificando importacion de modulos...
                        python -c "import sys; sys.stdout.reconfigure(encoding='utf-8'); from predictive_maintenance_agent import PredictiveMaintenanceAgent; print('[OK] Dependencias verificadas')"
                    '''
                }
            }
        }
        
        stage('Entrenamiento') {
            steps {
                script {
                    echo "[INICIO] Iniciando entrenamiento del modelo..."
                    bat '''
                        echo [DEBUG] Configurando codificacion...
                        set PYTHONIOENCODING=utf-8
                        set PYTHONUTF8=1
                        
                        echo [DEBUG] Activando entorno virtual...
                        call venv\\Scripts\\activate.bat
                        
                        echo [DEBUG] Ejecutando script de entrenamiento...
                        python scripts/train_model.py
                    '''
                }
            }
        }
    }
    
    post {
        success {
            echo '[OK] Pipeline ejecutado exitosamente'
            script {
                echo "[DEBUG] Guardando artefactos..."
                archiveArtifacts artifacts: 'maintenance_model.joblib', fingerprint: true
            }
        }
        failure {
            echo '[ERROR] Error en la ejecucion del pipeline'
        }
        always {
            echo '[LIMPIEZA] Limpiando workspace...'
            cleanWs()
        }
    }
} 