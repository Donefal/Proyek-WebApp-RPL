@echo off
SETLOCAL ENABLEEXTENSIONS

echo ==============================
echo  FastAPI Backend Launcher
echo ==============================

REM --- Kill process using port 8000 ---
echo Checking if port 8000 is in use...
for /f "tokens=5" %%a in ('netstat -ano ^| find ":8000" ^| find "LISTENING"') do (
    echo Port 8880 is in use by PID %%a
    echo Killing process...
    taskkill /PID %%a /F >nul 2>&1
    echo Process %%a terminated.
)

REM --- Move to project root ---
echo Moving to script directory...
cd /d "%~dp0"

REM --- Activate virtual environment ---
echo Activating virtual environment...
call .venv\Scripts\activate

IF %ERRORLEVEL% NEQ 0 (
    echo Failed to activate virtual environment!
    pause
    exit /b 1
)

REM --- Move to backend folder ---
cd backend

REM --- Run FastAPI server ---
echo Starting FastAPI development server...
fastapi dev main.py --host 0.0.0.0 --port 8880

echo ==============================
echo FastAPI server stopped.
echo ==============================
pause
