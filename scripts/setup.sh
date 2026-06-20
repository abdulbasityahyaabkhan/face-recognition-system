#!/bin/bash

# Face Recognition System Setup Script
# This script automates the initial setup for development

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Face Recognition System Setup${NC}"
echo -e "${GREEN}================================${NC}"

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if ! command -v python3.11 &> /dev/null; then
    echo -e "${RED}Python 3.11 not found. Please install Python 3.11${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python 3.11 found${NC}"

# Check PostgreSQL
echo -e "${YELLOW}Checking PostgreSQL...${NC}"
if ! command -v psql &> /dev/null; then
    echo -e "${RED}PostgreSQL not found. Please install PostgreSQL${NC}"
    exit 1
fi
echo -e "${GREEN}✓ PostgreSQL found${NC}"

# Check Redis
echo -e "${YELLOW}Checking Redis...${NC}"
if ! command -v redis-cli &> /dev/null; then
    echo -e "${RED}Redis not found. Please install Redis${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Redis found${NC}"

# Create .env file if not exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}Please edit .env with your configuration${NC}"
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Setup backend
echo -e "${YELLOW}Setting up backend...${NC}"

cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3.11 -m venv venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
else
    echo -e "${GREEN}✓ Virtual environment already exists${NC}"
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Create PostgreSQL database
echo -e "${YELLOW}Setting up PostgreSQL database...${NC}"
read -p "Enter PostgreSQL password (default: postgres): " pg_password
pg_password=${pg_password:-postgres}

# Check if database exists
if ! psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'face_recognition_db'" | grep -q 1; then
    echo -e "${YELLOW}Creating database...${NC}"
    psql -U postgres -c "CREATE DATABASE face_recognition_db;"
    psql -U postgres -d face_recognition_db -c "CREATE USER face_user WITH PASSWORD '$pg_password';"
    psql -U postgres -d face_recognition_db -c "ALTER ROLE face_user SET client_encoding TO 'utf8';"
    psql -U postgres -d face_recognition_db -c "ALTER ROLE face_user SET default_transaction_isolation TO 'read committed';"
    psql -U postgres -d face_recognition_db -c "GRANT ALL PRIVILEGES ON DATABASE face_recognition_db TO face_user;"
    echo -e "${GREEN}✓ Database created${NC}"
else
    echo -e "${GREEN}✓ Database already exists${NC}"
fi

# Run migrations
echo -e "${YELLOW}Running database migrations...${NC}"
python manage.py migrate
echo -e "${GREEN}✓ Migrations completed${NC}"

# Collect static files
echo -e "${YELLOW}Collecting static files...${NC}"
python manage.py collectstatic --noinput
echo -e "${GREEN}✓ Static files collected${NC}"

# Create superuser
echo -e "${YELLOW}Creating superuser...${NC}"
python manage.py createsuperuser
echo -e "${GREEN}✓ Superuser created${NC}"

cd ..

# Setup frontend
echo -e "${YELLOW}Setting up frontend...${NC}"

if [ -d "frontend" ]; then
    cd frontend
    
    # Check if node_modules exists
    if [ ! -d "node_modules" ]; then
        echo -e "${YELLOW}Installing npm dependencies...${NC}"
        npm install
        echo -e "${GREEN}✓ Frontend dependencies installed${NC}"
    else
        echo -e "${GREEN}✓ Frontend dependencies already installed${NC}"
    fi
    
    cd ..
else
    echo -e "${YELLOW}Frontend directory not found. Skipping frontend setup${NC}"
fi

# Create necessary directories
echo -e "${YELLOW}Creating necessary directories...${NC}"
mkdir -p backend/logs
mkdir -p backend/media
mkdir -p backend/staticfiles
mkdir -p ml_models/weights
mkdir -p data/faiss_indexes
echo -e "${GREEN}✓ Directories created${NC}"

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}================================${NC}"

echo -e "${YELLOW}Next steps:${NC}"
echo "1. Edit .env file with your configuration"
echo "2. Start PostgreSQL: sudo systemctl start postgresql"
echo "3. Start Redis: sudo systemctl start redis-server"
echo "4. Start Django: cd backend && source venv/bin/activate && python manage.py runserver"
echo "5. Start Celery (new terminal): cd backend && source venv/bin/activate && celery -A config worker"
echo "6. Start Frontend (new terminal): cd frontend && npm start"
echo ""
echo -e "${GREEN}Backend API: http://localhost:8000${NC}"
echo -e "${GREEN}Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}Admin Panel: http://localhost:8000/admin${NC}"
