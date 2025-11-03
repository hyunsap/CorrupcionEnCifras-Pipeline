#!/bin/bash

# Quick setup script for corrupcion-pipeline
# Run this after copying all files to set up the project

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Corrupción Pipeline Setup"
echo "=========================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose found${NC}"

# Create required directories
echo ""
echo "Creating directories..."
mkdir -p data logs initdb
echo -e "${GREEN}✓ Created data/, logs/, and initdb/ directories${NC}"

# Make scripts executable
echo ""
echo "Making scripts executable..."
chmod +x run_pipeline.sh 2>/dev/null || echo "run_pipeline.sh not found"
chmod +x check_status.sh 2>/dev/null || echo "check_status.sh not found"
echo -e "${GREEN}✓ Scripts are now executable${NC}"

# Check for required files
echo ""
echo "Checking for required files..."

REQUIRED_FILES=(
    "docker-compose.yml"
    "Dockerfile.scraper"
    "Dockerfile.etl"
    "Dockerfile.loader"
    "run_scrapers.py"
    "scraper_entramite.py"
    "scraper_completas.py"
    "scraper_jueces.py"
    "transform_expedientes.py"
    "cargar_etl.py"
    "requirements.txt"
)

MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${YELLOW}⚠${NC} $file (MISSING)"
        MISSING_FILES+=("$file")
    fi
done

# Check for init.sql
if [ -f "initdb/init.sql" ]; then
    echo -e "${GREEN}✓${NC} initdb/init.sql"
else
    echo -e "${YELLOW}⚠${NC} initdb/init.sql (MISSING)"
    MISSING_FILES+=("initdb/init.sql")
fi

if [ ${#MISSING_FILES[@]} -gt 0 ]; then
    echo ""
    echo -e "${YELLOW}⚠ Warning: Missing required files:${NC}"
    for file in "${MISSING_FILES[@]}"; do
        echo "  - $file"
    done
    echo ""
    echo "Please add these files before proceeding."
    exit 1
fi

echo ""
echo -e "${GREEN}✓ All required files present${NC}"

# Create .env from .env.example if it doesn't exist
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    echo ""
    echo "Creating .env file from .env.example..."
    cp .env.example .env
    echo -e "${GREEN}✓ Created .env file${NC}"
fi

# Initialize git if not already initialized
if [ ! -d ".git" ]; then
    echo ""
    read -p "Initialize git repository? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git init
        echo -e "${GREEN}✓ Git repository initialized${NC}"
        echo ""
        echo "Next steps for git:"
        echo "1. git add ."
        echo "2. git commit -m 'Initial commit'"
        echo "3. Create a GitHub repository"
        echo "4. git remote add origin <your-repo-url>"
        echo "5. git push -u origin main"
    fi
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "=========================================="
echo ""
echo "Next steps:"
echo ""
echo "1. Review and update docker-compose.yml (especially database password)"
echo "2. Test the pipeline:"
echo "   docker-compose up -d postgres"
echo "   ./run_pipeline.sh"
echo ""
echo "3. Start the scheduler for automatic runs:"
echo "   docker-compose up -d scheduler"
echo ""
echo "4. Check status anytime:"
echo "   ./check_status.sh"
echo ""