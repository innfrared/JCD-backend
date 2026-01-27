"""Shared response utilities."""
from rest_framework.response import Response
from typing import Any, Dict


def success_response(data: Any, status: int = 200) -> Response:
    """Create a success response."""
    return Response(data, status=status)


def error_response(message: str, status: int = 400, errors: Dict = None) -> Response:
    """Create an error response."""
    response_data = {'error': message}
    if errors:
        response_data['errors'] = errors
    return Response(response_data, status=status)

