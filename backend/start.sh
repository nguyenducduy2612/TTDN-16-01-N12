#!/bin/bash
# Quick Start Script for Backend AI Chatbot
# This script helps you setup and run the backend quickly

set -e  # Exit on error

echo "🚀 Backend AI Chatbot - Quick Start"
echo "===================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Step 1: Check Python
echo "📌 Step 1: Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python3 not found. Please install Python 3.8+${NC}"
    exit 1
fi
PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ Found: $PYTHON_VERSION${NC}"
echo ""

# Step 2: Create/Activate Virtual Environment
echo "📌 Step 2: Setting up Virtual Environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
else
    echo -e "${GREEN}✅ Virtual environment already exists${NC}"
fi

# Activate venv
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"
echo ""

# Step 3: Install Dependencies
echo "📌 Step 3: Installing Dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"
echo ""

# Step 4: Check .env file
echo "📌 Step 4: Checking Configuration..."
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠️  .env file not found${NC}"
    echo "Creating .env from template..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env file with your credentials:${NC}"
    echo "   - OPENAI_API_KEY"
    echo "   - ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD"
    echo ""
    echo "After editing .env, run this script again."
    exit 0
else
    echo -e "${GREEN}✅ .env file found${NC}"
fi
echo ""

# Step 5: Test Odoo Connection (Optional)
echo "📌 Step 5: Testing Odoo Connection..."
read -p "Do you want to test Odoo connection? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python test_odoo_connection.py
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Odoo connection test failed${NC}"
        echo "Please check your Odoo configuration in .env"
        exit 1
    fi
fi
echo ""

# Step 6: Start Server
echo "📌 Step 6: Starting Backend Server..."
echo -e "${GREEN}✅ Server starting at http://localhost:8000${NC}"
echo ""
echo "📚 API Documentation: http://localhost:8000/docs"
echo "❤️  Health Check: http://localhost:8000/api/health"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================="
echo ""

# Run server
python -m app.main
