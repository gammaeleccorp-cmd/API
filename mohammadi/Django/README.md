# Rahban API

In this project, the Rahban API is developed using Django REST Framework, with PostgreSQL as its database.

## Requirements

- Python 3.12+, Django 6.1, Django REST Framework
- PostgreSQL (settings come from `.env`)
- `djangorestframework-simplejwt` (login, refresh rotation, logout/blacklist)
- `drf-spectacular` (OpenAPI / Swagger)
- Argon2 password hashing, PyJWT for device tokens

## Project structure

| App         | Purpose                                                                 |
|-------------|-------------------------------------------------------------------------|
| `accounts`  | Custom `User` (mobile, national ID, role), register / login / JWT        |
| `devices`   | Devices, heartbeat / health, device commands, device tokens              |
| `vehicles`  | Vehicles and activation (binds a device to a vehicle)                    |
| `telemetry` | Telemetry points sent by devices and the history endpoints               |
| `notes`     | Practice CRUD written as APIView, Generic Views and ModelViewSet         |

## Roles

| Who      | How they get an account                    | Logs in with                | Manages                              |
|----------|--------------------------------------------|-----------------------------|--------------------------------------|
| user     | `POST /api/auth/register/`                 | mobile (= username) + password | own devices, vehicles, telemetry   |
| company  | created by staff in the **admin panel**    | its own username + password | own devices, vehicles, commands      |
| device   | token issued when a vehicle is activated   | device token (bearer)       | heartbeat, commands, telemetry       |
| staff    | `python manage.py createsuperuser`         | `/admin/` only              | everything, through the admin panel  |

Staff accounts are rejected by the API on purpose; everything an admin used to do through the API is
done in the admin panel (`/admin/`):

- **Companies**: create / edit / deactivate company accounts
- **Users, devices, vehicles, telemetry**: browse and search; telemetry is read-only
- **Device commands**: add a command for any device
- **Vehicles**: action "Force deactivate"
- **Devices**: action "Revoke device token"

## Getting started

```bash
python -m venv venv
source venv/bin/activate          
pip install -r requirements.txt
cp .env.example .env    # then edit the values
```

Create the PostgreSQL database and user:

```sql
CREATE DATABASE rahban_db;
CREATE USER rahban_user WITH PASSWORD 'your_password';
ALTER ROLE rahban_user SET client_encoding TO 'utf8';
ALTER ROLE rahban_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE rahban_db TO rahban_user;
\c rahban_db
GRANT ALL ON SCHEMA public TO rahban_user;
ALTER USER rahban_user CREATEDB;   # needed to run tests
```

Apply the existed migration files to the database and run the server:

```bash
python manage.py migrate
python manage.py createsuperuser    # staff account for /admin/
python manage.py runserver
```

- Admin panel: http://127.0.0.1:8000/admin/
- Swagger UI: http://127.0.0.1:8000/api/docs/ (Authorize with an access token)
- OpenAPI schema: http://127.0.0.1:8000/api/schema/

## Device simulator

```bash
python scripts/simulate_device.py --serial DEV-001 --token <device_token>
```

## Running tests

```bash
python manage.py test
```

The database user needs `CREATEDB`; Django creates and drops `test_rahban_db`.

## Notes

See [docs/drf-vs-fastapi.md](docs/drf-vs-fastapi.md) for the DRF vs FastAPI comparison.