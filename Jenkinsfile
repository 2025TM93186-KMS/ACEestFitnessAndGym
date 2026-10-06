pipeline {
    agent any

    environment {
        APP_NAME     = 'aceest-fitness-app'
        APP_VERSION  = '1.1.2'  
        DEV_URL      = "http://localhost:5001"
        TEST_URL     = "http://localhost:5002"
        STAGE_URL    = "http://localhost:5003"
        PROD_URL     = "http://localhost:5004"

        // Dynamic target port mapping depending on the current branch name
        CURRENT_PORT = "${env.BRANCH_NAME == 'Develop' ? '5001' : env.BRANCH_NAME == 'Test' ? '5002' : env.BRANCH_NAME == 'Stage' ? '5003' : '5004'}"
    }

    stages {
        stage('Initialize') {
            steps {
                echo "Starting the automation pipeline for: ${env.APP_NAME} v${env.APP_VERSION}"
            }
        }

        stage('Repository Synchronization') {
            steps {
                echo 'Pulling application code parameters cleanly from GitHub tracking layers...'
                checkout scm
            }
        }

        stage('Python Environment Assembly') {
            steps {
                echo 'Assembling a clean Python virtual environment and installing dependencies on Linux...'
                // Set up venv and install dependencies natively
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
                '''
            }
        }

        stage('Static Lint Analysis') {
            steps {
                echo 'Validating Python syntax compilation structure natively...'
                sh '''
                    . venv/bin/activate
                    python3 -m py_compile app.py
                '''
            }
        }

        stage('Automated Pytest Execution') {
            steps {
                echo 'Invoking component assertion tests inside clean virtual environment...'
                sh '''
                    . venv/bin/activate
                    pytest test_app.py
                '''
            }
        }

        stage('Deploy to Dev') {
            when { branch 'Develop' }
            steps {
                echo "Deploying to DEV environment at ${env.DEV_URL}..."
                sh '''
                    # Stop any running process on this port
                    sudo fuser -k ${CURRENT_PORT}/tcp || true
                    
                    # Launch app in background using the local venv python
                    . venv/bin/activate
                    nohup python3 app.py --port=${CURRENT_PORT} > dev_app.log 2>&1 &
                '''
            }
        }

        stage('Deploy to Test') {
            when { branch 'Test' }
            steps {
                echo "Deploying to TEST environment at ${env.TEST_URL}..."
                sh '''
                    sudo fuser -k ${CURRENT_PORT}/tcp || true
                    . venv/bin/activate
                    nohup python3 app.py --port=${CURRENT_PORT} > test_app.log 2>&1 &
                '''
            }
        }

        stage('Deploy to Stage') {
            when { branch 'Stage' }
            steps {
                echo "Deploying to STAGING environment at ${env.STAGE_URL}..."
                sh '''
                    sudo fuser -k ${CURRENT_PORT}/tcp || true
                    . venv/bin/activate
                    nohup python3 app.py --port=${CURRENT_PORT} > stage_app.log 2>&1 &
                '''
            }
        }

        stage('Deploy to Prod') {
            when { branch 'main' } 
            steps {
                echo "Deploying to PRODUCTION environment at ${env.PROD_URL}..."
                sh '''
                    sudo fuser -k ${CURRENT_PORT}/tcp || true
                    . venv/bin/activate
                    nohup python3 app.py --port=${CURRENT_PORT} > prod_app.log 2>&1 &
                '''
            }
        }
    }

    post {
        always {
            echo 'Purging working directory allocations to clear file system configurations safely.'
            cleanWs()
        }
        success {
            echo 'I succeeded!'
        }
        unstable {
            echo 'I am unstable :/'
        }
        failure {
            echo 'I failed :('
            script {
                try {
                    if (env.NOTIFICATION_EMAIL) {
                        mail to: "${env.NOTIFICATION_EMAIL}",
                             subject: "Failed Pipeline: ${currentBuild.fullDisplayName}",
                             body: "Something is wrong with ${env.BUILD_URL}"
                    } else {
                        echo "No NOTIFICATION_EMAIL environment variable set. Skipping email dispatch."
                    }
                } catch (Exception mailError) {
                    echo "Unable to dispatch SMTP alert notification: ${mailError.getMessage()}"
                }
            }
        }
        changed {
            echo 'Things were different before...'
        }
    }
}
