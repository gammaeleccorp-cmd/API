# Django IoT Backend

A backend project built with **Django**, **Django REST Framework**, and **PostgreSQL** to manage IoT devices, vehicles, users, and telemetry-related functionality.

## Features

- Django project with PostgreSQL integration.
- Environment variable management using `python-dotenv`.
- RESTful API development with Django REST Framework.
- JWT authentication using Simple JWT.
- Device activation and vehicle association.
- User-specific vehicle access and permissions.
- Notes CRUD operations implemented using:
  - APIView
  - Generic Views
  - ModelViewSet
- Custom object-level permissions.
- API pagination.
- Automated API tests using `APITestCase`.
- API documentation using OpenAPI, Swagger UI, and ReDoc.

## Tech Stack

- Python 3.11
- Django 5.2
- Django REST Framework
- PostgreSQL
- Simple JWT
- drf-spectacular
- psycopg
- python-dotenv

## Project Structure

```text
django-iot-project/
│
├── accounts/
├── config/
├── devices/
├── telemetry/
├── vehicles/
├── notes/
│
├── .env
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd django-iot-project
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```powershell
.\venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
SECRET_KEY=your-secret-key
DEBUG=True

DB_NAME=django_iot_db
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_HOST=localhost
DB_PORT=5432
```

**Important:** Never commit your real `.env` file or expose database credentials and Django secret keys.

### 5. Create the PostgreSQL database

Create a PostgreSQL database named:

```sql
CREATE DATABASE django_iot_db;
```

Make sure the database credentials match your `.env` configuration.

### 6. Apply migrations

```bash
python manage.py migrate
```

### 7. Create a superuser

```bash
python manage.py createsuperuser
```

### 8. Run the development server

```bash
python manage.py runserver
```

The API will be available at:

```text
http://127.0.0.1:8000/
```

## API Documentation

Interactive API documentation is available through:

| Documentation | URL |
|---|---|
| Swagger UI | `/api/docs/` |
| ReDoc | `/api/redoc/` |
| OpenAPI Schema | `/api/schema/` |

## Authentication

The project uses JWT authentication.

### Obtain a token

```http
POST /api/token/
```

Example request:

```json
{
    "username": "your_username",
    "password": "your_password"
}
```

### Refresh a token

```http
POST /api/token/refresh/
```

Use the access token in authenticated requests:

```http
Authorization: Bearer <access_token>
```

## Main API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/token/` | Obtain JWT tokens |
| POST | `/api/token/refresh/` | Refresh access token |
| GET | `/api/vehicles/` | List authenticated user's vehicles |
| GET | `/api/vehicles/{id}/` | Retrieve vehicle details |
| POST | `/api/devices/activate/` | Activate a device |
| GET | `/api/notes/` | List notes |
| POST | `/api/notes/` | Create a note |
| GET | `/api/notes/viewset/` | List notes using ModelViewSet |
| POST | `/api/notes/viewset/` | Create a note using ModelViewSet |
| GET | `/api/notes/viewset/{id}/` | Retrieve a note |
| PUT | `/api/notes/viewset/{id}/` | Update a note |
| PATCH | `/api/notes/viewset/{id}/` | Partially update a note |
| DELETE | `/api/notes/viewset/{id}/` | Delete a note |

## Running Tests

Run the automated tests for the Notes application:

```bash
python manage.py test notes
```

## Learning Objectives

This project provides practical experience with:

- Django project architecture.
- REST API development.
- PostgreSQL integration.
- Serializers and ModelSerializers.
- APIView, Generic Views, and ModelViewSet.
- JWT authentication.
- Custom permissions and object ownership.
- Pagination.
- Automated API testing.
- API documentation with Swagger and OpenAPI.

## License

This project is currently intended for educational and professional development purposes.