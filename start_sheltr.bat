@echo off
REM Sheltr Application Startup Script (Batch version)
REM This script starts both the backend API and frontend Expo app

echo ========================================
echo        SHELTR APPLICATION STARTUP
echo ========================================
echo.

cd /d "%~dp0"

REM Start Backend
echo [1/2] Starting Backend API Server...
cd backend
start "Sheltr Backend" cmd /k "python -m venv .venv 2>nul & .venv\Scripts\activate & pip install -q -r requirements.txt & python sheltr_backend.py"
echo Backend server starting on http://localhost:5000
cd ..

REM Wait for backend to initialize
timeout /t 3 /nobreak >nul

REM Start Frontend
echo [2/2] Starting Frontend Expo Server...
cd SheltrFE
start "Sheltr Frontend" cmd /k "npm install >nul 2>&1 & npx expo start"
echo Frontend server starting
cd ..

echo.
echo ========================================
echo    SHELTR APPLICATION STARTED
echo ========================================
echo.
echo Backend API:  http://localhost:5000
echo Frontend:     Check the Expo window for QR code
echo.
echo To stop: Close both command windows
echo.
pause
