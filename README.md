# Alert Management System

A Django-based web application for managing alerts with location-based associations, user profiles, and REST APIs. Includes background task scheduling for external alert fetching.

## Features

- **Alert Management**: Create, view, and manage alerts with types (info, warning, error)
- **Location Integration**: Associate alerts with geographical locations
- **User Profiles**: Automatic profile creation with optional location linking
- **REST API**: Full CRUD operations for alerts via RESTful endpoints
- **Authentication**: Login-required views with Django's built-in auth
- **Background Tasks**: Celery-based periodic alert fetching from external APIs
- **Responsive UI**: HTML templates with pagination for web interface
- **Comprehensive Testing**: Unit, integration, and performance tests
- **CI/CD**: GitHub Actions pipeline with automated testing

## Installation

### Prerequisites
- Python 3.12+
- Redis (for Celery tasks)
- Git

### Quick Start

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd zed-base
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up database**
   ```bash
   python manage.py migrate
   ```

5. **Create superuser (optional)**
   ```bash
   python manage.py createsuperuser
   ```

6. **Run development server**
   ```bash
   python manage.py runserver
   ```

Visit `http://127.0.0.1:8000/` in your browser.

## Usage

### Web Interface

- **Alerts**: View all alerts at `/alerts/`, details at `/alerts/<id>/`
- **Locations**: View locations at `/locations/`, details at `/locations/<id>/`
- **Admin**: Access Django admin at `/admin/` (requires superuser)

### API Endpoints

All API endpoints require authentication.

#### Alerts
- `GET /api/alerts/` - List all alerts (paginated)
- `POST /api/alerts/` - Create new alert
- `GET /api/alerts/<id>/` - Get alert details

#### Authentication
Use Django's session authentication or token authentication.

### Background Tasks

1. **Start Redis server**
   ```bash
   redis-server
   ```

2. **Start Celery worker**
   ```bash
   celery -A myproject worker --loglevel=info
   ```

3. **Start Celery beat (for scheduled tasks)**
   ```bash
   celery -A myproject beat --loglevel=info
   ```

4. **Schedule tasks via Django admin**
   - Go to `/admin/django_celery_beat/periodictask/`
   - Create task: `alerts.tasks.fetch_alerts_task` with arguments: `["https://api.example.com/alerts"]`

## Testing

Run the full test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=alerts
```

Test categories:
- **Unit Tests**: Isolated function testing
- **Integration Tests**: End-to-end workflow testing
- **Performance Tests**: Response time validation
- **API Tests**: REST endpoint validation

## Project Structure

```
zed-base/
├── alerts/                    # Main Django app
│   ├── migrations/           # Database migrations
│   ├── templates/            # HTML templates
│   ├── models.py             # Data models
│   ├── views.py              # View logic
│   ├── serializers.py        # API serializers
│   ├── services.py           # Business logic
│   ├── tasks.py              # Celery tasks
│   └── tests.py              # Test suite
├── myproject/                # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── celery.py
├── .github/workflows/        # CI/CD pipeline
├── requirements.txt          # Dependencies
└── README.md
```

## API Documentation

### Authentication
All API requests require authentication. Use session cookies or API tokens.

### Alert Object
```json
{
  "id": 1,
  "title": "Sample Alert",
  "message": "This is a test alert",
  "alert_type": "warning",
  "created_at": "2023-01-01T12:00:00Z",
  "is_active": true,
  "locations": [
    {
      "id": 1,
      "name": "New York",
      "latitude": "40.712800",
      "longitude": "-74.006000"
    }
  ]
}
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

1. Follow installation steps
2. Install development dependencies: `pip install pytest pytest-django`
3. Run tests before committing
4. Ensure code follows PEP 8 style

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Check the Django documentation
- Review Celery documentation for background tasks