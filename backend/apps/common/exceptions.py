import logging

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def custom_exception_handler(exc, context):
    """
    Standardizes error responses to maintain consistent JSON schema across all endpoints,
    including request_id and structured error lists.
    """
    response = exception_handler(exc, context)
    request = context.get("request")
    request_id = getattr(request, "request_id", None) if request else None

    if response is not None:
        errors = response.data
        if isinstance(errors, dict) and "detail" in errors:
            message = errors["detail"]
            details = errors
        elif isinstance(errors, dict):
            message = "Validation error"
            details = errors
        elif isinstance(errors, list):
            message = "Error list"
            details = {"non_field_errors": errors}
        else:
            message = str(errors)
            details = {"error": message}

        response.data = {
            "success": False,
            "status_code": response.status_code,
            "message": message,
            "errors": details,
            "request_id": request_id,
        }
    else:
        logger.exception("Unhandled server exception: %s", exc)
        response = Response(
            {
                "success": False,
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "message": "An internal server error occurred.",
                "errors": {"server_error": ["Please contact support if this issue persists."]},
                "request_id": request_id,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return response
