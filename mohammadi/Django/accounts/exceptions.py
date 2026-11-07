from rest_framework import status
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.views import exception_handler


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Conflict"
    default_code = "conflict"


def api_exception_handler(exc, context):
    """Validation errors are returned as 422 with a `detail` key."""
    response = exception_handler(exc, context)
    if response is not None and isinstance(exc, ValidationError):
        response.status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
        response.data = {"detail": response.data}
    return response
