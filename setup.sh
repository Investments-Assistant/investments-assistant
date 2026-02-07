#!/bin/bash
# Quick start script for Investment Assistant

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📈 Investment Assistant - Setup${NC}"
echo "=================================="

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python $python_version found"

# Create virtual environment
echo -e "\n${BLUE}Creating virtual environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
echo -e "\n${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install dependencies
echo -e "\n${BLUE}Installing dependencies...${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Setup environment file
echo -e "\n${BLUE}Setting up environment...${NC}"
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created from template${NC}"
    echo -e "\n${BLUE}⚠️  Please edit .env and add your OpenAI API key${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

echo -e "\n${GREEN}=================================="
echo "✓ Setup complete!"
echo -e "==================================${NC}"

echo -e "\n${BLUE}Next steps:${NC}"
echo "1. Edit .env with your OpenAI API key"
echo "2. Run: source venv/bin/activate"
echo "3. Run: streamlit run app.py"
echo ""
echo "The app will open at http://localhost:8501"
