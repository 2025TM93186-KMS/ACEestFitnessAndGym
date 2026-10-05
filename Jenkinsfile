pipeline {
    agent any

    environment {
        APP_NAME     = 'aceest-fitness-app'
        DEV_URL      = "http://localhost:5001"
        TEST_URL     = "http://localhost:5002"
        STAGE_URL    = "http://localhost:5003"
        PROD_URL     = "http://localhost:5004"

        // Dynamic target mapping depending on the current branch name
        CURRENT_PORT = "${env.BRANCH_NAME == 'Develop' ? '5001' : env.BRANCH_NAME == 'Test' ? '5002' : env.BRANCH_NAME == 'Stage' ? '5003' : '5004'}"
    }

    stages {
        stage('Initialize') {
            steps {
                echo "Starting the automation pipeline for: ${env.APP_NAME}"
            }
        }

        stage('Repository Synchronization') {
            steps {
                echo 'Pulling application code parameters cleanly from GitHub tracking layers...'
                checkout scm
            }
        }

        stage('Docker Compression Assembly') {
            steps {
                echo 'Assembling cached container virtualization blocks on Windows Docker Desktop...'
                bat "docker build -t %APP_NAME%:%BUILD_NUMBER% ."
            }
        }

        stage('Static Lint Analysis') {
            steps {
                echo 'Validating Python syntax compilation structure inside the Docker Container...'
                bat "docker run --rm %APP_NAME%:%BUILD_NUMBER% python -m py_compile app.py"
            }
        }

        stage('Automated Pytest Execution') {
            steps {
                echo 'Invoking component assertion tests inside clean container context...'
                bat "docker run --rm %APP_NAME%:%BUILD_NUMBER% pytest test_app.py"
            }
        }

        stage('Code Quality Inspection (SonarQube)') {
            steps {
                script {
                    try {
                        // 1. Attempts to find the scanner via global tool definition configuration
                        def scannerHome = tool 'SonarScanner'
                        
                        withSonarQubeEnv('SonarQube') {
                            bat """
                            "${scannerHome}\\bin\\sonar-scanner.bat" ^
                              -Dsonar.projectKey=${env.SONARCLOUD_PROJECT_KEY} ^
                              -Dsonar.organization=${env.SONARCLOUD_ORGANIZATION_KEY} ^
                              -Dsonar.sources=. ^
                              -Dsonar.python.version=3.10
                            """
                        }
                    } catch (Exception e) {
                        // 2. Safe localized fallback if Jenkins tool name definitions are unconfigured or mismatching
                        echo "Global 'SonarScanner' tool profile not found. Attempting systemic environment path fallback..."
                        withSonarQubeEnv('SonarQube') {
                            bat """
                            sonar-scanner.bat ^
                              -Dsonar.projectKey=${env.SONARCLOUD_PROJECT_KEY} ^
                              -Dsonar.organization=${env.SONARCLOUD_ORGANIZATION_KEY} ^
                              -Dsonar.sources=. ^
                              -Dsonar.python.version=3.10
                            """
                        }
                    }

                    // 3. Pauses to evaluate the Quality Gate response status thresholds
                    timeout(time: 10, unit: 'MINUTES') {
                        def qg = waitForQualityGate()
                        if (qg.status != 'OK') {
                            error "Pipeline aborted due to Quality Gate Failure! Status: ${qg.status}"
                        }
                    }
                }
            }
        }

        stage('Deploy to Dev') {
            when { branch 'Develop' }
            steps {
                echo "Deploying to DEV environment at ${env.DEV_URL}..."
                bat """
                FOR /F "tokens=*" %%i IN ('docker ps -q --filter "publish=%CURRENT_PORT%"') DO docker stop %%i
                docker run -d -p %CURRENT_PORT%:%CURRENT_PORT% --name %APP_NAME%-dev-%BUILD_NUMBER% %APP_NAME%:%BUILD_NUMBER% python app.py --port=%CURRENT_PORT%
                """
            }
        }

        stage('Deploy to Test') {
            when { branch 'Test' }
            steps {
                echo "Deploying to TEST environment at ${env.TEST_URL}..."
                bat """
                FOR /F "tokens=*" %%i IN ('docker ps -q --filter "publish=%CURRENT_PORT%"') DO docker stop %%i
                docker run -d -p %CURRENT_PORT%:%CURRENT_PORT% --name %APP_NAME%-test-%BUILD_NUMBER% %APP_NAME%:%BUILD_NUMBER% python app.py --port=%CURRENT_PORT%
                """
            }
        }

        stage('Deploy to Stage') {
            when { branch 'Stage' }
            steps {
                echo "Deploying to STAGING environment at ${env.STAGE_URL}..."
                bat """
                FOR /F "tokens=*" %%i IN ('docker ps -q --filter "publish=%CURRENT_PORT%"') DO docker stop %%i
                docker run -d -p %CURRENT_PORT%:%CURRENT_PORT% --name %APP_NAME%-stage-%BUILD_NUMBER% %APP_NAME%:%BUILD_NUMBER% python app.py --port=%CURRENT_PORT%
                """
            }
        }

        stage('Deploy to Prod') {
            when { branch 'Main' } 
            steps {
                echo "Deploying to PRODUCTION environment at ${env.PROD_URL}..."
                bat """
                FOR /F "tokens=*" %%i IN ('docker ps -q --filter "publish=%CURRENT_PORT%"') DO docker stop %%i
                docker run -d -p %CURRENT_PORT%:%CURRENT_PORT% --name %APP_NAME%-prod-%BUILD_NUMBER% %APP_NAME%:%BUILD_NUMBER% python app.py --port=%CURRENT_PORT%
                """
            }
        }
    }

    post {
        always {
            echo 'Purging Windows working directory allocations to clear file system locking processes.'
            cleanWs()
        }
        success {
            echo 'I succeeded!'
        }
        unstable {
            echo 'I am unstable :/'
        }
        failure {
            echo "Pipeline failure alert: Something is wrong with execution block link: ${env.BUILD_URL}"
            
            // FIXED: Wrapped the try-catch block inside a script step so Jenkins parses it cleanly
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
