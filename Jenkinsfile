pipeline {
    agent any

    environment {
        APP_NAME = 'aceest-fitness-app'
    }

    stages {
        stage('Repository Synchronization') {
            steps {
                echo 'Pulling application code parameters cleanly from GitHub tracking layers...'
                checkout scm
            }
        }

        stage('Docker Compression Assembly') {
            steps {
                echo 'Assembling cached container virtualization blocks on Windows Docker Desktop...'
                // This builds the container first so we can use its built-in Python environment
                bat "docker build -t %APP_NAME%:%BUILD_NUMBER% ."
            }
        }

        stage('Static Lint Analysis') {
            steps {
                echo 'Validating Python syntax compilation structure inside the Docker Container...'
                // OPTIMIZATION: Runs the compilation check using the container's internal Python
                bat "docker run --rm %APP_NAME%:%BUILD_NUMBER% python -m py_compile app.py"
            }
        }

        stage('Automated Pytest Execution') {
            steps {
                echo 'Invoking component assertion tests inside clean container context...'
                bat "docker run --rm %APP_NAME%:%BUILD_NUMBER% pytest test_app.py"
            }
        }
    }

    post {
        always {
            echo 'Purging Windows working directory allocations to clear file system locking processes.'
            cleanWs()
        }
    }
}
