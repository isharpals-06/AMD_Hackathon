@echo off
title AMD Multi-Model Fallback Router Control Panel
echo ==========================================================
echo       AMD Multi-Model Fallback Router Startup
echo ==========================================================
echo.

:: 1. Verify and start Ollama if not running
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%ERRORLEVEL%"=="0" (
    echo [INFO] Ollama is already running.
) else (
    echo [INFO] Ollama is not running. Starting Ollama Serve in background...
    start "" ollama serve
    echo [INFO] Waiting 3 seconds for Ollama to initialize...
    timeout /t 3 /nobreak >nul
)

:: 2. Start Backend API
echo [INFO] Starting FastAPI Backend on http://localhost:8000...
start "AMD Router Backend" cmd /k ".venv\Scripts\uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

:: 3. Start Frontend Dashboard
echo [INFO] Starting Vite Frontend on http://localhost:5173...
start "AMD Router Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ==========================================================
echo  All services triggered!
echo   - Backend API: http://localhost:8000
echo   - Frontend Dashboard: http://localhost:5173
echo   - Health Check: http://localhost:8000/health
echo.
echo  Press any key to close this manager window.
echo  (The backend and frontend windows will remain open).
echo ==========================================================
pause >nul
