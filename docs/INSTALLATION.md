# Installation Guide - Phase 1

## Prerequisites

### System Requirements
- OS: Ubuntu 22.04 LTS (or equivalent Linux/macOS)
- Python: 3.11+
- RAM: 8GB minimum (16GB recommended)
- GPU: NVIDIA (optional, for acceleration)
- Disk Space: 50GB+ (for models and data)

### Required Software
- Docker & Docker Compose (recommended)
- PostgreSQL 15+
- Redis
- Node.js 18+ (for frontend)
- Git

### Installation by OS

#### Ubuntu 22.04 LTS
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev

# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Install Redis
sudo apt install -y redis-server

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### macOS
```bash
# Using Homebrew
brew install python@3.11
brew install postgresql
brew install redis
brew install docker
brew install node@18

# Install Docker Desktop from https://www.docker.com/products/docker-desktop
```

#### Windows
```bash
# Using Windows Subsystem for Linux 2 (WSL2)
# Install WSL2 with Ubuntu 22.04

# Then follow Ubuntu installation steps above
```

## Installation Steps

### Step 1: Clone Repository
```bash
git clone https://github.com/abdulbasityahyaabkhan/face-recognition-system.git
cd face-recognition-system
```

### Step 2: Create Environment File
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```bash
nano .env
```

### Step 3: Option A - Docker Compose (Recommended)

**Advantages**:
- All services in containers
- No system dependency conflicts
- Easy to scale
- Production-ready

**Steps**:
```bash
# Build and start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f backend

# Run migrations (inside container)
docker-compose exec backend python backend/manage.py migrate

# Create superuser
docker-compose exec backend python backend/manage.py createsuperuser
```

**Accessing Services**:
- Backend API: http://localhost:8000
- Admin Panel: http://localhost:8000/admin
- Frontend: http://localhost:3000
- Flower (Celery): http://localhost:5555

### Step 3: Option B - Local Development Setup

**Prerequisites**:
- PostgreSQL running locally
- Redis running locally
- Python 3.11 venv

**Steps**:

#### 1. Set up Backend
```bash
cd backend

# Create virtual environment
python3.11 -m venv venv

# Activate venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create PostgreSQL database
sudo -u postgres psql -c "CREATE DATABASE face_recognition_db;"
sudo -u postgres psql -c "CREATE USER face_user WITH PASSWORD 'your_password';"
sudo -u postgres psql -c "ALTER ROLE face_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE face_user SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE face_user SET default_transaction_deferrable TO on;"
sudo -u postgres psql -c "ALTER ROLE face_user SET default_transaction_deferrable TO on;"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE face_recognition_db TO face_user;"

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Start development server
python manage.py runserver 0.0.0.0:8000
```

#### 2. Start Celery Worker (New Terminal)
```bash
cd backend
source venv/bin/activate
celery -A config worker --loglevel=info
```

#### 3. Start Celery Beat (New Terminal)
```bash
cd backend
source venv/bin/activate
celery -A config beat --loglevel=info
```

#### 4. Start Flower (New Terminal)
```bash
cd backend
source venv/bin/activate
celery -A config flower --port=5555
```

#### 5. Setup Frontend
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm start
```

## Verification

### 1. Check Backend API
```bash
curl http://localhost:8000/api/
```

Expected response:
```json
{
  "status": "ok",
  "version": "1.0.0"
}
```

### 2. Check Database Connection
```bash
# Via Docker
docker-compose exec db psql -U postgres -d face_recognition_db -c "\dt"

# Or locally
psql -U face_user -d face_recognition_db -c "\dt"
```

### 3. Check Redis Connection
```bash
redis-cli ping
```

Expected: `PONG`

### 4. Check Admin Panel
Visit: http://localhost:8000/admin

Login with superuser credentials created earlier.

### 5. Check Frontend
Visit: http://localhost:3000

Should see React app loading.

## Project Structure Created

```
face-recognition-system/
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore file
├── README.md                    # Project overview
├── docker-compose.yml           # Docker Compose configuration
├── backend/
│   └── requirements.txt          # Python dependencies
├── docker/
│   ├── Dockerfile.backend       # Backend container config
│   └── Dockerfile.frontend      # Frontend container config
├── docs/
│   ├── ARCHITECTURE.md          # System architecture
│   └── INSTALLATION.md          # This file
├── frontend/                    # React application (to be created)
├── ml_models/                   # ML models directory (to be created)
├── scripts/                     # Utility scripts (to be created)
└── tests/                       # Test suite (to be created)
```

## Troubleshooting

### Issue: Port Already in Use
```bash
# Find process using port
sudo lsof -i :8000

# Kill process
sudo kill -9 <PID>
```

### Issue: PostgreSQL Connection Error
```bash
# Check PostgreSQL service
sudo systemctl status postgresql

# Start PostgreSQL
sudo systemctl start postgresql
```

### Issue: Redis Connection Error
```bash
# Check Redis service
sudo systemctl status redis-server

# Start Redis
sudo systemctl start redis-server
```

### Issue: Docker Permission Denied
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Issue: Memory Issues with Docker
```bash
# Increase Docker memory limit
docker system prune -a  # Clean up unused resources
```

## Next Steps

1. ✅ Verify all services are running
2. ✅ Access admin panel at http://localhost:8000/admin
3. ✅ Create test user accounts
4. ⏭️ Proceed to Phase 2: PostgreSQL Database Models

## Support

For issues or questions:
1. Check logs: `docker-compose logs <service>`
2. Review error messages carefully
3. Consult documentation in `/docs/`
4. Open GitHub issue with detailed error information
