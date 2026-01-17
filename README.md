# Interactive Story Generator

![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![Django](https://img.shields.io/badge/django-5.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

AI-powered interactive story generator using Django and Ollama LLM. Create engaging stories where you choose the direction at each chapter.

## Features

- **Interactive storytelling** - Make choices that shape your story
- **AI-generated content** - Powered by Ollama LLM (llama3.2:3b)
- **Multi-language support** - Russian and English stories
- **RESTful API** - Full API for integration with other applications
- **Async generation** - Background chapter generation with Celery
- **User accounts** - Each user has their own story collection

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Django 5.0, Django REST Framework |
| Task Queue | Celery + RabbitMQ |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| AI/LLM | Ollama (llama3.2:3b) |
| Containers | Docker Compose |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- 8GB+ RAM (for Ollama LLM)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/AI_story_maker.git
   cd AI_story_maker
   ```

2. **Copy environment file**
   ```bash
   cp .env.example .env
   ```

3. **Start all services**
   ```bash
   docker compose up -d
   ```

4. **Open the application**
   - Web Interface: http://localhost:8000
   - Admin Panel: http://localhost:8000/admin (admin/admin)
   - API Docs: http://localhost:8000/api/docs/

The first startup may take longer as Docker pulls images and Ollama downloads the LLM model.

## API Endpoints

### Stories API (v1)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/stories/` | GET | List user's stories |
| `/api/v1/stories/` | POST | Create new story |
| `/api/v1/stories/{id}/` | GET | Get story with chapters |
| `/api/v1/stories/{id}/` | DELETE | Delete story |
| `/api/v1/stories/{id}/chapters/` | GET | List story chapters |
| `/api/v1/stories/{id}/chapters/{id}/choice/` | POST | Select choice for chapter |

### Task Status API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/task-status/{task_id}/` | GET | Get chapter generation status |

### Health Checks

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health/` | GET | Application health check |
| `/api/health/ollama/` | GET | Ollama service health check |

## Development

### Local Setup

1. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```

2. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

3. **Start services with Docker**
   ```bash
   docker compose up db rabbitmq redis ollama -d
   ```

4. **Run migrations**
   ```bash
   python manage.py migrate
   ```

5. **Start development server**
   ```bash
   python manage.py runserver
   ```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov --cov-report=html

# Run only unit tests (skip integration)
pytest -m "not integration"

# Run only fast tests (skip slow)
pytest -m "not slow"

# Run specific test file
pytest apps/stories/tests/test_models.py
```

### Code Quality

```bash
# Lint code
ruff check .

# Format code
ruff format .

# Type checking
mypy .
```

### Pre-commit Hooks

```bash
# Install hooks
pre-commit install

# Run on all files
pre-commit run --all-files
```

## Environment Variables

| Variable | Default | Required | Description |
|----------|---------|----------|-------------|
| `SECRET_KEY` | - | Yes | Django secret key |
| `DEBUG` | `True` | No | Debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | No | Allowed hosts |
| `POSTGRES_DB` | `story_generator` | No | Database name |
| `POSTGRES_USER` | `postgres` | No | Database user |
| `POSTGRES_PASSWORD` | `postgres` | No | Database password |
| `POSTGRES_HOST` | `db` | No | Database host |
| `CELERY_BROKER_URL` | `amqp://guest:guest@rabbitmq:5672/` | No | Celery broker URL |
| `OLLAMA_HOST` | `http://ollama:11434` | No | Ollama service URL |
| `OLLAMA_MODEL` | `llama3.2:3b` | No | LLM model name |
| `DEFAULT_MAX_CHAPTERS` | `10` | No | Default max chapters per story |
| `CHAPTER_GENERATION_TIMEOUT` | `120` | No | Generation timeout (seconds) |

## Project Structure

```
AI_story_maker/
├── apps/
│   ├── accounts/          # User authentication
│   ├── api/               # Generic API views
│   └── stories/           # Core story app
│       ├── api/v1/        # REST API
│       ├── services/      # Business logic
│       ├── tests/         # Unit & integration tests
│       ├── models.py      # Data models
│       ├── tasks.py       # Celery tasks
│       └── views.py       # Django views
├── common/                # Shared utilities
├── config/                # Django configuration
├── templates/             # HTML templates
├── tests/                 # Global test fixtures
├── docker-compose.yml     # Docker orchestration
└── pyproject.toml         # Project configuration
```

## Troubleshooting

### Ollama not responding

```bash
# Check Ollama container status
docker compose logs ollama

# Restart Ollama
docker compose restart ollama

# Test connection
curl http://localhost:11434/api/tags
```

### Celery tasks not executing

```bash
# Check Celery worker logs
docker compose logs celery_worker

# Check RabbitMQ connection
docker compose logs rabbitmq

# Restart Celery
docker compose restart celery_worker
```

### Database migrations not applied

```bash
# Run migrations manually
docker compose exec web python manage.py migrate

# Check migration status
docker compose exec web python manage.py showmigrations
```

### Permission denied on volumes

```bash
# Fix permissions (Linux/Mac)
sudo chown -R $USER:$USER .

# Rebuild containers
docker compose down -v
docker compose up -d --build
```

### Out of memory errors

Ollama requires significant RAM for the LLM model. Ensure:
- At least 8GB RAM available
- Increase Docker memory limit in Docker Desktop settings

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
