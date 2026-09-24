@echo off
title AI Mail Application — Quick Start
echo ========================================================
echo         AI-POWERED MAIL WEB APPLICATION
echo ========================================================
echo.

set ROOT_DIR=%~dp0
cd /d "%ROOT_DIR%"

echo [1/3] Checking Backend Environment...
if not exist "backend\venv\Scripts\activate.bat" (
    echo Creating Python virtual environment...
    python -m venv backend\venv
    call backend\venv\Scripts\activate.bat
    echo Installing backend dependencies...
    pip install -r backend\requirements.txt
) else (
    echo Backend virtual environment found.
)

if not exist "backend\.env" (
    echo Creating backend\.env from .env.example...
    copy backend\.env.example backend\.env
)

echo [2/3] Checking Frontend Environment...
if not exist "frontend\node_modules" (
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
) else (
    echo Frontend dependencies found.
)

if not exist "frontend\.env.local" (
    echo Creating frontend\.env.local from .env.example...
    copy frontend\.env.example frontend\.env.local
)

echo.
echo [3/3] Launching AI Mail Application Services...
echo.
echo  * FastAPI Backend:   http://localhost:8000 (API & Docs: /docs)
echo  * Next.js Frontend:  http://localhost:3000
echo.

:: Start Backend in a new command window
start "AI Mail Backend (FastAPI)" cmd /k "cd /d "%ROOT_DIR%backend" && call venv\Scripts\activate.bat && uvicorn app.main:app --reload --port 8000"

:: Start Frontend in a new command window
start "AI Mail Frontend (Next.js)" cmd /k "cd /d "%ROOT_DIR%frontend" && npm run dev"

echo Services started! You can close this launcher window.
echo Open http://localhost:3000 in your browser to access the app.
pause
