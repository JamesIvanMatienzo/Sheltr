#!/usr/bin/env pwsh
# Sheltr Application Startup Script
# This script starts both the backend API and frontend Expo app

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "       SHELTR APPLICATION STARTUP       " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $SCRIPT_DIR

# Check if Python is installed
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8 or higher." -ForegroundColor Red
    exit 1
}

# Check if Node.js is installed
Write-Host "[2/6] Checking Node.js installation..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version 2>&1
    Write-Host "✓ Node.js found: $nodeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install Node.js 18 or higher." -ForegroundColor Red
    exit 1
}

# Setup Python virtual environment and install dependencies
Write-Host "[3/6] Setting up Python backend..." -ForegroundColor Yellow
Set-Location "$SCRIPT_DIR\backend"

if (-not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..." -ForegroundColor Cyan
    python -m venv .venv
}

Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& ".\.venv\Scripts\Activate.ps1"

Write-Host "Installing Python dependencies..." -ForegroundColor Cyan
pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "✗ Failed to install Python dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Backend dependencies installed" -ForegroundColor Green

# Setup Node.js frontend
Write-Host "[4/6] Setting up React Native frontend..." -ForegroundColor Yellow
Set-Location "$SCRIPT_DIR\SheltrFE"

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing Node.js dependencies..." -ForegroundColor Cyan
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to install Node.js dependencies" -ForegroundColor Red
        exit 1
    }
}
Write-Host "✓ Frontend dependencies installed" -ForegroundColor Green

# Start the backend server in a new window
Write-Host "[5/6] Starting backend API server..." -ForegroundColor Yellow
Set-Location "$SCRIPT_DIR\backend"

$backendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '.\.venv\Scripts\Activate.ps1'; python sheltr_backend.py" -PassThru -WindowStyle Normal
Write-Host "✓ Backend server starting on http://localhost:5000" -ForegroundColor Green
Write-Host "  Backend PID: $($backendJob.Id)" -ForegroundColor Gray

# Wait a moment for backend to initialize
Start-Sleep -Seconds 3

# Start the frontend Expo server in a new window
Write-Host "[6/6] Starting frontend Expo server..." -ForegroundColor Yellow
Set-Location "$SCRIPT_DIR\SheltrFE"

$frontendJob = Start-Process powershell -ArgumentList "-NoExit", "-Command", "npx expo start" -PassThru -WindowStyle Normal
Write-Host "✓ Frontend server starting" -ForegroundColor Green
Write-Host "  Frontend PID: $($frontendJob.Id)" -ForegroundColor Gray

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   SHELTR APPLICATION STARTED          " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Backend API:  http://localhost:5000" -ForegroundColor Green
Write-Host "Frontend:     Check the Expo window for QR code" -ForegroundColor Green
Write-Host ""
Write-Host "To stop the application:" -ForegroundColor Yellow
Write-Host "  1. Close both PowerShell windows" -ForegroundColor Yellow
Write-Host "  2. Or press Ctrl+C in each window" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press any key to exit this launcher..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
