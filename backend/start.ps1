# Quick Start - Windows PowerShell
# Script để chạy backend trên Windows

Write-Host "🚀 Backend AI Chatbot - Quick Start" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Get script directory
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $SCRIPT_DIR

# Step 1: Check Python
Write-Host "📌 Step 1: Checking Python..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Step 2: Create/Activate Virtual Environment
Write-Host "📌 Step 2: Setting up Virtual Environment..." -ForegroundColor Yellow
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
} else {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
}

# Activate venv
& "venv\Scripts\Activate.ps1"
Write-Host "✅ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Step 3: Install Dependencies
Write-Host "📌 Step 3: Installing Dependencies..." -ForegroundColor Yellow
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
Write-Host "✅ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Step 4: Check .env file
Write-Host "📌 Step 4: Checking Configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Write-Host "⚠️  .env file not found" -ForegroundColor Yellow
    Write-Host "Creating .env from template..."
    Copy-Item .env.example .env
    Write-Host "⚠️  Please edit .env file with your credentials:" -ForegroundColor Yellow
    Write-Host "   - OPENAI_API_KEY"
    Write-Host "   - ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD"
    Write-Host ""
    Write-Host "After editing .env, run this script again."
    exit 0
} else {
    Write-Host "✅ .env file found" -ForegroundColor Green
}
Write-Host ""

# Step 5: Test Odoo Connection (Optional)
Write-Host "📌 Step 5: Testing Odoo Connection..." -ForegroundColor Yellow
$response = Read-Host "Do you want to test Odoo connection? (y/n)"
if ($response -eq "y" -or $response -eq "Y") {
    python test_odoo_connection.py
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Odoo connection test failed" -ForegroundColor Red
        Write-Host "Please check your Odoo configuration in .env"
        exit 1
    }
}
Write-Host ""

# Step 6: Start Server
Write-Host "📌 Step 6: Starting Backend Server..." -ForegroundColor Yellow
Write-Host "✅ Server starting at http://localhost:8000" -ForegroundColor Green
Write-Host ""
Write-Host "📚 API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host "❤️  Health Check: http://localhost:8000/api/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the server"
Write-Host "=================================="
Write-Host ""

# Run server
python -m app.main
