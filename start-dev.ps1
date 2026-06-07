# start-dev.ps1
# PowerShell script to run all OrchardDB microservices locally in separate console windows.

Write-Host "====================================================" -ForegroundColor Green
Write-Host "      Starting OrchardDB Developer Workspace        " -ForegroundColor Green
Write-Host "====================================================" -ForegroundColor Green

# 1. Start VDB Service (Port 8000)
Write-Host "Starting VDB Service (Port 8000)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd vdb_service; .\\venv\\Scripts\\activate; python run.py"

# 2. Start Auth Service (Port 8001)
Write-Host "Starting Auth Service (Port 8001)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd auth_service; .\\venv\\Scripts\\activate; python run.py"

# 3. Start PDF Service API (Port 8002)
Write-Host "Starting PDF Service API (Port 8002)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd pdf_service; .\\venv\\Scripts\\activate; python run.py"

# 4. Start PDF Service Celery Worker
Write-Host "Starting PDF Celery Worker..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd pdf_service; .\\venv\\Scripts\\activate; python -m celery -A app.worker.celery_app worker --loglevel=info"

# 5. Start Visualisation Service (Port 8003)
Write-Host "Starting Visualisation Service (Port 8003)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd visualisation_service; .\\venv\\Scripts\\activate; python run.py"

# 6. Start Frontend (Vite dev server)
Write-Host "Starting Frontend (Vite dev server)..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "----------------------------------------------------" -ForegroundColor Yellow
Write-Host "All services triggered! Check the individual console windows for logs." -ForegroundColor Green
Write-Host "Note: Ensure your local Postgres (5432), Redis (6379), and ChromaDB (8010) are running." -ForegroundColor Yellow
Write-Host "====================================================" -ForegroundColor Green
