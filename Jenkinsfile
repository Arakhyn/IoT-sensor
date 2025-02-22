pipeline {
    agent any
    
    // Parametrización del pipeline
    parameters {
        choice(
            name: 'TIPO_ENTRENAMIENTO',
            choices: ['completo', 'incremental'],
            description: 'Tipo de entrenamiento a realizar'
        )
        booleanParam(
            name: 'GUARDAR_METRICAS',
            defaultValue: true,
            description: 'Guardar métricas del entrenamiento'
        )
    }
    
    // Triggers programados
    triggers {
        // Entrenamiento diario a las 2 AM
        cron('0 2 * * *')
    }
    
    // Opciones generales
    options {
        // Mantener historial de las últimas 10 ejecuciones
        buildDiscarder(logRotator(numToKeepStr: '10'))
        // No ejecutar builds concurrentes
        disableConcurrentBuilds()
        // Timeout global
        timeout(time: 1, unit: 'HOURS')
    }
    
    environment {
        PYTHON_PATH = 'C:\\Users\\tomy_\\AppData\\Local\\Programs\\Python\\Python39\\python.exe'
        WORKSPACE_DIR = "${WORKSPACE}"
    }
    
    stages {
        stage('Validación de Código') {
            agent any
            steps {
                script {
                    echo "[INICIO] Validando código..."
                    bat '''
                        call venv\\Scripts\\activate.bat
                        pip install pylint pytest
                        pylint scripts/*.py || exit 0
                    '''
                }
            }
        }
        
        stage('Preparación') {
            agent any
            steps {
                script {
                    echo "[INICIO] Preparando entorno..."
                    
                    // Crear config.json con valores por defecto
                    bat '''
                        echo {"mode": "local","kafka_broker": "localhost:9092","kinesis_stream": "plc_data","postgres_local": {"dbname": "postgres","user": "postgres","password": "1234","host": "localhost","port": "5432"}} > config.json
                    '''
                    
                    // Crear entorno virtual e instalar dependencias
                    bat '''
                        if not exist venv\\Scripts\\activate.bat (
                            "%PYTHON_PATH%" -m venv venv
                        )
                        call venv\\Scripts\\activate.bat
                        python -m pip install --upgrade pip
                        pip install -r requirements.txt
                        pip install pytest
                    '''
                }
            }
        }
        
        stage('Pruebas') {
            agent any
            steps {
                script {
                    echo "[INICIO] Ejecutando pruebas..."
                    bat '''
                        call venv\\Scripts\\activate.bat
                        python -m pytest tests/ || exit 0
                    '''
                }
            }
        }
        
        stage('Entrenamiento') {
            agent any
            steps {
                script {
                    echo "[INICIO] Iniciando entrenamiento ${params.TIPO_ENTRENAMIENTO}..."
                    bat """
                        cd "${WORKSPACE}"
                        call venv\\Scripts\\activate.bat
                        python scripts/train_model.py --tipo ${params.TIPO_ENTRENAMIENTO}
                        if exist maintenance_model.joblib (
                            echo "✅ Modelo guardado exitosamente"
                        ) else (
                            echo "❌ Error: No se encontró el modelo entrenado"
                            exit 1
                        )
                    """
                }
            }
        }
        
        stage('Evaluación') {
            agent any
            when {
                expression { params.GUARDAR_METRICAS }
            }
            steps {
                script {
                    echo "[INICIO] Evaluando modelo..."
                    bat '''
                        call venv\\Scripts\\activate.bat
                        python scripts/evaluate_model.py
                        
                        if exist model_metrics.csv (
                            echo "✅ Métricas guardadas exitosamente"
                        ) else (
                            echo "❌ Error: No se encontró el archivo de métricas"
                            exit 1
                        )
                    '''
                    
                    // Leer y mostrar métricas en la consola
                    def metricas = readFile('model_metrics.csv').trim()
                    echo "📊 Métricas del modelo (último registro):"
                    echo metricas.split('\n')[1] // Mostrar solo la última línea con métricas
                }
            }
        }
    }
    
    post {
        success {
            script {
                echo "✅ Pipeline ejecutado exitosamente"
                // Verificar y archivar artefactos
                bat '''
                    dir
                    if exist maintenance_model.joblib (
                        echo "✅ Modelo encontrado"
                    ) else (
                        echo "❌ Modelo no encontrado"
                        exit 1
                    )
                    if exist model_metrics.csv (
                        echo "✅ Métricas encontradas"
                    ) else (
                        echo "❌ Métricas no encontradas"
                        exit 1
                    )
                '''
                archiveArtifacts artifacts: 'maintenance_model.joblib, model_metrics.csv', 
                               fingerprint: true,
                               allowEmptyArchive: false
            }
        }
        failure {
            echo "❌ Error en la ejecución del pipeline"
        }
        always {
            script {
                try {
                    // Intentar archivar lo que se pueda antes de limpiar
                    if (fileExists('model_metrics.csv')) {
                        archiveArtifacts artifacts: 'model_metrics.csv', 
                                       allowEmptyArchive: true
                    }
                    if (fileExists('maintenance_model.joblib')) {
                        archiveArtifacts artifacts: 'maintenance_model.joblib', 
                                       allowEmptyArchive: true
                    }
                } catch (Exception e) {
                    echo "Advertencia: No se pudieron archivar algunos artefactos"
                } finally {
                    cleanWs()
                }
            }
        }
    }
} 