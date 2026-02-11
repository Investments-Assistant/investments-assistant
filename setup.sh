#!/bin/bash
# Quick start script for Investment Assistant with Poetry

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📈 Investment Assistant - Setup${NC}"
echo "=================================="

# Check for Poetry
echo "Checking for Poetry..."
if ! command -v poetry &> /dev/null; then
    echo -e "${BLUE}Poetry not found. Installing Poetry...${NC}"
    curl -sSL https://install.python-poetry.org | python3 -
    export PATH="$HOME/.local/bin:$PATH"
    echo -e "${GREEN}✓ Poetry installed${NC}"
else
    poetry_version=$(poetry --version)
    echo -e "${GREEN}✓ $poetry_version found${NC}"
fi

# Configure Poetry to use in-project virtualenvs
echo -e "\n${BLUE}Configuring Poetry...${NC}"
poetry config virtualenvs.in-project true
echo -e "${GREEN}✓ Virtualenvs configured to be created in-project${NC}"

# Install dependencies
echo -e "\n${BLUE}Installing dependencies...${NC}"
poetry install
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
echo "2. Run: poetry run streamlit run app.py"
echo ""
echo "The app will open at http://localhost:8501"
