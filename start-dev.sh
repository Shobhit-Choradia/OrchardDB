#!/bin/bash

# start-dev.sh
# Shell script to run all OrchardDB microservices locally in background processes.

echo "===================================================="
echo "      Starting OrchardDB Developer Workspace        "
echo "===================================================="

# Trap ctrl-c and kill all child processes
trap "kill 0" EXIT

# 1. Start VDB Service (Port 8000)
echo "Starting VDB Service (Port 8000)..."
(cd vdb_service && source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null; python run.py) &

# 2. Start Auth Service (Port 8001)
echo "Starting Auth Service (Port 8001)..."
(cd auth_service && source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null; python run.py) &

# 3. Start PDF Service API (Port 8002)
echo "Starting PDF Service API (Port 8002)..."
(cd pdf_service && source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null; python run.py) &

# 4. Start PDF Service Celery Worker
echo "Starting PDF Celery Worker..."
(cd pdf_service && source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null; python -m celery -A app.worker.celery_app worker --loglevel=info) &

# 5. Start Visualisation Service (Port 8003)
echo "Starting Visualisation Service (Port 8003)..."
(cd visualisation_service && source venv/bin/activate 2>/dev/null || source venv/Scripts/activate 2>/dev/null; python run.py) &

# 6. Start Frontend (Vite dev server)
echo "Starting Frontend (Vite dev server)..."
(cd frontend && npm run dev) &

echo "----------------------------------------------------"
echo "All services started! Press Ctrl+C to terminate all processes."
echo "Note: Ensure your local Postgres (5432), Redis (6379), and ChromaDB (8010) are running."
echo "===================================================="

# Wait for all background processes to finish
wait
