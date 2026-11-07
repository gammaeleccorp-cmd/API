# DRF vs FastAPI

In this note, we compare Django REST Framework (DRF) and FastAPI based on building Rahban API with DRF.

## Philosophy

- **DRF** is "batteries included": ORM, migrations, admin panel, auth, permissions,
  pagination and test tools come with the ecosystem, with strong conventions.
- **FastAPI** is minimal and explicit: routing, validation and docs, and you choose the
  rest (ORM, auth, migrations, admin).

## Validation and serialization

| Topic            | DRF Serializer                        | Pydantic                          |
|------------------|---------------------------------------|-----------------------------------|
| Field definition | Field classes                         | Type hints                        |
| Errors           | `is_valid()` then `serializer.errors` | `ValidationError` raised at once  |
| Persistence      | `create()` / `update()` built in      | None, handled by you              |
| From ORM model   | `ModelSerializer` generates fields    | Separate schema and model         |

`ModelSerializer` removes duplication, but validation is less type-safe and IDE support is weaker.

## Views

DRF has three abstraction levels: `APIView` (explicit), Generic Views (declare queryset and serializer) and `ModelViewSet` with a router (full CRUD in a few lines).                                     
FastAPI has no built-in equivalent; every endpoint is a function.

## Authentication and permissions

- DRF: `simplejwt` gives login, refresh rotation and a blacklist out of the box.
  Permissions are composable classes with two levels: `has_permission` (view) and
  `has_object_permission` (single object, never applied to list endpoints).                                 
- FastAPI: JWT is usually built by hand with `OAuth2PasswordBearer` and `Depends`.
- Object permissions do not protect list endpoints, so `get_queryset()`
  must also filter by owner. That also returns `404` instead of `403`, which does not
  reveal that an object exists.

## Admin panel

Django has built-in admin panel that can manage users, companies, devices, vehicles, commands,...                      
FastAPI doesnt have built-in admin panel.

## Pagination

DRF: one setting enables it for generic views and viewsets (a plain `APIView` still needs
manual work).                                          
FastAPI: `limit` / `offset` parameters per endpoint or through a dependency.

## API documentation

FastAPI generates OpenAPI from type hints and is almost always accurate.                                   
DRF needs `drf-spectacular`, and hand-written `APIView`s need `@extend_schema`.

## Testing

DRF: `APITestCase` creates and destroys a test database and wraps each test in a transaction.                                          
FastAPI: `TestClient` with `pytest`, database setup is managed by hand.

## Performance and async

FastAPI is async-first and usually faster for I/O-heavy workloads.                              
Django and DRF are mainly synchronous, which is fine for typical CRUD APIs.