# Development Guide

## Development Workflow

### Code Style Guidelines

#### Python
- **Style Guide**: PEP 8
- **Line Length**: 100 characters
- **Imports**: Alphabetically sorted, separated by sections
- **Naming**:
  - Classes: PascalCase
  - Functions/Variables: snake_case
  - Constants: UPPER_SNAKE_CASE

#### Django Specific
- **Models**: Plural in app names, models in singular
- **Views**: Class-based views preferred for complex logic
- **Serializers**: One serializer per model (nested where appropriate)
- **Tests**: One test file per module

#### JavaScript/React
- **Style Guide**: Airbnb JavaScript
- **Components**: PascalCase for files, arrow functions
- **State Management**: React Context or Redux
- **Formatting**: Prettier configured

### Testing

#### Backend Testing

**Run all tests**:
```bash
pytest
```

**Run specific test**:
```bash
pytest tests/unit/test_models.py::TestUserModel
```

**Run with coverage**:
```bash
pytest --cov=backend tests/
```

**Test structure**:
```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_serializers.py
│   └── test_views.py
├── integration/
│   └── test_api_endpoints.py
└── conftest.py  # Shared fixtures
```

#### Frontend Testing

```bash
# Run tests
npm test

# Run with coverage
npm test -- --coverage

# Run specific test file
npm test -- TestComponent
```

### Code Quality Tools

**Black** (Code Formatter):
```bash
black backend/
```

**Flake8** (Linter):
```bash
flake8 backend/
```

**iSort** (Import Sorting):
```bash
isort backend/
```

**Pylint** (Code Analysis):
```bash
pylint backend/
```

**Run all checks**:
```bash
bash scripts/check_code_quality.sh
```

## Git Workflow

### Branch Naming
```
feature/feature-name           # New feature
bugfix/bug-description         # Bug fix
hotfix/urgent-issue            # Production hotfix
docs/documentation-update      # Documentation
refactor/refactoring-task      # Code refactoring
```

### Commit Messages
```
[TYPE] Brief description

Detailed explanation if needed.

Type: feat, fix, docs, style, refactor, test, chore
```

### Example
```
[feat] Add face detection API endpoint

- Implement RetinaFace detection
- Add input validation
- Return coordinates and confidence scores
```

## Local Development Setup

### Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Rebuild images
docker-compose up -d --build
```

### Manual Setup

**Backend**:
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

**Celery Worker**:
```bash
cd backend
source venv/bin/activate
celery -A config worker --loglevel=info
```

**Frontend**:
```bash
cd frontend
npm install
npm start
```

## Database Management

### Creating Migrations

```bash
# Create new migration
python backend/manage.py makemigrations

# Apply migrations
python backend/manage.py migrate

# Show migration status
python backend/manage.py showmigrations
```

### Database Reset (Development Only)

```bash
# Delete all data
python backend/manage.py flush

# Recreate from scratch
python backend/manage.py migrate
```

## Environment Variables

Create `.env` file from `.env.example`:

```bash
cp .env.example .env
```

Key variables for development:
```
DEBUG=True
SECRET_KEY=your-secret-key-for-development
DB_NAME=face_recognition_db
DB_USER=postgres
DB_PASSWORD=postgres
REDIS_HOST=localhost
```

## API Documentation

### Accessing API Docs

**Swagger UI**: http://localhost:8000/api/schema/swagger-ui/  
**ReDoc**: http://localhost:8000/api/schema/redoc/

### Testing APIs

**Using cURL**:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     http://localhost:8000/api/students/
```

**Using Postman**:
1. Import API collection from `/docs/postman_collection.json`
2. Set environment variables
3. Test endpoints

## Performance Profiling

### Django Debug Toolbar

Automatically enabled in DEBUG mode.  
Visit: http://localhost:8000/

### Database Query Profiling

```python
# In management command or script
from django.test.utils import override_settings
from django.db import connection, reset_queries

@override_settings(DEBUG=True)
def profile_queries():
    # Your code here
    print(len(connection.queries))
    for query in connection.queries:
        print(query['sql'])
```

### Celery Task Profiling

```bash
# Monitor Celery tasks
celery -A config inspect active

# Check worker stats
celery -A config inspect stats
```

## Debugging

### Django Debug Mode

Enable in `.env`:
```
DEBUG=True
```

### Python Debugger

```python
# In your code
import pdb; pdb.set_trace()

# Or modern alternative
import breakpoint; breakpoint()
```

### Celery Debugging

```bash
# Log level debug
celery -A config worker --loglevel=debug
```

## Documentation

### Docstring Format (Google Style)

```python
def function_name(param1, param2):
    """Brief description.
    
    Longer description if needed.
    
    Args:
        param1 (str): Description of param1
        param2 (int): Description of param2
        
    Returns:
        bool: Description of return value
        
    Raises:
        ValueError: Description of error condition
        
    Example:
        >>> function_name('test', 42)
        True
    """
    pass
```

### API Documentation

Document all endpoints with:
- Endpoint URL
- HTTP method
- Required parameters
- Response schema
- Error responses
- Example usage

## Common Commands

### Backend
```bash
# Create superuser
python backend/manage.py createsuperuser

# Shell access
python backend/manage.py shell

# Database
python backend/manage.py dbshell

# Static files
python backend/manage.py collectstatic
```

### Frontend
```bash
# Build for production
npm run build

# Run linter
npm run lint

# Format code
npm run format
```

### Docker
```bash
# View all images
docker images

# View containers
docker ps -a

# View logs
docker logs -f <container_id>

# Execute command in container
docker exec -it <container_id> bash
```

## Phase 1 Completion Checklist

✅ Development environment set up  
✅ Code quality tools configured  
✅ Testing framework ready  
✅ Git workflow documented  
✅ Database management tools available  

**Next Phase**: Phase 2 - PostgreSQL Database Models
